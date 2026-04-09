from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from ai_karen_engine.core.dependencies import (
    bypass_user_context_func as get_current_user,
)
from ai_karen_engine.services.audit_logging import get_audit_logger

router = APIRouter(tags=["audit"])


# Alias already created in import

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
    logs = get_audit_logger().get_recent_events(limit=limit)
    if category:
        logs = [log for log in logs if str(log.get("event_type") or "") == category]
    if user_id:
        logs = [log for log in logs if str(log.get("user_id") or "") == user_id]
    return logs
