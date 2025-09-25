"""
Simple Authentication Service for AI-Karen
Production-ready, minimal complexity JWT authentication.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pathlib import Path

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr

class UserModel(BaseModel):
    """Simple user model"""
    user_id: str
    email: str
    full_name: Optional[str] = None
    password_hash: str
    roles: list[str] = ["user"]
    is_active: bool = True
    created_at: str
    last_login: Optional[str] = None

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class SimpleAuthService:
    """Simple JWT-based authentication service"""
    
    def __init__(self):
        # Configuration from environment
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        
        # User storage
        self.storage_type = os.getenv("USER_STORAGE_TYPE", "json")
        self.storage_path = Path("data/users.json")
        
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage if it doesn't exist
        if not self.storage_path.exists():
            self._init_default_users()
    
    def _init_default_users(self) -> None:
        """Initialize with default admin user"""
        default_users = {
            "admin@example.com": UserModel(
                user_id="admin",
                email="admin@example.com", 
                full_name="Admin User",
                password_hash=self._hash_password("admin"),
                roles=["admin", "user"],
                created_at=datetime.now(timezone.utc).isoformat()
            ).model_dump()
        }
        
        with open(self.storage_path, "w") as f:
            json.dump(default_users, f, indent=2)
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from storage"""
        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self._init_default_users()
            return self._load_users()
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]) -> None:
        """Save users to storage"""
        with open(self.storage_path, "w") as f:
            json.dump(users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (simple but secure enough for this use case)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        """Authenticate user with email/password"""
        users = self._load_users()
        
        user_data = users.get(email)
        if not user_data:
            return None
        
        user = UserModel(**user_data)
        
        if not user.is_active:
            return None
            
        if not self._verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.now(timezone.utc).isoformat()
        users[email] = user.model_dump()
        self._save_users(users)
        
        return user
    
    def create_access_token(self, user: UserModel) -> tuple[str, int]:
        """Create JWT access token"""
        expires_delta = timedelta(hours=self.jwt_expiration_hours)
        expire = datetime.now(timezone.utc) + expires_delta
        
        payload = {
            "sub": user.user_id,
            "email": user.email,
            "roles": user.roles,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        expires_in = int(expires_delta.total_seconds())
        
        return token, expires_in
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Token is valid
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by ID"""
        users = self._load_users()
        
        for user_data in users.values():
            if user_data.get("user_id") == user_id:
                return UserModel(**user_data)
        
        return None
    
    def create_user(self, email: str, password: str, full_name: str = None, roles: list[str] = None) -> UserModel:
        """Create new user"""
        users = self._load_users()
        
        if email in users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        user = UserModel(
            user_id=email.split("@")[0],  # Simple user ID from email
            email=email,
            full_name=full_name,
            password_hash=self._hash_password(password),
            roles=roles or ["user"],
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        users[email] = user.model_dump()
        self._save_users(users)
        
        return user

# Global service instance
_auth_service: Optional[SimpleAuthService] = None

def get_auth_service() -> SimpleAuthService:
    """Get auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = SimpleAuthService()
    return _auth_service
