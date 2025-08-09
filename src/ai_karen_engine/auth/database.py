"""
Database client for the consolidated authentication service.

This module provides database operations for user data storage and retrieval,
session management, and audit logging.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from uuid import uuid4

from .config import DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseOperationError
from .models import AuthEvent, UserData


class DatabaseClient:
    """
    Database client for authentication operations.

    Supports SQLite for development and can be extended for PostgreSQL
    and other databases in production.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize database client with configuration."""
        self.config = config
        self.connection: Optional[sqlite3.Connection] = None
        self._setup_database()

    def _setup_database(self) -> None:
        """Set up database connection and create tables if needed."""
        try:
            # Parse database URL
            parsed = urlparse(self.config.database_url)

            if parsed.scheme == "sqlite":
                # Extract path from URL (remove leading slash for relative paths)
                db_path = (
                    parsed.path.lstrip("/")
                    if parsed.path.startswith("/")
                    else parsed.path
                )

                # Create directory if it doesn't exist
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

                # Connect to SQLite database
                self.connection = sqlite3.connect(
                    db_path,
                    timeout=self.config.connection_timeout_seconds,
                    check_same_thread=False,
                )
                self.connection.row_factory = sqlite3.Row

                # Create tables
                self._create_tables()
            else:
                raise DatabaseConnectionError(
                    f"Unsupported database scheme: {parsed.scheme}"
                )

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            cursor = self.connection.cursor()

            # Users table
            cursor.execute(
                """
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
            """
            )

            # Password hashes table (separate for security)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_password_hashes (
                    user_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_id TEXT PRIMARY KEY,
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
                    invalidation_reason TEXT,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Authentication providers
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_providers (
                    provider_id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )

            # External user identities
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_identities (
                    identity_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    provider_user TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (provider_id) REFERENCES auth_providers (provider_id),
                    UNIQUE (provider_id, provider_user)
                )
            """
            )

            # Password reset tokens table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_password_reset_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    ip_address TEXT NOT NULL DEFAULT 'unknown',
                    user_agent TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Email verification tokens table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_email_verification_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    ip_address TEXT NOT NULL DEFAULT 'unknown',
                    user_agent TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Auth events table for audit logging
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    email TEXT,
                    tenant_id TEXT,
                    ip_address TEXT NOT NULL DEFAULT 'unknown',
                    user_agent TEXT NOT NULL DEFAULT '',
                    request_id TEXT,
                    session_id TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    risk_score REAL NOT NULL DEFAULT 0.0,
                    security_flags TEXT NOT NULL DEFAULT '[]',
                    blocked_by_security BOOLEAN NOT NULL DEFAULT 0,
                    processing_time_ms REAL NOT NULL DEFAULT 0.0,
                    service_version TEXT NOT NULL DEFAULT 'consolidated-auth-v1'
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users (email)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users (tenant_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions (user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions (is_active)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_identity_user ON user_identities (user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_user ON auth_password_reset_tokens (user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_password_reset_tokens_expires ON auth_password_reset_tokens (expires_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_user ON auth_email_verification_tokens (user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_email_verification_tokens_expires ON auth_email_verification_tokens (expires_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events (user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events (event_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events (timestamp)"
            )

            self.connection.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to create tables: {e}", operation="create_tables"
            )

    async def create_user(self, user_data: UserData, password_hash: str) -> None:
        """Create a new user with password hash."""
        try:
            cursor = self.connection.cursor()

            # Insert user data
            cursor.execute(
                """
                INSERT INTO auth_users (
                    user_id, email, full_name, roles, tenant_id, preferences,
                    is_verified, is_active, created_at, updated_at, last_login_at,
                    failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_data.user_id,
                    user_data.email,
                    user_data.full_name,
                    json.dumps(user_data.roles),
                    user_data.tenant_id,
                    json.dumps(user_data.preferences),
                    user_data.is_verified,
                    user_data.is_active,
                    user_data.created_at.isoformat(),
                    user_data.updated_at.isoformat(),
                    user_data.last_login_at.isoformat()
                    if user_data.last_login_at
                    else None,
                    user_data.failed_login_attempts,
                    user_data.locked_until.isoformat()
                    if user_data.locked_until
                    else None,
                    user_data.two_factor_enabled,
                    user_data.two_factor_secret,
                ),
            )

            # Insert password hash
            cursor.execute(
                """
                INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    user_data.user_id,
                    password_hash,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )

            self.connection.commit()

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise DatabaseOperationError(
                    "User already exists", operation="create_user"
                )
            raise DatabaseOperationError(
                f"Database integrity error: {e}", operation="create_user"
            )
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to create user: {e}", operation="create_user"
            )

    async def get_user_by_id(self, user_id: str) -> Optional[UserData]:
        """Get user data by user ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM auth_users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_user_data(row)

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user by ID: {e}", operation="get_user"
            )

    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user data by email address."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM auth_users WHERE email = ?", (email,))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_user_data(row)

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user by email: {e}", operation="get_user"
            )

    async def update_user(self, user_data: UserData) -> None:
        """Update user data."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE auth_users SET
                    email = ?, full_name = ?, roles = ?, tenant_id = ?, preferences = ?,
                    is_verified = ?, is_active = ?, updated_at = ?, last_login_at = ?,
                    failed_login_attempts = ?, locked_until = ?, two_factor_enabled = ?,
                    two_factor_secret = ?
                WHERE user_id = ?
            """,
                (
                    user_data.email,
                    user_data.full_name,
                    json.dumps(user_data.roles),
                    user_data.tenant_id,
                    json.dumps(user_data.preferences),
                    user_data.is_verified,
                    user_data.is_active,
                    user_data.updated_at.isoformat(),
                    user_data.last_login_at.isoformat()
                    if user_data.last_login_at
                    else None,
                    user_data.failed_login_attempts,
                    user_data.locked_until.isoformat()
                    if user_data.locked_until
                    else None,
                    user_data.two_factor_enabled,
                    user_data.two_factor_secret,
                    user_data.user_id,
                ),
            )

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to update user: {e}", operation="update_user"
            )

    async def get_user_password_hash(self, user_id: str) -> Optional[str]:
        """Get password hash for a user."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT password_hash FROM auth_password_hashes WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()

            return row["password_hash"] if row else None

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get password hash: {e}", operation="get_password_hash"
            )

    async def update_user_password_hash(self, user_id: str, password_hash: str) -> None:
        """Update password hash for a user."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE auth_password_hashes SET password_hash = ?, updated_at = ?
                WHERE user_id = ?
            """,
                (password_hash, datetime.utcnow().isoformat(), user_id),
            )

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to update password hash: {e}", operation="update_password_hash"
            )

    async def get_auth_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Fetch authentication provider configuration."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM auth_providers WHERE provider_id = ?", (provider_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "provider_id": row["provider_id"],
                "tenant_id": row["tenant_id"],
                "type": row["type"],
                "config": json.loads(row["config"]),
                "metadata": json.loads(row["metadata"]),
                "enabled": bool(row["enabled"]),
                "created_at": datetime.fromisoformat(row["created_at"]),
                "updated_at": datetime.fromisoformat(row["updated_at"]),
            }
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get auth provider: {e}", operation="get_auth_provider"
            )

    async def upsert_auth_provider(
        self,
        provider_id: str,
        provider_type: str,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: str = "default",
        enabled: bool = True,
    ) -> None:
        """Insert or update an authentication provider."""
        try:
            cursor = self.connection.cursor()
            now = datetime.utcnow().isoformat()
            cursor.execute(
                """
                INSERT INTO auth_providers (
                    provider_id, tenant_id, type, config, metadata, enabled, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_id) DO UPDATE SET
                    tenant_id=excluded.tenant_id,
                    type=excluded.type,
                    config=excluded.config,
                    metadata=excluded.metadata,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
                """,
                (
                    provider_id,
                    tenant_id,
                    provider_type,
                    json.dumps(config),
                    json.dumps(metadata or {}),
                    enabled,
                    now,
                    now,
                ),
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to upsert auth provider: {e}", operation="upsert_auth_provider"
            )

    async def get_user_identity(
        self, provider_id: str, provider_user: str
    ) -> Optional[Dict[str, Any]]:
        """Get a user identity mapping for a provider."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM user_identities WHERE provider_id = ? AND provider_user = ?",
                (provider_id, provider_user),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "identity_id": row["identity_id"],
                "user_id": row["user_id"],
                "provider_id": row["provider_id"],
                "provider_user": row["provider_user"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": datetime.fromisoformat(row["created_at"]),
            }
        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get user identity: {e}", operation="get_user_identity"
            )

    async def link_user_identity(
        self,
        user_id: str,
        provider_id: str,
        provider_user: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a mapping between user and external provider identity."""
        try:
            existing = await self.get_user_identity(provider_id, provider_user)
            cursor = self.connection.cursor()
            if existing:
                cursor.execute(
                    "UPDATE user_identities SET user_id = ?, metadata = ? WHERE identity_id = ?",
                    (
                        user_id,
                        json.dumps(metadata or existing["metadata"]),
                        existing["identity_id"],
                    ),
                )
                self.connection.commit()
                existing["user_id"] = user_id
                existing["metadata"] = metadata or existing["metadata"]
                return existing

            identity_id = str(uuid4())
            cursor.execute(
                """
                INSERT INTO user_identities (
                    identity_id, user_id, provider_id, provider_user, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    identity_id,
                    user_id,
                    provider_id,
                    provider_user,
                    json.dumps(metadata or {}),
                    datetime.utcnow().isoformat(),
                ),
            )
            self.connection.commit()
            return {
                "identity_id": identity_id,
                "user_id": user_id,
                "provider_id": provider_id,
                "provider_user": provider_user,
                "metadata": metadata or {},
            }
        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to link user identity: {e}", operation="link_user_identity"
            )

    async def store_password_reset_token(
        self,
        token_id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> None:
        """Store a password reset token."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO auth_password_reset_tokens (
                    token_id, user_id, token_hash, created_at, expires_at, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    token_id,
                    user_id,
                    token_hash,
                    datetime.utcnow().isoformat(),
                    expires_at.isoformat(),
                    ip_address,
                    user_agent,
                ),
            )

            self.connection.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to store password reset token: {e}",
                operation="store_password_reset_token",
            )

    async def get_password_reset_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get password reset token data."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM auth_password_reset_tokens
                WHERE token_id = ? AND used_at IS NULL
            """,
                (token_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "token_id": row["token_id"],
                "user_id": row["user_id"],
                "token_hash": row["token_hash"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "expires_at": datetime.fromisoformat(row["expires_at"]),
                "used_at": datetime.fromisoformat(row["used_at"])
                if row["used_at"]
                else None,
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
            }

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get password reset token: {e}",
                operation="get_password_reset_token",
            )

    async def mark_password_reset_token_used(self, token_id: str) -> None:
        """Mark a password reset token as used."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE auth_password_reset_tokens SET used_at = ?
                WHERE token_id = ?
            """,
                (datetime.utcnow().isoformat(), token_id),
            )

            self.connection.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to mark password reset token as used: {e}",
                operation="mark_password_reset_token_used",
            )

    async def cleanup_expired_password_reset_tokens(self) -> int:
        """Clean up expired password reset tokens."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM auth_password_reset_tokens
                WHERE expires_at < ?
            """,
                (datetime.utcnow().isoformat(),),
            )

            deleted_count = cursor.rowcount
            self.connection.commit()
            return deleted_count

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to cleanup expired password reset tokens: {e}",
                operation="cleanup_expired_password_reset_tokens",
            )

    async def store_email_verification_token(
        self,
        token_id: str,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: str = "unknown",
        user_agent: str = "",
    ) -> None:
        """Store an email verification token."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO auth_email_verification_tokens (
                    token_id, user_id, token_hash, created_at, expires_at, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    token_id,
                    user_id,
                    token_hash,
                    datetime.utcnow().isoformat(),
                    expires_at.isoformat(),
                    ip_address,
                    user_agent,
                ),
            )

            self.connection.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to store email verification token: {e}",
                operation="store_email_verification_token",
            )

    async def get_email_verification_token(
        self, token_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get email verification token data."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                SELECT * FROM auth_email_verification_tokens
                WHERE token_id = ? AND used_at IS NULL
            """,
                (token_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                "token_id": row["token_id"],
                "user_id": row["user_id"],
                "token_hash": row["token_hash"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "expires_at": datetime.fromisoformat(row["expires_at"]),
                "used_at": datetime.fromisoformat(row["used_at"])
                if row["used_at"]
                else None,
                "ip_address": row["ip_address"],
                "user_agent": row["user_agent"],
            }

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get email verification token: {e}",
                operation="get_email_verification_token",
            )

    async def mark_email_verification_token_used(self, token_id: str) -> None:
        """Mark an email verification token as used."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE auth_email_verification_tokens SET used_at = ?
                WHERE token_id = ?
            """,
                (datetime.utcnow().isoformat(), token_id),
            )

            self.connection.commit()

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to mark email verification token as used: {e}",
                operation="mark_email_verification_token_used",
            )

    async def cleanup_expired_email_verification_tokens(self) -> int:
        """Clean up expired email verification tokens."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                DELETE FROM auth_email_verification_tokens
                WHERE expires_at < ?
            """,
                (datetime.utcnow().isoformat(),),
            )

            deleted_count = cursor.rowcount
            self.connection.commit()
            return deleted_count

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to cleanup expired email verification tokens: {e}",
                operation="cleanup_expired_email_verification_tokens",
            )

    async def store_auth_event(self, event: AuthEvent) -> None:
        """Store an authentication event for audit logging."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO auth_events (
                    event_id, event_type, timestamp, user_id, email, tenant_id,
                    ip_address, user_agent, request_id, session_id, success,
                    error_message, details, risk_score, security_flags,
                    blocked_by_security, processing_time_ms, service_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.user_id,
                    event.email,
                    event.tenant_id,
                    event.ip_address,
                    event.user_agent,
                    event.request_id,
                    event.session_token,
                    event.success,
                    event.error_message,
                    json.dumps(event.details),
                    event.risk_score,
                    json.dumps(event.security_flags),
                    event.blocked_by_security,
                    event.processing_time_ms,
                    event.service_version,
                ),
            )

            self.connection.commit()

        except Exception as e:
            # Don't let audit logging failures affect authentication
            pass

    def _row_to_user_data(self, row: sqlite3.Row) -> UserData:
        """Convert database row to UserData object."""
        return UserData(
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
            last_login_at=datetime.fromisoformat(row["last_login_at"])
            if row["last_login_at"]
            else None,
            failed_login_attempts=row["failed_login_attempts"],
            locked_until=datetime.fromisoformat(row["locked_until"])
            if row["locked_until"]
            else None,
            two_factor_enabled=bool(row["two_factor_enabled"]),
            two_factor_secret=row["two_factor_secret"],
        )

    async def health_check(self) -> bool:
        """Perform a health check on the database connection."""
        try:
            if not self.connection:
                return False

            # Simple query to test connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True

        except Exception:
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self) -> None:
        """Cleanup database connection on deletion."""
        self.close()
