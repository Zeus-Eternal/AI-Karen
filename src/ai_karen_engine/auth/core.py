"""
Core authentication layer for the consolidated authentication service.
"""

from __future__ import annotations

from datetime import datetime
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
from .database import DatabaseClient
from .session import SessionManager
from .tokens import TokenManager


class PasswordHasher:
    """Secure password hashing using bcrypt."""
    
    def __init__(self, rounds: int = 12) -> None:
        """Initialize password hasher with specified bcrypt rounds."""
        if not (4 <= rounds <= 20):
            raise ValueError("Bcrypt rounds must be between 4 and 20")
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        if not password or not hashed:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except (ValueError, TypeError):
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """Check if a password hash needs to be updated."""
        try:
            parts = hashed.split('$')
            if len(parts) >= 3 and parts[1] == '2b':
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
        except (ValueError, IndexError):
            pass
        return True


class PasswordValidator:
    """Password validation according to security requirements."""
    
    def __init__(self, min_length: int = 8, require_complexity: bool = True) -> None:
        """Initialize password validator with requirements."""
        self.min_length = min_length
        self.require_complexity = require_complexity
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against requirements."""
        errors = []
        
        if not password:
            errors.append("Password is required")
            return False, errors
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if self.require_complexity:
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


class CoreAuthenticator:
    """Core authentication logic without advanced security or intelligence features."""
    
    def __init__(self, config: AuthConfig) -> None:
        """Initialize core authenticator with configuration."""
        self.config = config
        self.db_client = DatabaseClient(config.database)
        self.token_manager = TokenManager(config.jwt)
        self.session_manager = SessionManager(config.session, self.token_manager)
        self.password_hasher = PasswordHasher(config.security.password_hash_rounds)
        self.password_validator = PasswordValidator(
            min_length=config.security.min_password_length,
            require_complexity=config.security.require_password_complexity
        )
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        **kwargs
    ) -> Optional[UserData]:
        """Authenticate a user with email and password."""
        start_time = datetime.utcnow()
        
        try:
            if not email or not password:
                raise InvalidCredentialsError("Email and password are required")
            
            user_data = await self.db_client.get_user_by_email(email)
            if not user_data:
                await self._log_auth_event(
                    AuthEventType.LOGIN_FAILED,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message="User not found",
                    start_time=start_time
                )
                raise InvalidCredentialsError()
            
            if not user_data.is_active:
                raise AccountDisabledError(user_id=user_data.user_id)
            
            if user_data.is_locked():
                raise AccountLockedError(
                    locked_until=user_data.locked_until.isoformat() if user_data.locked_until else None,
                    failed_attempts=user_data.failed_login_attempts
                )
            
            password_hash = await self.db_client.get_user_password_hash(user_data.user_id)
            if not password_hash:
                raise InvalidCredentialsError()
            
            if not self.password_hasher.verify_password(password, password_hash):
                user_data.increment_failed_attempts()
                
                if user_data.failed_login_attempts >= self.config.security.max_failed_attempts:
                    user_data.lock_account(self.config.security.lockout_duration_minutes)
                
                await self.db_client.update_user(user_data)
                raise InvalidCredentialsError()
            
            user_data.reset_failed_attempts()
            user_data.update_last_login()
            await self.db_client.update_user(user_data)
            
            if self.password_hasher.needs_rehash(password_hash):
                new_hash = self.password_hasher.hash_password(password)
                await self.db_client.update_user_password_hash(user_data.user_id, new_hash)
            
            await self._log_auth_event(
                AuthEventType.LOGIN_SUCCESS,
                user_id=user_data.user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                start_time=start_time
            )
            
            return user_data
            
        except Exception as e:
            if not isinstance(e, (InvalidCredentialsError, AccountLockedError, AccountDisabledError)):
                await self._log_auth_event(
                    AuthEventType.LOGIN_FAILED,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message=str(e),
                    start_time=start_time
                )
            raise
    
    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None,
        **kwargs
    ) -> SessionData:
        """Create a new authentication session for a user."""
        start_time = datetime.utcnow()
        
        try:
            session_data = await self.session_manager.create_session(
                user_data,
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=device_fingerprint,
            )
            
            await self._log_auth_event(
                AuthEventType.SESSION_CREATED,
                user_id=user_data.user_id,
                email=user_data.email,
                ip_address=ip_address,
                user_agent=user_agent,
                session_token=session_data.session_token,
                success=True,
                start_time=start_time
            )

            return session_data

        except Exception as e:
            await self._log_auth_event(
                AuthEventType.SESSION_CREATED,
                user_id=user_data.user_id,
                email=user_data.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message=str(e),
                start_time=start_time
            )
            raise
    
    async def validate_session(self, session_token: str, **kwargs) -> Optional[UserData]:
        """Validate a session token and return user data if valid."""
        if not session_token:
            raise SessionNotFoundError()
        
        try:
            session_data = await self.session_manager.store.get_session(session_token)
            if not session_data:
                raise SessionNotFoundError(session_token=session_token)

            if session_data.is_expired():
                await self.session_manager.delete_session(session_token)
                raise SessionExpiredError(session_token=session_token)

            session_data.update_last_accessed()
            await self.session_manager.store.update_session(session_data)

            return session_data.user_data

        except (SessionExpiredError, SessionNotFoundError):
            raise
    
    async def invalidate_session(self, session_token: str, reason: str = "manual", **kwargs) -> bool:
        """Invalidate a session token."""
        if not session_token:
            return False
        
        try:
            session_data = await self.session_manager.store.get_session(session_token)
            deleted = await self.session_manager.delete_session(session_token)
            
            if deleted and session_data:
                await self._log_auth_event(
                    AuthEventType.SESSION_INVALIDATED,
                    user_id=session_data.user_data.user_id,
                    session_token=session_token,
                    success=True,
                    details={"reason": reason}
                )
            
            return deleted
            
        except Exception:
            return False
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        tenant_id: str = "default",
        roles: Optional[List[str]] = None,
        **kwargs
    ) -> UserData:
        """Create a new user account."""
        start_time = datetime.utcnow()
        
        try:
            if not email or "@" not in email:
                raise PasswordValidationError("Invalid email format")
            
            is_valid, errors = self.password_validator.validate_password(password)
            if not is_valid:
                raise PasswordValidationError(
                    message="Password validation failed",
                    requirements=errors
                )
            
            existing_user = await self.db_client.get_user_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            
            password_hash = self.password_hasher.hash_password(password)
            
            user_data = UserData(
                user_id=str(uuid4()),
                email=email,
                full_name=full_name,
                tenant_id=tenant_id,
                roles=roles or ["user"],
                is_verified=not self.config.features.enable_email_verification,
                **kwargs
            )
            
            await self.db_client.create_user(user_data, password_hash)
            
            await self._log_auth_event(
                AuthEventType.USER_CREATED,
                user_id=user_data.user_id,
                email=email,
                success=True,
                start_time=start_time
            )
            
            return user_data
            
        except (UserAlreadyExistsError, PasswordValidationError):
            raise
    
    async def update_user_password(
        self,
        user_id: str,
        new_password: str,
        current_password: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Update a user's password."""
        start_time = datetime.utcnow()
        
        try:
            user_data = await self.db_client.get_user_by_id(user_id)
            if not user_data:
                raise UserNotFoundError(user_id=user_id)
            
            if current_password:
                current_hash = await self.db_client.get_user_password_hash(user_id)
                if not current_hash or not self.password_hasher.verify_password(current_password, current_hash):
                    raise InvalidCredentialsError("Current password is incorrect")
            
            is_valid, errors = self.password_validator.validate_password(new_password)
            if not is_valid:
                raise PasswordValidationError(
                    message="New password validation failed",
                    requirements=errors
                )
            
            new_hash = self.password_hasher.hash_password(new_password)
            await self.db_client.update_user_password_hash(user_id, new_hash)
            
            user_data.updated_at = datetime.utcnow()
            await self.db_client.update_user(user_data)
            
            await self._log_auth_event(
                AuthEventType.PASSWORD_CHANGED,
                user_id=user_id,
                email=user_data.email,
                success=True,
                start_time=start_time
            )
            
            return True
            
        except (UserNotFoundError, InvalidCredentialsError, PasswordValidationError):
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserData]:
        """Get user data by user ID."""
        return await self.db_client.get_user_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserData]:
        """Get user data by email address."""
        return await self.db_client.get_user_by_email(email)
    
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
        details: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None
    ) -> None:
        """Log an authentication event."""
        try:
            event = AuthEvent(
                event_type=event_type,
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                session_token=session_token,
                success=success,
                error_message=error_message,
                details=details or {}
            )
            
            if start_time:
                event.set_processing_time(start_time)
            
            if self.config.security.enable_audit_logging:
                await self.db_client.store_auth_event(event)
                
        except Exception:
            pass