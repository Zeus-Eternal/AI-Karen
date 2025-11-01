"""
Production Authentication Service

Enhanced authentication system for production deployment with proper security,
rate limiting, brute force protection, and first-run setup flow.
"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import jwt
from dataclasses import dataclass, field

from ..core.services.base import BaseService, ServiceConfig


@dataclass
class AuthAttempt:
    """Track authentication attempts for rate limiting."""
    ip_address: str
    email: str
    timestamp: datetime
    success: bool
    user_agent: Optional[str] = None


@dataclass
class UserAccount:
    """Production user account model."""

    user_id: str
    email: str
    password_hash: str
    full_name: str
    roles: List[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    tenant_id: str = "default"
    is_verified: bool = True
    two_factor_enabled: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)


class ProductionAuthService(BaseService):
    """
    Production-ready authentication service with security hardening.
    
    Features:
    - Secure password hashing
    - JWT token management with refresh
    - Rate limiting and brute force protection
    - First-run setup flow
    - Account lockout mechanisms
    - Audit logging
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if config is None:
            config = ServiceConfig(
                name="production_auth",
                enabled=True,
                config={
                    "users_file": "data/users.json",
                    "jwt_secret": os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
                    "jwt_algorithm": "HS256",
                    "access_token_expire_minutes": 30,
                    "refresh_token_expire_days": 7,
                    "max_failed_attempts": 5,
                    "lockout_duration_minutes": 15,
                    "rate_limit_window_minutes": 15,
                    "max_attempts_per_window": 10,
                    "require_strong_passwords": True,
                    "enable_audit_logging": True
                }
            )
        
        super().__init__(config)
        
        # Configuration
        self.users_file = Path(config.config.get("users_file", "data/users.json"))
        self.jwt_secret = config.config.get("jwt_secret")
        self.jwt_algorithm = config.config.get("jwt_algorithm", "HS256")
        self.access_token_expire_minutes = config.config.get("access_token_expire_minutes", 30)
        self.refresh_token_expire_days = config.config.get("refresh_token_expire_days", 7)
        self.max_failed_attempts = config.config.get("max_failed_attempts", 5)
        self.lockout_duration_minutes = config.config.get("lockout_duration_minutes", 15)
        self.rate_limit_window_minutes = config.config.get("rate_limit_window_minutes", 15)
        self.max_attempts_per_window = config.config.get("max_attempts_per_window", 10)
        self.require_strong_passwords = config.config.get("require_strong_passwords", True)
        self.enable_audit_logging = config.config.get("enable_audit_logging", True)
        
        # Runtime state
        self.users: Dict[str, UserAccount] = {}
        self.auth_attempts: List[AuthAttempt] = []
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
        # Ensure JWT secret is set
        if not self.jwt_secret:
            self.jwt_secret = secrets.token_urlsafe(32)
            self.logger.warning("JWT secret not configured, generated random secret")
    
    async def initialize(self) -> None:
        """Initialize the authentication service."""
        self.logger.info("Initializing Production Authentication Service")
        
        # Create data directory if it doesn't exist
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing users or create first-run setup
        await self._load_users()
        
        # Clean up old auth attempts
        self._cleanup_old_attempts()
        
        self.logger.info(f"Authentication service initialized with {len(self.users)} users")
    
    async def start(self) -> None:
        """Start the authentication service."""
        self.logger.info("Production Authentication Service started")
    
    async def stop(self) -> None:
        """Stop the authentication service."""
        await self._save_users()
        self.logger.info("Production Authentication Service stopped")
    
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            # Check if users file is accessible
            if self.users_file.exists():
                self.users_file.read_text()
            
            # Check JWT functionality
            test_payload = {"test": "data"}
            token = jwt.encode(test_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            decoded = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            return decoded["test"] == "data"
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def _load_users(self) -> None:
        """Load users from file or trigger first-run setup."""
        if not self.users_file.exists():
            self.logger.info("No users file found, first-run setup required")
            return
        
        try:
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
            
            # Convert to UserAccount objects
            for email, user_data in users_data.items():
                # Skip demo accounts
                if self._is_demo_account(email):
                    self.logger.info(f"Skipping demo account: {email}")
                    continue
                
                user = UserAccount(
                    user_id=user_data.get("user_id", email.split("@")[0]),
                    email=email,
                    password_hash=user_data.get("password_hash", ""),
                    full_name=user_data.get("full_name", ""),
                    roles=user_data.get("roles", ["user"]),
                    is_active=user_data.get("is_active", True),
                    created_at=datetime.fromisoformat(
                        user_data.get("created_at", datetime.now(timezone.utc).isoformat())
                    ),
                    updated_at=datetime.fromisoformat(
                        user_data.get(
                            "updated_at",
                            user_data.get("created_at", datetime.now(timezone.utc).isoformat())
                        )
                    ),
                    last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                    failed_login_attempts=user_data.get("failed_login_attempts", 0),
                    locked_until=datetime.fromisoformat(user_data["locked_until"]) if user_data.get("locked_until") else None,
                    tenant_id=user_data.get("tenant_id", "default"),
                    is_verified=user_data.get("is_verified", True),
                    two_factor_enabled=user_data.get("two_factor_enabled", False),
                    preferences=user_data.get("preferences", {})
                )
                self.users[email] = user
            
            self.logger.info(f"Loaded {len(self.users)} production users")
            
        except Exception as e:
            self.logger.error(f"Error loading users: {e}")
            self.users = {}
    
    async def _save_users(self) -> None:
        """Save users to file."""
        try:
            users_data = {}
            for email, user in self.users.items():
                users_data[email] = {
                    "user_id": user.user_id,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "full_name": user.full_name,
                    "roles": user.roles,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "failed_login_attempts": user.failed_login_attempts,
                    "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                    "tenant_id": user.tenant_id,
                    "is_verified": user.is_verified,
                    "two_factor_enabled": user.two_factor_enabled,
                    "preferences": user.preferences
                }
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            
            self.logger.debug("Users saved to file")
            
        except Exception as e:
            self.logger.error(f"Error saving users: {e}")
    
    def _is_demo_account(self, email: str) -> bool:
        """Check if an email is a demo account that should be removed."""
        demo_patterns = [
            "admin@example.com",
            "test@example.com",
            "demo@example.com",
            "user@example.com",
            "dev@example.com"
        ]
        return email.lower() in demo_patterns
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        try:
            if ":" not in password_hash:
                # Legacy hash without salt
                return hashlib.sha256(password.encode()).hexdigest() == password_hash
            
            salt, hash_value = password_hash.split(":", 1)
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == hash_value
        except Exception:
            return False
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        if not self.require_strong_passwords:
            return True, []
        
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    def _is_rate_limited(self, ip_address: str, email: str) -> bool:
        """Check if IP/email combination is rate limited."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.rate_limit_window_minutes)
        
        # Count recent attempts
        recent_attempts = [
            attempt for attempt in self.auth_attempts
            if attempt.timestamp >= window_start and 
            (attempt.ip_address == ip_address or attempt.email == email)
        ]
        
        return len(recent_attempts) >= self.max_attempts_per_window
    
    def _is_account_locked(self, user: UserAccount) -> bool:
        """Check if account is locked due to failed attempts."""
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return True
        
        if user.failed_login_attempts >= self.max_failed_attempts:
            # Auto-lock account
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.lockout_duration_minutes)
            return True
        
        return False
    
    def _record_auth_attempt(self, ip_address: str, email: str, success: bool, user_agent: str = None) -> None:
        """Record authentication attempt for rate limiting."""
        attempt = AuthAttempt(
            ip_address=ip_address,
            email=email,
            timestamp=datetime.now(timezone.utc),
            success=success,
            user_agent=user_agent
        )
        self.auth_attempts.append(attempt)
        
        # Log security event
        if self.enable_audit_logging:
            self.logger.info(
                f"Auth attempt: {email} from {ip_address} - {'SUCCESS' if success else 'FAILED'}",
                extra={
                    "event_type": "authentication",
                    "email": email,
                    "ip_address": ip_address,
                    "success": success,
                    "user_agent": user_agent
                }
            )
    
    def _cleanup_old_attempts(self) -> None:
        """Clean up old authentication attempts."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self.auth_attempts = [
            attempt for attempt in self.auth_attempts
            if attempt.timestamp >= cutoff
        ]
    
    def _create_jwt_token(self, user: UserAccount, token_type: str = "access") -> Tuple[str, datetime]:
        """Create a JWT token for the user."""
        now = datetime.now(timezone.utc)
        
        if token_type == "access":
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        else:  # refresh
            expires_delta = timedelta(days=self.refresh_token_expire_days)
        
        expires_at = now + expires_delta
        
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "roles": user.roles,
            "tenant_id": user.tenant_id,
            "type": token_type,
            "iat": now,
            "exp": expires_at
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token, expires_at
    
    def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if user still exists and is active
            user = self.users.get(payload.get("email"))
            if not user or not user.is_active:
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid token: {e}")
            return None
    
    async def is_first_run(self) -> bool:
        """Check if this is the first run (no admin users exist)."""
        admin_users = [
            user for user in self.users.values()
            if "admin" in user.roles or "super_admin" in user.roles
        ]
        return len(admin_users) == 0
    
    async def create_first_admin(self, email: str, password: str, full_name: str) -> UserAccount:
        """Create the first admin user during first-run setup."""
        if not await self.is_first_run():
            raise ValueError("Admin users already exist")
        
        # Validate password strength
        is_strong, issues = self._validate_password_strength(password)
        if not is_strong:
            raise ValueError(f"Password validation failed: {', '.join(issues)}")
        
        # Create admin user
        user = UserAccount(
            user_id="super_admin",
            email=email,
            password_hash=self._hash_password(password),
            full_name=full_name,
            roles=["super_admin", "admin", "user"],
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tenant_id="default",
            is_verified=True,
            preferences={
                "personalityTone": "balanced",
                "personalityVerbosity": "medium",
                "memoryDepth": "standard",
                "preferredLLMProvider": "llama-cpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 2048,
                "notifications": {"email": True, "push": False},
                "ui": {"theme": "system", "language": "en", "avatarUrl": None}
            }
        )
        
        self.users[email] = user
        await self._save_users()
        
        self.logger.info(f"Created first admin user: {email}")
        return user
    
    async def authenticate_user(self, email: str, password: str, ip_address: str, user_agent: str = None) -> Tuple[Optional[UserAccount], Optional[str], Optional[str]]:
        """
        Authenticate a user and return tokens.
        
        Returns:
            Tuple of (user, access_token, refresh_token) or (None, None, error_message)
        """
        # Check rate limiting
        if self._is_rate_limited(ip_address, email):
            self._record_auth_attempt(ip_address, email, False, user_agent)
            return None, None, "Too many authentication attempts. Please try again later."
        
        # Get user
        user = self.users.get(email)
        if not user:
            self._record_auth_attempt(ip_address, email, False, user_agent)
            return None, None, "Invalid credentials"
        
        # Check if account is locked
        if self._is_account_locked(user):
            self._record_auth_attempt(ip_address, email, False, user_agent)
            return None, None, f"Account is locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            await self._save_users()
            self._record_auth_attempt(ip_address, email, False, user_agent)
            return None, None, "Invalid credentials"
        
        # Successful authentication
        user.failed_login_attempts = 0
        user.locked_until = None
        now = datetime.now(timezone.utc)
        user.last_login = now
        user.updated_at = now
        await self._save_users()
        
        # Create tokens
        access_token, _ = self._create_jwt_token(user, "access")
        refresh_token, refresh_expires = self._create_jwt_token(user, "refresh")
        
        # Store refresh token
        self.refresh_tokens[refresh_token] = {
            "user_email": email,
            "expires_at": refresh_expires,
            "created_at": datetime.now(timezone.utc)
        }
        
        self._record_auth_attempt(ip_address, email, True, user_agent)
        return user, access_token, refresh_token
    
    async def validate_token(self, token: str) -> Optional[UserAccount]:
        """Validate an access token and return the user."""
        payload = self._validate_jwt_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        return self.users.get(payload.get("email"))
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Refresh an access token using a refresh token.
        
        Returns:
            Tuple of (new_access_token, error_message)
        """
        # Check if refresh token exists
        token_data = self.refresh_tokens.get(refresh_token)
        if not token_data:
            return None, "Invalid refresh token"
        
        # Check if refresh token is expired
        if token_data["expires_at"] < datetime.now(timezone.utc):
            del self.refresh_tokens[refresh_token]
            return None, "Refresh token expired"
        
        # Validate refresh token
        payload = self._validate_jwt_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None, "Invalid refresh token"
        
        # Get user
        user = self.users.get(payload.get("email"))
        if not user or not user.is_active:
            return None, "User not found or inactive"
        
        # Create new access token
        access_token, _ = self._create_jwt_token(user, "access")
        return access_token, None
    
    async def logout(self, refresh_token: str) -> None:
        """Logout user by invalidating refresh token."""
        if refresh_token in self.refresh_tokens:
            del self.refresh_tokens[refresh_token]
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        roles: List[str] = None,
        tenant_id: str = "default",
        is_verified: bool = True
    ) -> Tuple[Optional[UserAccount], Optional[str]]:
        """
        Create a new user account.
        
        Returns:
            Tuple of (user, error_message)
        """
        if email in self.users:
            return None, "User already exists"
        
        # Validate password strength
        is_strong, issues = self._validate_password_strength(password)
        if not is_strong:
            return None, f"Password validation failed: {', '.join(issues)}"
        
        # Create user
        now = datetime.now(timezone.utc)

        user = UserAccount(
            user_id=email.split("@")[0],
            email=email,
            password_hash=self._hash_password(password),
            full_name=full_name,
            roles=roles or ["user"],
            is_active=True,
            created_at=now,
            updated_at=now,
            tenant_id=tenant_id,
            is_verified=is_verified,
            preferences={
                "personalityTone": "balanced",
                "personalityVerbosity": "medium",
                "memoryDepth": "standard",
                "preferredLLMProvider": "llama-cpp",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 2048,
                "notifications": {"email": True, "push": False},
                "ui": {"theme": "system", "language": "en", "avatarUrl": None}
            }
        )
        
        self.users[email] = user
        await self._save_users()

        self.logger.info(f"Created new user: {email}")
        return user, None

    async def get_user_by_id(self, user_id: str) -> Optional[UserAccount]:
        """Retrieve a user by identifier."""
        for user in self.users.values():
            if user.user_id == user_id:
                return user
        return None

    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        """Retrieve a user by email address."""
        return self.users.get(email)

    async def list_users(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserAccount]:
        """List users with optional tenant filtering and pagination."""
        users = [
            user
            for user in self.users.values()
            if tenant_id is None or user.tenant_id == tenant_id
        ]

        users.sort(key=lambda item: item.created_at)
        return users[offset: offset + limit]

    async def update_user(
        self,
        user_id: str,
        *,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        tenant_id: Optional[str] = None,
        is_verified: Optional[bool] = None
    ) -> Tuple[Optional[UserAccount], Optional[str]]:
        """Update an existing user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None, "User not found"

        if full_name is not None:
            user.full_name = full_name
        if roles is not None and roles:
            user.roles = roles
        if preferences is not None:
            user.preferences = preferences
        if is_active is not None:
            user.is_active = is_active
        if tenant_id is not None:
            user.tenant_id = tenant_id
        if is_verified is not None:
            user.is_verified = is_verified

        user.updated_at = datetime.now(timezone.utc)
        await self._save_users()
        return user, None

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and invalidate their refresh tokens."""
        email_to_remove: Optional[str] = None
        for email, user in self.users.items():
            if user.user_id == user_id:
                email_to_remove = email
                break

        if not email_to_remove:
            return False

        del self.users[email_to_remove]
        await self._save_users()

        tokens_to_remove = [
            token
            for token, metadata in self.refresh_tokens.items()
            if metadata.get("user_email") == email_to_remove
        ]
        for token in tokens_to_remove:
            del self.refresh_tokens[token]

        return True

    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        
        recent_attempts = [
            attempt for attempt in self.auth_attempts
            if attempt.timestamp >= last_24h
        ]
        
        successful_attempts = [attempt for attempt in recent_attempts if attempt.success]
        failed_attempts = [attempt for attempt in recent_attempts if not attempt.success]
        
        locked_users = [
            user for user in self.users.values()
            if user.locked_until and user.locked_until > now
        ]
        
        return {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.is_active]),
            "locked_users": len(locked_users),
            "attempts_last_24h": len(recent_attempts),
            "successful_attempts_last_24h": len(successful_attempts),
            "failed_attempts_last_24h": len(failed_attempts),
            "active_refresh_tokens": len(self.refresh_tokens),
            "first_run_required": await self.is_first_run()
        }