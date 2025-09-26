"""Tests for development-mode authentication fallback."""

import importlib
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


class DummyRequest:
    """Minimal request object compatible with dependency helpers."""

    def __init__(self, path: str = "/api/chat/runtime") -> None:
        self.url = SimpleNamespace(path=path)
        self.headers = {}
        self.client = SimpleNamespace(host="127.0.0.1")


@pytest.fixture
def dependencies(monkeypatch):
    """Import the dependencies module with required environment defaults."""

    monkeypatch.setenv("KARI_DUCKDB_PASSWORD", "test-password")
    monkeypatch.setenv("KARI_JOB_SIGNING_KEY", "test-signing")
    module = importlib.import_module("ai_karen_engine.core.dependencies")
    return importlib.reload(module)


@pytest.mark.asyncio
async def test_dev_fallback_returns_synthetic_user(monkeypatch, dependencies):
    """When dev mode is enabled we should synthesize a user context."""

    monkeypatch.setenv("AUTH_DEV_MODE", "true")
    monkeypatch.setenv("AUTH_MODE", "development")

    class DummyMiddleware:
        async def authenticate_request(self, request):  # type: ignore[override]
            raise HTTPException(status_code=401, detail="Missing token")

    monkeypatch.setattr(
        "src.auth.auth_middleware.get_auth_middleware",
        lambda: DummyMiddleware(),
    )

    user_ctx = await dependencies.get_current_user_context(DummyRequest())

    assert user_ctx["user_id"] == "dev-user"
    assert user_ctx["tenant_id"] == "default"
    assert user_ctx["is_development_fallback"] is True
    assert user_ctx["roles"]  # ensure roles were assigned


@pytest.mark.asyncio
async def test_authenticated_user_preserved(monkeypatch, dependencies):
    """Real authenticated users should be returned even in dev mode."""

    monkeypatch.setenv("AUTH_DEV_MODE", "true")

    class DummyMiddleware:
        async def authenticate_request(self, request):  # type: ignore[override]
            return {"user_id": "actual-user", "roles": ["user"]}

    monkeypatch.setattr(
        "src.auth.auth_middleware.get_auth_middleware",
        lambda: DummyMiddleware(),
    )

    user_ctx = await dependencies.get_current_user_context(DummyRequest())

    assert user_ctx["user_id"] == "actual-user"
    assert user_ctx["tenant_id"] == "default"
    assert "is_development_fallback" not in user_ctx


@pytest.mark.asyncio
async def test_authentication_required_when_dev_disabled(monkeypatch, dependencies):
    """Without dev flags the dependency should propagate auth failures."""

    monkeypatch.delenv("AUTH_DEV_MODE", raising=False)
    monkeypatch.delenv("AUTH_ALLOW_DEV_LOGIN", raising=False)
    monkeypatch.setenv("AUTH_MODE", "production")

    class DummyMiddleware:
        async def authenticate_request(self, request):  # type: ignore[override]
            raise HTTPException(status_code=401, detail="Missing token")

    monkeypatch.setattr(
        "src.auth.auth_middleware.get_auth_middleware",
        lambda: DummyMiddleware(),
    )

    with pytest.raises(HTTPException):
        await dependencies.get_current_user_context(DummyRequest())
