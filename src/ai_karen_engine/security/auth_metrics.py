"""Authentication metrics integration with Prometheus."""

from __future__ import annotations

from typing import Dict

from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram, CollectorRegistry
except Exception:  # pragma: no cover
    class _DummyMetric:
        def inc(self, amount: int = 1) -> None:
            pass

        def observe(self, value: float) -> None:
            pass

    Counter = Histogram = _DummyMetric  # type: ignore
    CollectorRegistry = object  # type: ignore

AUTH_SUCCESS = None
AUTH_FAILURE = None
AUTH_PROCESSING_TIME = None


def init_auth_metrics(
    registry: CollectorRegistry | None = PROM_REGISTRY,
    force: bool = False,
):
    """Initialize authentication metrics.

    Parameters
    ----------
    registry:
        Prometheus registry to register metrics with. Defaults to the
        global ``PROM_REGISTRY`` used across the project.
    force:
        Force reinitialization even if metrics were already created.
    """
    global AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME
    if AUTH_SUCCESS is not None and not force:
        return AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME

    AUTH_SUCCESS = Counter(
        "kari_auth_success_total",
        "Total successful authentication events",
        registry=registry,
    )
    AUTH_FAILURE = Counter(
        "kari_auth_failure_total",
        "Total failed authentication events",
        registry=registry,
    )
    AUTH_PROCESSING_TIME = Histogram(
        "kari_auth_processing_seconds",
        "Time spent processing authentication events",
        registry=registry,
    )
    return AUTH_SUCCESS, AUTH_FAILURE, AUTH_PROCESSING_TIME


# Initialize metrics with default registry at import time
init_auth_metrics()


def metrics_hook(event: str, data: Dict[str, object]) -> None:
    """Forward authentication events to Prometheus metrics."""
    duration = float(data.get("processing_time", 0) or 0)
    if event == "login_success":
        AUTH_SUCCESS.inc()
        AUTH_PROCESSING_TIME.observe(duration)
    elif event in {"login_failure", "login_blocked", "rate_limit_exceeded"}:
        AUTH_FAILURE.inc()
        if duration:
            AUTH_PROCESSING_TIME.observe(duration)
