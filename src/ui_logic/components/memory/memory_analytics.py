"""
Kari Memory Analytics Logic
- Visualizes memory usage, retrievals, hit/miss rates, and recency
- RBAC: admin, analyst, user (read-only)
"""

from typing import Dict, Any, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_memory_analytics, fetch_audit_logs

def get_memory_analytics(user_ctx: Dict) -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst", "user"]):
        raise PermissionError("Insufficient privileges for memory analytics.")
    return fetch_memory_analytics(user_ctx.get("user_id"))

def get_memory_audit(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Insufficient privileges for memory audit.")
    return fetch_audit_logs(category="memory", user_id=user_ctx["user_id"])[-limit:][::-1]
