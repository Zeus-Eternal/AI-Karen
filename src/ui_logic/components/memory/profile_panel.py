"""
Kari Profile Panel Logic
- Loads editable user/shadow profiles (skills, traits, interests)
- RBAC: user (self-edit), admin (org-edit), audit-logged
"""

from typing import Dict, Any
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_user_profile, save_user_profile, fetch_audit_logs

def get_user_profile(user_ctx: Dict) -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for profile access.")
    return fetch_user_profile(user_ctx.get("user_id"))

def update_user_profile(user_ctx: Dict, profile: Dict[str, Any]):
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for profile editing.")
    return save_user_profile(user_ctx.get("user_id"), profile)

def get_profile_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin"]):
        raise PermissionError("Insufficient privileges for profile audit.")
    return fetch_audit_logs(category="profile", user_id=user_ctx["user_id"])[-limit:][::-1]
