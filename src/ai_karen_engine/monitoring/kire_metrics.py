"""
Prometheus metrics for KIRE routing (safe fallbacks when Prometheus is absent).
"""
from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram

    KIRE_DECISIONS_TOTAL = Counter(
        "kire_routing_decisions_total",
        "Total KIRE routing decisions",
        ["status", "task_type"],
    )
    KIRE_CACHE_EVENTS_TOTAL = Counter(
        "kire_routing_cache_events_total",
        "KIRE routing cache events",
        ["event"],  # hit|miss|store
    )
    KIRE_LATENCY_SECONDS = Histogram(
        "kire_routing_latency_seconds",
        "KIRE routing decision latency",
        ["task_type"],
        buckets=(0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0),
    )
    KIRE_ACTIONS_TOTAL = Counter(
        "kire_actions_total",
        "Total KIRE action invocations",
        ["action", "status"],
    )
    KIRE_PROVIDER_SELECTION_TOTAL = Counter(
        "kire_provider_selection_total",
        "KIRE provider/model selection outcomes",
        ["provider", "model", "status", "task_type"],
    )
    KIRE_DECISION_CONFIDENCE = Histogram(
        "kire_routing_decision_confidence",
        "Confidence distribution for routing decisions",
        ["task_type", "provider", "model"],
        buckets=(0.0, 0.25, 0.5, 0.65, 0.8, 0.9, 0.96, 1.01),
    )
    KIRE_ADVISORY_OUTCOMES_TOTAL = Counter(
        "kire_advisory_outcomes_total",
        "Outcome of KIRE advisory routing after governed chat execution",
        ["outcome", "final_status", "execution_path"],
    )
    KRO_SPECIALIZED_PATH_TOTAL = Counter(
        "kro_specialized_path_total",
        "Invocations of specialized KRO orchestration paths",
        ["path", "status"],
    )
except Exception:  # pragma: no cover - fallback

    class _Dummy:
        def labels(self, *args, **kwargs):  # type: ignore
            return self

        def inc(self, *args, **kwargs):  # type: ignore
            pass

        def observe(self, *args, **kwargs):  # type: ignore
            pass

    KIRE_DECISIONS_TOTAL = _Dummy()
    KIRE_CACHE_EVENTS_TOTAL = _Dummy()
    KIRE_LATENCY_SECONDS = _Dummy()
    KIRE_ACTIONS_TOTAL = _Dummy()
    KIRE_PROVIDER_SELECTION_TOTAL = _Dummy()
    KIRE_DECISION_CONFIDENCE = _Dummy()
    KIRE_ADVISORY_OUTCOMES_TOTAL = _Dummy()
    KRO_SPECIALIZED_PATH_TOTAL = _Dummy()

__all__ = [
    "KIRE_DECISIONS_TOTAL",
    "KIRE_CACHE_EVENTS_TOTAL",
    "KIRE_LATENCY_SECONDS",
    "KIRE_ACTIONS_TOTAL",
    "KIRE_PROVIDER_SELECTION_TOTAL",
    "KIRE_DECISION_CONFIDENCE",
    "KIRE_ADVISORY_OUTCOMES_TOTAL",
    "KRO_SPECIALIZED_PATH_TOTAL",
]
