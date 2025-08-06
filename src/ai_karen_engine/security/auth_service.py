"""Unified authentication service with layered components."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
import uuid
import warnings
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import bcrypt
import jwt

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.database.client import get_db_session
from ai_karen_engine.database.models.auth_models import (
    PasswordResetToken,
    User,
    UserSession,
)
from ai_karen_engine.security import auth_manager
from ai_karen_engine.security.config import AuthConfig
from ai_karen_engine.security.intelligence_engine import IntelligenceEngine
from ai_karen_engine.security.models import AuthContext, SessionData, UserData
from ai_karen_engine.security.security_enhancer import (
    AuditLogger,
    RateLimiter,
    SecurityEnhancer,
)
from ai_karen_engine.security.session_store import (
    InMemorySessionStore,
    RedisSessionStore,
    DatabaseSessionStore,
)

try:  # pragma: no cover - redis optional at runtime
    from redis.asyncio import Redis as AsyncRedis
except Exception:  # pragma: no cover
    AsyncRedis = None  # type: ignore

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Core authentication backends
# ---------------------------------------------------------------------------


class InMemoryAuthenticator:
    """Authentication backend using the in-memory :mod:`auth_manager`."""

    def __init__(self, config: AuthConfig) -> None:
        self.secret_key = config.jwt.secret_key
        self.algorithm = config.jwt.algorithm
        self.access_token_expire_minutes = int(
            config.jwt.access_token_expiry.total_seconds() // 60
        )
        self.refresh_token_expire_days = int(
            config.jwt.refresh_token_expiry.total_seconds() // 86400
        )
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        if hasattr(auth_manager, "_USERS"):
            auth_manager._USERS = {}

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
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
        auth_manager.create_user(
            username=email,
            password=password,
            roles=roles or ["user"],
            tenant_id=tenant_id,
            preferences=preferences or {},
        )
        return UserData(
            user_id=email,
            email=email,
            full_name=full_name,
            roles=roles or ["user"],
            tenant_id=tenant_id,
            preferences=preferences or {},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[UserData]:
        user_data = auth_manager.authenticate(email, password)
        if not user_data:
            return None
        return UserData(
            user_id=email,
            email=email,
            full_name=user_data.get("full_name"),
            roles=user_data.get("roles", ["user"]),
            tenant_id=user_data.get("tenant_id", "default"),
            preferences=user_data.get("preferences", {}),
            two_factor_enabled=user_data.get("two_factor_enabled", False),
            is_verified=user_data.get("is_verified", True),
        )

    def _generate_access_token(self, user_id: str) -> str:
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "exp": int(
                (now + timedelta(minutes=self.access_token_expire_minutes)).timestamp()
            ),
            "iat": int(now.timestamp()),
            "type": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def _generate_refresh_token(self, user_id: str) -> str:
        now = datetime.utcnow()
        payload = {
            "user_id": user_id,
            "exp": int(
                (now + timedelta(days=self.refresh_token_expire_days)).timestamp()
            ),
            "iat": int(now.timestamp()),
            "type": "refresh",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        access_token = self._generate_access_token(user_id)
        refresh_token = self._generate_refresh_token(user_id)
        session_token = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_fingerprint": device_fingerprint,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }
        self._active_sessions[session_token] = session_data
        return SessionData(
            access_token=access_token,
            refresh_token=refresh_token,
            session_token=session_token,
            expires_in=self.access_token_expire_minutes * 60,
            user_data=None,
        )

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[UserData]:
        try:
            payload = jwt.decode(
                session_token, self.secret_key, algorithms=[self.algorithm]
            )
            user_id = payload.get("user_id")
            token_type = payload.get("type")
            if user_id and token_type == "access":
                user_data = auth_manager._USERS.get(user_id)
                if user_data:
                    return UserData(
                        user_id=user_id,
                        email=user_id,
                        full_name=user_data.get("full_name"),
                        roles=user_data.get("roles", ["user"]),
                        tenant_id=user_data.get("tenant_id", "default"),
                        preferences=user_data.get("preferences", {}),
                        two_factor_enabled=user_data.get("two_factor_enabled", False),
                        is_verified=user_data.get("is_verified", True),
                    )
        except Exception:
            pass

        session_data = self._active_sessions.get(session_token)
        if session_data:
            user_id = session_data["user_id"]
            user_data = auth_manager._USERS.get(user_id)
            if user_data:
                return UserData(
                    user_id=user_id,
                    email=user_id,
                    full_name=user_data.get("full_name"),
                    roles=user_data.get("roles", ["user"]),
                    tenant_id=user_data.get("tenant_id", "default"),
                    preferences=user_data.get("preferences", {}),
                    two_factor_enabled=user_data.get("two_factor_enabled", False),
                    is_verified=user_data.get("is_verified", True),
                )
        return None

    async def invalidate_session(self, session_token: str) -> bool:
        if session_token in self._active_sessions:
            del self._active_sessions[session_token]
            return True
        return False

    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        try:
            auth_manager.update_password(user_id, new_password)
            return True
        except Exception:
            return False

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        if user_id in auth_manager._USERS:
            auth_manager._USERS[user_id]["preferences"] = preferences
            auth_manager.save_users()
            return True
        return False

    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[str]:
        if email not in auth_manager._USERS:
            return None
        return auth_manager.create_password_reset_token(email)

    async def verify_password_reset_token(self, token: str, new_password: str) -> bool:
        email = auth_manager.verify_password_reset_token(token)
        if not email:
            return False
        auth_manager.update_password(email, new_password)
        return True


class DatabaseAuthenticator:
    """Authentication backend using the SQL database."""

    def __init__(self, config: AuthConfig) -> None:
        self.session_expire_hours = int(
            config.session.session_timeout.total_seconds() // 3600
        )

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
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

    async def authenticate_user(
        self, email: str, password: str, **_: Any
    ) -> Optional[UserData]:
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

    async def validate_session(
        self, session_token: str, **_: Any
    ) -> Optional[UserData]:
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

    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if not user:
                return False
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
        return True

    async def update_user_preferences(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> bool:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if not user:
                return False
            current = json.loads(user.preferences) if user.preferences else {}
            current.update(preferences)
            user.preferences = json.dumps(current)
            user.updated_at = datetime.utcnow()
            db.commit()
        return True

    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[str]:
        with get_db_session() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            token = secrets.token_urlsafe(32)
            reset = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(reset)
            db.commit()
        return token

    async def verify_password_reset_token(self, token: str, new_password: str) -> bool:
        with get_db_session() as db:
            reset = (
                db.query(PasswordResetToken)
                .filter(
                    PasswordResetToken.token == token,
                    PasswordResetToken.is_used.is_(False),
                    PasswordResetToken.expires_at > datetime.utcnow(),
                )
                .first()
            )
            if not reset:
                return False
            user = db.query(User).filter(User.id == reset.user_id).first()
            if not user:
                return False
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            reset.is_used = True
            reset.used_at = datetime.utcnow()
            db.commit()
        return True

    def _to_user_data(self, user: User) -> UserData:
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


class CoreAuthenticator:
    """Wrapper that selects the appropriate backend implementation."""

    def __init__(self, config: Optional[AuthConfig] = None) -> None:
        self.config = config or AuthConfig.from_env()
        self.backend = (
            DatabaseAuthenticator(self.config)
            if self.config.features.use_database
            else InMemoryAuthenticator(self.config)
        )

    def hash_password(self, *args, **kwargs):
        return self.backend.hash_password(*args, **kwargs)

    def verify_password(self, *args, **kwargs):
        return self.backend.verify_password(*args, **kwargs)

    async def create_user(self, *args, **kwargs):
        return await self.backend.create_user(*args, **kwargs)

    async def authenticate_user(self, *args, **kwargs):
        return await self.backend.authenticate_user(*args, **kwargs)

    async def create_session(self, *args, **kwargs):
        return await self.backend.create_session(*args, **kwargs)

    async def validate_session(self, *args, **kwargs):
        return await self.backend.validate_session(*args, **kwargs)

    async def invalidate_session(self, *args, **kwargs):
        return await self.backend.invalidate_session(*args, **kwargs)

    async def update_user_password(self, *args, **kwargs):
        return await self.backend.update_user_password(*args, **kwargs)

    async def update_user_preferences(self, *args, **kwargs):
        return await self.backend.update_user_preferences(*args, **kwargs)

    async def create_password_reset_token(self, *args, **kwargs):
        return await self.backend.create_password_reset_token(*args, **kwargs)

    async def verify_password_reset_token(self, *args, **kwargs):
        return await self.backend.verify_password_reset_token(*args, **kwargs)


# ---------------------------------------------------------------------------
# High level service
# ---------------------------------------------------------------------------


class AuthService:
    """High level authentication façade with optional advanced features."""

    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        metrics_hook: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        core_authenticator: Optional[CoreAuthenticator] = None,
        security_enhancer: Optional[SecurityEnhancer] = None,
        intelligence_engine: Optional[IntelligenceEngine] = None,
        session_store: Optional[Any] = None,
    ) -> None:
        self.config = config or AuthConfig.from_env()

        self.core_authenticator = core_authenticator or CoreAuthenticator(self.config)

        if session_store is not None:
            self.session_store = session_store
        else:
            expire_seconds = int(self.config.session.session_timeout.total_seconds())
            backend = (self.config.session.storage_backend or "memory").lower()
            if backend == "redis":
                if AsyncRedis is None:
                    raise RuntimeError("Redis session backend requires redis library")
                redis_url = self.config.session.redis_url or "redis://localhost:6379/0"
                redis_client = AsyncRedis.from_url(redis_url)
                self.session_store = RedisSessionStore(redis_client, expire_seconds)
            elif backend in {"database", "sql"}:
                self.session_store = DatabaseSessionStore(expire_seconds)
            else:
                self.session_store = InMemorySessionStore(expire_seconds)

        self.intelligence_engine = (
            intelligence_engine
            if intelligence_engine is not None
            else (
                IntelligenceEngine()
                if self.config.features.enable_intelligent_checks
                else None
            )
        )

        if security_enhancer is not None:
            self.security_enhancer = security_enhancer
        elif (
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
        else:
            self.security_enhancer = None

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserData:
        return await self.core_authenticator.create_user(
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
    ) -> Optional[UserData]:
        if self.security_enhancer:
            self.security_enhancer.log_event("login_attempt", {"email": email})
            if not self.security_enhancer.allow_auth_attempt(email):
                return None

        user = await self.core_authenticator.authenticate_user(
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if not user:
            if self.security_enhancer:
                self.security_enhancer.log_event("login_failure", {"email": email})
            return None

        user_data = user

        if self.intelligence_engine:
            context = AuthContext(
                email=email,
                password_hash=hashlib.sha256(password.encode()).hexdigest(),
                client_ip=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                request_id=f"{email}:{int(time.time()*1000)}",
            )
            if hasattr(self.intelligence_engine, "calculate_risk_score"):
                risk_score = await self.intelligence_engine.calculate_risk_score(
                    context
                )
                thresholds = self.intelligence_engine.config.risk_thresholds
                if risk_score >= thresholds.high_risk_threshold:
                    logger.warning("Login attempt blocked due to high risk score")
                    if self.security_enhancer:
                        self.security_enhancer.log_event(
                            "login_blocked", {"email": email, "reason": "intelligent"}
                        )
                    return None
            elif hasattr(self.intelligence_engine, "analyze_login_attempt"):
                analysis = await self.intelligence_engine.analyze_login_attempt(context)
                if getattr(analysis, "should_block", False):
                    logger.warning("Login attempt blocked due to intelligent analysis")
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
        return await self.session_store.create_session(
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
    ) -> Optional[UserData]:
        return await self.session_store.validate_session(
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def invalidate_session(self, session_token: str) -> bool:
        if hasattr(self.session_store, "invalidate_session"):
            return await self.session_store.invalidate_session(session_token)
        return False

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> Optional[SessionData]:
        if hasattr(self.session_store, "refresh_token"):
            return await self.session_store.refresh_token(
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        return None

    async def update_password(self, user_id: str, new_password: str) -> bool:
        if hasattr(self.core_authenticator, "update_user_password"):
            return await self.core_authenticator.update_user_password(
                user_id=user_id, new_password=new_password
            )
        return False

    async def reset_password(self, token: str, new_password: str) -> bool:
        if hasattr(self.core_authenticator, "verify_password_reset_token"):
            return await self.core_authenticator.verify_password_reset_token(
                token=token, new_password=new_password
            )
        return False

    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None) -> None:
        if self.security_enhancer:
            self.security_enhancer.log_event(event, data)


_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Return a shared :class:`AuthService` instance."""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService(AuthConfig.from_env())
    return _auth_service_instance


def __getattr__(name: str) -> Any:  # pragma: no cover - legacy access
    if name == "auth_service":
        warnings.warn(
            "'auth_service' direct import is deprecated. Use 'get_auth_service()' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return get_auth_service()
    raise AttributeError(name)


__all__ = ["AuthService", "AuthConfig", "get_auth_service", "auth_service"]
