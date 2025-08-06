"""Canonical authentication service for AI Karen.

This module exposes :class:`AuthService` which provides a common interface for
basic in-memory authentication, production database backed authentication and
optional intelligent behavioural checks. Behaviour is controlled by an
:class:`AuthConfig` dataclass.

The service composes existing implementations rather than re-implementing
logic. When ``use_database`` is ``True`` the
:class:`~ai_karen_engine.security.production_auth_service.ProductionAuthService`
will be used for persistence and secure password hashing. Otherwise the
light-weight in-memory implementation from
:class:`~ai_karen_engine.services.auth_service.AuthService` is used.

If ``enable_intelligent_checks`` is set, every successful authentication
attempt is analysed by
:class:`~ai_karen_engine.security.intelligent_auth_service.IntelligentAuthService`.
If the analysis decides the attempt should be blocked ``authenticate_user``
returns ``None``.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.security.intelligent_auth_service import (
    AuthContext,
    IntelligentAuthService,
)
from ai_karen_engine.security.production_auth_service import ProductionAuthService
from ai_karen_engine.services.auth_service import AuthService as BasicAuthService

# mypy: ignore-errors


logger = get_logger(__name__)


@dataclass
class AuthConfig:
    """Configuration switches for :class:`AuthService`."""

    use_database: bool = False
    enable_intelligent_checks: bool = False


class AuthService:
    """High level authentication façade with optional advanced features."""

    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        self.config = config or AuthConfig()
        self.basic_service = BasicAuthService()
        self.production_service: Optional[ProductionAuthService] = (
            ProductionAuthService() if self.config.use_database else None
        )
        self.intelligent_service: Optional[IntelligentAuthService] = (
            IntelligentAuthService() if self.config.enable_intelligent_checks else None
        )

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[list[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Create a new user using the configured backend."""

        if self.production_service:
            return await self.production_service.create_user(
                email=email,
                password=password,
                full_name=full_name,
                roles=roles,
                tenant_id=tenant_id,
                preferences=preferences,
            )

        return await self.basic_service.create_user(
            email=email,
            password=password,
            full_name=full_name,
            roles=roles,
            tenant_id=tenant_id,
            preferences=preferences,
        )

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Authenticate a user and optionally run intelligent checks."""

        if self.production_service:
            user = await self.production_service.authenticate_user(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            user = await self.basic_service.authenticate_user(
                email=email,
                password=password,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        if not user:
            return None

        if self.intelligent_service:
            context = AuthContext(
                email=email,
                password_hash=hashlib.sha256(password.encode()).hexdigest(),
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=f"{email}:{int(time.time()*1000)}",
            )
            analysis = await self.intelligent_service.analyze_login_attempt(context)
            if analysis.should_block:
                logger.warning("Login attempt blocked by intelligent auth service")
                return None

        return user

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a session using the configured backend."""

        if self.production_service:
            return await self.production_service.create_session(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
            )

        return await self.basic_service.create_session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Validate a session token and return associated user data."""

        if self.production_service:
            return await self.production_service.validate_session(
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return await self.basic_service.validate_session(
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session token if supported by the backend."""

        if self.production_service:
            return await self.production_service.invalidate_session(session_token)

        return await self.basic_service.invalidate_session(session_token)


__all__ = ["AuthService", "AuthConfig"]
