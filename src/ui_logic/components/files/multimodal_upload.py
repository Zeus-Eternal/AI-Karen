"""
Kari Multi-Modal Upload Logic
- One function to rule all: image, PDF, audio, video
- Triggers OCR, transcription, and preview extractors
- RBAC enforced
"""

from typing import Dict
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    save_file,
    run_ocr,
    run_transcription,
    extract_preview,
    fetch_audit_logs
)

def handle_multimodal_upload(user_ctx: Dict, file_bytes: bytes, filename: str, filetype: str, meta: Dict = None) -> Dict:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "analyst"]):
        raise PermissionError("No permission for multi-modal upload.")
    file_id = save_file(user_ctx["user_id"], file_bytes, filename, filetype, meta)
    preview = extract_preview(file_id)
    ocr = run_ocr(file_id) if "image" in filetype or "pdf" in filetype else None
    transcript = run_transcription(file_id) if "audio" in filetype or "video" in filetype else None
    return {
        "file_id": file_id,
        "preview": preview,
        "ocr": ocr,
        "transcript": transcript
    }

def get_multimodal_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionError("No access to multimodal audit.")
    return fetch_audit_logs(category="multimodal_upload", user_id=user_ctx["user_id"])[-limit:][::-1]
