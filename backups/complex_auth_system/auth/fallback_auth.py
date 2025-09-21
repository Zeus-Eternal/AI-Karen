"""
Fallback Authentication System

This module provides a fallback authentication system that works without PostgreSQL
for development and testing purposes. It uses SQLite as a local database and provides
the same interface as the production authentication system.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import bcrypt

from ai_karen_engine.auth.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    PasswordValidationError,
    SessionExpiredError,
    SessionNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ai_karen_engine.auth.models import AuthEvent, AuthEventType, SessionData, UserData


class SQLiteFallbackAuth:
    """
    SQLite-based fallback authentication system.

    This provides the same interface as the production PostgreSQL system
    but uses SQLite for local development when PostgreSQL is not available.
    """

    def __init__(self, db_path: str = "data/fallback_auth.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"{__name__}.SQLiteFallbackAuth")
        self._initialized = False

        # In-memory session storage for simplicity
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_tokens

        self.logger.info(f"SQLite fallback auth initialized: {self.db_path}")

    async def initialize(self) -> None:
        """Initialize the SQLite database schema."""
        if self._initialized:
            return

        try:
            await self._create_schema()
            await self._create_default_users()
            self._initialized = True
            self.logger.info("SQLite fallback auth schema initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize SQLite fallback auth: {e}")
            raise

    async def _create_schema(self) -> None:
        """Create SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    roles TEXT DEFAULT '["user"]',
                    tenant_id TEXT DEFAULT 'default',
                    preferences TEXT DEFAULT '{}',
                    is_verified BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    two_factor_secret TEXT
                )
            """
            )

            # Auth events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    email TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_token TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    details TEXT DEFAULT '{}',
                    risk_score REAL DEFAULT 0.0
                )
            """
            )

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_events_user ON auth_events(user_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_auth_events_type ON auth_events(event_type)"
            )

            conn.commit()

        finally:
            conn.close()

    async def _create_default_users(self) -> None:
        """Create default admin and demo users."""
        # Create admin user
        try:
            await self.create_user(
                email="admin@ai-karen.local",
                password="admin123",
                full_name="System Administrator",
                roles=["admin", "user"],
            )
            self.logger.info("Created default admin user: admin@ai-karen.local")
        except UserAlreadyExistsError:
            pass  # User already exists

        # Create demo user
        try:
            await self.create_user(
                email="demo@ai-karen.local",
                password="demo123",
                full_name="Demo User",
                roles=["user"],
            )
            self.logger.info("Created default demo user: demo@ai-karen.local")
        except UserAlreadyExistsError:
            pass  # User already exists

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def _validate_password(self, password: str) -> bool:
        """Validate password complexity."""
        if len(password) < 8:
            return False

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        return has_upper and has_lower and has_digit and has_special

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenant_id: str = "default",
        **kwargs,
    ) -> UserData:
        """Create a new user."""
        await self.initialize()

        if not self._validate_password(password):
            raise PasswordValidationError(
                "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
            )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                raise UserAlreadyExistsError(f"User with email {email} already exists")

            # Create user
            user_id = str(uuid4())
            password_hash = self._hash_password(password)

            cursor.execute(
                """
                INSERT INTO users (
                    user_id, email, password_hash, full_name, roles, tenant_id,
                    is_verified, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    email,
                    password_hash,
                    full_name,
                    json.dumps(roles or ["user"]),
                    tenant_id,
                    True,
                    True,
                    datetime.utcnow(),
                    datetime.utcnow(),
                ),
            )

            conn.commit()

            # Log event
            await self._log_auth_event(
                AuthEventType.USER_CREATED, user_id=user_id, email=email, success=True
            )

            return UserData(
                user_id=user_id,
                email=email,
                full_name=full_name,
                roles=roles or ["user"],
                tenant_id=tenant_id,
                is_verified=True,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        finally:
            conn.close()

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
    ) -> Optional[UserData]:
        """Authenticate a user with email and password."""
        await self.initialize()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user
            cursor.execute(
                """
                SELECT user_id, email, password_hash, full_name, roles, tenant_id,
                       is_verified, is_active, failed_login_attempts, locked_until
                FROM users WHERE email = ?
            """,
                (email,),
            )

            row = cursor.fetchone()
            if not row:
                await self._log_auth_event(
                    AuthEventType.LOGIN_FAILED,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message="User not found",
                )
                raise InvalidCredentialsError("Invalid credentials")

            (
                user_id,
                email,
                password_hash,
                full_name,
                roles_json,
                tenant_id,
                is_verified,
                is_active,
                failed_attempts,
                locked_until,
            ) = row

            # Check if account is locked
            if locked_until:
                locked_until_dt = datetime.fromisoformat(locked_until)
                if datetime.utcnow() < locked_until_dt:
                    raise AccountLockedError(f"Account locked until {locked_until}")

            # Check if account is active
            if not is_active:
                raise InvalidCredentialsError("Account is disabled")

            # Verify password
            if not self._verify_password(password, password_hash):
                # Increment failed attempts
                failed_attempts += 1
                locked_until_new = None

                if failed_attempts >= 5:  # Lock after 5 failed attempts
                    locked_until_new = (
                        datetime.utcnow() + timedelta(minutes=15)
                    ).isoformat()

                cursor.execute(
                    """
                    UPDATE users SET failed_login_attempts = ?, locked_until = ?, updated_at = ?
                    WHERE user_id = ?
                """,
                    (failed_attempts, locked_until_new, datetime.utcnow(), user_id),
                )
                conn.commit()

                await self._log_auth_event(
                    AuthEventType.LOGIN_FAILED,
                    user_id=user_id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message="Invalid password",
                )

                if locked_until_new:
                    raise AccountLockedError(
                        "Account locked due to too many failed attempts"
                    )
                else:
                    raise InvalidCredentialsError("Invalid credentials")

            # Reset failed attempts on successful login
            cursor.execute(
                """
                UPDATE users SET failed_login_attempts = 0, locked_until = NULL,
                               last_login_at = ?, updated_at = ?
                WHERE user_id = ?
            """,
                (datetime.utcnow(), datetime.utcnow(), user_id),
            )
            conn.commit()

            # Log successful login
            await self._log_auth_event(
                AuthEventType.LOGIN_SUCCESS,
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
            )

            return UserData(
                user_id=user_id,
                email=email,
                full_name=full_name,
                roles=json.loads(roles_json),
                tenant_id=tenant_id,
                is_verified=bool(is_verified),
                is_active=bool(is_active),
                last_login_at=datetime.utcnow(),
            )

        finally:
            conn.close()

    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
    ) -> SessionData:
        """Create a new session for a user."""
        await self.initialize()

        # Generate session token
        session_token = f"session_{uuid4().hex}"
        access_token = f"access_{uuid4().hex}"
        refresh_token = f"refresh_{uuid4().hex}"

        # Create session data
        session_data = SessionData(
            session_token=session_token,
            access_token=access_token,
            refresh_token=refresh_token,
            user_data=user_data,
            expires_in=24 * 3600,  # 24 hours
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
        )

        # Store session
        self.sessions[session_token] = session_data

        # Track user sessions
        if user_data.user_id not in self.user_sessions:
            self.user_sessions[user_data.user_id] = []
        self.user_sessions[user_data.user_id].append(session_token)

        # Log session creation
        await self._log_auth_event(
            AuthEventType.SESSION_CREATED,
            user_id=user_data.user_id,
            email=user_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            session_token=session_token,
            success=True,
        )

        return session_data

    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs,
    ) -> Optional[UserData]:
        """Validate a session token."""
        await self.initialize()

        session = self.sessions.get(session_token)
        if not session:
            return None

        # Check if session is expired
        if session.is_expired():
            # Remove expired session
            del self.sessions[session_token]
            if session.user_data.user_id in self.user_sessions:
                self.user_sessions[session.user_data.user_id] = [
                    s
                    for s in self.user_sessions[session.user_data.user_id]
                    if s != session_token
                ]
            return None

        # Update last accessed
        session.update_last_accessed()

        return session.user_data

    async def invalidate_session(
        self, session_token: str, reason: str = "manual", **kwargs
    ) -> bool:
        """Invalidate a session."""
        await self.initialize()

        session = self.sessions.get(session_token)
        if not session:
            return False

        # Remove session
        del self.sessions[session_token]

        # Remove from user sessions
        if session.user_data.user_id in self.user_sessions:
            self.user_sessions[session.user_data.user_id] = [
                s
                for s in self.user_sessions[session.user_data.user_id]
                if s != session_token
            ]

        # Log session invalidation
        await self._log_auth_event(
            AuthEventType.SESSION_INVALIDATED,
            user_id=session.user_data.user_id,
            email=session.user_data.email,
            session_token=session_token,
            success=True,
            details={"reason": reason},
        )

        return True

    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user by email address."""
        await self.initialize()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT user_id, email, full_name, roles, tenant_id, is_verified, is_active,
                       created_at, updated_at, last_login_at
                FROM users WHERE email = ?
            """,
                (email,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            (
                user_id,
                email,
                full_name,
                roles_json,
                tenant_id,
                is_verified,
                is_active,
                created_at,
                updated_at,
                last_login_at,
            ) = row

            return UserData(
                user_id=user_id,
                email=email,
                full_name=full_name,
                roles=json.loads(roles_json),
                tenant_id=tenant_id,
                is_verified=bool(is_verified),
                is_active=bool(is_active),
                created_at=datetime.fromisoformat(created_at) if created_at else None,
                updated_at=datetime.fromisoformat(updated_at) if updated_at else None,
                last_login_at=datetime.fromisoformat(last_login_at)
                if last_login_at
                else None,
            )

        finally:
            conn.close()

    async def _log_auth_event(
        self,
        event_type: AuthEventType,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: str = "unknown",
        user_agent: str = "",
        session_token: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        details: Optional[Dict] = None,
        risk_score: float = 0.0,
    ) -> None:
        """Log an authentication event."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO auth_events (
                    event_id, event_type, user_id, email, ip_address, user_agent,
                    session_token, success, error_message, details, risk_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid4()),
                    event_type.value,
                    user_id,
                    email,
                    ip_address,
                    user_agent,
                    session_token,
                    success,
                    error_message,
                    json.dumps(details or {}),
                    risk_score,
                ),
            )

            conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to log auth event: {e}")
        finally:
            conn.close()

    async def get_auth_statistics(self) -> Dict[str, int]:
        """Get authentication statistics."""
        await self.initialize()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get user counts
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            active_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE is_verified = 1")
            verified_users = cursor.fetchone()[0]

            # Get session count
            active_sessions = len(
                [s for s in self.sessions.values() if not s.is_expired()]
            )

            # Get recent events
            cursor.execute(
                """
                SELECT COUNT(*) FROM auth_events
                WHERE event_type = 'LOGIN_FAILED' AND timestamp > datetime('now', '-1 hour')
            """
            )
            failed_logins_last_hour = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM auth_events
                WHERE event_type = 'LOGIN_SUCCESS' AND timestamp > datetime('now', '-1 hour')
            """
            )
            successful_logins_last_hour = cursor.fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users,
                "active_sessions": active_sessions,
                "failed_logins_last_hour": failed_logins_last_hour,
                "successful_logins_last_hour": successful_logins_last_hour,
            }

        finally:
            conn.close()


# Global fallback auth instance
_fallback_auth: Optional[SQLiteFallbackAuth] = None


def get_fallback_auth() -> SQLiteFallbackAuth:
    """Get the global fallback authentication instance."""
    global _fallback_auth
    if _fallback_auth is None:
        _fallback_auth = SQLiteFallbackAuth()
    return _fallback_auth


async def test_fallback_auth():
    """Test the fallback authentication system."""
    print("🧪 Testing SQLite Fallback Authentication System")
    print("=" * 50)

    auth = get_fallback_auth()
    await auth.initialize()

    try:
        # Test user creation
        print("1. Testing user creation...")
        user = await auth.create_user(
            email="test@example.com", password="TestPassword123!", full_name="Test User"
        )
        print(f"✅ Created user: {user.email}")

        # Test authentication
        print("2. Testing authentication...")
        authenticated_user = await auth.authenticate_user(
            email="test@example.com",
            password="TestPassword123!",
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )
        print(f"✅ Authenticated user: {authenticated_user.email}")

        # Test session creation
        print("3. Testing session creation...")
        session = await auth.create_session(
            user_data=authenticated_user,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )
        print(f"✅ Created session: {session.session_token[:16]}...")

        # Test session validation
        print("4. Testing session validation...")
        validated_user = await auth.validate_session(
            session_token=session.session_token,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )
        print(f"✅ Validated session for user: {validated_user.email}")

        # Test statistics
        print("5. Testing statistics...")
        stats = await auth.get_auth_statistics()
        print(f"✅ Statistics: {stats}")

        print("\n🎉 All fallback authentication tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_fallback_auth())
