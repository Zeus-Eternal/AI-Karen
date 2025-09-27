from typing import Any, Dict

import pytest

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover - fastapi optional
    FASTAPI_AVAILABLE = False
    FastAPI = TestClient = None

from ai_karen_engine.api_routes.health import router
from ai_karen_engine.services.connection_health_manager import (
    ConnectionType,
    initialize_connection_health_manager,
    shutdown_connection_health_manager,
)


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
@pytest.mark.asyncio
async def test_health_endpoints_return_service_status() -> None:
    manager = await initialize_connection_health_manager(start_monitoring=False)
    manager.register_service("dummy", ConnectionType.DATABASE, lambda: True)

    app = FastAPI()
    app.include_router(router, prefix="/api")
    client = TestClient(app)

    response = client.get("/api/health", headers={"X-Correlation-Id": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["services"]["dummy"]["status"] == "healthy"
    assert data["correlation_id"] == "test"

    response = client.get("/api/health/dummy")
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["status"] == "healthy"

    await shutdown_connection_health_manager()


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_degraded_mode_compatibility_payload(monkeypatch) -> None:
    fake_payload = {
        "is_active": True,
        "reason": "all_providers_failed",
        "activated_at": "2024-01-01T00:00:00Z",
        "failed_providers": ["openai"],
        "remote_provider_outages": ["openai"],
        "recovery_attempts": 1,
        "last_recovery_attempt": None,
        "core_helpers_available": {
            "fallback_responses": True,
            "local_fallback_ready": True,
            "total_ai_capabilities": 1,
        },
        "infrastructure_issues": ["database"],
        "ai_status": "degraded",
    }

    async def _fake_status() -> Dict[str, Any]:
        return fake_payload

    monkeypatch.setattr(
        "ai_karen_engine.api_routes.health._build_degraded_mode_status",
        _fake_status,
    )

    app = FastAPI()
    app.include_router(router, prefix="/api")
    client = TestClient(app)

    response = client.get("/api/health/degraded-mode/compat")
    assert response.status_code == 200
    data = response.json()
    assert data["degraded_mode"] is True
    assert data["is_active"] is True
    assert data["ai_status"] == fake_payload["ai_status"]
    assert data["payload"]["failed_providers"] == fake_payload["failed_providers"]
