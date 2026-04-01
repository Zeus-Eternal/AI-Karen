"""Canonical authentication middleware boundary for active runtime imports."""

from __future__ import annotations

from typing import Any

from src.auth.auth_middleware import (  # noqa: F401
    AuthenticationError,
    BaseAuthMiddleware,
    SecureAuthMiddleware,
)


def get_auth_middleware() -> Any:
    """Resolve the active auth middleware through the canonical app boundary."""
    from src.auth.auth_middleware import get_auth_middleware as _get_auth_middleware

    return _get_auth_middleware()


async def get_current_user(*args: Any, **kwargs: Any) -> Any:
    """Proxy the current-user dependency through the canonical app boundary."""
    from src.auth.auth_middleware import get_current_user as _get_current_user

    return await _get_current_user(*args, **kwargs)


def get_rate_limiter() -> Any:
    """Resolve the auth rate limiter through the canonical app boundary."""
    from src.auth.auth_middleware import get_rate_limiter as _get_rate_limiter

    return _get_rate_limiter()

__all__ = [
    "AuthenticationError",
    "BaseAuthMiddleware",
    "SecureAuthMiddleware",
    "get_auth_middleware",
    "get_current_user",
    "get_rate_limiter",
]
