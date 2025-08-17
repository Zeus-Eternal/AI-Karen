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

from ai_karen_engine.integrations.registry import get_registry, ModelMetadata
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

MODEL_INVOCATIONS_TOTAL = (
    Counter(
        "model_invocations_total",
        "Total LLM model invocations",
        ["model"],
    )
    if METRICS_ENABLED
    else Counter()
)
FALLBACK_RATE = (
    Counter(
        "fallback_rate",
        "Fallback invocations",
        ["profile"],
    )
    if METRICS_ENABLED
    else Counter()
)
AVG_RESPONSE_TIME = (
    Histogram(
        "avg_response_time",
        "LLM response time",
        ["model"],
    )
    if METRICS_ENABLED
    else Histogram()
)

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
        self.routing_stats["total_requests"] += 1
        
        try:
            # Step 1: Check explicit user preferences
            if request.preferred_provider and request.preferred_model:
                decision = self._try_explicit_preference(request)
                if decision:
                    self.routing_stats["successful_routes"] += 1
                    return decision
            
            # Step 2: Policy-based intelligent selection
            decision = self._policy_based_selection(request)
            if decision:
                self.routing_stats["successful_routes"] += 1
                return decision
            
            # Step 3: System defaults with health filtering
            decision = self._system_default_selection(request)
            if decision:
                self.routing_stats["fallback_routes"] += 1
                return decision
            
            # Step 4: Local model fallback
            decision = self._local_fallback_selection(request)
            if decision:
                self.routing_stats["fallback_routes"] += 1
                return decision
            
            # Step 5: Degraded mode
            if self.degraded_mode_manager:
                decision = self._degraded_mode_selection(request)
                if decision:
                    self.routing_stats["degraded_routes"] += 1
                    return decision
            
            # No viable options found
            self.routing_stats["failed_routes"] += 1
            raise RuntimeError("No viable LLM providers or runtimes available")
            
        except Exception as e:
            self.logger.error(f"Routing failed for request: {e}")
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
    
    def _try_explicit_preference(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Try to honor explicit user preferences if they are viable."""
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
                        reason="Explicit user preference (provider + model + runtime)",
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
                    reason="Explicit user preference (provider + model)",
                    confidence=0.9,
                    fallback_chain=[],
                    estimated_cost=None,
                    estimated_latency=None,
                    privacy_compliant=self._check_privacy_compliance(request, request.preferred_provider, selected_runtime),
                    capabilities=list(provider_spec.capabilities),
                )
        
        return None


    def _policy_based_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select provider and runtime based on routing policy."""
        # Get policy-based preferences
        preferred_provider = self._get_policy_provider(request)
        preferred_runtime = self._get_policy_runtime(request)
        
        # Check privacy constraints
        allowed_providers = self.policy.privacy_provider_map.get(request.privacy_level, [])
        allowed_runtimes = self.policy.privacy_runtime_map.get(request.privacy_level, [])
        
        if preferred_provider not in allowed_providers:
            # Find alternative provider that meets privacy requirements
            for provider in allowed_providers:
                if self._is_provider_healthy(provider):
                    preferred_provider = provider
                    break
            else:
                return None  # No privacy-compliant providers available
        
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
        
        # Check if provider meets requirements
        if request.requires_streaming and "streaming" not in provider_spec.capabilities:
            return None
        if request.requires_function_calling and "function_calling" not in provider_spec.capabilities:
            return None
        if request.requires_vision and "vision" not in provider_spec.capabilities:
            return None
        
        # Select a model (this would be enhanced with actual model discovery)
        model_id = self._select_model_for_provider(preferred_provider, request)
        if not model_id:
            return None
        
        confidence = self._calculate_confidence(request, preferred_provider, preferred_runtime)
        
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
        """Select using system defaults with health filtering."""
        # Get healthy providers in priority order
        healthy_providers = [
            p for p in self.registry.list_providers(healthy_only=True)
            if self._check_privacy_compliance(request, p, None)
        ]
        
        if not healthy_providers:
            return None
        
        # Select first healthy provider
        selected_provider = healthy_providers[0]
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
            reason="System default selection with health filtering",
            confidence=0.7,
            fallback_chain=self._build_fallback_chain(request),
            estimated_cost=self._estimate_cost(selected_provider, model_id),
            estimated_latency=self._estimate_latency(selected_provider, selected_runtime),
            privacy_compliant=self._check_privacy_compliance(request, selected_provider, selected_runtime),
            capabilities=list(provider_spec.capabilities) if provider_spec else [],
        )
    
    def _local_fallback_selection(self, request: RoutingRequest) -> Optional[RouteDecision]:
        """Select local models as fallback."""
        local_providers = ["local", "huggingface"]
        local_runtimes = ["llama.cpp", "transformers"]
        
        for provider in local_providers:
            if not self._is_provider_healthy(provider):
                continue
            
            if not self._check_privacy_compliance(request, provider, None):
                continue
            
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
                        reason="Local fallback selection",
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
    
    def _calculate_confidence(self, request: RoutingRequest, provider: str, runtime: str) -> float:
        """Calculate confidence score for routing decision."""
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
    
    # Analysis methods for dry-run functionality
    
    def _analyze_explicit_preference(self, request: RoutingRequest) -> Dict[str, Any]:
        """Analyze explicit user preferences for dry-run."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "analysis": {},
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
        """Analyze policy-based selection for dry-run."""
        result = {
            "viable": False,
            "decision": None,
            "issues": [],
            "policy_analysis": {},
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