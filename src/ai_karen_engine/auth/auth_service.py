"""Canonical authentication service boundary for active runtime imports."""

from __future__ import annotations

from typing import Any

from src.auth.auth_service import AuthService  # noqa: F401


async def get_auth_service() -> Any:
    """Resolve the active auth service through the canonical app boundary."""
    from src.auth.auth_service import get_auth_service as _get_auth_service

    return await _get_auth_service()


def get_auth_service_sync() -> Any:
    """Resolve the sync auth service through the canonical app boundary."""
    from src.auth.auth_service import get_auth_service_sync as _get_auth_service_sync

    return _get_auth_service_sync()


def user_account_to_dict(user: Any) -> dict[str, Any]:
    """Normalize user account objects through the canonical auth boundary."""
    from src.auth.auth_service import user_account_to_dict as _user_account_to_dict

    return _user_account_to_dict(user)

__all__ = [
    "AuthService",
    "get_auth_service",
    "get_auth_service_sync",
    "user_account_to_dict",
]
