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

from sqlalchemy.exc import SQLAlchemyError

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import LLMProvider, LLMRequest
from ai_karen_engine.services.metrics_service import get_metrics_service

# Lazy imports to avoid circular import issues
# Providers will be imported when needed in get_provider_class()

try:
    from prometheus_client import CollectorRegistry, Counter, Histogram

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
def record_llm_metric(
    event: str, duration: float, success: bool, provider: str, **extra
) -> None:
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
        _LLM_LATENCY.labels(
            event=event, provider=provider, success=label_success
        ).observe(duration)
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

    def warm_cache(self) -> None:
        """Warm provider caches by issuing a tiny generation request.

        Providers may override this for custom behaviour. The default
        implementation makes a best-effort call to :meth:`generate_text` with a
        single-token prompt and ignores all errors so that warmup never blocks
        startup.
        """
        try:
            self.generate_text("hello", max_tokens=1)
        except Exception:  # pragma: no cover - warmup is best-effort
            logger.debug("warm_cache failed", exc_info=True)


# ========== Main Utility Class ==========


class LLMUtils:
    """
    Centralized interface for all LLM operations—preferred for dependency injection.
    """

    def __init__(
        self,
        providers: Optional[Dict[str, LLMProviderBase]] = None,
        default: str = "llamacpp",
        use_registry: bool = True,
    ):
        self.use_registry = use_registry
        self.default = default

        if use_registry:
            # Use registry for provider management (import here to avoid circular import)
            from ai_karen_engine.integrations.llm_registry import get_registry

            self.registry = get_registry()
            self.providers = {}  # Cache for instantiated providers

            # Prefer first available provider when the configured default is unavailable
            try:
                available = set(self.registry.get_available_providers())
                if self.default not in available:
                    # Use registry's auto select (first suitable/available)
                    picked = self.registry.auto_select_provider({})
                    if picked:
                        logger.info(
                            f"Default provider '{self.default}' unavailable; using first available: '{picked}'"
                        )
                        self.default = picked
            except Exception:
                # Do not fail init if registry probing has issues
                logger.debug("Default provider auto-select probe failed", exc_info=True)
        else:
            # Legacy mode - use provided providers or create default ones
            if providers is None:
                # Lazy import providers to avoid circular imports
                from ai_karen_engine.integrations.providers.deepseek_provider import (
                    DeepseekProvider,
                )
                from ai_karen_engine.integrations.providers.gemini_provider import (
                    GeminiProvider,
                )
                from ai_karen_engine.integrations.providers.huggingface_provider import (
                    HuggingFaceProvider,
                )
                from ai_karen_engine.integrations.providers.llamacpp_provider import (
                    LlamaCppProvider,
                )
                from ai_karen_engine.integrations.providers.openai_provider import (
                    OpenAIProvider,
                )

                providers = {
                    "llama-cpp": LlamaCppProvider(),
                    "openai": OpenAIProvider(),
                    "gemini": GeminiProvider(),
                    "deepseek": DeepseekProvider(),
                    "huggingface": HuggingFaceProvider(),
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
                raise ProviderNotAvailable(
                    f"Provider '{provider_name}' not available in registry."
                )

            # Cache the instance
            self.providers[provider_name] = provider_instance
            return provider_instance
        else:
            # Legacy mode
            if provider_name not in self.providers:
                raise ProviderNotAvailable(
                    f"Provider '{provider_name}' not registered."
                )
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
                if hasattr(provider_instance, "health_check"):
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

    def auto_select_provider(
        self, requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Automatically select best available provider."""
        if self.use_registry:
            return self.registry.auto_select_provider(requirements)
        else:
            # Simple fallback for legacy mode
            available = self.list_available_providers()
            return available[0] if available else None

    def _record_request(
        self,
        provider_name: str,
        model: Optional[str],
        usage: Dict[str, Any],
        latency: float,
        user_ctx: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist request metrics for cost reporting."""
        try:
            with get_db_session_context() as session:
                provider_rec = (
                    session.query(LLMProvider).filter_by(name=provider_name).first()
                )
                provider_id = provider_rec.id if provider_rec else None
                req = LLMRequest(
                    provider_id=provider_id,
                    provider_name=provider_name,
                    model=model,
                    tenant_id=(user_ctx or {}).get("tenant_id"),
                    user_id=(user_ctx or {}).get("user_id"),
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                    cost=usage.get("cost"),
                    latency_ms=int(latency * 1000),
                )
                session.add(req)
                session.commit()
        except SQLAlchemyError:
            logger.exception("Failed to record LLM request")

    def generate_text(
        self,
        prompt: str,
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_ctx: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        # Respect explicit model by requesting a correctly initialized provider from registry
        provider_name = provider or self.default
        model_name = kwargs.get("model")
        if self.use_registry:
            provider_obj = self.registry.get_provider(provider_name, model=model_name)  # type: ignore[arg-type]
            if not provider_obj:
                raise ProviderNotAvailable(f"Provider '{provider_name}' not available in registry.")
            # Do not cache by plain provider name to avoid model mix-ups
        else:
            provider_obj = self.get_provider(provider)
        trace_id = trace_id or str(uuid.uuid4())
        model_name = model_name or getattr(provider_obj, "model", None)
        t0 = time.time()
        status = "success"
        meta = {
            "prompt": prompt[:100],
            "provider": provider_name,
            "user_roles": user_ctx.get("roles") if user_ctx else None,
            "trace_id": trace_id,
            "kwargs": kwargs,
        }
        trace_llm_event("generate_text_start", trace_id, meta)
        metrics_service = get_metrics_service()
        model_name = kwargs.get("model") or getattr(provider_obj, "model", None)
        try:
            out = provider_obj.generate_text(prompt, **kwargs)
            duration = time.time() - t0
            usage = getattr(provider_obj, "last_usage", {})
            self._record_request(
                provider or self.default,
                model_name,
                usage,
                duration,
                user_ctx,
            )
            metrics_service.record_llm_latency(
                duration,
                provider or self.default,
                model_name or "",
                "success",
                trace_id,
            )
            meta["duration"] = duration
            trace_llm_event("generate_text_success", trace_id, meta)
            return out
        except Exception as ex:
            duration = time.time() - t0
            metrics_service.record_llm_latency(
                duration,
                provider or self.default,
                model_name or "",
                "error",
                trace_id,
            )
            meta.update({"duration": duration, "error": str(ex)})
            trace_llm_event("generate_text_error", trace_id, meta)
            raise GenerationFailed(f"Provider '{provider}' failed: {ex}")
        finally:
            duration = time.time() - t0
            try:
                from ai_karen_engine.services.metrics_service import get_metrics_service

                get_metrics_service().record_llm_latency(
                    duration,
                    provider=provider_name,
                    model=model_name or "",
                    status=status,
                )
            except Exception:
                pass

    def embed(
        self,
        text: Union[str, List[str]],
        provider: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_ctx: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[float]:
        provider_name = provider or self.default
        model_name = kwargs.get("model")
        if self.use_registry:
            provider_obj = self.registry.get_provider(provider_name, model=model_name)  # type: ignore[arg-type]
            if not provider_obj:
                raise ProviderNotAvailable(f"Provider '{provider_name}' not available in registry.")
        else:
            provider_obj = self.get_provider(provider)
        trace_id = trace_id or str(uuid.uuid4())
        model_name = model_name or getattr(provider_obj, "model", None)
        t0 = time.time()
        status = "success"
        meta = {
            "provider": provider_name,
            "trace_id": trace_id,
            "kwargs": kwargs,
        }
        trace_llm_event("embed_start", trace_id, meta)
        try:
            out = provider_obj.embed(text, **kwargs)
            duration = time.time() - t0
            usage = getattr(provider_obj, "last_usage", {})
            self._record_request(
                provider_name,
                model_name,
                usage,
                duration,
                user_ctx,
            )
            meta["duration"] = duration
            trace_llm_event("embed_success", trace_id, meta)
            return out
        except Exception as ex:
            status = "error"
            meta.update({"duration": time.time() - t0, "error": str(ex)})
            trace_llm_event("embed_error", trace_id, meta)
            raise EmbeddingFailed(f"Provider '{provider}' failed: {ex}")
        finally:
            duration = time.time() - t0
            try:
                from ai_karen_engine.services.metrics_service import get_metrics_service

                get_metrics_service().record_llm_latency(
                    duration,
                    provider=provider_name,
                    model=model_name or "",
                    status=status,
                )
            except Exception:
                pass


# ========== Prompt-First Plugin API ==========
def get_llm_manager(
    providers: Optional[Dict[str, LLMProviderBase]] = None,
    default: str = "llamacpp",
    use_registry: bool = True,
) -> LLMUtils:
    return LLMUtils(providers, default=default, use_registry=use_registry)


def generate_text(
    prompt: str,
    provider: Optional[str] = None,
    user_ctx: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> str:
    mgr = get_llm_manager()
    return mgr.generate_text(prompt, provider=provider, user_ctx=user_ctx, **kwargs)


def embed_text(
    text: Union[str, List[str]], provider: Optional[str] = None, **kwargs
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
    "LLMUtils",
    "get_llm_manager",
    "generate_text",
    "embed_text",
    "record_llm_metric",
]
