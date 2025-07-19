from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

import jwt

AUTH_SIGNING_KEY = os.getenv("KARI_AUTH_SIGNING_KEY", "change-me-in-prod")
SESSION_DURATION = int(os.getenv("KARI_SESSION_DURATION", "3600"))
JWT_ALGORITHM = "HS256"

def _device_fingerprint(user_agent: str, ip: str) -> str:
    """
    Create a unique device fingerprint from user agent and IP.
    """
    data = f"{user_agent}:{ip}".encode()
    return hashlib.sha256(data).hexdigest()

def create_session(
    user_id: str,
    roles: List[str],
    user_agent: str,
    ip: str,
    tenant_id: Optional[str] = None,
) -> str:
    """
    Create a JWT session token for a user.
    - Multi-tenant by tenant_id
    - Device-bound by user agent and IP hash
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "roles": roles,
        "exp": now + SESSION_DURATION,
        "iat": now,
        "device": _device_fingerprint(user_agent, ip),
        "tenant_id": tenant_id or "default",
    }
    return jwt.encode(payload, AUTH_SIGNING_KEY, algorithm=JWT_ALGORITHM)

def validate_session(token: str, user_agent: str, ip: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT session token.
    - Checks expiry, device fingerprint, and signature.
    """
    try:
        decoded = jwt.decode(token, AUTH_SIGNING_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
    if decoded.get("exp", 0) < time.time():
        return None
    if decoded.get("device") != _device_fingerprint(user_agent, ip):
        return None
    return decoded

__all__ = ["create_session", "validate_session"]
