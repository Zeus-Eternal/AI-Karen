"""
Kari Chat Window Logic
- Returns chat history, renders message context, supports infinite scroll
- RBAC on chat retrieval, context shaping
"""

from typing import Dict, List, Any
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import fetch_chat_history

def get_chat_history(user_ctx: Dict, limit: int = 50) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized to view chat history.")
    return fetch_chat_history(user_ctx["user_id"], limit)
