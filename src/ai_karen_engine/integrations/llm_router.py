"""
Intelligent LLM Router with Policy-Based Selection

This module implements an intelligent routing system that selects the optimal LLM provider
and runtime based on user preferences, task requirements, privacy constraints, and performance needs.

Key Features:
- Policy-based routing: privacy/context → llama.cpp, interactive → vLLM, flexibility → Transformers
- Tiered fallback strategy: user preference → system defaults → local models → degraded mode
- Explainable routing with dry-run capabilities for debugging
- Privacy-aware routing for sensitive operations
- Performance-aware routing for interactive vs batch operations
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from ai_karen_engine.integrations.registry import get_registry, ModelMetadata, ProviderSpec
from ai_karen_engine.core.degraded_mode import get_degraded_mode_manager, DegradedModeReason

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional
    yaml = None  # type: ignore

try:
    from prometheus_client import Counter, Histogram

    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional
    METRICS_ENABLED = False

    class _DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, n: int = 1):
            pass

        def observe(self, v: float):
            pass

    Counter = Histogram = _DummyMetric

def _create_metrics():
    """Create metrics with collision handling."""
    if not METRICS_ENABLED:
        return _DummyMetric(), _DummyMetric(), _DummyMetric()
    
    try:
        model_invocations = Counter(
            "model_invocations_total",
            "Total LLM model invocations",
            ["model"],
        )
    except ValueError:
        # Metric already exists, get existing one
        from prometheus_client import REGISTRY
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == 'model_invocations_total':
                model_invocations = collector
                break
        else:
            model_invocations = _DummyMetric()
    
    try:
        fallback_rate = Counter(
            "fallback_rate",
            "Fallback invocations",
            ["profile"],
        )
    except ValueError:
        from prometheus_client import REGISTRY
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == 'fallback_rate':
                fallback_rate = collector
                break
        else:
            fallback_rate = _DummyMetric()
    
    try:
        avg_response_time = Histogram(
            "avg_response_time",
            "LLM response time",
            ["model"],
        )
    except ValueError:
        from prometheus_client import REGISTRY
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == 'avg_response_time':
                avg_response_time = collector
                break
        else:
            avg_response_time = _DummyMetric()
    
    return model_invocations, fallback_rate, avg_response_time

MODEL_INVOCATIONS_TOTAL, FALLBACK_RATE, AVG_RESPONSE_TIME = _create_metrics()

# -----------------------------
# Routing Data Models
# -----------------------------

class TaskType(Enum):
    """Types of tasks that influence routing decisions."""
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CREATIVE = "creative"
    ANALYSIS = "analysis"


class PrivacyLevel(Enum):
    """Privacy levels that influence routing decisions."""
    PUBLIC = "public"          # Can use any provider
    INTERNAL = "internal"      # Prefer local or trusted providers
    CONFIDENTIAL = "confidential"  # Local only
    RESTRICTED = "restricted"  # Core helpers only


class PerformanceRequirement(Enum):
    """Performance requirements that influence routing decisions."""
    INTERACTIVE = "interactive"  # Low latency, real-time
    BATCH = "batch"             # High throughput, can wait
    BACKGROUND = "background"   # Lowest priority, resource efficient


@dataclass
class RoutingRequest:
    """Request for LLM routing with context and requirements."""
    prompt: str
    task_type: TaskType = TaskType.CHAT
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    performance_req: PerformanceRequirement = PerformanceRequirement.INTERACTIVE
    
    # User preferences
    preferred_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    preferred_runtime: Optional[str] = None
    
    # Context information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context_length: Optional[int] = None
    
    # Additional requirements
    requires_streaming: bool = False
    requires_function_calling: bool = False
    requires_vision: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    # Capability requirements (optional, for explicit capability-aware routing)
    capability_requirements: Optional[Any] = None  # CapabilityRequirement object
    allow_capability_degradation: bool = True
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class RouteDecision(TypedDict):
    """Result of routing decision with explanation."""
    provider: str
    runtime: str
    model_id: str
    reason: str
    confidence: float
    fallback_chain: List[str]
    estimated_cost: Optional[float]
    estimated_latency: Optional[float]
    privacy_compliant: bool
    capabilities: List[str]


@dataclass
class RoutingPolicy:
    """Policy configuration for routing decisions."""
    name: str
    description: str = ""
    
    # Task type mappings
    task_provider_map: Dict[TaskType, str] = field(default_factory=dict)
    task_runtime_map: Dict[TaskType, str] = field(default_factory=dict)
    
    # Privacy constraints
    privacy_provider_map: Dict[PrivacyLevel, List[str]] = field(default_factory=dict)
    privacy_runtime_map: Dict[PrivacyLevel, List[str]] = field(default_factory=dict)
    
    # Performance preferences
    performance_provider_map: Dict[PerformanceRequirement, str] = field(default_factory=dict)
    performance_runtime_map: Dict[PerformanceRequirement, str] = field(default_factory=dict)
    
    # Fallback chain
    fallback_providers: List[str] = field(default_factory=list)
    fallback_runtimes: List[str] = field(default_factory=list)
    
    # Weights for decision scoring
    privacy_weight: float = 0.4
    performance_weight: float = 0.3
    cost_weight: float = 0.2
    availability_weight: float = 0.1


DEFAULT_PATH = Path(__file__).parents[2] / "config" / "llm_profiles.yml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text()
    if yaml:
        return yaml.safe_load(text)
    # minimal JSON fallback
    return json.loads(text)


def _get_default_routing_policy() -> RoutingPolicy:
    """Get the default routing policy with intelligent mappings."""
    return RoutingPolicy(
        name="default",
        description="Default intelligent routing policy",
        
        # Task-specific provider preferences
        task_provider_map={
            TaskType.CHAT: "openai",
            TaskType.CODE: "deepseek", 
            TaskType.REASONING: "gemini",
            TaskType.EMBEDDING: "huggingface",
            TaskType.SUMMARIZATION: "local",
            TaskType.TRANSLATION: "gemini",
            TaskType.CREATIVE: "openai",
            TaskType.ANALYSIS: "gemini",
        },
        
        # Task-specific runtime preferences
        task_runtime_map={
            TaskType.CHAT: "vllm",
            TaskType.CODE: "transformers",
            TaskType.REASONING: "vllm", 
            TaskType.EMBEDDING: "transformers",
            TaskType.SUMMARIZATION: "llama.cpp",
            TaskType.TRANSLATION: "transformers",
            TaskType.CREATIVE: "vllm",
            TaskType.ANALYSIS: "transformers",
        },
        
        # Privacy-based constraints
        privacy_provider_map={
            PrivacyLevel.PUBLIC: ["openai", "gemini", "deepseek", "huggingface", "local"],
            PrivacyLevel.INTERNAL: ["huggingface", "local"],
            PrivacyLevel.CONFIDENTIAL: ["local"],
            PrivacyLevel.RESTRICTED: ["local"],
        },
        
        privacy_runtime_map={
            PrivacyLevel.PUBLIC: ["vllm", "transformers", "llama.cpp", "core_helpers"],
            PrivacyLevel.INTERNAL: ["transformers", "llama.cpp", "core_helpers"],
            PrivacyLevel.CONFIDENTIAL: ["llama.cpp", "core_helpers"],
            PrivacyLevel.RESTRICTED: ["core_helpers"],
        },
        
        # Performance-based preferences
        performance_provider_map={
            PerformanceRequirement.INTERACTIVE: "openai",  # Fastest API response
            PerformanceRequirement.BATCH: "local",        # Cost effective for bulk
            PerformanceRequirement.BACKGROUND: "local",   # Resource efficient
        },
        
        performance_runtime_map={
            PerformanceRequirement.INTERACTIVE: "vllm",      # High throughput GPU
            PerformanceRequirement.BATCH: "transformers",   # Flexible batching
            PerformanceRequirement.BACKGROUND: "llama.cpp", # Memory efficient
        },
        
        # Fallback chains
        fallback_providers=["local", "huggingface"],
        fallback_runtimes=["llama.cpp", "core_helpers"],
        
        # Decision weights
        privacy_weight=0.4,
        performance_weight=0.3,
        cost_weight=0.2,
        availability_weight=0.1,
    )


class IntelligentLLMRouter:
    """
    Intelligent LLM router with policy-based selection and explainable decisions.
    
    This router implements sophisticated routing logic that considers:
    - User preferences and explicit selections
    - Task type and requirements
    - Privacy constraints and data sensitivity
    - Performance requirements (latency vs throughput)
    - Provider and runtime health status
    - Cost optimization
    - Fallback strategies including degraded mode
    """
    
    def __init__(
        self,
        registry=None,
        policy: Optional[RoutingPolicy] = None,
        enable_degraded_mode: bool = True,
        enable_health_monitoring: bool = True,
    ):
        self.registry = registry or get_registry()
        self.policy = policy or _get_default_routing_policy()
        self.logger = logging.getLogger("kari.intelligent_router")
        self.degraded_mode_manager = get_degraded_mode_manager() if enable_degraded_mode else None
        
        # Initialize fallback manager
        try:
            from ai_karen_engine.integrations.fallback_manager import get_fallback_manager
            self.fallback_manager = get_fallback_manager(registry=self.registry, router=self)
            self.fallback_manager.start_recovery_monitoring()
        except ImportError:
            self.logger.warning("Fallback manager not available")
            self.fallback_manager = None
        
        # Initialize failure pattern analyzer
        try:
            from ai_karen_engine.integrations.failure_pattern_analyzer import get_failure_analyzer
            self.failure_analyzer = get_failure_analyzer(registry=self.registry)
        except ImportError:
            self.logger.warning("Failure pattern analyzer not available")
            self.failure_analyzer = None
        
        # Initialize partial failure handler
        try:
            from ai_karen_engine.integrations.partial_failure_handler import get_partial_failure_handler
            self.partial_failure_handler = get_partial_failure_handler(registry=self.registry)
        except ImportError:
            self.logger.warning("Partial failure handler not available")
            self.partial_failure_handler = None
        
        # Initialize capability router
        try:
            from ai_karen_engine.integrations.capability_router import get_capability_router
            self.capability_router = get_capability_router(registry=self.registry, base_router=self)
        except ImportError:
            self.logger.warning("Capability router not available")
            self.capability_router = None
        
        # Initialize model availability manager
        try:
            from ai_karen_engine.integrations.model_availability_manager import get_model_availability_manager
            self.model_availability_manager = get_model_availability_manager(registry=self.registry)
            if not self.model_availability_manager.monitoring_active:
                self.model_availability_manager.start_monitoring()
        except ImportError:
            self.logger.warning("Model availability manager not available")
            self.model_availability_manager = None
        
        # Initialize health monitoring if enabled
        self.health_monitor = None
        if enable_health_monitoring:
            try:
                from ai_karen_engine.integrations.health_monitor import get_health_monitor
                self.health_monitor = get_health_monitor()
                # Start monitoring if not already active
                if not self.health_monitor.monitoring_active:
                    self.health_monitor.start_monitoring()
            except ImportError:
                self.logger.warning("Health monitoring not available")
                self.health_monitor = None
        
        # Routing statistics
        self.routing_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "fallback_routes": 0,
            "degraded_routes": 0,
            "failed_routes": 0,
        }
    
    def route(self, request: RoutingRequest) -> RouteDecision:
        """
        Route a request to the optimal provider and runtime.
        
        Routing precedence:
        1. User explicit preferences (if healthy)
        2. Policy-based selection (task + privacy + performance)
        3. System defaults with health filtering
        4. Local models as fallback
        5. Degraded mode with core helpers
        """
        # Check if request has capability requirements and use capability-aware routing
        if hasattr(request, 'capability_requirements') and request.capability_requirements:
            return self.route_with_capability_requirements(request, request.capability_requirements)
        
        # Auto-detect capability requirements based on request attributes
        capability_requirements = self._detect_capability_requirements(request)
        if capability_requirements and capability_requirements.required:
            return self.route_with_capability_requirements(request, capability_requirements)
        
        return self.route_with_fallback(request)
    
    def route_with_fallback(self, request: RoutingRequest) -> RouteDecision:
        """
        Route a request with comprehensive fallback handling and detailed logging.
        
        This method implements robust fallback chain execution with retry logic,
        detailed logging for each routing attempt, and intelligent fallback chain
        construction based on provider health and capabilities.
        
        Args:
            request: The routing request with context and requirements
            
        Returns:
            RouteDecision with comprehensive fallback information
            
        Raises:
            RuntimeError: When all routing options are exhausted
        """
        self.routing_stats["total_requests"] += 1
        failed_providers = []
        attempted_routes = []
        
        self.logger.info(f"Starting routing for {request.task_type.value} task with {request.privacy_level.value} privacy")
        
        try:
            # Step 1: Check explicit user preferences
            if request.preferred_provider and request.preferred_model:
                self.logger.debug(f"Attempting explicit user preference: {request.preferred_provider}/{request.preferred_model}")
                decision = self._try_explicit_preference_with_retry(request, failed_providers, attempted_routes)
                if decision:
                    self.routing_stats["successful_routes"] += 1
                    self.logger.info(f"Successfully routed to explicit preference: {decision['provider']}/{decision['model_id']}")
                    return decision
            
            # Step 2: Policy-based intelligent selection
            self.logger.debug("Attempting policy-based selection")
            decision = self._policy_based_selection_with_retry(request, failed_providers, attempted_routes)
            if decision:
                self.routing_stats["successful_routes"] += 1
                self.logger.info(f"Successfully routed via policy: {decision['provider']}/{decision['model_id']}")
                return decision
            
            # Step 3: System defaults with health filtering
            self.logger.debug("Attempting system default selection")
            decision = self._system_default_selection_with_retry(request, failed_providers, attempted_routes)
            if decision:
                self.routing_stats["fallback_routes"] += 1
                self.logger.info(f"Successfully routed via system defaults: {decision['provider']}/{decision['model_id']}")
                return decision
            
            # Step 4: Execute comprehensive fallback chain
            self.logger.debug("Executing comprehensive fallback chain")
            decision = self._execute_fallback_chain(request, failed_providers, attempted_routes)
            if decision:
                self.routing_stats["fallback_routes"] += 1
                self.logger.info(f"Successfully routed via fallback chain: {decision['provider']}/{decision['model_id']}")
                return decision
            
            # Step 5: Degraded mode as last resort
            if self.degraded_mode_manager:
                self.logger.debug("Attempting degraded mode activation")
                decision = self._degraded_mode_selection_with_retry(request, failed_providers, attempted_routes)
                if decision:
                    self.routing_stats["degraded_routes"] += 1
                    self.logger.warning(f"Routed to degraded mode: {decision['provider']}/{decision['model_id']}")
                    return decision
            
            # No viable options found - log comprehensive failure information
            self.routing_stats["failed_routes"] += 1
            failure_summary = {
                "failed_providers": failed_providers,
                "attempted_routes": attempted_routes,
                "request_requirements": {
                    "task_type": request.task_type.value,
                    "privacy_level": request.privacy_level.value,
                    "performance_req": request.performance_req.value,
                    "requires_streaming": request.requires_streaming,
                    "requires_function_calling": request.requires_function_calling,
                    "requires_vision": request.requires_vision,
                }
            }
            self.logger.error(f"All routing options exhausted. Failure summary: {failure_summary}")
            raise RuntimeError(f"No viable LLM providers or runtimes available. Failed providers: {failed_providers}")
            
        except Exception as e:
            if "No viable LLM providers" not in str(e):
                self.logger.error(f"Routing failed with unexpected error: {e}")
                self.routing_stats["failed_routes"] += 1
            raise
    
    def dry_run(self, request: RoutingRequest) -> Dict[str, Any]:
        """
        Perform a dry run of routing decisions for debugging and explanation.
        
        Returns detailed information about the routing process without actually
        selecting a provider or runtime.
        """
        dry_run_result = {
            "request_summary": {
                "task_type": request.task_type.value,
                "privacy_level": request.privacy_level.value,
                "performance_req": request.performance_req.value,
                "preferred_provider": request.preferred_provider,
                "preferred_model": request.preferred_model,
                "requires_streaming": request.requires_streaming,
                "requires_function_calling": request.requires_function_calling,
                "requires_vision": request.requires_vision,
            },
            "routing_steps": [],
            "available_providers": [],
            "available_runtimes": [],
            "policy_analysis": {},
            "final_recommendation": None,
            "alternative_options": [],
        }
        
        # Analyze available providers
        providers = self.registry.list_providers(healthy_only=False)
        for provider_name in providers:
            provider_spec = self.registry.get_provider_spec(provider_name)
            health = self.registry.get_health_status(f"provider:{provider_name}")
            
            dry_run_result["available_providers"].append({
                "name": provider_name,
                "requires_api_key": provider_spec.requires_api_key if provider_spec else False,
                "capabilities": list(provider_spec.capabilities) if provider_spec else [],
                "health_status": health.status if health else "unknown",
                "category": provider_spec.category if provider_spec else "unknown",
            })
        
        # Analyze available runtimes
        runtimes = self.registry.list_runtimes(healthy_only=False)
        for runtime_name in runtimes:
            runtime_spec = self.registry.get_runtime_spec(runtime_name)
            health = self.registry.get_health_status(f"runtime:{runtime_name}")
            
            dry_run_result["available_runtimes"].append({
                "name": runtime_name,
                "family": runtime_spec.family if runtime_spec else [],
                "supports": runtime_spec.supports if runtime_spec else [],
                "health_status": health.status if health else "unknown",
                "requires_gpu": runtime_spec.requires_gpu if runtime_spec else False,
                "priority": runtime_spec.priority if runtime_spec else 50,
            })
        
        # Step-by-step routing analysis
        try:
            # Step 1: Explicit preferences
            if request.preferred_provider and request.preferred_model:
                step_result = self._analyze_explicit_preference(request)
                dry_run_result["routing_steps"].append({
                    "step": 1,
                    "name": "Explicit User Preference",
                    "result": step_result,
                })
                if step_result["viable"]:
                    dry_run_result["final_recommendation"] = step_result["decision"]
            
            # Step 2: Policy-based selection
            if not dry_run_result["final_recommendation"]:
                step_result = self._analyze_policy_selection(request)
                dry_run_result["routing_steps"].append({
                    "step": 2,
                    "name": "Policy-Based Selection",
                    "result": step_result,
                })
                dry_run_result["policy_analysis"] = step_result.get("policy_analysis", {})
                if step_result["viable"]:
                    dry_run_result["final_recommendation"] = step_result["decision"]
            
            # Step 3: System defaults
            if not dry_run_result["final_recommendation"]:
                step_result = self._analyze_system_defaults(request)
                dry_run_result["routing_steps"].append({
                    "step": 3,
                    "name": "System Default Selection",
                    "result": step_result,
                })
                if step_result["viable"]:
                    dry_run_result["final_recommendation"] = step_result["decision"]
            
            # Step 4: Local fallback
            if not dry_run_result["final_recommendation"]:
                step_result = self._analyze_local_fallback(request)
                dry_run_result["routing_steps"].append({
                    "step": 4,
                    "name": "Local Fallback Selection",
                    "result": step_result,
                })
                if step_result["viable"]:
                    dry_run_result["final_recommendation"] = step_result["decision"]
            
            # Step 5: Degraded mode
            if not dry_run_result["final_recommendation"] and self.degraded_mode_manager:
                step_result = self._analyze_degraded_mode(request)
                dry_run_result["routing_steps"].append({
                    "step": 5,
                    "name": "Degraded Mode Selection",
                    "result": step_result,
                })
                if step_result["viable"]:
                    dry_run_result["final_recommendation"] = step_result["decision"]
            
            # Generate alternative options
            dry_run_result["alternative_options"] = self._generate_alternatives(request)
            
        except Exception as e:
            dry_run_result["error"] = str(e)
            self.logger.error(f"Dry run analysis failed: {e}")
        
        return dry_run_result
    
    def _try_explicit_preference_with_retry(self, request: RoutingRequest, failed_providers: List[str], attempted_routes: List[Dict[str, Any]]) -> Optional[RouteDecision]:
        """Try explicit user preferences with retry logic and detailed logging."""
        attempt = {
            "step": "explicit_preference",
            "provider": request.preferred_provider,
            "model": request.preferred_model,
            "runtime": request.preferred_runtime,
            "timestamp": time.time(),
            "success": False,
            "failure_reason": None
        }
        
        try:
            decision = self._try_explicit_preference(request)
            if decision:
                attempt["success"] = True
                attempted_routes.append(attempt)
                return decision
            else:
                attempt["failure_reason"] = "Preference not viable (health/compatibility issues)"
                if request.preferred_provider not in failed_providers:
                    failed_providers.append(request.preferred_provider)
                    # Record failure for pattern analysis
                    self.record_routing_failure(
                        provider=request.preferred_provider,
                        error_type="preference_not_viable",
                        error_message="Explicit preference not viable due to health/compatibility issues",
                        request_type=request.task_type.value,
                        model=request.preferred_model
                    )
        except Exception as e:
            attempt["failure_reason"] = str(e)
            if request.preferred_provider not in failed_providers:
                failed_providers.append(request.preferred_provider)
                # Record failure for pattern analysis
                self.record_routing_failure(
                    provider=request.preferred_provider,
                    error_type="explicit_preference_error",
                    error_message=str(e),
                    request_type=request.task_type.value,
                    model=request.preferred_model
                )
            self.logger.warning(f"Explicit preference failed: {e}")
        
        attempted_routes.append(attempt)
        return None
    
    def _policy_based_selection_with_retry(self, request: RoutingRequest, failed_providers: List[str], attempted_routes: List[Dict[str, Any]]) -> Optional[RouteDecision]:
        """Policy-based selection with retry logic and detailed logging."""
        preferred_provider = self._get_policy_provider(request)
        preferred_runtime = self._get_policy_runtime(request)
        
        attempt = {
            "step": "policy_based",
            "provider": preferred_provider,
            "runtime": preferred_runtime,
            "timestamp": time.time(),
            "success": False,
            "failure_reason": None
        }
        
        try:
            decision = self._policy_based_selection(request)
            if decision:
                attempt["success"] = True
                attempted_routes.append(attempt)
                return decision
            else:
                attempt["failure_reason"] = "Policy selection not viable (health/privacy/compatibility issues)"
                if preferred_provider not in failed_providers:
                    failed_providers.append(preferred_provider)
                    # Record failure for pattern analysis
                    self.record_routing_failure(
                        provider=preferred_provider,
                        error_type="policy_selection_not_viable",
                        error_message="Policy-based selection not viable due to health/privacy/compatibility issues",
                        request_type=request.task_type.value
                    )
        except Exception as e:
            attempt["failure_reason"] = str(e)
            if preferred_provider not in failed_providers:
                failed_providers.append(preferred_provider)
                # Record failure for pattern analysis
                self.record_routing_failure(
                    provider=preferred_provider,
                    error_type="policy_selection_error",
                    error_message=str(e),
                    request_type=request.task_type.value
                )
            self.logger.warning(f"Policy-based selection failed: {e}")
        
        attempted_routes.append(attempt)
        return None
    
    def _system_default_selection_with_retry(self, request: RoutingRequest, failed_providers: List[str], attempted_routes: List[Dict[str, Any]]) -> Optional[RouteDecision]:
        """System default selection with retry logic and detailed logging."""
        attempt = {
            "step": "system_defaults",
            "timestamp": time.time(),
            "success": False,
            "failure_reason": None
        }
        
        try:
            decision = self._system_default_selection(request)
            if decision:
                attempt["provider"] = decision["provider"]
                attempt["runtime"] = decision["runtime"]
                attempt["success"] = True
                attempted_routes.append(attempt)
                return decision
            else:
                attempt["failure_reason"] = "No healthy system defaults available"
        except Exception as e:
            attempt["failure_reason"] = str(e)
            self.logger.warning(f"System default selection failed: {e}")
        
        attempted_routes.append(attempt)
        return None
    
    def _execute_fallback_chain(self, request: RoutingRequest, failed_providers: List[str], attempted_routes: List[Dict[str, Any]]) -> Optional[RouteDecision]:
        """Execute comprehensive fallback chain with detailed logging using fallback manager."""
        if self.fallback_manager:
            # Use the dedicated fallback manager for intelligent fallback handling
            fallback_chain = self.fallback_manager.construct_fallback_chain(request, failed_providers)
            fallback_result = self.fallback_manager.execute_fallback(request, fallback_chain)
            
            # Convert fallback attempts to attempted_routes format
            for attempt in fallback_result.attempts:
                attempted_routes.append({
                    "step": "fallback_chain",
                    "provider": attempt.provider,
                    "runtime": attempt.runtime,
                    "model": attempt.model,
                    "timestamp": attempt.timestamp.timestamp(),
                    "success": attempt.success,
                    "failure_reason": attempt.error_message,
                    "latency": attempt.latency,
                    "confidence": attempt.confidence
                })
            
            if fallback_result.success:
                # Create route decision from successful fallback
                decision = RouteDecision(
                    provider=fallback_result.used_provider,
                    runtime=fallback_result.used_runtime,
                    model_id=fallback_result.used_model,
                    reason=f"Fallback chain success: {fallback_result.strategy_used.value if fallback_result.strategy_used else 'unknown'}",
                    confidence=0.6,  # Medium confidence for fallback
                    fallback_chain=fallback_chain,
                    estimated_cost=self._estimate_cost(fallback_result.used_provider, fallback_result.used_model),
                    estimated_latency=self._estimate_latency(fallback_result.used_provider, fallback_result.used_runtime),
                    privacy_compliant=self._check_privacy_compliance(request, fallback_result.used_provider, fallback_result.used_runtime),
                    capabilities=self._get_provider_capabilities(fallback_result.used_provider)
                )
                
                # Add fallback metadata
                decision["attempted_routes"] = attempted_routes
                decision["failed_providers"] = failed_providers
                decision["fallback_total_time"] = fallback_result.total_time
                decision["degraded_mode_activated"] = fallback_result.degraded_mode_activated
                
                return decision
            else:
                # Update failed providers list
                for attempt in fallback_result.attempts:
                    if not attempt.success and attempt.provider not in failed_providers:
                        failed_providers.append(attempt.provider)
        else:
            # Fallback to original implementation if fallback manager not available
            fallback_chain = self._build_comprehensive_fallback_chain(request, failed_providers)
            
            self.logger.info(f"Executing fallback chain (legacy): {fallback_chain}")
            
            for provider in fallback_chain:
                if provider in failed_providers:
                    self.logger.debug(f"Skipping already failed provider: {provider}")
                    continue
                
                attempt = {
                    "step": "fallback_chain",
                    "provider": provider,
                    "timestamp": time.time(),
                    "success": False,
                    "failure_reason": None
                }
                
                try:
                    # Check provider health first
                    if not self._is_provider_healthy(provider):
                        attempt["failure_reason"] = "Provider unhealthy"
                        failed_providers.append(provider)
                        attempted_routes.append(attempt)
                        continue
                    
                    # Check privacy compliance
                    if not self._check_privacy_compliance(request, provider, None):
                        attempt["failure_reason"] = "Privacy compliance failed"
                        attempted_routes.append(attempt)
                        continue
                    
                    # Try to select model and runtime
                    model_id = self._select_model_for_provider(provider, request)
                    if not model_id:
                        attempt["failure_reason"] = "No suitable model found"
                        failed_providers.append(provider)
                        attempted_routes.append(attempt)
                        continue
                    
                    # Find compatible runtime
                    decision = self._find_compatible_runtime_for_fallback(request, provider, model_id)
                    if decision:
                        attempt["model"] = model_id
                        attempt["runtime"] = decision["runtime"]
                        attempt["success"] = True
                        attempted_routes.append(attempt)
                        
                        # Update decision with fallback information
                        decision["fallback_chain"] = fallback_chain
                        decision["attempted_routes"] = attempted_routes
                        decision["failed_providers"] = failed_providers
                        
                        return decision
                    else:
                        attempt["failure_reason"] = "No compatible runtime found"
                        failed_providers.append(provider)
                        
                except Exception as e:
                    attempt["failure_reason"] = str(e)
                    failed_providers.append(provider)
                    self.logger.warning(f"Fallback attempt failed for {provider}: {e}")
                
                attempted_routes.append(attempt)
        
        return None
    
    def _degraded_mode_selection_with_retry(self, request: RoutingRequest, failed_providers: List[str], attempted_routes: List[Dict[str, Any]]) -> Optional[RouteDecision]:
        """Degraded mode selection with retry logic and detailed logging."""
        attempt = {
            "step": "degraded_mode",
            "provider": "core_helpers",
            "runtime": "core_helpers",
            "timestamp": time.time(),
            "success": False,
            "failure_reason": None
        }
        
        try:
            # Try using fallback manager for degraded mode activation
            if self.fallback_manager:
                decision = self.fallback_manager.activate_degraded_mode(request)
                if decision:
                    attempt["success"] = True
                    attempted_routes.append(attempt)
                    
                    # Update decision with comprehensive fallback information
                    decision["fallback_chain"] = failed_providers
                    decision["attempted_routes"] = attempted_routes
                    decision["failed_providers"] = failed_providers
                    
                    return decision
                else:
                    attempt["failure_reason"] = "Fallback manager could not activate degraded mode"
            
            # Fallback to direct degraded mode manager
            if not self.degraded_mode_manager:
                attempt["failure_reason"] = "Degraded mode manager not available"
                attempted_routes.append(attempt)
                return None
            
            decision = self._degraded_mode_selection(request)
            if decision:
                attempt["success"] = True
                attempted_routes.append(attempt)
                
                # Update decision with comprehensive fallback information
                decision["fallback_chain"] = failed_providers
                decision["attempted_routes"] = attempted_routes
                decision["failed_providers"] = failed_providers
                
                return decision
            else:
                attempt["failure_reason"] = "Degraded mode not available"
        except Exception as e:
            attempt["failure_reason"] = str(e)
            self.logger.error(f"Degraded mode selection failed: {e}")
        
        attempted_routes.append(attempt)
        return None
    
    def _build_comprehensive_fallback_chain(self, request: RoutingRequest, failed_providers: List[str]) -> List[str]:
        """Build comprehensive fallback chain based on provider health and capabilities."""
        fallback_chain = []
        
        # Start with policy fallbacks
        policy_fallbacks = [p for p in self.policy.fallback_providers if p not in failed_providers]
        fallback_chain.extend(policy_fallbacks)
        
        # Add local providers if not already included
        local_providers = ["local", "huggingface"]
        for provider in local_providers:
            if provider not in fallback_chain and provider not in failed_providers:
                if self._check_privacy_compliance(request, provider, None):
                    fallback_chain.append(provider)
        
        # Add any remaining healthy providers that meet privacy requirements
        all_providers = self.registry.list_providers(healthy_only=True)
        for provider in all_providers:
            if (provider not in fallback_chain and 
                provider not in failed_providers and
                self._check_privacy_compliance(request, provider, None)):
                fallback_chain.append(provider)
        
        self.logger.debug(f"Built fallback chain: {fallback_chain} (excluding failed: {failed_providers})")
        return fallback_chain
    
    def _get_provider_capabilities(self, provider: str) -> List[str]:
        """Get capabilities for a provider."""
        provider_spec = self.registry.get_provider_spec(provider)
        if provider_spec:
            return list(provider_spec.capabilities)
        return []
    
    def _find_compatible_runtime_for_fallback(self, request: RoutingRequest, provider: str, model_id: str) -> Optional[RouteDecision]:
        """Find compatible runtime for fallback provider."""
        provider_spec = self.registry.get_provider_spec(provider)
        if not provider_spec:
            return None
        
        # Create model metadata
        model_meta = ModelMetadata(
            id=model_id,
            name=model_id,
            provider=provider,
        )
        
        # Get compatible runtimes
        compatible_runtimes = self.registry.compatible_runtimes(model_meta)
        
        # Filter by health and privacy compliance
        viable_runtimes = []
        for runtime in compatible_runtimes:
            if (self._is_runtime_healthy(runtime) and 
                self._check_privacy_compliance(request, provider, runtime)):
                viable_runtimes.append(runtime)
        
        if not viable_runtimes:
            return None
        
        # Select the best runtime (first one is highest priority)
        selected_runtime = viable_runtimes[0]
        
        confidence = self._calculate_confidence(request, provider, selected_runtime, model_id)
        
        return RouteDecision(
            provider=provider,
            runtime=selected_runtime,
            model_id=model_id,
            reason=f"Fallback selection: {provider} with {selected_runtime}",
            confidence=confidence,
            fallback_chain=[],  # Will be updated by caller
            estimated_cost=self._estimate_cost(provider, model_id),
            estimated_latency=self._estimate_latency(provider, selected_runtime),
            privacy_compliant=self._check_privacy_compliance(request, provider, selected_runtime),
            capabilities=list(provider_spec.capabilities),
        )
    
    def _try_explicit_preference(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Try to honor explicit user preferences with capability validation."""
        if not (request.preferred_provider and request.preferred_model):
            return None
        
        # Check if preferred provider is healthy
        provider_health = self.registry.get_health_status(f"provider:{request.preferred_provider}")
        if provider_health and provider_health.status not in ["healthy", "unknown"]:
            self.logger.info(f"Preferred provider {request.preferred_provider} is unhealthy: {provider_health.status}")
            return None
        
        # Check if provider exists and get spec
        provider_spec = self.registry.get_provider_spec(request.preferred_provider)
        if not provider_spec:
            self.logger.info(f"Preferred provider {request.preferred_provider} not found")
            return None
        
        # Validate capability requirements
        capability_validation = self._validate_provider_capabilities(request, provider_spec)
        if not capability_validation["valid"]:
            self.logger.info(f"Explicit preference {request.preferred_provider} missing capabilities: {capability_validation['missing_capabilities']}")
            
            # Try capability fallback for explicit preferences
            fallback_request = self._create_capability_fallback_request(request)
            if fallback_request != request:
                self.logger.info(f"Explicit preference attempting capability fallback: {self._get_capability_changes(request, fallback_request)}")
                return self._try_explicit_preference(fallback_request)
            return None
        
        # Create model metadata for compatibility checking
        model_meta = ModelMetadata(
            id=request.preferred_model,
            name=request.preferred_model,
            provider=request.preferred_provider,
        )
        
        # Find compatible runtime (prefer user preference if specified)
        if request.preferred_runtime:
            runtime_health = self.registry.get_health_status(f"runtime:{request.preferred_runtime}")
            if runtime_health is None or runtime_health.status in ["healthy", "unknown"]:
                runtime_spec = self.registry.get_runtime_spec(request.preferred_runtime)
                if runtime_spec and self.registry._is_compatible(model_meta, runtime_spec):
                    return RouteDecision(
                        provider=request.preferred_provider,
                        runtime=request.preferred_runtime,
                        model_id=request.preferred_model,
                        reason="Explicit user preference (provider + model + runtime) with capability validation",
                        confidence=1.0,
                        fallback_chain=[],
                        estimated_cost=None,
                        estimated_latency=None,
                        privacy_compliant=self._check_privacy_compliance(request, request.preferred_provider, request.preferred_runtime),
                        capabilities=list(provider_spec.capabilities),
                    )
        
        # Find optimal runtime for the model
        compatible_runtimes = self.registry.compatible_runtimes(model_meta)
        if compatible_runtimes:
            # Filter by health
            healthy_runtimes = [
                rt for rt in compatible_runtimes
                if self.registry.get_health_status(f"runtime:{rt}") is None or
                   self.registry.get_health_status(f"runtime:{rt}").status in ["healthy", "unknown"]
            ]
            
            if healthy_runtimes:
                selected_runtime = healthy_runtimes[0]  # Highest priority healthy runtime
                return RouteDecision(
                    provider=request.preferred_provider,
                    runtime=selected_runtime,
                    model_id=request.preferred_model,
                    reason="Explicit user preference (provider + model) with capability validation",
                    confidence=0.9,
                    fallback_chain=[],
                    estimated_cost=None,
                    estimated_latency=None,
                    privacy_compliant=self._check_privacy_compliance(request, request.preferred_provider, selected_runtime),
                    capabilities=list(provider_spec.capabilities),
                )
        
        return None


    def _policy_based_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select provider and runtime based on routing policy with capability-aware routing."""
        # Get policy-based preferences
        preferred_provider = self._get_policy_provider(request)
        preferred_runtime = self._get_policy_runtime(request)
        
        # Check privacy constraints
        allowed_providers = self.policy.privacy_provider_map.get(request.privacy_level, [])
        allowed_runtimes = self.policy.privacy_runtime_map.get(request.privacy_level, [])
        
        # Filter providers by capability requirements first
        capability_compatible_providers = self._filter_providers_by_capabilities(request, allowed_providers)
        
        if preferred_provider not in capability_compatible_providers:
            # Find alternative provider that meets privacy and capability requirements
            for provider in capability_compatible_providers:
                if self._is_provider_healthy(provider):
                    preferred_provider = provider
                    break
            else:
                # Try capability fallback if no exact match found
                fallback_request = self._create_capability_fallback_request(request)
                if fallback_request != request:
                    self.logger.info(f"Attempting capability fallback: {self._get_capability_changes(request, fallback_request)}")
                    return self._policy_based_selection(fallback_request)
                return None  # No capability-compatible providers available
        
        if preferred_runtime not in allowed_runtimes:
            # Find alternative runtime that meets privacy requirements
            for runtime in allowed_runtimes:
                if self._is_runtime_healthy(runtime):
                    preferred_runtime = runtime
                    break
            else:
                return None  # No privacy-compliant runtimes available
        
        # Check if preferred provider is healthy
        if not self._is_provider_healthy(preferred_provider):
            return None
        
        # Check if preferred runtime is healthy
        if not self._is_runtime_healthy(preferred_runtime):
            return None
        
        # Get provider spec for capabilities
        provider_spec = self.registry.get_provider_spec(preferred_provider)
        if not provider_spec:
            return None
        
        # Validate capability requirements (should pass since we filtered above)
        capability_validation = self._validate_provider_capabilities(request, provider_spec)
        if not capability_validation["valid"]:
            self.logger.warning(f"Provider {preferred_provider} failed capability validation: {capability_validation['missing_capabilities']}")
            return None
        
        # Select a model (this would be enhanced with actual model discovery)
        model_id = self._select_model_for_provider(preferred_provider, request)
        if not model_id:
            return None
        
        confidence = self._calculate_confidence(request, preferred_provider, preferred_runtime, model_id)
        
        return RouteDecision(
            provider=preferred_provider,
            runtime=preferred_runtime,
            model_id=model_id,
            reason=f"Policy-based selection for {request.task_type.value} task with {request.privacy_level.value} privacy",
            confidence=confidence,
            fallback_chain=self._build_fallback_chain(request),
            estimated_cost=self._estimate_cost(preferred_provider, model_id),
            estimated_latency=self._estimate_latency(preferred_provider, preferred_runtime),
            privacy_compliant=True,
            capabilities=list(provider_spec.capabilities),
        )
    
    def _system_default_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select using system defaults with health and capability filtering."""
        # Get healthy providers in priority order
        healthy_providers = [
            p for p in self.registry.list_providers(healthy_only=True)
            if self._check_privacy_compliance(request, p, None)
        ]
        
        if not healthy_providers:
            return None
        
        # Filter by capability requirements
        capability_compatible_providers = self._filter_providers_by_capabilities(request, healthy_providers)
        
        if not capability_compatible_providers:
            # Try capability fallback if no exact match found
            fallback_request = self._create_capability_fallback_request(request)
            if fallback_request != request:
                self.logger.info(f"System defaults attempting capability fallback: {self._get_capability_changes(request, fallback_request)}")
                return self._system_default_selection(fallback_request)
            return None
        
        # Rank providers by capability score
        ranked_providers = self._select_providers_by_capability_score(request, capability_compatible_providers)
        
        if not ranked_providers:
            return None
        
        # Select best-scoring provider
        selected_provider = ranked_providers[0]
        provider_spec = self.registry.get_provider_spec(selected_provider)
        
        # Find compatible runtime
        model_id = self._select_model_for_provider(selected_provider, request)
        if not model_id:
            return None
        
        model_meta = ModelMetadata(
            id=model_id,
            name=model_id,
            provider=selected_provider,
        )
        
        compatible_runtimes = self.registry.compatible_runtimes(model_meta)
        healthy_runtimes = [
            rt for rt in compatible_runtimes
            if self._is_runtime_healthy(rt) and self._check_privacy_compliance(request, selected_provider, rt)
        ]
        
        if not healthy_runtimes:
            return None
        
        selected_runtime = healthy_runtimes[0]
        
        return RouteDecision(
            provider=selected_provider,
            runtime=selected_runtime,
            model_id=model_id,
            reason="System default selection with health and capability filtering",
            confidence=0.7,
            fallback_chain=self._build_fallback_chain(request),
            estimated_cost=self._estimate_cost(selected_provider, model_id),
            estimated_latency=self._estimate_latency(selected_provider, selected_runtime),
            privacy_compliant=self._check_privacy_compliance(request, selected_provider, selected_runtime),
            capabilities=list(provider_spec.capabilities) if provider_spec else [],
        )
    
    def _local_fallback_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select local models as fallback with capability-aware routing."""
        local_providers = ["local", "huggingface"]
        local_runtimes = ["llama.cpp", "transformers"]
        
        # Filter local providers by capability requirements
        capability_compatible_providers = []
        for provider in local_providers:
            if (self._is_provider_healthy(provider) and 
                self._check_privacy_compliance(request, provider, None) and
                self._check_provider_capabilities(request, provider)):
                capability_compatible_providers.append(provider)
        
        if not capability_compatible_providers:
            # Try capability fallback for local providers
            fallback_request = self._create_capability_fallback_request(request)
            if fallback_request != request:
                self.logger.info(f"Local fallback attempting capability fallback: {self._get_capability_changes(request, fallback_request)}")
                return self._local_fallback_selection(fallback_request)
            return None
        
        # Rank providers by capability score
        ranked_providers = self._select_providers_by_capability_score(request, capability_compatible_providers)
        
        for provider in ranked_providers:
            model_id = self._select_model_for_provider(provider, request)
            if not model_id:
                continue
            
            # Find compatible runtime
            for runtime in local_runtimes:
                if self._is_runtime_healthy(runtime) and self._check_privacy_compliance(request, provider, runtime):
                    provider_spec = self.registry.get_provider_spec(provider)
                    
                    return RouteDecision(
                        provider=provider,
                        runtime=runtime,
                        model_id=model_id,
                        reason="Local fallback selection with capability filtering",
                        confidence=0.5,
                        fallback_chain=[],
                        estimated_cost=0.0,  # Local models are free
                        estimated_latency=self._estimate_latency(provider, runtime),
                        privacy_compliant=True,  # Local models are always privacy compliant
                        capabilities=list(provider_spec.capabilities) if provider_spec else [],
                    )
        
        return None
    
    def _degraded_mode_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select degraded mode with core helpers."""
        if not self.degraded_mode_manager:
            return None
        
        # Activate degraded mode if not already active
        if not self.degraded_mode_manager.get_status().is_active:
            self.degraded_mode_manager.activate_degraded_mode(
                DegradedModeReason.ALL_PROVIDERS_FAILED,
                ["No viable providers or runtimes available"]
            )
        
        return RouteDecision(
            provider="core_helpers",
            runtime="core_helpers",
            model_id="tinyllama+distilbert+spacy",
            reason="Degraded mode - all other options failed",
            confidence=0.2,
            fallback_chain=[],
            estimated_cost=0.0,
            estimated_latency=1.0,  # Fast but limited
            privacy_compliant=True,
            capabilities=["basic_text", "simple_analysis"],
        )
    
    # Helper methods for routing logic
    
    def _get_policy_provider(self, request: RoutingRequest) -> str:
        """Get preferred provider based on policy."""
        # Task-based preference
        task_provider = self.policy.task_provider_map.get(request.task_type)
        if task_provider:
            return task_provider
        
        # Performance-based preference
        perf_provider = self.policy.performance_provider_map.get(request.performance_req)
        if perf_provider:
            return perf_provider
        
        # Default fallback
        return self.policy.fallback_providers[0] if self.policy.fallback_providers else "local"
    
    def _get_policy_runtime(self, request: RoutingRequest) -> str:
        """Get preferred runtime based on policy."""
        # Task-based preference
        task_runtime = self.policy.task_runtime_map.get(request.task_type)
        if task_runtime:
            return task_runtime
        
        # Performance-based preference
        perf_runtime = self.policy.performance_runtime_map.get(request.performance_req)
        if perf_runtime:
            return perf_runtime
        
        # Default fallback
        return self.policy.fallback_runtimes[0] if self.policy.fallback_runtimes else "llama.cpp"
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is healthy."""
        # First check if provider is disabled by failure analyzer
        if self.failure_analyzer and self.failure_analyzer.is_provider_disabled(provider):
            return False
        
        if self.health_monitor:
            return self.health_monitor.is_component_healthy(f"provider:{provider}")
        else:
            health = self.registry.get_health_status(f"provider:{provider}")
            return health is None or health.status in ["healthy", "unknown"]
    
    def _is_runtime_healthy(self, runtime: str) -> bool:
        """Check if a runtime is healthy."""
        if self.health_monitor:
            return self.health_monitor.is_component_healthy(f"runtime:{runtime}")
        else:
            health = self.registry.get_health_status(f"runtime:{runtime}")
            return health is None or health.status in ["healthy", "unknown"]
    
    def _check_privacy_compliance(self, request: RoutingRequest, provider: str, runtime: Optional[str]) -> bool:
        """Check if provider/runtime combination meets privacy requirements."""
        allowed_providers = self.policy.privacy_provider_map.get(request.privacy_level, [])
        if provider not in allowed_providers:
            return False
        
        if runtime:
            allowed_runtimes = self.policy.privacy_runtime_map.get(request.privacy_level, [])
            if runtime not in allowed_runtimes:
                return False
        
        return True
    
    def _select_model_for_provider(self, provider: str, request: RoutingRequest) -> Optional[str]:
        """Select an appropriate model for the provider based on request."""
        provider_spec = self.registry.get_provider_spec(provider)
        if not provider_spec:
            return None
        
        # For now, return a simple default - this would be enhanced with actual model discovery
        if provider == "openai":
            if request.requires_vision:
                return "gpt-4o"
            elif request.task_type == TaskType.CODE:
                return "gpt-4o-mini"
            else:
                return "gpt-4o-mini"
        elif provider == "gemini":
            return "gemini-1.5-flash"
        elif provider == "deepseek":
            return "deepseek-chat"
        elif provider == "local":
            return "llama3.2:latest"
        elif provider == "huggingface":
            return "microsoft/DialoGPT-medium"
        else:
            return "default-model"
    
    def _calculate_confidence(self, request: RoutingRequest, provider: str, runtime: str, model_id: str = None) -> float:
        """Calculate confidence score for routing decision using advanced scoring."""
        try:
            from ai_karen_engine.integrations.confidence_scoring import get_confidence_scorer
            
            scorer = get_confidence_scorer()
            confidence, metadata = scorer.score_routing_decision(
                request=request,
                provider=provider,
                runtime=runtime,
                model_id=model_id or "default",
                policy=self.policy,
            )
            
            # Store metadata for debugging (could be returned in dry-run)
            if hasattr(self, '_last_confidence_metadata'):
                self._last_confidence_metadata = metadata
            
            return confidence
            
        except Exception as e:
            self.logger.warning(f"Advanced confidence scoring failed, using fallback: {e}")
            
            # Fallback to simple confidence calculation
            confidence = 0.5  # Base confidence
            
            # Boost confidence for exact matches
            if provider == self._get_policy_provider(request):
                confidence += 0.2
            if runtime == self._get_policy_runtime(request):
                confidence += 0.2
            
            # Boost for health
            if self._is_provider_healthy(provider):
                confidence += 0.1
            if self._is_runtime_healthy(runtime):
                confidence += 0.1
            
            return min(confidence, 1.0)
    
    def _build_fallback_chain(self, request: RoutingRequest) -> List[str]:
        """Build fallback chain for the request."""
        chain = []
        
        # Add policy fallbacks
        chain.extend(self.policy.fallback_providers)
        
        # Add local providers
        chain.extend(["local", "huggingface"])
        
        # Add degraded mode
        if self.degraded_mode_manager:
            chain.append("core_helpers")
        
        return list(dict.fromkeys(chain))  # Remove duplicates while preserving order
    
    def _estimate_cost(self, provider: str, model_id: str) -> Optional[float]:
        """Estimate cost for using this provider/model."""
        # Simplified cost estimation - would be enhanced with real pricing data
        if provider in ["local", "huggingface", "core_helpers"]:
            return 0.0
        elif provider == "openai":
            if "gpt-4" in model_id:
                return 0.03  # $0.03 per 1K tokens (rough estimate)
            else:
                return 0.002  # $0.002 per 1K tokens
        elif provider == "gemini":
            return 0.001  # $0.001 per 1K tokens
        elif provider == "deepseek":
            return 0.0002  # $0.0002 per 1K tokens
        else:
            return None
    
    def _estimate_latency(self, provider: str, runtime: str) -> Optional[float]:
        """Estimate latency for this provider/runtime combination."""
        # Simplified latency estimation in seconds
        if provider in ["openai", "gemini", "deepseek"]:
            return 1.5  # API latency
        elif runtime == "vllm":
            return 0.5  # Fast GPU inference
        elif runtime == "transformers":
            return 2.0  # Medium CPU/GPU inference
        elif runtime == "llama.cpp":
            return 1.0  # Efficient CPU inference
        elif runtime == "core_helpers":
            return 0.3  # Very fast but limited
        else:
            return None
    
    # Capability-aware routing methods
    
    def _filter_providers_by_capabilities(self, request: RoutingRequest, candidate_providers: List[str]) -> List[str]:
        """Filter providers based on capability requirements."""
        compatible_providers = []
        
        for provider in candidate_providers:
            if self._check_provider_capabilities(request, provider):
                compatible_providers.append(provider)
        
        return compatible_providers
    
    def _check_provider_capabilities(self, request: RoutingRequest, provider: str) -> bool:
        """Check if a provider supports the required capabilities."""
        provider_spec = self.registry.get_provider_spec(provider)
        if not provider_spec:
            return False
        
        validation = self._validate_provider_capabilities(request, provider_spec)
        return validation["valid"]
    
    def _validate_provider_capabilities(self, request: RoutingRequest, provider_spec: ProviderSpec) -> Dict[str, Any]:
        """Validate provider capabilities against request requirements."""
        validation_result = {
            "valid": True,
            "missing_capabilities": [],
            "supported_capabilities": list(provider_spec.capabilities),
            "fallback_suggestions": []
        }
        
        # Check streaming capability
        if request.requires_streaming and "streaming" not in provider_spec.capabilities:
            validation_result["valid"] = False
            validation_result["missing_capabilities"].append("streaming")
            validation_result["fallback_suggestions"].append("Remove streaming requirement")
        
        # Check function calling capability
        if request.requires_function_calling and "function_calling" not in provider_spec.capabilities:
            validation_result["valid"] = False
            validation_result["missing_capabilities"].append("function_calling")
            validation_result["fallback_suggestions"].append("Use regular chat without function calling")
        
        # Check vision capability
        if request.requires_vision and "vision" not in provider_spec.capabilities:
            validation_result["valid"] = False
            validation_result["missing_capabilities"].append("vision")
            validation_result["fallback_suggestions"].append("Use text-only mode")
        
        return validation_result
    
    def _create_capability_fallback_request(self, request: RoutingRequest) -> RoutingRequest:
        """Create a fallback request with reduced capability requirements."""
        # Create a copy of the request
        fallback_request = RoutingRequest(
            prompt=request.prompt,
            task_type=request.task_type,
            privacy_level=request.privacy_level,
            performance_req=request.performance_req,
            preferred_provider=request.preferred_provider,
            preferred_model=request.preferred_model,
            preferred_runtime=request.preferred_runtime,
            user_id=request.user_id,
            session_id=request.session_id,
            context_length=request.context_length,
            requires_streaming=request.requires_streaming,
            requires_function_calling=request.requires_function_calling,
            requires_vision=request.requires_vision,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            metadata=request.metadata.copy()
        )
        
        # Apply capability fallback in order of priority
        # Vision → text-only (highest priority fallback)
        if fallback_request.requires_vision:
            fallback_request.requires_vision = False
            fallback_request.metadata["capability_fallback"] = "vision_to_text_only"
            return fallback_request
        
        # Function calling → regular chat
        if fallback_request.requires_function_calling:
            fallback_request.requires_function_calling = False
            fallback_request.metadata["capability_fallback"] = "function_calling_to_regular_chat"
            return fallback_request
        
        # Streaming → non-streaming (lowest priority fallback)
        if fallback_request.requires_streaming:
            fallback_request.requires_streaming = False
            fallback_request.metadata["capability_fallback"] = "streaming_to_non_streaming"
            return fallback_request
        
        # No fallback possible
        return request
    
    def _get_capability_changes(self, original: RoutingRequest, fallback: RoutingRequest) -> str:
        """Get a description of capability changes for logging."""
        changes = []
        
        if original.requires_vision and not fallback.requires_vision:
            changes.append("vision → text-only")
        
        if original.requires_function_calling and not fallback.requires_function_calling:
            changes.append("function calling → regular chat")
        
        if original.requires_streaming and not fallback.requires_streaming:
            changes.append("streaming → non-streaming")
        
        return ", ".join(changes) if changes else "no changes"
    
    def _select_providers_by_capability_score(self, request: RoutingRequest, candidate_providers: List[str]) -> List[str]:
        """Select and rank providers by capability compatibility score."""
        provider_scores = []
        
        for provider in candidate_providers:
            if not self._is_provider_healthy(provider):
                continue
            
            provider_spec = self.registry.get_provider_spec(provider)
            if not provider_spec:
                continue
            
            score = self._calculate_capability_score(request, provider_spec)
            provider_scores.append((provider, score))
        
        # Sort by score (descending) and return provider names
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        return [provider for provider, score in provider_scores]
    
    def _calculate_capability_score(self, request: RoutingRequest, provider_spec: ProviderSpec) -> float:
        """Calculate capability compatibility score for a provider."""
        score = 0.0
        max_score = 0.0
        
        # Streaming capability (weight: 0.2)
        max_score += 0.2
        if request.requires_streaming:
            if "streaming" in provider_spec.capabilities:
                score += 0.2
        else:
            # Bonus for having streaming even if not required
            if "streaming" in provider_spec.capabilities:
                score += 0.1
        
        # Function calling capability (weight: 0.3)
        max_score += 0.3
        if request.requires_function_calling:
            if "function_calling" in provider_spec.capabilities:
                score += 0.3
        else:
            # Bonus for having function calling even if not required
            if "function_calling" in provider_spec.capabilities:
                score += 0.15
        
        # Vision capability (weight: 0.3)
        max_score += 0.3
        if request.requires_vision:
            if "vision" in provider_spec.capabilities:
                score += 0.3
        else:
            # Bonus for having vision even if not required
            if "vision" in provider_spec.capabilities:
                score += 0.15
        
        # Additional capabilities bonus (weight: 0.2)
        max_score += 0.2
        additional_capabilities = len(provider_spec.capabilities) - 3  # Subtract basic capabilities
        if additional_capabilities > 0:
            score += min(0.2, additional_capabilities * 0.05)
        
        # Normalize score
        return score / max_score if max_score > 0 else 0.0
    
    def record_routing_failure(self, provider: str, error_type: str, error_message: str, request_type: str, model: str = None):
        """Record routing failure for pattern analysis."""
        if self.failure_analyzer:
            try:
                self.failure_analyzer.record_failure(
                    provider=provider,
                    error_type=error_type,
                    error_message=error_message,
                    request_type=request_type,
                    model=model
                )
            except Exception as e:
                self.logger.warning(f"Failed to record routing failure: {e}")
        else:
            # Fallback logging when failure analyzer is not available
            self.logger.warning(f"Routing failure - Provider: {provider}, Type: {error_type}, Message: {error_message}")
    
    def get_capability_requirements(self, request: RoutingRequest) -> List[str]:
        """Get list of capability requirements from a routing request."""
        requirements = []
        
        if request.requires_streaming:
            requirements.append("streaming")
        if request.requires_function_calling:
            requirements.append("function_calling")
        if request.requires_vision:
            requirements.append("vision")
        
        return requirements
    
    def get_routing_diagnostics(self) -> Dict[str, Any]:
        """Get detailed diagnostics about routing decisions and failures."""
        diagnostics = {
            "routing_stats": self.routing_stats.copy(),
            "policy_info": {
                "name": self.policy.name,
                "description": self.policy.description,
                "privacy_weight": self.policy.privacy_weight,
                "performance_weight": self.policy.performance_weight,
                "cost_weight": self.policy.cost_weight,
                "availability_weight": self.policy.availability_weight,
            },
            "available_providers": [],
            "available_runtimes": [],
            "health_status": {},
            "failure_patterns": {},
        }
        
        # Get provider information
        for provider in self.registry.list_providers(healthy_only=False):
            provider_spec = self.registry.get_provider_spec(provider)
            health = self.registry.get_health_status(f"provider:{provider}")
            
            diagnostics["available_providers"].append({
                "name": provider,
                "healthy": self._is_provider_healthy(provider),
                "capabilities": list(provider_spec.capabilities) if provider_spec else [],
                "requires_api_key": provider_spec.requires_api_key if provider_spec else False,
                "health_status": health.status if health else "unknown",
            })
        
        # Get runtime information
        for runtime in self.registry.list_runtimes(healthy_only=False):
            runtime_spec = self.registry.get_runtime_spec(runtime)
            health = self.registry.get_health_status(f"runtime:{runtime}")
            
            diagnostics["available_runtimes"].append({
                "name": runtime,
                "healthy": self._is_runtime_healthy(runtime),
                "supports": runtime_spec.supports if runtime_spec else [],
                "requires_gpu": runtime_spec.requires_gpu if runtime_spec else False,
                "health_status": health.status if health else "unknown",
            })
        
        # Get failure patterns if available
        if self.failure_analyzer:
            try:
                diagnostics["failure_patterns"] = self.failure_analyzer.get_failure_summary()
            except Exception as e:
                diagnostics["failure_patterns"] = {"error": str(e)}
        
        return diagnostics
    
    # Analysis methods for dry-run functionality
    
    def _analyze_explicit_preference(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze explicit user preferences for dry-run with capability analysis."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "analysis": {},
            "capability_analysis": {},
        }
        
        if not (request.preferred_provider and request.preferred_model):
            result["issues"].append("No explicit preferences specified")
            return result
        
        # Check provider health
        provider_health = self.registry.get_health_status(f"provider:{request.preferred_provider}")
        result["analysis"]["provider_health"] = provider_health.status if provider_health else "unknown"
        
        if provider_health and provider_health.status not in ["healthy", "unknown"]:
            result["issues"].append(f"Preferred provider {request.preferred_provider} is unhealthy: {provider_health.status}")
            return result
        
        # Check provider existence
        provider_spec = self.registry.get_provider_spec(request.preferred_provider)
        if not provider_spec:
            result["issues"].append(f"Preferred provider {request.preferred_provider} not found")
            return result
        
        result["analysis"]["provider_capabilities"] = list(provider_spec.capabilities)
        
        # Analyze capability requirements
        capability_validation = self._validate_provider_capabilities(request, provider_spec)
        result["capability_analysis"] = {
            "required_capabilities": self.get_capability_requirements(request),
            "provider_capabilities": list(provider_spec.capabilities),
            "validation_result": capability_validation,
            "capability_score": self._calculate_capability_score(request, provider_spec),
        }
        
        if not capability_validation["valid"]:
            result["issues"].extend([f"Missing capability: {cap}" for cap in capability_validation["missing_capabilities"]])
            
            # Suggest capability fallback
            fallback_request = self._create_capability_fallback_request(request)
            if fallback_request != request:
                result["capability_analysis"]["fallback_suggestion"] = self._get_capability_changes(request, fallback_request)
            
            return result
        
        # Check privacy compliance
        if not self._check_privacy_compliance(request, request.preferred_provider, request.preferred_runtime):
            result["issues"].append("Preferred provider/runtime does not meet privacy requirements")
            return result
        
        # If we get here, the preference is viable
        result["viable"] = True
        result["decision"] = {
            "provider": request.preferred_provider,
            "model": request.preferred_model,
            "runtime": request.preferred_runtime or "auto-selected",
        }
        
        return result
    
    def _analyze_policy_selection(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze policy-based selection for dry-run with capability analysis."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "policy_analysis": {},
            "capability_analysis": {},
        }
        
        # Analyze policy preferences
        preferred_provider = self._get_policy_provider(request)
        preferred_runtime = self._get_policy_runtime(request)
        
        result["policy_analysis"] = {
            "task_based_provider": self.policy.task_provider_map.get(request.task_type),
            "performance_based_provider": self.policy.performance_provider_map.get(request.performance_req),
            "selected_provider": preferred_provider,
            "task_based_runtime": self.policy.task_runtime_map.get(request.task_type),
            "performance_based_runtime": self.policy.performance_runtime_map.get(request.performance_req),
            "selected_runtime": preferred_runtime,
            "privacy_constraints": {
                "allowed_providers": self.policy.privacy_provider_map.get(request.privacy_level, []),
                "allowed_runtimes": self.policy.privacy_runtime_map.get(request.privacy_level, []),
            }
        }
        
        # Analyze capability compatibility
        provider_spec = self.registry.get_provider_spec(preferred_provider)
        if provider_spec:
            capability_validation = self._validate_provider_capabilities(request, provider_spec)
            result["capability_analysis"] = {
                "required_capabilities": self.get_capability_requirements(request),
                "provider_capabilities": list(provider_spec.capabilities),
                "validation_result": capability_validation,
                "capability_score": self._calculate_capability_score(request, provider_spec),
            }
            
            if not capability_validation["valid"]:
                result["issues"].extend([f"Missing capability: {cap}" for cap in capability_validation["missing_capabilities"]])
                
                # Suggest capability fallback
                fallback_request = self._create_capability_fallback_request(request)
                if fallback_request != request:
                    result["capability_analysis"]["fallback_suggestion"] = self._get_capability_changes(request, fallback_request)
        
        # Check privacy compliance
        if not self._check_privacy_compliance(request, preferred_provider, preferred_runtime):
            result["issues"].append("Policy selection does not meet privacy requirements")
            return result
        
        # Check health
        if not self._is_provider_healthy(preferred_provider):
            result["issues"].append(f"Policy-selected provider {preferred_provider} is unhealthy")
            return result
        
        if not self._is_runtime_healthy(preferred_runtime):
            result["issues"].append(f"Policy-selected runtime {preferred_runtime} is unhealthy")
            return result
        
        # Check capability compatibility
        if provider_spec and not self._check_provider_capabilities(request, preferred_provider):
            result["issues"].append(f"Policy-selected provider {preferred_provider} lacks required capabilities")
            return result
        
        result["viable"] = True
        result["decision"] = {
            "provider": preferred_provider,
            "runtime": preferred_runtime,
            "model": self._select_model_for_provider(preferred_provider, request),
        }
        
        return result
    
    def _analyze_system_defaults(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze system default selection for dry-run."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "analysis": {},
        }
        
        healthy_providers = [
            p for p in self.registry.list_providers(healthy_only=True)
            if self._check_privacy_compliance(request, p, None)
        ]
        
        result["analysis"]["healthy_providers"] = healthy_providers
        
        if not healthy_providers:
            result["issues"].append("No healthy providers available that meet privacy requirements")
            return result
        
        selected_provider = healthy_providers[0]
        model_id = self._select_model_for_provider(selected_provider, request)
        
        if not model_id:
            result["issues"].append(f"No suitable model found for provider {selected_provider}")
            return result
        
        result["viable"] = True
        result["decision"] = {
            "provider": selected_provider,
            "model": model_id,
            "runtime": "auto-selected",
        }
        
        return result
    
    def _analyze_local_fallback(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze local fallback selection for dry-run."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "analysis": {},
        }
        
        local_providers = ["local", "huggingface"]
        available_locals = [p for p in local_providers if self._is_provider_healthy(p)]
        
        result["analysis"]["available_local_providers"] = available_locals
        
        if not available_locals:
            result["issues"].append("No healthy local providers available")
            return result
        
        selected_provider = available_locals[0]
        model_id = self._select_model_for_provider(selected_provider, request)
        
        result["viable"] = True
        result["decision"] = {
            "provider": selected_provider,
            "model": model_id,
            "runtime": "llama.cpp",
        }
        
        return result
    
    def _analyze_degraded_mode(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze degraded mode selection for dry-run."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "analysis": {},
        }
        
        if not self.degraded_mode_manager:
            result["issues"].append("Degraded mode is disabled")
            return result
        
        result["analysis"]["degraded_mode_status"] = self.degraded_mode_manager.get_status().is_active
        
        result["viable"] = True
        result["decision"] = {
            "provider": "core_helpers",
            "model": "tinyllama+distilbert+spacy",
            "runtime": "core_helpers",
        }
        
        return result
    
    def _generate_alternatives(self, request: RoutingRequest) -> List[Dict[str, Any]]:
        """Generate alternative routing options for dry-run."""
        alternatives = []
        
        # Get all healthy providers
        healthy_providers = self.registry.list_providers(healthy_only=True)
        
        for provider in healthy_providers:
            if not self._check_privacy_compliance(request, provider, None):
                continue
            
            model_id = self._select_model_for_provider(provider, request)
            if not model_id:
                continue
            
            # Find compatible runtimes
            model_meta = ModelMetadata(id=model_id, name=model_id, provider=provider)
            compatible_runtimes = self.registry.compatible_runtimes(model_meta)
            
            for runtime in compatible_runtimes:
                if not self._is_runtime_healthy(runtime):
                    continue
                
                if not self._check_privacy_compliance(request, provider, runtime):
                    continue
                
                confidence = self._calculate_confidence(request, provider, runtime)
                
                alternatives.append({
                    "provider": provider,
                    "runtime": runtime,
                    "model": model_id,
                    "confidence": confidence,
                    "estimated_cost": self._estimate_cost(provider, model_id),
                    "estimated_latency": self._estimate_latency(provider, runtime),
                    "privacy_compliant": True,
                })
        
        # Sort by confidence
        alternatives.sort(key=lambda x: x["confidence"], reverse=True)
        
        return alternatives[:5]  # Return top 5 alternatives
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics including health information."""
        stats = self.routing_stats.copy()
        
        # Add health information if available
        if self.health_monitor:
            health_summary = self.health_monitor.get_health_summary()
            stats["health_summary"] = health_summary
            stats["recent_health_events"] = len(self.health_monitor.get_recent_events(hours=1))
            stats["recent_failovers"] = len(self.health_monitor.get_recent_failovers(hours=1))
        
        # Add policy information
        stats["active_policy"] = self.policy.name
        stats["policy_weights"] = {
            "privacy": self.policy.privacy_weight,
            "performance": self.policy.performance_weight,
            "cost": self.policy.cost_weight,
            "availability": self.policy.availability_weight,
        }
        
        return stats
    
    def reset_routing_stats(self) -> None:
        """Reset routing statistics."""
        self.routing_stats = {
            "total_requests": 0,
            "successful_routes": 0,
            "fallback_routes": 0,
            "degraded_routes": 0,
            "failed_routes": 0,
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components."""
        if self.health_monitor:
            return {
                "summary": self.health_monitor.get_health_summary(),
                "healthy_providers": self.health_monitor.get_healthy_components("provider"),
                "healthy_runtimes": self.health_monitor.get_healthy_components("runtime"),
                "unhealthy_components": self.health_monitor.get_unhealthy_components(),
                "recent_events": self.health_monitor.get_recent_events(hours=24),
                "recent_failovers": self.health_monitor.get_recent_failovers(hours=24),
            }
        else:
            # Fallback to registry health check
            all_health = self.registry.health_check_all()
            healthy_providers = []
            healthy_runtimes = []
            unhealthy_components = {}
            
            for component, status in all_health.items():
                if status.status in ["healthy", "unknown"]:
                    if component.startswith("provider:"):
                        healthy_providers.append(component)
                    elif component.startswith("runtime:"):
                        healthy_runtimes.append(component)
                else:
                    unhealthy_components[component] = status
            
            return {
                "summary": {
                    "total_components": len(all_health),
                    "healthy_components": len(healthy_providers) + len(healthy_runtimes),
                    "unhealthy_components": len(unhealthy_components),
                },
                "healthy_providers": healthy_providers,
                "healthy_runtimes": healthy_runtimes,
                "unhealthy_components": unhealthy_components,
                "recent_events": [],
                "recent_failovers": [],
            }
    
    def update_policy(self, policy: RoutingPolicy) -> None:
        """Update the routing policy."""
        old_policy = self.policy.name
        self.policy = policy
        self.logger.info(f"Updated routing policy from '{old_policy}' to '{policy.name}'")
    
    def get_policy_info(self) -> Dict[str, Any]:
        """Get information about the current routing policy."""
        return {
            "name": self.policy.name,
            "description": self.policy.description,
            "weights": {
                "privacy": self.policy.privacy_weight,
                "performance": self.policy.performance_weight,
                "cost": self.policy.cost_weight,
                "availability": self.policy.availability_weight,
            },
            "fallback_providers": self.policy.fallback_providers,
            "fallback_runtimes": self.policy.fallback_runtimes,
        }
    
    def analyze_failure_patterns(self, time_window_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Analyze failure patterns for the specified time window.
        
        Args:
            time_window_hours: Time window for analysis in hours
            
        Returns:
            Failure analysis results or None if analyzer not available
        """
        if not self.failure_analyzer:
            self.logger.warning("Failure pattern analyzer not available")
            return None
        
        try:
            analysis = self.failure_analyzer.analyze_failure_patterns(time_window_hours)
            
            # Convert to dictionary for JSON serialization
            return {
                "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
                "time_window_hours": time_window_hours,
                "total_failures": analysis.total_failures,
                "unique_providers_affected": analysis.unique_providers_affected,
                "detected_patterns": [
                    {
                        "pattern_type": pattern.pattern_type.value,
                        "severity": pattern.severity.value,
                        "affected_providers": pattern.affected_providers,
                        "failure_count": pattern.failure_count,
                        "time_span_hours": pattern.time_span.total_seconds() / 3600,
                        "confidence": pattern.confidence,
                        "description": pattern.description,
                        "recommendations": pattern.recommendations
                    }
                    for pattern in analysis.detected_patterns
                ],
                "provider_metrics": {
                    provider: {
                        "total_requests": metrics.total_requests,
                        "successful_requests": metrics.successful_requests,
                        "failed_requests": metrics.failed_requests,
                        "success_rate": metrics.success_rate,
                        "average_response_time": metrics.average_response_time,
                        "consecutive_failures": metrics.consecutive_failures,
                        "is_disabled": metrics.is_disabled,
                        "disable_reason": metrics.disable_reason,
                        "last_failure": metrics.last_failure.isoformat() if metrics.last_failure else None
                    }
                    for provider, metrics in analysis.provider_metrics.items()
                },
                "most_failed_providers": analysis.most_failed_providers,
                "common_failure_reasons": analysis.common_failure_reasons,
                "recovery_success_rate": analysis.recovery_success_rate,
                "recommendations": analysis.recommendations,
                "disabled_providers": analysis.disabled_providers
            }
            
        except Exception as e:
            self.logger.error(f"Failure pattern analysis failed: {e}")
            return None
    
    def get_failure_statistics(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive failure statistics."""
        if not self.failure_analyzer:
            return None
        
        try:
            return self.failure_analyzer.get_failure_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get failure statistics: {e}")
            return None
    
    def disable_provider(self, provider: str, reason: str) -> bool:
        """
        Manually disable a provider.
        
        Args:
            provider: Provider to disable
            reason: Reason for disabling
            
        Returns:
            True if provider was disabled successfully
        """
        if not self.failure_analyzer:
            self.logger.warning("Cannot disable provider - failure analyzer not available")
            return False
        
        try:
            success = self.failure_analyzer.disable_provider(provider, reason, manual=True)
            if success:
                self.logger.info(f"Provider {provider} disabled manually: {reason}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to disable provider {provider}: {e}")
            return False
    
    def enable_provider(self, provider: str) -> bool:
        """
        Manually enable a previously disabled provider.
        
        Args:
            provider: Provider to enable
            
        Returns:
            True if provider was enabled successfully
        """
        if not self.failure_analyzer:
            self.logger.warning("Cannot enable provider - failure analyzer not available")
            return False
        
        try:
            success = self.failure_analyzer.enable_provider(provider)
            if success:
                self.logger.info(f"Provider {provider} enabled manually")
            return success
        except Exception as e:
            self.logger.error(f"Failed to enable provider {provider}: {e}")
            return False
    
    def is_provider_disabled(self, provider: str) -> bool:
        """Check if a provider is currently disabled."""
        if not self.failure_analyzer:
            return False
        
        try:
            return self.failure_analyzer.is_provider_disabled(provider)
        except Exception as e:
            self.logger.error(f"Failed to check if provider {provider} is disabled: {e}")
            return False
    
    def record_routing_failure(self, provider: str, error_type: str, error_message: str,
                              request_type: str, model: Optional[str] = None,
                              runtime: Optional[str] = None) -> None:
        """
        Record a routing failure for pattern analysis.
        
        Args:
            provider: Name of the failed provider
            error_type: Type/category of the error
            error_message: Detailed error message
            request_type: Type of request that failed
            model: Model that was being used (if applicable)
            runtime: Runtime that was being used (if applicable)
        """
        if not self.failure_analyzer:
            return
        
        try:
            self.failure_analyzer.record_failure(
                provider=provider,
                error_type=error_type,
                error_message=error_message,
                request_type=request_type,
                model=model,
                runtime=runtime
            )
        except Exception as e:
            self.logger.error(f"Failed to record routing failure: {e}")
    
    def record_routing_success(self, provider: str, response_time: float,
                              request_type: str, model: Optional[str] = None,
                              runtime: Optional[str] = None) -> None:
        """
        Record a successful routing for pattern analysis.
        
        Args:
            provider: Name of the successful provider
            response_time: Response time in seconds
            request_type: Type of request that succeeded
            model: Model that was used (if applicable)
            runtime: Runtime that was used (if applicable)
        """
        if not self.failure_analyzer:
            return
        
        try:
            self.failure_analyzer.record_success(
                provider=provider,
                response_time=response_time,
                request_type=request_type,
                model=model,
                runtime=runtime
            )
        except Exception as e:
            self.logger.error(f"Failed to record routing success: {e}")


# Backward compatibility - keep the old LLMRouter class as a wrapper
class LLMRouter:
    """Legacy LLM router for backward compatibility."""
    
    def __init__(self, registry=None, local_model: str = "llama3.2:latest"):
        self.intelligent_router = IntelligentLLMRouter(registry=registry)
        self.local_model = local_model
        self.logger = logging.getLogger("kari.llm_router")
        self.degraded_mode_manager = get_degraded_mode_manager()
        self.consecutive_failures = 0
        self.max_failures_before_degraded = 3
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using intelligent routing."""
        # Convert legacy kwargs to RoutingRequest
        request = RoutingRequest(
            prompt=prompt,
            task_type=TaskType.CHAT,  # Default
            privacy_level=PrivacyLevel.PUBLIC,  # Default
            performance_req=PerformanceRequirement.INTERACTIVE,  # Default
            preferred_provider=kwargs.get("provider"),
            preferred_model=kwargs.get("model"),
            requires_streaming=kwargs.get("stream", False),
            user_id=kwargs.get("user_id"),
            metadata=kwargs,
        )
        
        try:
            decision = self.intelligent_router.route(request)
            
            # Here you would actually call the selected provider/runtime
            # For now, return a placeholder response
            return f"Generated response using {decision['provider']} with {decision['model_id']} on {decision['runtime']}"
            
        except Exception as e:
            self.logger.error(f"Intelligent routing failed: {e}")
            
            # Fallback to degraded mode
            if self.degraded_mode_manager:
                try:
                    response = await self.degraded_mode_manager.generate_degraded_response(prompt, **kwargs)
                    return response.get("content", "I apologize, but I'm experiencing technical difficulties.")
                except Exception as degraded_error:
                    self.logger.error(f"Even degraded mode failed: {degraded_error}")
            
            raise RuntimeError("All LLM generation methods failed") from e
    
    def check_provider_health(self) -> Dict[str, bool]:
        """Check health of all providers."""
        health_results = self.intelligent_router.registry.health_check_all()
        return {
            component.replace("provider:", ""): status.status == "healthy"
            for component, status in health_results.items()
            if component.startswith("provider:")
        }
    
    def record_routing_failure(self, provider: str, error_type: str, error_message: str, 
                             request_type: str, model: Optional[str] = None) -> None:
        """Record a routing failure for pattern analysis."""
        if self.failure_analyzer:
            self.failure_analyzer.record_failure(
                provider=provider,
                error_type=error_type,
                error_message=error_message,
                request_type=request_type,
                model=model
            )
        
        # Also record in partial failure handler
        if self.partial_failure_handler:
            from ai_karen_engine.integrations.partial_failure_handler import FailureType
            
            # Map error types to FailureType enum
            failure_type_map = {
                "authentication_error": FailureType.AUTHENTICATION_ERROR,
                "rate_limit_error": FailureType.RATE_LIMIT_ERROR,
                "network_error": FailureType.NETWORK_ERROR,
                "timeout_error": FailureType.TIMEOUT_ERROR,
                "provider_unavailable": FailureType.PROVIDER_UNAVAILABLE,
                "model_unavailable": FailureType.MODEL_UNAVAILABLE,
                "capability_missing": FailureType.CAPABILITY_MISSING,
                "configuration_error": FailureType.CONFIGURATION_ERROR,
                "resource_error": FailureType.RESOURCE_ERROR,
            }
            
            failure_type = failure_type_map.get(error_type, FailureType.PROVIDER_UNAVAILABLE)
            
            self.partial_failure_handler.record_failure(
                provider=provider,
                model=model,
                failure_type=failure_type,
                error_message=error_message,
                request_type=request_type
            )
    
    def route_with_capability_requirements(self, request: RoutingRequest, 
                                         capability_requirements: Optional[Any] = None) -> RouteDecision:
        """
        Route a request with specific capability requirements and graceful degradation.
        
        This method implements capability-based routing that routes requests to providers
        with required features, with automatic capability fallback when needed.
        
        Args:
            request: The routing request
            capability_requirements: CapabilityRequirement object specifying needed capabilities
            
        Returns:
            RouteDecision with capability-aware routing information
        """
        if not self.capability_router or not capability_requirements:
            # Fall back to standard routing if capability router not available
            return self.route_with_fallback(request)
        
        try:
            from ai_karen_engine.integrations.capability_router import RoutingCapabilityRequest
            
            # Create capability-aware routing request
            cap_request = RoutingCapabilityRequest(
                original_request=request,
                capability_requirements=capability_requirements,
                allow_capability_degradation=True,
                max_degradation_steps=3
            )
            
            # Attempt capability-aware routing
            cap_result = self.capability_router.route_with_capabilities(cap_request)
            
            if cap_result.success:
                # Convert capability routing result to standard RouteDecision
                decision = RouteDecision(
                    provider=cap_result.provider,
                    runtime=cap_result.runtime or "default",
                    model_id=cap_result.model or "default",
                    reason=cap_result.routing_reason or "Capability-aware routing successful",
                    confidence=0.9 if not cap_result.fallback_applied else 0.7,
                    fallback_chain=[],
                    estimated_cost=None,
                    estimated_latency=None,
                    privacy_compliant=True,
                    capabilities=list(cap_result.achieved_capabilities)
                )
                
                # Add degradation information to reason if applicable
                if cap_result.degraded_capabilities:
                    degraded_caps = [cap.value for cap in cap_result.degraded_capabilities]
                    decision["reason"] += f" (degraded capabilities: {degraded_caps})"
                
                self.logger.info(f"Capability-aware routing successful: {cap_result.provider}")
                return decision
            else:
                self.logger.warning("Capability-aware routing failed, falling back to standard routing")
                return self.route_with_fallback(request)
                
        except Exception as e:
            self.logger.error(f"Capability-aware routing failed with error: {e}")
            return self.route_with_fallback(request)
    
    def attempt_model_fallback_within_provider(self, provider: str, failed_model: str, 
                                             request: RoutingRequest) -> Optional[str]:
        """
        Attempt to find a fallback model within the same provider when a specific model fails.
        
        This implements model-level fallbacks within providers when specific models are unavailable.
        
        Args:
            provider: Name of the provider
            failed_model: Model that failed
            request: Original routing request for context
            
        Returns:
            ID of fallback model, or None if no suitable fallback found
        """
        if not self.model_availability_manager:
            self.logger.warning("Model availability manager not available for model fallback")
            return None
        
        try:
            # Attempt model fallback using the availability manager
            fallback_model = self.model_availability_manager.attempt_model_fallback(
                provider=provider,
                failed_model=failed_model,
                request_type=request.task_type.value if hasattr(request, 'task_type') else None
            )
            
            if fallback_model:
                self.logger.info(f"Found model fallback within {provider}: {failed_model} → {fallback_model}")
                return fallback_model
            else:
                self.logger.debug(f"No model fallback found within {provider} for {failed_model}")
                return None
                
        except Exception as e:
            self.logger.error(f"Model fallback attempt failed: {e}")
            return None
    
    def get_isolated_providers(self) -> List[str]:
        """
        Get list of currently isolated providers to prevent cascading failures.
        
        Returns:
            List of provider names that are currently isolated
        """
        if not self.partial_failure_handler:
            return []
        
        try:
            isolated_providers = []
            available_providers = self.registry.list_providers(healthy_only=False)
            
            for provider in available_providers:
                if self.partial_failure_handler.is_provider_isolated(provider):
                    isolated_providers.append(provider)
            
            return isolated_providers
            
        except Exception as e:
            self.logger.error(f"Failed to get isolated providers: {e}")
            return []
    
    def check_provider_isolation_status(self, provider: str) -> Dict[str, Any]:
        """
        Check the isolation status of a specific provider.
        
        Args:
            provider: Name of the provider to check
            
        Returns:
            Dictionary with isolation status information
        """
        if not self.partial_failure_handler:
            return {"isolated": False, "reason": "Partial failure handler not available"}
        
        try:
            is_isolated = self.partial_failure_handler.is_provider_isolated(provider)
            
            status_info = {"isolated": is_isolated}
            
            if provider in self.partial_failure_handler.provider_isolation:
                isolation_status = self.partial_failure_handler.provider_isolation[provider]
                status_info.update({
                    "failure_count": isolation_status.failure_count,
                    "last_failure": isolation_status.last_failure.isoformat() if isolation_status.last_failure else None,
                    "isolation_reason": isolation_status.isolation_reason,
                    "isolation_timestamp": isolation_status.isolation_timestamp.isoformat() if isolation_status.isolation_timestamp else None,
                    "recovery_attempts": isolation_status.recovery_attempts,
                    "next_recovery_check": isolation_status.next_recovery_check.isoformat() if isolation_status.next_recovery_check else None
                })
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"Failed to check provider isolation status: {e}")
            return {"isolated": False, "error": str(e)}
    
    def _detect_capability_requirements(self, request: RoutingRequest) -> Optional[Any]:
        """
        Auto-detect capability requirements based on request attributes.
        
        Args:
            request: The routing request to analyze
            
        Returns:
            CapabilityRequirement object or None if no special requirements detected
        """
        try:
            from ai_karen_engine.integrations.partial_failure_handler import CapabilityRequirement, CapabilityType
            
            required_capabilities = set()
            preferred_capabilities = set()
            
            # Check for streaming requirement
            if getattr(request, 'requires_streaming', False):
                required_capabilities.add(CapabilityType.STREAMING)
            else:
                preferred_capabilities.add(CapabilityType.STREAMING)
            
            # Check for function calling requirement
            if getattr(request, 'requires_function_calling', False):
                required_capabilities.add(CapabilityType.FUNCTION_CALLING)
            
            # Check for vision requirement
            if getattr(request, 'requires_vision', False):
                required_capabilities.add(CapabilityType.VISION)
            
            # Check task type for capability hints
            if hasattr(request, 'task_type'):
                if request.task_type == TaskType.CODE:
                    preferred_capabilities.add(CapabilityType.CODE_GENERATION)
                elif request.task_type == TaskType.REASONING:
                    preferred_capabilities.add(CapabilityType.REASONING)
                elif request.task_type == TaskType.EMBEDDING:
                    required_capabilities.add(CapabilityType.EMBEDDINGS)
            
            # Only create capability requirements if we detected some requirements
            if required_capabilities or preferred_capabilities:
                return CapabilityRequirement(
                    required=required_capabilities,
                    preferred=preferred_capabilities
                )
            
            return None
            
        except ImportError:
            self.logger.debug("Capability detection not available")
            return None
        except Exception as e:
            self.logger.error(f"Error detecting capability requirements: {e}")
            return None
    
    def validate_provider_capabilities(self, provider: str, requirements: Any) -> Dict[str, Any]:
        """
        Validate that a provider meets specific capability requirements.
        
        Args:
            provider: Name of the provider to validate
            requirements: CapabilityRequirement object
            
        Returns:
            Dictionary with validation results
        """
        if not self.capability_router:
            return {"valid": False, "error": "Capability router not available"}
        
        try:
            check_result = self.capability_router.check_provider_capabilities(provider, requirements)
            
            return {
                "valid": check_result.has_required_capabilities,
                "provider": check_result.provider,
                "missing_capabilities": [cap.value for cap in check_result.missing_capabilities],
                "available_capabilities": [cap.value for cap in check_result.available_capabilities],
                "degradation_options": check_result.degradation_options
            }
            
        except Exception as e:
            self.logger.error(f"Provider capability validation failed: {e}")
            return {"valid": False, "error": str(e)}
    
    def get_capability_alternatives(self, original_requirements: Any) -> List[Dict[str, Any]]:
        """
        Get alternative capability requirements through graceful degradation.
        
        Args:
            original_requirements: Original CapabilityRequirement object
            
        Returns:
            List of alternative capability requirements
        """
        if not self.capability_router:
            return []
        
        try:
            alternatives = self.capability_router.get_capability_alternatives(original_requirements)
            
            return [
                {
                    "required": [cap.value for cap in alt.required],
                    "preferred": [cap.value for cap in alt.preferred],
                    "fallback_acceptable": [cap.value for cap in alt.fallback_acceptable]
                }
                for alt in alternatives
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get capability alternatives: {e}")
            return []
    
    def get_model_availability_status(self, provider: str, model_id: str) -> Dict[str, Any]:
        """
        Get availability status for a specific model within a provider.
        
        Args:
            provider: Name of the provider
            model_id: ID of the model to check
            
        Returns:
            Dictionary with model availability information
        """
        if not self.model_availability_manager:
            return {"status": "unknown", "error": "Model availability manager not available"}
        
        try:
            health_check = self.model_availability_manager.check_model_availability(provider, model_id)
            
            return {
                "model_id": health_check.model_id,
                "provider": health_check.provider,
                "status": health_check.status.value,
                "last_check": health_check.last_check.isoformat(),
                "response_time": health_check.response_time,
                "error_message": health_check.error_message,
                "success_rate": health_check.success_rate,
                "consecutive_failures": health_check.consecutive_failures,
                "last_successful_request": health_check.last_successful_request.isoformat() if health_check.last_successful_request else None,
                "capabilities_verified": list(health_check.capabilities_verified)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get model availability status: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_available_models_for_provider(self, provider: str, 
                                        selection_criteria: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Get list of available models for a provider with optional filtering.
        
        Args:
            provider: Name of the provider
            selection_criteria: Optional criteria for filtering models
            
        Returns:
            List of available model IDs
        """
        if not self.model_availability_manager:
            self.logger.warning("Model availability manager not available")
            try:
                # Fallback to registry
                models = self.registry.list_models(provider=provider)
                return [m.id for m in models]
            except Exception as e:
                self.logger.error(f"Failed to get models from registry: {e}")
                return []
        
        try:
            # Convert selection criteria dict to ModelSelectionCriteria if provided
            criteria = None
            if selection_criteria:
                from ai_karen_engine.integrations.model_availability_manager import ModelSelectionCriteria, CapabilityType
                
                criteria = ModelSelectionCriteria(
                    prefer_faster_models=selection_criteria.get("prefer_faster_models", True),
                    prefer_higher_success_rate=selection_criteria.get("prefer_higher_success_rate", True),
                    max_acceptable_response_time=selection_criteria.get("max_acceptable_response_time"),
                    min_acceptable_success_rate=selection_criteria.get("min_acceptable_success_rate", 0.8),
                    request_type=selection_criteria.get("request_type"),
                    capability_requirements=set(selection_criteria.get("capability_requirements", []))
                )
            
            return self.model_availability_manager.get_available_models(provider, criteria)
            
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []
    
    def select_best_model_for_provider(self, provider: str, model_options: List[str],
                                     selection_criteria: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Select the best model from available options for a provider.
        
        Args:
            provider: Name of the provider
            model_options: List of model IDs to choose from
            selection_criteria: Optional criteria for selection
            
        Returns:
            ID of the best model, or None if no suitable model found
        """
        if not self.model_availability_manager:
            self.logger.warning("Model availability manager not available, returning first option")
            return model_options[0] if model_options else None
        
        try:
            # Convert selection criteria dict to ModelSelectionCriteria if provided
            criteria = None
            if selection_criteria:
                from ai_karen_engine.integrations.model_availability_manager import ModelSelectionCriteria
                
                criteria = ModelSelectionCriteria(
                    prefer_faster_models=selection_criteria.get("prefer_faster_models", True),
                    prefer_higher_success_rate=selection_criteria.get("prefer_higher_success_rate", True),
                    max_acceptable_response_time=selection_criteria.get("max_acceptable_response_time"),
                    min_acceptable_success_rate=selection_criteria.get("min_acceptable_success_rate", 0.8),
                    request_type=selection_criteria.get("request_type"),
                    capability_requirements=set(selection_criteria.get("capability_requirements", []))
                )
            
            return self.model_availability_manager.select_best_model(provider, model_options, criteria)
            
        except Exception as e:
            self.logger.error(f"Failed to select best model: {e}")
            return model_options[0] if model_options else None
    
    def record_model_performance(self, provider: str, model_id: str, 
                               response_time: float, success: bool,
                               request_type: Optional[str] = None) -> None:
        """
        Record performance metrics for a model to improve future selection.
        
        Args:
            provider: Name of the provider
            model_id: ID of the model
            response_time: Response time in seconds
            success: Whether the request was successful
            request_type: Type of request for categorized metrics
        """
        if not self.model_availability_manager:
            self.logger.debug("Model availability manager not available for performance recording")
            return
        
        try:
            self.model_availability_manager.record_model_performance(
                provider=provider,
                model_id=model_id,
                response_time=response_time,
                success=success,
                request_type=request_type
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record model performance: {e}")
    
    def get_model_performance_report(self, provider: Optional[str] = None,
                                   hours_back: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance report for models.
        
        Args:
            provider: Specific provider to report on (None for all)
            hours_back: Number of hours back to include in report (None for all time)
            
        Returns:
            Dictionary with performance report
        """
        if not self.model_availability_manager:
            return {"error": "Model availability manager not available"}
        
        try:
            from datetime import timedelta
            
            time_window = timedelta(hours=hours_back) if hours_back else None
            
            return self.model_availability_manager.get_model_performance_report(
                provider=provider,
                time_window=time_window
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get model performance report: {e}")
            return {"error": str(e)}


# Backward compatibility - keep the old LLMProfileRouter class
class LLMProfileRouter:
    """Legacy profile router for backward compatibility."""
    
    def __init__(self, profile: str = "default", config_path: Path = DEFAULT_PATH):
        self.profile = profile
        self.config_path = config_path
        self.profiles = self._load_profiles()
        self.intelligent_router = IntelligentLLMRouter()
    
    def _load_profiles(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        data = _load_yaml(self.config_path)
        return data.get("profiles", {}) if isinstance(data, dict) else {}
    
    def select_provider(self, task_intent: str) -> str:
        """Select provider based on profile configuration."""
        prof = self.profiles.get(self.profile, {})
        provider = prof.get("providers", {}).get(task_intent)
        if provider:
            return provider
        fb = prof.get("fallback")
        if fb:
            FALLBACK_RATE.labels(profile=self.profile).inc()
            return fb
        raise RuntimeError(f"No provider for intent '{task_intent}' and no fallback")
    
    def invoke(self, llm_utils, prompt: str, task_intent: str, preferred_provider: Optional[str] = None, preferred_model: Optional[str] = None, **kwargs) -> str:
        """Invoke LLM using intelligent routing."""
        # Convert to new routing request format
        task_type_map = {
            "chat": TaskType.CHAT,
            "code": TaskType.CODE,
            "reasoning": TaskType.REASONING,
            "embedding": TaskType.EMBEDDING,
            "summarization": TaskType.SUMMARIZATION,
            "translation": TaskType.TRANSLATION,
            "creative": TaskType.CREATIVE,
            "analysis": TaskType.ANALYSIS,
        }
        
        request = RoutingRequest(
            prompt=prompt,
            task_type=task_type_map.get(task_intent, TaskType.CHAT),
            preferred_provider=preferred_provider,
            preferred_model=preferred_model,
            metadata=kwargs,
        )
        
        start = time.time()
        try:
            decision = self.intelligent_router.route(request)
            
            # Here you would actually call the selected provider
            # For now, use the legacy llm_utils interface
            result = llm_utils.generate_text(prompt, provider=decision["provider"], model=decision["model_id"], **kwargs)
            return result
            
        finally:
            model_label = f"{decision['provider']}:{decision['model_id']}" if 'decision' in locals() else "unknown"
            MODEL_INVOCATIONS_TOTAL.labels(model=model_label).inc()
            AVG_RESPONSE_TIME.labels(model=model_label).observe(time.time() - start)


# Convenience functions for easy access
def create_intelligent_router(policy: Optional[RoutingPolicy] = None) -> IntelligentLLMRouter:
    """Create an intelligent LLM router with optional custom policy."""
    return IntelligentLLMRouter(policy=policy)


def route_request(request: RoutingRequest) -> RouteDecision:
    """Route a single request using the default intelligent router."""
    router = IntelligentLLMRouter()
    return router.route(request)


def dry_run_request(request: RoutingRequest) -> Dict[str, Any]:
    """Perform a dry run of routing for debugging."""
    router = IntelligentLLMRouter()
    return router.dry_run(request)


# Export all classes and functions
__all__ = [
    "TaskType",
    "PrivacyLevel", 
    "PerformanceRequirement",
    "RoutingRequest",
    "RouteDecision",
    "RoutingPolicy",
    "IntelligentLLMRouter",
    "LLMRouter",
    "LLMProfileRouter",
    "create_intelligent_router",
    "route_request",
    "dry_run_request",
]