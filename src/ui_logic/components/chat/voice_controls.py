"""
Kari Voice Controls Logic
- Voice-to-text (STT) and text-to-speech (TTS) integration (local-first)
- RBAC, audit, fallback
"""

from typing import Dict
from src.ui_logic.hooks.rbac import require_roles
from src.ui_logic.utils.api import run_stt, run_tts, fetch_voice_logs

def transcribe_voice(user_ctx: Dict, audio_bytes: bytes, meta: Dict = None) -> str:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for STT.")
    return run_stt(user_ctx["user_id"], audio_bytes, meta)

def synthesize_voice(user_ctx: Dict, text: str, voice_id: str = "default") -> bytes:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin"]):
        raise PermissionError("Not authorized for TTS.")
    return run_tts(user_ctx["user_id"], text, voice_id)

def get_voice_logs(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin"]):
        raise PermissionError("No access to voice logs.")
    return fetch_voice_logs(user_ctx["user_id"])[-limit:][::-1]
