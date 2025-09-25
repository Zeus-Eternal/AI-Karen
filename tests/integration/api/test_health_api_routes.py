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
    app.include_router(router, prefix="/api/health")
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
