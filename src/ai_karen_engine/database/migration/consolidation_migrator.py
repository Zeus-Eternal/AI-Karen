"""
Database consolidation migrator for SQLite to PostgreSQL migration.

This module provides the main migration service that handles the complete
process of migrating authentication data from SQLite to PostgreSQL with
UUID consistency and data validation.
"""

import json
import logging
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ai_karen_engine.database.migration.backup_manager import BackupManager
from ai_karen_engine.database.migration.migration_validator import (
    MigrationValidationReport,
    MigrationValidator,
)
from ai_karen_engine.database.migration.postgres_schema import (
    PasswordResetToken,
    PostgreSQLAuthSchema,
    User,
    UserSession,
)


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    message: str
    users_migrated: int = 0
    sessions_migrated: int = 0
    tokens_migrated: int = 0
    uuid_mappings: Optional[Dict[str, str]] = None
    validation_report: Optional[MigrationValidationReport] = None
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "users_migrated": self.users_migrated,
            "sessions_migrated": self.sessions_migrated,
            "tokens_migrated": self.tokens_migrated,
            "uuid_mappings_count": len(self.uuid_mappings) if self.uuid_mappings else 0,
            "validation_report": self.validation_report.to_dict()
            if self.validation_report
            else None,
            "errors": self.errors,
        }


class DatabaseConsolidationMigrator:
    """
    Handles migration from SQLite to PostgreSQL for authentication data.

    This class orchestrates the complete migration process including:
    - Creating PostgreSQL schema
    - Migrating user data with UUID consistency
    - Migrating sessions and tokens with proper foreign keys
    - Validating migration success
    - Providing rollback capabilities
    """

    def __init__(
        self,
        sqlite_paths: List[str],
        postgres_url: str,
        backup_dir: str = "migration_backups",
    ):
        """
        Initialize the migration service.

        Args:
            sqlite_paths: List of SQLite database file paths
            postgres_url: PostgreSQL connection URL
            backup_dir: Directory for backup files
        """
        self.sqlite_paths = sqlite_paths
        self.postgres_url = postgres_url
        self.postgres_engine = create_engine(postgres_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.postgres_engine
        )

        # Initialize supporting services
        self.schema_manager = PostgreSQLAuthSchema(postgres_url)
        self.backup_manager = BackupManager(backup_dir)
        self.validator = MigrationValidator(sqlite_paths, postgres_url)

        self.logger = logging.getLogger(__name__)

        # Track migration state
        self.uuid_mappings: Dict[str, str] = {}  # old_id -> new_uuid
        self.migration_timestamp = datetime.utcnow()

    async def migrate_all_data(
        self, create_backups: bool = True, validate_after: bool = True
    ) -> MigrationResult:
        """
        Execute complete migration process.

        Args:
            create_backups: Whether to create backups before migration
            validate_after: Whether to validate migration after completion

        Returns:
            Migration result with success status and details
        """
        self.logger.info("Starting complete database migration process")

        try:
            # Step 1: Create backups if requested
            backup_mapping = {}
            if create_backups:
                self.logger.info("Creating backups before migration")
                backup_mapping = self.backup_manager.backup_sqlite_databases(
                    self.sqlite_paths
                )

                # Verify backup integrity
                if not self.backup_manager.verify_backup_integrity(backup_mapping):
                    raise Exception("Backup integrity verification failed")

            # Step 2: Create PostgreSQL schema
            self.logger.info("Creating PostgreSQL authentication schema")
            if not self.schema_manager.create_schema(drop_existing=False):
                raise Exception("Failed to create PostgreSQL schema")

            # Step 3: Migrate data in order (users first, then dependent tables)
            users_migrated = await self._migrate_users()
            sessions_migrated = await self._migrate_sessions()
            tokens_migrated = await self._migrate_tokens()

            # Step 4: Create performance indexes
            self.logger.info("Creating performance indexes")
            self.schema_manager.create_indexes()

            # Step 5: Validate migration if requested
            validation_report = None
            if validate_after:
                self.logger.info("Validating migration results")
                validation_report = self.validator.validate_complete_migration()

                if not validation_report.overall_success:
                    raise Exception(
                        f"Migration validation failed: {validation_report.validation_timestamp}"
                    )

            # Success!
            result = MigrationResult(
                success=True,
                message=f"Migration completed successfully - {users_migrated} users, {sessions_migrated} sessions, {tokens_migrated} tokens migrated",
                users_migrated=users_migrated,
                sessions_migrated=sessions_migrated,
                tokens_migrated=tokens_migrated,
                uuid_mappings=self.uuid_mappings,
                validation_report=validation_report,
            )

            self.logger.info(f"Migration completed successfully: {result.message}")
            return result

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")

            # Attempt rollback if backups were created
            if backup_mapping:
                self.logger.info("Attempting rollback due to migration failure")
                try:
                    await self._rollback_migration(backup_mapping)
                    self.logger.info("Rollback completed successfully")
                except Exception as rollback_error:
                    self.logger.error(f"Rollback also failed: {rollback_error}")

            return MigrationResult(
                success=False, message=f"Migration failed: {e}", errors=[str(e)]
            )

    async def _migrate_users(self) -> int:
        """
        Migrate user data from SQLite to PostgreSQL.

        Returns:
            Number of users migrated
        """
        self.logger.info("Migrating user data")

        users_migrated = 0

        for sqlite_path in self.sqlite_paths:
            try:
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()

                # Find user tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'"
                )
                user_tables = [row[0] for row in cursor.fetchall()]

                for table_name in user_tables:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]

                    # Skip if not a user table
                    if "email" not in columns:
                        continue

                    # Migrate users from this table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    sqlite_users = cursor.fetchall()

                    for user_row in sqlite_users:
                        user_data = dict(zip(columns, user_row))
                        migrated_user = await self._migrate_single_user(user_data)

                        if migrated_user:
                            users_migrated += 1

                            # Store UUID mapping for foreign key updates
                            old_id = user_data.get("user_id") or user_data.get("id")
                            if old_id:
                                self.uuid_mappings[str(old_id)] = str(migrated_user.id)

                conn.close()

            except Exception as e:
                self.logger.error(f"Failed to migrate users from {sqlite_path}: {e}")
                raise

        self.logger.info(f"Migrated {users_migrated} users successfully")
        return users_migrated

    async def _migrate_single_user(self, user_data: Dict) -> Optional[User]:
        """
        Migrate a single user record.

        Args:
            user_data: User data from SQLite

        Returns:
            Migrated User object or None if failed
        """
        try:
            with self.SessionLocal() as session:
                # Check if user already exists
                existing_user = (
                    session.query(User)
                    .filter(User.email == user_data.get("email"))
                    .first()
                )
                if existing_user:
                    self.logger.warning(
                        f"User {user_data.get('email')} already exists, skipping"
                    )
                    return existing_user

                # Create new user with consistent UUID
                new_user = User(
                    id=uuid.uuid4(),
                    email=user_data.get("email"),
                    password_hash=user_data.get("password_hash"),
                    full_name=user_data.get("full_name"),
                    tenant_id=uuid.UUID(user_data.get("tenant_id", str(uuid.uuid4()))),
                    roles=user_data.get("roles", []),
                    preferences=user_data.get("preferences", {}),
                    is_verified=user_data.get("is_verified", False),
                    is_active=user_data.get("is_active", True),
                    two_factor_enabled=user_data.get("two_factor_enabled", False),
                    two_factor_secret=user_data.get("two_factor_secret"),
                    created_at=self._parse_datetime(user_data.get("created_at")),
                    updated_at=self._parse_datetime(user_data.get("updated_at")),
                    last_login_at=self._parse_datetime(user_data.get("last_login_at")),
                    failed_login_attempts=user_data.get("failed_login_attempts", 0),
                    locked_until=self._parse_datetime(user_data.get("locked_until")),
                )

                session.add(new_user)
                session.commit()
                session.refresh(new_user)

                return new_user

        except Exception as e:
            self.logger.error(f"Failed to migrate user {user_data.get('email')}: {e}")
            return None

    async def _migrate_sessions(self) -> int:
        """
        Migrate session data from SQLite to PostgreSQL.

        Returns:
            Number of sessions migrated
        """
        self.logger.info("Migrating session data")

        sessions_migrated = 0

        for sqlite_path in self.sqlite_paths:
            try:
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()

                # Find session tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%session%'"
                )
                session_tables = [row[0] for row in cursor.fetchall()]

                for table_name in session_tables:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]

                    # Skip if not a session table
                    if "session_token" not in columns:
                        continue

                    # Migrate sessions from this table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    sqlite_sessions = cursor.fetchall()

                    for session_row in sqlite_sessions:
                        session_data = dict(zip(columns, session_row))
                        migrated_session = await self._migrate_single_session(
                            session_data
                        )

                        if migrated_session:
                            sessions_migrated += 1

                conn.close()

            except Exception as e:
                self.logger.error(f"Failed to migrate sessions from {sqlite_path}: {e}")
                raise

        self.logger.info(f"Migrated {sessions_migrated} sessions successfully")
        return sessions_migrated

    async def _migrate_single_session(
        self, session_data: Dict
    ) -> Optional[UserSession]:
        """
        Migrate a single session record.

        Args:
            session_data: Session data from SQLite

        Returns:
            Migrated UserSession object or None if failed
        """
        try:
            with self.SessionLocal() as session:
                # Check if session already exists
                existing_session = (
                    session.query(UserSession)
                    .filter(
                        UserSession.session_token == session_data.get("session_token")
                    )
                    .first()
                )
                if existing_session:
                    self.logger.warning(
                        f"Session {session_data.get('session_token')} already exists, skipping"
                    )
                    return existing_session

                # Map old user_id to new UUID
                old_user_id = str(session_data.get("user_id"))
                new_user_id = self.uuid_mappings.get(old_user_id)

                if not new_user_id:
                    self.logger.warning(
                        f"No UUID mapping found for user_id {old_user_id}, skipping session"
                    )
                    return None

                # Create new session with proper foreign key
                new_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(new_user_id),
                    session_token=session_data.get("session_token"),
                    access_token=session_data.get("access_token"),
                    refresh_token=session_data.get("refresh_token"),
                    expires_at=self._parse_datetime(session_data.get("expires_at"))
                    or self._parse_datetime(session_data.get("expires_in")),
                    created_at=self._parse_datetime(session_data.get("created_at")),
                    last_accessed=self._parse_datetime(
                        session_data.get("last_accessed")
                    ),
                    ip_address=session_data.get("ip_address"),
                    user_agent=session_data.get("user_agent"),
                    device_fingerprint=session_data.get("device_fingerprint"),
                    geolocation=session_data.get("geolocation"),
                    risk_score=session_data.get("risk_score", 0.0),
                    security_flags=session_data.get("security_flags", []),
                    is_active=session_data.get("is_active", True),
                    invalidated_at=self._parse_datetime(
                        session_data.get("invalidated_at")
                    ),
                    invalidation_reason=session_data.get("invalidation_reason"),
                )

                session.add(new_session)
                session.commit()
                session.refresh(new_session)

                return new_session

        except Exception as e:
            self.logger.error(
                f"Failed to migrate session {session_data.get('session_token')}: {e}"
            )
            return None

    async def _migrate_tokens(self) -> int:
        """
        Migrate password reset token data from SQLite to PostgreSQL.

        Returns:
            Number of tokens migrated
        """
        self.logger.info("Migrating password reset token data")

        tokens_migrated = 0

        for sqlite_path in self.sqlite_paths:
            try:
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()

                # Find token tables
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%token%'"
                )
                token_tables = [row[0] for row in cursor.fetchall()]

                for table_name in token_tables:
                    # Get table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]

                    # Skip if not a token table
                    if "token" not in columns:
                        continue

                    # Migrate tokens from this table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    sqlite_tokens = cursor.fetchall()

                    for token_row in sqlite_tokens:
                        token_data = dict(zip(columns, token_row))
                        migrated_token = await self._migrate_single_token(token_data)

                        if migrated_token:
                            tokens_migrated += 1

                conn.close()

            except Exception as e:
                self.logger.error(f"Failed to migrate tokens from {sqlite_path}: {e}")
                raise

        self.logger.info(f"Migrated {tokens_migrated} tokens successfully")
        return tokens_migrated

    async def _migrate_single_token(
        self, token_data: Dict
    ) -> Optional[PasswordResetToken]:
        """
        Migrate a single password reset token record.

        Args:
            token_data: Token data from SQLite

        Returns:
            Migrated PasswordResetToken object or None if failed
        """
        try:
            with self.SessionLocal() as session:
                # Check if token already exists
                existing_token = (
                    session.query(PasswordResetToken)
                    .filter(PasswordResetToken.token == token_data.get("token"))
                    .first()
                )
                if existing_token:
                    self.logger.warning(
                        f"Token {token_data.get('token')} already exists, skipping"
                    )
                    return existing_token

                # Map old user_id to new UUID
                old_user_id = str(token_data.get("user_id"))
                new_user_id = self.uuid_mappings.get(old_user_id)

                if not new_user_id:
                    self.logger.warning(
                        f"No UUID mapping found for user_id {old_user_id}, skipping token"
                    )
                    return None

                # Create new token with proper foreign key
                new_token = PasswordResetToken(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(new_user_id),
                    token=token_data.get("token"),
                    expires_at=self._parse_datetime(token_data.get("expires_at")),
                    used=token_data.get("used", False),
                    created_at=self._parse_datetime(token_data.get("created_at")),
                    ip_address=token_data.get("ip_address"),
                    user_agent=token_data.get("user_agent"),
                )

                session.add(new_token)
                session.commit()
                session.refresh(new_token)

                return new_token

        except Exception as e:
            self.logger.error(f"Failed to migrate token {token_data.get('token')}: {e}")
            return None

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string from SQLite.

        Args:
            date_str: Date string from SQLite

        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None

        try:
            # Try common datetime formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, try parsing as timestamp
            try:
                timestamp = float(date_str)
                return datetime.fromtimestamp(timestamp)
            except (ValueError, TypeError):
                pass

            self.logger.warning(f"Could not parse datetime: {date_str}")
            return None

        except Exception as e:
            self.logger.warning(f"Error parsing datetime {date_str}: {e}")
            return None

    async def _rollback_migration(self, backup_mapping: Dict[str, str]) -> None:
        """
        Rollback migration by restoring SQLite backups and clearing PostgreSQL.

        Args:
            backup_mapping: Dictionary mapping original paths to backup paths
        """
        try:
            self.logger.info("Rolling back migration")

            # Clear PostgreSQL authentication tables
            with self.postgres_engine.connect() as conn:
                # Disable foreign key checks temporarily
                conn.execute(text("SET session_replication_role = replica"))

                # Clear tables in reverse dependency order
                tables_to_clear = [
                    "password_reset_tokens",
                    "user_identities",
                    "auth_sessions",
                    "auth_users",
                    "auth_providers",
                ]

                for table in tables_to_clear:
                    try:
                        conn.execute(text(f"DELETE FROM {table}"))
                        self.logger.info(f"Cleared table: {table}")
                    except Exception as e:
                        self.logger.warning(f"Could not clear table {table}: {e}")

                # Re-enable foreign key checks
                conn.execute(text("SET session_replication_role = DEFAULT"))
                conn.commit()

            # Restore SQLite backups
            if not self.backup_manager.restore_sqlite_databases(backup_mapping):
                raise Exception("Failed to restore SQLite backups")

            self.logger.info("Migration rollback completed successfully")

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            raise

    def get_migration_status(self) -> Dict:
        """
        Get current migration status and statistics.

        Returns:
            Dictionary with migration status information
        """
        try:
            status = {
                "migration_timestamp": self.migration_timestamp.isoformat(),
                "uuid_mappings_count": len(self.uuid_mappings),
                "postgres_schema_valid": self.schema_manager.validate_schema(),
                "table_info": self.schema_manager.get_table_info(),
            }

            # Get record counts from PostgreSQL
            with self.postgres_engine.connect() as conn:
                for table in ["auth_users", "auth_sessions", "password_reset_tokens"]:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        status[f"{table}_count"] = result.scalar()
                    except Exception:
                        status[f"{table}_count"] = 0

            return status

        except Exception as e:
            self.logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}
