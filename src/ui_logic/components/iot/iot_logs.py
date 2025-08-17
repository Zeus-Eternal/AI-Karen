"""
Kari IoT Device Manager Logic
- Scan, pair, list, control all smart devices (Zigbee/Z-Wave/IP/BLE)
- RBAC: user (own), admin/devops (all)
- Enterprise audit trail
"""

from typing import Dict, Any, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_devices, pair_device, control_device, fetch_audit_logs
)

def get_devices(user_ctx: Dict) -> List[Dict[str, Any]]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "devops"]):
        raise PermissionError("Insufficient privileges to view devices.")
    return fetch_devices(user_ctx.get("user_id"), all_access="admin" in user_ctx.get("roles", []))

def start_device_pairing(user_ctx: Dict, protocol: str) -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "devops"]):
        raise PermissionError("Insufficient privileges to pair devices.")
    return pair_device(user_ctx.get("user_id"), protocol)

def send_device_command(user_ctx: Dict, device_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "devops"]):
        raise PermissionError("Insufficient privileges for device control.")
    return control_device(user_ctx.get("user_id"), device_id, command)

def get_device_audit(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "devops"]):
        raise PermissionError("Insufficient privileges for device audit.")
    return fetch_audit_logs(category="iot_device", user_id=user_ctx["user_id"])[-limit:][::-1]
