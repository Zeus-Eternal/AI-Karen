"""Session storage interfaces and implementations.

This module defines a :class:`SessionStore` protocol describing the minimal
behaviour required by the authentication system. Three concrete
implementations are provided:

``InMemorySessionStore``
    Stores sessions in process memory. Useful for tests or single process
    deployments.
``RedisSessionStore``
    Uses a Redis backend for distributed deployments. Expiration is handled
    by Redis' key TTLs.
``DatabaseSessionStore``
    Persists sessions in the SQL database using the existing
    ``UserSession`` model.

All stores support configurable session expiration and expose a ``cleanup``
method which removes expired sessions where applicable.
"""

from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Protocol

from ai_karen_engine.database.client import get_db_session
from ai_karen_engine.database.models.auth_models import User, UserSession
from ai_karen_engine.security.models import SessionData, UserData

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - redis optional at runtime
    Redis = None  # type: ignore


class SessionStore(Protocol):
    """Protocol for session storage backends."""

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        ...

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[UserData]:
        ...

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[SessionData]:
        ...

    async def invalidate_session(self, session_token: str) -> bool:
        ...

    async def cleanup(self) -> None:
        ...


@dataclass
class _SessionRecord:
    user_id: str
    expires_at: datetime


class InMemorySessionStore(SessionStore):
    """Simple in-memory session storage."""

    def __init__(self, expire_seconds: int = 3600) -> None:
        self.expire_seconds = expire_seconds
        self.sessions: Dict[str, _SessionRecord] = {}
        self.refresh_map: Dict[str, str] = {}

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        await self.cleanup()
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires = datetime.utcnow() + timedelta(seconds=self.expire_seconds)
        self.sessions[session_token] = _SessionRecord(user_id, expires)
        self.refresh_map[refresh_token] = user_id
        return SessionData(
            access_token=session_token,
            refresh_token=refresh_token,
            session_token=session_token,
            expires_in=self.expire_seconds,
            user_data=None,
        )

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[UserData]:
        await self.cleanup()
        record = self.sessions.get(session_token)
        if not record:
            return None
        return UserData(
            user_id=record.user_id,
            email=record.user_id,
            full_name=None,
            roles=[],
            tenant_id="default",
            preferences={},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[SessionData]:
        await self.cleanup()
        user_id = self.refresh_map.get(refresh_token)
        if not user_id:
            return None
        return await self.create_session(user_id, ip_address, user_agent)

    async def invalidate_session(self, session_token: str) -> bool:
        await self.cleanup()
        return self.sessions.pop(session_token, None) is not None

    async def cleanup(self) -> None:
        now = datetime.utcnow()
        expired = [k for k, v in self.sessions.items() if v.expires_at <= now]
        for key in expired:
            self.sessions.pop(key, None)


class RedisSessionStore(SessionStore):
    """Redis-backed session storage."""

    def __init__(self, redis: Redis, expire_seconds: int = 3600, prefix: str = "sess") -> None:
        if Redis is None:
            raise RuntimeError("redis library is not available")
        self.redis = redis
        self.expire_seconds = expire_seconds
        self.prefix = prefix

    def _key(self, token: str) -> str:
        return f"{self.prefix}:{token}"

    def _refresh_key(self, token: str) -> str:
        return f"{self.prefix}:refresh:{token}"

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        await self.redis.set(self._key(session_token), user_id, ex=self.expire_seconds)
        await self.redis.set(
            self._refresh_key(refresh_token), user_id, ex=self.expire_seconds
        )
        return SessionData(
            access_token=session_token,
            refresh_token=refresh_token,
            session_token=session_token,
            expires_in=self.expire_seconds,
            user_data=None,
        )

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[UserData]:
        user_id = await self.redis.get(self._key(session_token))
        if not user_id:
            return None
        user_id_str = user_id.decode() if isinstance(user_id, bytes) else str(user_id)
        return UserData(
            user_id=user_id_str,
            email=user_id_str,
            full_name=None,
            roles=[],
            tenant_id="default",
            preferences={},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[SessionData]:
        user_id = await self.redis.get(self._refresh_key(refresh_token))
        if not user_id:
            return None
        await self.redis.delete(self._refresh_key(refresh_token))
        user_id_str = user_id.decode() if isinstance(user_id, bytes) else str(user_id)
        return await self.create_session(user_id_str, ip_address, user_agent)

    async def invalidate_session(self, session_token: str) -> bool:
        return bool(await self.redis.delete(self._key(session_token)))

    async def cleanup(self) -> None:  # pragma: no cover - redis handles expiration
        return None


class DatabaseSessionStore(SessionStore):
    """Database-backed session storage using ``UserSession`` model."""

    def __init__(self, expire_seconds: int = 3600) -> None:
        self.expire_seconds = expire_seconds

    async def create_session(
        self,
        user_id: str,
        ip_address: str = "",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
    ) -> SessionData:
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=self.expire_seconds)
        with get_db_session() as db:
            session = UserSession(
                user_id=uuid.UUID(user_id),
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
            expires_in=self.expire_seconds,
            user_data=None,
        )

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "",
        user_agent: str = "",
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
        return UserData(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            roles=[],
            tenant_id=user.tenant_id,
            preferences={},
            two_factor_enabled=False,
            is_verified=True,
        )

    async def refresh_token(
        self,
        refresh_token: str,
        ip_address: str = "",
        user_agent: str = "",
    ) -> Optional[SessionData]:
        with get_db_session() as db:
            session = (
                db.query(UserSession)
                .filter(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active.is_(True),
                    UserSession.expires_at > datetime.utcnow(),
                )
                .first()
            )
            if not session:
                return None
            session.is_active = False
            db.add(session)
            db.commit()
        return await self.create_session(str(session.user_id), ip_address, user_agent)

    async def invalidate_session(self, session_token: str) -> bool:
        with get_db_session() as db:
            session = db.query(UserSession).filter(UserSession.session_token == session_token).first()
            if not session:
                return False
            session.is_active = False
            db.add(session)
            db.commit()
            return True

    async def cleanup(self) -> None:
        with get_db_session() as db:
            db.query(UserSession).filter(UserSession.expires_at <= datetime.utcnow()).delete()
            db.commit()
