"""
Kari Follow-Up Engine Logic
- Secure follow-up and reminder management
"""

from typing import Dict, List
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import (
    fetch_follow_ups,
    create_follow_up,
    remove_follow_up,
    update_follow_up,
    fetch_audit_logs,
)

def get_follow_ups(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to access follow-ups.")
    return fetch_follow_ups(user_ctx["user_id"])

def add_follow_up(user_ctx: Dict, follow_up: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to add follow-up.")
    return create_follow_up(user_ctx["user_id"], follow_up)

def remove_follow_up_item(user_ctx: Dict, followup_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to remove follow-up.")
    return remove_follow_up(user_ctx["user_id"], followup_id)

def update_follow_up_item(user_ctx: Dict, followup_id: str, updates: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to update follow-up.")
    return update_follow_up(user_ctx["user_id"], followup_id, updates)

def get_follow_up_audit_trail(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for follow-up audit.")
    return fetch_audit_logs(category="follow_up", user_id=user_ctx["user_id"])[-limit:][::-1]
