from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, String, Text, select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class SessionModel(Base):
    """Database model for stored sessions."""

    __tablename__ = "session_store"

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), index=True, nullable=True)
    data = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class SessionStore:
    """Flexible session storage supporting memory, Redis, and database backends."""

    def __init__(
        self,
        backend: str = "memory",
        redis_client: Optional[Any] = None,
        db_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None,
        prefix: str = "session_store:",
    ) -> None:
        self.backend = backend
        self.prefix = prefix

        if backend == "memory":
            self._store: Dict[str, Dict[str, Any]] = {}
        elif backend == "redis":
            if redis_client is None:
                raise ValueError("redis_client is required for redis backend")
            self.redis = redis_client
        elif backend == "database":
            if db_sessionmaker is None:
                raise ValueError("db_sessionmaker is required for database backend")
            self.db_sessionmaker = db_sessionmaker
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    # ------------------------------------------------------------------
    # Basic session operations
    # ------------------------------------------------------------------
    async def set_session(
        self, session_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None
    ) -> None:
        """Store a session."""

        expires_at = (
            datetime.utcnow() + timedelta(seconds=ttl_seconds)
            if ttl_seconds
            else None
        )

        if self.backend == "memory":
            self._store[session_id] = {
                "data": data,
                "expires_at": expires_at,
            }
        elif self.backend == "redis":
            key = f"{self.prefix}{session_id}"
            payload = json.dumps(data)
            if ttl_seconds:
                self.redis.setex(key, ttl_seconds, payload)
            else:
                self.redis.set(key, payload)
            user_id = data.get("user_id")
            if user_id:
                self.redis.sadd(f"{self.prefix}user:{user_id}", session_id)
                if ttl_seconds:
                    self.redis.expire(f"{self.prefix}user:{user_id}", ttl_seconds)
        else:  # database
            async with self.db_sessionmaker() as session:
                await session.merge(
                    SessionModel(
                        session_id=session_id,
                        user_id=data.get("user_id"),
                        data=json.dumps(data),
                        expires_at=expires_at,
                    )
                )
                await session.commit()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID."""

        if self.backend == "memory":
            entry = self._store.get(session_id)
            if not entry:
                return None
            if entry["expires_at"] and entry["expires_at"] < datetime.utcnow():
                self._store.pop(session_id, None)
                return None
            return entry["data"]
        elif self.backend == "redis":
            key = f"{self.prefix}{session_id}"
            payload = self.redis.get(key)
            if not payload:
                return None
            return json.loads(payload)
        else:
            async with self.db_sessionmaker() as session:
                db_obj = await session.get(SessionModel, session_id)
                if not db_obj:
                    return None
                if db_obj.expires_at and db_obj.expires_at < datetime.utcnow():
                    await session.delete(db_obj)
                    await session.commit()
                    return None
                return json.loads(db_obj.data)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if removed."""

        if self.backend == "memory":
            return self._store.pop(session_id, None) is not None
        elif self.backend == "redis":
            key = f"{self.prefix}{session_id}"
            existed = self.redis.delete(key)
            # Remove from user mapping
            # Need to scan user sets
            for user_key in self.redis.scan_iter(f"{self.prefix}user:*"):
                self.redis.srem(user_key, session_id)
            return bool(existed)
        else:
            async with self.db_sessionmaker() as session:
                result = await session.execute(
                    delete(SessionModel).where(SessionModel.session_id == session_id)
                )
                await session.commit()
                return result.rowcount > 0

    # ------------------------------------------------------------------
    # Listing helpers
    # ------------------------------------------------------------------
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """Return all sessions as list of dicts including session_id."""
        sessions: List[Dict[str, Any]] = []
        if self.backend == "memory":
            for sid, entry in list(self._store.items()):
                if entry["expires_at"] and entry["expires_at"] < datetime.utcnow():
                    self._store.pop(sid, None)
                    continue
                data = entry["data"].copy()
                data.setdefault("session_id", sid)
                sessions.append(data)
        elif self.backend == "redis":
            for key in self.redis.scan_iter(f"{self.prefix}*"):
                sid = key.decode().replace(self.prefix, "")
                if sid.startswith("user:"):
                    continue
                payload = self.redis.get(key)
                if payload:
                    data = json.loads(payload)
                    data.setdefault("session_id", sid)
                    sessions.append(data)
        else:
            async with self.db_sessionmaker() as session:
                result = await session.execute(select(SessionModel))
                rows = result.scalars().all()
                for row in rows:
                    if row.expires_at and row.expires_at < datetime.utcnow():
                        await session.delete(row)
                        continue
                    data = json.loads(row.data)
                    data.setdefault("session_id", row.session_id)
                    sessions.append(data)
                await session.commit()
        return sessions

    async def get_sessions_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Return sessions for a specific user."""
        if self.backend == "memory":
            result = []
            for sid, entry in list(self._store.items()):
                if entry["expires_at"] and entry["expires_at"] < datetime.utcnow():
                    self._store.pop(sid, None)
                    continue
                if entry["data"].get("user_id") == user_id:
                    data = entry["data"].copy()
                    data.setdefault("session_id", sid)
                    result.append(data)
            return result
        elif self.backend == "redis":
            key = f"{self.prefix}user:{user_id}"
            session_ids = self.redis.smembers(key)
            sessions = []
            for raw_sid in session_ids:
                sid = raw_sid.decode() if isinstance(raw_sid, bytes) else raw_sid
                data = await self.get_session(sid)
                if data:
                    data.setdefault("session_id", sid)
                    sessions.append(data)
            return sessions
        else:
            async with self.db_sessionmaker() as session:
                result = await session.execute(
                    select(SessionModel).where(SessionModel.user_id == user_id)
                )
                rows = result.scalars().all()
                sessions: List[Dict[str, Any]] = []
                for row in rows:
                    if row.expires_at and row.expires_at < datetime.utcnow():
                        await session.delete(row)
                        continue
                    data = json.loads(row.data)
                    data.setdefault("session_id", row.session_id)
                    sessions.append(data)
                await session.commit()
                return sessions

    async def count_sessions(self) -> int:
        """Return total number of sessions."""
        if self.backend == "memory":
            await self._cleanup_memory()
            return len(self._store)
        elif self.backend == "redis":
            return len([key for key in self.redis.scan_iter(f"{self.prefix}*") if not key.decode().startswith(f"{self.prefix}user:")])
        else:
            async with self.db_sessionmaker() as session:
                result = await session.execute(select(func.count()).select_from(SessionModel))
                return result.scalar_one()

    async def _cleanup_memory(self) -> None:
        """Remove expired sessions from memory store."""
        now = datetime.utcnow()
        expired = [sid for sid, v in self._store.items() if v["expires_at"] and v["expires_at"] < now]
        for sid in expired:
            self._store.pop(sid, None)
