"""
Security Manager for Llama.cpp Server

This module provides security hardening features including:
- Authentication and authorization
- Data encryption
- API key management
- Security logging
- Rate limiting
- Request validation
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import base64
import hmac
import jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# Try to import FastAPI components
try:
    from fastapi import HTTPException, Security, status, Depends
    from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
    from fastapi.security.api_key import APIKeyQuery
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    # Fallback for when FastAPI is not available
    FASTAPI_AVAILABLE = False
    
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    # Import typing utilities for proper Field function implementation
    from typing import Any, Callable, TypeVar, Union, overload
    
    _T = TypeVar('_T')
    
    def Field(default=..., *, default_factory=None, **kwargs):
        """
        Simplified Field function for when FastAPI is not available.
        This is a basic implementation that doesn't fully match Pydantic's Field
        but provides basic functionality.
        """
        # If default_factory is provided, call it to get the default value
        if default_factory is not None:
            return default_factory()
        
        # If default is ellipsis, return None
        if default is ...:
            return None
        
        # Otherwise return the default value
        return default
    
    class APIKeyHeader:
        def __init__(self, name: str, auto_error: bool = True):
            self.name = name
            self.auto_error = auto_error
    
    class APIKeyQuery:
        def __init__(self, name: str, auto_error: bool = True):
            self.name = name
            self.auto_error = auto_error
    
    class OAuth2PasswordBearer:
        def __init__(self, tokenUrl: str, auto_error: bool = True):
            self.tokenUrl = tokenUrl
            self.auto_error = auto_error
    
    class status:
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403
import ipaddress
import re
import uuid

# Try to import optional dependencies
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from .config_manager import ConfigManager  # type: ignore
except ImportError:
    # Fallback for when config_manager is not available
    class ConfigManager:
        def __init__(self, config_path=None):
            self.config = {}
        
        def get(self, key, default=None):
            return self.config.get(key, default)
        
        def set(self, key, value):
            self.config[key] = value
            return True
        
        def save(self):
            return True

try:
    from .error_handler import ErrorCategory, ErrorLevel, handle_error  # type: ignore
except ImportError:
    # Fallback for when error_handler is not available
    class ErrorCategory:
        SECURITY = "security"
    
    class ErrorLevel:
        ERROR = "error"
        WARNING = "warning"
    
    def handle_error(category, code, details=None, level=ErrorLevel.ERROR, include_traceback=True):
        print(f"Error: {category} - {code} - {details}")
        return None

# Security constants
MIN_PASSWORD_LENGTH = 12
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION = 300  # 5 minutes
API_KEY_LENGTH = 32
JWT_EXPIRATION = 3600  # 1 hour
REFRESH_TOKEN_EXPIRATION = 86400  # 24 hours
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

class UserRole(Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API = "api"

class Permission(Enum):
    """Permissions for authorization"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MODEL_MANAGE = "model_manage"
    SYSTEM_CONFIG = "system_config"
    USER_MANAGE = "user_manage"

@dataclass
class User:
    """User data model"""
    username: str
    password_hash: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    api_keys: List[str] = field(default_factory=list)
    refresh_tokens: List[str] = field(default_factory=list)
    active: bool = True

@dataclass
class APIKey:
    """API key data model"""
    key: str
    name: str
    user: str
    permissions: List[Permission] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    active: bool = True

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = JWT_EXPIRATION
    password_min_length: int = MIN_PASSWORD_LENGTH
    max_login_attempts: int = MAX_LOGIN_ATTEMPTS
    login_lockout_duration: int = LOGIN_LOCKOUT_DURATION
    rate_limit_requests: int = RATE_LIMIT_REQUESTS
    rate_limit_window: int = RATE_LIMIT_WINDOW
    enable_api_keys: bool = True
    enable_jwt: bool = True
    enable_rate_limiting: bool = True
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = field(default_factory=list)
    enable_ip_blacklist: bool = False
    ip_blacklist: List[str] = field(default_factory=list)
    enable_request_logging: bool = True
    encryption_key: Optional[str] = None
    redis_url: Optional[str] = None

class TokenData(BaseModel):
    """Token data model for JWT"""
    username: str
    role: UserRole
    permissions: List[Permission] = []
    exp: Optional[int] = None

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str
    new_password: str

class CreateAPIKeyRequest(BaseModel):
    """Create API key request model"""
    name: str
    permissions: List[Permission] = []
    expires_in_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    """API key response model"""
    key: str
    name: str
    permissions: List[Permission]
    created_at: datetime
    expires_at: Optional[datetime]

class SecurityManager:
    """
    Security Manager class that handles authentication, authorization,
    encryption, and other security-related tasks.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the security manager with configuration"""
        self.config_manager = ConfigManager(config_path)
        self._load_config()
        
        # Initialize security components
        self._init_encryption()
        self._init_jwt()
        self._init_rate_limiting()
        
        # Load users and API keys
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self._load_security_data()
        
        # Initialize FastAPI security dependencies
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
        self.api_key_query = APIKeyQuery(name="api_key", auto_error=False)
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)
        
        # Create default admin user if no users exist
        if not self.users:
            self._create_default_admin()
    
    def _load_config(self):
        """Load security configuration from config manager"""
        # Helper function to safely get config values with proper types
        def get_config_value(key, default, expected_type):
            value = self.config_manager.get(key, default)
            if value is None:
                return default
            try:
                return expected_type(value)
            except (ValueError, TypeError):
                return default
        
        self.security_config = SecurityConfig(
            secret_key=get_config_value("security.secret_key", secrets.token_urlsafe(32), str),
            jwt_algorithm=get_config_value("security.jwt_algorithm", "HS256", str),
            jwt_expiration=get_config_value("security.jwt_expiration", JWT_EXPIRATION, int),
            password_min_length=get_config_value("security.password_min_length", MIN_PASSWORD_LENGTH, int),
            max_login_attempts=get_config_value("security.max_login_attempts", MAX_LOGIN_ATTEMPTS, int),
            login_lockout_duration=get_config_value("security.login_lockout_duration", LOGIN_LOCKOUT_DURATION, int),
            rate_limit_requests=get_config_value("security.rate_limit_requests", RATE_LIMIT_REQUESTS, int),
            rate_limit_window=get_config_value("security.rate_limit_window", RATE_LIMIT_WINDOW, int),
            enable_api_keys=get_config_value("security.enable_api_keys", True, bool),
            enable_jwt=get_config_value("security.enable_jwt", True, bool),
            enable_rate_limiting=get_config_value("security.enable_rate_limiting", True, bool),
            enable_ip_whitelist=get_config_value("security.enable_ip_whitelist", False, bool),
            ip_whitelist=get_config_value("security.ip_whitelist", [], list),
            enable_ip_blacklist=get_config_value("security.enable_ip_blacklist", False, bool),
            ip_blacklist=get_config_value("security.ip_blacklist", [], list),
            enable_request_logging=get_config_value("security.enable_request_logging", True, bool),
            encryption_key=get_config_value("security.encryption_key", None, str),
            redis_url=get_config_value("security.redis_url", None, str)
        )
        
        # Save the secret key if it was just generated
        if not self.config_manager.get("security.secret_key"):
            self.config_manager.set("security.secret_key", self.security_config.secret_key)
            self.config_manager.save()
    
    def _init_encryption(self):
        """Initialize encryption components"""
        if self.security_config.encryption_key:
            # Use provided encryption key
            key = self.security_config.encryption_key.encode()
            try:
                self.cipher_suite = Fernet(key)
            except Exception as e:
                handle_error(
                    ErrorCategory.SECURITY,
                    "invalid_encryption_key",
                    f"Invalid encryption key: {str(e)}",
                    ErrorLevel.ERROR
                )
                # Generate a new key
                self._generate_encryption_key()
        else:
            # Generate a new encryption key
            self._generate_encryption_key()
    
    def _generate_encryption_key(self):
        """Generate a new encryption key and save it"""
        key = Fernet.generate_key()
        self.cipher_suite = Fernet(key)
        
        # Save the key to config
        self.config_manager.set("security.encryption_key", key.decode())
        self.config_manager.save()
        self.security_config.encryption_key = key.decode()
    
    def _init_jwt(self):
        """Initialize JWT components"""
        self.jwt_secret = self.security_config.secret_key
        self.jwt_algorithm = self.security_config.jwt_algorithm
    
    def _init_rate_limiting(self):
        """Initialize rate limiting components"""
        self.rate_limit_data = {}
        
        # Try to initialize Redis if available and configured
        self.redis_client = None
        if REDIS_AVAILABLE and self.security_config.redis_url:
            try:
                self.redis_client = redis.from_url(self.security_config.redis_url)  # type: ignore
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                handle_error(
                    ErrorCategory.SECURITY,
                    "redis_connection_failed",
                    f"Failed to connect to Redis: {str(e)}",
                    ErrorLevel.WARNING
                )
                self.redis_client = None
    
    def _load_security_data(self):
        """Load users and API keys from storage"""
        # Load users
        users_data = self.config_manager.get("security.users", {})
        for username, user_data in users_data.items():
            try:
                # Convert string datetime back to datetime objects
                created_at = datetime.fromisoformat(user_data["created_at"]) if "created_at" in user_data and isinstance(user_data["created_at"], str) else datetime.now()
                last_login = datetime.fromisoformat(user_data["last_login"]) if "last_login" in user_data and isinstance(user_data["last_login"], str) else None
                locked_until = datetime.fromisoformat(user_data["locked_until"]) if "locked_until" in user_data and isinstance(user_data["locked_until"], str) else None
                
                # Convert role string to UserRole enum
                role = UserRole(user_data["role"])
                
                # Convert permission strings to Permission enums
                permissions = [Permission(p) for p in user_data.get("permissions", [])]
                
                self.users[username] = User(
                    username=username,
                    password_hash=user_data["password_hash"],
                    role=role,
                    permissions=permissions,
                    created_at=created_at,
                    last_login=last_login,
                    login_attempts=user_data.get("login_attempts", 0),
                    locked_until=locked_until,
                    api_keys=user_data.get("api_keys", []),
                    refresh_tokens=user_data.get("refresh_tokens", []),
                    active=user_data.get("active", True)
                )
            except Exception as e:
                handle_error(
                    ErrorCategory.SECURITY,
                    "user_load_failed",
                    f"Failed to load user {username}: {str(e)}",
                    ErrorLevel.WARNING
                )
        
        # Load API keys
        api_keys_data = self.config_manager.get("security.api_keys", {})
        for key, key_data in api_keys_data.items():
            try:
                # Convert string datetime back to datetime objects
                created_at = datetime.fromisoformat(key_data["created_at"]) if "created_at" in key_data and isinstance(key_data["created_at"], str) else datetime.now()
                expires_at = datetime.fromisoformat(key_data["expires_at"]) if "expires_at" in key_data and isinstance(key_data["expires_at"], str) else None
                last_used = datetime.fromisoformat(key_data["last_used"]) if "last_used" in key_data and isinstance(key_data["last_used"], str) else None
                
                # Convert permission strings to Permission enums
                permissions = [Permission(p) for p in key_data.get("permissions", [])]
                
                self.api_keys[key] = APIKey(
                    key=key,
                    name=key_data["name"],
                    user=key_data["user"],
                    permissions=permissions,
                    created_at=created_at,
                    expires_at=expires_at,
                    last_used=last_used,
                    active=key_data.get("active", True)
                )
            except Exception as e:
                handle_error(
                    ErrorCategory.SECURITY,
                    "api_key_load_failed",
                    f"Failed to load API key {key[:8]}...: {str(e)}",
                    ErrorLevel.WARNING
                )
    
    def _save_security_data(self):
        """Save users and API keys to storage"""
        # Convert users to serializable format
        users_data = {}
        for username, user in self.users.items():
            users_data[username] = {
                "password_hash": user.password_hash,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions],
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_attempts": user.login_attempts,
                "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                "api_keys": user.api_keys,
                "refresh_tokens": user.refresh_tokens,
                "active": user.active
            }
        
        # Convert API keys to serializable format
        api_keys_data = {}
        for key, api_key in self.api_keys.items():
            api_keys_data[key] = {
                "name": api_key.name,
                "user": api_key.user,
                "permissions": [p.value for p in api_key.permissions],
                "created_at": api_key.created_at.isoformat(),
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                "active": api_key.active
            }
        
        # Save to config
        self.config_manager.set("security.users", users_data)
        self.config_manager.set("security.api_keys", api_keys_data)
        self.config_manager.save()
    
    def _create_default_admin(self):
        """Create a default admin user if no users exist"""
        default_admin_password = "admin123"  # This should be changed immediately
        password_hash = self._hash_password(default_admin_password)
        
        admin_user = User(
            username="admin",
            password_hash=password_hash,
            role=UserRole.ADMIN,
            permissions=list(Permission),  # Admin has all permissions
            active=True
        )
        
        self.users["admin"] = admin_user
        self._save_security_data()
        
        handle_error(
            ErrorCategory.SECURITY,
            "default_admin_created",
            "Default admin user created. Please change the password immediately.",
            ErrorLevel.WARNING
        )
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _is_account_locked(self, user: User) -> bool:
        """Check if a user account is locked"""
        if user.locked_until and user.locked_until > datetime.now():
            return True
        return False
    
    def _lock_account(self, user: User):
        """Lock a user account"""
        user.locked_until = datetime.now() + timedelta(seconds=self.security_config.login_lockout_duration)
        user.login_attempts = 0
        self._save_security_data()
    
    def _unlock_account(self, user: User):
        """Unlock a user account"""
        user.locked_until = None
        user.login_attempts = 0
        self._save_security_data()
    
    def _increment_login_attempts(self, user: User):
        """Increment login attempts for a user"""
        user.login_attempts += 1
        if user.login_attempts >= self.security_config.max_login_attempts:
            self._lock_account(user)
        self._save_security_data()
    
    def _reset_login_attempts(self, user: User):
        """Reset login attempts for a user"""
        user.login_attempts = 0
        user.locked_until = None
        self._save_security_data()
    
    def _generate_jwt_token(self, user: User) -> Tuple[str, str]:
        """Generate JWT access and refresh tokens for a user"""
        # Access token
        access_token_payload = {
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": datetime.utcnow() + timedelta(seconds=self.security_config.jwt_expiration)
        }
        access_token = jwt.encode(access_token_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        # Refresh token
        refresh_token = secrets.token_urlsafe(32)
        user.refresh_tokens.append(refresh_token)
        
        # Limit the number of refresh tokens per user
        if len(user.refresh_tokens) > 5:
            user.refresh_tokens.pop(0)
        
        self._save_security_data()
        
        return access_token, refresh_token
    
    def _generate_api_key(self) -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(API_KEY_LENGTH)
    
    def _verify_jwt_token(self, token: str) -> Optional[TokenData]:
        """Verify a JWT token and return the token data"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Extract data from payload
            username = payload.get("username")
            role = UserRole(payload.get("role"))
            permissions = [Permission(p) for p in payload.get("permissions", [])]
            
            return TokenData(
                username=username,
                role=role,
                permissions=permissions,
                exp=payload.get("exp")
            )
        except jwt.PyJWTError:
            return None
    
    def _verify_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Verify a refresh token and return the associated user"""
        for username, user in self.users.items():
            if refresh_token in user.refresh_tokens:
                return user
        return None
    
    def _verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify an API key and return the key data"""
        key_data = self.api_keys.get(api_key)
        if not key_data or not key_data.active:
            return None
        
        # Check if the key has expired
        if key_data.expires_at and key_data.expires_at < datetime.now():
            return None
        
        # Update last used timestamp
        key_data.last_used = datetime.now()
        self._save_security_data()
        
        return key_data
    
    def _is_ip_allowed(self, ip: str) -> bool:
        """Check if an IP address is allowed based on whitelist/blacklist"""
        # Check blacklist first
        if self.security_config.enable_ip_blacklist:
            for blocked_ip in self.security_config.ip_blacklist:
                try:
                    if ipaddress.ip_address(ip) in ipaddress.ip_network(blocked_ip, strict=False):
                        return False
                except ValueError:
                    # If the IP is invalid, continue checking
                    continue
        
        # Check whitelist
        if self.security_config.enable_ip_whitelist and self.security_config.ip_whitelist:
            for allowed_ip in self.security_config.ip_whitelist:
                try:
                    if ipaddress.ip_address(ip) in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                except ValueError:
                    # If the IP is invalid, continue checking
                    continue
            
            # If whitelist is enabled and IP is not in whitelist, deny
            return False
        
        # If neither whitelist nor blacklist blocks the IP, allow
        return True
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """Check if the identifier has exceeded the rate limit"""
        if not self.security_config.enable_rate_limiting:
            return True
        
        current_time = int(time.time())
        window_start = current_time - self.security_config.rate_limit_window
        
        # Use Redis if available
        if self.redis_client:
            try:
                key = f"rate_limit:{identifier}"
                pipe = self.redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Add current request
                pipe.zadd(key, {str(current_time): current_time})
                
                # Set expiration if not already set
                pipe.expire(key, self.security_config.rate_limit_window)
                
                # Count requests in window
                pipe.zcard(key)
                
                _, _, count = pipe.execute()
                
                return count <= self.security_config.rate_limit_requests
            except Exception:
                # Fall back to in-memory rate limiting
                pass
        
        # In-memory rate limiting (not persistent across restarts)
        if identifier not in self.rate_limit_data:
            self.rate_limit_data[identifier] = []
        
        # Filter out old requests
        self.rate_limit_data[identifier] = [
            req_time for req_time in self.rate_limit_data[identifier]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self.rate_limit_data[identifier]) >= self.security_config.rate_limit_requests:
            return False
        
        # Add current request
        self.rate_limit_data[identifier].append(current_time)
        return True
    
    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """
        Encrypt data using Fernet encryption
        
        Args:
            data: Data to encrypt (string or bytes)
            
        Returns:
            Encrypted data as a base64-encoded string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted_data = self.cipher_suite.encrypt(data)
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> bytes:
        """
        Decrypt data using Fernet encryption
        
        Args:
            encrypted_data: Encrypted data as a base64-encoded string
            
        Returns:
            Decrypted data as bytes
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data
        except Exception as e:
            handle_error(
                ErrorCategory.SECURITY,
                "decryption_failed",
                f"Failed to decrypt data: {str(e)}",
                ErrorLevel.ERROR
            )
            raise ValueError("Decryption failed")
    
    def hash_data(self, data: Union[str, bytes]) -> str:
        """
        Hash data using SHA-256
        
        Args:
            data: Data to hash (string or bytes)
            
        Returns:
            Hexadecimal hash string
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
    def verify_hash(self, data: Union[str, bytes], hash_value: str) -> bool:
        """
        Verify data against a hash
        
        Args:
            data: Data to verify (string or bytes)
            hash_value: Hash to verify against
            
        Returns:
            True if the data matches the hash, False otherwise
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        computed_hash = hashlib.sha256(data).hexdigest()
        return hmac.compare_digest(computed_hash, hash_value)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check length
        if len(password) < self.security_config.password_min_length:
            issues.append(f"Password must be at least {self.security_config.password_min_length} characters long")
        
        # Check for uppercase letters
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        # Check for lowercase letters
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        # Check for digits
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    def create_user(self, username: str, password: str, role: UserRole, permissions: Optional[List[Permission]] = None) -> bool:
        """
        Create a new user
        
        Args:
            username: Username for the new user
            password: Password for the new user
            role: Role for the new user
            permissions: List of permissions for the new user
            
        Returns:
            True if the user was created successfully, False otherwise
        """
        if username in self.users:
            handle_error(
                ErrorCategory.SECURITY,
                "user_exists",
                f"User {username} already exists",
                ErrorLevel.WARNING
            )
            return False
        
        # Validate password strength
        is_valid, issues = self.validate_password_strength(password)
        if not is_valid:
            handle_error(
                ErrorCategory.SECURITY,
                "weak_password",
                f"Password for user {username} is weak: {', '.join(issues)}",
                ErrorLevel.WARNING
            )
            return False
        
        # Hash password
        password_hash = self._hash_password(password)
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            permissions=permissions or []
        )
        
        self.users[username] = user
        self._save_security_data()
        
        return True
    
    def update_user(self, username: str, **kwargs) -> bool:
        """
        Update a user's data
        
        Args:
            username: Username of the user to update
            **kwargs: Fields to update (password, role, permissions, active)
            
        Returns:
            True if the user was updated successfully, False otherwise
        """
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Update password if provided
        if "password" in kwargs:
            is_valid, issues = self.validate_password_strength(kwargs["password"])
            if not is_valid:
                handle_error(
                    ErrorCategory.SECURITY,
                    "weak_password",
                    f"Password for user {username} is weak: {', '.join(issues)}",
                    ErrorLevel.WARNING
                )
                return False
            
            user.password_hash = self._hash_password(kwargs["password"])
        
        # Update role if provided
        if "role" in kwargs:
            user.role = kwargs["role"]
        
        # Update permissions if provided
        if "permissions" in kwargs:
            user.permissions = kwargs["permissions"]
        
        # Update active status if provided
        if "active" in kwargs:
            user.active = kwargs["active"]
        
        self._save_security_data()
        return True
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user
        
        Args:
            username: Username of the user to delete
            
        Returns:
            True if the user was deleted successfully, False otherwise
        """
        if username not in self.users:
            return False
        
        # Revoke all API keys for this user
        api_keys_to_revoke = [key for key, api_key in self.api_keys.items() if api_key.user == username]
        for key in api_keys_to_revoke:
            self.revoke_api_key(key)
        
        # Delete user
        del self.users[username]
        self._save_security_data()
        
        return True
    
    def authenticate_user(self, username: str, password: str, ip: Optional[str] = None) -> Optional[LoginResponse]:
        """
        Authenticate a user with username and password
        
        Args:
            username: Username to authenticate
            password: Password to authenticate
            ip: IP address of the client (optional)
            
        Returns:
            LoginResponse with tokens if authentication is successful, None otherwise
        """
        # Check if user exists
        if username not in self.users:
            return None
        
        user = self.users[username]
        
        # Check if user is active
        if not user.active:
            handle_error(
                ErrorCategory.SECURITY,
                "account_disabled",
                f"Account for user {username} is disabled",
                ErrorLevel.WARNING
            )
            return None
        
        # Check if account is locked
        if self._is_account_locked(user):
            handle_error(
                ErrorCategory.SECURITY,
                "account_locked",
                f"Account for user {username} is locked",
                ErrorLevel.WARNING
            )
            return None
        
        # Check IP address if provided
        if ip and not self._is_ip_allowed(ip):
            handle_error(
                ErrorCategory.SECURITY,
                "ip_blocked",
                f"IP address {ip} is not allowed",
                ErrorLevel.WARNING
            )
            return None
        
        # Check rate limiting
        if not self._check_rate_limit(f"login:{username}"):
            handle_error(
                ErrorCategory.SECURITY,
                "rate_limit_exceeded",
                f"Login rate limit exceeded for user {username}",
                ErrorLevel.WARNING
            )
            return None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._increment_login_attempts(user)
            handle_error(
                ErrorCategory.SECURITY,
                "authentication_failed",
                f"Authentication failed for user {username}",
                ErrorLevel.WARNING
            )
            return None
        
        # Reset login attempts on successful authentication
        self._reset_login_attempts(user)
        
        # Update last login time
        user.last_login = datetime.now()
        self._save_security_data()
        
        # Generate tokens
        access_token, refresh_token = self._generate_jwt_token(user)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.security_config.jwt_expiration
        )
    
    def refresh_tokens(self, refresh_token: str) -> Optional[LoginResponse]:
        """
        Refresh JWT tokens using a refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            LoginResponse with new tokens if refresh is successful, None otherwise
        """
        # Verify refresh token
        user = self._verify_refresh_token(refresh_token)
        if not user:
            return None
        
        # Generate new tokens
        access_token, new_refresh_token = self._generate_jwt_token(user)
        
        # Remove old refresh token
        user.refresh_tokens.remove(refresh_token)
        self._save_security_data()
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=self.security_config.jwt_expiration
        )
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if the token was revoked successfully, False otherwise
        """
        for username, user in self.users.items():
            if refresh_token in user.refresh_tokens:
                user.refresh_tokens.remove(refresh_token)
                self._save_security_data()
                return True
        return False
    
    def create_api_key(self, user: str, name: str, permissions: Optional[List[Permission]] = None, expires_in_days: Optional[int] = None) -> Optional[APIKeyResponse]:
        """
        Create a new API key
        
        Args:
            user: Username of the user to create the API key for
            name: Name of the API key
            permissions: List of permissions for the API key
            expires_in_days: Number of days until the API key expires
            
        Returns:
            APIKeyResponse with the new API key if creation is successful, None otherwise
        """
        # Check if user exists
        if user not in self.users:
            return None
        
        # Generate API key
        key = self._generate_api_key()
        
        # Calculate expiration date
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # Create API key
        api_key = APIKey(
            key=key,
            name=name,
            user=user,
            permissions=permissions or [],
            expires_at=expires_at
        )
        
        self.api_keys[key] = api_key
        
        # Add API key to user
        self.users[user].api_keys.append(key)
        self._save_security_data()
        
        return APIKeyResponse(
            key=key,
            name=name,
            permissions=api_key.permissions,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at
        )
    
    def revoke_api_key(self, key: str) -> bool:
        """
        Revoke an API key
        
        Args:
            key: API key to revoke
            
        Returns:
            True if the API key was revoked successfully, False otherwise
        """
        if key not in self.api_keys:
            return False
        
        api_key = self.api_keys[key]
        api_key.active = False
        
        # Remove API key from user
        user = self.users.get(api_key.user)
        if user and key in user.api_keys:
            user.api_keys.remove(key)
        
        self._save_security_data()
        return True
    
    def authenticate_api_key(self, api_key: str, ip: Optional[str] = None) -> Optional[Tuple[User, APIKey]]:
        """
        Authenticate with an API key
        
        Args:
            api_key: API key to authenticate
            ip: IP address of the client (optional)
            
        Returns:
            Tuple of (User, APIKey) if authentication is successful, None otherwise
        """
        # Check if API key is enabled
        if not self.security_config.enable_api_keys:
            return None
        
        # Verify API key
        key_data = self._verify_api_key(api_key)
        if not key_data:
            return None
        
        # Get user
        user = self.users.get(key_data.user)
        if not user or not user.active:
            return None
        
        # Check IP address if provided
        if ip and not self._is_ip_allowed(ip):
            handle_error(
                ErrorCategory.SECURITY,
                "ip_blocked",
                f"IP address {ip} is not allowed",
                ErrorLevel.WARNING
            )
            return None
        
        # Check rate limiting
        if not self._check_rate_limit(f"api_key:{api_key}"):
            handle_error(
                ErrorCategory.SECURITY,
                "rate_limit_exceeded",
                f"API key rate limit exceeded",
                ErrorLevel.WARNING
            )
            return None
        
        return user, key_data
    
    def authenticate_jwt(self, token: str, ip: Optional[str] = None) -> Optional[TokenData]:
        """
        Authenticate with a JWT token
        
        Args:
            token: JWT token to authenticate
            ip: IP address of the client (optional)
            
        Returns:
            TokenData if authentication is successful, None otherwise
        """
        # Check if JWT is enabled
        if not self.security_config.enable_jwt:
            return None
        
        # Verify JWT token
        token_data = self._verify_jwt_token(token)
        if not token_data:
            return None
        
        # Get user
        user = self.users.get(token_data.username)
        if not user or not user.active:
            return None
        
        # Check IP address if provided
        if ip and not self._is_ip_allowed(ip):
            handle_error(
                ErrorCategory.SECURITY,
                "ip_blocked",
                f"IP address {ip} is not allowed",
                ErrorLevel.WARNING
            )
            return None
        
        # Check rate limiting
        if not self._check_rate_limit(f"jwt:{token_data.username}"):
            handle_error(
                ErrorCategory.SECURITY,
                "rate_limit_exceeded",
                f"JWT rate limit exceeded for user {token_data.username}",
                ErrorLevel.WARNING
            )
            return None
        
        return token_data
    
    def check_permission(self, user_or_token: Union[User, TokenData], permission: Permission) -> bool:
        """
        Check if a user or token has a specific permission
        
        Args:
            user_or_token: User or TokenData to check
            permission: Permission to check
            
        Returns:
            True if the user or token has the permission, False otherwise
        """
        # Admin role has all permissions
        if user_or_token.role == UserRole.ADMIN:
            return True
        
        # Check if the user or token has the permission
        return permission in user_or_token.permissions
    
    def get_current_user(self, token: Optional[str] = None, api_key: Optional[str] = None) -> Optional[User]:
        """
        FastAPI dependency to get the current user from a JWT token or API key
        
        Args:
            token: JWT token (from OAuth2PasswordBearer)
            api_key: API key (from APIKeyHeader)
            
        Returns:
            User if authentication is successful, None otherwise
        """
        # Try JWT token first
        if token:
            token_data = self.authenticate_jwt(token)
            if token_data:
                user = self.users.get(token_data.username)
                if user and user.active:
                    return user
        
        # Try API key
        if api_key:
            result = self.authenticate_api_key(api_key)
            if result:
                return result[0]  # Return the user
        
        return None
    
    def get_current_active_user(self, current_user: User) -> User:
        """
        FastAPI dependency to get the current active user
        
        Args:
            current_user: Current user from get_current_user
            
        Returns:
            User if the user is active, raises HTTPException otherwise
        """
        if not current_user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )
        return current_user
    
    def require_permission(self, permission: Permission):
        """
        FastAPI dependency to require a specific permission
        
        Args:
            permission: Permission to require
            
        Returns:
            Dependency function that checks for the permission
        """
        def dependency(current_user: User):
            if not self.check_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
            return current_user
        
        return dependency
    
    def require_role(self, role: UserRole):
        """
        FastAPI dependency to require a specific role
        
        Args:
            role: Role to require
            
        Returns:
            Dependency function that checks for the role
        """
        def dependency(current_user: User):
            if current_user.role != role and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
            return current_user
        
        return dependency
    
    def log_security_event(self, event_type: str, details: Optional[Dict[str, Any]] = None, ip: Optional[str] = None, user: Optional[str] = None):
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            details: Additional details about the event
            ip: IP address of the client
            user: Username of the user
        """
        if not self.security_config.enable_request_logging:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details or {},
            "ip": ip,
            "user": user
        }
        
        # Log to console for now
        # In a production environment, this would be logged to a secure log file or SIEM system
        print(f"Security Event: {json.dumps(event)}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get the current security status
        
        Returns:
            Dictionary with security status information
        """
        # Count active users
        active_users = sum(1 for user in self.users.values() if user.active)
        
        # Count active API keys
        active_api_keys = sum(1 for api_key in self.api_keys.values() if api_key.active)
        
        # Count locked accounts
        locked_accounts = sum(1 for user in self.users.values() if self._is_account_locked(user))
        
        return {
            "active_users": active_users,
            "total_users": len(self.users), 
            "active_api_keys": active_api_keys,
            "total_api_keys": len(self.api_keys),
            "locked_accounts": locked_accounts,
            "security_features": {
                "api_keys_enabled": self.security_config.enable_api_keys,
                "jwt_enabled": self.security_config.enable_jwt,
                "rate_limiting_enabled": self.security_config.enable_rate_limiting,
                "ip_whitelist_enabled": self.security_config.enable_ip_whitelist,
                "ip_blacklist_enabled": self.security_config.enable_ip_blacklist,
                "request_logging_enabled": self.security_config.enable_request_logging
            }
        }