"""
Kari Widget Builder Logic (Framework-Agnostic)
- API for embeddable widget CRUD, sharing, and audit
- RBAC-secured (admin/developer only)
"""

from typing import Dict, List, Optional
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import (
    list_widgets, 
    save_widget, 
    delete_widget, 
    fetch_audit_logs
)

def get_widgets(user_ctx: Dict) -> List[Dict]:
    """Return all embeddable widgets for the user (RBAC: admin/developer only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to access widgets.")
    return list_widgets(owner=user_ctx["user_id"])

def create_widget(user_ctx: Dict, config: Dict) -> str:
    """Create a new widget and return its embed code."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to create widgets.")
    return save_widget(config, user_ctx["user_id"])

def remove_widget(user_ctx: Dict, widget_id: str):
    """Delete a widget (RBAC: admin/developer only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to delete widgets.")
    return delete_widget(widget_id, user_ctx["user_id"])

def get_widget_audit_trail(user_ctx: Dict, limit: int = 25):
    """Fetch audit log for widget actions."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges for widget audit trail.")
    return fetch_audit_logs(category="widget", user_id=user_ctx["user_id"])[-limit:][::-1]
