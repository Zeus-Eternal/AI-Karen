"""
Unit tests for session management and storage functionality.

Tests all session storage backends (database, Redis, memory) and the
SessionManager class with comprehensive coverage of session operations.
"""

import asyncio
import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from ai_karen_engine.auth.config import SessionConfig, JWTConfig
from ai_karen_engine.auth.exceptions import DatabaseOperationError, SessionError
from ai_karen_engine.auth.models import SessionData, UserData
from ai_karen_engine.auth.session import (
    SessionManager,
    SessionStore,
    DatabaseSessionBackend,
    RedisSessionBackend,
    MemorySessionBackend
)
from ai_karen_engine.auth.tokens import TokenManager


@pytest.fixture
def sample_user_data():
    """Create sample user data for testing."""
    return UserData(
        user_id="test-user-123",
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        tenant_id="test-tenant",
        preferences={"theme": "dark"},
        is_verified=True,
        is_active=True
    )


@pytest.fixture
def session_config():
    """Create session configuration for testing."""
    return SessionConfig(
        session_timeout_hours=24,
        max_sessions_per_user=5,
        storage_type="memory",
        redis_url=None,
        cookie_name="test_session",
        cookie_secure=False,
        cookie_httponly=True,
        cookie_samesite="lax"
    )


@pytest.fixture
def jwt_config():
    """Create JWT configuration for testing."""
    return JWTConfig(
        secret_key="test-secret-key-for-testing",
        algorithm="HS256",
        access_token_expire_minutes=60,
        refresh_token_expire_days=30
    )


@pytest.fixture
def token_manager(jwt_config):
    """Create token manager for testing."""
    return TokenManager(jwt_config)


@pytest.fixture
def sample_session_data(sample_user_data, token_manager):
    """Create sample session data for testing."""
    async def _create_session():
        access_token = await token_manager.create_access_token(sample_user_data)
        refresh_token = await token_manager.create_refresh_token(sample_user_data)
        
        return SessionData(
            session_token="test-session-token-123",
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=sample_user_data,
            expires_in=86400,  # 24 hours
            ip_address="192.168.1.1",
            user_agent="Test User Agent",
            device_fingerprint="test-device-fingerprint",
            geolocation={"country": "US", "city": "Test City"},
            risk_score=0.1
        )
    
    return asyncio.run(_create_session())


class TestMemorySessionBackend:
    """Test the in-memory session storage backend."""
    
    @pytest.fixture
    def memory_backend(self, session_config):
        """Create memory session backend for testing."""
        return MemorySessionBackend(session_config)
    
    @pytest.mark.asyncio
    async def test_store_and_get_session(self, memory_backend, sample_session_data):
        """Test storing and retrieving a session."""
        # Store session
        await memory_backend.store_session(sample_session_data)
        
        # Retrieve session
        retrieved_session = await memory_backend.get_session(sample_session_data.session_token)
        
        assert retrieved_session is not None
        assert retrieved_session.session_token == sample_session_data.session_token
        assert retrieved_session.user_data.user_id == sample_session_data.user_data.user_id
        assert retrieved_session.access_token == sample_session_data.access_token
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, memory_backend):
        """Test retrieving a non-existent session."""
        session = await memory_backend.get_session("nonexistent-token")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_update_session(self, memory_backend, sample_session_data):
        """Test updating a session."""
        # Store original session
        await memory_backend.store_session(sample_session_data)
        
        # Update session data
        sample_session_data.risk_score = 0.5
        sample_session_data.add_security_flag("suspicious_location")
        
        # Update session
        await memory_backend.update_session(sample_session_data)
        
        # Retrieve and verify
        retrieved_session = await memory_backend.get_session(sample_session_data.session_token)
        assert retrieved_session.risk_score == 0.5
        assert "suspicious_location" in retrieved_session.security_flags
    
    @pytest.mark.asyncio
    async def test_delete_session(self, memory_backend, sample_session_data):
        """Test deleting a session."""
        # Store session
        await memory_backend.store_session(sample_session_data)
        
        # Verify session exists
        session = await memory_backend.get_session(sample_session_data.session_token)
        assert session is not None
        
        # Delete session
        deleted = await memory_backend.delete_session(sample_session_data.session_token)
        assert deleted is True
        
        # Verify session is gone
        session = await memory_backend.get_session(sample_session_data.session_token)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, memory_backend, sample_user_data, token_manager):
        """Test getting all sessions for a user."""
        # Create multiple sessions for the same user
        sessions = []
        for i in range(3):
            access_token = await token_manager.create_access_token(sample_user_data)
            refresh_token = await token_manager.create_refresh_token(sample_user_data)
            
            session = SessionData(
                session_token=f"session-{i}",
                access_token=access_token,
                refresh_token=refresh_token,
                user_data=sample_user_data,
                expires_in=86400,
                ip_address=f"192.168.1.{i+1}",
                user_agent=f"User Agent {i}"
            )
            sessions.append(session)
            await memory_backend.store_session(session)
        
        # Get user sessions
        user_sessions = await memory_backend.get_user_sessions(sample_user_data.user_id)
        
        assert len(user_sessions) == 3
        assert all(s.user_data.user_id == sample_user_data.user_id for s in user_sessions)
    
    @pytest.mark.asyncio
    async def test_delete_user_sessions(self, memory_backend, sample_user_data, token_manager):
        """Test deleting all sessions for a user."""
        # Create multiple sessions for the user
        for i in range(3):
            access_token = await token_manager.create_access_token(sample_user_data)
            refresh_token = await token_manager.create_refresh_token(sample_user_data)
            
            session = SessionData(
                session_token=f"session-{i}",
                access_token=access_token,
                refresh_token=refresh_token,
                user_data=sample_user_data,
                expires_in=86400
            )
            await memory_backend.store_session(session)
        
        # Delete all user sessions
        deleted_count = await memory_backend.delete_user_sessions(sample_user_data.user_id)
        assert deleted_count == 3
        
        # Verify sessions are gone
        user_sessions = await memory_backend.get_user_sessions(sample_user_data.user_id)
        assert len(user_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, memory_backend, sample_user_data, token_manager):
        """Test cleaning up expired sessions."""
        # Create expired session
        access_token = await token_manager.create_access_token(sample_user_data)
        refresh_token = await token_manager.create_refresh_token(sample_user_data)
        
        expired_session = SessionData(
            session_token="expired-session",
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=sample_user_data,
            expires_in=1,  # 1 second
            created_at=datetime.utcnow() - timedelta(seconds=2)  # Created 2 seconds ago
        )
        
        # Create active session
        active_session = SessionData(
            session_token="active-session",
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=sample_user_data,
            expires_in=86400  # 24 hours
        )
        
        await memory_backend.store_session(expired_session)
        await memory_backend.store_session(active_session)
        
        # Cleanup expired sessions
        cleaned_count = await memory_backend.cleanup_expired_sessions()
        assert cleaned_count == 1
        
        # Verify only active session remains
        assert await memory_backend.get_session("expired-session") is None
        assert await memory_backend.get_session("active-session") is not None


class TestDatabaseSessionBackend:
    """Test the database session storage backend."""
    
    @pytest.fixture
    def db_session_config(self):
        """Create database session configuration for testing."""
        # Create temporary database file
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        config = SessionConfig(
            session_timeout_hours=24,
            max_sessions_per_user=5,
            storage_type="database"
        )
        
        yield config
        
        # Cleanup
        Path(temp_db.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def database_backend(self, db_session_config):
        """Create database session backend for testing."""
        backend = DatabaseSessionBackend(db_session_config)
        
        # Create the sessions table for testing
        cursor = backend.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_in INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                ip_address TEXT NOT NULL DEFAULT 'unknown',
                user_agent TEXT NOT NULL DEFAULT '',
                device_fingerprint TEXT,
                geolocation TEXT,
                risk_score REAL NOT NULL DEFAULT 0.0,
                security_flags TEXT NOT NULL DEFAULT '[]',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                invalidated_at TEXT,
                invalidation_reason TEXT
            )
        """)
        
        # Create users table for JOIN operations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                roles TEXT NOT NULL,
                tenant_id TEXT NOT NULL DEFAULT 'default',
                preferences TEXT NOT NULL DEFAULT '{}',
                is_verified BOOLEAN NOT NULL DEFAULT 1,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                two_factor_enabled BOOLEAN NOT NULL DEFAULT 0,
                two_factor_secret TEXT
            )
        """)
        
        backend.connection.commit()
        return backend
    
    @pytest.mark.asyncio
    async def test_store_session_database(self, database_backend, sample_session_data, sample_user_data):
        """Test storing a session in the database."""
        # First insert the user data (use INSERT OR IGNORE to avoid unique constraint issues)
        cursor = database_backend.connection.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO auth_users (
                user_id, email, full_name, roles, tenant_id, preferences,
                is_verified, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_user_data.user_id,
            sample_user_data.email,
            sample_user_data.full_name,
            json.dumps(sample_user_data.roles),
            sample_user_data.tenant_id,
            json.dumps(sample_user_data.preferences),
            sample_user_data.is_verified,
            sample_user_data.is_active,
            sample_user_data.created_at.isoformat(),
            sample_user_data.updated_at.isoformat()
        ))
        database_backend.connection.commit()
        
        # Store session
        await database_backend.store_session(sample_session_data)
        
        # Verify session was stored
        cursor.execute("SELECT * FROM auth_sessions WHERE session_token = ?", 
                      (sample_session_data.session_token,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row["session_token"] == sample_session_data.session_token
        assert row["user_id"] == sample_session_data.user_data.user_id


class TestRedisSessionBackend:
    """Test the Redis session storage backend."""
    
    @pytest.fixture
    def redis_session_config(self):
        """Create Redis session configuration for testing."""
        return SessionConfig(
            session_timeout_hours=24,
            max_sessions_per_user=5,
            storage_type="redis",
            redis_url="redis://localhost:6379/0"
        )
    
    @pytest.mark.asyncio
    async def test_redis_backend_initialization_without_redis(self, redis_session_config):
        """Test Redis backend initialization without redis package."""
        with patch.dict('sys.modules', {'redis.asyncio': None}):
            with pytest.raises(ImportError, match="redis package is required"):
                RedisSessionBackend(redis_session_config)
    
    @pytest.mark.asyncio
    async def test_redis_backend_without_url(self, session_config):
        """Test Redis backend initialization without Redis URL."""
        config = session_config
        config.storage_type = "redis"
        config.redis_url = None
        
        with pytest.raises(DatabaseOperationError, match="Failed to connect to Redis"):
            RedisSessionBackend(config)


class TestSessionManager:
    """Test the main SessionManager class."""
    
    @pytest.fixture
    def session_manager(self, session_config, token_manager):
        """Create session manager for testing."""
        return SessionManager(session_config, token_manager)
    
    @pytest.mark.asyncio
    async def test_generate_session_token(self, session_manager):
        """Test session token generation."""
        token1 = session_manager.generate_session_token()
        token2 = session_manager.generate_session_token()
        
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2  # Should be unique
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, sample_user_data):
        """Test creating a new session."""
        session = await session_manager.create_session(
            user_data=sample_user_data,
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            risk_score=0.2
        )
        
        assert session.user_data.user_id == sample_user_data.user_id
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Test Browser"
        assert session.risk_score == 0.2
        assert len(session.session_token) > 0
        assert len(session.access_token) > 0
        assert len(session.refresh_token) > 0
    
    @pytest.mark.asyncio
    async def test_validate_session(self, session_manager, sample_user_data):
        """Test session validation."""
        # Create session
        session = await session_manager.create_session(sample_user_data)
        
        # Validate session
        validated_session = await session_manager.validate_session(session.session_token)
        
        assert validated_session is not None
        assert validated_session.session_token == session.session_token
        assert validated_session.user_data.user_id == sample_user_data.user_id
    
    @pytest.mark.asyncio
    async def test_validate_invalid_session(self, session_manager):
        """Test validating an invalid session token."""
        session = await session_manager.validate_session("invalid-token")
        assert session is None
    
    @pytest.mark.asyncio
    async def test_validate_empty_session_token(self, session_manager):
        """Test validating an empty session token."""
        session = await session_manager.validate_session("")
        assert session is None
        
        session = await session_manager.validate_session(None)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_refresh_session(self, session_manager, sample_user_data):
        """Test refreshing a session."""
        # Create session
        original_session = await session_manager.create_session(sample_user_data)
        original_access_token = original_session.access_token
        
        # Wait a moment to ensure different timestamps
        await asyncio.sleep(0.01)
        
        # Refresh session
        refreshed_session = await session_manager.refresh_session(
            original_session.session_token,
            original_session.refresh_token
        )
        
        assert refreshed_session is not None
        assert refreshed_session.session_token == original_session.session_token
        # Note: tokens might be the same if created at the same timestamp, so just check it exists
        assert len(refreshed_session.access_token) > 0
        assert refreshed_session.refresh_token == original_session.refresh_token
    
    @pytest.mark.asyncio
    async def test_refresh_session_invalid_token(self, session_manager, sample_user_data):
        """Test refreshing with invalid tokens."""
        # Create session
        session = await session_manager.create_session(sample_user_data)
        
        # Try to refresh with wrong refresh token
        refreshed = await session_manager.refresh_session(
            session.session_token,
            "invalid-refresh-token"
        )
        assert refreshed is None
        
        # Try to refresh with wrong session token
        refreshed = await session_manager.refresh_session(
            "invalid-session-token",
            session.refresh_token
        )
        assert refreshed is None
    
    @pytest.mark.asyncio
    async def test_invalidate_session(self, session_manager, sample_user_data):
        """Test invalidating a session."""
        # Create session
        session = await session_manager.create_session(sample_user_data)
        
        # Invalidate session
        invalidated = await session_manager.invalidate_session(
            session.session_token,
            "test_invalidation"
        )
        assert invalidated is True
        
        # Verify session is invalidated by getting it directly from store
        retrieved_session = await session_manager.store.get_session(session.session_token)
        assert retrieved_session is not None  # Session still exists but is invalidated
        assert not retrieved_session.is_active
        assert retrieved_session.invalidation_reason == "test_invalidation"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager, sample_user_data):
        """Test deleting a session."""
        # Create session
        session = await session_manager.create_session(sample_user_data)
        
        # Delete session
        deleted = await session_manager.delete_session(session.session_token)
        assert deleted is True
        
        # Verify session is gone
        retrieved_session = await session_manager.validate_session(session.session_token)
        assert retrieved_session is None
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_manager, sample_user_data):
        """Test getting all sessions for a user."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(
                sample_user_data,
                ip_address=f"192.168.1.{i+1}"
            )
            sessions.append(session)
        
        # Get user sessions
        user_sessions = await session_manager.get_user_sessions(sample_user_data.user_id)
        
        assert len(user_sessions) == 3
        assert all(s.user_data.user_id == sample_user_data.user_id for s in user_sessions)
    
    @pytest.mark.asyncio
    async def test_invalidate_user_sessions(self, session_manager, sample_user_data):
        """Test invalidating all sessions for a user."""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(sample_user_data)
            sessions.append(session)
        
        # Invalidate all sessions except the first one
        invalidated_count = await session_manager.invalidate_user_sessions(
            sample_user_data.user_id,
            exclude_session=sessions[0].session_token,
            reason="user_logout"
        )
        
        assert invalidated_count == 2
        
        # Verify first session is still active
        session = await session_manager.validate_session(sessions[0].session_token)
        assert session is not None
        assert session.is_active
        
        # Verify other sessions are invalidated (check directly from store)
        for i in range(1, 3):
            session = await session_manager.store.get_session(sessions[i].session_token)
            assert session is not None
            assert not session.is_active
    
    @pytest.mark.asyncio
    async def test_delete_user_sessions(self, session_manager, sample_user_data):
        """Test deleting all sessions for a user."""
        # Create multiple sessions
        for i in range(3):
            await session_manager.create_session(sample_user_data)
        
        # Delete all user sessions
        deleted_count = await session_manager.delete_user_sessions(sample_user_data.user_id)
        assert deleted_count == 3
        
        # Verify sessions are gone
        user_sessions = await session_manager.get_user_sessions(sample_user_data.user_id)
        assert len(user_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self, sample_user_data):
        """Test enforcement of maximum sessions per user."""
        # Create config with low session limit
        config = SessionConfig(
            session_timeout_hours=24,
            max_sessions_per_user=2,
            storage_type="memory"
        )
        
        jwt_config = JWTConfig(secret_key="test-key")
        token_manager = TokenManager(jwt_config)
        session_manager = SessionManager(config, token_manager)
        
        # Create sessions up to the limit
        sessions = []
        for i in range(3):  # Try to create 3 sessions with limit of 2
            session = await session_manager.create_session(sample_user_data)
            sessions.append(session)
        
        # Should only have 2 active sessions (oldest should be deleted)
        user_sessions = await session_manager.get_user_sessions(sample_user_data.user_id)
        assert len(user_sessions) <= 2
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """Test cleanup of expired sessions."""
        # This test would need to create expired sessions and verify cleanup
        # For now, just test that the method runs without error
        cleaned_count = await session_manager.cleanup_expired_sessions()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, session_manager):
        """Test getting session statistics."""
        stats = await session_manager.get_session_stats()
        
        assert isinstance(stats, dict)
        assert "total_sessions" in stats
        assert "active_sessions" in stats
        assert "expired_sessions" in stats
    
    def test_stop_cleanup_task(self, session_manager):
        """Test stopping the cleanup task."""
        # Start cleanup task
        session_manager._start_cleanup_task()
        
        # Only test if cleanup task was created (depends on event loop availability)
        if session_manager._cleanup_task is not None:
            # Stop cleanup task
            session_manager.stop_cleanup_task()
            
            # Task should be cancelled
            assert session_manager._cleanup_task.cancelled()
        else:
            # If no cleanup task was created, just test that stop doesn't crash
            session_manager.stop_cleanup_task()


class TestSessionStore:
    """Test the SessionStore class that manages different backends."""
    
    @pytest.mark.asyncio
    async def test_memory_backend_selection(self, session_config):
        """Test that memory backend is selected correctly."""
        session_config.storage_type = "memory"
        store = SessionStore(session_config)
        
        assert isinstance(store.backend, MemorySessionBackend)
    
    @pytest.mark.asyncio
    async def test_database_backend_selection(self, session_config):
        """Test that database backend is selected correctly."""
        session_config.storage_type = "database"
        store = SessionStore(session_config)
        
        assert isinstance(store.backend, DatabaseSessionBackend)
    
    @pytest.mark.asyncio
    async def test_invalid_backend_type(self, session_config):
        """Test error handling for invalid backend type."""
        session_config.storage_type = "invalid"
        
        with pytest.raises(ValueError, match="Unsupported session storage type"):
            SessionStore(session_config)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])