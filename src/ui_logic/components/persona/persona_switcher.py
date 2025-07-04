"""
Kari Persona Switcher Logic
- Fast persona, role, or mood switching
- Secure, config-driven, and fully auditable
"""

from typing import Dict, List
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_personas, switch_persona, fetch_audit_logs

def get_available_personas(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "branding"]):
        raise PermissionError("Insufficient privileges for persona switching.")
    return fetch_personas(user_ctx["user_id"])

def set_persona(user_ctx: Dict, persona_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "branding"]):
        raise PermissionError("Insufficient privileges to set persona.")
    return switch_persona(user_ctx["user_id"], persona_id)

def get_persona_switch_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "branding"]):
        raise PermissionError("Insufficient privileges for persona switch audit.")
    return fetch_audit_logs(category="persona_switch", user_id=user_ctx["user_id"])[-limit:][::-1]
