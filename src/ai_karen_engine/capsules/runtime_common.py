"""Shared runtime helpers for capsule implementations."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import platform
import uuid
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

CAPSULE_SIGNING_KEY = os.getenv("KARI_CAPSULE_SIGNING_KEY", "change-me-to-secure-key")
MAX_PROMPT_LENGTH = int(os.getenv("KARI_MAX_PROMPT_LENGTH", "8192"))
JWT_ALGORITHM = "HS256"


class CapsuleSecurityError(Exception):
    """Shared capsule security violation."""


def _set_hardware_affinity() -> None:
    """Best-effort hardware affinity / priority hint for capsule execution."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        system = platform.system()
        if system == "Linux":
            cpus = list(range(os.cpu_count() or 1))
            if len(cpus) > 1:
                process.cpu_affinity([cpus[-1]])
                logger.info("Set CPU affinity to core %s", cpus[-1], extra={"correlation_id": "affinity"})
        elif system == "Windows":
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("Set process to HIGH priority (Windows)", extra={"correlation_id": "affinity"})
        elif system == "Darwin":
            os.nice(-10)
            logger.info("Set process priority up (Darwin/Mac)", extra={"correlation_id": "affinity"})
    except Exception as exc:
        logger.warning(
            "Hardware affinity/isolation not enforced: %s",
            exc,
            extra={"correlation_id": "affinity"},
        )


def _sign_payload(payload: Dict[str, Any]) -> str:
    """Generate a stable HMAC signature for capsule audit payloads."""
    msg = str(sorted(payload.items())).encode()
    return hmac.new(CAPSULE_SIGNING_KEY.encode(), msg, hashlib.sha512).hexdigest()


def validate_jwt(token: str) -> Dict[str, Any]:
    """Validate a JWT using the shared capsule signing key."""
    try:
        import jwt

        return jwt.decode(
            token,
            CAPSULE_SIGNING_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True},
        )
    except Exception as exc:
        raise CapsuleSecurityError(f"JWT validation failed: {exc}") from exc


def get_correlation_id() -> str:
    """Generate a unique correlation id."""
    return str(uuid.uuid4())

