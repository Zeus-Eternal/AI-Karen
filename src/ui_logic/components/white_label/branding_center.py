"""
Kari Branding Center Logic (Framework-Agnostic)
- Enterprise branding CRUD and audit
- RBAC-secured (enterprise/admin only)
"""

from typing import Dict, Optional
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_branding_config,
    save_branding_config,
    fetch_audit_logs
)

def get_branding_config(user_ctx: Dict) -> Dict:
    """Fetch current branding config (RBAC: admin/enterprise only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "enterprise"]):
        raise PermissionError("Insufficient privileges for branding center.")
    return fetch_branding_config()

def update_branding_config(user_ctx: Dict, config: Dict):
    """Update branding config (RBAC: admin/enterprise only)."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "enterprise"]):
        raise PermissionError("Insufficient privileges to update branding.")
    return save_branding_config(config, user_ctx["user_id"])

def get_branding_audit_trail(user_ctx: Dict, limit: int = 25):
    """Fetch audit log for branding changes."""
    if not user_ctx or not require_roles(user_ctx, ["admin", "enterprise"]):
        raise PermissionError("Insufficient privileges for branding audit.")
    return fetch_audit_logs(category="branding", user_id=user_ctx["user_id"])[-limit:][::-1]
