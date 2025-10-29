"""
No Authentication Service for AI-Karen
Minimal service that provides default user data without authentication.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field

DEFAULT_USER_PREFERENCES: Dict[str, Any] = {
    "personalityTone": "balanced",
    "personalityVerbosity": "medium",
    "memoryDepth": "standard",
    "customPersonaInstructions": "",
    "preferredLLMProvider": "llama-cpp",
    "preferredModel": "llama3.2:latest",
    "temperature": 0.7,
    "maxTokens": 2048,
    "notifications": {
        "email": True,
        "push": False,
    },
    "ui": {
        "theme": "system",
        "language": "en",
        "avatarUrl": None,
    },
}


class UserModel(BaseModel):
    """Simple user model - no authentication required."""

    user_id: str = "default_user"
    email: EmailStr = "user@example.com"
    full_name: Optional[str] = "Default User"
    roles: List[str] = Field(default_factory=lambda: ["user", "admin"])
    is_active: bool = True
    tenant_id: str = "default"
    preferences: Dict[str, Any] = Field(default_factory=lambda: DEFAULT_USER_PREFERENCES.copy())


class LoginRequest(BaseModel):
    """Login request model (not used in no-auth mode)"""
    email: EmailStr = "user@example.com"
    password: str = "password"


class LoginResponse(BaseModel):
    """Login response model - returns default user."""
    access_token: str = "no-auth-token"
    token_type: str = "bearer"
    expires_in: int = 86400
    user: Dict[str, Any]
    token: Optional[str] = "no-auth-token"
    refresh_token: Optional[str] = "no-auth-token"
    user_id: Optional[str] = "default_user"
    email: Optional[EmailStr] = "user@example.com"
    roles: Optional[List[str]] = Field(default_factory=lambda: ["user", "admin"])
    tenant_id: Optional[str] = "default"
    user_data: Optional[Dict[str, Any]] = None


class NoAuthService:
    """No authentication service - returns default user for all requests"""

    def __init__(self) -> None:
        # Create default user
        self.default_user = UserModel()

    def authenticate_user(self, email: str, password: str) -> UserModel:
        """Always return default user (no authentication required)"""
        return self.default_user

    def create_access_token(self, user: UserModel, *, expiration_hours: Optional[int] = None) -> tuple[str, int]:
        """Return dummy token"""
        return "no-auth-token", 86400

    def create_long_lived_token(self, user: UserModel) -> tuple[str, int]:
        """Return dummy token"""
        return "no-auth-token", 86400

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Always return valid payload"""
        return {
            "sub": "default_user",
            "email": "user@example.com",
            "roles": ["user", "admin"],
            "type": "access",
        }

    def validate_and_get_user_from_token(self, token: str) -> UserModel:
        """Always return default user"""
        return self.default_user

    def get_user_by_id(self, user_id: str) -> UserModel:
        """Always return default user"""
        return self.default_user

    def get_user_by_email(self, email: str) -> UserModel:
        """Always return default user"""
        return self.default_user

    def serialize_user(self, user: UserModel) -> Dict[str, Any]:
        """Serialize user data"""
        return {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
            "preferences": user.preferences,
        }

    def create_user(self, email: str, password: str, full_name: str = None, roles: Optional[List[str]] = None) -> UserModel:
        """Always return default user"""
        return self.default_user


# Global service instance
_auth_service: Optional[NoAuthService] = None


def get_auth_service() -> NoAuthService:
    """Get auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = NoAuthService()
    return _auth_service
