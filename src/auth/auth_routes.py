"""
No Authentication Routes for AI-Karen.
Provides minimal endpoints that return default user data without authentication.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .auth_service import (
    get_auth_service,
    LoginRequest,
    LoginResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_default_response() -> JSONResponse:
    """Create response with default user data"""
    auth_service = get_auth_service()
    user = auth_service.default_user
    user_payload = auth_service.serialize_user(user)
    
    body: Dict[str, Any] = {
        "access_token": "no-auth-token",
        "token": "no-auth-token",
        "refresh_token": "no-auth-token",
        "token_type": "bearer",
        "expires_in": 86400,
        "user": user_payload,
        "user_data": user_payload,
        "user_id": user_payload["user_id"],
        "email": user_payload["email"],
        "roles": user_payload["roles"],
        "tenant_id": user_payload.get("tenant_id", "default"),
    }
    return JSONResponse(body)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> JSONResponse:
    """No authentication required - always return default user."""
    return _create_default_response()


@router.get("/me")
async def get_current_user_info() -> Dict[str, Any]:
    """Get current user information (always returns default user)."""
    auth_service = get_auth_service()
    user = auth_service.default_user
    serialized = auth_service.serialize_user(user)
    serialized["authenticated"] = True
    serialized["last_active"] = datetime.now(timezone.utc).isoformat()
    return serialized


@router.post("/logout")
async def logout() -> JSONResponse:
    """Logout user (no-op in no-auth mode)."""
    return JSONResponse({"detail": "Successfully logged out"})


@router.post("/register", response_model=LoginResponse)
async def register() -> JSONResponse:
    """Register new user (always returns default user)."""
    return _create_default_response()


@router.get("/health")
async def auth_health() -> Dict[str, Any]:
    """Authentication service health check."""
    return {
        "status": "healthy",
        "service": "no-auth",
        "mode": "no-authentication",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/status")
async def auth_status() -> Dict[str, Any]:
    """Authentication status - no auth mode."""
    return {
        "status": "healthy",
        "mode": "no-authentication",
        "provider": "none",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "authentication": False,
            "authorization": False,
        },
    }


@router.get("/validate-session")
async def validate_session() -> Dict[str, Any]:
    """Validate current session (always valid in no-auth mode)."""
    auth_service = get_auth_service()
    user = auth_service.default_user
    user_payload = auth_service.serialize_user(user)
    
    return {
        "valid": True,
        "user": user_payload,
        "authenticated": True,
        "session_id": "no-auth-session",
        "expires_at": None,  # Never expires in no-auth mode
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/dev-login")
async def dev_login() -> JSONResponse:
    """Development login endpoint (same as regular login in no-auth mode)."""
    return _create_default_response()
