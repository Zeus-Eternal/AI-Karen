"""
Kari Code Sandbox Logic
- Secure, RBAC-isolated code execution on user-uploaded or in-app code
- Audit-trail, resource/cpu/mem/timeout guards
- Framework-agnostic: UI renders separately
"""

from typing import Dict, Any
from ui.hooks.rbac import require_roles
from ui.utils.api import run_code_safely, fetch_audit_logs

def execute_code(user_ctx: Dict, code: str, input_data: Any = None, language: str = "python") -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "developer", "admin"]):
        raise PermissionError("Not authorized for code sandbox.")
    return run_code_safely(user_ctx["user_id"], code, input_data, language)

def get_code_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Not authorized for code audit.")
    return fetch_audit_logs(category="code_sandbox", user_id=user_ctx["user_id"])[-limit:][::-1]
