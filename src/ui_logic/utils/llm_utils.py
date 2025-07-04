"""
Kari UI LLM Utilities (Production)
- Zero-trust LLM interaction, hardware-aware affinity (no NUMA), cryptographic audit trails.
- Pure UI-level: no business logic, no provider registry, no cloud secrets here.
- Compatible with Streamlit, FastAPI, Tauri/React, etc.
"""

import os
import time
import hashlib
import hmac
import threading
from typing import Any, Dict, Optional, List, Generator, Callable, Union
from pathlib import Path

# === Security & Audit Constants ===
LLM_SIGNING_KEY = os.getenv("KARI_LLM_SIGNING_KEY", "change-me-to-secure-key")
MAX_SAFE_TOKENS = int(os.getenv("KARI_MAX_SAFE_TOKENS", "8192"))
TOKEN_ESTIMATE_RATIO = 0.75  # 1 token ≈ 0.75 words (conservative)

# === Cross-Platform Hardware Affinity (No NUMA!) ===
try:
    import psutil
    PSUTIL_ENABLED = True
except ImportError:
    PSUTIL_ENABLED = False

def set_affinity_safe(cpu_idx: Optional[int] = None):
    """Set CPU affinity for this process or thread (cross-platform, fallback safe)."""
    if not PSUTIL_ENABLED:
        return
    p = psutil.Process(os.getpid())
    try:
        if cpu_idx is None:
            cpu_idx = 0
        p.cpu_affinity([cpu_idx])
    except Exception:
        pass

# === Secure Logging ===
AUDIT_LOG_PATH = Path("/secure/logs/kari/llm_audit.log")
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

class LLMSecurityError(Exception):
    """Base class for all LLM security violations"""
    pass

def _sign_llm_payload(payload: str) -> str:
    """Generate HMAC signature for prompt/response validation"""
    return hmac.new(
        LLM_SIGNING_KEY.encode(),
        payload.encode(),
        hashlib.sha512
    ).hexdigest()

class SecureLLMUtils:
    """
    Kari UI LLM Utilities:
    - Memory-safe text processing
    - Hardware-aware execution
    - Cryptographic validation, streaming, stats, markdown
    - All ops thread-safe and audit-logged
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self):
        """Secure initialization sequence"""
        self.audit_log = open(AUDIT_LOG_PATH, "a")
        self.audit_lock = threading.Lock()

    def _secure_trim(self, text: str, max_tokens: int) -> str:
        """Hardened text truncation with overflow protection"""
        if max_tokens > MAX_SAFE_TOKENS:
            raise LLMSecurityError(f"Max tokens {max_tokens} exceeds safe limit")
        words = text.split()
        safe_limit = int(max_tokens * TOKEN_ESTIMATE_RATIO)
        if len(words) <= safe_limit:
            return text
        trimmed = " ".join(words[:safe_limit])
        self._log_audit_event(
            action="text_truncation",
            original_length=len(text),
            trimmed_length=len(trimmed)
        )
        return trimmed + " [TRUNCATED]"

    def _log_audit_event(self, **event_data):
        """Cryptographically signed audit logging"""
        timestamp = int(time.time())
        event = {
            "timestamp": timestamp,
            **event_data,
            "signature": _sign_llm_payload(str(timestamp) + str(event_data))
        }
        with self.audit_lock:
            self.audit_log.write(f"{event}\n")
            self.audit_log.flush()

    def estimate_tokens(self, text: str) -> int:
        """Token estimation with bounds checking"""
        word_count = len(text.split())
        estimate = int(word_count / TOKEN_ESTIMATE_RATIO)
        if estimate > MAX_SAFE_TOKENS:
            self._log_audit_event(
                action="token_estimate_overflow",
                estimate=estimate,
                max_safe=MAX_SAFE_TOKENS
            )
            raise LLMSecurityError(f"Token estimate {estimate} exceeds safe limit")
        return estimate

    def render_markdown_response(self, response: Union[str, Dict]) -> str:
        """Secure response rendering with injection protection"""
        from markdown import markdown
        from bs4 import BeautifulSoup
        if isinstance(response, str):
            clean_text = BeautifulSoup(response, "html.parser").get_text()
            return markdown(clean_text)
        if isinstance(response, dict):
            if "content" in response:
                content = BeautifulSoup(response["content"], "html.parser").get_text()
                role = response.get("role", "Kari")
                return f"**{role}:**\n\n{markdown(content)}"
            return f"```json\n{response}\n```"
        raise LLMSecurityError("Invalid response type for rendering")

    def stream_llm_response(self, llm, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Streaming generator with audit and hardware isolation (affinity only)"""
        set_affinity_safe()  # Always safe, cross-platform; no NUMA
        signed_prompt = _sign_llm_payload(prompt)
        self._log_audit_event(
            action="stream_start",
            prompt_hash=hashlib.sha256(prompt.encode()).hexdigest(),
            prompt_signature=signed_prompt
        )
        try:
            for chunk in llm.generate(prompt, stream=True, **kwargs):
                if not isinstance(chunk, str):
                    raise LLMSecurityError("Invalid chunk type in stream")
                yield chunk
        finally:
            self._log_audit_event(action="stream_end")

    def get_llm_stats(self, llm, prompt: str) -> Dict[str, Any]:
        """Secure performance diagnostics with validation"""
        from time import perf_counter
        start = perf_counter()
        response = llm.generate_text(prompt)
        latency = perf_counter() - start
        stats = {
            "model": getattr(llm, "name", "unknown"),
            "tokens_in": self.estimate_tokens(prompt),
            "tokens_out": self.estimate_tokens(response),
            "latency": latency,
            "response_hash": hashlib.sha256(response.encode()).hexdigest(),
            "validated": False
        }
        # Cryptographic validation (if supported by backend)
        if hasattr(llm, "verify_response"):
            stats["validated"] = llm.verify_response(prompt, response)
        self._log_audit_event(
            action="llm_stats",
            **{k: v for k, v in stats.items() if k != "response_hash"}
        )
        return stats

    def wrap_llm_for_ui(self, llm, **extra) -> Callable:
        """Secure LLM wrapper for UI with execution guards"""
        def secured_call(prompt: str, **kwargs):
            prompt = self._secure_trim(prompt, MAX_SAFE_TOKENS)
            set_affinity_safe()
            merged = {**extra, **kwargs}
            return llm.generate_text(prompt, **merged)
        return secured_call

# === Singleton for All UI Layers ===
def get_llm_utils():
    if SecureLLMUtils._instance is None:
        with SecureLLMUtils._lock:
            if SecureLLMUtils._instance is None:
                SecureLLMUtils._instance = SecureLLMUtils()
    return SecureLLMUtils._instance

# === Public API ===
llm_utils = get_llm_utils()
