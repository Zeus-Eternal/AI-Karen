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
from datetime import datetime
from typing import Any, Dict, Optional

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.intelligent_auth_service import (
    AuthContext,
    IntelligentAuthService,
)
from ai_karen_engine.security.models import SessionData, UserData
from ai_karen_engine.security.production_auth_service import ProductionAuthService
from ai_karen_engine.services.auth_service import AuthService as BasicAuthService

# mypy: ignore-errors


logger = get_logger(__name__)


class AuthService:
    """High level authentication façade with optional advanced features."""

    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        self.config = config or AuthConfig()
        self.basic_service = BasicAuthService()
        self.production_service: Optional[ProductionAuthService] = (
            ProductionAuthService() if self.config.features.use_database else None
        )
        self.intelligent_service: Optional[IntelligentAuthService] = (
            IntelligentAuthService()
            if self.config.features.enable_intelligent_checks
            else None
        )

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[list[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserData:
        """Create a new user using the configured backend."""

        if self.production_service:
            user = await self.production_service.create_user(
                email=email,
                password=password,
                full_name=full_name,
                roles=roles,
                tenant_id=tenant_id,
                preferences=preferences,
            )
            return self._to_user_data(user)

        user = await self.basic_service.create_user(
            email=email,
            password=password,
            full_name=full_name,
            roles=roles,
            tenant_id=tenant_id,
            preferences=preferences,
        )
        return self._to_user_data(user)

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[UserData]:
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

        user_data = self._to_user_data(user)

        if self.intelligent_service:
            context = AuthContext(
                email=email,
                password_hash=hashlib.sha256(password.encode()).hexdigest(),
                client_ip=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                request_id=f"{email}:{int(time.time()*1000)}",
            )
            analysis = await self.intelligent_service.analyze_login_attempt(context)
            if analysis.should_block:
                logger.warning("Login attempt blocked by intelligent auth service")
                return None

        return user_data

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        """Create a session using the configured backend."""

        if self.production_service:
            session = await self.production_service.create_session(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
            )
        else:
            session = await self.basic_service.create_session(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
            )

        return self._to_session_data(session)

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[UserData]:
        """Validate a session token and return associated user data."""

        if self.production_service:
            user = await self.production_service.validate_session(
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            user = await self.basic_service.validate_session(
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        if not user:
            return None

        return self._to_user_data(user)

    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session token if supported by the backend."""

        if self.production_service:
            return await self.production_service.invalidate_session(session_token)

        return await self.basic_service.invalidate_session(session_token)

    # ------------------------------------------------------------------
    # Internal helpers

    def _to_user_data(self, data: Any) -> UserData:
        """Convert various user representations into :class:`UserData`."""

        if isinstance(data, UserData):
            return data

        if isinstance(data, dict):
            return UserData(
                user_id=str(data.get("user_id") or data.get("id", "")),
                email=data.get("email", ""),
                full_name=data.get("full_name"),
                roles=list(data.get("roles", [])),
                tenant_id=data.get("tenant_id", "default"),
                preferences=data.get("preferences", {}),
                two_factor_enabled=data.get("two_factor_enabled", False),
                is_verified=data.get("is_verified", True),
            )

        return UserData(
            user_id=str(getattr(data, "id", getattr(data, "user_id", ""))),
            email=getattr(data, "email", ""),
            full_name=getattr(data, "full_name", None),
            roles=list(getattr(data, "roles", []) or []),
            tenant_id=getattr(data, "tenant_id", "default"),
            preferences=getattr(data, "preferences", {}),
            two_factor_enabled=getattr(data, "two_factor_enabled", False),
            is_verified=getattr(data, "is_verified", True),
        )

    def _to_session_data(
        self, data: Any, user_data: Optional[UserData] = None
    ) -> SessionData:
        """Convert raw session data into :class:`SessionData`."""

        if isinstance(data, SessionData):
            return data

        if isinstance(data, dict):
            return SessionData(
                access_token=data.get("access_token", ""),
                refresh_token=data.get("refresh_token", ""),
                session_token=data.get("session_token", ""),
                expires_in=data.get("expires_in", 0),
                user_data=user_data,
            )

        return SessionData("", "", "", 0, user_data)


__all__ = ["AuthService", "AuthConfig"]
