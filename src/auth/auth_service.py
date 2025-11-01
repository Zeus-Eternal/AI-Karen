"""Production authentication facade for Kari AI."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple

from pydantic import BaseModel, EmailStr, Field

from ai_karen_engine.core.errors.exceptions import AuthenticationError
from ai_karen_engine.core.services.base import ServiceConfig
from ai_karen_engine.services.production_auth_service import (
    ProductionAuthService,
    UserAccount,
)


logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response payload returned to clients."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


_backend_instance: Optional[ProductionAuthService] = None
_backend_lock: asyncio.Lock = asyncio.Lock()
_backend_initialized: bool = False
_backend_config: Optional[ServiceConfig] = None

_auth_service_instance: Optional["AuthService"] = None
_auth_service_lock: asyncio.Lock = asyncio.Lock()


async def _get_backend(config: Optional[ServiceConfig] = None) -> ProductionAuthService:
    """Get (and lazily initialize) the shared production auth backend."""
    global _backend_instance, _backend_initialized, _backend_config

    async with _backend_lock:
        if _backend_instance is None:
            _backend_config = config or _backend_config
            _backend_instance = ProductionAuthService(_backend_config)
            logger.info("Created production auth backend instance")

        if not _backend_initialized:
            await _backend_instance.initialize()
            await _backend_instance.start()
            _backend_initialized = True
            logger.info("Production auth backend initialized")

        return _backend_instance


async def ensure_production_auth_service_ready(
    config: Optional[ServiceConfig] = None,
) -> ProductionAuthService:
    """Ensure the production authentication backend is ready."""
    return await _get_backend(config)


async def shutdown_production_auth_service() -> None:
    """Shutdown the shared production authentication backend."""
    global _backend_instance, _backend_initialized

    async with _backend_lock:
        if _backend_instance is None:
            return

        try:
            await _backend_instance.stop()
        finally:
            _backend_instance = None
            _backend_initialized = False
            logger.info("Production auth backend shutdown complete")


async def get_production_auth_backend(
    config: Optional[ServiceConfig] = None,
) -> ProductionAuthService:
    """Expose the shared backend for modules that need direct access."""
    return await _get_backend(config)


class AuthService:
    """High level facade around :class:`ProductionAuthService`."""

    def __init__(self, config: Optional[ServiceConfig] = None) -> None:
        self._config = config
        self._backend: Optional[ProductionAuthService] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def _ensure_backend(self) -> ProductionAuthService:
        if self._backend is None:
            async with self._lock:
                if self._backend is None:
                    self._backend = await _get_backend(self._config)
        return self._backend

    @staticmethod
    def _serialize_user(user: UserAccount) -> Dict[str, Any]:
        return {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": getattr(user, "full_name", None),
            "roles": list(user.roles),
            "tenant_id": user.tenant_id,
            "is_active": user.is_active,
            "is_verified": getattr(user, "is_verified", True),
            "two_factor_enabled": getattr(user, "two_factor_enabled", False),
            "preferences": getattr(user, "preferences", {}),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

    async def login(
        self,
        credentials: LoginRequest,
        *,
        ip_address: str,
        user_agent: Optional[str] = None,
    ) -> LoginResponse:
        backend = await self._ensure_backend()
        user, access_token, refresh_token = await backend.authenticate_user(
            email=credentials.email,
            password=credentials.password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not user or not access_token or not refresh_token:
            message = refresh_token or "Authentication failed"
            raise AuthenticationError(message)

        payload = self._serialize_user(user)
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(backend.access_token_expire_minutes * 60),
            user=payload,
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        backend = await self._ensure_backend()
        token, error = await backend.refresh_access_token(refresh_token)
        if error or not token:
            raise AuthenticationError(error or "Unable to refresh token")
        return token

    async def logout(self, refresh_token: str) -> None:
        backend = await self._ensure_backend()
        await backend.logout(refresh_token)

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        backend = await self._ensure_backend()
        user = await backend.validate_token(token)
        if not user:
            return None
        return self._serialize_user(user)

    async def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        tenant_id: str = "default",
        roles: Optional[List[str]] = None,
        is_verified: bool = True,
    ) -> UserAccount:
        backend = await self._ensure_backend()
        user, error = await backend.create_user(
            email=email,
            password=password,
            full_name=full_name,
            roles=roles or ["user"],
            tenant_id=tenant_id,
            is_verified=is_verified,
        )
        if error or not user:
            raise AuthenticationError(error or "Failed to create user")
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UserAccount]:
        backend = await self._ensure_backend()
        return await backend.get_user_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        backend = await self._ensure_backend()
        return await backend.get_user_by_email(email)

    async def update_user(
        self,
        user_id: str,
        *,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        tenant_id: Optional[str] = None,
        is_verified: Optional[bool] = None,
    ) -> UserAccount:
        backend = await self._ensure_backend()
        user, error = await backend.update_user(
            user_id,
            full_name=full_name,
            roles=roles,
            preferences=preferences,
            is_active=is_active,
            tenant_id=tenant_id,
            is_verified=is_verified,
        )
        if error or not user:
            raise AuthenticationError(error or "Failed to update user")
        return user

    async def delete_user(self, user_id: str) -> bool:
        backend = await self._ensure_backend()
        return await backend.delete_user(user_id)

    async def list_users(
        self,
        *,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserAccount]:
        backend = await self._ensure_backend()
        return await backend.list_users(tenant_id=tenant_id, limit=limit, offset=offset)

    async def get_auth_stats(self) -> Dict[str, Any]:
        backend = await self._ensure_backend()
        return await backend.get_auth_stats()

    async def is_first_run(self) -> bool:
        backend = await self._ensure_backend()
        return await backend.is_first_run()

    async def create_first_admin(
        self, email: str, password: str, full_name: str
    ) -> UserAccount:
        backend = await self._ensure_backend()
        return await backend.create_first_admin(email=email, password=password, full_name=full_name)


async def get_auth_service(
    config: Optional[ServiceConfig] = None,
) -> AuthService:
    """Return the shared :class:`AuthService` instance."""
    global _auth_service_instance

    async with _auth_service_lock:
        if _auth_service_instance is None:
            _auth_service_instance = AuthService(config)
            logger.info("Created AuthService facade")

    # Ensure backend is ready before returning
    await _auth_service_instance._ensure_backend()
    return _auth_service_instance
