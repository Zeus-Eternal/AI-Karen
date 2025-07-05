"""
Kari IoT Logs Panel
- Query, search, and audit device logs/events
- RBAC: user (own), admin/devops (all)
"""

from typing import Dict, List, Any
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_iot_logs, fetch_audit_logs

def get_iot_logs(user_ctx: Dict, device_id: str = None, search: str = "") -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "devops"]):
        raise PermissionError("Insufficient privileges for IoT logs.")
    return fetch_iot_logs(user_ctx.get("user_id"), device_id=device_id, search=search)

def get_iot_log_audit(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "devops"]):
        raise PermissionError("Insufficient privileges for IoT log audit.")
    return fetch_audit_logs(category="iot_log", user_id=user_ctx["user_id"])[-limit:][::-1]
