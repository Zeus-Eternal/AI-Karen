"""Session helpers bridging to the production authentication service."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import UserData

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _get_auth_middleware():
    """Resolve the production authentication middleware."""
    from ai_karen_engine.auth.auth_middleware import get_auth_middleware

    return get_auth_middleware()


async def _authenticate_request(request: Request) -> Dict[str, Any]:
    import os
    auth_bypass = os.getenv("KARI_AUTH_BYPASS", "true").lower() == "true"
    if auth_bypass:
        logger.debug("Auth bypass active in session helper")
        return {
            "user_id": "dev-user",
            "email": "dev-user@localhost",
            "user_type": "developer",
            "permissions": ["extension:*", "chat:*", "admin:*"],
            "token_id": "dev-token-id"
        }

    middleware = _get_auth_middleware()
    user_data = await middleware.authenticate_request(request)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_data


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> UserData:
    """FastAPI dependency that resolves the authenticated user."""
    payload = await _authenticate_request(request)
    return UserData.ensure(payload)


__all__ = ["get_current_user"]
