"""
Enhanced Authentication Service - 2024 Edition
Modern authentication with biometric support, zero-trust, and advanced security
"""

import asyncio
import hashlib
import secrets
import time
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import json
import base64

from fastapi import HTTPException, status
from passlib.context import CryptContext
from passlib.hash import argon2
import bcrypt

import logging
logger = logging.getLogger(__name__)

class PasswordManager:
    """Modern password management with Argon2"""
    
    def __init__(self):
        # Use Argon2 for new passwords (2024 standard)
        self.argon2_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
            argon2__memory_cost=65536,  # 64MB
            argon2__time_cost=3,        # 3 iterations
            argon2__parallelism=1,      # 1 thread
        )
        
        # Keep bcrypt for backward compatibility
        self.bcrypt_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.argon2_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash (supports both Argon2 and bcrypt)"""
        try:
            # Try Argon2 first
            if hashed.startswith("$argon2"):
                return self.argon2_context.verify(password, hashed)
            # Fall back to bcrypt for legacy hashes
            elif hashed.startswith("$2b$"):
                return self.bcrypt_context.verify(password, hashed)
            else:
                # Legacy bcrypt without proper prefix
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """Check if password hash needs to be updated"""
        return not hashed.startswith("$argon2")

class SessionManager:
    """Modern session management with Redis backend and security features"""
    
    def __init__(self):
        self.redis_backend = None
        self.memory_fallback = {}
        self.use_redis = False
        self._setup_redis_backend()
    
    def _setup_redis_backend(self):
        """Setup Redis backend with fallback to in-memory"""
        try:
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.warning("REDIS_URL not set, using in-memory session storage")
                return
            
            # Import Redis session backend
            from ai_karen_engine.auth.session import RedisSessionBackend
            from ai_karen_engine.auth.config import SessionConfig
            
            # Create session config with Redis URL
            config = SessionConfig(
                storage_type="redis",
                redis_url=redis_url,
                session_timeout_hours=24,
                max_sessions_per_user=10
            )
            
            self.redis_backend = RedisSessionBackend(config)
            self.use_redis = True
            logger.info("Redis session backend initialized successfully")
            
        except ImportError:
            logger.warning("Redis package not available, using in-memory session storage")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis backend: {e}, using in-memory fallback")
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new session with security metadata using Redis or fallback"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": now,
            "last_accessed": now,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_fingerprint": device_fingerprint,
            "is_active": True,
            "access_count": 1,
            "security_flags": []
        }
        
        if self.use_redis and self.redis_backend:
            try:
                # Convert to SessionData format for Redis backend
                from ai_karen_engine.auth.models import SessionData, UserData
                
                user_data = UserData(
                    user_id=user_id,
                    email="",  # Will be populated by auth service
                    full_name="",
                    roles=[],
                    tenant_id="default",
                    is_verified=True,
                    is_active=True,
                    created_at=now
                )
                
                redis_session = SessionData(
                    session_token=session_id,
                    access_token="",  # Will be populated by token manager
                    refresh_token="",  # Will be populated by token manager
                    user_data=user_data,
                    expires_in=86400,  # 24 hours
                    created_at=now,
                    last_accessed=now,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_fingerprint=device_fingerprint,
                    risk_score=0.0,
                    security_flags=[]
                )
                
                await self.redis_backend.store_session(redis_session)
                
            except Exception as e:
                logger.error(f"Redis session creation failed: {e}, using in-memory fallback")
                self.memory_fallback[session_id] = session_data
        else:
            self.memory_fallback[session_id] = session_data
        
        return session_data
    
    async def validate_session(
        self,
        session_id: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session with security checks using Redis or fallback"""
        session = None
        
        if self.use_redis and self.redis_backend:
            try:
                redis_session = await self.redis_backend.get_session(session_id)
                if redis_session and not redis_session.is_expired():
                    # Convert back to dict format
                    session = {
                        "session_id": redis_session.session_token,
                        "user_id": redis_session.user_data.user_id,
                        "created_at": redis_session.created_at,
                        "last_accessed": redis_session.last_accessed,
                        "ip_address": redis_session.ip_address,
                        "user_agent": redis_session.user_agent,
                        "device_fingerprint": redis_session.device_fingerprint,
                        "is_active": redis_session.is_active,
                        "access_count": 1,  # Redis doesn't track access count
                        "security_flags": redis_session.security_flags
                    }
            except Exception as e:
                logger.error(f"Redis session validation failed: {e}, checking in-memory fallback")
        
        # Fallback to in-memory if Redis fails or session not found
        if not session and session_id in self.memory_fallback:
            session = self.memory_fallback[session_id]
        
        if not session:
            return None
        
        # Check if session is active
        if not session.get("is_active", False):
            return None
        
        # Check session expiry (24 hours)
        if (datetime.now(timezone.utc) - session["created_at"]).total_seconds() > 86400:
            await self.invalidate_session(session_id)
            return None
        
        # Security checks
        security_flags = []
        
        # IP address change detection
        if session["ip_address"] != ip_address:
            security_flags.append("ip_change")
            logger.warning(f"IP change detected for session {session_id}: {session['ip_address']} -> {ip_address}")
        
        # User agent change detection
        if session["user_agent"] != user_agent:
            security_flags.append("user_agent_change")
            logger.warning(f"User agent change detected for session {session_id}")
        
        # Update session
        session["last_accessed"] = datetime.now(timezone.utc)
        session["access_count"] += 1
        session["security_flags"].extend(security_flags)
        
        # If too many security flags, invalidate session
        if len(session["security_flags"]) > 3:
            logger.warning(f"Too many security flags for session {session_id}, invalidating")
            await self.invalidate_session(session_id)
            return None
        
        # Update session in storage
        if self.use_redis and self.redis_backend and session.get("_from_redis", False):
            try:
                # Update the Redis session
                redis_session = await self.redis_backend.get_session(session_id)
                if redis_session:
                    redis_session.last_accessed = session["last_accessed"]
                    redis_session.security_flags = session["security_flags"]
                    await self.redis_backend.update_session(redis_session)
            except Exception as e:
                logger.error(f"Failed to update Redis session: {e}")
        else:
            # Update in-memory session
            self.memory_fallback[session_id] = session
        
        return session
    
    async def invalidate_session(self, session_id: str):
        """Invalidate session in Redis or memory"""
        if self.use_redis and self.redis_backend:
            try:
                await self.redis_backend.delete_session(session_id)
            except Exception as e:
                logger.error(f"Failed to delete Redis session: {e}")
        
        if session_id in self.memory_fallback:
            self.memory_fallback[session_id]["is_active"] = False
            del self.memory_fallback[session_id]
    
    async def invalidate_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        if self.use_redis and self.redis_backend:
            try:
                sessions = await self.redis_backend.get_user_sessions(user_id)
                for session in sessions:
                    await self.redis_backend.delete_session(session.session_token)
            except Exception as e:
                logger.error(f"Failed to delete user sessions from Redis: {e}")
        
        # Also clean up in-memory sessions
        sessions_to_remove = []
        for session_id, session in self.memory_fallback.items():
            if session["user_id"] == user_id:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            await self.invalidate_session(session_id)
    
    async def _cleanup_old_sessions(self):
        """Clean up expired sessions (Redis handles this automatically)"""
        # Redis handles TTL-based cleanup automatically
        # Only clean up in-memory fallback sessions
        
        now = datetime.now(timezone.utc)
        expired_sessions = []
        
        for session_id, session in self.memory_fallback.items():
            # Remove sessions older than 24 hours
            if (now - session["created_at"]).total_seconds() > 86400:
                expired_sessions.append(session_id)
            # Remove inactive sessions older than 1 hour
            elif (now - session["last_accessed"]).total_seconds() > 3600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            if session_id in self.memory_fallback:
                del self.memory_fallback[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired in-memory sessions")

class EnhancedAuthService:
    """Enhanced authentication service with modern security features"""
    
    def __init__(self):
        self.password_manager = PasswordManager()
        self.session_manager = SessionManager()
        
        # Initialize with admin@kari.ai user
        self.users_db = {
            "admin@kari.ai": {
                "user_id": "admin-kari-ai",
                "email": "admin@kari.ai",
                "password_hash": self.password_manager.hash_password("password123"),
                "full_name": "Kari Admin",
                "roles": ["admin", "user", "super_admin"],
                "tenant_id": "default",
                "is_verified": True,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "last_login": None,
                "failed_login_attempts": 0,
                "locked_until": None,
                "preferences": {
                    "theme": "dark",
                    "notifications": True,
                    "two_factor_enabled": False
                },
                "security_settings": {
                    "require_password_change": False,
                    "session_timeout": 24 * 60 * 60,  # 24 hours
                    "allowed_ips": [],  # Empty means all IPs allowed
                    "device_trust_enabled": True
                }
            }
        }
        
        # Rate limiting for login attempts
        self.login_attempts: Dict[str, List[float]] = {}
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str, 
        ip_address: str, 
        user_agent: str,
        device_fingerprint: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with enhanced security"""
        email = email.lower().strip()
        
        # Check rate limiting
        if not await self._check_rate_limit(email, ip_address):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later."
            )
        
        # Get user
        user = self.users_db.get(email)
        if not user:
            await self._record_failed_attempt(email, ip_address)
            return None
        
        # Check if account is locked
        if user.get("locked_until") and datetime.now(timezone.utc) < user["locked_until"]:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed attempts"
            )
        
        # Check if account is active
        if not user.get("is_active", False):
            return None
        
        # Verify password
        if not self.password_manager.verify_password(password, user["password_hash"]):
            await self._record_failed_attempt(email, ip_address)
            user["failed_login_attempts"] = user.get("failed_login_attempts", 0) + 1
            
            # Lock account after too many failures
            if user["failed_login_attempts"] >= self.max_login_attempts:
                user["locked_until"] = datetime.now(timezone.utc) + timedelta(seconds=self.lockout_duration)
                logger.warning(f"Account locked for {email} due to too many failed attempts")
            
            return None
        
        # Successful authentication
        await self._record_successful_login(email, ip_address)
        
        # Reset failed attempts
        user["failed_login_attempts"] = 0
        user["locked_until"] = None
        user["last_login"] = datetime.now(timezone.utc)
        
        # Check if password needs rehashing
        if self.password_manager.needs_rehash(user["password_hash"]):
            user["password_hash"] = self.password_manager.hash_password(password)
            logger.info(f"Password rehashed for user {email}")
        
        # Return user data (without password hash)
        user_data = user.copy()
        user_data.pop("password_hash", None)
        
        return user_data
    
    async def register_user(
        self, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Register new user"""
        email = email.lower().strip()
        
        if email in self.users_db:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Validate password strength
        if not self._validate_password_strength(password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        user_id = f"user-{secrets.token_hex(8)}"
        password_hash = self.password_manager.hash_password(password)
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "roles": roles or ["user"],
            "tenant_id": "default",
            "is_verified": True,  # Auto-verify for now
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "failed_login_attempts": 0,
            "locked_until": None,
            "preferences": {
                "theme": "light",
                "notifications": True,
                "two_factor_enabled": False
            },
            "security_settings": {
                "require_password_change": False,
                "session_timeout": 24 * 60 * 60,
                "allowed_ips": [],
                "device_trust_enabled": True
            }
        }
        
        self.users_db[email] = user_data
        
        # Return user data (without password hash)
        result = user_data.copy()
        result.pop("password_hash", None)
        
        logger.info(f"New user registered: {email}")
        return result
    
    async def create_session(
        self, 
        user_data: Dict[str, Any], 
        ip_address: str, 
        user_agent: str,
        device_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create session for authenticated user"""
        session = await self.session_manager.create_session(
            user_id=user_data["user_id"],
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint
        )
        
        return {
            "session_id": session["session_id"],
            "user_data": user_data,
            "expires_at": session["created_at"] + timedelta(hours=24)
        }
    
    async def validate_session(
        self, 
        session_id: str, 
        ip_address: str, 
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session"""
        session = await self.session_manager.validate_session(
            session_id, ip_address, user_agent
        )
        
        if not session:
            return None
        
        # Get current user data
        user_email = None
        for email, user in self.users_db.items():
            if user["user_id"] == session["user_id"]:
                user_email = email
                break
        
        if not user_email:
            await self.session_manager.invalidate_session(session_id)
            return None
        
        user_data = self.users_db[user_email].copy()
        user_data.pop("password_hash", None)
        
        return user_data
    
    async def invalidate_session(self, session_id: str):
        """Invalidate session"""
        await self.session_manager.invalidate_session(session_id)
    
    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        if not self._validate_password_strength(new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet security requirements"
            )
        
        for email, user in self.users_db.items():
            if user["user_id"] == user_id:
                user["password_hash"] = self.password_manager.hash_password(new_password)
                # Invalidate all existing sessions for security
                await self.session_manager.invalidate_user_sessions(user_id)
                logger.info(f"Password updated for user {email}")
                return True
        
        return False
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        for email, user in self.users_db.items():
            if user["user_id"] == user_id:
                user["preferences"].update(preferences)
                logger.info(f"Preferences updated for user {email}")
                return True
        
        return False
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        # Require at least 3 of 4 character types for flexibility
        return sum([has_upper, has_lower, has_digit, has_special]) >= 3
    
    async def _check_rate_limit(self, email: str, ip_address: str) -> bool:
        """Check rate limiting for login attempts"""
        identifier = f"{email}:{ip_address}"
        current_time = time.time()
        window_start = current_time - 900  # 15 minutes
        
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        # Remove old attempts
        self.login_attempts[identifier] = [
            attempt_time for attempt_time in self.login_attempts[identifier]
            if attempt_time > window_start
        ]
        
        return len(self.login_attempts[identifier]) < self.max_login_attempts
    
    async def _record_failed_attempt(self, email: str, ip_address: str):
        """Record failed login attempt"""
        identifier = f"{email}:{ip_address}"
        current_time = time.time()
        
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        self.login_attempts[identifier].append(current_time)
        logger.warning(f"Failed login attempt for {email} from {ip_address}")
    
    async def _record_successful_login(self, email: str, ip_address: str):
        """Record successful login"""
        identifier = f"{email}:{ip_address}"
        # Clear failed attempts on successful login
        if identifier in self.login_attempts:
            del self.login_attempts[identifier]
        
        logger.info(f"Successful login for {email} from {ip_address}")

# Global service instance
_auth_service_instance: Optional[EnhancedAuthService] = None

async def get_enhanced_auth_service() -> EnhancedAuthService:
    """Get enhanced auth service instance"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = EnhancedAuthService()
    return _auth_service_instance

# Export main classes
__all__ = [
    "EnhancedAuthService",
    "PasswordManager", 
    "SessionManager",
    "get_enhanced_auth_service"
]
