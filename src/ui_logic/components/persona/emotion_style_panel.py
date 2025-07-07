"""
Kari Persona: Emotion & Style Panel Logic
- Configure AI's tone, mood, language, and affect
- RBAC-secured (user, admin, branding)
- All mutations are audit-logged
"""

from typing import Dict, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_emotion_styles, save_emotion_style, fetch_audit_logs

def get_emotion_styles(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "branding"]):
        raise PermissionError("Insufficient privileges for emotion/style panel.")
    return fetch_emotion_styles(user_ctx["user_id"])

def update_emotion_style(user_ctx: Dict, style_id: str, config: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "branding"]):
        raise PermissionError("Insufficient privileges to update emotion style.")
    return save_emotion_style(user_ctx["user_id"], style_id, config)

def get_emotion_style_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "branding"]):
        raise PermissionError("Insufficient privileges for emotion style audit.")
    return fetch_audit_logs(category="emotion_style", user_id=user_ctx["user_id"])[-limit:][::-1]
