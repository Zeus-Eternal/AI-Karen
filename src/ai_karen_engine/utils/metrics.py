"""Prometheus metrics initialization helpers.

This module centralizes Prometheus metric setup and ensures metrics
are registered only once. Subsequent calls to :func:`init_metrics`
will reuse existing metrics rather than attempting to re-register
them, which can trigger errors when modules are reloaded.
"""

from __future__ import annotations

import logging
from typing import Tuple

from ai_karen_engine.integrations.llm_utils import PROM_REGISTRY

try:  # pragma: no cover - import guarded for optional dependency
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )
except ImportError:  # pragma: no cover

    class _DummyMetric:
        """Fallback metric used when prometheus_client is unavailable."""

        def __init__(self, *args, **kwargs):
            pass

        def inc(self, amount: int = 1) -> None:
            pass

        def time(self):
            class _Ctx:
                def __enter__(self):  # noqa: D401 - simple context
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    pass

            return _Ctx()

    Counter = Histogram = _DummyMetric  # type: ignore

    def generate_latest() -> bytes:  # type: ignore
        return b""

    CONTENT_TYPE_LATEST = "text/plain"  # type: ignore


logger = logging.getLogger(__name__)

# Public metric references populated on first initialization
REQUEST_COUNT = None
REQUEST_LATENCY = None
LNM_ERROR_COUNT = None

_metrics_initialized = False


def _create_dummy_metric():
    class _LocalDummyMetric:
        def inc(self, amount: int = 1) -> None:
            pass

        def time(self):
            class _Ctx:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb) -> None:
                    pass

            return _Ctx()

    return _LocalDummyMetric()


def init_metrics() -> Tuple[object, object, object]:
    """Initialize Prometheus metrics safely.

    Returns
    -------
    Tuple[object, object, object]
        Tuple of the request counter, latency histogram, and LNM error
        counter. Repeated invocations will return the same metric
        objects without re-registering them.
    """

    global REQUEST_COUNT, REQUEST_LATENCY, LNM_ERROR_COUNT, _metrics_initialized

    if _metrics_initialized:
        logger.debug("Metrics already initialized; reusing existing metrics")
        return REQUEST_COUNT, REQUEST_LATENCY, LNM_ERROR_COUNT

    try:
        REQUEST_COUNT = Counter(
            "kari_http_requests_total",
            "Total HTTP requests",
            registry=PROM_REGISTRY,
        )
        REQUEST_LATENCY = Histogram(
            "kari_http_request_seconds",
            "Latency of HTTP requests",
            registry=PROM_REGISTRY,
        )
        LNM_ERROR_COUNT = Counter(
            "lnm_runtime_errors_total",
            "Total LNM pipeline failures",
            registry=PROM_REGISTRY,
        )
        logger.debug(
            "Metrics initialized successfully: REQUEST_COUNT=%s", REQUEST_COUNT
        )
    except ValueError as e:  # Prometheus duplicates
        if "Duplicated timeseries" in str(e):
            logger.debug("Handling duplicate metrics: %s", e)
            REQUEST_COUNT = None
            REQUEST_LATENCY = None
            LNM_ERROR_COUNT = None
            for collector in PROM_REGISTRY._collector_to_names:  # type: ignore[attr-defined]
                if hasattr(collector, "_name"):
                    if collector._name == "kari_http_requests_total":
                        REQUEST_COUNT = collector
                    elif collector._name == "kari_http_request_seconds":
                        REQUEST_LATENCY = collector
                    elif collector._name == "lnm_runtime_errors_total":
                        LNM_ERROR_COUNT = collector
            if REQUEST_COUNT is None:
                REQUEST_COUNT = _create_dummy_metric()
            if REQUEST_LATENCY is None:
                REQUEST_LATENCY = _create_dummy_metric()
            if LNM_ERROR_COUNT is None:
                LNM_ERROR_COUNT = _create_dummy_metric()
            logger.debug("Reused existing metrics: REQUEST_COUNT=%s", REQUEST_COUNT)
        else:
            logger.debug("Unexpected ValueError during metrics init: %s", e)
            raise
    except Exception as e:  # pragma: no cover - unexpected failure path
        logger.debug("Error initializing metrics: %s", e)
        REQUEST_COUNT = _create_dummy_metric()
        REQUEST_LATENCY = _create_dummy_metric()
        LNM_ERROR_COUNT = _create_dummy_metric()

    _metrics_initialized = True
    return REQUEST_COUNT, REQUEST_LATENCY, LNM_ERROR_COUNT


__all__ = [
    "init_metrics",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "LNM_ERROR_COUNT",
    "generate_latest",
    "CONTENT_TYPE_LATEST",
]
