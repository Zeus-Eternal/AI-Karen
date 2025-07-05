"""
Kari Chat Context Panel Logic
- Surfaces session memory, facts, extracted entities
- RBAC: user/admin/analyst
"""

from typing import Dict, Any
from ui_logic.hooks.rbac import require_roles
from ui_logic.hooks.memory_hook import fetch_session_memory

def get_session_context(user_ctx: Dict) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("No access to session context.")
    return fetch_session_memory(user_ctx)
