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
import json
import secrets
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import bcrypt

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.database.client import get_db_session
from ai_karen_engine.database.models.auth_models import User, UserSession
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.intelligent_auth_service import (
    AuthContext,
    IntelligentAuthService,
)
from ai_karen_engine.security.models import SessionData, UserData
from ai_karen_engine.security.production_auth_service import ProductionAuthService
from ai_karen_engine.services.auth_service import AuthService as BasicAuthService
from ai_karen_engine.security.security_enhancer import (
    AuditLogger,
    RateLimiter,
    SecurityEnhancer,
)

# mypy: ignore-errors


logger = get_logger(__name__)


class CoreAuthenticator:
    """Simple authentication service using a SQL database backend."""

    session_expire_hours = 24

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""

        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its bcrypt hash."""

        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except ValueError:
            return False

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserData:
        """Create a new user with a securely hashed password."""

        roles = roles or ["user"]
        preferences = preferences or {}

        with get_db_session() as db:
            if db.query(User).filter(User.email == email).first():
                raise ValueError("User already exists")

            user = User(
                email=email,
                password_hash=self.hash_password(password),
                full_name=full_name,
                roles=json.dumps(roles),
                tenant_id=tenant_id,
                preferences=json.dumps(preferences),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return self._to_user_data(user)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserData]:
        """Authenticate a user by verifying their password."""

        with get_db_session() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user or not self.verify_password(password, user.password_hash):
                return None

        return self._to_user_data(user)

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        """Create a session for an authenticated user."""

        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=self.session_expire_hours)
        user_uuid = uuid.UUID(user_id)

        with get_db_session() as db:
            session = UserSession(
                user_id=user_uuid,
                session_token=session_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                expires_at=expires_at,
            )
            db.add(session)
            db.commit()

        return SessionData(
            access_token=session_token,
            refresh_token=refresh_token,
            session_token=session_token,
            expires_in=int((expires_at - datetime.utcnow()).total_seconds()),
            user_data=None,
        )

    async def validate_session(self, session_token: str) -> Optional[UserData]:
        """Validate a session token and return associated user data."""

        with get_db_session() as db:
            session = (
                db.query(UserSession)
                .filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active.is_(True),
                    UserSession.expires_at > datetime.utcnow(),
                )
                .first()
            )
            if not session:
                return None

            user = db.query(User).filter(User.id == session.user_id).first()
            if not user:
                return None

        return self._to_user_data(user)

    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate an existing session."""

        with get_db_session() as db:
            session = (
                db.query(UserSession)
                .filter(UserSession.session_token == session_token)
                .first()
            )
            if not session:
                return False
            session.is_active = False
            db.commit()
            return True

    def _to_user_data(self, user: User) -> UserData:
        """Convert ORM user model to :class:`UserData`."""

        return UserData(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=json.loads(user.roles) if user.roles else [],
            tenant_id=user.tenant_id,
            preferences=json.loads(user.preferences) if user.preferences else {},
            two_factor_enabled=user.two_factor_enabled,
            is_verified=user.is_verified,
        )


class AuthService:
    """High level authentication façade with optional advanced features."""

    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        metrics_hook: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
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
        self.security_enhancer: Optional[SecurityEnhancer] = None
        if (
            self.config.features.enable_rate_limiter
            or self.config.features.enable_audit_logging
        ):
            rate_limiter = (
                RateLimiter(max_calls=5, period=60)
                if self.config.features.enable_rate_limiter
                else None
            )
            audit_logger = (
                AuditLogger(metrics_hook=metrics_hook)
                if self.config.features.enable_audit_logging
                else None
            )
            self.security_enhancer = SecurityEnhancer(
                rate_limiter=rate_limiter, audit_logger=audit_logger
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
        if self.security_enhancer:
            self.security_enhancer.log_event("login_attempt", {"email": email})
            if not self.security_enhancer.allow_auth_attempt(email):
                return None

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
            if self.security_enhancer:
                self.security_enhancer.log_event("login_failure", {"email": email})
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
                if self.security_enhancer:
                    self.security_enhancer.log_event(
                        "login_blocked", {"email": email, "reason": "intelligent"}
                    )
                return None

        if self.security_enhancer:
            self.security_enhancer.log_event("login_success", {"email": email})

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
