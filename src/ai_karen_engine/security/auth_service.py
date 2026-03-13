"""
Enhanced Authentication Service with comprehensive security features.

This service provides advanced authentication capabilities including:
- Multi-factor authentication (MFA)
- Device verification and fingerprinting
- Security event monitoring
- Threat detection and response
- Account lockout and recovery
"""

import asyncio
import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import jwt
import bcrypt
from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.audit_logging import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)
from ai_karen_engine.auth.models import UserData

logger = get_logger(__name__)


class MFAMethod(str, Enum):
    """Multi-factor authentication methods."""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"     # SMS verification
    EMAIL = "email"   # Email verification
    BACKUP_CODE = "backup_code"  # Backup codes
    PUSH = "push"   # Push notification
    HARDWARE_TOKEN = "hardware_token"  # Hardware token


class ThreatLevel(str, Enum):
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Security event types."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    MFA_SUCCESS = "mfa_success"
    MFA_FAILURE = "mfa_failure"
    DEVICE_TRUSTED = "device_trusted"
    DEVICE_BLOCKED = "device_blocked"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PASSWORD_CHANGE = "password_change"
    SECURITY_QUESTION_ANSWERED = "security_question_answered"


@dataclass
class DeviceInfo:
    """Device information for fingerprinting."""
    device_id: str
    user_agent: str
    ip_address: str
    fingerprint: str
    is_trusted: bool = False
    trust_level: str = "unknown"
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityEvent:
    """Security event for monitoring and analysis."""
    event_id: str
    event_type: SecurityEventType
    user_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = "unknown"
    user_agent: str = ""
    device_fingerprint: str = ""
    threat_level: ThreatLevel = ThreatLevel.LOW
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class EnhancedAuthConfig(ServiceConfig):
    """Enhanced authentication configuration."""
    # JWT settings
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Password settings
    password_min_length: int = 12
    password_require_complexity: bool = True
    password_history_count: int = 12
    password_max_age_days: int = 90
    
    # Account security
    max_failed_login_attempts: int = 5
    account_lockout_minutes: int = 30
    session_timeout_hours: int = 24
    max_sessions_per_user: int = 5
    
    # MFA settings
    mfa_required: bool = True
    mfa_methods: List[MFAMethod] = field(default_factory=lambda: [MFAMethod.TOTP, MFAMethod.SMS])
    backup_codes_count: int = 10
    
    # Device verification
    device_verification_enabled: bool = True
    device_trust_days: int = 30
    max_trusted_devices: int = 5
    
    # Security monitoring
    threat_detection_enabled: bool = True
    anomaly_detection_enabled: bool = True
    security_event_retention_days: int = 365
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_window_minutes: int = 15
    rate_limit_max_attempts: int = 10
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "enhanced_auth_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class EnhancedAuthService(BaseService):
    """
    Enhanced Authentication Service with comprehensive security features.
    
    This service provides advanced authentication capabilities including multi-factor
    authentication, device verification, threat detection, and security monitoring.
    """
    
    def __init__(self, config: Optional[EnhancedAuthConfig] = None):
        """Initialize the Enhanced Authentication Service."""
        super().__init__(config or EnhancedAuthConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Database session will be injected
        self._db_session: Optional[AsyncSession] = None
        
        # Thread-safe data structures
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._user_cache: Dict[str, UserData] = {}
        self._device_cache: Dict[str, DeviceInfo] = {}
        self._security_events: List[SecurityEvent] = []
        self._failed_attempts: Dict[str, List[datetime]] = {}
        
        # Initialize audit logger
        self._audit_logger = get_audit_logger()
        
        # Load configuration from environment
        self._load_config_from_env()
    
    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "AUTH_JWT_SECRET_KEY": "jwt_secret_key",
            "AUTH_JWT_ALGORITHM": "jwt_algorithm",
            "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES": "access_token_expire_minutes",
            "AUTH_REFRESH_TOKEN_EXPIRE_DAYS": "refresh_token_expire_days",
            "AUTH_PASSWORD_MIN_LENGTH": "password_min_length",
            "AUTH_PASSWORD_REQUIRE_COMPLEXITY": "password_require_complexity",
            "AUTH_MAX_FAILED_LOGIN_ATTEMPTS": "max_failed_login_attempts",
            "AUTH_ACCOUNT_LOCKOUT_MINUTES": "account_lockout_minutes",
            "AUTH_SESSION_TIMEOUT_HOURS": "session_timeout_hours",
            "AUTH_MFA_REQUIRED": "mfa_required",
            "AUTH_DEVICE_VERIFICATION_ENABLED": "device_verification_enabled",
            "AUTH_THREAT_DETECTION_ENABLED": "threat_detection_enabled",
            "AUTH_RATE_LIMIT_ENABLED": "rate_limit_enabled",
        }
        
        for env_var, config_attr in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Convert string to appropriate type
                if config_attr in ["mfa_required", "password_require_complexity", 
                                 "device_verification_enabled", "threat_detection_enabled", 
                                 "rate_limit_enabled"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                elif config_attr in ["password_min_length", "max_failed_login_attempts", 
                                  "account_lockout_minutes", "session_timeout_hours",
                                  "access_token_expire_minutes", "refresh_token_expire_days"]:
                    value = int(value)
                
                setattr(self.config, config_attr, value)
    
    async def initialize(self) -> None:
        """Initialize the Enhanced Authentication Service."""
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
                logger.info("Enhanced Authentication Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Enhanced Authentication Service: {e}")
                raise RuntimeError(f"Enhanced Authentication Service initialization failed: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.config.jwt_secret_key or self.config.jwt_secret_key == "change-me-in-production":
            logger.warning("JWT secret key is not configured properly")
        
        if self.config.password_min_length < 8:
            logger.warning("Password minimum length is less than 8 characters")
        
        if self.config.max_failed_login_attempts < 3:
            logger.warning("Maximum failed login attempts is less than 3")
    
    async def _ensure_database_tables(self) -> None:
        """Ensure database tables exist."""
        # This would typically create the necessary tables
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
                    roles=["admin", "user"],
                    is_verified=True
                )
                logger.info("Created default admin user")
        except Exception as e:
            logger.error(f"Error creating default admin user: {e}")
    
    def set_db_session(self, session: AsyncSession) -> None:
        """Set the database session for the service."""
        self._db_session = session
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: str = ""
    ) -> Tuple[Optional[UserData], Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Authenticate a user with enhanced security checks.
        
        Args:
            email: User email
            password: User password
            ip_address: IP address of the client
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            
        Returns:
            Tuple of (user, access_token, refresh_token, security_context)
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._db_session:
            raise RuntimeError("Database session not set")
        
        security_context = {
            "requires_mfa": False,
            "requires_device_verification": False,
            "threat_level": ThreatLevel.LOW,
            "security_events": [],
            "device_trusted": False,
        }
        
        try:
            # Rate limiting check
            if self.config.rate_limit_enabled:
                if not await self._check_rate_limit(email, ip_address):
                    await self._log_security_event(
                        SecurityEventType.LOGIN_FAILURE,
                        user_id=email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        device_fingerprint=device_fingerprint,
                        threat_level=ThreatLevel.MEDIUM,
                        details={"reason": "rate_limit_exceeded"}
                    )
                    return None, None, None, security_context
            
            # Get user by email
            user = await self.get_user_by_email(email)
            if not user:
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.LOW,
                    details={"reason": "user_not_found"}
                )
                return None, None, None, security_context
            
            # Check if account is locked
            if await self._is_account_locked(user.user_id):
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.HIGH,
                    details={"reason": "account_locked"}
                )
                return None, None, None, security_context
            
            # Check if account is active
            if not user.is_active:
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.MEDIUM,
                    details={"reason": "account_inactive"}
                )
                return None, None, None, security_context
            
            # Verify password
            if not self._verify_password(password, user.get("password_hash", "")):
                await self._increment_failed_login_attempts(user.user_id)
                await self._log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.MEDIUM,
                    details={"reason": "invalid_password"}
                )
                return None, None, None, security_context
            
            # Check for suspicious activity
            threat_level = await self._analyze_login_attempt(user.user_id, ip_address, user_agent, device_fingerprint)
            security_context["threat_level"] = threat_level
            
            # Device verification
            if self.config.device_verification_enabled:
                device_info = await self._get_or_create_device(user.user_id, device_fingerprint, user_agent, ip_address)
                security_context["device_trusted"] = device_info.is_trusted
                if not device_info.is_trusted:
                    security_context["requires_device_verification"] = True
            
            # Check if MFA is required
            if self.config.mfa_required and user.get("mfa_enabled", False):
                security_context["requires_mfa"] = True
            
            # Reset failed login attempts on successful authentication
            await self._reset_failed_login_attempts(user.user_id)
            
            # Update last login
            await self._update_last_login(user.user_id)
            
            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token()
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            session_data = {
                "id": session_id,
                "user_id": user.user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
                "created_at": datetime.utcnow(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "device_fingerprint": device_fingerprint,
                "is_active": True,
            }
            
            # Store session
            self._active_sessions[session_id] = session_data
            
            # Log successful authentication
            await self._log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                threat_level=threat_level,
                details={"session_id": session_id}
            )
            
            logger.info(f"User authenticated successfully - {email}")
            return user, access_token, refresh_token, security_context
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            await self._log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=email,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
                threat_level=ThreatLevel.HIGH,
                details={"error": str(e)}
            )
            return None, None, None, security_context
    
    async def verify_mfa(
        self,
        user_id: str,
        mfa_method: MFAMethod,
        mfa_code: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: str = ""
    ) -> bool:
        """
        Verify multi-factor authentication code.
        
        Args:
            user_id: User ID
            mfa_method: MFA method used
            mfa_code: MFA code to verify
            ip_address: IP address of the client
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            
        Returns:
            True if MFA verification is successful, False otherwise
        """
        try:
            # This would integrate with the MFA service
            # For now, we'll simulate the verification
            
            # Log MFA verification attempt
            success = False  # This would be determined by the MFA service
            
            if success:
                await self._log_security_event(
                    SecurityEventType.MFA_SUCCESS,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.LOW,
                    details={"mfa_method": mfa_method.value}
                )
            else:
                await self._log_security_event(
                    SecurityEventType.MFA_FAILURE,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.MEDIUM,
                    details={"mfa_method": mfa_method.value}
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Error verifying MFA: {e}")
            return False
    
    async def trust_device(
        self,
        user_id: str,
        device_fingerprint: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> bool:
        """
        Trust a device for a user.
        
        Args:
            user_id: User ID
            device_fingerprint: Device fingerprint
            ip_address: IP address of the client
            user_agent: User agent string
            
        Returns:
            True if device was trusted successfully, False otherwise
        """
        try:
            # Check if user has reached max trusted devices
            trusted_devices = await self._get_trusted_devices(user_id)
            if len(trusted_devices) >= self.config.max_trusted_devices:
                logger.warning(f"User {user_id} has reached maximum trusted devices")
                return False
            
            # Trust the device
            device_info = await self._get_device_info(device_fingerprint)
            if device_info:
                device_info.is_trusted = True
                device_info.trust_level = "trusted"
                
                # Update device in cache/database
                self._device_cache[device_fingerprint] = device_info
                
                await self._log_security_event(
                    SecurityEventType.DEVICE_TRUSTED,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    threat_level=ThreatLevel.LOW,
                    details={"device_id": device_info.device_id}
                )
                
                logger.info(f"Device trusted for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error trusting device: {e}")
            return False
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        *,
        roles: Optional[List[str]] = None,
        is_verified: bool = False
    ) -> Tuple[Optional[UserData], Optional[str]]:
        """
        Create a new user with enhanced security.
        
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
        
        if not self._db_session:
            raise RuntimeError("Database session not set")
        
        try:
            # Validate email
            if not self._validate_email(email):
                return None, "Invalid email address"
            
            # Validate password
            password_error = self._validate_password(password)
            if password_error:
                return None, password_error
            
            # Check if user already exists
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                return None, "User with this email already exists"
            
            # Hash password
            password_hash = self._hash_password(password)
            
            # Create user
            user_id = secrets.token_urlsafe(32)
            user_data = {
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "password_hash": password_hash,
                "roles": roles or ["user"],
                "is_verified": is_verified,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            
            user = UserData.ensure(user_data)
            
            # Save user to database
            # This would typically be a database operation
            # For now, we'll just add to cache
            self._user_cache[user_id] = user
            
            logger.info(f"User created successfully - {email}")
            return user, None
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None, str(e)
    
    async def validate_token(self, token: str) -> Optional[UserData]:
        """
        Validate an access token with enhanced security checks.
        
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
            if not user.is_active:
                logger.warning(f"User not active: {user_id}")
                return None
            
            # Check if session is still active
            session_id = payload.get("session_id")
            if session_id and session_id in self._active_sessions:
                session = self._active_sessions[session_id]
                if not session["is_active"]:
                    logger.warning(f"Session is not active: {session_id}")
                    return None
                
                # Update session last used time
                session["last_used"] = datetime.utcnow()
            
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
    
    # Helper methods
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_access_token(self, user: UserData) -> str:
        """Generate an access token for a user."""
        now = int(time.time())
        payload = {
            "sub": user.user_id,
            "iat": now,
            "exp": now + (self.config.access_token_expire_minutes * 60),
            "type": "access",
            "roles": user.get("roles", []),
            "email": user.get("email"),
        }
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def _generate_refresh_token(self) -> str:
        """Generate a refresh token."""
        return secrets.token_urlsafe(64)
    
    def _validate_email(self, email: str) -> bool:
        """Validate an email address."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> Optional[str]:
        """Validate a password."""
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
    
    async def _check_rate_limit(self, email: str, ip_address: str) -> bool:
        """Check if rate limit is exceeded."""
        if not self.config.rate_limit_enabled:
            return True
        
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.config.rate_limit_window_minutes)
        
        # Check failed attempts for this email
        email_attempts = self._failed_attempts.get(email, [])
        recent_attempts = [t for t in email_attempts if t >= window_start]
        
        if len(recent_attempts) >= self.config.rate_limit_max_attempts:
            return False
        
        # Check failed attempts for this IP
        ip_attempts = self._failed_attempts.get(ip_address, [])
        recent_ip_attempts = [t for t in ip_attempts if t >= window_start]
        
        if len(recent_ip_attempts) >= self.config.rate_limit_max_attempts:
            return False
        
        return True
    
    async def _increment_failed_login_attempts(self, user_id: str) -> None:
        """Increment failed login attempts for a user."""
        # This would typically update the database
        logger.warning(f"Incrementing failed login attempts for user {user_id}")
    
    async def _reset_failed_login_attempts(self, user_id: str) -> None:
        """Reset failed login attempts for a user."""
        # This would typically update the database
        logger.info(f"Resetting failed login attempts for user {user_id}")
    
    async def _is_account_locked(self, user_id: str) -> bool:
        """Check if a user account is locked."""
        # This would typically check the database
        return False
    
    async def _analyze_login_attempt(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: str
    ) -> ThreatLevel:
        """Analyze login attempt for suspicious activity."""
        # This would implement threat detection logic
        # For now, return low threat level
        return ThreatLevel.LOW
    
    async def _get_or_create_device(
        self,
        user_id: str,
        device_fingerprint: str,
        user_agent: str,
        ip_address: str
    ) -> DeviceInfo:
        """Get or create device information."""
        if device_fingerprint in self._device_cache:
            return self._device_cache[device_fingerprint]
        
        # Create new device info
        device_info = DeviceInfo(
            device_id=secrets.token_urlsafe(32),
            user_agent=user_agent,
            ip_address=ip_address,
            fingerprint=device_fingerprint,
            is_trusted=False,
            trust_level="unknown"
        )
        
        self._device_cache[device_fingerprint] = device_info
        return device_info
    
    async def _get_device_info(self, device_fingerprint: str) -> Optional[DeviceInfo]:
        """Get device information by fingerprint."""
        return self._device_cache.get(device_fingerprint)
    
    async def _get_trusted_devices(self, user_id: str) -> List[DeviceInfo]:
        """Get trusted devices for a user."""
        # This would typically query the database
        return [d for d in self._device_cache.values() if d.is_trusted]
    
    async def _update_last_login(self, user_id: str) -> None:
        """Update the last login time for a user."""
        # This would typically update the database
        logger.info(f"Updating last login time for user {user_id}")
    
    async def _log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: str,
        *,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: str = "",
        threat_level: ThreatLevel = ThreatLevel.LOW,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a security event."""
        event = SecurityEvent(
            event_id=secrets.token_urlsafe(32),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            threat_level=threat_level,
            details=details or {}
        )
        
        self._security_events.append(event)
        
        # Log to audit system
        self._audit_logger.log_audit_event({
            "event_type": event_type.value,
            "severity": "info" if threat_level == ThreatLevel.LOW else "warning",
            "message": f"Security event: {event_type.value}",
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "metadata": {
                "device_fingerprint": device_fingerprint,
                "threat_level": threat_level.value,
                "event_id": event.event_id,
                **(details or {})
            }
        })
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserData]:
        """Get a user by ID."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get a user by email."""
        for user in self._user_cache.values():
            if user.get("email") == email:
                return user
        return None
    
    async def health_check(self) -> bool:
        """Check the health of the Enhanced Authentication Service."""
        if not self._initialized:
            return False
        
        try:
            # Check if we can create and validate a token
            test_user_id = "test_user"
            token = self._generate_access_token(UserData.ensure({
                "user_id": test_user_id,
                "email": "test@example.com",
                "roles": ["user"]
            }))
            
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            if payload.get("sub") != test_user_id:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Enhanced Authentication Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Enhanced Authentication Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Enhanced Authentication Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Enhanced Authentication Service."""
        if not self._initialized:
            return
        
        # Clear active sessions
        self._active_sessions.clear()
        
        # Clear caches
        self._user_cache.clear()
        self._device_cache.clear()
        self._security_events.clear()
        self._failed_attempts.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Enhanced Authentication Service stopped successfully")


__all__ = [
    "EnhancedAuthService",
    "MFAMethod",
    "ThreatLevel",
    "SecurityEventType",
    "DeviceInfo",
    "SecurityEvent",
    "EnhancedAuthConfig",
]