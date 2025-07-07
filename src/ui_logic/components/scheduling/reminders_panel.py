"""
Kari Reminders Panel Logic
- Secure reminder CRUD, RBAC, audit trail
"""

from typing import Dict, List
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import (
    fetch_reminders,
    add_reminder,
    remove_reminder,
    update_reminder,
    fetch_audit_logs,
)

def get_reminders(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to access reminders.")
    return fetch_reminders(user_ctx["user_id"])

def create_reminder(user_ctx: Dict, reminder: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to create reminder.")
    return add_reminder(user_ctx["user_id"], reminder)

def delete_reminder(user_ctx: Dict, reminder_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to delete reminder.")
    return remove_reminder(user_ctx["user_id"], reminder_id)

def modify_reminder(user_ctx: Dict, reminder_id: str, updates: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to update reminder.")
    return update_reminder(user_ctx["user_id"], reminder_id, updates)

def get_reminders_audit_trail(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for reminders audit.")
    return fetch_audit_logs(category="reminder", user_id=user_ctx["user_id"])[-limit:][::-1]
