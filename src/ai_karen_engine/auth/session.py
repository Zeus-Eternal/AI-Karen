"""
Session storage and management for the consolidated authentication service.

This module provides session storage backends including database, Redis,
and in-memory storage for authentication sessions.
"""

from __future__ import annotations

import asyncio
import json
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .config import SessionConfig
from .exceptions import DatabaseOperationError, SessionError
from .models import SessionData, UserData
from .tokens import TokenManager


class SessionManager:
    """
    Complete session management system with token generation, validation, and cleanup.
    
    This class provides the main interface for session management operations,
    including secure token generation, session validation, and automatic cleanup.
    """
    
    def __init__(self, config: SessionConfig, token_manager: TokenManager) -> None:
        """Initialize session manager with configuration and token manager."""
        self.config = config
        self.token_manager = token_manager
        self.store = SessionStore(config)
        self._cleanup_task: Optional[asyncio.Task] = None
        # Don't start cleanup task during initialization - start it when needed
    
    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running, cleanup task will be started when needed
            pass
    
    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue cleanup even if one iteration fails
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
        risk_score: float = 0.0
    ) -> SessionData:
        """
        Create a new session for a user.
        
        Args:
            user_data: User data for the session
            ip_address: Client IP address
            user_agent: Client user agent
            device_fingerprint: Device fingerprint (optional)
            geolocation: Geolocation data (optional)
            risk_score: Initial risk score
        
        Returns:
            SessionData object with tokens and session information
        """
        # Generate secure tokens
        session_token = self.generate_session_token()
        access_token = await self.token_manager.create_access_token(user_data)
        refresh_token = await self.token_manager.create_refresh_token(user_data)
        
        # Calculate expires_in from access token expiry
        expires_in = int(self.config.session_timeout.total_seconds())
        
        # Create session data
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
            risk_score=risk_score
        )
        
        # Enforce max sessions per user
        await self._enforce_session_limit(user_data.user_id)
        
        # Store the session
        await self.store.store_session(session_data)
        
        return session_data
    
    async def validate_session(self, session_token: str) -> Optional[SessionData]:
        """
        Validate a session token and return session data if valid.
        
        Args:
            session_token: Session token to validate
        
        Returns:
            SessionData if valid, None if invalid or expired
        """
        if not session_token:
            return None
        
        # Get session from storage
        session = await self.store.get_session(session_token)
        if not session:
            return None
        
        # Check if session is expired
        if session.is_expired():
            await self.store.delete_session(session_token)
            return None
        
        # Update last accessed time
        session.update_last_accessed()
        await self.store.update_session(session)
        
        return session
    
    async def refresh_session(
        self,
        session_token: str,
        refresh_token: str
    ) -> Optional[SessionData]:
        """
        Refresh a session using a refresh token.
        
        Args:
            session_token: Current session token
            refresh_token: Refresh token
        
        Returns:
            Updated SessionData with new access token, or None if invalid
        """
        # Get current session
        session = await self.store.get_session(session_token)
        if not session or session.refresh_token != refresh_token:
            return None
        
        try:
            # Validate refresh token
            await self.token_manager.validate_refresh_token(refresh_token)
            
            # Create new access token
            new_access_token = await self.token_manager.create_access_token(session.user_data)
            
            # Update session with new access token
            session.access_token = new_access_token
            session.update_last_accessed()
            
            await self.store.update_session(session)
            return session
            
        except Exception:
            return None
    
    async def invalidate_session(self, session_token: str, reason: str = "manual") -> bool:
        """
        Invalidate a session.
        
        Args:
            session_token: Session token to invalidate
            reason: Reason for invalidation
        
        Returns:
            True if session was invalidated, False if not found
        """
        session = await self.store.get_session(session_token)
        if not session:
            return False
        
        session.invalidate(reason)
        await self.store.update_session(session)
        return True
    
    async def delete_session(self, session_token: str) -> bool:
        """
        Delete a session completely.
        
        Args:
            session_token: Session token to delete
        
        Returns:
            True if session was deleted, False if not found
        """
        return await self.store.delete_session(session_token)
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all active sessions for a user."""
        return await self.store.get_user_sessions(user_id)
    
    async def invalidate_user_sessions(
        self,
        user_id: str,
        exclude_session: Optional[str] = None,
        reason: str = "user_logout"
    ) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            exclude_session: Session token to exclude from invalidation
            reason: Reason for invalidation
        
        Returns:
            Number of sessions invalidated
        """
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
            # Sort by last accessed time (oldest first)
            sessions.sort(key=lambda s: s.last_accessed)
            
            # Delete oldest sessions to make room
            sessions_to_delete = len(sessions) - self.config.max_sessions_per_user + 1
            for i in range(sessions_to_delete):
                await self.store.delete_session(sessions[i].session_token)
    
    async def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics (for monitoring)."""
        # This would be implemented based on the backend capabilities
        # For now, return basic stats
        return {
            "total_sessions": 0,  # Would be implemented per backend
            "active_sessions": 0,
            "expired_sessions": 0
        }
    
    def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
    
    def __del__(self) -> None:
        """Cleanup when session manager is destroyed."""
        self.stop_cleanup_task()


class SessionStore:
    """
    Session storage manager supporting multiple backends.
    
    Supports database, Redis, and in-memory storage based on configuration.
    """
    
    def __init__(self, config: SessionConfig) -> None:
        """Initialize session store with configuration."""
        self.config = config
        
        if config.storage_type == "database":
            self.backend = DatabaseSessionBackend(config)
        elif config.storage_type == "redis":
            self.backend = RedisSessionBackend(config)
        elif config.storage_type == "memory":
            self.backend = MemorySessionBackend(config)
        else:
            raise ValueError(f"Unsupported session storage type: {config.storage_type}")
    
    async def store_session(self, session_data: SessionData) -> None:
        """Store a session."""
        await self.backend.store_session(session_data)
    
    async def get_session(self, session_token: str) -> Optional[SessionData]:
        """Get a session by token."""
        return await self.backend.get_session(session_token)
    
    async def update_session(self, session_data: SessionData) -> None:
        """Update a session."""
        await self.backend.update_session(session_data)
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session."""
        return await self.backend.delete_session(session_token)
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user."""
        return await self.backend.get_user_sessions(user_id)
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        return await self.backend.delete_user_sessions(user_id)
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        return await self.backend.cleanup_expired_sessions()


class DatabaseSessionBackend:
    """Database-backed session storage."""
    
    def __init__(self, config: SessionConfig) -> None:
        """Initialize database session backend."""
        self.config = config
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_connection()
    
    def _setup_connection(self) -> None:
        """Set up database connection."""
        try:
            # For now, use a simple SQLite connection
            # In production, this would use the same database as the main auth database
            self.connection = sqlite3.connect(
                "auth_sessions.db",
                timeout=30,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to connect to session database: {e}")
    
    async def store_session(self, session_data: SessionData) -> None:
        """Store a session in the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO auth_sessions (
                    session_token, user_id, access_token, refresh_token, expires_in,
                    created_at, last_accessed, ip_address, user_agent, device_fingerprint,
                    geolocation, risk_score, security_flags, is_active, invalidated_at,
                    invalidation_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data.session_token,
                session_data.user_data.user_id,
                session_data.access_token,
                session_data.refresh_token,
                session_data.expires_in,
                session_data.created_at.isoformat(),
                session_data.last_accessed.isoformat(),
                session_data.ip_address,
                session_data.user_agent,
                session_data.device_fingerprint,
                json.dumps(session_data.geolocation) if session_data.geolocation else None,
                session_data.risk_score,
                json.dumps(session_data.security_flags),
                session_data.is_active,
                session_data.invalidated_at.isoformat() if session_data.invalidated_at else None,
                session_data.invalidation_reason
            ))
            
            self.connection.commit()
            
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(f"Failed to store session: {e}", operation="store_session")
    
    async def get_session(self, session_token: str) -> Optional[SessionData]:
        """Get a session from the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT s.*, u.* FROM auth_sessions s
                JOIN auth_users u ON s.user_id = u.user_id
                WHERE s.session_token = ? AND s.is_active = 1
            """, (session_token,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_session_data(row)
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get session: {e}", operation="get_session")
    
    async def update_session(self, session_data: SessionData) -> None:
        """Update a session in the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE auth_sessions SET
                    last_accessed = ?, risk_score = ?, security_flags = ?,
                    is_active = ?, invalidated_at = ?, invalidation_reason = ?
                WHERE session_token = ?
            """, (
                session_data.last_accessed.isoformat(),
                session_data.risk_score,
                json.dumps(session_data.security_flags),
                session_data.is_active,
                session_data.invalidated_at.isoformat() if session_data.invalidated_at else None,
                session_data.invalidation_reason,
                session_data.session_token
            ))
            
            self.connection.commit()
            
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(f"Failed to update session: {e}", operation="update_session")
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session from the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM auth_sessions WHERE session_token = ?", (session_token,))
            self.connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(f"Failed to delete session: {e}", operation="delete_session")
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT s.*, u.* FROM auth_sessions s
                JOIN auth_users u ON s.user_id = u.user_id
                WHERE s.user_id = ? AND s.is_active = 1
                ORDER BY s.last_accessed DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            return [self._row_to_session_data(row) for row in rows]
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get user sessions: {e}", operation="get_user_sessions")
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM auth_sessions WHERE user_id = ?", (user_id,))
            self.connection.commit()
            
            return cursor.rowcount
            
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(f"Failed to delete user sessions: {e}", operation="delete_user_sessions")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            cursor = self.connection.cursor()
            
            # Delete sessions that have expired based on their creation time and expires_in
            cursor.execute("""
                DELETE FROM auth_sessions 
                WHERE datetime(created_at, '+' || expires_in || ' seconds') < datetime('now')
            """)
            
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(f"Failed to cleanup expired sessions: {e}", operation="cleanup_sessions")
    
    def _row_to_session_data(self, row: sqlite3.Row) -> SessionData:
        """Convert database row to SessionData object."""
        # Extract user data from the joined row
        user_data = UserData(
            user_id=row["user_id"],
            email=row["email"],
            full_name=row["full_name"],
            roles=json.loads(row["roles"]),
            tenant_id=row["tenant_id"],
            preferences=json.loads(row["preferences"]),
            is_verified=bool(row["is_verified"]),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_login_at=datetime.fromisoformat(row["last_login_at"]) if row["last_login_at"] else None,
            failed_login_attempts=row["failed_login_attempts"],
            locked_until=datetime.fromisoformat(row["locked_until"]) if row["locked_until"] else None,
            two_factor_enabled=bool(row["two_factor_enabled"]),
            two_factor_secret=row["two_factor_secret"]
        )
        
        return SessionData(
            session_token=row["session_token"],
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            user_data=user_data,
            expires_in=row["expires_in"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]),
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            device_fingerprint=row["device_fingerprint"],
            geolocation=json.loads(row["geolocation"]) if row["geolocation"] else None,
            risk_score=row["risk_score"],
            security_flags=json.loads(row["security_flags"]),
            is_active=bool(row["is_active"]),
            invalidated_at=datetime.fromisoformat(row["invalidated_at"]) if row["invalidated_at"] else None,
            invalidation_reason=row["invalidation_reason"]
        )


class RedisSessionBackend:
    """Redis-backed session storage for high-performance session management."""
    
    def __init__(self, config: SessionConfig) -> None:
        """Initialize Redis session backend."""
        self.config = config
        self.redis_client = None
        self._setup_redis_connection()
    
    def _setup_redis_connection(self) -> None:
        """Set up Redis connection."""
        try:
            import redis.asyncio as redis
            
            if not self.config.redis_url:
                raise ValueError("Redis URL is required for Redis session backend")
            
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
        except ImportError:
            raise ImportError("redis package is required for Redis session backend. Install with: pip install redis")
        except Exception as e:
            raise DatabaseOperationError(f"Failed to connect to Redis: {e}", operation="redis_connect")
    
    def _get_session_key(self, session_token: str) -> str:
        """Get Redis key for session."""
        return f"auth:session:{session_token}"
    
    def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user sessions set."""
        return f"auth:user_sessions:{user_id}"
    
    async def store_session(self, session_data: SessionData) -> None:
        """Store a session in Redis."""
        try:
            session_key = self._get_session_key(session_data.session_token)
            user_sessions_key = self._get_user_sessions_key(session_data.user_data.user_id)
            
            # Serialize session data
            session_json = json.dumps(session_data.to_dict())
            
            # Calculate TTL based on session timeout
            ttl_seconds = int(self.config.session_timeout.total_seconds())
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Store session data with TTL
            pipe.setex(session_key, ttl_seconds, session_json)
            
            # Add session token to user's session set
            pipe.sadd(user_sessions_key, session_data.session_token)
            pipe.expire(user_sessions_key, ttl_seconds)
            
            await pipe.execute()
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to store session in Redis: {e}", operation="store_session")
    
    async def get_session(self, session_token: str) -> Optional[SessionData]:
        """Get a session from Redis."""
        try:
            session_key = self._get_session_key(session_token)
            session_json = await self.redis_client.get(session_key)
            
            if not session_json:
                return None
            
            session_dict = json.loads(session_json)
            return SessionData.from_dict(session_dict)
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get session from Redis: {e}", operation="get_session")
    
    async def update_session(self, session_data: SessionData) -> None:
        """Update a session in Redis."""
        try:
            session_key = self._get_session_key(session_data.session_token)
            
            # Check if session exists
            exists = await self.redis_client.exists(session_key)
            if not exists:
                return
            
            # Update session data while preserving TTL
            session_json = json.dumps(session_data.to_dict())
            ttl = await self.redis_client.ttl(session_key)
            
            if ttl > 0:
                await self.redis_client.setex(session_key, ttl, session_json)
            else:
                # If no TTL, use default session timeout
                ttl_seconds = int(self.config.session_timeout.total_seconds())
                await self.redis_client.setex(session_key, ttl_seconds, session_json)
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to update session in Redis: {e}", operation="update_session")
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session from Redis."""
        try:
            # Get session to find user_id
            session = await self.get_session(session_token)
            if not session:
                return False
            
            session_key = self._get_session_key(session_token)
            user_sessions_key = self._get_user_sessions_key(session.user_data.user_id)
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.delete(session_key)
            pipe.srem(user_sessions_key, session_token)
            
            results = await pipe.execute()
            return results[0] > 0
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete session from Redis: {e}", operation="delete_session")
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user from Redis."""
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_tokens = await self.redis_client.smembers(user_sessions_key)
            
            if not session_tokens:
                return []
            
            # Get all sessions in parallel
            pipe = self.redis_client.pipeline()
            for token in session_tokens:
                session_key = self._get_session_key(token)
                pipe.get(session_key)
            
            session_jsons = await pipe.execute()
            
            sessions = []
            expired_tokens = []
            
            for i, session_json in enumerate(session_jsons):
                if session_json:
                    try:
                        session_dict = json.loads(session_json)
                        session = SessionData.from_dict(session_dict)
                        
                        # Check if session is expired
                        if not session.is_expired():
                            sessions.append(session)
                        else:
                            expired_tokens.append(session_tokens[i])
                    except Exception:
                        # Invalid session data, mark for cleanup
                        expired_tokens.append(session_tokens[i])
                else:
                    # Session not found, mark for cleanup
                    expired_tokens.append(session_tokens[i])
            
            # Clean up expired tokens from user sessions set
            if expired_tokens:
                await self.redis_client.srem(user_sessions_key, *expired_tokens)
            
            # Sort by last accessed time (most recent first)
            sessions.sort(key=lambda s: s.last_accessed, reverse=True)
            return sessions
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to get user sessions from Redis: {e}", operation="get_user_sessions")
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user from Redis."""
        try:
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_tokens = await self.redis_client.smembers(user_sessions_key)
            
            if not session_tokens:
                return 0
            
            # Delete all session keys
            pipe = self.redis_client.pipeline()
            for token in session_tokens:
                session_key = self._get_session_key(token)
                pipe.delete(session_key)
            
            # Delete user sessions set
            pipe.delete(user_sessions_key)
            
            results = await pipe.execute()
            
            # Count successful deletions (excluding the user sessions set deletion)
            return sum(1 for result in results[:-1] if result > 0)
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to delete user sessions from Redis: {e}", operation="delete_user_sessions")
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from Redis."""
        try:
            # Redis automatically expires keys with TTL, but we need to clean up
            # orphaned entries in user session sets
            
            # This is a simplified cleanup - in production, you might want to
            # use Redis SCAN to iterate through keys more efficiently
            
            # For now, we'll rely on Redis TTL for automatic cleanup
            # and clean up orphaned user session sets during get_user_sessions
            
            return 0  # Redis handles expiration automatically
            
        except Exception as e:
            raise DatabaseOperationError(f"Failed to cleanup expired sessions from Redis: {e}", operation="cleanup_sessions")


class MemorySessionBackend:
    """In-memory session storage for development and testing."""
    
    def __init__(self, config: SessionConfig) -> None:
        """Initialize memory session backend."""
        self.config = config
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, set] = {}  # user_id -> set of session_tokens
    
    async def store_session(self, session_data: SessionData) -> None:
        """Store a session in memory."""
        self.sessions[session_data.session_token] = session_data
        
        # Add to user sessions index
        user_id = session_data.user_data.user_id
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_data.session_token)
    
    async def get_session(self, session_token: str) -> Optional[SessionData]:
        """Get a session from memory."""
        session = self.sessions.get(session_token)
        
        # Check if session is expired (but not just inactive)
        if session and self._is_time_expired(session):
            await self.delete_session(session_token)
            return None
        
        return session
    
    def _is_time_expired(self, session: SessionData) -> bool:
        """Check if session is expired based on time only (not active status)."""
        expires_at = session.created_at + timedelta(seconds=session.expires_in)
        return datetime.utcnow() > expires_at
    
    async def update_session(self, session_data: SessionData) -> None:
        """Update a session in memory."""
        if session_data.session_token in self.sessions:
            self.sessions[session_data.session_token] = session_data
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete a session from memory."""
        if session_token in self.sessions:
            session = self.sessions[session_token]
            user_id = session.user_data.user_id
            
            # Remove from sessions
            del self.sessions[session_token]
            
            # Remove from user sessions index
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_token)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            return True
        return False
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user from memory."""
        if user_id not in self.user_sessions:
            return []
        
        user_sessions = []
        expired_tokens = []
        
        for token in list(self.user_sessions[user_id]):
            session = self.sessions.get(token)
            if session and not self._is_time_expired(session):
                user_sessions.append(session)
            else:
                expired_tokens.append(token)
        
        # Clean up expired sessions
        for token in expired_tokens:
            await self.delete_session(token)
        
        # Sort by last accessed time (most recent first)
        user_sessions.sort(key=lambda s: s.last_accessed, reverse=True)
        return user_sessions
    
    async def delete_user_sessions(self, user_id: str) -> int:
        """Delete all sessions for a user from memory."""
        if user_id not in self.user_sessions:
            return 0
        
        tokens_to_delete = list(self.user_sessions[user_id])
        deleted_count = 0
        
        for token in tokens_to_delete:
            if await self.delete_session(token):
                deleted_count += 1
        
        return deleted_count
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from memory."""
        expired_tokens = []
        for token, session in self.sessions.items():
            if self._is_time_expired(session):
                expired_tokens.append(token)
        
        deleted_count = 0
        for token in expired_tokens:
            if await self.delete_session(token):
                deleted_count += 1
        
        return deleted_count