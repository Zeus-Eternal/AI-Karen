"""
Simple Authentication Routes for AI-Karen.
Provides a minimal-yet-complete authentication surface that aligns with the
expectations of the production web UI while remaining easy to maintain.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from .auth_service import (
    get_auth_service,
    LoginRequest,
    LoginResponse,
    UserModel,
)
from .auth_middleware import require_auth

router = APIRouter(prefix="/auth", tags=["authentication"])


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    full_name: Optional[str] = None


class UpdateCredentialsRequest(BaseModel):
    new_username: Optional[EmailStr] = Field(default=None, description="Updated email address")
    new_password: Optional[str] = Field(default=None, min_length=4)
    full_name: Optional[str] = None

    @field_validator("new_username")
    @classmethod
    def _normalize_email(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value else value

    @model_validator(mode="after")
    def _ensure_updates(self) -> "UpdateCredentialsRequest":
        if self.new_username is None and self.new_password is None and self.full_name is None:
            raise ValueError("At least one field must be provided")
        return self


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ValidateSessionResponse(BaseModel):
    valid: bool
    user: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_user(user: UserModel) -> Dict[str, Any]:
    auth_service = get_auth_service()
    return auth_service.serialize_user(user)


def _create_auth_response(user: UserModel, token: str, expires_in: int) -> JSONResponse:
    user_payload = _serialize_user(user)
    body: Dict[str, Any] = {
        "access_token": token,
        "token": token,
        "refresh_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user_payload,
        "user_data": user_payload,
        "user_id": user_payload["user_id"],
        "email": user_payload["email"],
        "roles": user_payload["roles"],
        "tenant_id": user_payload.get("tenant_id", "default"),
    }
    response = JSONResponse(body)
    response.set_cookie(
        key="auth_token",
        value=token,
        max_age=expires_in,
        httponly=True,
        secure=os.getenv("AUTH_COOKIE_SECURE", "false").lower() in ("1", "true", "yes"),
        samesite=os.getenv("AUTH_COOKIE_SAMESITE", "lax"),
        path="/",
    )
    return response


def _extract_token_from_request(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1]
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        return cookie_token
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> JSONResponse:
    """Authenticate user and return JWT token."""
    auth_service = get_auth_service()
    user = auth_service.authenticate_user(request.email.lower(), request.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token, expires_in = auth_service.create_access_token(user)
    return _create_auth_response(user, access_token, expires_in)


@router.get("/me")
async def get_current_user_info(request: Request, current_user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    """Get current user information."""
    auth_service = get_auth_service()
    user = auth_service.get_user_by_id(current_user["user_id"])
    if user:
        serialized = _serialize_user(user)
    else:  # Fallback to the minimal middleware payload
        serialized = {
            "user_id": current_user["user_id"],
            "email": current_user.get("email"),
            "full_name": current_user.get("full_name"),
            "roles": current_user.get("roles", []),
            "tenant_id": current_user.get("tenant_id", "default"),
            "two_factor_enabled": current_user.get("two_factor_enabled", False),
            "preferences": current_user.get("preferences", {}),
        }

    serialized["authenticated"] = True
    serialized["last_active"] = datetime.now(timezone.utc).isoformat()
    return serialized


@router.get("/validate-session", response_model=ValidateSessionResponse)
async def validate_session(request: Request) -> ValidateSessionResponse:
    auth_service = get_auth_service()
    token = _extract_token_from_request(request)
    if not token:
        return ValidateSessionResponse(valid=False)

    user = auth_service.validate_and_get_user_from_token(token)
    if not user:
        return ValidateSessionResponse(valid=False)

    return ValidateSessionResponse(valid=True, user=_serialize_user(user))


@router.post("/logout")
async def logout(_: Dict[str, Any] = Depends(require_auth)) -> JSONResponse:
    """Logout user (client should discard token)."""
    response = JSONResponse({"detail": "Successfully logged out"})
    response.delete_cookie("auth_token", path="/")
    return response


@router.post("/register", response_model=LoginResponse)
async def register(payload: RegisterRequest) -> JSONResponse:
    """Register new user."""
    auth_service = get_auth_service()
    try:
        user = auth_service.create_user(payload.email.lower(), payload.password, payload.full_name)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Registration failed: {exc}") from exc

    access_token, expires_in = auth_service.create_access_token(user)
    return _create_auth_response(user, access_token, expires_in)


@router.post("/dev-login", response_model=LoginResponse)
async def dev_login() -> JSONResponse:
    """Development login endpoint - automatically logs in as admin user."""
    if os.getenv("AUTH_ALLOW_DEV_LOGIN", "false").lower() not in ("1", "true", "yes"):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Dev login is disabled")

    auth_service = get_auth_service()
    user = auth_service.get_user_by_email("admin@example.com")
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default admin user not found")

    access_token, expires_in = auth_service.create_access_token(user)
    return _create_auth_response(user, access_token, expires_in)


@router.get("/health")
async def auth_health() -> Dict[str, Any]:
    """Authentication service health check."""
    auth_service = get_auth_service()
    try:
        users = auth_service._load_users()
        return {
            "status": "healthy",
            "service": "auth",
            "user_count": len(users),
            "storage": auth_service.storage_type,
            "mode": auth_service.auth_mode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Auth service unhealthy: {exc}") from exc


@router.get("/status")
async def auth_status() -> Dict[str, Any]:
    """Detailed authentication status for monitoring dashboards."""
    auth_service = get_auth_service()
    users = auth_service._load_users()
    return {
        "status": "healthy",
        "mode": auth_service.auth_mode,
        "provider": "simple-jwt",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "refresh": True,
            "long_lived_tokens": True,
            "password_reset": True,
            "two_factor": False,
        },
        "user_count": len(users),
    }


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: Request) -> JSONResponse:
    auth_service = get_auth_service()
    token = _extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    user = auth_service.validate_and_get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    new_token, expires_in = auth_service.create_access_token(user)
    return _create_auth_response(user, new_token, expires_in)


@router.post("/update_credentials", response_model=LoginResponse)
async def update_credentials(
    payload: UpdateCredentialsRequest,
    current_user: Dict[str, Any] = Depends(require_auth),
) -> JSONResponse:
    auth_service = get_auth_service()
    try:
        updated_user = auth_service.update_user_credentials(
            current_email=current_user["email"],
            new_email=payload.new_username,
            new_password=payload.new_password,
            full_name=payload.full_name,
        )
    except HTTPException:
        raise

    new_token, expires_in = auth_service.create_access_token(updated_user)
    return _create_auth_response(updated_user, new_token, expires_in)


@router.post("/request_password_reset")
async def request_password_reset(payload: PasswordResetRequest) -> Dict[str, Any]:
    auth_service = get_auth_service()
    token = auth_service.create_password_reset_token(payload.email.lower())

    response: Dict[str, Any] = {
        "detail": "If an account exists, password reset instructions have been sent.",
    }
    if token and os.getenv("AUTH_DEBUG_RESET_TOKENS", "false").lower() in ("1", "true", "yes"):
        response["debug_reset_token"] = token
    return response


@router.post("/reset_password")
async def reset_password(payload: PasswordResetConfirmRequest) -> Dict[str, Any]:
    auth_service = get_auth_service()
    auth_service.reset_password(payload.token, payload.new_password)
    return {"detail": "Password reset successful"}


@router.post("/create-long-lived-token", response_model=LoginResponse)
async def create_long_lived_token(request: Request) -> JSONResponse:
    auth_service = get_auth_service()
    token = _extract_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    user = auth_service.validate_and_get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    long_token, expires_in = auth_service.create_long_lived_token(user)
    return _create_auth_response(user, long_token, expires_in)
