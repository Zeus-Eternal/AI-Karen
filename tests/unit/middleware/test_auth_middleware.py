"""Tests for auth middleware."""

# mypy: ignore-errors

import asyncio
import hashlib
import uuid
from contextlib import contextmanager
from types import SimpleNamespace

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_karen_engine.database.models import ApiKey, Base, Role, RolePermission
from ai_karen_engine.middleware.auth import auth_middleware
from ai_karen_engine.utils.auth import create_session


async def _call_next(request):
    return Response(content="ok")


def _build_request(
    path: str = "/plugins",
    token: str | None = None,
    api_key: str | None = None,
    scopes: str | None = None,
):
    headers = {"user-agent": "agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["X-API-Key"] = api_key
    if scopes:
        headers["X-Required-Scopes"] = scopes
    return SimpleNamespace(
        url=SimpleNamespace(path=path),
        headers=headers,
        client=SimpleNamespace(host="1.1.1.1"),
        state=SimpleNamespace(),
    )


def test_missing_token():
    req = _build_request()
    resp = asyncio.run(auth_middleware(req, _call_next))
    assert resp.status_code == 401


def test_invalid_token():
    req = _build_request(token="bad")
    resp = asyncio.run(auth_middleware(req, _call_next))
    assert resp.status_code == 401


def test_valid_token():
    token = create_session("admin", ["admin"], "agent", "1.1.1.1")
    req = _build_request(token=token)
    resp = asyncio.run(auth_middleware(req, _call_next))
    assert resp.status_code == 200
    assert getattr(req.state, "user", None) == "admin"
    assert "admin" in getattr(req.state, "roles", [])


def test_api_key_valid(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    @contextmanager
    def fake_ctx():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(
        "ai_karen_engine.middleware.auth.get_db_session_context", fake_ctx
    )

    key = "secret"
    hashed = hashlib.sha256(key.encode()).hexdigest()
    with Session() as session:
        session.add(
            ApiKey(key_id=str(uuid.uuid4()), hashed_key=hashed, scopes=["chat:read"])
        )
        session.commit()

    req = _build_request(api_key=key)
    resp = asyncio.run(auth_middleware(req, _call_next))
    assert resp.status_code == 200
    assert getattr(req.state, "scopes", []) == ["chat:read"]


def test_rbac_scope_denied(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    @contextmanager
    def fake_ctx():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(
        "ai_karen_engine.middleware.auth.get_db_session_context", fake_ctx
    )

    with Session() as session:
        role = Role(role_id=str(uuid.uuid4()), tenant_id="default", name="user")
        session.add(role)
        session.add(
            RolePermission(role_id=role.role_id, permission="chat:read", scope="*")
        )
        session.commit()

    token = create_session("user", ["user"], "agent", "1.1.1.1")
    req = _build_request(token=token, scopes="chat:write")
    resp = asyncio.run(auth_middleware(req, _call_next))
    assert resp.status_code == 403
