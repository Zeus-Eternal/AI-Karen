"""
Session storage and management for the consolidated authentication service.

Provides session storage backends (database, Redis, in-memory) and FastAPI
auth dependencies (`get_current_user`, `get_current_user_optional`, `require_roles`).
"""

from __future__ import annotations

import asyncio
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from .config import SessionConfig
from .exceptions import DatabaseOperationError, SessionError
from .models import SessionData, UserData
from .tokens import TokenManager

# =============================================================================
# Session Manager
# =============================================================================


class SessionManager:
    """
    Complete session management system with token generation, validation, and cleanup.
    """

    def __init__(
        self, config: SessionConfig, token_manager: TokenManager, db_client=None
    ) -> None:
        """Initialize session manager with configuration and token manager."""
        self.config = config
        self.token_manager = token_manager
        self.store = SessionStore(config, db_client)
        self._cleanup_task: Optional[asyncio.Task] = None  # started lazily

    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No running loop; caller can start later.
            pass

    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(3600)  # hourly
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception:
                # Keep going on errors
                pass

    def generate_session_token(self) -> str:
        """Generate a secure session token."""
        return secrets.token_urlsafe(32)

    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict] = None,
        risk_score: float = 0.0,
    ) -> SessionData:
        """Create a new session for a user."""
        session_token = self.generate_session_token()
        access_token = await self.token_manager.create_access_token(user_data)
        refresh_token = await self.token_manager.create_refresh_token(user_data)

        expires_in = int(self.config.session_timeout.total_seconds())

        session_data = SessionData(
            session_token=session_token,
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=user_data,
            expires_in=expires_in,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            geolocation=geolocation,
            risk_score=risk_score,
        )

        await self._enforce_session_limit(user_data.user_id)
        await self.store.store_session(session_data)
        return session_data

    async def validate_session(self, session_token: str) -> Optional[SessionData]:
        """Validate a session token and return session data if valid."""
        if not session_token:
            return None

        session = await self.store.get_session(session_token)
        if not session:
            return None

        if session.is_expired():
            await self.store.delete_session(session_token)
            return None

        session.update_last_accessed()
        await self.store.update_session(session)
        return session

    async def refresh_session(
        self, session_token: str, refresh_token: str
    ) -> Optional[SessionData]:
        """Refresh a session using a refresh token."""
        session = await self.store.get_session(session_token)
        if not session or session.refresh_token != refresh_token:
            return None

        try:
            await self.token_manager.validate_refresh_token(refresh_token)
            new_access_token = await self.token_manager.create_access_token(
                session.user_data
            )
            session.access_token = new_access_token
            session.update_last_accessed()
            await self.store.update_session(session)
            return session
        except Exception:
            return None

    async def invalidate_session(
        self, session_token: str, reason: str = "manual"
    ) -> bool:
        """Invalidate a session."""
        session = await self.store.get_session(session_token)
        if not session:
            return False
        session.invalidate(reason)
        await self.store.update_session(session)
        return True

    async def delete_session(self, session_token: str) -> bool:
        """Delete a session completely."""
        return await self.store.delete_session(session_token)

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all active sessions for a user."""
        return await self.store.get_user_sessions(user_id)

    async def invalidate_user_sessions(
        self,
        user_id: str,
        exclude_session: Optional[str] = None,
        reason: str = "user_logout",
    ) -> int:
        """Invalidate all sessions for a user."""
        sessions = await self.store.get_user_sessions(user_id)
        invalidated_count = 0
        for session in sessions:
            if exclude_session and session.session_token == exclude_session:
                continue
            session.invalidate(reason)
            await self.store.update_session(session)
            invalidated_count += 1
        return invalidated_count

    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        return await self.store.delete_user_sessions(user_id)

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return await self.store.cleanup_expired_sessions()

    async def _enforce_session_limit(self, user_id: str) -> None:
        """Enforce maximum sessions per user limit."""
        if self.config.max_sessions_per_user <= 0:
            return
        sessions = await self.store.get_user_sessions(user_id)
        if len(sessions) >= self.config.max_sessions_per_user:
            sessions.sort(key=lambda s: s.last_accessed)  # oldest first
            to_delete = len(sessions) - self.config.max_sessions_per_user + 1
            for i in range(to_delete):
                await self.store.delete_session(sessions[i].session_token)

    async def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics (placeholder; implement per backend if needed)."""
        return {"total_sessions": 0, "active_sessions": 0, "expired_sessions": 0}

    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    def __del__(self) -> None:  # best-effort
        self.stop_cleanup_task()


# =============================================================================
# Store + Backends
# =============================================================================


class SessionStore:
    """Session storage manager supporting multiple backends."""

    def __init__(self, config: SessionConfig, db_client=None) -> None:
        self.config = config
        if config.storage_type == "database":
            self.backend = DatabaseSessionBackend(config, db_client)
        elif config.storage_type == "redis":
            self.backend = RedisSessionBackend(config)
        elif config.storage_type == "memory":
            self.backend = MemorySessionBackend(config)
        else:
            raise ValueError(f"Unsupported session storage type: {config.storage_type}")

    async def store_session(self, session_data: SessionData) -> None:
        await self.backend.store_session(session_data)

    async def get_session(self, session_token: str) -> Optional[SessionData]:
        return await self.backend.get_session(session_token)

    async def update_session(self, session_data: SessionData) -> None:
        await self.backend.update_session(session_data)

    async def delete_session(self, session_token: str) -> bool:
        return await self.backend.delete_session(session_token)

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        return await self.backend.get_user_sessions(user_id)

    async def delete_user_sessions(self, user_id: str) -> int:
        return await self.backend.delete_user_sessions(user_id)

    async def cleanup_expired_sessions(self) -> int:
        return await self.backend.cleanup_expired_sessions()


class DatabaseSessionBackend:
    """PostgreSQL-backed session storage using the unified auth database client."""

    def __init__(self, config: SessionConfig, db_client=None) -> None:
        self.config = config
        self.db_client = db_client  # Will be injected by SessionManager

    async def store_session(self, session_data: SessionData) -> None:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="store_session"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                    INSERT INTO auth_sessions (
                        session_token, user_id, access_token, refresh_token, expires_in,
                        created_at, last_accessed, ip_address, user_agent, device_fingerprint,
                        geolocation, risk_score, security_flags, is_active, invalidated_at,
                        invalidation_reason
                    ) VALUES (
                        :session_token, :user_id, :access_token, :refresh_token, :expires_in,
                        :created_at, :last_accessed, :ip_address, :user_agent, :device_fingerprint,
                        :geolocation, :risk_score, :security_flags, :is_active, :invalidated_at,
                        :invalidation_reason
                    )
                    ON CONFLICT (session_token) DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        last_accessed = EXCLUDED.last_accessed,
                        risk_score = EXCLUDED.risk_score,
                        security_flags = EXCLUDED.security_flags,
                        is_active = EXCLUDED.is_active,
                        invalidated_at = EXCLUDED.invalidated_at,
                        invalidation_reason = EXCLUDED.invalidation_reason
                """
                    ),
                    {
                        "session_token": session_data.session_token,
                        "user_id": session_data.user_data.user_id,
                        "access_token": session_data.access_token,
                        "refresh_token": session_data.refresh_token,
                        "expires_in": session_data.expires_in,
                        "created_at": session_data.created_at,
                        "last_accessed": session_data.last_accessed,
                        "ip_address": session_data.ip_address,
                        "user_agent": session_data.user_agent,
                        "device_fingerprint": session_data.device_fingerprint,
                        "geolocation": json.dumps(session_data.geolocation)
                        if session_data.geolocation
                        else None,
                        "risk_score": session_data.risk_score,
                        "security_flags": json.dumps(session_data.security_flags),
                        "is_active": session_data.is_active,
                        "invalidated_at": session_data.invalidated_at,
                        "invalidation_reason": session_data.invalidation_reason,
                    },
                )
                await session.commit()
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to store session: {e}", operation="store_session"
            )

    async def get_session(self, session_token: str) -> Optional[SessionData]:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="get_session"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text
                result = await session.execute(text("""
                    SELECT 
                        s.session_token, s.access_token, s.refresh_token, s.expires_in,
                        s.created_at as session_created_at, s.last_accessed, s.ip_address, 
                        s.user_agent, s.device_fingerprint, s.geolocation, s.risk_score, 
                        s.security_flags,
                        u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
                        u.is_verified, u.is_active, u.created_at as user_created_at, 
                        u.updated_at, u.last_login_at, u.failed_login_attempts, u.locked_until,
                        u.two_factor_enabled, u.two_factor_secret
                    FROM auth_sessions s
                    JOIN auth_users u ON s.user_id = u.user_id
                    WHERE s.session_token = :session_token AND s.is_active = true
                """
                    ),
                    {"session_token": session_token},
                )

                row = result.fetchone()
                if not row:
                    return None
                return self._row_to_session_data(row)
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get session: {e}", operation="get_session"
            )

    async def update_session(self, session_data: SessionData) -> None:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="update_session"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text

                await session.execute(
                    text(
                        """
                    UPDATE auth_sessions SET
                        last_accessed = :last_accessed, risk_score = :risk_score,
                        security_flags = :security_flags, is_active = :is_active,
                        invalidated_at = :invalidated_at, invalidation_reason = :invalidation_reason
                    WHERE session_token = :session_token
                """
                    ),
                    {
                        "last_accessed": session_data.last_accessed,
                        "risk_score": session_data.risk_score,
                        "security_flags": json.dumps(session_data.security_flags),
                        "is_active": session_data.is_active,
                        "invalidated_at": session_data.invalidated_at,
                        "invalidation_reason": session_data.invalidation_reason,
                        "session_token": session_data.session_token,
                    },
                )
                await session.commit()
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to update session: {e}", operation="update_session"
            )

    async def delete_session(self, session_token: str) -> bool:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="delete_session"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                    DELETE FROM auth_sessions WHERE session_token = :session_token
                """
                    ),
                    {"session_token": session_token},
                )
                await session.commit()
                return result.rowcount > 0
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to delete session: {e}", operation="delete_session"
            )

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="get_user_sessions"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text
                result = await session.execute(text("""
                    SELECT 
                        s.session_token, s.access_token, s.refresh_token, s.expires_in,
                        s.created_at as session_created_at, s.last_accessed, s.ip_address, 
                        s.user_agent, s.device_fingerprint, s.geolocation, s.risk_score, 
                        s.security_flags,
                        u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
                        u.is_verified, u.is_active, u.created_at as user_created_at, 
                        u.updated_at, u.last_login_at, u.failed_login_attempts, u.locked_until,
                        u.two_factor_enabled, u.two_factor_secret
                    FROM auth_sessions s
                    JOIN auth_users u ON s.user_id = u.user_id
                    WHERE s.user_id = :user_id AND s.is_active = true
                    ORDER BY s.last_accessed DESC
                """
                    ),
                    {"user_id": user_id},
                )

                rows = result.fetchall()
                return [self._row_to_session_data(row) for row in rows]
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user sessions: {e}", operation="get_user_sessions"
            )

    async def delete_user_sessions(self, user_id: str) -> int:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="delete_user_sessions"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                    DELETE FROM auth_sessions WHERE user_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to delete user sessions: {e}", operation="delete_user_sessions"
            )

    async def cleanup_expired_sessions(self) -> int:
        if not self.db_client:
            raise DatabaseOperationError(
                "Database client not available", operation="cleanup_sessions"
            )

        try:
            async with self.db_client.session_factory() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text(
                        """
                    DELETE FROM auth_sessions
                    WHERE created_at + INTERVAL '1 second' * expires_in < NOW()
                """
                    )
                )
                await session.commit()
                return result.rowcount
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to cleanup expired sessions: {e}", operation="cleanup_sessions"
            )

    def _row_to_session_data(self, row) -> SessionData:
        # Column order from the explicit SELECT query:
        # s.session_token, s.access_token, s.refresh_token, s.expires_in,
        # s.created_at as session_created_at, s.last_accessed, s.ip_address, 
        # s.user_agent, s.device_fingerprint, s.geolocation, s.risk_score, 
        # s.security_flags,
        # u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
        # u.is_verified, u.is_active, u.created_at as user_created_at, 
        # u.updated_at, u.last_login_at, u.failed_login_attempts, u.locked_until,
        # u.two_factor_enabled, u.two_factor_secret
        
        user_data = UserData(
            user_id=str(row[12]),  # u.user_id
            email=row[13],  # u.email
            full_name=row[14],  # u.full_name
            roles=row[15] if isinstance(row[15], list) else (json.loads(row[15]) if row[15] else []),  # u.roles
            tenant_id=str(row[16]),  # u.tenant_id
            preferences=row[17] if isinstance(row[17], dict) else (json.loads(row[17]) if row[17] else {}),  # u.preferences
            is_verified=bool(row[18]),  # u.is_verified
            is_active=bool(row[19]),  # u.is_active
            created_at=row[20] if isinstance(row[20], datetime) else datetime.fromisoformat(str(row[20])),  # u.created_at
            updated_at=row[21] if isinstance(row[21], datetime) else datetime.fromisoformat(str(row[21])),  # u.updated_at
            last_login_at=row[22] if isinstance(row[22], datetime) else (datetime.fromisoformat(str(row[22])) if row[22] else None),  # u.last_login_at
            failed_login_attempts=row[23] or 0,  # u.failed_login_attempts
            locked_until=row[24] if isinstance(row[24], datetime) else (datetime.fromisoformat(str(row[24])) if row[24] else None),  # u.locked_until
            two_factor_enabled=bool(row[25]),  # u.two_factor_enabled
            two_factor_secret=row[26],  # u.two_factor_secret
        )

        return SessionData(
            session_token=row[0],  # s.session_token
            access_token=row[1],  # s.access_token
            refresh_token=row[2],  # s.refresh_token
            user_data=user_data,
            expires_in=row[3],  # s.expires_in
            created_at=row[4] if isinstance(row[4], datetime) else datetime.fromisoformat(str(row[4])),  # s.created_at
            last_accessed=row[5] if isinstance(row[5], datetime) else datetime.fromisoformat(str(row[5])),  # s.last_accessed
            ip_address=row[6],  # s.ip_address
            user_agent=row[7],  # s.user_agent
            device_fingerprint=row[8],  # s.device_fingerprint
            geolocation=row[9] if isinstance(row[9], dict) else (json.loads(row[9]) if row[9] else None),  # s.geolocation
            risk_score=row[10] or 0.0,  # s.risk_score
            security_flags=row[11] if isinstance(row[11], list) else (json.loads(row[11]) if row[11] else []),  # s.security_flags
        )


class RedisSessionBackend:
    """Redis-backed session storage for high-performance session management."""

    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self.redis_client = None
        self._setup_redis_connection()

    def _setup_redis_connection(self) -> None:
        try:
            import redis.asyncio as redis

            if not self.config.redis_url:
                raise ValueError("Redis URL is required for Redis session backend")

            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
        except ImportError:
            raise ImportError(
                "redis package is required for Redis session backend. Install with: pip install redis"
            )
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to connect to Redis: {e}", operation="redis_connect"
            )

    def _get_session_key(self, session_token: str) -> str:
        return f"auth:session:{session_token}"

    def _get_user_sessions_key(self, user_id: str) -> str:
        return f"auth:user_sessions:{user_id}"

    async def store_session(self, session_data: SessionData) -> None:
        try:
            session_key = self._get_session_key(session_data.session_token)
            user_sessions_key = self._get_user_sessions_key(
                session_data.user_data.user_id
            )

            session_json = json.dumps(session_data.to_dict())
            ttl_seconds = int(self.config.session_timeout.total_seconds())

            pipe = self.redis_client.pipeline()
            pipe.setex(session_key, ttl_seconds, session_json)
            pipe.sadd(user_sessions_key, session_data.session_token)
            pipe.expire(user_sessions_key, ttl_seconds)
            await pipe.execute()
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to store session in Redis: {e}", operation="store_session"
            )

    async def get_session(self, session_token: str) -> Optional[SessionData]:
        try:
            session_key = self._get_session_key(session_token)
            session_json = await self.redis_client.get(session_key)
            if not session_json:
                return None
            return SessionData.from_dict(json.loads(session_json))
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get session from Redis: {e}", operation="get_session"
            )

    async def update_session(self, session_data: SessionData) -> None:
        try:
            session_key = self._get_session_key(session_data.session_token)
            exists = await self.redis_client.exists(session_key)
            if not exists:
                return
            session_json = json.dumps(session_data.to_dict())
            ttl = await self.redis_client.ttl(session_key)
            if ttl > 0:
                await self.redis_client.setex(session_key, ttl, session_json)
            else:
                ttl_seconds = int(self.config.session_timeout.total_seconds())
                await self.redis_client.setex(session_key, ttl_seconds, session_json)
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to update session in Redis: {e}", operation="update_session"
            )

    async def delete_session(self, session_token: str) -> bool:
        try:
            session = await self.get_session(session_token)
            if not session:
                return False

            session_key = self._get_session_key(session_token)
            user_sessions_key = self._get_user_sessions_key(session.user_data.user_id)

            pipe = self.redis_client.pipeline()
            pipe.delete(session_key)
            pipe.srem(user_sessions_key, session_token)
            results = await pipe.execute()
            return results[0] > 0
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to delete session from Redis: {e}", operation="delete_session"
            )

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_tokens = await self.redis_client.smembers(user_sessions_key)
            if not session_tokens:
                return []

            pipe = self.redis_client.pipeline()
            for token in session_tokens:
                pipe.get(self._get_session_key(token))
            session_jsons = await pipe.execute()

            sessions: List[SessionData] = []
            expired_tokens: List[str] = []

            tokens_list = list(session_tokens)
            for i, session_json in enumerate(session_jsons):
                token = tokens_list[i]
                if session_json:
                    try:
                        session = SessionData.from_dict(json.loads(session_json))
                        if not session.is_expired():
                            sessions.append(session)
                        else:
                            expired_tokens.append(token)
                    except Exception:
                        expired_tokens.append(token)
                else:
                    expired_tokens.append(token)

            if expired_tokens:
                await self.redis_client.srem(user_sessions_key, *expired_tokens)

            sessions.sort(key=lambda s: s.last_accessed, reverse=True)
            return sessions
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user sessions from Redis: {e}",
                operation="get_user_sessions",
            )

    async def delete_user_sessions(self, user_id: str) -> int:
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_tokens = await self.redis_client.smembers(user_sessions_key)
            if not session_tokens:
                return 0

            pipe = self.redis_client.pipeline()
            for token in session_tokens:
                pipe.delete(self._get_session_key(token))
            pipe.delete(user_sessions_key)
            results = await pipe.execute()

            return sum(1 for r in results[:-1] if r > 0)
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to delete user sessions from Redis: {e}",
                operation="delete_user_sessions",
            )

    async def cleanup_expired_sessions(self) -> int:
        # Redis handles key expiry via TTL; orphan set members cleaned during reads.
        return 0


class MemorySessionBackend:
    """In-memory session storage for development and testing."""

    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, set] = {}  # user_id -> set(session_token)

    async def store_session(self, session_data: SessionData) -> None:
        self.sessions[session_data.session_token] = session_data
        uid = session_data.user_data.user_id
        self.user_sessions.setdefault(uid, set()).add(session_data.session_token)

    async def get_session(self, session_token: str) -> Optional[SessionData]:
        session = self.sessions.get(session_token)
        if session and self._is_time_expired(session):
            await self.delete_session(session_token)
            return None
        return session

    def _is_time_expired(self, session: SessionData) -> bool:
        expires_at = session.created_at + timedelta(seconds=session.expires_in)
        return datetime.now(timezone.utc) > expires_at

    async def update_session(self, session_data: SessionData) -> None:
        if session_data.session_token in self.sessions:
            self.sessions[session_data.session_token] = session_data

    async def delete_session(self, session_token: str) -> bool:
        if session_token in self.sessions:
            session = self.sessions[session_token]
            uid = session.user_data.user_id
            del self.sessions[session_token]
            if uid in self.user_sessions:
                self.user_sessions[uid].discard(session_token)
                if not self.user_sessions[uid]:
                    del self.user_sessions[uid]
            return True
        return False

    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        tokens = list(self.user_sessions.get(user_id, set()))
        out: List[SessionData] = []
        expired: List[str] = []
        for t in tokens:
            s = self.sessions.get(t)
            if s and not self._is_time_expired(s):
                out.append(s)
            else:
                expired.append(t)
        for t in expired:
            await self.delete_session(t)
        out.sort(key=lambda s: s.last_accessed, reverse=True)
        return out

    async def delete_user_sessions(self, user_id: str) -> int:
        tokens = list(self.user_sessions.get(user_id, set()))
        deleted = 0
        for t in tokens:
            if await self.delete_session(t):
                deleted += 1
        return deleted

    async def cleanup_expired_sessions(self) -> int:
        expired = [t for t, s in self.sessions.items() if self._is_time_expired(s)]
        deleted = 0
        for t in expired:
            if await self.delete_session(t):
                deleted += 1
        return deleted


# =============================================================================
# FastAPI dependencies (placed at end, clean exports)
# =============================================================================

# Optional FastAPI import to avoid hard dependency outside API runtime
try:
    from fastapi import Depends, HTTPException, Request, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

    _FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover
    _FASTAPI_AVAILABLE = False

    # Stubs to avoid NameErrors if imported without FastAPI context
    def Depends(*_args: Any, **_kwargs: Any) -> None:  # type: ignore
        """Fallback stub for fastapi.Depends when FastAPI isn't installed."""
        return None

    HTTPException = Exception  # type: ignore
    Request = object  # type: ignore
    status = type("status", (), {"HTTP_401_UNAUTHORIZED": 401, "HTTP_403_FORBIDDEN": 403})  # type: ignore
    HTTPAuthorizationCredentials = object  # type: ignore
    HTTPBearer = lambda *a, **k: None  # type: ignore

_security = HTTPBearer(auto_error=False) if _FASTAPI_AVAILABLE else None  # type: ignore

# Global singleton for dependencies
_session_manager_singleton: Optional[SessionManager] = None


def initialize_session_service(
    config: SessionConfig, token_manager: TokenManager
) -> SessionManager:
    """
    Initialize the global SessionManager used by FastAPI dependencies.
    Call this once during app startup.
    """
    global _session_manager_singleton
    _session_manager_singleton = SessionManager(
        config=config, token_manager=token_manager
    )
    return _session_manager_singleton


def get_session_manager() -> SessionManager:
    """Return the initialized SessionManager or raise a clear error."""
    if _session_manager_singleton is None:
        raise RuntimeError(
            "Session service not initialized. Call initialize_session_service(...) at startup."
        )
    return _session_manager_singleton


async def _maybe_await(fn: Callable, *args, **kwargs):
    if asyncio.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    return fn(*args, **kwargs)


def _to_user_data(payload: Any) -> UserData:
    """Convert token payloads into UserData (supports dict or {'user': {...}})."""
    if isinstance(payload, UserData):
        return payload
    if isinstance(payload, dict):
        data = payload.get("user", payload)
        return UserData(**data)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported token payload type.")  # type: ignore


async def _extract_user_from_access_token(
    tm: TokenManager, access_token: str
) -> UserData:
    """
    Be flexible with TokenManager APIs:
    - validate_access_token(token)
    - decode_access_token(token)
    - verify_access_token(token)
    """
    for method_name in (
        "validate_access_token",
        "decode_access_token",
        "verify_access_token",
    ):
        if hasattr(tm, method_name):
            method = getattr(tm, method_name)
            try:
                payload = await _maybe_await(method, access_token)
                return _to_user_data(payload)
            except Exception:
                continue
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token validation failed.")  # type: ignore


async def get_current_user(
    request: Request,  # type: ignore[type-arg]
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_security),  # type: ignore
) -> UserData:
    """
    Primary auth dependency.
    - Requires Authorization: Bearer <access_token>
    - Optionally validates X-Session-Token if provided
    - Returns UserData
    """
    if not _FASTAPI_AVAILABLE:  # pragma: no cover
        raise RuntimeError("FastAPI is required to use get_current_user.")

    if (
        not creds
        or not getattr(creds, "scheme", None)
        or creds.scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    access_token = getattr(creds, "credentials", "") or ""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty access token."
        )

    sm = get_session_manager()
    tm = sm.token_manager

    user = await _extract_user_from_access_token(tm, access_token)

    session_token = request.headers.get("X-Session-Token")  # type: ignore[attr-defined]
    if session_token:
        session = await sm.validate_session(session_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session.",
            )
        if getattr(session.user_data, "user_id", None) != getattr(
            user, "user_id", None
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token user mismatch for session.",
            )

    return user


async def get_current_user_optional(
    request: Request,  # type: ignore[type-arg]
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_security),  # type: ignore
) -> Optional[UserData]:
    """Non-failing variant: returns None if unauthenticated."""
    if not _FASTAPI_AVAILABLE:  # pragma: no cover
        return None

    if (
        not creds
        or not getattr(creds, "scheme", None)
        or creds.scheme.lower() != "bearer"
    ):
        return None

    access_token = getattr(creds, "credentials", "") or ""
    if not access_token:
        return None

    sm = get_session_manager()
    tm = sm.token_manager

    try:
        user = await _extract_user_from_access_token(tm, access_token)
    except HTTPException:
        return None

    session_token = request.headers.get("X-Session-Token")  # type: ignore[attr-defined]
    if session_token:
        session = await sm.validate_session(session_token)
        if not session:
            return None
        if getattr(session.user_data, "user_id", None) != getattr(
            user, "user_id", None
        ):
            return None

    return user


def require_roles(required: Iterable[str]):
    """
    Role guard factory.

    Usage:
        @router.get("/admin")
        async def admin_route(user=Depends(require_roles(["admin"]))): ...
    """
    required_set = set(required or [])

    async def _dep(user: UserData = Depends(get_current_user)):  # type: ignore
        roles = set(getattr(user, "roles", []) or [])
        if not required_set.issubset(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions.",
            )
        return user

    return _dep


__all__ = [
    # Classes
    "SessionManager",
    "SessionStore",
    "DatabaseSessionBackend",
    "RedisSessionBackend",
    "MemorySessionBackend",
    # FastAPI deps
    "initialize_session_service",
    "get_session_manager",
    "get_current_user",
    "get_current_user_optional",
    "require_roles",
]
