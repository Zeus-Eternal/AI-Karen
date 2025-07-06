import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_session_memory, fetch_audit_logs

logger = logging.getLogger("kari.memory.session_core")
logger.setLevel(logging.INFO)

class SessionExplorerError(Exception):
    pass

def check_session_permissions(user_ctx: Dict[str, Any], roles=None):
    try:
        require_roles(user_ctx, roles or ["user", "admin", "analyst"])
        return True
    except Exception as e:
        logger.warning(f"RBAC failure: {e}")
        return False

def get_session_records(
    user_ctx: Dict[str, Any],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 200
) -> List[Dict[str, Any]]:
    if not check_session_permissions(user_ctx):
        raise PermissionError("Insufficient privileges for session memory access.")
    try:
        records = fetch_session_memory(
            session_id=session_id,
            user_id=user_id or user_ctx.get("user_id"),
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            token=user_ctx.get("token"),
            org=user_ctx.get("org_id")
        )
        return records or []
    except Exception as e:
        logger.error(f"Failed to fetch session memory: {e}")
        raise

def get_audit_logs_for_entry(
    user_ctx: Dict[str, Any],
    entry: Dict[str, Any],
    limit: int = 10
) -> List[Dict[str, Any]]:
    if not check_session_permissions(user_ctx, ["admin"]):
        raise PermissionError("Audit log access denied.")
    try:
        return fetch_audit_logs(
            category="memory_event",
            user_id=entry.get("user_id"),
            search=entry.get("id"),
            limit=limit,
            token=user_ctx.get("token"),
            org=user_ctx.get("org_id")
        )
    except Exception as e:
        logger.warning(f"Audit log fetch failed: {e}")
        return []
