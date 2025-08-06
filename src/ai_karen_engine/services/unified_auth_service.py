"""
Unified Production Authentication Service

This service provides all authentication functionality in one place:
- Database-backed user authentication
- Session management with JWT tokens
- Password reset functionality
- User management
- Security features (rate limiting, session validation)
"""

from __future__ import annotations

import os
import jwt
import bcrypt
import secrets
import uuid
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserData:
    """User data structure"""
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]
    is_verified: bool
    is_active: bool


@dataclass
class SessionData:
    """Session data structure"""
    access_token: str
    refresh_token: str
    session_token: str
    expires_in: int
    user_data: UserData


class UnifiedAuthService:
    """Unified authentication service for production use"""
    
    def __init__(self):
        self.database_url = os.environ.get(
            'POSTGRES_URL', 
            'postgresql://karen_user:karen_secure_pass_change_me@localhost:5432/ai_karen'
        )
        self.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30    # 30 days
        self.session_expire_hours = 24         # 24 hours
        
        # Rate limiting (simple in-memory for now)
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._max_attempts = 5
        self._lockout_duration = timedelta(minutes=15)
        
    def _get_db_connection(self):
        """Get database connection"""
        try:
            engine = create_engine(self.database_url)
            return engine.connect()
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def _generate_token(self, payload: Dict[str, Any], expires_delta: timedelta) -> str:
        """Generate JWT token"""
        expire = datetime.now(timezone.utc) + expires_delta
        payload.update({"exp": expire})
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    def _check_rate_limit(self, email: str) -> bool:
        """Check if user is rate limited"""
        now = datetime.now(timezone.utc)
        
        if email not in self._failed_attempts:
            return True
        
        # Clean old attempts
        self._failed_attempts[email] = [
            attempt for attempt in self._failed_attempts[email]
            if now - attempt < self._lockout_duration
        ]
        
        # Check if user is locked out
        if len(self._failed_attempts[email]) >= self._max_attempts:
            logger.warning(f"Rate limit exceeded for {email}")
            return False
        
        return True
    
    def _record_failed_attempt(self, email: str):
        """Record failed login attempt"""
        now = datetime.now(timezone.utc)
        if email not in self._failed_attempts:
            self._failed_attempts[email] = []
        self._failed_attempts[email].append(now)
    
    def _clear_failed_attempts(self, email: str):
        """Clear failed login attempts"""
        if email in self._failed_attempts:
            del self._failed_attempts[email]
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[UserData]:
        """Authenticate user with email and password"""
        
        # Check rate limiting
        if not self._check_rate_limit(email):
            return None
        
        try:
            with self._get_db_connection() as connection:
                # Query user from database
                result = connection.execute(
                    text('''
                        SELECT u.id, u.email, u.password_hash, u.roles, u.preferences, 
                               u.is_active, u.is_verified, u.tenant_id
                        FROM users u 
                        WHERE u.email = :email AND u.is_active = true
                    '''),
                    {'email': email}
                )
                user_row = result.fetchone()
                
                if not user_row:
                    logger.warning(f"User not found or inactive: {email}")
                    self._record_failed_attempt(email)
                    return None
                
                user_id, user_email, password_hash, roles, preferences, is_active, is_verified, tenant_id = user_row
                
                # Verify password
                if not password_hash or not self._verify_password(password, password_hash):
                    logger.warning(f"Invalid password for user: {email}")
                    self._record_failed_attempt(email)
                    return None
                
                # Clear failed attempts on successful login
                self._clear_failed_attempts(email)
                
                # Log successful authentication
                logger.info(f"User authenticated successfully: {email}")
                
                return UserData(
                    user_id=str(user_id),
                    email=user_email,
                    roles=roles or ["user"],
                    tenant_id=str(tenant_id),
                    preferences=preferences or {},
                    is_verified=is_verified,
                    is_active=is_active
                )
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            self._record_failed_attempt(email)
            return None
    
    async def create_session(
        self,
        user_data: UserData,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> SessionData:
        """Create new session for authenticated user"""
        
        try:
            # Generate tokens
            session_token = secrets.token_urlsafe(32)
            
            access_payload = {
                "user_id": user_data.user_id,
                "email": user_data.email,
                "roles": user_data.roles,
                "tenant_id": user_data.tenant_id,
                "session_token": session_token,
                "type": "access"
            }
            
            refresh_payload = {
                "user_id": user_data.user_id,
                "session_token": session_token,
                "type": "refresh"
            }
            
            access_token = self._generate_token(
                access_payload, 
                timedelta(minutes=self.access_token_expire_minutes)
            )
            
            refresh_token = self._generate_token(
                refresh_payload,
                timedelta(days=self.refresh_token_expire_days)
            )
            
            # Store session in database
            with self._get_db_connection() as connection:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=self.session_expire_hours)
                
                connection.execute(
                    text('''
                        INSERT INTO user_sessions 
                        (id, user_id, session_token, refresh_token, expires_at, ip_address, user_agent, is_active)
                        VALUES (:id, :user_id, :session_token, :refresh_token, :expires_at, :ip_address, :user_agent, :is_active)
                    '''),
                    {
                        'id': str(uuid.uuid4()),
                        'user_id': user_data.user_id,
                        'session_token': session_token,
                        'refresh_token': refresh_token,
                        'expires_at': expires_at,
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'is_active': True
                    }
                )
                connection.commit()
            
            logger.info(f"Session created for user: {user_data.email}")
            
            return SessionData(
                access_token=access_token,
                refresh_token=refresh_token,
                session_token=session_token,
                expires_in=self.access_token_expire_minutes * 60,
                user_data=user_data
            )
            
        except Exception as e:
            logger.error(f"Session creation failed for {user_data.email}: {e}")
            raise
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Validate session token and return user data"""
        
        try:
            with self._get_db_connection() as connection:
                # Query session from database
                result = connection.execute(
                    text('''
                        SELECT s.user_id, s.expires_at, s.is_active,
                               u.email, u.roles, u.preferences, u.tenant_id, u.is_verified, u.is_active as user_active
                        FROM user_sessions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.session_token = :session_token AND s.is_active = true
                    '''),
                    {'session_token': session_token}
                )
                session_row = result.fetchone()
                
                if not session_row:
                    logger.warning("Invalid or inactive session token")
                    return None
                
                user_id, expires_at, session_active, email, roles, preferences, tenant_id, is_verified, user_active = session_row
                
                # Check if session has expired
                if expires_at < datetime.now(timezone.utc):
                    logger.warning(f"Session expired for user: {email}")
                    # Mark session as inactive
                    connection.execute(
                        text('UPDATE user_sessions SET is_active = false WHERE session_token = :session_token'),
                        {'session_token': session_token}
                    )
                    connection.commit()
                    return None
                
                # Check if user is still active
                if not user_active:
                    logger.warning(f"User account inactive: {email}")
                    return None
                
                # Update last accessed time
                connection.execute(
                    text('UPDATE user_sessions SET last_accessed = :now WHERE session_token = :session_token'),
                    {'now': datetime.now(timezone.utc), 'session_token': session_token}
                )
                connection.commit()
                
                return {
                    "user_id": str(user_id),
                    "email": email,
                    "roles": roles or ["user"],
                    "tenant_id": str(tenant_id),
                    "preferences": preferences or {},
                    "is_verified": is_verified
                }
                
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session"""
        
        try:
            with self._get_db_connection() as connection:
                result = connection.execute(
                    text('UPDATE user_sessions SET is_active = false WHERE session_token = :session_token'),
                    {'session_token': session_token}
                )
                connection.commit()
                
                if result.rowcount > 0:
                    logger.info("Session invalidated successfully")
                    return True
                else:
                    logger.warning("Session not found for invalidation")
                    return False
                    
        except Exception as e:
            logger.error(f"Session invalidation failed: {e}")
            return False
    
    async def create_user(
        self,
        email: str,
        password: str,
        roles: Optional[List[str]] = None,
        tenant_id: str = "00000000-0000-0000-0000-000000000001",  # Default tenant
        preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[UserData]:
        """Create a new user"""
        
        try:
            with self._get_db_connection() as connection:
                # Check if user already exists
                result = connection.execute(
                    text('SELECT id FROM users WHERE email = :email'),
                    {'email': email}
                )
                if result.fetchone():
                    logger.warning(f"User already exists: {email}")
                    return None
                
                # Create user
                user_id = str(uuid.uuid4())
                password_hash = self._hash_password(password)
                
                connection.execute(
                    text('''
                        INSERT INTO users (id, tenant_id, email, password_hash, roles, preferences, is_active, is_verified, created_at, updated_at)
                        VALUES (:id, :tenant_id, :email, :password_hash, :roles, :preferences::jsonb, :is_active, :is_verified, :created_at, :updated_at)
                    '''),
                    {
                        'id': user_id,
                        'tenant_id': tenant_id,
                        'email': email,
                        'password_hash': password_hash,
                        'roles': roles or ["user"],
                        'preferences': json.dumps(preferences or {}),
                        'is_active': True,
                        'is_verified': True,  # Auto-verify for now
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
                connection.commit()
                
                logger.info(f"User created successfully: {email}")
                
                return UserData(
                    user_id=user_id,
                    email=email,
                    roles=roles or ["user"],
                    tenant_id=tenant_id,
                    preferences=preferences or {},
                    is_verified=True,
                    is_active=True
                )
                
        except Exception as e:
            logger.error(f"User creation failed for {email}: {e}")
            return None
    
    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        
        try:
            with self._get_db_connection() as connection:
                password_hash = self._hash_password(new_password)
                
                result = connection.execute(
                    text('UPDATE users SET password_hash = :password_hash, updated_at = :updated_at WHERE id = :user_id'),
                    {
                        'password_hash': password_hash,
                        'updated_at': datetime.now(timezone.utc),
                        'user_id': user_id
                    }
                )
                connection.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Password updated for user: {user_id}")
                    return True
                else:
                    logger.warning(f"User not found for password update: {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Password update failed for {user_id}: {e}")
            return False
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        
        try:
            with self._get_db_connection() as connection:
                result = connection.execute(
                    text('UPDATE users SET preferences = :preferences::jsonb, updated_at = :updated_at WHERE id = :user_id'),
                    {
                        'preferences': json.dumps(preferences),
                        'updated_at': datetime.now(timezone.utc),
                        'user_id': user_id
                    }
                )
                connection.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Preferences updated for user: {user_id}")
                    return True
                else:
                    logger.warning(f"User not found for preferences update: {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Preferences update failed for {user_id}: {e}")
            return False
    
    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[str]:
        """Create password reset token"""
        
        try:
            with self._get_db_connection() as connection:
                # Check if user exists
                result = connection.execute(
                    text('SELECT id FROM users WHERE email = :email AND is_active = true'),
                    {'email': email}
                )
                user_row = result.fetchone()
                
                if not user_row:
                    # Don't reveal if user exists or not for security
                    logger.warning(f"Password reset requested for non-existent user: {email}")
                    return None
                
                user_id = user_row[0]
                
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
                
                # Store reset token
                connection.execute(
                    text('''
                        INSERT INTO password_reset_tokens (id, user_id, token, expires_at, created_at)
                        VALUES (:id, :user_id, :token, :expires_at, :created_at)
                    '''),
                    {
                        'id': str(uuid.uuid4()),
                        'user_id': str(user_id),
                        'token': reset_token,
                        'expires_at': expires_at,
                        'created_at': datetime.now(timezone.utc)
                    }
                )
                connection.commit()
                
                logger.info(f"Password reset token created for user: {email}")
                return reset_token
                
        except Exception as e:
            logger.error(f"Password reset token creation failed for {email}: {e}")
            return None
    
    async def verify_password_reset_token(self, token: str, new_password: str) -> bool:
        """Verify password reset token and update password"""
        
        try:
            with self._get_db_connection() as connection:
                # Find valid reset token
                result = connection.execute(
                    text('''
                        SELECT prt.user_id, prt.expires_at, prt.used_at
                        FROM password_reset_tokens prt
                        WHERE prt.token = :token
                    '''),
                    {'token': token}
                )
                token_row = result.fetchone()
                
                if not token_row:
                    logger.warning("Invalid password reset token")
                    return False
                
                user_id, expires_at, used_at = token_row
                
                # Check if token has expired
                if expires_at < datetime.now(timezone.utc):
                    logger.warning("Password reset token has expired")
                    return False
                
                # Check if token has already been used
                if used_at:
                    logger.warning("Password reset token has already been used")
                    return False
                
                # Update password
                password_hash = self._hash_password(new_password)
                connection.execute(
                    text('UPDATE users SET password_hash = :password_hash, updated_at = :updated_at WHERE id = :user_id'),
                    {
                        'password_hash': password_hash,
                        'updated_at': datetime.now(timezone.utc),
                        'user_id': str(user_id)
                    }
                )
                
                # Mark token as used
                connection.execute(
                    text('UPDATE password_reset_tokens SET used_at = :used_at WHERE token = :token'),
                    {
                        'used_at': datetime.now(timezone.utc),
                        'token': token
                    }
                )
                
                connection.commit()
                
                logger.info(f"Password reset successful for user: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Password reset verification failed: {e}")
            return False


# Global instance
auth_service = UnifiedAuthService()