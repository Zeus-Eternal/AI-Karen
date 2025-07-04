"""
Kari Status Monitor Logic
- Provides real-time device/session status
"""

from typing import Dict
from ui.hooks.rbac import require_roles
from ui.utils.api import fetch_device_status


def get_device_status(user_ctx: Dict) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Insufficient privileges to access device status.")
    return fetch_device_status(user_ctx["user_id"])
