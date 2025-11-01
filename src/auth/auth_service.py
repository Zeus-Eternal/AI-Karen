"""Production authentication service adapter for Kari AI."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Dict, Optional

from ai_karen_engine.services.production_auth_service import (
    ProductionAuthService,
    UserAccount,
)


__all__ = [
    "AuthService",
    "get_auth_service",
    "get_auth_service_sync",
    "user_account_to_dict",
]


_service_lock = asyncio.Lock()
_auth_service: Optional[ProductionAuthService] = None
_service_started = False


def user_account_to_dict(user: UserAccount) -> Dict[str, Any]:
    """Convert a :class:`UserAccount` into a JSON serialisable dict."""

    payload = asdict(user)
    # Ensure datetimes are ISO8601 strings for transport safety
    for field in ("created_at", "last_login", "locked_until"):
        value = payload.get(field)
        if value is None:
            continue
        payload[field] = value.isoformat()

    # Normalise naming used by existing API consumers
    payload.pop("password_hash", None)
    payload.setdefault("preferences", {})
    payload.setdefault("tenant_id", "default")
    payload.setdefault("roles", ["user"])
    payload.setdefault("is_active", True)
    payload.setdefault("two_factor_enabled", False)
    payload.setdefault("is_verified", True)
    return payload


async def _ensure_service_started() -> ProductionAuthService:
    """Initialise and return the shared production auth service."""

    global _auth_service, _service_started

    if _auth_service is None:
        _auth_service = ProductionAuthService()

    if not _service_started:
        async with _service_lock:
            if not _service_started:
                await _auth_service.initialize()
                await _auth_service.start()
                _service_started = True

    return _auth_service


async def get_auth_service() -> ProductionAuthService:
    """Return the lazily initialised production authentication service."""

    return await _ensure_service_started()


def get_auth_service_sync() -> ProductionAuthService:
    """Blocking helper used by CLI tools and scripts."""

    if _auth_service is not None and _service_started:
        return _auth_service

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():  # pragma: no cover - defensive guard
        raise RuntimeError("Use 'await get_auth_service()' inside an event loop")

    return asyncio.run(get_auth_service())


class AuthService:
    """Compatibility façade used by legacy integration points."""

    def __init__(self) -> None:
        self._service: Optional[ProductionAuthService] = None

    async def _get_service(self) -> ProductionAuthService:
        if self._service is None:
            self._service = await get_auth_service()
        return self._service

    async def authenticate(
        self,
        email: str,
        password: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Dict[str, Any]:
        service = await self._get_service()
        user, access_token, refresh_token = await service.authenticate_user(
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if not user:
            raise ValueError("Invalid credentials")

        payload = user_account_to_dict(user)
        payload.update(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }
        )
        return payload

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        service = await self._get_service()
        user = await service.validate_token(token)
        if not user:
            return None
        return user_account_to_dict(user)

    async def create_user(
        self,
        email: str,
        password: str,
        *,
        full_name: Optional[str] = None,
        roles: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        service = await self._get_service()
        user, error = await service.create_user(
            email=email,
            password=password,
            full_name=full_name or email.split("@")[0],
            roles=roles or ["user"],
        )
        if error:
            raise ValueError(error)
        return user_account_to_dict(user)

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        service = await self._get_service()
        token, error = await service.refresh_access_token(refresh_token)
        if error:
            raise ValueError(error)
        return {"access_token": token, "token_type": "bearer"}

    async def logout(self, refresh_token: str) -> None:
        service = await self._get_service()
        await service.logout(refresh_token)

    async def get_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Fetch a user record by email or internal identifier."""

        service = await self._get_service()
        user = await service.get_user(identifier)
        if not user:
            return None
        return user_account_to_dict(user)
