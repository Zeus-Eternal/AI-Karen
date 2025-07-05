"""
Kari Doc Summary Logic
- Multi-modal doc (PDF/DOCX/TXT) extraction, OCR, table detection, fact/summary extraction
- RBAC: user/admin, all actions audited
"""

from typing import Dict, Any
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    extract_doc_content,
    summarize_document,
    fetch_audit_logs
)

def extract_document(user_ctx: Dict, file_id: str, meta: Dict = None) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("No access to document extraction.")
    return extract_doc_content(user_ctx["user_id"], file_id, meta)

def get_doc_summary(user_ctx: Dict, file_id: str) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("No access to document summarization.")
    return summarize_document(user_ctx["user_id"], file_id)

def get_doc_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("No access to document audit.")
    return fetch_audit_logs(category="doc_summary", user_id=user_ctx["user_id"])[-limit:][::-1]
