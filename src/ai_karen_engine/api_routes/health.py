from __future__ import annotations

"""Health monitoring API routes.

Expose structured service health information with Prometheus metrics,
correlation-aware logging, and circuit breaker support.
"""

import time
from typing import Any, Dict

from ai_karen_engine.utils.dependency_checks import import_fastapi
from ai_karen_engine.services.connection_health_manager import (
    ConnectionHealthManager,
    get_connection_health_manager,
)
from ai_karen_engine.services.correlation_service import get_request_id
from ai_karen_engine.services.structured_logging import (
    get_structured_logging_service,
)

APIRouter, Request = import_fastapi("APIRouter", "Request")

# ---------------------------------------------------------------------------
# Prometheus metrics with safe fallbacks
# ---------------------------------------------------------------------------
try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram

    _REQ_COUNTER = Counter(
        "health_endpoint_requests_total",
        "Total health endpoint requests",
        ["endpoint"],
    )
    _LATENCY_HIST = Histogram(
        "health_endpoint_latency_seconds",
        "Latency for health endpoint requests",
        ["endpoint"],
    )
except Exception:  # pragma: no cover - prometheus optional

    class _DummyMetric:
        def labels(self, **_kwargs):  # type: ignore[override]
            return self

        def inc(self, *_args, **_kwargs):  # type: ignore[override]
            pass

        def observe(self, *_args, **_kwargs):  # type: ignore[override]
            pass

    _REQ_COUNTER = _DummyMetric()
    _LATENCY_HIST = _DummyMetric()


router = APIRouter()


def _record_metrics(endpoint: str, duration_ms: float) -> None:
    """Record Prometheus metrics if available."""
    _REQ_COUNTER.labels(endpoint=endpoint).inc()
    _LATENCY_HIST.labels(endpoint=endpoint).observe(duration_ms / 1000)


def _collect_health(manager: ConnectionHealthManager) -> Dict[str, Any]:
    """Collect health status for all registered services."""
    services: Dict[str, Any] = {}
    for name in list(manager.health_status.keys()):
        try:
            result = manager.health_status[name]
            services[name] = {
                "status": result.status.value,
                "last_check": result.last_check.isoformat(),
                "response_time_ms": result.response_time_ms,
                "degraded_features": result.degraded_features,
            }
        except Exception as exc:  # pragma: no cover - defensive
            services[name] = {"status": "unknown", "error": str(exc)}
    return services


@router.get("")
async def overall_health(request: Request) -> Dict[str, Any]:
    """Return overall health status for registered services."""
    start = time.time()
    correlation_id = request.headers.get("X-Correlation-Id") or get_request_id()
    manager = get_connection_health_manager()

    # Perform health checks with circuit breaker protection
    for name in list(manager.health_status.keys()):
        try:
            await manager.check_service_health(name)
        except Exception:
            # check_service_health already handles circuit breaker and
            # degraded mode. Failures are reflected in status.
            pass

    services = _collect_health(manager)
    overall = (
        "healthy"
        if all(s["status"] == "healthy" for s in services.values())
        else "degraded"
    )

    duration_ms = (time.time() - start) * 1000
    _record_metrics("overall", duration_ms)

    get_structured_logging_service().log_api_request(
        method="GET",
        endpoint="/api/health",
        status_code=200,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
    )

    return {
        "status": overall,
        "services": services,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }


@router.get("/{service_name}")
async def service_health(service_name: str, request: Request) -> Dict[str, Any]:
    """Return health status for a specific service."""
    start = time.time()
    correlation_id = request.headers.get("X-Correlation-Id") or get_request_id()
    manager = get_connection_health_manager()

    try:
        result = await manager.check_service_health(service_name)
        status = {
            "status": result.status.value,
            "last_check": result.last_check.isoformat(),
            "response_time_ms": result.response_time_ms,
            "degraded_features": result.degraded_features,
        }
        code = 200
    except Exception as exc:
        status = {"status": "unknown", "error": str(exc)}
        code = 404

    duration_ms = (time.time() - start) * 1000
    _record_metrics(service_name, duration_ms)

    get_structured_logging_service().log_api_request(
        method="GET",
        endpoint=f"/api/health/{service_name}",
        status_code=code,
        duration_ms=duration_ms,
        correlation_id=correlation_id,
    )

    return {"service": service_name, "result": status, "correlation_id": correlation_id}


__all__ = ["router"]

