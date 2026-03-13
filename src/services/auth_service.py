"""
Authentication Service for CoPilot Architecture.

This service provides comprehensive authentication functionality including
user management, session management, and token validation.
"""

import asyncio
import hashlib
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.models import AuthUser, AuthSession, Tenant

logger = get_logger(__name__)


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    SECURITY_OFFICER = "security_officer"
    AGENT = "agent"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class UserAccount:
    """User account data structure."""
    id: str
    email: str
    full_name: str
    password_hash: str
    roles: List[UserRole] = field(default_factory=list)
    status: UserStatus = UserStatus.ACTIVE
    is_verified: bool = True
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    password_changed_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    locked_until: Optional[datetime] = None
    failed_login_attempts: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)
    tenant_id: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Session data structure."""
    id: str
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = "unknown"
    user_agent: str = ""
    device_fingerprint: str = ""
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthConfig(ServiceConfig):
    """Authentication configuration."""
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_require_complexity: bool = True
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30
    session_timeout_hours: int = 24
    enable_two_factor: bool = True
    bcrypt_rounds: int = 12
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "auth_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class AuthService(BaseService):
    """
    Authentication Service for CoPilot Architecture.
    
    This service provides comprehensive authentication functionality including
    user management, session management, and token validation.
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize the Authentication Service."""
        super().__init__(config or AuthConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        self._db_client: Optional[MultiTenantPostgresClient] = None
        
        # Thread-safe data structures
        self._active_sessions: Dict[str, Session] = {}
        self._user_cache: Dict[str, UserAccount] = {}
        
        # Load configuration from environment
        self._load_config_from_env()
    
    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        if "AUTH_JWT_SECRET_KEY" in os.environ:
            self.config.jwt_secret_key = os.environ["AUTH_JWT_SECRET_KEY"]
        
        if "AUTH_JWT_ALGORITHM" in os.environ:
            self.config.jwt_algorithm = os.environ["AUTH_JWT_ALGORITHM"]
        
        if "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES" in os.environ:
            self.config.access_token_expire_minutes = int(os.environ["AUTH_ACCESS_TOKEN_EXPIRE_MINUTES"])
        
        if "AUTH_REFRESH_TOKEN_EXPIRE_DAYS" in os.environ:
            self.config.refresh_token_expire_days = int(os.environ["AUTH_REFRESH_TOKEN_EXPIRE_DAYS"])
        
        if "AUTH_PASSWORD_MIN_LENGTH" in os.environ:
            self.config.password_min_length = int(os.environ["AUTH_PASSWORD_MIN_LENGTH"])
        
        if "AUTH_MAX_FAILED_LOGIN_ATTEMPTS" in os.environ:
            self.config.max_failed_login_attempts = int(os.environ["AUTH_MAX_FAILED_LOGIN_ATTEMPTS"])
        
        if "AUTH_ACCOUNT_LOCKOUT_MINUTES" in os.environ:
            self.config.account_lockout_minutes = int(os.environ["AUTH_ACCOUNT_LOCKOUT_MINUTES"])
    
    async def initialize(self) -> None:
        """Initialize the Authentication Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Validate configuration
                self._validate_config()
                
                # Initialize database tables if needed
                await self._ensure_database_tables()
                
                # Create default admin user if it doesn't exist
                await self._ensure_default_admin_user()
                
                self._initialized = True
                logger.info("Authentication Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Authentication Service: {e}")
                raise RuntimeError(f"Authentication Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.config.jwt_secret_key or self.config.jwt_secret_key == "change-me-in-production":
            logger.warning("JWT secret key is not configured properly. Please set AUTH_JWT_SECRET_KEY environment variable.")
        
        if self.config.password_min_length < 8:
            logger.warning("Password minimum length is less than 8 characters. This is not recommended.")
        
        if self.config.max_failed_login_attempts < 3:
            logger.warning("Maximum failed login attempts is less than 3. This may reduce security.")
    
    async def _ensure_database_tables(self) -> None:
        """Ensure database tables exist."""
        # This would typically create the necessary tables
        # For now, we'll assume they exist
        logger.debug("Database tables check completed")
    
    async def _ensure_default_admin_user(self) -> None:
        """Ensure default admin user exists."""
        try:
            # Check if admin user exists
            admin_user = await self.get_user_by_email("admin@kari.ai")
            if not admin_user:
                # Create default admin user
                default_password = "password123"  # This should be changed in production
                await self.create_user(
                    email="admin@kari.ai",
                    password=default_password,
                    full_name="System Administrator",
                    roles=[UserRole.ADMIN, UserRole.USER],
                    is_verified=True
                )
                logger.info("Created default admin user")
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set the database session for the service."""
        self._db_session = session

    def _get_db_client(self) -> MultiTenantPostgresClient:
        """Return a cached database client for fallback sessions."""
        if self._db_client is None:
            self._db_client = MultiTenantPostgresClient()
        return self._db_client

    @asynccontextmanager
    async def _session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a session scope using injected or fallback client sessions."""
        if self._db_session is not None:
            yield self._db_session
            return
        async with self._get_db_client().get_async_session() as session:
            yield session

    async def _resolve_tenant_id(
        self,
        session: AsyncSession,
        tenant_identifier: Optional[str],
    ) -> Optional[uuid.UUID]:
        """Resolve tenant identifier to UUID, if available."""
        if not tenant_identifier:
            return None
        try:
            return uuid.UUID(str(tenant_identifier))
        except ValueError:
            pass

        result = await session.execute(
            select(Tenant).where(Tenant.slug == tenant_identifier)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant.id

        logger.warning("Unknown tenant identifier '%s'; using default tenant", tenant_identifier)
        return None

    def _build_user_account(self, auth_user: AuthUser) -> UserAccount:
        """Map AuthUser ORM model to UserAccount."""
        now = datetime.utcnow()
        status = UserStatus.ACTIVE if auth_user.is_active else UserStatus.INACTIVE
        if auth_user.locked_until and auth_user.locked_until > now:
            status = UserStatus.LOCKED

        return UserAccount(
            id=str(auth_user.user_id),
            email=auth_user.email,
            full_name=auth_user.full_name or "",
            password_hash=auth_user.password_hash,
            tenant_id=str(auth_user.tenant_id) if auth_user.tenant_id else "default",
            roles=list(auth_user.roles or []),
            preferences=auth_user.preferences or {},
            is_verified=auth_user.is_verified,
            two_factor_enabled=auth_user.two_factor_enabled,
            created_at=auth_user.created_at or now,
            updated_at=auth_user.updated_at or now,
            last_login=auth_user.last_login,
            failed_login_attempts=auth_user.failed_login_attempts,
            locked_until=auth_user.locked_until,
            status=status,
        )

    async def _persist_auth_session(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str,
    ) -> None:
        """Persist a session record to the database when possible."""
        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            logger.warning("Skipping DB session persistence; invalid user id: %s", user_id)
            return

        try:
            async with self._session_scope() as db_session:
                db_session.add(
                    AuthSession(
                        session_token=uuid.uuid4(),
                        user_id=user_uuid,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        expires_in=self.config.refresh_token_expire_days * 24 * 60 * 60,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_fingerprint=device_fingerprint,
                        is_active=True,
                    )
                )
                await db_session.flush()
        except Exception as e:
            logger.error("Failed to persist session to database: %s", e)
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Tuple[Optional[UserAccount], Optional[str], Optional[str]]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: User password
            ip_address: IP address of the client
            user_agent: User agent string
            
        Returns:
            Tuple of (user, access_token, refresh_token) or (None, None, None) if authentication fails
        """
        if not self._initialized:
            await self.initialize()
        
        # Note: _db_session check removed - method handles None case with temporary client
        
        try:
            # Get user by email
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning("Authentication failed: user not found - %s", email)
                return None, None, "Invalid credentials"
            
            # Check if account is locked
            if user.status == UserStatus.LOCKED:
                if user.locked_until and user.locked_until > datetime.utcnow():
                    logger.warning("Authentication failed: account locked - %s", email)
                    return None, None, "Account locked"
                else:
                    # Account lockout has expired, unlock it
                    await self._unlock_user_account(user.id)
            
            # Check if account is active
            if user.status != UserStatus.ACTIVE:
                logger.warning("Authentication failed: account not active - %s", email)
                return None, None, "Account inactive"
            
            # Verify password
            if not self._verify_password(password, user.password_hash):
                # Increment failed login attempts
                await self._increment_failed_login_attempts(user.id)
                logger.warning("Authentication failed: invalid password - %s", email)
                return None, None, "Invalid credentials"
            
            # Check if email is verified
            if not user.is_verified:
                logger.warning("Authentication failed: email not verified - %s", email)
                return None, None, "Email not verified"
            
            # Reset failed login attempts on successful authentication
            await self._reset_failed_login_attempts(user.id)
            
            # Update last login
            await self._update_last_login(user.id)
            
            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token()
            
            # Create session
            device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
            session = Session(
                id=secrets.token_urlsafe(32),
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint
            )
            
            # Store session
            self._active_sessions[session.id] = session

            await self._persist_auth_session(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
            )
            
            logger.info("User authenticated successfully - %s", email)
            return user, access_token, refresh_token
            
        except Exception as e:
            logger.error("Error authenticating user: %s", e)
            return None, None, "Authentication failed"
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        *,
        tenant_id: Optional[str] = None,
        roles: Optional[List[UserRole]] = None,
        is_verified: bool = False
    ) -> Tuple[Optional[UserAccount], Optional[str]]:
        """
        Create a new user.
        
        Args:
            email: User email
            password: User password
            full_name: User full name
            roles: List of user roles
            is_verified: Whether the user is verified
            
        Returns:
            Tuple of (user, error) or (None, error_message) if creation fails
        """
        if not self._initialized:
            await self.initialize()
        
        # Note: _db_session check removed - method handles None case with temporary client
        
        try:
            # Validate email
            if not self._validate_email(email):
                return None, "Invalid email address"
            
            # Validate password
            password_error = self._validate_password(password)
            if password_error:
                return None, password_error
            
            async with self._session_scope() as session:
                # Check if user already exists
                existing_user = await session.execute(
                    select(AuthUser).where(AuthUser.email == email)
                )
                if existing_user.scalar_one_or_none():
                    return None, "User with this email already exists"

                # Hash password
                password_hash = self._hash_password(password)

                resolved_tenant_id = await self._resolve_tenant_id(session, tenant_id)
                roles_payload = [role.value if isinstance(role, UserRole) else str(role) for role in (roles or [UserRole.USER])]

                auth_user = AuthUser(
                    user_id=uuid.uuid4(),
                    email=email,
                    full_name=full_name,
                    password_hash=password_hash,
                    tenant_id=resolved_tenant_id,
                    roles=roles_payload,
                    preferences={},
                    is_verified=is_verified,
                    is_active=True,
                )
                session.add(auth_user)
                await session.flush()

                user = self._build_user_account(auth_user)
                if not is_verified:
                    user.status = UserStatus.PENDING_VERIFICATION

                self._user_cache[user.id] = user

            logger.info("User created successfully - %s", email)
            return user, None
            
        except Exception as e:
            logger.error("Error creating user: %s", e)
            return None, str(e)
    
    async def validate_token(self, token: str) -> Optional[UserAccount]:
        """
        Validate an access token.
        
        Args:
            token: Access token to validate
            
        Returns:
            User account if token is valid, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            # Check if token is expired
            if payload.get("exp", 0) < time.time():
                logger.warning("Token expired")
                return None
            
            # Get user ID from token
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("Invalid token: missing user ID")
                return None
            
            # Get user
            user = await self.get_user_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                return None
            
            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"User not active: {user_id}")
                return None
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (new_access_token, error) or (None, error_message) if refresh fails
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._session_scope() as db_session:
                result = await db_session.execute(
                    select(AuthSession).where(
                        AuthSession.refresh_token == refresh_token,
                        AuthSession.is_active == True,
                    )
                )
                db_auth_session = result.scalar_one_or_none()
                if not db_auth_session:
                    return None, "Invalid refresh token"

                if db_auth_session.expires_in:
                    expires_at = db_auth_session.created_at + timedelta(
                        seconds=db_auth_session.expires_in
                    )
                    if expires_at < datetime.utcnow():
                        db_auth_session.is_active = False
                        db_auth_session.invalidated_at = datetime.utcnow()
                        db_auth_session.invalidation_reason = "refresh_token_expired"
                        await db_session.flush()
                        return None, "Session expired"

                user_result = await db_session.execute(
                    select(AuthUser).where(AuthUser.user_id == db_auth_session.user_id)
                )
                auth_user = user_result.scalar_one_or_none()
                if not auth_user or not auth_user.is_active:
                    return None, "User not found or inactive"

                new_access_token = self._generate_access_token_by_id(str(auth_user.user_id))
                db_auth_session.access_token = new_access_token
                db_auth_session.last_accessed = datetime.utcnow()
                await db_session.flush()

                logger.info("Access token refreshed successfully for user %s", auth_user.user_id)
                return new_access_token, None

        except Exception as e:
            logger.warning("Database refresh token failed, falling back to memory: %s", e)

        # Fallback to in-memory sessions
        try:
            session = None
            for s in self._active_sessions.values():
                if s.refresh_token == refresh_token and s.is_active:
                    session = s
                    break

            if not session:
                return None, "Invalid refresh token"

            if session.expires_at < datetime.utcnow():
                session.is_active = False
                return None, "Session expired"

            user = await self.get_user_by_id(session.user_id)
            if not user or user.status != UserStatus.ACTIVE:
                return None, "User not found or inactive"

            new_access_token = self._generate_access_token(user)
            session.access_token = new_access_token
            session.last_used = datetime.utcnow()

            logger.info("Access token refreshed successfully for user %s", user.id)
            return new_access_token, None

        except Exception as e:
            logger.error("Error refreshing access token: %s", e)
            return None, str(e)
    
    async def logout(self, refresh_token: str) -> None:
        """
        Logout a user by invalidating their refresh token.
        
        Args:
            refresh_token: Refresh token to invalidate
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._session_scope() as db_session:
                result = await db_session.execute(
                    select(AuthSession).where(AuthSession.refresh_token == refresh_token)
                )
                db_auth_session = result.scalar_one_or_none()
                if db_auth_session:
                    db_auth_session.is_active = False
                    db_auth_session.invalidated_at = datetime.utcnow()
                    db_auth_session.invalidation_reason = "logout"
                    await db_session.flush()
                    logger.info("User logged out successfully: %s", db_auth_session.user_id)
                    return
        except Exception as e:
            logger.warning("Database logout failed, falling back to memory: %s", e)

        try:
            for session in self._active_sessions.values():
                if session.refresh_token == refresh_token:
                    session.is_active = False
                    logger.info("User logged out successfully: %s", session.user_id)
                    break
        except Exception as e:
            logger.error("Error during logout: %s", e)
    
    async def get_user(self, identifier: str) -> Optional[UserAccount]:
        """
        Get a user by email or ID.
        
        Args:
            identifier: User email or ID
            
        Returns:
            User account if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        # Try to get by ID first
        user = await self.get_user_by_id(identifier)
        if user:
            return user
        
        # Try to get by email
        return await self.get_user_by_email(identifier)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserAccount]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User account if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            user_uuid = uuid.UUID(str(user_id))
        except ValueError:
            return None

        try:
            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return None

                user = self._build_user_account(auth_user)
                self._user_cache[user.id] = user
                return user
        except Exception as e:
            logger.error("Error fetching user by id: %s", e)
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            User account if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        # Check cache first
        for user in self._user_cache.values():
            if user.email == email:
                return user

        try:
            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(
                        AuthUser.email == email,
                        AuthUser.is_active == True,
                    )
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return None

                user = self._build_user_account(auth_user)
                self._user_cache[user.id] = user
                return user
        except Exception as e:
            logger.error("Error fetching user by email: %s", e)
            return None
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: str = ""
    ) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            ip_address: IP address of the client
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            
        Returns:
            New session
        """
        if not self._initialized:
            await self.initialize()
        
        # Generate tokens
        access_token = self._generate_access_token_by_id(user_id)
        refresh_token = self._generate_refresh_token()
        
        # Create session
        session = Session(
            id=secrets.token_urlsafe(32),
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint or self._generate_device_fingerprint(user_agent, ip_address)
        )
        
        # Store session
        self._active_sessions[session.id] = session

        await self._persist_auth_session(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=session.device_fingerprint,
        )
        
        logger.info("Session created for user %s", user_id)
        return session
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[UserAccount]:
        """
        Validate a session token.
        
        Args:
            session_token: Session token to validate
            ip_address: IP address of the client
            user_agent: User agent string
            
        Returns:
            User account if session is valid, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._session_scope() as db_session:
                result = await db_session.execute(
                    select(AuthSession).where(
                        AuthSession.access_token == session_token,
                        AuthSession.is_active == True,
                    )
                )
                db_auth_session = result.scalar_one_or_none()
                if not db_auth_session:
                    return None

                try:
                    payload = jwt.decode(
                        session_token,
                        self.config.jwt_secret_key,
                        algorithms=[self.config.jwt_algorithm],
                    )
                    if payload.get("exp", 0) < time.time():
                        return None
                except Exception:
                    return None

                if db_auth_session.device_fingerprint:
                    current_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
                    if db_auth_session.device_fingerprint != current_fingerprint:
                        logger.warning(
                            "Device fingerprint mismatch for session %s", db_auth_session.session_token
                        )

                db_auth_session.last_accessed = datetime.utcnow()
                await db_session.flush()

                user_result = await db_session.execute(
                    select(AuthUser).where(AuthUser.user_id == db_auth_session.user_id)
                )
                auth_user = user_result.scalar_one_or_none()
                if not auth_user or not auth_user.is_active:
                    return None

                user = self._build_user_account(auth_user)
                self._user_cache[user.id] = user
                return user
        except Exception as e:
            logger.warning("Database session validation failed, falling back to memory: %s", e)

        try:
            session = None
            for s in self._active_sessions.values():
                if s.access_token == session_token and s.is_active:
                    session = s
                    break

            if not session:
                return None

            if session.expires_at < datetime.utcnow():
                session.is_active = False
                return None

            if session.device_fingerprint:
                current_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
                if session.device_fingerprint != current_fingerprint:
                    logger.warning("Device fingerprint mismatch for session %s", session.id)

            session.last_used = datetime.utcnow()

            user = await self.get_user_by_id(session.user_id)
            if not user or user.status != UserStatus.ACTIVE:
                return None

            return user

        except Exception as e:
            logger.error("Error validating session: %s", e)
            return None
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=self.config.bcrypt_rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Password to verify
            password_hash: Hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_access_token(self, user: UserAccount) -> str:
        """
        Generate an access token for a user.
        
        Args:
            user: User account
            
        Returns:
            Access token
        """
        return self._generate_access_token_by_id(user.id)
    
    def _generate_access_token_by_id(self, user_id: str) -> str:
        """
        Generate an access token for a user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Access token
        """
        now = int(time.time())
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + (self.config.access_token_expire_minutes * 60),
            "type": "access"
        }
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def _generate_refresh_token(self) -> str:
        """
        Generate a refresh token.
        
        Returns:
            Refresh token
        """
        return secrets.token_urlsafe(64)
    
    def _generate_device_fingerprint(self, user_agent: str, ip: str) -> str:
        """
        Generate a device fingerprint from user agent and IP.
        
        Args:
            user_agent: User agent string
            ip: IP address
            
        Returns:
            Device fingerprint
        """
        data = f"{user_agent}:{ip}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def _validate_email(self, email: str) -> bool:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> Optional[str]:
        """
        Validate a password.
        
        Args:
            password: Password to validate
            
        Returns:
            None if password is valid, error message otherwise
        """
        if len(password) < self.config.password_min_length:
            return f"Password must be at least {self.config.password_min_length} characters long"
        
        if self.config.password_require_complexity:
            # Check for at least one uppercase, one lowercase, one digit, and one special character
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
            
            if not (has_upper and has_lower and has_digit and has_special):
                return "Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character"
        
        return None
    
    async def _increment_failed_login_attempts(self, user_id: str) -> None:
        """
        Increment failed login attempts for a user.
        
        Args:
            user_id: User ID
        """
        try:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                logger.warning("Invalid user id for failed login update: %s", user_id)
                return

            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return

                auth_user.failed_login_attempts = (auth_user.failed_login_attempts or 0) + 1
                if auth_user.failed_login_attempts >= self.config.max_failed_login_attempts:
                    auth_user.locked_until = datetime.utcnow() + timedelta(
                        minutes=self.config.account_lockout_minutes
                    )
                await session.flush()

                cached = self._user_cache.get(str(auth_user.user_id))
                if cached:
                    cached.failed_login_attempts = auth_user.failed_login_attempts
                    cached.locked_until = auth_user.locked_until
                    if cached.locked_until and cached.locked_until > datetime.utcnow():
                        cached.status = UserStatus.LOCKED

                logger.warning("Incremented failed login attempts for user %s", user_id)
        except Exception as e:
            logger.error("Failed to increment failed login attempts: %s", e)
    
    async def _reset_failed_login_attempts(self, user_id: str) -> None:
        """
        Reset failed login attempts for a user.
        
        Args:
            user_id: User ID
        """
        try:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                logger.warning("Invalid user id for failed login reset: %s", user_id)
                return

            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return

                auth_user.failed_login_attempts = 0
                auth_user.locked_until = None
                await session.flush()

                cached = self._user_cache.get(str(auth_user.user_id))
                if cached:
                    cached.failed_login_attempts = 0
                    cached.locked_until = None
                    if cached.status == UserStatus.LOCKED:
                        cached.status = UserStatus.ACTIVE

                logger.info("Reset failed login attempts for user %s", user_id)
        except Exception as e:
            logger.error("Failed to reset failed login attempts: %s", e)
    
    async def _lock_user_account(self, user_id: str) -> None:
        """
        Lock a user account.
        
        Args:
            user_id: User ID
        """
        try:
            locked_until = datetime.utcnow() + timedelta(
                minutes=self.config.account_lockout_minutes
            )
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                logger.warning("Invalid user id for lock: %s", user_id)
                return

            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return

                auth_user.locked_until = locked_until
                await session.flush()

                cached = self._user_cache.get(str(auth_user.user_id))
                if cached:
                    cached.locked_until = locked_until
                    cached.status = UserStatus.LOCKED

                logger.warning("Locked user account %s", user_id)
        except Exception as e:
            logger.error("Failed to lock user account: %s", e)
    
    async def _unlock_user_account(self, user_id: str) -> None:
        """
        Unlock a user account.
        
        Args:
            user_id: User ID
        """
        try:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                logger.warning("Invalid user id for unlock: %s", user_id)
                return

            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return

                auth_user.locked_until = None
                auth_user.failed_login_attempts = 0
                await session.flush()

                cached = self._user_cache.get(str(auth_user.user_id))
                if cached:
                    cached.locked_until = None
                    cached.failed_login_attempts = 0
                    cached.status = UserStatus.ACTIVE

                logger.info("Unlocked user account %s", user_id)
        except Exception as e:
            logger.error("Failed to unlock user account: %s", e)
    
    async def _update_last_login(self, user_id: str) -> None:
        """
        Update the last login time for a user.
        
        Args:
            user_id: User ID
        """
        try:
            try:
                user_uuid = uuid.UUID(str(user_id))
            except ValueError:
                logger.warning("Invalid user id for last login update: %s", user_id)
                return

            async with self._session_scope() as session:
                result = await session.execute(
                    select(AuthUser).where(AuthUser.user_id == user_uuid)
                )
                auth_user = result.scalar_one_or_none()
                if not auth_user:
                    return

                auth_user.last_login = datetime.utcnow()
                await session.flush()

                cached = self._user_cache.get(str(auth_user.user_id))
                if cached:
                    cached.last_login = auth_user.last_login

                logger.info("Updated last login time for user %s", user_id)
        except Exception as e:
            logger.error("Failed to update last login time: %s", e)
    
    async def health_check(self) -> bool:
        """
        Check the health of the Authentication Service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            # Check if we can create and validate a token
            test_user_id = "test_user"
            token = self._generate_access_token_by_id(test_user_id)
            
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            if payload.get("sub") != test_user_id:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Authentication Service health check failed: {e}")
            return False
    
    async def get_auth_stats(self) -> Dict[str, Any]:
            """
            Get authentication service statistics.

            Returns:
                Dictionary containing authentication statistics
            """
            try:
                from sqlalchemy import select, func, text
                from ai_karen_engine.database.models import AuthUser, AuthSession
                from ai_karen_engine.database.client import MultiTenantPostgresClient
                
                # Use existing session or create temporary client
                if not self._db_session:
                    try:
                        temp_client = MultiTenantPostgresClient()
                        async with temp_client.get_async_session() as session:
                            # Get user count
                            result = await session.execute(
                                select(func.count()).select_from(AuthUser)
                            )
                            total_users = result.scalar() or 0

                            # Get active user count
                            result = await session.execute(
                                select(func.count()).select_from(AuthUser).where(AuthUser.is_active == True)
                            )
                            active_users = result.scalar() or 0

                            # Get total session count
                            result = await session.execute(
                                select(func.count()).select_from(AuthSession)
                            )
                            total_sessions = result.scalar() or 0

                            # Get active session count (within last 24 hours)
                            result = await session.execute(
                                select(func.count()).select_from(AuthSession).where(
                                    AuthSession.is_active == True,
                                    AuthSession.last_used >= text("NOW() - INTERVAL '24 hours'")
                                )
                            )
                            active_sessions = result.scalar() or 0

                        return {
                            "total_users": total_users,
                            "active_users": active_users,
                            "total_sessions": total_sessions,
                            "active_sessions": active_sessions,
                            "service_status": "running" if self._initialized else "stopped"
                        }
                    except Exception as temp_error:
                        logger.warning(f"Could not use temporary database client: {temp_error}")
                        return {
                            "total_users": 0,
                            "active_users": 0,
                            "total_sessions": 0,
                            "active_sessions": 0,
                            "service_status": "error",
                            "error": "Database session not available"
                        }

                from sqlalchemy import select, func, text
                from ai_karen_engine.database.models import AuthUser, AuthSession

                # Get user count
                result = await self._db_session.execute(
                    select(func.count()).select_from(AuthUser)
                )
                total_users = result.scalar() or 0

                # Get active user count
                result = await self._db_session.execute(
                    select(func.count()).select_from(AuthUser).where(AuthUser.is_active == True)
                )
                active_users = result.scalar() or 0

                # Get total session count
                result = await self._db_session.execute(
                    select(func.count()).select_from(AuthSession)
                )
                total_sessions = result.scalar() or 0

                # Get active session count (within last 24 hours)
                result = await self._db_session.execute(
                    select(func.count()).select_from(AuthSession).where(
                        AuthSession.is_active == True,
                        AuthSession.last_used >= text("NOW() - INTERVAL '24 hours'")
                    )
                )
                active_sessions = result.scalar() or 0

                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "service_status": "running" if self._initialized else "stopped"
                }
            except Exception as e:
                logger.error(f"Failed to get auth stats: {e}")
                return {
                    "total_users": 0,
                    "active_users": 0,
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "service_status": "error",
                    "error": str(e)
                }
    
    async def is_first_run(self) -> bool:
            """
            Check if this is the first run (no users exist).

            Returns:
                True if no users exist, False otherwise
            """
            try:
                from sqlalchemy import select, func
                from ai_karen_engine.database.models import AuthUser
                from ai_karen_engine.database.client import MultiTenantPostgresClient
                
                # Use existing session or create temporary client
                if not self._db_session:
                    try:
                        temp_client = MultiTenantPostgresClient()
                        async with temp_client.get_async_session() as session:
                            result = await session.execute(
                                select(func.count()).select_from(AuthUser)
                            )
                            user_count = result.scalar() or 0
                            return user_count == 0
                    except Exception as temp_error:
                        logger.warning(f"Could not use temporary database client: {temp_error}")
                        return True  # Assume first run if database not available

                from sqlalchemy import select, func
                from ai_karen_engine.database.models import AuthUser

                result = await self._db_session.execute(
                    select(func.count()).select_from(AuthUser)
                )
                user_count = result.scalar() or 0

                return user_count == 0
            except Exception as e:
                logger.error(f"Failed to check first run status: {e}")
                return False
    
    async def create_first_admin(
        self,
        email: str,
        password: str,
        full_name: str
    ) -> UserAccount:
        """
        Create the first admin user (only works if no users exist).
        
        Args:
            email: Admin email address
            password: Admin password
            full_name: Admin full name
            
        Returns:
            Created UserAccount
            
        Raises:
            ValueError: If users already exist or creation fails
        """
        if not await self.is_first_run():
            raise ValueError("First-run setup has already been completed")
        
        # Create admin user with super_admin role
        user, error = await self.create_user(
            email=email,
            password=password,
            full_name=full_name,
            roles=[UserRole.ADMIN, UserRole.USER],
            is_verified=True
        )
        
        if not user:
            raise ValueError(f"Failed to create first admin user: {error}")
        
        logger.info(f"First admin user created: {email}")
        return user
    
    async def start(self) -> None:
        """Start the Authentication Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Authentication Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Authentication Service."""
        if not self._initialized:
            return
        
        # Clear active sessions
        self._active_sessions.clear()
        
        # Clear user cache
        self._user_cache.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Authentication Service stopped successfully")
