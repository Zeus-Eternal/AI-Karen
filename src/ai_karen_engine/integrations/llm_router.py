"""LLM routing utilities."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_karen_engine.integrations.llm_registry import get_registry

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

DEFAULT_PATH = Path(__file__).parents[2] / "config" / "llm_profiles.yml"


def _load_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text()
    if yaml:
        return yaml.safe_load(text)
    # minimal JSON fallback
    return json.loads(text)


class LLMProfileRouter:
    """Route LLM requests according to intent profiles."""

    def __init__(self, profile: str = "default", config_path: Path = DEFAULT_PATH):
        self.profile = profile
        self.config_path = config_path
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        data = _load_yaml(self.config_path)
        return data.get("profiles", {}) if isinstance(data, dict) else {}

    def select_provider(self, task_intent: str) -> str:
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
        # Use preferred provider if specified, otherwise use profile-based selection
        if preferred_provider:
            provider = preferred_provider
            logging.info(f"Using preferred provider: {provider}")
        else:
            provider = self.select_provider(task_intent)
        
        start = time.time()
        try:
            # Pass preferred model if specified
            if preferred_model:
                kwargs['model'] = preferred_model
                logging.info(f"Using preferred model: {preferred_model}")
            
            result = llm_utils.generate_text(prompt, provider=provider, **kwargs)
            return result
        finally:
            model_label = f"{provider}:{preferred_model}" if preferred_model else provider
            MODEL_INVOCATIONS_TOTAL.labels(model=model_label).inc()
            AVG_RESPONSE_TIME.labels(model=model_label).observe(time.time() - start)


class LLMRouter:
    """Basic provider router prioritizing local models."""

    def __init__(
        self,
        registry=None,
        local_priority: Optional[List[str]] = None,
    ) -> None:
        self.registry = registry or get_registry()
        self.logger = logging.getLogger("kari.llm_router")
        self.local_priority = local_priority or ["ollama", "llama.cpp", "llama_cpp"]

    def _is_healthy(self, name: str) -> bool:
        """Check if a provider is healthy using the registry health check."""
        try:
            result = self.registry.health_check(name)
            return result.get("status") == "healthy"
        except Exception as exc:  # pragma: no cover - safety
            self.logger.debug("Health check failed for %s: %s", name, exc)
            return False

    def _get_provider(self, name: str):
        try:
            return self.registry.get_provider(name)
        except Exception:
            return None

    def select_provider(
        self,
        request: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ):
        """Select the best available provider.

        The order of precedence is:
        1. User preferred provider if healthy
        2. Local providers (Ollama, llama.cpp) if healthy
        3. First healthy remote provider from registry
        """

        pref = (user_preferences or {}).get("provider")
        if pref and self._is_healthy(pref):
            provider = self._get_provider(pref)
            if provider:
                return provider

        for name in self.local_priority:
            if self._is_healthy(name):
                provider = self._get_provider(name)
                if provider:
                    return provider

        for name in self.registry.list_providers():
            if name in self.local_priority:
                continue
            if self._is_healthy(name):
                provider = self._get_provider(name)
                if provider:
                    return provider

        return None

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the selected provider."""
        provider = self.select_provider(user_preferences=kwargs.get("user_preferences"))
        if not provider:
            raise RuntimeError("No LLM providers available")
        return provider.generate_text(prompt, **kwargs)
