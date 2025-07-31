"""
Production Authentication Service
Real database integration with secure password hashing and session management
"""

import bcrypt
import jwt
import redis
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.database.models.auth_models import (
    User, UserSession, PasswordResetToken, EmailVerificationToken, ChatMemory
)
from ai_karen_engine.database.client import get_db_session
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class ProductionAuthService:
    """Production-ready authentication service"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        self.secret_key = settings.auth.secret_key
        self.algorithm = settings.auth.algorithm
        
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        roles: List[str] = None,
        tenant_id: str = "default",
        preferences: Dict[str, Any] = None
    ) -> User:
        """Create a new user with secure password hashing"""
        
        if roles is None:
            roles = ["user"]
        
        if preferences is None:
            preferences = {
                "personalityTone": "friendly",
                "personalityVerbosity": "balanced",
                "memoryDepth": "medium",
                "customPersonaInstructions": "",
                "preferredLLMProvider": "ollama",
                "preferredModel": "llama3.2:latest",
                "temperature": 0.7,
                "maxTokens": 1000,
                "notifications": {"email": True, "push": False},
                "ui": {"theme": "light", "language": "en", "avatarUrl": ""},
                "chatMemory": {
                    "shortTermDays": 1,
                    "longTermDays": 30,
                    "tailTurns": 3,
                    "summarizeThresholdTokens": 3000
                }
            }
        
        with get_db_session() as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User already exists")
            
            # Hash password securely
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt(rounds=settings.auth.password_hash_rounds)
            ).decode('utf-8')
            
            # Create user
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                roles=json.dumps(roles),
                tenant_id=tenant_id,
                preferences=json.dumps(preferences)
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created user: {email}")
            return user
    
    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with secure password verification"""
        
        with get_db_session() as db:
            # Get user
            user = db.query(User).filter(
                and_(User.email == email, User.is_active == True)
            ).first()
            
            if not user:
                logger.warning(f"Authentication failed - user not found: {email}")
                return None
            
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning(f"Authentication failed - account locked: {email}")
                return None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account after too many failures
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    logger.warning(f"Account locked due to failed attempts: {email}")
                
                db.commit()
                logger.warning(f"Authentication failed - invalid password: {email}")
                return None
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            
            db.commit()
            
            # Parse user data
            roles = json.loads(user.roles) if user.roles else ["user"]
            preferences = json.loads(user.preferences) if user.preferences else {}
            
            logger.info(f"User authenticated successfully: {email}")
            
            return {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": roles,
                "tenant_id": user.tenant_id,
                "preferences": preferences,
                "two_factor_enabled": user.two_factor_enabled,
                "is_verified": user.is_verified
            }
    
    async def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        device_fingerprint: Optional[str] = None
    ) -> Dict[str, str]:
        """Create a new user session with JWT tokens"""
        
        # Generate tokens
        session_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        # Create JWT access token
        access_token_data = {
            "sub": user_id,
            "session_id": session_token,
            "exp": datetime.utcnow() + timedelta(minutes=settings.auth.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        access_token = jwt.encode(access_token_data, self.secret_key, algorithm=self.algorithm)
        
        # Create JWT refresh token
        refresh_token_data = {
            "sub": user_id,
            "session_id": session_token,
            "exp": datetime.utcnow() + timedelta(days=settings.auth.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        refresh_jwt = jwt.encode(refresh_token_data, self.secret_key, algorithm=self.algorithm)
        
        with get_db_session() as db:
            # Clean up old sessions (keep only the most recent ones)
            old_sessions = db.query(UserSession).filter(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            ).order_by(UserSession.created_at.desc()).offset(settings.auth.max_sessions_per_user - 1).all()
            
            for session in old_sessions:
                session.is_active = False
            
            # Create new session
            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                refresh_token=refresh_token,
                user_agent=user_agent,
                ip_address=ip_address,
                device_fingerprint=device_fingerprint,
                expires_at=datetime.utcnow() + timedelta(hours=settings.auth.session_expire_hours)
            )
            
            db.add(session)
            db.commit()
        
        # Store session in Redis for fast access
        session_data = {
            "user_id": user_id,
            "session_id": session_token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.redis_client.setex(
            f"session:{session_token}",
            timedelta(hours=settings.auth.session_expire_hours),
            json.dumps(session_data)
        )
        
        logger.info(f"Created session for user: {user_id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_jwt,
            "session_token": session_token,
            "token_type": "bearer",
            "expires_in": settings.auth.access_token_expire_minutes * 60
        }
    
    async def validate_session(
        self,
        session_token: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Validate a user session - handles both JWT tokens and session tokens"""
        
        # First try to validate as JWT token
        try:
            decoded = jwt.decode(session_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's an access token
            if decoded.get("type") == "access":
                # Validate session exists in database
                session_id = decoded.get("session_id")
                if session_id:
                    with get_db_session() as db:
                        session = db.query(UserSession).filter(
                            and_(
                                UserSession.session_token == session_id,
                                UserSession.is_active == True,
                                UserSession.expires_at > datetime.utcnow()
                            )
                        ).first()
                        
                        if session:
                            # Update last activity
                            session.last_activity_at = datetime.utcnow()
                            
                            # Check for suspicious activity
                            if session.ip_address != ip_address:
                                session.is_suspicious = True
                                session.risk_score = min(session.risk_score + 20, 100)
                                logger.warning(f"Suspicious session activity - IP change: {session.user_id}")
                            
                            db.commit()
                            
                            # Get user data
                            user = db.query(User).filter(User.id == session.user_id).first()
                            if user and user.is_active:
                                roles = json.loads(user.roles) if user.roles else ["user"]
                                preferences = json.loads(user.preferences) if user.preferences else {}
                                
                                return {
                                    "user_id": user.id,
                                    "email": user.email,
                                    "full_name": user.full_name,
                                    "roles": roles,
                                    "tenant_id": user.tenant_id,
                                    "preferences": preferences,
                                    "two_factor_enabled": user.two_factor_enabled,
                                    "is_verified": user.is_verified,
                                    "session_id": session.id,
                                    "risk_score": session.risk_score
                                }
        except jwt.InvalidTokenError:
            # Not a valid JWT, try as session token
            pass
        
        # Try to validate as session token (fallback for direct session token usage)
        # Check Redis first for fast access
        session_data = self.redis_client.get(f"session:{session_token}")
        if not session_data:
            return None
        
        session_info = json.loads(session_data)
        
        # Validate with database
        with get_db_session() as db:
            session = db.query(UserSession).filter(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not session:
                # Remove from Redis if not in DB
                self.redis_client.delete(f"session:{session_token}")
                return None
            
            # Update last activity
            session.last_activity_at = datetime.utcnow()
            
            # Check for suspicious activity
            if session.ip_address != ip_address:
                session.is_suspicious = True
                session.risk_score = min(session.risk_score + 20, 100)
                logger.warning(f"Suspicious session activity - IP change: {session.user_id}")
            
            db.commit()
            
            # Get user data
            user = db.query(User).filter(User.id == session.user_id).first()
            if not user or not user.is_active:
                return None
            
            roles = json.loads(user.roles) if user.roles else ["user"]
            preferences = json.loads(user.preferences) if user.preferences else {}
            
            return {
                "user_id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": roles,
                "tenant_id": user.tenant_id,
                "preferences": preferences,
                "two_factor_enabled": user.two_factor_enabled,
                "is_verified": user.is_verified,
                "session_id": session.id,
                "risk_score": session.risk_score
            }
    
    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a user session"""
        
        with get_db_session() as db:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
                
                # Remove from Redis
                self.redis_client.delete(f"session:{session_token}")
                
                logger.info(f"Invalidated session: {session_token}")
                return True
        
        return False
    
    async def update_user_password(
        self,
        user_id: str,
        new_password: str
    ) -> bool:
        """Update user password with secure hashing"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Hash new password
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt(rounds=settings.auth.password_hash_rounds)
            ).decode('utf-8')
            
            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Updated password for user: {user_id}")
            return True
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Merge with existing preferences
            current_prefs = json.loads(user.preferences) if user.preferences else {}
            current_prefs.update(preferences)
            
            user.preferences = json.dumps(current_prefs)
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Updated preferences for user: {user_id}")
            return True
    
    async def create_password_reset_token(
        self,
        email: str,
        ip_address: str,
        user_agent: str
    ) -> Optional[str]:
        """Create a password reset token"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Create reset token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(reset_token)
            db.commit()
            
            logger.info(f"Created password reset token for: {email}")
            return token
    
    async def verify_password_reset_token(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """Verify and use password reset token"""
        
        with get_db_session() as db:
            reset_token = db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.token == token,
                    PasswordResetToken.is_used == False,
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not reset_token:
                return False
            
            # Update password
            user = db.query(User).filter(User.id == reset_token.user_id).first()
            if not user:
                return False
            
            # Hash new password
            password_hash = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt(rounds=settings.auth.password_hash_rounds)
            ).decode('utf-8')
            
            user.password_hash = password_hash
            user.updated_at = datetime.utcnow()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.used_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Password reset completed for user: {user.email}")
            return True


# Global service instance
production_auth_service = ProductionAuthService()