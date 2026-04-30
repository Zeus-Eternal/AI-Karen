import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from ai_karen_engine.api_routes.memory import memory as memory_routes


class _UnavailableRuntime:
    available = False
    service = None
    reason = "memory_runtime_unavailable"


@pytest.fixture()
def client(monkeypatch):
    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request: Request, call_next):
        request.state.user = {"user_id": "u1", "org_id": "o1"}
        return await call_next(request)

    app.include_router(memory_routes.router)

    async def _allow(*_args, **_kwargs):
        return True

    monkeypatch.setattr(memory_routes, "check_rbac_scope", _allow)
    return TestClient(app)


@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("post", "/memory/search", {"user_id": "u1", "org_id": "o1", "query": "hello", "top_k": 3}),
        ("post", "/memory/commit", {"user_id": "u1", "org_id": "o1", "text": "hello", "tags": [], "importance": 5, "decay": "short"}),
    ],
)
def test_unavailable_backend_returns_503_with_deterministic_metadata(client, monkeypatch, method, path, payload):
    async def _resolve():
        return _UnavailableRuntime()

    monkeypatch.setattr(memory_routes, "resolve_memory_runtime", _resolve)

    response = getattr(client, method)(path, json=payload)
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["message"] == "Memory backend unavailable"
    assert detail["details"]["backend"] == "neuro_vault"
    assert detail["details"]["reason"] == "memory_runtime_unavailable"


def test_cross_tenant_rejected_before_backend_execution(client, monkeypatch):
    called = {"value": False}

    async def _resolve():
        called["value"] = True
        return _UnavailableRuntime()

    monkeypatch.setattr(memory_routes, "resolve_memory_runtime", _resolve)

    response = client.post(
        "/memory/search",
        json={"user_id": "u-other", "org_id": "o1", "query": "hello", "top_k": 1},
    )
    assert response.status_code == 403
    assert called["value"] is False
