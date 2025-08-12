import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.ai_karen_engine.api_routes.memory_routes import router as memory_router
from src.ai_karen_engine.api_routes.copilot_routes import router as copilot_router


@pytest.fixture
def memory_client():
    app = FastAPI()
    app.include_router(memory_router, prefix="/memory")
    return TestClient(app)


@pytest.fixture
def copilot_client():
    app = FastAPI()
    app.include_router(copilot_router, prefix="/copilot")
    return TestClient(app)


def test_memory_search_unauthorized(memory_client):
    payload = {
        "user_id": "u1",
        "org_id": "o1",
        "query": "hi",
        "top_k": 1,
    }
    with patch(
        "src.ai_karen_engine.api_routes.memory_routes.check_rbac_scope",
        new=AsyncMock(return_value=False),
    ):
        response = memory_client.post("/memory/search", json=payload)
    assert response.status_code == 403


def test_memory_search_rbac_unavailable(memory_client):
    payload = {
        "user_id": "u1",
        "org_id": "o1",
        "query": "hi",
        "top_k": 1,
    }
    with patch(
        "src.ai_karen_engine.api_routes.memory_routes.RBAC_AVAILABLE",
        False,
    ):
        response = memory_client.post("/memory/search", json=payload)
    assert response.status_code == 403


def test_copilot_assist_unauthorized(copilot_client):
    payload = {
        "user_id": "u1",
        "org_id": "o1",
        "message": "hi",
        "top_k": 1,
        "context": {},
    }
    with patch(
        "src.ai_karen_engine.api_routes.copilot_routes.check_rbac_scope",
        new=AsyncMock(return_value=False),
    ):
        response = copilot_client.post("/copilot/assist", json=payload)
    assert response.status_code == 403


def test_copilot_assist_rbac_error(copilot_client):
    payload = {
        "user_id": "u1",
        "org_id": "o1",
        "message": "hi",
        "top_k": 1,
        "context": {},
    }
    with patch(
        "src.ai_karen_engine.api_routes.copilot_routes.check_scope",
        new=AsyncMock(side_effect=Exception("boom")),
    ):
        response = copilot_client.post("/copilot/assist", json=payload)
    assert response.status_code == 403
