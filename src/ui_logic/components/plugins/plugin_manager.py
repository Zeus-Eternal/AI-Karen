"""
Kari Plugin Manager Logic
- Secure plugin CRUD, RBAC, and audit
"""

from typing import Dict, List
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import (
    list_plugins,
    install_plugin,
    uninstall_plugin,
    enable_plugin,
    disable_plugin,
    fetch_audit_logs,
)

def get_plugins(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "developer"]):
        raise PermissionError("Insufficient privileges to view plugins.")
    return list_plugins(user_ctx["user_id"])

def install_new_plugin(user_ctx: Dict, plugin_meta: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to install plugin.")
    return install_plugin(user_ctx["user_id"], plugin_meta)

def remove_plugin(user_ctx: Dict, plugin_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to remove plugin.")
    return uninstall_plugin(user_ctx["user_id"], plugin_id)

def set_plugin_enabled(user_ctx: Dict, plugin_id: str, enabled: bool) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to enable/disable plugin.")
    if enabled:
        return enable_plugin(user_ctx["user_id"], plugin_id)
    return disable_plugin(user_ctx["user_id"], plugin_id)

def get_plugins_audit_trail(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges for plugin audit.")
    return fetch_audit_logs(category="plugin", user_id=user_ctx["user_id"])[-limit:][::-1]
