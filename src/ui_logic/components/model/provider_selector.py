"""
Kari LLM Provider Selector Logic
- Lists available providers, with RBAC and config
"""

from typing import Dict, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_providers

def get_available_providers(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for provider selection.")
    return fetch_providers(user_ctx.get("user_id"))
