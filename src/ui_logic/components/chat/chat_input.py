"""
Kari Chat Input Logic
- Handles user input, prompts, attachments, voice
- RBAC, message validation, input audit
"""

from typing import Dict, Any
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import submit_message, fetch_input_audit

def handle_chat_input(user_ctx: Dict, message: str, attachments: list = None, meta: Dict = None) -> str:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to send messages.")
    return submit_message(user_ctx["user_id"], message, attachments or [], meta)

def get_input_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin"]):
        raise PermissionError("No access to input audit.")
    return fetch_input_audit(user_ctx["user_id"])[-limit:][::-1]
