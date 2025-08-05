import asyncio
from types import SimpleNamespace

from types import SimpleNamespace

from fastapi import Response

from ai_karen_engine.middleware.auth import auth_middleware
from ai_karen_engine.utils.auth import create_session


async def _call_next(request):
    return Response(content="ok")


def _build_request(path="/plugins", token: str | None = None):
    headers = {"user-agent": "agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
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
