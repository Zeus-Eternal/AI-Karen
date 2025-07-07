"""
Kari Model Selector Logic
- Provides all available models (local/cloud, by provider)
- Enforces RBAC and feature flags
"""

from typing import Dict, List
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import fetch_available_models

def get_available_models(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges for model selection.")
    return fetch_available_models(user_ctx.get("user_id"))
