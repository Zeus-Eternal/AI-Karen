"""
Migration utilities for consolidating data from existing authentication services.

This module provides utilities to migrate data from various existing authentication
services and databases into the unified authentication system.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import DatabaseConfig
from .database_schema import DatabaseSchemaManager
from .exceptions import DatabaseOperationError, MigrationError
from .models import UserData

logger = logging.getLogger(__name__)


class AuthDataMigrator:
    """
    Handles migration of authentication data from existing services
    to the unified authentication system.
    """

    def __init__(self, target_config: DatabaseConfig) -> None:
        """Initialize migrator with target database configuration."""
        self.target_config = target_config
        self.schema_manager = DatabaseSchemaManager(target_config)
        self.migration_log: List[Dict[str, Any]] = []

    def migrate_from_existing_databases(
        self, source_databases: List[str], dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Migrate data from existing authentication databases.

        Args:
            source_databases: List of database file paths to migrate from
            dry_run: If True, only analyze what would be migrated without making changes

        Returns:
            Migration summary with statistics and any errors
        """
        migration_summary = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "source_databases": source_databases,
            "migrated_users": 0,
            "migrated_sessions": 0,
            "migrated_events": 0,
            "errors": [],
            "warnings": [],
            "completed_at": None,
        }

        try:
            # Ensure target schema exists
            if not dry_run:
                self.schema_manager.create_unified_schema()

            for db_path in source_databases:
                if not Path(db_path).exists():
                    migration_summary["warnings"].append(
                        f"Source database not found: {db_path}"
                    )
                    continue

                try:
                    db_summary = self._migrate_single_database(db_path, dry_run)
                    migration_summary["migrated_users"] += db_summary.get("users", 0)
                    migration_summary["migrated_sessions"] += db_summary.get(
                        "sessions", 0
                    )
                    migration_summary["migrated_events"] += db_summary.get("events", 0)

                except Exception as e:
                    error_msg = f"Failed to migrate from {db_path}: {e}"
                    migration_summary["errors"].append(error_msg)
                    logger.error(error_msg)

            migration_summary["completed_at"] = datetime.now(timezone.utc).isoformat()

            if not dry_run:
                self._log_migration(migration_summary)

            return migration_summary

        except Exception as e:
            migration_summary["errors"].append(f"Migration failed: {e}")
            migration_summary["completed_at"] = datetime.now(timezone.utc).isoformat()
            raise MigrationError(f"Migration failed: {e}")

    def _migrate_single_database(self, db_path: str, dry_run: bool) -> Dict[str, int]:
        """Migrate data from a single database file."""
        summary = {"users": 0, "sessions": 0, "events": 0}

        try:
            # Connect to source database
            source_conn = sqlite3.connect(db_path)
            source_conn.row_factory = sqlite3.Row

            # Get table names
            cursor = source_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row["name"] for row in cursor.fetchall()]

            # Migrate users
            if "auth_users" in tables:
                summary["users"] = self._migrate_users(source_conn, dry_run)
            elif "users" in tables:
                summary["users"] = self._migrate_legacy_users(source_conn, dry_run)

            # Migrate sessions
            if "auth_sessions" in tables:
                summary["sessions"] = self._migrate_sessions(source_conn, dry_run)
            elif "user_sessions" in tables:
                summary["sessions"] = self._migrate_legacy_sessions(
                    source_conn, dry_run
                )

            # Migrate events/audit logs
            if "auth_events" in tables:
                summary["events"] = self._migrate_events(source_conn, dry_run)
            elif "audit_log" in tables:
                summary["events"] = self._migrate_legacy_audit_logs(
                    source_conn, dry_run, table_name="audit_log"
                )
            elif "audit_logs" in tables:
                summary["events"] = self._migrate_legacy_audit_logs(
                    source_conn, dry_run, table_name="audit_logs"
                )

            source_conn.close()

        except Exception as e:
            raise MigrationError(f"Failed to migrate from {db_path}: {e}")

        return summary

    def _migrate_users(self, source_conn: sqlite3.Connection, dry_run: bool) -> int:
        """Migrate users from auth_users table."""
        cursor = source_conn.cursor()
        cursor.execute("SELECT * FROM auth_users")
        users = cursor.fetchall()

        if dry_run:
            return len(users)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for user_row in users:
            try:
                # Check if user already exists
                target_cursor.execute(
                    "SELECT user_id FROM auth_users WHERE email = ?",
                    (user_row["email"],),
                )
                if target_cursor.fetchone():
                    logger.warning(f"User {user_row['email']} already exists, skipping")
                    continue

                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Migrate user data
                target_cursor.execute(
                    """
                    INSERT INTO auth_users (
                        user_id, email, full_name, roles, tenant_id, preferences,
                        is_verified, is_active, created_at, updated_at, last_login_at,
                        failed_login_attempts, locked_until, two_factor_enabled, two_factor_secret
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_row["user_id"],
                        user_row["email"],
                        safe_get(user_row, "full_name"),
                        safe_get(user_row, "roles", '["user"]'),
                        safe_get(user_row, "tenant_id", "default"),
                        safe_get(user_row, "preferences", "{}"),
                        safe_get(user_row, "is_verified", True),
                        safe_get(user_row, "is_active", True),
                        safe_get(
                            user_row,
                            "created_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(
                            user_row,
                            "updated_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(user_row, "last_login_at"),
                        safe_get(user_row, "failed_login_attempts", 0),
                        safe_get(user_row, "locked_until"),
                        safe_get(user_row, "two_factor_enabled", False),
                        safe_get(user_row, "two_factor_secret"),
                    ),
                )

                # Migrate password hash if available
                if "password_hash" in user_row.keys():
                    target_cursor.execute(
                        """
                        INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            user_row["user_id"],
                            user_row["password_hash"],
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

                migrated_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to migrate user {safe_get(user_row, 'email', 'unknown')}: {e}"
                )

        target_conn.commit()
        return migrated_count

    def _migrate_legacy_users(
        self, source_conn: sqlite3.Connection, dry_run: bool
    ) -> int:
        """Migrate users from legacy users table format."""
        cursor = source_conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        if dry_run:
            return len(users)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for user_row in users:
            try:
                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Generate user_id if not present
                user_id = safe_get(user_row, "id") or str(uuid.uuid4())

                # Check if user already exists
                target_cursor.execute(
                    "SELECT user_id FROM auth_users WHERE email = ?",
                    (user_row["email"],),
                )
                if target_cursor.fetchone():
                    logger.warning(f"User {user_row['email']} already exists, skipping")
                    continue

                # Convert legacy data format
                roles = safe_get(user_row, "roles", "user")
                if isinstance(roles, str):
                    roles = json.dumps([roles] if roles else ["user"])

                preferences = safe_get(user_row, "preferences", "{}")
                if isinstance(preferences, dict):
                    preferences = json.dumps(preferences)

                # Migrate user data
                target_cursor.execute(
                    """
                    INSERT INTO auth_users (
                        user_id, email, full_name, roles, tenant_id, preferences,
                        is_verified, is_active, created_at, updated_at, last_login_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        user_id,
                        user_row["email"],
                        safe_get(user_row, "full_name") or safe_get(user_row, "name"),
                        roles,
                        safe_get(user_row, "tenant_id", "default"),
                        preferences,
                        safe_get(user_row, "is_verified", True),
                        safe_get(user_row, "is_active", True),
                        safe_get(
                            user_row,
                            "created_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(
                            user_row,
                            "updated_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(user_row, "last_login"),
                    ),
                )

                # Migrate password hash if available
                if "password_hash" in user_row.keys():
                    target_cursor.execute(
                        """
                        INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            user_id,
                            user_row["password_hash"],
                            datetime.now(timezone.utc).isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

                migrated_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to migrate legacy user {safe_get(user_row, 'email', 'unknown')}: {e}"
                )

        target_conn.commit()
        return migrated_count

    def _migrate_sessions(self, source_conn: sqlite3.Connection, dry_run: bool) -> int:
        """Migrate sessions from auth_sessions table."""
        cursor = source_conn.cursor()
        cursor.execute("SELECT * FROM auth_sessions WHERE is_active = 1")
        sessions = cursor.fetchall()

        if dry_run:
            return len(sessions)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for session_row in sessions:
            try:
                # Check if session already exists
                target_cursor.execute(
                    "SELECT session_id FROM auth_sessions WHERE session_id = ?",
                    (session_row["session_token"],),
                )
                if target_cursor.fetchone():
                    continue

                # Check if user exists in target database
                target_cursor.execute(
                    "SELECT user_id FROM auth_users WHERE user_id = ?",
                    (session_row["user_id"],),
                )
                if not target_cursor.fetchone():
                    logger.warning(
                        f"User {session_row['user_id']} not found for session migration"
                    )
                    continue

                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Migrate session data
                target_cursor.execute(
                    """
                    INSERT INTO auth_sessions (
                        session_token, user_id, access_token, refresh_token, expires_in,
                        created_at, last_accessed, ip_address, user_agent, device_fingerprint,
                        geolocation, risk_score, security_flags, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_row["session_token"],
                        session_row["user_id"],
                        safe_get(session_row, "access_token", ""),
                        safe_get(session_row, "refresh_token", ""),
                        safe_get(session_row, "expires_in", 3600),
                        safe_get(
                            session_row,
                            "created_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(
                            session_row,
                            "last_accessed",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(session_row, "ip_address", "unknown"),
                        safe_get(session_row, "user_agent", ""),
                        safe_get(session_row, "device_fingerprint"),
                        safe_get(session_row, "geolocation"),
                        safe_get(session_row, "risk_score", 0.0),
                        safe_get(session_row, "security_flags", "[]"),
                        safe_get(session_row, "is_active", True),
                    ),
                )

                migrated_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to migrate session {safe_get(session_row, 'session_token', 'unknown')}: {e}"
                )

        target_conn.commit()
        return migrated_count

    def _migrate_legacy_sessions(
        self, source_conn: sqlite3.Connection, dry_run: bool
    ) -> int:
        """Migrate sessions from legacy user_sessions table format."""
        cursor = source_conn.cursor()
        cursor.execute("SELECT * FROM user_sessions WHERE is_active = 1")
        sessions = cursor.fetchall()

        if dry_run:
            return len(sessions)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for session_row in sessions:
            try:
                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Generate session_token if using different field
                session_token = (
                    safe_get(session_row, "session_token")
                    or safe_get(session_row, "token")
                    or str(uuid.uuid4())
                )

                # Check if session already exists
                target_cursor.execute(
                    "SELECT session_id FROM auth_sessions WHERE session_id = ?",
                    (session_token,),
                )
                if target_cursor.fetchone():
                    continue

                # Check if user exists in target database
                target_cursor.execute(
                    "SELECT user_id FROM auth_users WHERE user_id = ?",
                    (session_row["user_id"],),
                )
                if not target_cursor.fetchone():
                    logger.warning(
                        f"User {session_row['user_id']} not found for session migration"
                    )
                    continue

                # Convert expires_at to expires_in if needed
                expires_in = 3600  # Default 1 hour
                if "expires_at" in session_row.keys() and session_row["expires_at"]:
                    try:
                        expires_at = datetime.fromisoformat(session_row["expires_at"])
                        expires_in = int(
                            (expires_at - datetime.now(timezone.utc)).total_seconds()
                        )
                        if expires_in <= 0:
                            continue  # Skip expired sessions
                    except Exception:
                        pass

                # Migrate session data
                target_cursor.execute(
                    """
                    INSERT INTO auth_sessions (
                        session_token, user_id, access_token, refresh_token, expires_in,
                        created_at, last_accessed, ip_address, user_agent, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        session_token,
                        session_row["user_id"],
                        safe_get(session_row, "access_token", session_token),
                        safe_get(session_row, "refresh_token", ""),
                        expires_in,
                        safe_get(
                            session_row,
                            "created_at",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(
                            session_row,
                            "last_accessed",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                        safe_get(session_row, "ip_address", "unknown"),
                        safe_get(session_row, "user_agent", ""),
                        safe_get(session_row, "is_active", True),
                    ),
                )

                migrated_count += 1

            except Exception as e:
                logger.error(f"Failed to migrate legacy session: {e}")

        target_conn.commit()
        return migrated_count

    def _migrate_events(self, source_conn: sqlite3.Connection, dry_run: bool) -> int:
        """Migrate events from auth_events table."""
        cursor = source_conn.cursor()
        # Only migrate recent events (last 30 days) to avoid overwhelming the target
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        cursor.execute(
            "SELECT * FROM auth_events WHERE timestamp > ? ORDER BY timestamp DESC LIMIT 10000",
            (cutoff_date,),
        )
        events = cursor.fetchall()

        if dry_run:
            return len(events)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for event_row in events:
            try:
                # Check if event already exists
                target_cursor.execute(
                    "SELECT event_id FROM auth_events WHERE event_id = ?",
                    (event_row["event_id"],),
                )
                if target_cursor.fetchone():
                    continue

                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Migrate event data
                target_cursor.execute(
                    """
                    INSERT INTO auth_events (
                        event_id, event_type, timestamp, user_id, email, tenant_id,
                        ip_address, user_agent, request_id, session_id, success,
                        error_message, details, risk_score, security_flags,
                        blocked_by_security, processing_time_ms, service_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event_row["event_id"],
                        event_row["event_type"],
                        event_row["timestamp"],
                        safe_get(event_row, "user_id"),
                        safe_get(event_row, "email"),
                        safe_get(event_row, "tenant_id", "default"),
                        safe_get(event_row, "ip_address", "unknown"),
                        safe_get(event_row, "user_agent", ""),
                        safe_get(event_row, "request_id"),
                        safe_get(event_row, "session_token"),
                        safe_get(event_row, "success", True),
                        safe_get(event_row, "error_message"),
                        safe_get(event_row, "details", "{}"),
                        safe_get(event_row, "risk_score", 0.0),
                        safe_get(event_row, "security_flags", "[]"),
                        safe_get(event_row, "blocked_by_security", False),
                        safe_get(event_row, "processing_time_ms", 0.0),
                        safe_get(event_row, "service_version", "migrated"),
                    ),
                )

                migrated_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to migrate event {safe_get(event_row, 'event_id', 'unknown')}: {e}"
                )

        target_conn.commit()
        return migrated_count

    def _migrate_legacy_audit_logs(
        self, source_conn: sqlite3.Connection, dry_run: bool, table_name: str
    ) -> int:
        """Migrate events from legacy audit log table format."""
        cursor = source_conn.cursor()
        # Only migrate recent events (last 30 days)
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        cursor.execute(
            f"SELECT * FROM {table_name} WHERE created_at > ? ORDER BY created_at DESC LIMIT 10000",
            (cutoff_date,),
        )
        events = cursor.fetchall()

        if dry_run:
            return len(events)

        target_conn = self.schema_manager.connection
        target_cursor = target_conn.cursor()

        migrated_count = 0

        for event_row in events:
            try:
                # Helper function to safely get values from sqlite3.Row
                def safe_get(row, key, default=None):
                    try:
                        return row[key] if key in row.keys() else default
                    except (KeyError, TypeError):
                        return default

                # Generate event_id if not present
                event_id = safe_get(event_row, "id") or str(uuid.uuid4())

                # Check if event already exists
                target_cursor.execute(
                    "SELECT event_id FROM auth_events WHERE event_id = ?", (event_id,)
                )
                if target_cursor.fetchone():
                    continue

                # Convert legacy audit log to auth event format
                event_type = safe_get(event_row, "action", "unknown")
                timestamp = safe_get(
                    event_row, "created_at", datetime.now(timezone.utc).isoformat()
                )

                # Migrate event data
                target_cursor.execute(
                    """
                    INSERT INTO auth_events (
                        event_id, event_type, timestamp, user_id, ip_address, user_agent,
                        success, details, service_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event_id,
                        event_type,
                        timestamp,
                        safe_get(event_row, "user_id"),
                        safe_get(event_row, "ip_address", "unknown"),
                        safe_get(event_row, "user_agent", ""),
                        True,  # Assume success for legacy logs
                        json.dumps(safe_get(event_row, "details", {}))
                        if isinstance(safe_get(event_row, "details"), dict)
                        else safe_get(event_row, "details", "{}"),
                        "migrated-legacy",
                    ),
                )

                migrated_count += 1

            except Exception as e:
                logger.error(f"Failed to migrate legacy audit log: {e}")

        target_conn.commit()
        return migrated_count

    def _log_migration(self, summary: Dict[str, Any]) -> None:
        """Log migration summary to the database."""
        try:
            target_conn = self.schema_manager.connection
            cursor = target_conn.cursor()

            cursor.execute(
                """
                INSERT INTO auth_events (
                    event_id, event_type, timestamp, success, details, service_version
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    "data_migration",
                    summary["started_at"],
                    len(summary["errors"]) == 0,
                    json.dumps(summary),
                    "migration-utility",
                ),
            )

            target_conn.commit()

        except Exception as e:
            logger.error(f"Failed to log migration: {e}")

    def cleanup_old_data(self, older_than_days: int = 90) -> Dict[str, int]:
        """
        Clean up old data from the unified database.

        Args:
            older_than_days: Remove data older than this many days

        Returns:
            Dictionary with counts of cleaned up records
        """
        cleanup_summary = {"expired_tokens": 0, "old_events": 0, "inactive_sessions": 0}

        try:
            target_conn = self.schema_manager.connection
            cursor = target_conn.cursor()

            cutoff_date = (
                datetime.now(timezone.utc) - timedelta(days=older_than_days)
            ).isoformat()

            # Clean up expired password reset tokens
            cursor.execute(
                "DELETE FROM auth_password_reset_tokens WHERE expires_at < ?",
                (datetime.now(timezone.utc).isoformat(),),
            )
            cleanup_summary["expired_tokens"] += cursor.rowcount

            # Clean up expired email verification tokens
            cursor.execute(
                "DELETE FROM auth_email_verification_tokens WHERE expires_at < ?",
                (datetime.now(timezone.utc).isoformat(),),
            )
            cleanup_summary["expired_tokens"] += cursor.rowcount

            # Clean up old events (keep recent ones for audit)
            cursor.execute(
                "DELETE FROM auth_events WHERE timestamp < ? AND event_type NOT IN ('login', 'logout', 'password_change')",
                (cutoff_date,),
            )
            cleanup_summary["old_events"] = cursor.rowcount

            # Clean up inactive sessions
            cursor.execute(
                "DELETE FROM auth_sessions WHERE is_active = 0 AND created_at < ?",
                (cutoff_date,),
            )
            cleanup_summary["inactive_sessions"] = cursor.rowcount

            target_conn.commit()

            logger.info(f"Cleanup completed: {cleanup_summary}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise DatabaseOperationError(
                f"Failed to cleanup old data: {e}", operation="cleanup"
            )

        return cleanup_summary

    def validate_migration(self) -> Dict[str, Any]:
        """
        Validate the migrated data for consistency and integrity.

        Returns:
            Validation report with any issues found
        """
        validation_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "issues": [],
            "warnings": [],
            "statistics": {},
        }

        try:
            target_conn = self.schema_manager.connection
            cursor = target_conn.cursor()

            # Check for users without password hashes
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM auth_users u
                LEFT JOIN auth_password_hashes p ON u.user_id = p.user_id
                WHERE p.user_id IS NULL
            """
            )
            users_without_passwords = cursor.fetchone()["count"]
            if users_without_passwords > 0:
                validation_report["warnings"].append(
                    f"{users_without_passwords} users without password hashes"
                )

            # Check for orphaned sessions
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM auth_sessions s
                LEFT JOIN auth_users u ON s.user_id = u.user_id
                WHERE u.user_id IS NULL
            """
            )
            orphaned_sessions = cursor.fetchone()["count"]
            if orphaned_sessions > 0:
                validation_report["issues"].append(
                    f"{orphaned_sessions} orphaned sessions found"
                )

            # Check for duplicate emails
            cursor.execute(
                """
                SELECT email, COUNT(*) as count FROM auth_users
                GROUP BY email HAVING COUNT(*) > 1
            """
            )
            duplicate_emails = cursor.fetchall()
            if duplicate_emails:
                validation_report["issues"].append(
                    f"{len(duplicate_emails)} duplicate email addresses found"
                )

            # Get statistics
            cursor.execute("SELECT COUNT(*) as count FROM auth_users")
            validation_report["statistics"]["total_users"] = cursor.fetchone()["count"]

            cursor.execute(
                "SELECT COUNT(*) as count FROM auth_sessions WHERE is_active = 1"
            )
            validation_report["statistics"]["active_sessions"] = cursor.fetchone()[
                "count"
            ]

            cursor.execute("SELECT COUNT(*) as count FROM auth_events")
            validation_report["statistics"]["total_events"] = cursor.fetchone()["count"]

        except Exception as e:
            validation_report["issues"].append(f"Validation failed: {e}")

        return validation_report
