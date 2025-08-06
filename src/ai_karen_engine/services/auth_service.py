"""
Unified Authentication Service

This service consolidates authentication functionality using the regular auth_manager
instead of having a separate "production" auth service. It provides:
- User authentication and session management
- Password reset functionality
- Two-factor authentication
- JWT token management
- Session validation
"""

from __future__ import annotations

import asyncio
import jwt
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ai_karen_engine.security import auth_manager
from ai_karen_engine.security.session_store import SessionStore
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UserData:
    """User data structure"""
    user_id: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]
    two_factor_enabled: bool
    is_verified: bool


@dataclass
class SessionData:
    """Session data structure"""
    access_token: str
    refresh_token: str
    session_token: str
    expires_in: int
    user_data: UserData


class AuthService:
    """Unified authentication service using the regular auth_manager"""
    
    def __init__(self):
        # JWT configuration
        self.secret_key = "your-secret-key-change-in-production"  # Should come from config
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
        # Session storage (uses in-memory store by default)
        self.session_store = SessionStore()
        
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        
        try:
            # Use the regular auth_manager for authentication
            user_data = auth_manager.authenticate(email, password)
            
            if not user_data:
                return None
            
            # Convert to our expected format
            return {
                "user_id": email,  # Using email as user_id for now
                "email": email,
                "full_name": user_data.get("full_name"),
                "roles": user_data.get("roles", ["user"]),
                "tenant_id": user_data.get("tenant_id", "default"),
                "preferences": user_data.get("preferences", {}),
                "two_factor_enabled": user_data.get("two_factor_enabled", False),
                "is_verified": user_data.get("is_verified", True)
            }
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {e}")
            return None
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenant_id: str = "default",
        preferences: Optional[Dict[str, Any]] = None
    ) -> UserData:
        """Create a new user"""
        
        try:
            # Create user using auth_manager
            auth_manager.create_user(
                username=email,
                password=password,
                roles=roles or ["user"],
                tenant_id=tenant_id,
                preferences=preferences or {}
            )
            
            # Return user data
            return UserData(
                user_id=email,
                email=email,
                full_name=full_name,
                roles=roles or ["user"],
                tenant_id=tenant_id,
                preferences=preferences or {},
                two_factor_enabled=False,
                is_verified=True  # Auto-verify for now
            )
            
        except Exception as e:
            logger.error(f"User creation failed for {email}: {e}")
            raise ValueError(f"Failed to create user: {str(e)}")
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str = "unknown",
        user_agent: str = "",
        device_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new session for authenticated user"""
        
        try:
            # Generate tokens
            access_token = self._generate_access_token(user_id)
            refresh_token = self._generate_refresh_token(user_id)
            session_token = secrets.token_urlsafe(32)
            
            # Store session data
            session_data = {
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "device_fingerprint": device_fingerprint,
                "created_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            await self.session_store.set_session(
                session_token,
                session_data,
                ttl_seconds=self.access_token_expire_minutes * 60,
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_token": session_token,
                "expires_in": self.access_token_expire_minutes * 60,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Session creation failed for user {user_id}: {e}")
            raise
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Validate session token (either session token or JWT) and return user data"""
        
        try:
            # First try to validate as JWT token
            try:
                payload = jwt.decode(session_token, self.secret_key, algorithms=[self.algorithm])
                user_id = payload.get("user_id")
                token_type = payload.get("type")
                
                if user_id and token_type == "access":
                    # Get current user data from auth_manager
                    user_data = auth_manager._USERS.get(user_id)
                    if user_data:
                        return {
                            "user_id": user_id,
                            "email": user_id,
                            "full_name": user_data.get("full_name"),
                            "roles": user_data.get("roles", ["user"]),
                            "tenant_id": user_data.get("tenant_id", "default"),
                            "preferences": user_data.get("preferences", {}),
                            "two_factor_enabled": user_data.get("two_factor_enabled", False),
                            "is_verified": user_data.get("is_verified", True)
                        }
            except jwt.InvalidTokenError:
                # Not a JWT token, try as session token
                pass
            
            # Check if it's a session token
            session_data = await self.session_store.get_session(session_token)
            if not session_data:
                return None
            
            user_id = session_data["user_id"]
            
            # Get current user data from auth_manager
            user_data = auth_manager._USERS.get(user_id)
            if not user_data:
                # Clean up invalid session
                await self.session_store.delete_session(session_token)
                return None
            
            # Update last accessed time
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            
            # Return user data in expected format
            return {
                "user_id": user_id,
                "email": user_id,
                "full_name": user_data.get("full_name"),
                "roles": user_data.get("roles", ["user"]),
                "tenant_id": user_data.get("tenant_id", "default"),
                "preferences": user_data.get("preferences", {}),
                "two_factor_enabled": user_data.get("two_factor_enabled", False),
                "is_verified": user_data.get("is_verified", True)
            }
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session"""
        
        try:
            return await self.session_store.delete_session(session_token)
            
        except Exception as e:
            logger.error(f"Session invalidation failed: {e}")
            return False
    
    async def update_user_password(
        self,
        user_id: str,
        new_password: str
    ) -> bool:
        """Update user password"""
        
        try:
            auth_manager.update_password(user_id, new_password)
            return True
            
        except Exception as e:
            logger.error(f"Password update failed for user {user_id}: {e}")
            return False
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        
        try:
            if user_id in auth_manager._USERS:
                auth_manager._USERS[user_id]["preferences"] = preferences
                auth_manager.save_users()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Preferences update failed for user {user_id}: {e}")
            return False
    
    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str = "unknown",
        user_agent: str = ""
    ) -> Optional[str]:
        """Create password reset token"""
        
        try:
            # Check if user exists
            if email not in auth_manager._USERS:
                return None
            
            token = auth_manager.create_password_reset_token(email)
            logger.info(f"Password reset token created for {email}")
            return token
            
        except Exception as e:
            logger.error(f"Password reset token creation failed: {e}")
            return None
    
    async def verify_password_reset_token(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """Verify password reset token and update password"""
        
        try:
            email = auth_manager.verify_password_reset_token(token)
            if not email:
                return False
            
            auth_manager.update_password(email, new_password)
            logger.info(f"Password reset successful for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            return False
    
    def _generate_access_token(self, user_id: str) -> str:
        """Generate JWT access token"""
        
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token"""
        
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return await self.session_store.count_sessions()

    async def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return await self.session_store.get_session(session_token)


# Global service instance
auth_service = AuthService()