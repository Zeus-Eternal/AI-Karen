"""
PostgreSQL-optimized database client for authentication operations.

This module provides high-performance database operations specifically optimized
for PostgreSQL, including UPSERT operations, JSONB queries, and efficient
indexing strategies.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

try:
    from sqlalchemy import create_engine, func, text
    from sqlalchemy.dialects.postgresql import insert
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.pool import AsyncAdaptedQueuePool
except ImportError:
    # Fallback for environments without SQLAlchemy
    create_engine = None
    create_async_engine = None
    AsyncSession = None
    async_sessionmaker = None
    IntegrityError = Exception
    SQLAlchemyError = Exception
    AsyncAdaptedQueuePool = None
    text = None
    func = None
    insert = None

from .config import DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseOperationError
from .models import AuthEvent, SessionData, UserData


class OptimizedAuthDatabaseClient:
    """
    PostgreSQL-optimized database client for authentication operations.

    This client provides high-performance operations using PostgreSQL-specific
    features like UPSERT, JSONB queries, partial indexes, and connection pooling.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize optimized PostgreSQL database client."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.OptimizedAuthDatabaseClient")

        if not create_async_engine:
            raise DatabaseConnectionError(
                "SQLAlchemy is required for PostgreSQL operations. "
                "Please install with: pip install sqlalchemy[asyncio] asyncpg"
            )

        # Create async engine with optimized settings
        self.engine = create_async_engine(
            config.database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=config.connection_pool_size,
            max_overflow=config.connection_pool_max_overflow,
            pool_timeout=config.connection_timeout_seconds,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,  # Recycle connections every hour
            echo=config.enable_query_logging,
            # PostgreSQL-specific optimizations
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for faster connection times
                    "application_name": "ai_karen_auth",
                }
            },
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self.logger.info("Optimized PostgreSQL AuthDatabaseClient initialized")

    async def initialize_optimized_schema(self) -> None:
        """Initialize PostgreSQL schema with performance optimizations."""
        try:
            async with self.engine.begin() as conn:
                # Create optimized users table with JSONB and partial indexes
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_users (
                        user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE NOT NULL,
                        full_name VARCHAR(255),
                        roles JSONB DEFAULT '[]'::jsonb,
                        tenant_id UUID NOT NULL,
                        preferences JSONB DEFAULT '{}'::jsonb,
                        is_verified BOOLEAN DEFAULT false,
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_login_at TIMESTAMP WITH TIME ZONE,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP WITH TIME ZONE,
                        two_factor_enabled BOOLEAN DEFAULT false,
                        two_factor_secret VARCHAR(255)
                    )
                """
                    )
                )

                # Create optimized sessions table with proper foreign keys
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        session_token VARCHAR(255) PRIMARY KEY,
                        user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT NOT NULL,
                        expires_in INTEGER NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        ip_address INET,
                        user_agent TEXT,
                        device_fingerprint VARCHAR(255),
                        geolocation JSONB,
                        risk_score FLOAT DEFAULT 0.0,
                        security_flags JSONB DEFAULT '[]'::jsonb,
                        is_active BOOLEAN DEFAULT true,
                        invalidated_at TIMESTAMP WITH TIME ZONE,
                        invalidation_reason VARCHAR(255)
                    )
                """
                    )
                )

                # Create password hashes table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_password_hashes (
                        user_id UUID PRIMARY KEY REFERENCES auth_users(user_id) ON DELETE CASCADE,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """
                    )
                )

                # Create optimized indexes for performance
                await self._create_optimized_indexes(conn)

            self.logger.info("Optimized PostgreSQL schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize optimized schema: {e}")
            raise DatabaseConnectionError(f"Schema initialization failed: {e}")

    async def initialize_schema(self) -> None:
        """Compatibility wrapper for standardized schema initialization."""
        await self.initialize_optimized_schema()

    async def _create_optimized_indexes(self, conn) -> None:
        """Create optimized indexes for PostgreSQL performance."""
        indexes = [
            # Primary lookup indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_email_active ON auth_users(email) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_tenant_active ON auth_users(tenant_id) WHERE is_active = true",
            # JSONB indexes for role-based queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_roles_gin ON auth_users USING GIN (roles)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_preferences_gin ON auth_users USING GIN (preferences)",
            # Session indexes with partial conditions
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_user_active ON auth_sessions(user_id) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_token_active ON auth_sessions(session_token) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(created_at, expires_in) WHERE is_active = true",
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_user_created ON auth_sessions(user_id, created_at DESC) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_tenant_email ON auth_users(tenant_id, email) WHERE is_active = true",
            # Security-focused indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_users_locked ON auth_users(locked_until) WHERE locked_until IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_sessions_risk_score ON auth_sessions(risk_score DESC) WHERE is_active = true AND risk_score > 0.5",
        ]

        for index_sql in indexes:
            try:
                await conn.execute(text(index_sql))
            except Exception as e:
                # Log but don't fail on index creation errors (might already exist)
                self.logger.warning(f"Index creation warning: {e}")

    async def upsert_user(self, user_data: UserData, password_hash: str) -> UserData:
        """
        Upsert user data using PostgreSQL's ON CONFLICT feature.

        This provides atomic user creation/update operations with optimal performance.
        """
        try:
            async with self.session_factory() as session:
                # Use PostgreSQL UPSERT for atomic operation
                result = await session.execute(
                    text(
                        """
                    INSERT INTO auth_users (
                        user_id, email, full_name, roles, tenant_id, preferences,
                        is_verified, is_active, created_at, updated_at, last_login_at,
                        failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
                    ) VALUES (
                        :user_id, :email, :full_name, :roles, :tenant_id, :preferences,
                        :is_verified, :is_active, :created_at, :updated_at, :last_login_at,
                        :failed_login_attempts, :locked_until, :two_factor_enabled, :two_factor_secret
                    )
                    ON CONFLICT (email) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        roles = EXCLUDED.roles,
                        preferences = EXCLUDED.preferences,
                        is_verified = EXCLUDED.is_verified,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at,
                        last_login_at = EXCLUDED.last_login_at,
                        failed_login_attempts = EXCLUDED.failed_login_attempts,
                        locked_until = EXCLUDED.locked_until,
                        two_factor_enabled = EXCLUDED.two_factor_enabled,
                        two_factor_secret = EXCLUDED.two_factor_secret
                    RETURNING user_id, email, created_at
                """
                    ),
                    {
                        "user_id": user_data.user_id,
                        "email": user_data.email,
                        "full_name": user_data.full_name,
                        "roles": json.dumps(user_data.roles),
                        "tenant_id": user_data.tenant_id,
                        "preferences": json.dumps(user_data.preferences),
                        "is_verified": user_data.is_verified,
                        "is_active": user_data.is_active,
                        "created_at": user_data.created_at,
                        "updated_at": user_data.updated_at,
                        "last_login_at": user_data.last_login_at,
                        "failed_login_attempts": user_data.failed_login_attempts,
                        "locked_until": user_data.locked_until,
                        "two_factor_enabled": user_data.two_factor_enabled,
                        "two_factor_secret": user_data.two_factor_secret,
                    },
                )

                user_result = result.fetchone()
                if not user_result:
                    raise DatabaseOperationError(
                        "Failed to upsert user", operation="upsert_user"
                    )

                # Upsert password hash
                await session.execute(
                    text(
                        """
                    INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                    VALUES (:user_id, :password_hash, :created_at, :updated_at)
                    ON CONFLICT (user_id) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        updated_at = EXCLUDED.updated_at
                """
                    ),
                    {
                        "user_id": user_result.user_id,
                        "password_hash": password_hash,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )

                await session.commit()

                # Update user_data with actual database values
                user_data.user_id = str(user_result.user_id)
                user_data.created_at = user_result.created_at

                return user_data

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to upsert user: {e}", operation="upsert_user"
            )

    async def get_user_with_roles(
        self, email: str, required_roles: List[str]
    ) -> Optional[UserData]:
        """
        Get user by email with role filtering using JSONB queries.

        This uses PostgreSQL's JSONB operators for efficient role-based lookups.
        """
        try:
            async with self.session_factory() as session:
                # Use JSONB containment operator for efficient role checking
                result = await session.execute(
                    text(
                        """
                    SELECT * FROM auth_users
                    WHERE email = :email
                    AND is_active = true
                    AND roles @> :required_roles::jsonb
                """
                    ),
                    {"email": email, "required_roles": json.dumps(required_roles)},
                )

                row = result.fetchone()
                if not row:
                    return None

                return self._row_to_user_data(row)

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user with roles: {e}", operation="get_user_with_roles"
            )

    async def bulk_update_user_preferences(
        self, updates: List[Tuple[str, Dict[str, Any]]]
    ) -> int:
        """
        Bulk update user preferences using PostgreSQL's JSONB merge operations.

        Args:
            updates: List of (user_id, preferences_dict) tuples

        Returns:
            Number of users updated
        """
        try:
            async with self.session_factory() as session:
                updated_count = 0

                for user_id, preferences in updates:
                    result = await session.execute(
                        text(
                            """
                        UPDATE auth_users
                        SET preferences = preferences || :new_preferences::jsonb,
                            updated_at = NOW()
                        WHERE user_id = :user_id AND is_active = true
                    """
                        ),
                        {
                            "user_id": user_id,
                            "new_preferences": json.dumps(preferences),
                        },
                    )

                    updated_count += result.rowcount

                await session.commit()
                return updated_count

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to bulk update preferences: {e}",
                operation="bulk_update_preferences",
            )

    async def create_session_optimized(self, session_data: SessionData) -> None:
        """
        Create session with optimized PostgreSQL operations.

        This includes automatic cleanup of expired sessions and efficient storage.
        """
        try:
            async with self.session_factory() as session:
                # Clean up expired sessions for this user first (maintenance)
                await session.execute(
                    text(
                        """
                    UPDATE auth_sessions
                    SET is_active = false,
                        invalidated_at = NOW(),
                        invalidation_reason = 'expired'
                    WHERE user_id = :user_id
                    AND is_active = true
                    AND (created_at + INTERVAL '1 second' * expires_in) < NOW()
                """
                    ),
                    {"user_id": session_data.user_data.user_id},
                )

                # Insert new session
                await session.execute(
                    text(
                        """
                    INSERT INTO auth_sessions (
                        session_token, user_id, access_token, refresh_token, expires_in,
                        created_at, last_accessed, ip_address, user_agent, device_fingerprint,
                        geolocation, risk_score, security_flags, is_active
                    ) VALUES (
                        :session_token, :user_id, :access_token, :refresh_token, :expires_in,
                        :created_at, :last_accessed, :ip_address, :user_agent, :device_fingerprint,
                        :geolocation, :risk_score, :security_flags, :is_active
                    )
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
                    },
                )

                await session.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to create optimized session: {e}",
                operation="create_session_optimized",
            )

    async def validate_session_with_user(
        self, session_token: str
    ) -> Optional[Tuple[SessionData, UserData]]:
        """
        Validate session and return both session and user data in a single query.

        This uses JOIN operations for optimal performance.
        """
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT
                        s.session_token, s.access_token, s.refresh_token, s.expires_in,
                        s.created_at as session_created, s.last_accessed, s.ip_address,
                        s.user_agent, s.device_fingerprint, s.geolocation, s.risk_score,
                        s.security_flags, s.is_active as session_active,
                        u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
                        u.is_verified, u.is_active as user_active, u.created_at as user_created,
                        u.updated_at, u.last_login_at, u.failed_login_attempts, u.locked_until,
                        u.two_factor_enabled, u.two_factor_secret
                    FROM auth_sessions s
                    JOIN auth_users u ON s.user_id = u.user_id
                    WHERE s.session_token = :session_token
                    AND s.is_active = true
                    AND u.is_active = true
                    AND (s.created_at + INTERVAL '1 second' * s.expires_in) > NOW()
                """
                    ),
                    {"session_token": session_token},
                )

                row = result.fetchone()
                if not row:
                    return None

                # Update last accessed time
                await session.execute(
                    text(
                        """
                    UPDATE auth_sessions
                    SET last_accessed = NOW()
                    WHERE session_token = :session_token
                """
                    ),
                    {"session_token": session_token},
                )

                await session.commit()

                # Build session data
                session_data = SessionData(
                    session_token=row.session_token,
                    access_token=row.access_token,
                    refresh_token=row.refresh_token,
                    expires_in=row.expires_in,
                    created_at=row.session_created,
                    last_accessed=row.last_accessed,
                    ip_address=row.ip_address or "unknown",
                    user_agent=row.user_agent or "",
                    device_fingerprint=row.device_fingerprint,
                    geolocation=json.loads(row.geolocation)
                    if row.geolocation
                    else None,
                    risk_score=row.risk_score,
                    security_flags=json.loads(row.security_flags)
                    if row.security_flags
                    else [],
                    is_active=row.session_active,
                    user_data=UserData(
                        user_id=str(row.user_id),
                        email=row.email,
                        full_name=row.full_name,
                        roles=json.loads(row.roles) if row.roles else [],
                        tenant_id=str(row.tenant_id),
                        preferences=json.loads(row.preferences)
                        if row.preferences
                        else {},
                        is_verified=row.is_verified,
                        is_active=row.user_active,
                        created_at=row.user_created,
                        updated_at=row.updated_at,
                        last_login_at=row.last_login_at,
                        failed_login_attempts=row.failed_login_attempts,
                        locked_until=row.locked_until,
                        two_factor_enabled=row.two_factor_enabled,
                        two_factor_secret=row.two_factor_secret,
                    ),
                )

                return session_data, session_data.user_data

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to validate session with user: {e}",
                operation="validate_session_with_user",
            )

    async def cleanup_expired_sessions(self, batch_size: int = 1000) -> int:
        """
        Efficiently clean up expired sessions using batch operations.

        Returns:
            Number of sessions cleaned up
        """
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    UPDATE auth_sessions
                    SET is_active = false,
                        invalidated_at = NOW(),
                        invalidation_reason = 'expired'
                    WHERE is_active = true
                    AND (created_at + INTERVAL '1 second' * expires_in) < NOW()
                    AND session_token IN (
                        SELECT session_token FROM auth_sessions
                        WHERE is_active = true
                        AND (created_at + INTERVAL '1 second' * expires_in) < NOW()
                        LIMIT :batch_size
                    )
                """
                    ),
                    {"batch_size": batch_size},
                )

                await session.commit()
                return result.rowcount

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    async def get_user_sessions_count(self, user_id: str) -> int:
        """Get count of active sessions for a user."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) as session_count
                    FROM auth_sessions
                    WHERE user_id = :user_id
                    AND is_active = true
                    AND (created_at + INTERVAL '1 second' * expires_in) > NOW()
                """
                    ),
                    {"user_id": user_id},
                )

                row = result.fetchone()
                return row.session_count if row else 0

        except Exception as e:
            self.logger.error(f"Failed to get user sessions count: {e}")
            return 0

    async def get_authentication_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get authentication statistics using PostgreSQL aggregation functions.

        Returns comprehensive stats for monitoring and analytics.
        """
        try:
            async with self.session_factory() as session:
                # Get user stats
                user_result = await session.execute(
                    text(
                        """
                    SELECT
                        COUNT(*) as total_users,
                        COUNT(*) FILTER (WHERE is_active = true) as active_users,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL ':hours hours') as new_users,
                        COUNT(*) FILTER (WHERE locked_until IS NOT NULL AND locked_until > NOW()) as locked_users
                    FROM auth_users
                """
                    ),
                    {"hours": hours},
                )

                # Get session stats
                session_result = await session.execute(
                    text(
                        """
                    SELECT
                        COUNT(*) as total_sessions,
                        COUNT(*) FILTER (WHERE is_active = true) as active_sessions,
                        COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL ':hours hours') as recent_sessions,
                        AVG(risk_score) as avg_risk_score,
                        MAX(risk_score) as max_risk_score
                    FROM auth_sessions
                    WHERE created_at > NOW() - INTERVAL ':hours hours'
                """
                    ),
                    {"hours": hours},
                )

                user_stats = user_result.fetchone()
                session_stats = session_result.fetchone()

                return {
                    "users": {
                        "total": user_stats.total_users,
                        "active": user_stats.active_users,
                        "new_in_period": user_stats.new_users,
                        "locked": user_stats.locked_users,
                    },
                    "sessions": {
                        "total": session_stats.total_sessions,
                        "active": session_stats.active_sessions,
                        "recent": session_stats.recent_sessions,
                        "avg_risk_score": float(session_stats.avg_risk_score or 0),
                        "max_risk_score": float(session_stats.max_risk_score or 0),
                    },
                    "period_hours": hours,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Failed to get authentication stats: {e}")
            return {}

    def _row_to_user_data(self, row) -> UserData:
        """Convert database row to UserData object."""
        return UserData(
            user_id=str(row.user_id),
            email=row.email,
            full_name=row.full_name,
            roles=json.loads(row.roles) if row.roles else [],
            tenant_id=str(row.tenant_id),
            preferences=json.loads(row.preferences) if row.preferences else {},
            is_verified=row.is_verified,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_login_at=row.last_login_at,
            failed_login_attempts=row.failed_login_attempts,
            locked_until=row.locked_until,
            two_factor_enabled=row.two_factor_enabled,
            two_factor_secret=row.two_factor_secret,
        )

    async def close(self) -> None:
        """Close database connections."""
        try:
            await self.engine.dispose()
            self.logger.info("Optimized PostgreSQL connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
