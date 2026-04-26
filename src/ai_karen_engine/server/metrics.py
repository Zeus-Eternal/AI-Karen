from __future__ import annotations

from ai_karen_engine.utils.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    LNM_ERROR_COUNT as ERROR_COUNT,
    init_metrics as initialize_metrics,
)

PROMETHEUS_ENABLED = True

__all__ = [
    "initialize_metrics",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "ERROR_COUNT",
    "PROMETHEUS_ENABLED",
]
