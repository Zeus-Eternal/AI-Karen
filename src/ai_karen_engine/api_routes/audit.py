from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request

from ai_karen_engine.utils.auth import validate_session

router = APIRouter(prefix="/api/audit", tags=["audit"])

_AUDIT_LOGS: List[dict] = [
    {
        "id": str(uuid.uuid4()),
        "user_id": "admin",
        "action": "login",
        "resource_type": "auth",
        "resource_id": "login",
        "details": {},
        "created_at": "2025-07-28T00:00:00Z",
    }
]


def _get_context(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing token")
    token = auth.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=401, detail="invalid token")
    return ctx


@router.get("/logs")
async def get_audit_logs(
    request: Request,
    limit: int = 100,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
):
    _get_context(request)
    logs = list(_AUDIT_LOGS)
    if category:
        logs = [l for l in logs if l.get("action") == category]
    if user_id:
        logs = [l for l in logs if l.get("user_id") == user_id]
    return logs[-limit:][::-1]
