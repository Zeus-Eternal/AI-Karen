from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from ai_karen_engine.core.dependencies import get_current_user_context

router = APIRouter(tags=["audit"])


# Alias core dependency for convenience
get_current_user = get_current_user_context

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


@router.get("/logs")
async def get_audit_logs(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 100,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
):
    logs = list(_AUDIT_LOGS)
    if category:
        logs = [log for log in logs if log.get("action") == category]
    if user_id:
        logs = [log for log in logs if log.get("user_id") == user_id]
    return logs[-limit:][::-1]
