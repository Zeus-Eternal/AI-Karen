"""
KIRE Router - intelligent LLM routing that integrates with existing LLMRegistry.
"""
from __future__ import annotations
import time
import hashlib
import json
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.cache import MemoryCache, get_request_deduplicator
from ai_karen_engine.monitoring.kire_metrics import (
    KIRE_DECISIONS_TOTAL,
    KIRE_CACHE_EVENTS_TOTAL,
    KIRE_LATENCY_SECONDS,
)

# Use shared MemoryCache impl to align with CopilotKit infra
_cache = MemoryCache(max_size=2048, default_ttl=300)
_cache_index: Dict[str, set] = {}
_deduper = get_request_deduplicator()

from ai_karen_engine.routing.types import RouteRequest, RouteDecision
from ai_karen_engine.routing.profile_resolver import ProfileResolver
from ai_karen_engine.routing.decision_logger import DecisionLogger
from ai_karen_engine.integrations.task_analyzer import TaskAnalyzer

# Import existing components
try:
    from ai_karen_engine.integrations.provider_status import ProviderHealth
except ImportError:
    # Fallback if provider status not available
    class ProviderHealth:
        @staticmethod
        async def is_healthy(provider: str) -> bool:
            return True  # Assume healthy for now

try:
    from ai_karen_engine.core.degraded_mode import DegradedMode
except ImportError:
    # Fallback if degraded mode not available
    class DegradedMode:
        @staticmethod
        def get_fallback_provider() -> tuple[str, str]:
            return "llamacpp", "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"


class KIRERouter:
    """Kari Intelligent Routing Engine - integrates with existing LLMRegistry."""
    
    def __init__(self, llm_registry=None):
        from ai_karen_engine.integrations.llm_registry import LLMRegistry
        self.llm_registry = llm_registry or LLMRegistry()
        self.profile_resolver = ProfileResolver()
        self.logger = DecisionLogger()
        self.task_analyzer = TaskAnalyzer()
    
    async def route_provider_selection(self, request: RouteRequest) -> RouteDecision:
        """Main routing method - returns routing decision."""
        t0 = time.perf_counter()
        cache_key = self._generate_cache_key(request)
        # Correlation id sourced from context if present (CopilotKit pattern)
        corr = None
        try:
            corr = (request.context or {}).get("request_metadata", {}).get("correlation_id") or (request.context or {}).get("correlation_id")
        except Exception:
            corr = None
        corr_id = corr or hashlib.md5(cache_key.encode()).hexdigest()[:10]
        
        # Emit start event
        try:
            self.logger.log_start(corr_id, request.user_id, "routing.select", {"task_type": request.task_type, "khrp_step": request.khrp_step})
        except Exception:
            pass

        # Check cache first
        cached = _cache.get(cache_key)
        if cached is not None:
            KIRE_CACHE_EVENTS_TOTAL.labels(event="hit").inc()
            return cached
        # Record cache miss
        KIRE_CACHE_EVENTS_TOTAL.labels(event="miss").inc()

        try:
            # Get user profile
            profile = self.profile_resolver.get_user_profile(request.user_id)
            assignment = self.profile_resolver.get_model_assignment(
                profile, request.task_type, request.khrp_step
            )
            # Analyze query for task hints/capabilities
            analysis = self.task_analyzer.analyze(request.query, context=request.context)
            task_type = request.task_type or analysis.task_type

            # Start from profile assignment or default config
            provider = assignment.provider if assignment else "openai"
            model = assignment.model if assignment else "gpt-4o-mini"
            chain = profile.fallback_chain if profile else ["openai", "deepseek", "llamacpp"]
            
            async def _decide():
                # Apply capability/constraint matching and health checks
                return await self._refine_by_requirements(
                    provider, model, request, chain, analysis.required_capabilities, task_type
                )

            # Deduplicate identical in-flight routing decisions (same cache key)
            provider, model, reason, conf = await _deduper.deduplicate(_decide)
        except Exception as ex:
            # Log error and metrics, then rethrow
            try:
                self.logger.log_decision(
                    request_id=corr_id,
                    user_id=request.user_id,
                    task_type=request.task_type,
                    khrp_step=request.khrp_step,
                    decision=RouteDecision(provider="", model="", reasoning=str(ex), confidence=0.0),
                    execution_time_ms=(time.perf_counter() - t0) * 1000,
                    success=False,
                    error=str(ex),
                )
                KIRE_DECISIONS_TOTAL.labels(status="error", task_type=request.task_type or "chat").inc()
                KIRE_LATENCY_SECONDS.labels(task_type=request.task_type or "chat").observe((time.perf_counter() - t0))
            except Exception:
                pass
            raise
        
        decision = RouteDecision(
            provider=provider,
            model=model,
            reasoning=reason,
            confidence=conf,
            fallback_chain=chain,
            metadata={
                "task_type": task_type,
                "khrp_step": request.khrp_step,
                "analysis": {
                    "required_capabilities": analysis.required_capabilities,
                    "confidence": analysis.confidence,
                    "step_hint": analysis.khrp_step_hint,
                },
                "execution_time_ms": (time.perf_counter() - t0) * 1000
            }
        )
        
        # Cache only high-confidence, non-dynamic steps
        if conf >= 0.8 and request.khrp_step not in ("evidence_gathering", "tool_execution"):
            _cache.set(cache_key, decision)
            # index by user for targeted invalidation
            try:
                _cache_index.setdefault(request.user_id, set()).add(cache_key)
            except Exception:
                pass
            KIRE_CACHE_EVENTS_TOTAL.labels(event="store").inc()
        
        # Log decision
        self.logger.log_decision(
            request_id=corr_id,
            user_id=request.user_id,
            task_type=request.task_type,
            khrp_step=request.khrp_step,
            decision=decision,
            execution_time_ms=(time.perf_counter() - t0) * 1000,
            success=True
        )
        # Metrics
        try:
            KIRE_DECISIONS_TOTAL.labels(status="success", task_type=request.task_type or "chat").inc()
            KIRE_LATENCY_SECONDS.labels(task_type=request.task_type or "chat").observe((time.perf_counter() - t0))
        except Exception:
            pass
        
        return decision
    
    async def _refine_by_requirements(self, provider: str, model: str, 
                                    req: RouteRequest, chain: List[str], required_caps: List[str], inferred_task: str) -> tuple[str, str, str, float]:
        """Refine provider/model selection based on requirements and health."""
        # KHRP step-specific preferences
        if req.khrp_step in ("reasoning_core",):
            # Prefer models that are stronger in reasoning if available
            preferred = [("openai", "gpt-4o"), ("deepseek", "deepseek-chat")]
            for prov, mod in preferred:
                if await ProviderHealth.is_healthy(prov):
                    provider, model = prov, mod
                    break

        # Task/capability-specific steering
        if "embeddings" in required_caps:
            if await ProviderHealth.is_healthy("huggingface"):
                provider, model = "huggingface", "sentence-transformers/all-MiniLM-L6-v2"
        elif inferred_task == "summarization":
            if await ProviderHealth.is_healthy("llamacpp"):
                provider, model = "llamacpp", "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"

        # Health gate on chosen provider
        if not await ProviderHealth.is_healthy(provider):
            reason = f"{provider} unhealthy; selecting fallback"
            
            # Try fallback chain
            for fb in chain:
                if await ProviderHealth.is_healthy(fb):
                    return fb, self._default_model(fb), reason, 0.75
            
            # Final degraded mode
            degraded_provider, degraded_model = DegradedMode.get_fallback_provider()
            return degraded_provider, degraded_model, "degraded-mode", 0.6
        
        # Apply task-specific optimizations
        if inferred_task == "code" and provider == "openai":
            # Prefer deepseek for coding tasks
            if await ProviderHealth.is_healthy("deepseek"):
                return "deepseek", "deepseek-coder", "optimized for coding", 0.95

        # Cost gate (simple heuristic)
        max_cost = req.requirements.get("max_cost_per_call") if req.requirements else None
        if max_cost is not None:
            est_cost = self._estimate_cost(provider, model, req)
            if est_cost is not None and est_cost > max_cost:
                # Try cheaper alternatives in chain
                for alt in chain:
                    if not await ProviderHealth.is_healthy(alt):
                        continue
                    alt_model = self._default_model(alt)
                    alt_cost = self._estimate_cost(alt, alt_model, req)
                    if alt_cost is not None and alt_cost <= max_cost:
                        return alt, alt_model, f"cost gate: {provider}/{model}->{alt}/{alt_model}", 0.82
                # Keep selection but lower confidence and flag cost breach
                return provider, model, "over_cost_budget; using profile selection", 0.75
        
        # Default: use profile assignment
        reason = f"profile assignment for {inferred_task}"
        return provider, model, reason, 0.9
    
    def _default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "deepseek": "deepseek-chat",
            "llamacpp": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
            "gemini": "gemini-1.5-flash",
            "huggingface": "microsoft/DialoGPT-large"
        }
        return defaults.get(provider, "auto")
    
    def _generate_cache_key(self, request: RouteRequest) -> str:
        """Generate cache key for routing request."""
        req_hash = hashlib.md5(
            json.dumps(request.requirements, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"{request.user_id}:{request.task_type}:{request.khrp_step or 'none'}:{req_hash}"

    def _estimate_cost(self, provider: str, model: str, req: RouteRequest) -> Optional[float]:
        """Very rough per-call cost estimate based on provider defaults.
        This is a heuristic placeholder; integrate real pricing later.
        """
        pricing = {
            "openai": 0.005,   # per 1k tokens (placeholder)
            "deepseek": 0.003,
            "gemini": 0.004,
            "huggingface": 0.002,
            "llamacpp": 0.0,
        }
        # Assume small call unless specified
        tks = int((req.requirements or {}).get("expected_tokens", 1000))
        per_1k = pricing.get(provider)
        return None if per_1k is None else per_1k * (tks / 1000.0)


# Cache invalidation helpers
def invalidate_user_cache(user_id: str):
    """Invalidate cache entries for a specific user using index."""
    keys = list(_cache_index.get(user_id, set()))
    for k in keys:
        _cache.delete(k)
    _cache_index.pop(user_id, None)


def invalidate_provider_cache(_provider: str):
    """Invalidate routing cache broadly on provider health changes."""
    # Simple strategy: clear all entries because decisions embed provider choice
    _cache.clear()
    _cache_index.clear()


def get_routing_cache_stats() -> Dict[str, Any]:
    """Expose routing cache stats for diagnostics."""
    return _cache.get_stats()


def get_routing_dedup_stats() -> Dict[str, Any]:
    """Expose routing request deduplicator stats for diagnostics."""
    return _deduper.get_stats()
