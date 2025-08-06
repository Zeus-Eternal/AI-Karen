from __future__ import annotations

import hashlib
import os
import time
import uuid
from typing import Any, Dict, List, Optional
import asyncio

import jwt

from ai_karen_engine.security.auth_service import auth_service
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)

# Legacy configuration for backward compatibility
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
    Create a JWT session token for a user using production authentication service.
    This function maintains backward compatibility while using the production database.
    """
    try:
        # Use auth service to create session
        loop = asyncio.get_event_loop()
        session_data = loop.run_until_complete(
            auth_service.create_session(
                user_id=user_id,
                ip_address=ip,
                user_agent=user_agent,
                device_fingerprint=_device_fingerprint(user_agent, ip)
            )
        )
        
        # Return the access token for backward compatibility
        return session_data["access_token"]
        
    except Exception as e:
        logger.error(f"Failed to create session using production auth service: {e}")
        
        # Fallback to legacy JWT creation for backward compatibility
        now = int(time.time())
        payload = {
            "sub": user_id,
            "roles": roles,
            "exp": now + SESSION_DURATION,
            "iat": now,
            "device": _device_fingerprint(user_agent, ip),
            "tenant_id": tenant_id or "default",
            "jti": uuid.uuid4().hex,
        }
        return jwt.encode(payload, AUTH_SIGNING_KEY, algorithm=JWT_ALGORITHM)

def validate_session(token: str, user_agent: str, ip: str) -> Optional[Dict[str, Any]]:
    """
    Validate a JWT session token using production authentication service.
    Falls back to legacy validation for backward compatibility.
    """
    try:
        # First try to validate using auth service
        loop = asyncio.get_event_loop()
        user_data = loop.run_until_complete(
            auth_service.validate_session(
                session_token=token,
                ip_address=ip,
                user_agent=user_agent
            )
        )
        
        if user_data:
            # Convert to legacy format for backward compatibility
            return {
                "sub": user_data["user_id"],
                "roles": user_data["roles"],
                "tenant_id": user_data["tenant_id"],
                "exp": int(time.time()) + SESSION_DURATION,  # Approximate expiry
                "iat": int(time.time()),
                "device": _device_fingerprint(user_agent, ip),
                "jti": uuid.uuid4().hex,
            }
    
    except Exception as e:
        logger.warning(f"Production auth validation failed, trying legacy: {e}")
    
    # Fallback to legacy JWT validation
    try:
        decoded = jwt.decode(token, AUTH_SIGNING_KEY, algorithms=[JWT_ALGORITHM])
        if decoded.get("exp", 0) < time.time():
            return None
        if decoded.get("device") != _device_fingerprint(user_agent, ip):
            return None
        return decoded
    except Exception as e:
        logger.debug(f"Legacy JWT validation also failed: {e}")
        return None

__all__ = ["create_session", "validate_session", "SESSION_DURATION"]
