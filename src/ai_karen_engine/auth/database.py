"""
Unified PostgreSQL database client for the consolidated authentication service.

This module provides database operations for user data storage and retrieval,
session management, and audit logging using PostgreSQL exclusively.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

try:
    from sqlalchemy import create_engine, text
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

from .config import DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseOperationError
from .models import AuthEvent, UserData


class AuthDatabaseClient:
    """
    Unified PostgreSQL database client for authentication operations.

    This client exclusively uses PostgreSQL for all authentication data,
    replacing the previous dual SQLite/PostgreSQL architecture.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize PostgreSQL database client with configuration."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AuthDatabaseClient")

        if not create_async_engine:
            raise DatabaseConnectionError(
                "SQLAlchemy is required for PostgreSQL operations. "
                "Please install with: pip install sqlalchemy[asyncio] asyncpg"
            )

        # Create async engine for PostgreSQL
        self.engine = create_async_engine(
            config.database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=config.connection_pool_size,
            max_overflow=config.connection_pool_max_overflow,
            pool_timeout=config.connection_timeout_seconds,
            echo=config.enable_query_logging,
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Track whether the database schema has been initialized
        self._schema_initialized = False

        self.logger.info("PostgreSQL AuthDatabaseClient initialized")

    async def _ensure_schema(self) -> None:
        """Ensure database schema is initialized before operations."""
        if not self._schema_initialized:
            await self.initialize_schema()

    async def initialize_schema(self) -> None:
        """Initialize PostgreSQL schema with authentication tables."""
        try:
            async with self.engine.begin() as conn:
                try:
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
                except Exception as e:
                    self.logger.warning(
                        "Failed to create pgcrypto extension: %s", e
                    )

                # Create users table
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

                # Create sessions table
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

                # Create authentication providers table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_providers (
                        provider_id VARCHAR(255) PRIMARY KEY,
                        tenant_id UUID,
                        type VARCHAR(100) NOT NULL,
                        config JSONB NOT NULL,
                        metadata JSONB DEFAULT '{}'::jsonb,
                        enabled BOOLEAN DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """
                    )
                )

                # Create user identities table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS user_identities (
                        identity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
                        provider_id VARCHAR(255) NOT NULL REFERENCES auth_providers(provider_id),
                        provider_user VARCHAR(255) NOT NULL,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE (provider_id, provider_user)
                    )
                """
                    )
                )

                # Create password reset tokens table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_password_reset_tokens (
                        token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
                        token_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        used_at TIMESTAMP WITH TIME ZONE,
                        ip_address INET,
                        user_agent TEXT
                    )
                """
                    )
                )

                # Create email verification tokens table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_email_verification_tokens (
                        token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id UUID NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,
                        token_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        used_at TIMESTAMP WITH TIME ZONE,
                        ip_address INET,
                        user_agent TEXT
                    )
                """
                    )
                )

                # Create auth events table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS auth_events (
                        event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        event_type VARCHAR(100) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        user_id UUID,
                        email VARCHAR(255),
                        tenant_id UUID,
                        ip_address INET,
                        user_agent TEXT,
                        request_id VARCHAR(255),
                        session_token VARCHAR(255),
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        details JSONB DEFAULT '{}'::jsonb,
                        risk_score FLOAT DEFAULT 0.0,
                        security_flags JSONB DEFAULT '[]'::jsonb,
                        blocked_by_security BOOLEAN DEFAULT false,
                        processing_time_ms FLOAT DEFAULT 0.0,
                        service_version VARCHAR(100) DEFAULT 'consolidated-auth-v1'
                    )
                """
                    )
                )

                # Create indexes
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users(tenant_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions(is_active) WHERE is_active = true"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_user_identities_user ON user_identities(user_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_user ON auth_password_reset_tokens(user_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_expires ON auth_password_reset_tokens(expires_at)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_user ON auth_email_verification_tokens(user_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_expires ON auth_email_verification_tokens(expires_at)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events(user_id)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type)"
                    )
                )
                await conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events(timestamp)"
                    )
                )

            self._schema_initialized = True
            self.logger.info("PostgreSQL schema initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize schema: {e}")
            raise DatabaseConnectionError(f"Schema initialization failed: {e}")

    async def create_user(self, user_data: UserData, password_hash: str) -> None:
        """Create a new user with password hash in PostgreSQL."""
        try:
            async with self.session_factory() as session:
                # Insert user data
                await session.execute(
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

                # Insert password hash
                await session.execute(
                    text(
                        """
                    INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                    VALUES (:user_id, :password_hash, :created_at, :updated_at)
                """
                    ),
                    {
                        "user_id": user_data.user_id,
                        "password_hash": password_hash,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )

                await session.commit()

        except IntegrityError as e:
            if "duplicate key" in str(e).lower():
                raise DatabaseOperationError(
                    "User already exists", operation="create_user"
                )
            raise DatabaseOperationError(
                f"Database integrity error: {e}", operation="create_user"
            )
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to create user: {e}", operation="create_user"
            )

    async def get_user_by_id(self, user_id: str) -> Optional[UserData]:
        """Get user data by user ID from PostgreSQL."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT * FROM auth_users WHERE user_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )

                row = result.fetchone()
                if not row:
                    return None

                return self._row_to_user_data(row)

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user by ID: {e}", operation="get_user"
            )

    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user data by email address from PostgreSQL."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT * FROM auth_users WHERE email = :email
                """
                    ),
                    {"email": email},
                )

                row = result.fetchone()
                if not row:
                    return None

                return self._row_to_user_data(row)

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user by email: {e}", operation="get_user"
            )

    async def update_user(self, user_data: UserData) -> None:
        """Update user data in PostgreSQL."""
        try:
            async with self.session_factory() as session:
                await session.execute(
                    text(
                        """
                    UPDATE auth_users SET
                        email = :email, full_name = :full_name, roles = :roles,
                        tenant_id = :tenant_id, preferences = :preferences,
                        is_verified = :is_verified, is_active = :is_active,
                        updated_at = :updated_at, last_login_at = :last_login_at,
                        failed_login_attempts = :failed_login_attempts,
                        locked_until = :locked_until, two_factor_enabled = :two_factor_enabled,
                        two_factor_secret = :two_factor_secret
                    WHERE user_id = :user_id
                """
                    ),
                    {
                        "email": user_data.email,
                        "full_name": user_data.full_name,
                        "roles": json.dumps(user_data.roles),
                        "tenant_id": user_data.tenant_id,
                        "preferences": json.dumps(user_data.preferences),
                        "is_verified": user_data.is_verified,
                        "is_active": user_data.is_active,
                        "updated_at": user_data.updated_at,
                        "last_login_at": user_data.last_login_at,
                        "failed_login_attempts": user_data.failed_login_attempts,
                        "locked_until": user_data.locked_until,
                        "two_factor_enabled": user_data.two_factor_enabled,
                        "two_factor_secret": user_data.two_factor_secret,
                        "user_id": user_data.user_id,
                    },
                )

                await session.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to update user: {e}", operation="update_user"
            )

    async def get_user_password_hash(self, user_id: str) -> Optional[str]:
        """Get password hash for a user from PostgreSQL."""
        try:
            async with self.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT password_hash FROM auth_password_hashes WHERE user_id = :user_id
                """
                    ),
                    {"user_id": user_id},
                )

                row = result.fetchone()
                return row.password_hash if row else None

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get password hash: {e}", operation="get_password_hash"
            )

    async def update_user_password_hash(self, user_id: str, password_hash: str) -> None:
        """Update password hash for a user in PostgreSQL."""
        try:
            async with self.session_factory() as session:
                await session.execute(
                    text(
                        """
                    UPDATE auth_password_hashes
                    SET password_hash = :password_hash, updated_at = :updated_at
                    WHERE user_id = :user_id
                """
                    ),
                    {
                        "password_hash": password_hash,
                        "updated_at": datetime.utcnow(),
                        "user_id": user_id,
                    },
                )

                await session.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to update password hash: {e}", operation="update_password_hash"
            )

    async def store_auth_event(self, event: AuthEvent) -> None:
        """Store authentication event in PostgreSQL."""
        try:
            await self._ensure_schema()
            async with self.session_factory() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO auth_events (
                        event_id, event_type, timestamp, user_id, email, tenant_id,
                        ip_address, user_agent, request_id, session_token, success,
                        error_message, details, risk_score, security_flags,
                        blocked_by_security, processing_time_ms, service_version
                    ) VALUES (
                        :event_id, :event_type, :timestamp, :user_id, :email, :tenant_id,
                        :ip_address, :user_agent, :request_id, :session_token, :success,
                        :error_message, :details, :risk_score, :security_flags,
                        :blocked_by_security, :processing_time_ms, :service_version
                    )
                """
                    ),
                    {
                        "event_id": str(uuid4()),
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp,
                        "user_id": event.user_id,
                        "email": event.email,
                        "tenant_id": event.tenant_id,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "request_id": event.request_id,
                        "session_token": event.session_token,
                        "success": event.success,
                        "error_message": event.error_message,
                        "details": json.dumps(event.details),
                        "risk_score": event.risk_score,
                        "security_flags": json.dumps(event.security_flags),
                        "blocked_by_security": event.blocked_by_security,
                        "processing_time_ms": event.processing_time_ms,
                        "service_version": event.service_version,
                    },
                )

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to store auth event: {e}")
            # Don't raise exception for audit logging failures

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
            self.logger.info("PostgreSQL connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")


# Maintain backward compatibility
DatabaseClient = AuthDatabaseClient
