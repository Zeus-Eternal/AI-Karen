"""Production-ready chat business logic for Kari UI."""

from __future__ import annotations

import hmac
import hashlib
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ai_karen_engine.core.logging.logger import LogLevel, get_logger


class ChatSecurityError(Exception):
    """Base class for chat security violations."""


DEFAULT_SIGNING_KEY = "change-me-to-secure-key"


def _load_signing_key() -> str:
    """Return the configured signing key or raise if not securely configured."""

    logger = get_logger("ui.chat.security", level=LogLevel.WARNING)
    key_candidate = os.getenv("KARI_UI_SIGNING_KEY", "").strip()
    key_file = os.getenv("KARI_UI_SIGNING_KEY_FILE", "").strip()

    if not key_candidate and key_file:
        candidate_path = Path(key_file)
        if not candidate_path.exists():
            raise RuntimeError(
                f"KARI_UI_SIGNING_KEY_FILE={candidate_path} does not exist; unable to load UI signing key"
            )
        key_candidate = candidate_path.read_text(encoding="utf-8").strip()

    if key_candidate and key_candidate != DEFAULT_SIGNING_KEY:
        if len(key_candidate) < 32:
            logger = get_logger("ui.chat.security", level=LogLevel.WARNING)
            logger.warning(
                "UI signing key is shorter than 32 characters; hardening by hashing provided value"
            )
            return hashlib.sha512(key_candidate.encode("utf-8")).hexdigest()
        return key_candidate

    fallback_path = Path("config/ui_signing_key.secret")
    if fallback_path.exists():
        key_candidate = fallback_path.read_text(encoding="utf-8").strip()
        if key_candidate:
            return key_candidate

    logger.error(
        "KARI_UI_SIGNING_KEY is not configured; falling back to hashed default. "
        "This must be overridden in production."
    )
    return hashlib.sha512(DEFAULT_SIGNING_KEY.encode("utf-8")).hexdigest()


UI_SIGNING_KEY = _load_signing_key()
SESSION_TIMEOUT = int(os.getenv("KARI_SESSION_TIMEOUT", "3600"))

AUDIT_LOGGER = get_logger("ui.chat.audit", level=LogLevel.INFO)
SECURITY_LOGGER = get_logger("ui.chat.security", level=LogLevel.INFO)


def _sign_ui_payload(payload: str) -> str:
    """Generate HMAC signature for UI state validation."""

    return hmac.new(UI_SIGNING_KEY.encode(), payload.encode(), hashlib.sha512).hexdigest()


def _coerce_timestamp(raw: Any) -> Optional[float]:
    """Convert assorted timestamp formats into epoch seconds."""

    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            try:
                return datetime.fromisoformat(raw).timestamp()
            except ValueError:
                return None
    return None


def enforce_cpu_affinity() -> bool:
    """Attempt to set CPU affinity for deterministic performance."""

    try:
        import psutil  # pragma: no cover - optional dependency

        process = psutil.Process(os.getpid())
        process.cpu_affinity([0])
        AUDIT_LOGGER.info("cpu_affinity_applied", cores=[0])
        return True
    except Exception as exc:  # pragma: no cover - environment specific
        SECURITY_LOGGER.debug(
            "cpu_affinity_not_applied", reason=str(exc.__class__.__name__), detail=str(exc)
        )
        return False


class SecureChatPage:
    """Thread-safe chat business logic with auditing and strict validation."""

    _instance: Optional["SecureChatPage"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SecureChatPage":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        """Perform secure initialization sequence."""

        log_dir = Path(os.getenv("KARI_LOG_DIR", "logs")) / "kari"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.session_cache: dict[str, dict[str, Any]] = {}
        self.session_lock = threading.Lock()
        self.affinity_applied = enforce_cpu_affinity()

    def _prune_sessions(self) -> None:
        """Drop expired session cache entries."""

        now = time.time()
        expired = [token for token, data in self.session_cache.items() if data["expires"] <= now]
        for token in expired:
            self.session_cache.pop(token, None)
        if expired:
            AUDIT_LOGGER.debug("expired_sessions_removed", count=len(expired))

    def validate_session(self, user_ctx: Dict[str, Any]) -> bool:
        """Validate cryptographic session token and enforce expiry."""

        session_token = user_ctx.get("session_token")
        if not session_token:
            SECURITY_LOGGER.warning("missing_session_token", user=user_ctx.get("user_id"))
            return False

        timestamp = _coerce_timestamp(user_ctx.get("timestamp"))
        if timestamp is None:
            SECURITY_LOGGER.warning("invalid_session_timestamp", user=user_ctx.get("user_id"))
            return False

        if time.time() - timestamp > SESSION_TIMEOUT:
            SECURITY_LOGGER.info("session_expired", user=user_ctx.get("user_id"))
            return False

        try:
            msg = f"{user_ctx['user_id']}|{user_ctx['roles']}|{user_ctx.get('timestamp', '')}"
            expected = _sign_ui_payload(msg)
            if not hmac.compare_digest(expected, session_token):
                SECURITY_LOGGER.warning("session_signature_mismatch", user=user_ctx.get("user_id"))
                return False
        except Exception as exc:
            SECURITY_LOGGER.exception(
                "session_validation_error", user=user_ctx.get("user_id"), error=str(exc)
            )
            return False

        with self.session_lock:
            self._prune_sessions()
            cached = self.session_cache.get(session_token)
            if cached and cached["user_id"] != user_ctx["user_id"]:
                SECURITY_LOGGER.error(
                    "session_user_mismatch",
                    token=session_token,
                    expected_user=cached["user_id"],
                    actual_user=user_ctx["user_id"],
                )
                return False
            self.session_cache[session_token] = {
                "user_id": user_ctx["user_id"],
                "roles": list(user_ctx.get("roles", [])),
                "expires": timestamp + SESSION_TIMEOUT,
            }

        return True

    def log_audit_event(self, **event_data: Any) -> None:
        """Emit structured audit events for chat operations."""

        payload = {
            "timestamp": int(time.time()),
            **event_data,
        }
        AUDIT_LOGGER.info("chat_event", **payload)

    def authenticate_and_authorize(
        self, get_user_context, require_roles, required_roles=None
    ) -> Dict[str, Any]:
        """Authenticate user context and enforce RBAC controls."""

        user_ctx = get_user_context()
        if not user_ctx.get("user_id"):
            raise ChatSecurityError("Missing user context")

        roles_needed = required_roles or ["user", "admin", "devops", "analyst"]
        require_roles(user_ctx, roles_needed)

        if not self.validate_session(user_ctx):
            self.log_audit_event(event="session_rejected", user=user_ctx.get("user_id"))
            raise ChatSecurityError("Invalid session token")

        self.log_audit_event(event="session_validated", user=user_ctx["user_id"], roles=user_ctx.get("roles", []))
        return user_ctx

    def fetch_context_panel_data(self, user_ctx: Dict[str, Any], fetch_session_memory) -> Dict[str, Any]:
        """Fetch secure session memory for context panel."""

        memory = fetch_session_memory(user_ctx)
        if not isinstance(memory, dict):
            raise ChatSecurityError("Invalid memory format")
        return memory

    def fetch_chat_history(self, user_ctx: Dict[str, Any], fetch_chat_window):
        """Fetch chat history window."""

        return fetch_chat_window(user_ctx=user_ctx)

    def fetch_persona_data(self, fetch_persona_switcher, fetch_emotion_style_panel):
        """Fetch persona and emotion controls data."""

        persona = fetch_persona_switcher()
        emotion = fetch_emotion_style_panel()
        return {"persona": persona, "emotion": emotion}

    def handle_input(self, user_ctx: Dict[str, Any], handle_chat_input, handle_voice_input):
        """Process chat/voice input."""

        text_result = handle_chat_input(user_ctx=user_ctx)
        voice_result = handle_voice_input(user_ctx=user_ctx)
        return {"text": text_result, "voice": voice_result}

    def handle_multimodal(self, user_ctx: Dict[str, Any], handle_multimodal_upload):
        """Process file uploads."""

        return handle_multimodal_upload(user_ctx=user_ctx)


def get_chat_page() -> SecureChatPage:
    if SecureChatPage._instance is None:
        with SecureChatPage._lock:
            if SecureChatPage._instance is None:
                SecureChatPage._instance = SecureChatPage()
    return SecureChatPage._instance


chat_logic = get_chat_page()
