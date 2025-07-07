"""
Kari Persona Analytics Logic
- Tracks persona switch usage, sentiment, and user impact
- RBAC: user, admin, analyst
- All access is audit-logged
"""

from typing import Dict, List
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import fetch_persona_analytics, fetch_audit_logs

def get_persona_analytics(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("Insufficient privileges for persona analytics.")
    return fetch_persona_analytics(user_ctx["user_id"])

def get_persona_analytics_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges for persona analytics audit.")
    return fetch_audit_logs(category="persona_analytics", user_id=user_ctx["user_id"])[-limit:][::-1]
