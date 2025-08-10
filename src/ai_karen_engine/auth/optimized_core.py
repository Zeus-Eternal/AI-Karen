"""
PostgreSQL-optimized core authentication layer.

This module provides high-performance authentication operations using
PostgreSQL-specific optimizations and efficient query patterns.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import bcrypt

from .config import AuthConfig
from .exceptions import (
    AccountDisabledError,
    AccountLockedError,
    InvalidCredentialsError,
    PasswordValidationError,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .models import AuthEvent, AuthEventType, SessionData, UserData
from .optimized_database import OptimizedAuthDatabaseClient
from .optimized_session import OptimizedSessionManager
from .tokens import TokenManager

try:
    import json

    from sqlalchemy import text
except ImportError:
    text = None
    import json


class OptimizedPasswordHasher:
    """
    Optimized password hashing with PostgreSQL-aware performance tuning.

    Includes adaptive hashing and efficient verification patterns.
    """

    def __init__(self, rounds: int = 12) -> None:
        """Initialize optimized password hasher."""
        if not (4 <= rounds <= 20):
            raise ValueError("Bcrypt rounds must be between 4 and 20")
        self.rounds = rounds
        self.logger = logging.getLogger(f"{__name__}.OptimizedPasswordHasher")

    def hash_password(self, password: str) -> str:
        """Hash password with optimized bcrypt settings."""
        if not password:
            raise ValueError("Password cannot be empty")

        # Use optimized salt generation
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password with timing attack protection."""
        if not password or not hashed:
            return False

        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    def verify_password_batch(
        self, password_hash_pairs: List[Tuple[str, str]]
    ) -> List[bool]:
        """
        Batch password verification for improved performance.

        Useful for bulk operations or when verifying multiple passwords.
        """
        results = []
        for password, hashed in password_hash_pairs:
            results.append(self.verify_password(password, hashed))
        return results

    def needs_rehash(self, hashed: str) -> bool:
        """Check if password hash needs updating."""
        try:
            parts = hashed.split("$")
            if len(parts) >= 3 and parts[1] == "2b":
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
        except (ValueError, IndexError):
            pass
        return True


class OptimizedCoreAuthenticator:
    """
    PostgreSQL-optimized core authentication with high-performance operations.

    Features:
    - Batch operations for improved throughput
    - Optimized database queries with proper indexing
    - Efficient session management with cleanup
    - Connection pooling optimization
    """

    def __init__(self, config: AuthConfig) -> None:
        """Initialize optimized core authenticator."""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.OptimizedCoreAuthenticator")

        # Initialize optimized components
        self.db_client = OptimizedAuthDatabaseClient(config.database)
        self.token_manager = TokenManager(config.jwt)
        self.session_manager = OptimizedSessionManager(
            config.session, self.token_manager, self.db_client
        )
        self.password_hasher = OptimizedPasswordHasher(
            config.security.password_hash_rounds
        )

        # Performance tracking
        self._operation_times: Dict[str, List[float]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the optimized authenticator."""
        if self._initialized:
            return

        try:
            # Initialize database schema with optimizations
            await self.db_client.initialize_schema()

            # Start session manager background tasks
            await self.session_manager.start_background_tasks()

            self._initialized = True
            self.logger.info("Optimized core authenticator initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize optimized authenticator: {e}")
            raise

    async def authenticate_user_optimized(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
    ) -> Optional[UserData]:
        """
        Authenticate user with PostgreSQL optimizations.

        Uses efficient queries and proper indexing for maximum performance.
        """
        start_time = datetime.now(timezone.utc)
        operation = "authenticate_user_optimized"

        try:
            if not email or not password:
                raise InvalidCredentialsError("Email and password are required")

            # Use optimized user lookup with active user filtering
            async with self.db_client.session_factory() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT
                        u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
                        u.is_verified, u.is_active, u.created_at, u.updated_at, u.last_login_at,
                        u.failed_login_attempts, u.locked_until, u.two_factor_enabled, u.two_factor_secret,
                        p.password_hash
                    FROM auth_users u
                    JOIN auth_password_hashes p ON u.user_id = p.user_id
                    WHERE u.email = :email AND u.is_active = true
                """
                    ),
                    {"email": email},
                )

                row = result.fetchone()
                if not row:
                    await self._log_failed_auth(
                        email, ip_address, user_agent, "user_not_found", start_time
                    )
                    raise InvalidCredentialsError()

                user_data = self.db_client._row_to_user_data(row)
                password_hash = row.password_hash

            # Check account status
            if user_data.is_locked():
                await self._log_failed_auth(
                    email, ip_address, user_agent, "account_locked", start_time
                )
                raise AccountLockedError(
                    locked_until=user_data.locked_until.isoformat()
                    if user_data.locked_until
                    else None,
                    failed_attempts=user_data.failed_login_attempts,
                )

            # Verify password
            if not self.password_hasher.verify_password(password, password_hash):
                # Update failed attempts using optimized query
                await self._increment_failed_attempts(user_data)
                await self._log_failed_auth(
                    email, ip_address, user_agent, "invalid_password", start_time
                )
                raise InvalidCredentialsError()

            # Successful authentication - update user data
            await self._handle_successful_auth(user_data, password_hash)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            self.logger.info(f"Optimized authentication successful for {email}")
            return user_data

        except (InvalidCredentialsError, AccountLockedError, AccountDisabledError):
            raise
        except Exception as e:
            self.logger.error(f"Optimized authentication error: {e}")
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def create_user_optimized(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        tenant_id: str = "default",
        roles: Optional[List[str]] = None,
        **kwargs,
    ) -> UserData:
        """
        Create user with PostgreSQL UPSERT optimization.

        Uses ON CONFLICT for atomic operations and better performance.
        """
        start_time = datetime.now(timezone.utc)
        operation = "create_user_optimized"

        try:
            # Validate password
            is_valid, errors = self._validate_password(password)
            if not is_valid:
                raise PasswordValidationError(errors=errors)

            # Hash password
            password_hash = self.password_hasher.hash_password(password)

            # Create user data
            user_data = UserData(
                user_id=str(uuid4()),
                email=email,
                full_name=full_name,
                tenant_id=tenant_id,
                roles=roles or ["user"],
                **kwargs,
            )

            # Use optimized upsert operation
            created_user = await self.db_client.upsert_user(user_data, password_hash)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            self.logger.info(f"Optimized user creation successful for {email}")
            return created_user

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def create_session_optimized(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        geolocation: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SessionData:
        """
        Create session with optimized PostgreSQL operations.

        Includes automatic cleanup and efficient storage.
        """
        start_time = datetime.now(timezone.utc)
        operation = "create_session_optimized"

        try:
            session_data = await self.session_manager.create_session(
                user_data=user_data,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                geolocation=geolocation,
                **kwargs,
            )

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            return session_data

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def validate_session_optimized(
        self, session_token: str, **kwargs
    ) -> Optional[UserData]:
        """
        Validate session with optimized database queries.

        Uses JOIN operations for efficient validation.
        """
        start_time = datetime.now(timezone.utc)
        operation = "validate_session_optimized"

        try:
            user_data = await self.session_manager.validate_session(session_token)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            return user_data

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def batch_validate_sessions(
        self, session_tokens: List[str]
    ) -> Dict[str, Optional[UserData]]:
        """
        Batch validate multiple sessions for improved performance.

        Uses efficient batch queries to validate multiple sessions at once.
        """
        start_time = datetime.now(timezone.utc)
        operation = "batch_validate_sessions"

        try:
            results = {}

            # Process in batches to avoid overwhelming the database
            batch_size = 50
            for i in range(0, len(session_tokens), batch_size):
                batch = session_tokens[i : i + batch_size]

                # Use batch query for validation
                async with self.db_client.session_factory() as session:
                    result = await session.execute(
                        text(
                            """
                        SELECT
                            s.session_token,
                            u.user_id, u.email, u.full_name, u.roles, u.tenant_id, u.preferences,
                            u.is_verified, u.is_active, u.created_at, u.updated_at, u.last_login_at,
                            u.failed_login_attempts, u.locked_until, u.two_factor_enabled, u.two_factor_secret
                        FROM auth_sessions s
                        JOIN auth_users u ON s.user_id = u.user_id
                        WHERE s.session_token = ANY(:tokens)
                        AND s.is_active = true
                        AND u.is_active = true
                        AND (s.created_at + INTERVAL '1 second' * s.expires_in) > NOW()
                    """
                        ),
                        {"tokens": batch},
                    )

                    # Process results
                    valid_sessions = {}
                    for row in result.fetchall():
                        user_data = self.db_client._row_to_user_data(row)
                        valid_sessions[row.session_token] = user_data

                    # Add results for this batch
                    for token in batch:
                        results[token] = valid_sessions.get(token)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            return results

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def get_user_by_email_with_roles(
        self, email: str, required_roles: List[str]
    ) -> Optional[UserData]:
        """
        Get user by email with role filtering using JSONB queries.

        Uses PostgreSQL's JSONB operators for efficient role-based lookups.
        """
        start_time = datetime.now(timezone.utc)
        operation = "get_user_by_email_with_roles"

        try:
            user_data = await self.db_client.get_user_with_roles(email, required_roles)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            return user_data

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def bulk_update_user_preferences(
        self, updates: List[Tuple[str, Dict[str, Any]]]
    ) -> int:
        """
        Bulk update user preferences using PostgreSQL JSONB operations.

        Efficiently updates multiple users' preferences in batch.
        """
        start_time = datetime.now(timezone.utc)
        operation = "bulk_update_user_preferences"

        try:
            count = await self.db_client.bulk_update_user_preferences(updates)

            # Record performance metric
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(operation, processing_time)

            return count

        except Exception as e:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            self._record_operation_time(f"{operation}_error", processing_time)
            raise

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        metrics = {}

        for operation, times in self._operation_times.items():
            if times:
                metrics[operation] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "p95_ms": sorted(times)[int(len(times) * 0.95)]
                    if len(times) > 20
                    else max(times),
                }

        # Add database statistics
        db_stats = await self.db_client.get_authentication_stats()
        metrics["database_stats"] = db_stats

        # Add session statistics
        session_stats = await self.session_manager.get_session_statistics()
        metrics["session_stats"] = session_stats

        return metrics

    def _validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against requirements."""
        errors = []

        if not password:
            errors.append("Password is required")
            return False, errors

        if len(password) < self.config.security.min_password_length:
            errors.append(
                f"Password must be at least {self.config.security.min_password_length} characters long"
            )

        if self.config.security.require_password_complexity:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

            if not has_upper:
                errors.append("Password must contain at least one uppercase letter")
            if not has_lower:
                errors.append("Password must contain at least one lowercase letter")
            if not has_digit:
                errors.append("Password must contain at least one digit")
            if not has_special:
                errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors

    async def _increment_failed_attempts(self, user_data: UserData) -> None:
        """Increment failed login attempts with optimized query."""
        try:
            async with self.db_client.session_factory() as session:
                # Use atomic increment operation
                result = await session.execute(
                    text(
                        """
                    UPDATE auth_users
                    SET failed_login_attempts = failed_login_attempts + 1,
                        locked_until = CASE
                            WHEN failed_login_attempts + 1 >= :max_attempts
                            THEN NOW() + INTERVAL ':lockout_minutes minutes'
                            ELSE locked_until
                        END,
                        updated_at = NOW()
                    WHERE user_id = :user_id
                    RETURNING failed_login_attempts, locked_until
                """
                    ),
                    {
                        "user_id": user_data.user_id,
                        "max_attempts": self.config.security.max_failed_attempts,
                        "lockout_minutes": self.config.security.lockout_duration_minutes,
                    },
                )

                row = result.fetchone()
                if row:
                    user_data.failed_login_attempts = row.failed_login_attempts
                    user_data.locked_until = row.locked_until

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to increment failed attempts: {e}")

    async def _handle_successful_auth(
        self, user_data: UserData, password_hash: str
    ) -> None:
        """Handle successful authentication updates."""
        try:
            async with self.db_client.session_factory() as session:
                # Reset failed attempts and update last login
                await session.execute(
                    text(
                        """
                    UPDATE auth_users
                    SET failed_login_attempts = 0,
                        locked_until = NULL,
                        last_login_at = NOW(),
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """
                    ),
                    {"user_id": user_data.user_id},
                )

                # Check if password needs rehashing
                if self.password_hasher.needs_rehash(password_hash):
                    new_hash = self.password_hasher.hash_password(password_hash)
                    await session.execute(
                        text(
                            """
                        UPDATE auth_password_hashes
                        SET password_hash = :password_hash,
                            updated_at = NOW()
                        WHERE user_id = :user_id
                    """
                        ),
                        {
                            "user_id": user_data.user_id,
                            "password_hash": new_hash,
                        },
                    )

                await session.commit()

                # Update user data object
                user_data.failed_login_attempts = 0
                user_data.locked_until = None
                user_data.last_login_at = datetime.now(timezone.utc)
                user_data.updated_at = datetime.now(timezone.utc)

        except Exception as e:
            self.logger.error(f"Failed to handle successful auth: {e}")

    async def _log_failed_auth(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str,
        start_time: datetime,
    ) -> None:
        """Log failed authentication attempt."""
        try:
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000

            # Log to database if audit logging is enabled
            if self.config.security.enable_audit_logging:
                event = AuthEvent(
                    event_type=AuthEventType.LOGIN_FAILED,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message=reason,
                    processing_time_ms=processing_time,
                )
                await self.db_client.store_auth_event(event)

        except Exception as e:
            self.logger.error(f"Failed to log failed auth: {e}")

    def _record_operation_time(self, operation: str, time_ms: float) -> None:
        """Record operation time for performance monitoring."""
        if operation not in self._operation_times:
            self._operation_times[operation] = []

        # Keep only recent measurements (last 1000)
        times = self._operation_times[operation]
        times.append(time_ms)
        if len(times) > 1000:
            times.pop(0)

    async def close(self) -> None:
        """Clean up resources."""
        try:
            await self.session_manager.stop_background_tasks()
            await self.db_client.close()
            self.logger.info("Optimized core authenticator closed")
        except Exception as e:
            self.logger.error(f"Error closing optimized authenticator: {e}")
