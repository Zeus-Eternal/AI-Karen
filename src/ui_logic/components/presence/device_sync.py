"""
Kari Device Sync Logic
- Handles device registration and sync operations
"""

from typing import Dict
from ui.hooks.rbac import require_roles
from ui.utils.api import sync_user_devices


def sync_devices(user_ctx: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to sync devices.")
    return sync_user_devices(user_ctx["user_id"])
