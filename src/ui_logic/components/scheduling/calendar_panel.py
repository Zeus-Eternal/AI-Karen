"""
Kari Calendar Panel Business Logic
- Secure, RBAC-guarded, multi-calendar operations
"""

from typing import Dict, List
from ui.hooks.rbac import require_roles
from ui.utils.api import (
    fetch_user_calendar,
    add_event_to_calendar,
    remove_event_from_calendar,
    update_calendar_event,
    fetch_audit_logs,
)

def get_calendar(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to access calendar.")
    return fetch_user_calendar(user_ctx["user_id"])

def add_event(user_ctx: Dict, event: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to add event.")
    return add_event_to_calendar(user_ctx["user_id"], event)

def remove_event(user_ctx: Dict, event_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to remove event.")
    return remove_event_from_calendar(user_ctx["user_id"], event_id)

def update_event(user_ctx: Dict, event_id: str, updates: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to update event.")
    return update_calendar_event(user_ctx["user_id"], event_id, updates)

def get_calendar_audit_trail(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for calendar audit.")
    return fetch_audit_logs(category="calendar", user_id=user_ctx["user_id"])[-limit:][::-1]
