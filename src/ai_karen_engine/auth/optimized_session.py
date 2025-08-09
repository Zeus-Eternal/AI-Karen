"""
PostgreSQL-optimized session management for authentication operations.

This module provides high-performance session management using PostgreSQL-specific
features like efficient cleanup, foreign key constraints, and optimized queries.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .config import SessionConfig
from .exceptions import SessionExpiredError, SessionNotFoundError, DatabaseOperationError
from .models import SessionData, UserData
from .optimized_database import OptimizedAuthDatabaseClient
from .tokens import TokenManager

try:
    from sqlalchemy import text
    import json
except ImportError:
    text = None
    import json


class OptimizedSessionManager:
    """
    PostgreSQL-optimized session manager with efficient storage and cleanup.
    
    Features:
    - Automatic expired session cleanup
    - Efficient session validation with JOINs
    - Connection pooling optimization
    - Batch operations for maintenance
    """

    def __init__(
        self, 
        config: SessionConfig, 
        token_manager: TokenManager,
        db_client: OptimizedAuthDatabaseClient
    ) -> None:
        """Initialize optimized session manager."""
        self.config = config
        self.token_manager = token_manager
        self.db_client = db_client
        self.logger = logging.getLogger(f"{__name__}.OptimizedSessionManager")
        
        # Session cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5 minutes
        self._running = False

    async def start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        if self._running:
            return
            
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Session manager background tasks started")

    async def stop_background_tasks(self) -> None:
        """Stop background maintenance tasks."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Session manager background tasks stopped")

    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SessionData:
        """
        Create a new session with optimized PostgreSQL storage.
        
        This method includes automatic cleanup of old sessions and efficient storage.
        """
        try:
            # Check session limits for user
            active_sessions = await self.db_client.get_user_sessions_count(user_data.user_id)
            if active_sessions >= self.config.max_sessions_per_user:
                # Clean up oldest sessions to make room
                await self._cleanup_oldest_user_sessions(
                    user_data.user_id, 
                    keep_count=self.config.max_sessions_per_user - 1
                )

            # Generate tokens
            access_token = self.token_manager.create_access_token(user_data)
            refresh_token = self.token_manager.create_refresh_token(user_data)
            session_token = self._generate_session_token()

            # Create session data
            session_data = SessionData(
                session_token=session_token,
                access_token=access_token,
                refresh_token=refresh_token,
                user_data=user_data,
                expires_in=int(self.config.session_timeout.total_seconds()),
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                geolocation=geolocation,
            )

            # Store in database with optimizations
            await self.db_client.create_session_optimized(session_data)

            self.logger.info(f"Created optimized session for user {user_data.user_id}")
            return session_data

        except Exception as e:
            self.logger.error(f"Failed to create optimized session: {e}")
            raise DatabaseOperationError(f"Session creation failed: {e}", operation="create_session")

    async def validate_session(self, session_token: str) -> Optional[UserData]:
        """
        Validate session token with optimized database query.
        
        Uses JOIN operations to get both session and user data efficiently.
        """
        try:
            result = await self.db_client.validate_session_with_user(session_token)
            if not result:
                return None

            session_data, user_data = result

            # Additional validation checks
            if session_data.is_expired():
                await self._invalidate_session(session_token, "expired")
                raise SessionExpiredError(session_token=session_token)

            if not user_data.is_active:
                await self._invalidate_session(session_token, "user_deactivated")
                return None

            if user_data.is_locked():
                await self._invalidate_session(session_token, "user_locked")
                return None

            return user_data

        except SessionExpiredError:
            raise
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return None

    async def get_session(self, session_token: str) -> Optional[SessionData]:
        """Get full session data by token."""
        try:
            result = await self.db_client.validate_session_with_user(session_token)
            if not result:
                return None

            session_data, _ = result
            return session_data

        except Exception as e:
            self.logger.error(f"Failed to get session: {e}")
            return None

    async def update_session(self, session_data: SessionData) -> bool:
        """Update session data in database."""
        try:
            async with self.db_client.session_factory() as session:
                await session.execute(text("""
                    UPDATE auth_sessions 
                    SET risk_score = :risk_score,
                        security_flags = :security_flags,
                        last_accessed = :last_accessed,
                        geolocation = :geolocation
                    WHERE session_token = :session_token
                    AND is_active = true
                """), {
                    "risk_score": session_data.risk_score,
                    "security_flags": json.dumps(session_data.security_flags),
                    "last_accessed": session_data.last_accessed,
                    "geolocation": json.dumps(session_data.geolocation) if session_data.geolocation else None,
                    "session_token": session_data.session_token,
                })

                await session.commit()
                return True

        except Exception as e:
            self.logger.error(f"Failed to update session: {e}")
            return False

    async def invalidate_session(self, session_token: str, reason: str = "manual") -> bool:
        """Invalidate a session token."""
        return await self._invalidate_session(session_token, reason)

    async def invalidate_user_sessions(self, user_id: str, reason: str = "user_action") -> int:
        """Invalidate all sessions for a user."""
        try:
            async with self.db_client.session_factory() as session:
                result = await session.execute(text("""
                    UPDATE auth_sessions 
                    SET is_active = false,
                        invalidated_at = NOW(),
                        invalidation_reason = :reason
                    WHERE user_id = :user_id
                    AND is_active = true
                """), {
                    "user_id": user_id,
                    "reason": reason
                })

                await session.commit()
                count = result.rowcount
                
                self.logger.info(f"Invalidated {count} sessions for user {user_id}")
                return count

        except Exception as e:
            self.logger.error(f"Failed to invalidate user sessions: {e}")
            return 0

    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[SessionData]:
        """Get all sessions for a user."""
        try:
            async with self.db_client.session_factory() as session:
                where_clause = "WHERE user_id = :user_id"
                if active_only:
                    where_clause += " AND is_active = true AND (created_at + INTERVAL '1 second' * expires_in) > NOW()"

                result = await session.execute(text(f"""
                    SELECT 
                        session_token, access_token, refresh_token, expires_in,
                        created_at, last_accessed, ip_address, user_agent,
                        device_fingerprint, geolocation, risk_score, security_flags,
                        is_active, invalidated_at, invalidation_reason
                    FROM auth_sessions 
                    {where_clause}
                    ORDER BY created_at DESC
                """), {"user_id": user_id})

                sessions = []
                for row in result.fetchall():
                    # We need user data - get it separately for now
                    user_data = await self.db_client.get_user_by_id(user_id)
                    if not user_data:
                        continue

                    session_data = SessionData(
                        session_token=row.session_token,
                        access_token=row.access_token,
                        refresh_token=row.refresh_token,
                        user_data=user_data,
                        expires_in=row.expires_in,
                        created_at=row.created_at,
                        last_accessed=row.last_accessed,
                        ip_address=row.ip_address or "unknown",
                        user_agent=row.user_agent or "",
                        device_fingerprint=row.device_fingerprint,
                        geolocation=json.loads(row.geolocation) if row.geolocation else None,
                        risk_score=row.risk_score,
                        security_flags=json.loads(row.security_flags) if row.security_flags else [],
                        is_active=row.is_active,
                        invalidated_at=row.invalidated_at,
                        invalidation_reason=row.invalidation_reason,
                    )
                    sessions.append(session_data)

                return sessions

        except Exception as e:
            self.logger.error(f"Failed to get user sessions: {e}")
            return []

    async def refresh_session(self, refresh_token: str) -> Optional[SessionData]:
        """Refresh a session using refresh token."""
        try:
            # Validate refresh token
            user_data = self.token_manager.validate_refresh_token(refresh_token)
            if not user_data:
                return None

            # Find session with this refresh token
            async with self.db_client.session_factory() as session:
                result = await session.execute(text("""
                    SELECT session_token FROM auth_sessions 
                    WHERE refresh_token = :refresh_token 
                    AND is_active = true
                """), {"refresh_token": refresh_token})

                row = result.fetchone()
                if not row:
                    return None

                session_token = row.session_token

            # Get current session data
            current_session = await self.get_session(session_token)
            if not current_session:
                return None

            # Create new tokens
            new_access_token = self.token_manager.create_access_token(user_data)
            new_refresh_token = self.token_manager.create_refresh_token(user_data)

            # Update session with new tokens
            async with self.db_client.session_factory() as session:
                await session.execute(text("""
                    UPDATE auth_sessions 
                    SET access_token = :access_token,
                        refresh_token = :refresh_token,
                        last_accessed = NOW()
                    WHERE session_token = :session_token
                """), {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "session_token": session_token,
                })

                await session.commit()

            # Update session data object
            current_session.access_token = new_access_token
            current_session.refresh_token = new_refresh_token
            current_session.last_accessed = datetime.utcnow()

            return current_session

        except Exception as e:
            self.logger.error(f"Failed to refresh session: {e}")
            return None

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions efficiently."""
        try:
            count = await self.db_client.cleanup_expired_sessions()
            if count > 0:
                self.logger.info(f"Cleaned up {count} expired sessions")
            return count

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics for monitoring."""
        try:
            return await self.db_client.get_authentication_stats()
        except Exception as e:
            self.logger.error(f"Failed to get session statistics: {e}")
            return {}

    def _generate_session_token(self) -> str:
        """Generate a secure session token."""
        import secrets
        return f"sess_{secrets.token_urlsafe(32)}"

    async def _invalidate_session(self, session_token: str, reason: str) -> bool:
        """Internal method to invalidate a session."""
        try:
            async with self.db_client.session_factory() as session:
                result = await session.execute(text("""
                    UPDATE auth_sessions 
                    SET is_active = false,
                        invalidated_at = NOW(),
                        invalidation_reason = :reason
                    WHERE session_token = :session_token
                    AND is_active = true
                """), {
                    "session_token": session_token,
                    "reason": reason
                })

                await session.commit()
                return result.rowcount > 0

        except Exception as e:
            self.logger.error(f"Failed to invalidate session: {e}")
            return False

    async def _cleanup_oldest_user_sessions(self, user_id: str, keep_count: int) -> None:
        """Clean up oldest sessions for a user, keeping only the most recent ones."""
        try:
            async with self.db_client.session_factory() as session:
                await session.execute(text("""
                    UPDATE auth_sessions 
                    SET is_active = false,
                        invalidated_at = NOW(),
                        invalidation_reason = 'session_limit_exceeded'
                    WHERE session_token IN (
                        SELECT session_token FROM auth_sessions
                        WHERE user_id = :user_id 
                        AND is_active = true
                        ORDER BY created_at ASC
                        LIMIT (
                            SELECT GREATEST(0, COUNT(*) - :keep_count)
                            FROM auth_sessions 
                            WHERE user_id = :user_id AND is_active = true
                        )
                    )
                """), {
                    "user_id": user_id,
                    "keep_count": keep_count
                })

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to cleanup oldest user sessions: {e}")

    async def _cleanup_loop(self) -> None:
        """Background task for periodic session cleanup."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                if not self._running:
                    break
                    
                await self.cleanup_expired_sessions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying