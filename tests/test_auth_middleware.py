import asyncio
from types import SimpleNamespace

import ai_karen_engine.fastapi_stub as fastapi_stub
import ai_karen_engine.pydantic_stub as pydantic_stub
import sys

sys.modules.setdefault("fastapi", fastapi_stub)
sys.modules.setdefault("pydantic", pydantic_stub)

from ai_karen_engine.middleware.auth import auth_middleware
from ai_karen_engine.utils.auth import create_session
from ai_karen_engine.fastapi_stub import Response


async def _call_next(request):
    return Response({"ok": True})


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
