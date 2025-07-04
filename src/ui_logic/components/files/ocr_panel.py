"""
Kari OCR Panel Logic
- Enterprise OCR (Tesseract, PaddleOCR, Vision API) on any file
- RBAC: user/admin/analyst
- Every request audited
"""

from typing import Dict, Any
from ui.hooks.rbac import require_roles
from ui.utils.api import run_ocr, fetch_audit_logs

def extract_ocr(user_ctx: Dict, file_id: str) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("Not authorized for OCR.")
    return run_ocr(file_id, user_ctx.get("user_id"))

def get_ocr_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("No access to OCR audit.")
    return fetch_audit_logs(category="ocr_panel", user_id=user_ctx["user_id"])[-limit:][::-1]
