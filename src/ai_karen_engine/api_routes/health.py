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


@router.get("/degraded-mode")
async def degraded_mode_status() -> Dict[str, Any]:
    """Check if system is running in degraded mode"""
    try:
        # Check various system components for degraded mode
        degraded_components = []
        
        # Check database
        try:
            from ai_karen_engine.services.database_connection_manager import get_database_manager
            db_manager = get_database_manager()
            if db_manager.is_degraded():
                degraded_components.append("database")
        except Exception:
            degraded_components.append("database")
        
        # Check Redis
        try:
            from ai_karen_engine.services.redis_connection_manager import get_redis_manager
            redis_manager = get_redis_manager()
            if redis_manager.is_degraded():
                degraded_components.append("redis")
        except Exception:
            degraded_components.append("redis")
        
        # Check AI providers - but consider local models as available
        failed_providers = []
        try:
            from ai_karen_engine.services.provider_registry import get_provider_registry_service
            provider_service = get_provider_registry_service()
            system_status = provider_service.get_system_status()
            
            # Check if we have local models available
            from pathlib import Path
            models_dir = Path("models")
            tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").exists()
            
            # Check spaCy availability
            spacy_available = False
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
            except:
                pass
            
            # Only consider degraded if NO providers AND NO local models
            if system_status["available_providers"] == 0 and not (tinyllama_available or spacy_available):
                degraded_components.append("ai_providers")
                failed_providers = system_status.get("failed_providers", [])
            elif system_status["available_providers"] == 0:
                # We have local models, so just note the failed remote providers
                failed_providers = system_status.get("failed_providers", [])
                
        except Exception:
            # Check if local models are available as fallback
            try:
                from pathlib import Path
                models_dir = Path("models")
                tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").exists()
                
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
                
                # Only degraded if no local models
                if not (tinyllama_available or spacy_available):
                    degraded_components.append("ai_providers")
                    failed_providers = ["unknown"]
            except:
                degraded_components.append("ai_providers")
                failed_providers = ["unknown"]
        
        is_degraded = len(degraded_components) > 0
        
        # Determine degraded mode reason
        reason = None
        if is_degraded:
            if "ai_providers" in degraded_components and "database" in degraded_components:
                reason = "all_providers_failed"
            elif "database" in degraded_components:
                reason = "network_issues"
            elif "ai_providers" in degraded_components:
                reason = "all_providers_failed"
            else:
                reason = "resource_exhaustion"
        
        # Core helpers availability - check actual availability
        try:
            from pathlib import Path
            models_dir = Path("models")
            tinyllama_available = (models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf").exists()
            
            spacy_available = False
            try:
                import spacy
                nlp = spacy.load("en_core_web_sm")
                spacy_available = True
            except:
                pass
            
            core_helpers_available = {
                "local_nlp": spacy_available,  # spaCy NLP processing
                "local_llm": tinyllama_available,  # TinyLlama for text generation
                "fallback_responses": True,  # Always available
                "basic_analytics": True,  # Basic analytics work
                "file_operations": True,  # File ops work
                "database_fallback": "database" not in degraded_components
            }
        except Exception:
            core_helpers_available = {
                "local_nlp": False,
                "local_llm": False,
                "fallback_responses": True,
                "basic_analytics": True,
                "file_operations": True,
                "database_fallback": False
            }
        
        from datetime import datetime, timezone
        return {
            "is_active": is_degraded,
            "reason": reason,
            "activated_at": datetime.now(timezone.utc).isoformat() if is_degraded else None,
            "failed_providers": failed_providers,
            "recovery_attempts": 0,  # Could track this in a persistent store
            "last_recovery_attempt": None,  # Could track this too
            "core_helpers_available": core_helpers_available
        }
        
    except Exception as e:
        from datetime import datetime, timezone
        return {
            "is_active": True,
            "reason": "resource_exhaustion",
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "failed_providers": ["unknown"],
            "recovery_attempts": 0,
            "last_recovery_attempt": None,
            "core_helpers_available": {
                "local_nlp": False,
                "local_llm": False,
                "fallback_responses": True,
                "basic_analytics": True,
                "file_operations": True,
                "database_fallback": False
            }
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

