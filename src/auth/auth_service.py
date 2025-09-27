"""
Simple Authentication Service for AI-Karen
Production-ready, minimal complexity JWT authentication with compatibility
for the streamlined web UI expectations.
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path

import jwt
from fastapi import HTTPException, status
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
    """Simple user model persisted in local JSON storage."""

    user_id: str
    email: EmailStr
    full_name: Optional[str] = None
    password_hash: str
    roles: List[str] = Field(default_factory=lambda: ["user"])
    is_active: bool = True
    created_at: str
    last_login: Optional[str] = None
    tenant_id: str = "default"
    two_factor_enabled: bool = False
    preferences: Dict[str, Any] = Field(default_factory=lambda: json.loads(json.dumps(DEFAULT_USER_PREFERENCES)))


class LoginRequest(BaseModel):
    """Login request model"""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model aligned with web UI expectations."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None


class SimpleAuthService:
    """Simple JWT-based authentication service"""

    def __init__(self) -> None:
        # Configuration from environment
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        self.jwt_long_lived_hours = int(os.getenv("JWT_LONG_LIVED_HOURS", "168"))  # 7 days
        self.password_reset_token_hours = int(os.getenv("PASSWORD_RESET_TOKEN_HOURS", "2"))
        self.auth_mode = os.getenv("AUTH_MODE", "production").lower()
        self.default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminadmin")

        # User storage
        self.storage_type = os.getenv("USER_STORAGE_TYPE", "json")
        self.storage_path = Path("data/users.json")
        self.reset_tokens_path = Path("data/password_reset_tokens.json")

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.reset_tokens_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize storage if it doesn't exist
        if not self.storage_path.exists():
            self._init_default_users()

        if not self.reset_tokens_path.exists():
            self.reset_tokens_path.write_text("{}", encoding="utf-8")

        # Clean up expired reset tokens at startup
        self._cleanup_expired_reset_tokens()

    # ------------------------------------------------------------------
    # Internal storage helpers
    # ------------------------------------------------------------------
    def _init_default_users(self) -> None:
        """Initialize with default admin user"""
        default_users = {
            "admin@example.com": UserModel(
                user_id="dev_admin",
                email="admin@example.com",
                full_name="Development Admin",
                password_hash=self._hash_password(self.default_admin_password),
                roles=["admin", "user"],
                created_at=datetime.now(timezone.utc).isoformat(),
            ).model_dump()
        }

        with open(self.storage_path, "w", encoding="utf-8") as file:
            json.dump(default_users, file, indent=2)

    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from storage"""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            self._init_default_users()
            return self._load_users()

    def _save_users(self, users: Dict[str, Dict[str, Any]]) -> None:
        """Save users to storage"""
        with open(self.storage_path, "w", encoding="utf-8") as file:
            json.dump(users, file, indent=2)

    def _load_reset_tokens(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.reset_tokens_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_reset_tokens(self, tokens: Dict[str, Dict[str, Any]]) -> None:
        with open(self.reset_tokens_path, "w", encoding="utf-8") as file:
            json.dump(tokens, file, indent=2)

    def _cleanup_expired_reset_tokens(self) -> None:
        tokens = self._load_reset_tokens()
        now = datetime.now(timezone.utc)
        changed = False
        for token, metadata in list(tokens.items()):
            try:
                expires_at = datetime.fromisoformat(metadata["expires_at"])
            except Exception:
                expires_at = now - timedelta(seconds=1)
            if expires_at < now:
                tokens.pop(token, None)
                changed = True
        if changed:
            self._save_reset_tokens(tokens)

    # ------------------------------------------------------------------
    # Password & token utilities
    # ------------------------------------------------------------------
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (simple but adequate for this use case)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self._hash_password(password) == password_hash

    # ------------------------------------------------------------------
    # User and token lifecycle
    # ------------------------------------------------------------------
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
        users[user.email] = user.model_dump()
        self._save_users(users)
        return user

    def create_access_token(self, user: UserModel, *, expiration_hours: Optional[int] = None) -> tuple[str, int]:
        """Create JWT access token"""
        hours = expiration_hours or self.jwt_expiration_hours
        expires_delta = timedelta(hours=hours)
        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": user.user_id,
            "email": user.email,
            "roles": user.roles,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        expires_in = int(expires_delta.total_seconds())
        return token, expires_in

    def create_long_lived_token(self, user: UserModel) -> tuple[str, int]:
        return self.create_access_token(user, expiration_hours=self.jwt_long_lived_hours)

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def validate_and_get_user_from_token(self, token: str) -> Optional[UserModel]:
        payload = self.validate_token(token)
        if not payload:
            return None
        return self.get_user_by_id(payload.get("sub", ""))

    def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        users = self._load_users()
        for user_data in users.values():
            if user_data.get("user_id") == user_id:
                return UserModel(**user_data)
        return None

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        users = self._load_users()
        data = users.get(email)
        return UserModel(**data) if data else None

    def serialize_user(self, user: UserModel) -> Dict[str, Any]:
        preferences = json.loads(json.dumps(user.preferences)) if isinstance(user.preferences, (dict, list)) else json.loads(json.dumps(DEFAULT_USER_PREFERENCES))
        return {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
            "two_factor_enabled": user.two_factor_enabled,
            "preferences": preferences,
        }

    def update_user_credentials(
        self,
        current_email: str,
        *,
        new_email: Optional[str] = None,
        new_password: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> UserModel:
        users = self._load_users()
        user_data = users.get(current_email)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user = UserModel(**user_data)

        if new_email:
            normalized_email = new_email.lower()
            if normalized_email != user.email and normalized_email in users:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
            users.pop(user.email)
            user.email = normalized_email
            user.user_id = normalized_email.split("@")[0]

        if new_password:
            user.password_hash = self._hash_password(new_password)

        if full_name is not None:
            user.full_name = full_name

        users[user.email] = user.model_dump()
        self._save_users(users)
        return user

    def create_password_reset_token(self, email: str) -> Optional[str]:
        users = self._load_users()
        if email not in users:
            return None

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.password_reset_token_hours)
        tokens = self._load_reset_tokens()
        tokens[token] = {
            "email": email,
            "expires_at": expires_at.isoformat(),
        }
        self._save_reset_tokens(tokens)
        return token

    def reset_password(self, token: str, new_password: str) -> UserModel:
        tokens = self._load_reset_tokens()
        metadata = tokens.get(token)
        if not metadata:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        try:
            expires_at = datetime.fromisoformat(metadata["expires_at"])
        except Exception:
            expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        if expires_at < datetime.now(timezone.utc):
            tokens.pop(token, None)
            self._save_reset_tokens(tokens)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

        email = metadata.get("email")
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

        users = self._load_users()
        user_data = users.get(email)
        if not user_data:
            tokens.pop(token, None)
            self._save_reset_tokens(tokens)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user = UserModel(**user_data)
        user.password_hash = self._hash_password(new_password)
        user.last_login = None

        users[email] = user.model_dump()
        self._save_users(users)

        tokens.pop(token, None)
        self._save_reset_tokens(tokens)
        return user

    def create_user(self, email: str, password: str, full_name: str = None, roles: Optional[List[str]] = None) -> UserModel:
        """Create new user"""
        users = self._load_users()

        if email in users:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

        user = UserModel(
            user_id=email.split("@")[0],
            email=email,
            full_name=full_name,
            password_hash=self._hash_password(password),
            roles=roles or ["user"],
            created_at=datetime.now(timezone.utc).isoformat(),
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
