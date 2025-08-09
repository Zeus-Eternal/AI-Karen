"""
Database schema management for the consolidated authentication service.

This module provides database schema creation, migration, and optimization
utilities for the unified authentication system.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .config import DatabaseConfig
from .exceptions import DatabaseConnectionError, DatabaseOperationError

logger = logging.getLogger(__name__)


class DatabaseSchemaManager:
    """
    Manages database schema creation, migration, and optimization
    for the consolidated authentication service.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize schema manager with database configuration."""
        self.config = config
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        try:
            parsed = urlparse(self.config.database_url)

            if parsed.scheme == "sqlite":
                db_path = (
                    parsed.path.lstrip("/")
                    if parsed.path.startswith("/")
                    else parsed.path
                )
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

                self.connection = sqlite3.connect(
                    db_path,
                    timeout=self.config.connection_timeout_seconds,
                    check_same_thread=False,
                )
                self.connection.row_factory = sqlite3.Row

                # Enable foreign key constraints
                self.connection.execute("PRAGMA foreign_keys = ON")

                # Enable WAL mode for better concurrency
                self.connection.execute("PRAGMA journal_mode = WAL")

                # Optimize SQLite settings
                self.connection.execute("PRAGMA synchronous = NORMAL")
                self.connection.execute("PRAGMA cache_size = -64000")  # 64MB cache
                self.connection.execute("PRAGMA temp_store = MEMORY")

            else:
                raise DatabaseConnectionError(
                    f"Unsupported database scheme: {parsed.scheme}"
                )

        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")

    def create_unified_schema(self) -> None:
        """Create the unified authentication database schema."""
        try:
            cursor = self.connection.cursor()

            # Create schema version table first
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_schema_version (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT,
                    migration_script TEXT
                )
            """
            )

            # Create users table with comprehensive fields
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    roles TEXT NOT NULL DEFAULT '["user"]',
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
                    two_factor_secret TEXT,
                    password_reset_required BOOLEAN NOT NULL DEFAULT 0,
                    account_activation_token TEXT,
                    account_activated_at TEXT,
                    profile_picture_url TEXT,
                    timezone TEXT DEFAULT 'UTC',
                    language TEXT DEFAULT 'en',
                    notification_preferences TEXT DEFAULT '{}',
                    security_questions TEXT DEFAULT '[]',
                    login_history TEXT DEFAULT '[]',
                    device_tokens TEXT DEFAULT '[]'
                )
            """
            )

            # Create password hashes table (separate for security)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_password_hashes (
                    user_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    salt TEXT,
                    hash_algorithm TEXT NOT NULL DEFAULT 'bcrypt',
                    hash_rounds INTEGER NOT NULL DEFAULT 12,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    previous_hashes TEXT DEFAULT '[]',
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create sessions table with enhanced security fields
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
                    session_type TEXT NOT NULL DEFAULT 'web',
                    device_id TEXT,
                    device_name TEXT,
                    browser_info TEXT DEFAULT '{}',
                    os_info TEXT DEFAULT '{}',
                    network_info TEXT DEFAULT '{}',
                    authentication_method TEXT DEFAULT 'password',
                    mfa_verified BOOLEAN NOT NULL DEFAULT 0,
                    remember_me BOOLEAN NOT NULL DEFAULT 0,
                    concurrent_session_count INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create password reset tokens table
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
                    request_source TEXT DEFAULT 'web',
                    verification_code TEXT,
                    attempts_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create email verification tokens table
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
                    email_address TEXT NOT NULL,
                    verification_type TEXT DEFAULT 'registration',
                    attempts_count INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 5,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create comprehensive auth events table for audit logging
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
                    error_code TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    risk_score REAL NOT NULL DEFAULT 0.0,
                    security_flags TEXT NOT NULL DEFAULT '[]',
                    blocked_by_security BOOLEAN NOT NULL DEFAULT 0,
                    processing_time_ms REAL NOT NULL DEFAULT 0.0,
                    service_version TEXT NOT NULL DEFAULT 'consolidated-auth-v1',
                    geolocation TEXT,
                    device_fingerprint TEXT,
                    authentication_method TEXT,
                    mfa_method TEXT,
                    correlation_id TEXT,
                    parent_event_id TEXT,
                    severity_level TEXT DEFAULT 'info',
                    compliance_flags TEXT DEFAULT '[]',
                    retention_period_days INTEGER DEFAULT 2555
                )
            """
            )

            # Create rate limiting table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_rate_limits (
                    identifier TEXT NOT NULL,
                    limit_type TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_size_seconds INTEGER NOT NULL,
                    request_count INTEGER NOT NULL DEFAULT 1,
                    max_requests INTEGER NOT NULL,
                    blocked_until TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (identifier, limit_type, window_start)
                )
            """
            )

            # Create user roles table for RBAC
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_user_roles (
                    user_id TEXT NOT NULL,
                    role_name TEXT NOT NULL,
                    granted_by TEXT,
                    granted_at TEXT NOT NULL,
                    expires_at TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    role_metadata TEXT DEFAULT '{}',
                    PRIMARY KEY (user_id, role_name),
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create permissions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_permissions (
                    permission_id TEXT PRIMARY KEY,
                    permission_name TEXT UNIQUE NOT NULL,
                    resource_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
            """
            )

            # Create role permissions mapping
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_role_permissions (
                    role_name TEXT NOT NULL,
                    permission_id TEXT NOT NULL,
                    granted_at TEXT NOT NULL,
                    granted_by TEXT,
                    PRIMARY KEY (role_name, permission_id),
                    FOREIGN KEY (permission_id) REFERENCES auth_permissions (permission_id) ON DELETE CASCADE
                )
            """
            )

            # Create device tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_user_devices (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT,
                    device_type TEXT,
                    device_fingerprint TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    is_trusted BOOLEAN NOT NULL DEFAULT 0,
                    trust_score REAL DEFAULT 0.0,
                    device_info TEXT DEFAULT '{}',
                    location_info TEXT DEFAULT '{}',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
                )
            """
            )

            # Create security alerts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_security_alerts (
                    alert_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    metadata TEXT DEFAULT '{}',
                    related_event_ids TEXT DEFAULT '[]',
                    action_taken TEXT,
                    FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE SET NULL
                )
            """
            )

            self._create_indexes()
            self._create_triggers()
            self._insert_default_data()

            # Record schema version
            cursor.execute(
                """
                INSERT OR REPLACE INTO auth_schema_version (version, applied_at, description)
                VALUES (?, ?, ?)
            """,
                (
                    "1.0.0",
                    datetime.utcnow().isoformat(),
                    "Initial unified authentication schema",
                ),
            )

            self.connection.commit()
            logger.info("Unified authentication schema created successfully")

        except Exception as e:
            self.connection.rollback()
            raise DatabaseOperationError(
                f"Failed to create schema: {e}", operation="create_schema"
            )

    def _create_indexes(self) -> None:
        """Create database indexes for performance optimization."""
        cursor = self.connection.cursor()

        # User indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users (email)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_tenant ON auth_users (tenant_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_active ON auth_users (is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_verified ON auth_users (is_verified)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_created ON auth_users (created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_users_last_login ON auth_users (last_login_at)"
        )

        # Session indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_active ON auth_sessions (is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions (expires_in)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_created ON auth_sessions (created_at)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_last_accessed ON auth_sessions (last_accessed)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_ip ON auth_sessions (ip_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_sessions_device ON auth_sessions (device_id)"
        )

        # Token indexes
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

        # Event indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events (event_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events (timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_success ON auth_events (success)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_ip ON auth_events (ip_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_session ON auth_events (session_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_events_correlation ON auth_events (correlation_id)"
        )

        # Rate limiting indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_identifier ON auth_rate_limits (identifier)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_type ON auth_rate_limits (limit_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_window ON auth_rate_limits (window_start)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_blocked ON auth_rate_limits (blocked_until)"
        )

        # RBAC indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_roles_user ON auth_user_roles (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_roles_role ON auth_user_roles (role_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_roles_active ON auth_user_roles (is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_role_permissions_role ON auth_role_permissions (role_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_role_permissions_permission ON auth_role_permissions (permission_id)"
        )

        # Device tracking indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_devices_user ON auth_user_devices (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_devices_fingerprint ON auth_user_devices (device_fingerprint)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_devices_trusted ON auth_user_devices (is_trusted)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_user_devices_last_seen ON auth_user_devices (last_seen_at)"
        )

        # Security alerts indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_security_alerts_user ON auth_security_alerts (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_security_alerts_type ON auth_security_alerts (alert_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_security_alerts_severity ON auth_security_alerts (severity)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_security_alerts_status ON auth_security_alerts (status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_security_alerts_created ON auth_security_alerts (created_at)"
        )

    def _create_triggers(self) -> None:
        """Create database triggers for automatic data management."""
        cursor = self.connection.cursor()

        # Trigger to update user updated_at timestamp
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_auth_users_updated_at
            AFTER UPDATE ON auth_users
            BEGIN
                UPDATE auth_users SET updated_at = datetime('now') WHERE user_id = NEW.user_id;
            END
        """
        )

        # Trigger to update password hash updated_at timestamp
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_auth_password_hashes_updated_at
            AFTER UPDATE ON auth_password_hashes
            BEGIN
                UPDATE auth_password_hashes SET updated_at = datetime('now') WHERE user_id = NEW.user_id;
            END
        """
        )

        # Trigger to update session last_accessed timestamp
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_auth_sessions_last_accessed
            AFTER UPDATE ON auth_sessions
            WHEN OLD.last_accessed = NEW.last_accessed
            BEGIN
                UPDATE auth_sessions SET last_accessed = datetime('now') WHERE session_id = NEW.session_id;
            END
        """
        )

        # Trigger to cleanup expired tokens
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS cleanup_expired_password_reset_tokens
            AFTER INSERT ON auth_password_reset_tokens
            BEGIN
                DELETE FROM auth_password_reset_tokens
                WHERE expires_at < datetime('now') AND used_at IS NULL;
            END
        """
        )

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS cleanup_expired_email_verification_tokens
            AFTER INSERT ON auth_email_verification_tokens
            BEGIN
                DELETE FROM auth_email_verification_tokens
                WHERE expires_at < datetime('now') AND used_at IS NULL;
            END
        """
        )

    def _insert_default_data(self) -> None:
        """Insert default data required for the authentication system."""
        cursor = self.connection.cursor()

        # Insert default permissions
        default_permissions = [
            ("auth:login", "authentication", "login", "Allow user to login"),
            ("auth:logout", "authentication", "logout", "Allow user to logout"),
            (
                "auth:change_password",
                "authentication",
                "change_password",
                "Allow user to change password",
            ),
            (
                "auth:reset_password",
                "authentication",
                "reset_password",
                "Allow user to reset password",
            ),
            ("user:read_profile", "user", "read", "Allow user to read their profile"),
            (
                "user:update_profile",
                "user",
                "update",
                "Allow user to update their profile",
            ),
            ("admin:manage_users", "user", "manage", "Allow admin to manage users"),
            (
                "admin:view_audit_logs",
                "audit",
                "read",
                "Allow admin to view audit logs",
            ),
        ]

        for perm_name, resource_type, action, description in default_permissions:
            perm_id = f"perm_{perm_name.replace(':', '_')}"
            cursor.execute(
                """
                INSERT OR IGNORE INTO auth_permissions
                (permission_id, permission_name, resource_type, action, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    perm_id,
                    perm_name,
                    resource_type,
                    action,
                    description,
                    datetime.utcnow().isoformat(),
                ),
            )

        # Insert default role permissions
        default_role_permissions = [
            ("user", "perm_auth_login"),
            ("user", "perm_auth_logout"),
            ("user", "perm_auth_change_password"),
            ("user", "perm_auth_reset_password"),
            ("user", "perm_user_read_profile"),
            ("user", "perm_user_update_profile"),
            ("admin", "perm_auth_login"),
            ("admin", "perm_auth_logout"),
            ("admin", "perm_auth_change_password"),
            ("admin", "perm_user_read_profile"),
            ("admin", "perm_user_update_profile"),
            ("admin", "perm_admin_manage_users"),
            ("admin", "perm_admin_view_audit_logs"),
        ]

        for role_name, permission_id in default_role_permissions:
            cursor.execute(
                """
                INSERT OR IGNORE INTO auth_role_permissions
                (role_name, permission_id, granted_at, granted_by)
                VALUES (?, ?, ?, ?)
            """,
                (role_name, permission_id, datetime.utcnow().isoformat(), "system"),
            )

    def get_schema_version(self) -> Optional[str]:
        """Get the current schema version."""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT version FROM auth_schema_version ORDER BY applied_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row["version"] if row else None
        except Exception:
            return None

    def optimize_database(self) -> None:
        """Optimize database performance."""
        try:
            cursor = self.connection.cursor()

            # Analyze tables for query optimization
            cursor.execute("ANALYZE")

            # Vacuum database to reclaim space
            cursor.execute("VACUUM")

            # Update statistics
            cursor.execute("PRAGMA optimize")

            logger.info("Database optimization completed")

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise DatabaseOperationError(
                f"Failed to optimize database: {e}", operation="optimize"
            )

    def get_table_statistics(self) -> Dict[str, Any]:
        """Get database table statistics."""
        try:
            cursor = self.connection.cursor()
            stats = {}

            # Get table names
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'auth_%'"
            )
            tables = [row["name"] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()["count"]

                cursor.execute(f"PRAGMA table_info({table})")
                columns = len(cursor.fetchall())

                stats[table] = {"row_count": count, "column_count": columns}

            return stats

        except Exception as e:
            raise DatabaseOperationError(
                f"Failed to get table statistics: {e}", operation="get_statistics"
            )

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self) -> None:
        """Cleanup database connection on deletion."""
        self.close()
