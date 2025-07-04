"""
Kari Session Explorer Logic
- Lists and audits all session memory, events, and extracted facts
- RBAC: user (own), admin/analyst (all), config-driven audit
"""

from typing import Dict, Any, List
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_session_memory, fetch_audit_logs

def get_session_memory(user_ctx: Dict, session_id: str = None) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("Insufficient privileges for session memory access.")
    return fetch_session_memory(user_ctx.get("user_id"), session_id=session_id)

def get_session_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges for session audit.")
    return fetch_audit_logs(category="session", user_id=user_ctx["user_id"])[-limit:][::-1]
