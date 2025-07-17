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
        logger.debug("Prometheus metrics disabled or failed")

def trace_llm_event(event: str, correlation_id: str, meta: Dict[str, Any]):
    logger.info(f"[TRACE] event={event} correlation_id={correlation_id} meta={meta}")

# ========== Provider Base ==========
class LLMProviderBase:
    def generate_text(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        raise NotImplementedError

# Example: Local Ollama
class OllamaProvider(LLMProviderBase):
    def __init__(self, model: str = "llama3.2:latest"):
        try:
            import ollama
            self.ollama = ollama
        except ImportError:
            raise ProviderNotAvailable("Ollama Python package not installed.")
        self.model = model

    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from Ollama.

        If ``model`` is supplied in ``kwargs`` use it, otherwise fall back to
        ``self.model``. This avoids passing duplicate ``model`` arguments to the
        underlying client which expects only one.
        """
        t0 = time.time()
        try:
            model = kwargs.pop("model", self.model)
            result = self.ollama.generate(model=model, prompt=prompt, **kwargs)
            text = result.get("response") or result.get("text") or ""
            record_llm_metric("generate_text", time.time() - t0, True, "ollama")
            return text
        except Exception as ex:
            record_llm_metric(
                "generate_text", time.time() - t0, False, "ollama", error=str(ex)
            )
            raise GenerationFailed(f"Ollama error: {ex}")

    def embed(self, text: Union[str, List[str]], **kwargs) -> List[float]:
        t0 = time.time()
        try:
            raise NotImplementedError("Ollama embedding not wired (implement as needed).")
        except Exception as ex:
            record_llm_metric("embed", time.time() - t0, False, "ollama", error=str(ex))
            raise EmbeddingFailed(f"Ollama embed error: {ex}")

# More providers (Gemini, Anthropic, etc.) can be added here, plugin style.

# ========== Main Utility Class ==========

class LLMUtils:
    """
    Centralized interface for all LLM operations—preferred for dependency injection.
    """
    def __init__(
        self,
        providers: Optional[Dict[str, LLMProviderBase]] = None,
        default: str = "ollama"
    ):
        self.providers = providers or {"ollama": OllamaProvider()}
        self.default = default

    def get_provider(self, provider: Optional[str] = None) -> LLMProviderBase:
        provider = provider or self.default
        if provider not in self.providers:
            raise ProviderNotAvailable(f"Provider '{provider}' not registered.")
        return self.providers[provider]

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
    default: str = "ollama"
) -> LLMUtils:
    return LLMUtils(providers, default=default)

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
