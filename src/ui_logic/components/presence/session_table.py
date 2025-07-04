"""
Kari Session Table Logic
- Lists active sessions and their metadata
"""

from typing import Dict, List
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_active_sessions, fetch_audit_logs


def get_active_sessions(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to view sessions.")
    return fetch_active_sessions(user_ctx["user_id"])


def get_session_audit(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin"]):
        raise PermissionError("Insufficient privileges for session audit.")
    return fetch_audit_logs(category="sessions", user_id=user_ctx["user_id"])[-limit:][::-1]
