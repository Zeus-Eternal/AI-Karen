"""
Kari File Dropper Logic
- Secure, RBAC-controlled, audit-logged file uploads (multi-modal)
"""

from typing import Dict, Any, List
from ui.hooks.rbac import require_roles
from ui.utils.api import save_file, fetch_upload_logs

def upload_file(user_ctx: Dict, file_bytes: bytes, filename: str, filetype: str, meta: Dict = None) -> str:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("Not authorized for file upload.")
    return save_file(user_ctx["user_id"], file_bytes, filename, filetype, meta)

def get_upload_logs(user_ctx: Dict, limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("Not authorized for upload logs.")
    return fetch_upload_logs(user_ctx["user_id"])[-limit:][::-1]
