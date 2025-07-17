"""Profile-based LLM provider router."""
import json
import time
from pathlib import Path
from typing import Dict, Any

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

MODEL_INVOCATIONS_TOTAL = Counter(
    "model_invocations_total",
    "Total LLM model invocations",
    ["model"],
) if METRICS_ENABLED else Counter()
FALLBACK_RATE = Counter(
    "fallback_rate",
    "Fallback invocations",
    ["profile"],
) if METRICS_ENABLED else Counter()
AVG_RESPONSE_TIME = Histogram(
    "avg_response_time",
    "LLM response time",
    ["model"],
) if METRICS_ENABLED else Histogram()

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

    def invoke(self, llm_utils, prompt: str, task_intent: str, **kwargs) -> str:
        provider = self.select_provider(task_intent)
        start = time.time()
        try:
            result = llm_utils.generate_text(prompt, provider=provider, **kwargs)
            return result
        finally:
            MODEL_INVOCATIONS_TOTAL.labels(model=provider).inc()
            AVG_RESPONSE_TIME.labels(model=provider).observe(time.time() - start)
