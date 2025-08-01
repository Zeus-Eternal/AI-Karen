"""
Kari LLM Utils - Production Enterprise Version

- Centralized, DI-driven LLM orchestration for Kari AI
- Supports multiple providers (local, remote, plugins) and prompt-first hooks
- Metrics, tracing, RBAC, error trace, and observability built-in
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union

try:
    from prometheus_client import Counter, Histogram, CollectorRegistry
    PROM_REGISTRY = CollectorRegistry()
    _LLM_COUNT = Counter(
        "llm_requests_total",
        "Total LLM requests",
        ["event", "provider", "success"],
        registry=PROM_REGISTRY,
    )
    _LLM_LATENCY = Histogram(
        "llm_request_latency_seconds",
        "LLM request latency",
        ["event", "provider", "success"],
        registry=PROM_REGISTRY,
    )
    METRICS_ENABLED = True
except Exception:  # pragma: no cover - optional dep
    class _DummyMetric:
        def labels(self, **kwargs):
            return self

        def inc(self, n: int = 1) -> None:
            pass

        def observe(self, v: float) -> None:
            pass

    METRICS_ENABLED = False
    PROM_REGISTRY = None  # type: ignore
    _LLM_COUNT = _LLM_LATENCY = _DummyMetric()

logger = logging.getLogger("kari.llm_utils")

# ========== Exceptions ==========
class LLMError(Exception):
    pass


class ProviderNotAvailable(LLMError):
    pass


class GenerationFailed(LLMError):
    pass


class EmbeddingFailed(LLMError):
    pass

# ========== Metrics/Observability (Stub for Prometheus) ==========
def record_llm_metric(event: str, duration: float, success: bool, provider: str, **extra) -> None:
    """Record a metric for an LLM event.

    Parameters
    ----------
    event:
        Event name such as ``generate_text`` or ``embed``.
    duration:
        Duration of the call in seconds.
    success:
        ``True`` if the call succeeded.
    provider:
        Name of the LLM provider.
    extra:
        Additional metadata ignored by the metrics layer.
    """

    logger.info(
        f"[METRIC] event={event} duration={duration:.3f}s success={success} provider={provider} extra={extra}"
    )

    label_success = "true" if success else "false"
    try:
        _LLM_COUNT.labels(event=event, provider=provider, success=label_success).inc()
        _LLM_LATENCY.labels(event=event, provider=provider, success=label_success).observe(duration)
    except Exception:  # pragma: no cover - safety guard
        logger.info("Prometheus metrics disabled or failed")

def trace_llm_event(event: str, correlation_id: str, meta: Dict[str, Any]):
    logger.info(f"[TRACE] event={event} correlation_id={correlation_id} meta={meta}")

# ========== Provider Base ==========
class LLMProviderBase:
    def generate_text(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        raise NotImplementedError

# Import enhanced providers
from ai_karen_engine.integrations.providers.ollama_provider import OllamaProvider
from ai_karen_engine.integrations.providers.openai_provider import OpenAIProvider
from ai_karen_engine.integrations.providers.gemini_provider import GeminiProvider
from ai_karen_engine.integrations.providers.deepseek_provider import DeepseekProvider
from ai_karen_engine.integrations.providers.huggingface_provider import HuggingFaceProvider

# ========== Main Utility Class ==========

class LLMUtils:
    """
    Centralized interface for all LLM operations—preferred for dependency injection.
    """
    def __init__(
        self,
        providers: Optional[Dict[str, LLMProviderBase]] = None,
        default: str = "ollama",
        use_registry: bool = True
    ):
        self.use_registry = use_registry
        self.default = default
        
        if use_registry:
            # Use registry for provider management (import here to avoid circular import)
            from ai_karen_engine.integrations.llm_registry import get_registry
            self.registry = get_registry()
            self.providers = {}  # Cache for instantiated providers
        else:
            # Legacy mode - use provided providers or create default ones
            if providers is None:
                providers = {
                    "ollama": OllamaProvider(),
                    "openai": OpenAIProvider(),
                    "gemini": GeminiProvider(),
                    "deepseek": DeepseekProvider(),
                    "huggingface": HuggingFaceProvider()
                }
            self.providers = providers
            self.registry = None

    def get_provider(self, provider: Optional[str] = None) -> LLMProviderBase:
        provider_name = provider or self.default
        
        if self.use_registry:
            # Get provider from registry
            if provider_name in self.providers:
                return self.providers[provider_name]
            
            # Create provider instance via registry
            provider_instance = self.registry.get_provider(provider_name)
            if not provider_instance:
                raise ProviderNotAvailable(f"Provider '{provider_name}' not available in registry.")
            
            # Cache the instance
            self.providers[provider_name] = provider_instance
            return provider_instance
        else:
            # Legacy mode
            if provider_name not in self.providers:
                raise ProviderNotAvailable(f"Provider '{provider_name}' not registered.")
            return self.providers[provider_name]
    
    def list_available_providers(self) -> List[str]:
        """Get list of available providers."""
        if self.use_registry:
            return self.registry.get_available_providers()
        else:
            return list(self.providers.keys())
    
    def health_check_provider(self, provider: str) -> Dict[str, Any]:
        """Perform health check on a specific provider."""
        if self.use_registry:
            return self.registry.health_check(provider)
        else:
            # Basic health check for legacy mode
            try:
                provider_instance = self.get_provider(provider)
                if hasattr(provider_instance, 'health_check'):
                    return provider_instance.health_check()
                else:
                    return {"status": "healthy", "message": "Provider available"}
            except Exception as ex:
                return {"status": "unhealthy", "error": str(ex)}
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all providers."""
        if self.use_registry:
            return self.registry.health_check_all()
        else:
            results = {}
            for provider_name in self.providers.keys():
                results[provider_name] = self.health_check_provider(provider_name)
            return results
    
    def auto_select_provider(self, requirements: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Automatically select best available provider."""
        if self.use_registry:
            return self.registry.auto_select_provider(requirements)
        else:
            # Simple fallback for legacy mode
            available = self.list_available_providers()
            return available[0] if available else None

    def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_ctx: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        provider_obj = self.get_provider(provider)
        trace_id = trace_id or str(uuid.uuid4())
        t0 = time.time()
        meta = {
            "prompt": prompt[:100],
            "provider": provider or self.default,
            "user_roles": user_ctx.get("roles") if user_ctx else None,
            "trace_id": trace_id,
            "kwargs": kwargs,
        }
        trace_llm_event("generate_text_start", trace_id, meta)
        try:
            out = provider_obj.generate_text(prompt, **kwargs)
            meta["duration"] = time.time() - t0
            trace_llm_event("generate_text_success", trace_id, meta)
            return out
        except Exception as ex:
            meta.update({"duration": time.time() - t0, "error": str(ex)})
            trace_llm_event("generate_text_error", trace_id, meta)
            raise GenerationFailed(f"Provider '{provider}' failed: {ex}")

    def embed(
        self,
        text: Union[str, List[str]],
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        provider_obj = self.get_provider(provider)
        trace_id = trace_id or str(uuid.uuid4())
        t0 = time.time()
        meta = {
            "provider": provider or self.default,
            "trace_id": trace_id,
            "kwargs": kwargs,
        }
        trace_llm_event("embed_start", trace_id, meta)
        try:
            out = provider_obj.embed(text, **kwargs)
            meta["duration"] = time.time() - t0
            trace_llm_event("embed_success", trace_id, meta)
            return out
        except Exception as ex:
            meta.update({"duration": time.time() - t0, "error": str(ex)})
            trace_llm_event("embed_error", trace_id, meta)
            raise EmbeddingFailed(f"Provider '{provider}' failed: {ex}")

# ========== Prompt-First Plugin API ==========
def get_llm_manager(
    providers: Optional[Dict[str, LLMProviderBase]] = None,
    default: str = "ollama",
    use_registry: bool = True
) -> LLMUtils:
    return LLMUtils(providers, default=default, use_registry=use_registry)

def generate_text(
    prompt: str,
    provider: Optional[str] = None,
    user_ctx: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    mgr = get_llm_manager()
    return mgr.generate_text(prompt, provider=provider, user_ctx=user_ctx, **kwargs)

def embed_text(
    text: Union[str, List[str]],
    provider: Optional[str] = None,
    **kwargs
) -> List[float]:
    mgr = get_llm_manager()
    return mgr.embed(text, provider=provider, **kwargs)

# ========== __all__ ==========
__all__ = [
    "LLMError",
    "ProviderNotAvailable",
    "GenerationFailed",
    "EmbeddingFailed",
    "PROM_REGISTRY",
    "LLMProviderBase",
    "OllamaProvider",
    "LLMUtils",
    "get_llm_manager",
    "generate_text",
    "embed_text",
]