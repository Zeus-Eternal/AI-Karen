"""Security capsule implementation."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from ai_karen_engine.capsules.base_capsule import BaseCapsule
from ai_karen_engine.capsules.runtime_common import (
    _set_hardware_affinity,
    _sign_payload,
    get_correlation_id,
    validate_jwt,
)
from ai_karen_engine.capsules.security_common import (
    validate_allowed_tools,
    validate_prompt_safety,
)

logger = logging.getLogger("security.capsule")

try:
    from prometheus_client import Counter

    CAPSULE_SUCCESS = Counter(
        "capsule_security_success_total", "Successful security capsule executions"
    )
    CAPSULE_FAILURE = Counter(
        "capsule_security_failure_total", "Failed security capsule executions"
    )
except ImportError:
    CAPSULE_SUCCESS = CAPSULE_FAILURE = None


class SecurityCapsule(BaseCapsule):
    """BaseCapsule-backed security operations capsule."""

    _instance: Optional["SecurityCapsule"] = None
    _lock = threading.Lock()

    def __new__(cls, capsule_dir: Optional[Path] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, capsule_dir: Optional[Path] = None):
        if getattr(self, "_security_initialized", False):
            return

        super().__init__(capsule_dir or Path(__file__).parent)
        self._security_initialized = True
        logger.info("Security capsule initialized in secure mode")

    def _execute_core(self, context):
        _set_hardware_affinity()

        audit_payload = {
            "user": context.user_ctx.get("sub"),
            "action": "security_task",
            "timestamp": int(time.time()),
            "correlation_id": context.correlation_id,
            "capsule": self.get_id(),
        }
        audit_payload["signature"] = _sign_payload(audit_payload)

        try:
            from ai_karen_engine.services.plugin_router import render_prompt
            from ai_karen_engine.integrations.llm_registry import get_registry

            prompt = render_prompt(
                self.prompt_template or "",
                context={
                    "user_ctx": context.user_ctx,
                    "request": context.request,
                    "audit_payload": audit_payload,
                },
            )

            validate_prompt_safety(prompt)
            validate_allowed_tools("llm.generate_text", self.manifest.allowed_tools)

            llm = get_registry().get_active()
            result = llm.generate_text(
                prompt,
                max_tokens=self.manifest.max_tokens,
                temperature=self.manifest.temperature,
            )

            if CAPSULE_SUCCESS is not None:
                CAPSULE_SUCCESS.inc()

            logger.info(
                "Security task succeeded for user %s", context.user_ctx.get("sub")
            )

            return {
                "result": result,
                "audit": audit_payload,
                "security": {
                    "integrity_check": _sign_payload(
                        {"result": result, "cid": context.correlation_id}
                    ),
                    "model_used": str(type(llm).__name__),
                    "correlation_id": context.correlation_id,
                },
            }
        except Exception:
            if CAPSULE_FAILURE is not None:
                CAPSULE_FAILURE.inc()
            raise

    def execute_task(self, request: Dict[str, Any], jwt_token: str) -> Dict[str, Any]:
        """Compatibility wrapper for the legacy plugin interface."""
        user_ctx = validate_jwt(jwt_token)
        result = self.execute(
            request=request,
            user_ctx=user_ctx,
            correlation_id=get_correlation_id(),
            memory_context=None,
        )
        return result.model_dump()


def get_capsule_handler() -> SecurityCapsule:
    """Return the process-local Security capsule singleton."""
    if SecurityCapsule._instance is None:
        with SecurityCapsule._lock:
            if SecurityCapsule._instance is None:
                SecurityCapsule._instance = SecurityCapsule()
    return SecurityCapsule._instance


def handler(request: Dict[str, Any], jwt_token: str) -> Dict[str, Any]:
    """Standard plugin interface with JWT enforcement."""
    return get_capsule_handler().execute_task(request, jwt_token)


__all__ = [
    "SecurityCapsule",
    "get_capsule_handler",
    "handler",
]
