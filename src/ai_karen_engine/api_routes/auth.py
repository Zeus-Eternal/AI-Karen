from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from datetime import datetime, timedelta
from collections import defaultdict
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from ai_karen_engine.utils.auth import (
    create_session,
    validate_session,
    SESSION_DURATION,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Session cookie configuration
COOKIE_NAME = "kari_session"

# Simple in-memory login rate limiter: max 5 attempts per minute per IP
_LOGIN_ATTEMPTS: Dict[str, List[datetime]] = defaultdict(list)
RATE_LIMIT = 5
RATE_WINDOW = timedelta(minutes=1)

# In-memory user store for demo purposes
_USERS: Dict[str, Dict[str, Any]] = {
    "admin@example.com": {
        "password": "admin",
        "roles": ["admin", "dev", "user"],
        "tenant_id": "admin_tenant",
        "preferences": {
            "personalityTone": "professional",
            "personalityVerbosity": "balanced",
            "memoryDepth": "deep",
            "customPersonaInstructions": "You are an advanced AI assistant with administrative capabilities.",
            "preferredLLMProvider": "ollama",
            "preferredModel": "llama3.2:latest",
            "temperature": 0.7,
            "maxTokens": 2000,
            "notifications": {"email": True, "push": False},
            "ui": {"theme": "dark", "language": "en"},
        },
    },
    "user@example.com": {
        "password": "user",
        "roles": ["user"],
        "tenant_id": "user_tenant",
        "preferences": {
            "personalityTone": "friendly",
            "personalityVerbosity": "balanced",
            "memoryDepth": "medium",
            "customPersonaInstructions": "You are a helpful and friendly AI assistant.",
            "preferredLLMProvider": "ollama",
            "preferredModel": "llama3.2:latest",
            "temperature": 0.7,
            "maxTokens": 1000,
            "notifications": {"email": True, "push": False},
            "ui": {"theme": "light", "language": "en"},
        },
    },
}


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request, response: Response) -> LoginResponse:
    # --- simple rate limiting ---
    ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()
    attempts = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < RATE_WINDOW]
    if len(attempts) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    attempts.append(now)
    _LOGIN_ATTEMPTS[ip] = attempts

    user = _USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    token = create_session(
        subject=req.email,
        roles=user["roles"],
        user_agent=request.headers.get("user-agent", ""),
        client_ip=ip,
        tenant_id=tenant_id,
    )

    # Set secure HttpOnly cookie for session
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return LoginResponse(
        token=token,
        user_id=req.email,
        email=req.email,
        roles=user["roles"],
        tenant_id=tenant_id,
        preferences=user.get("preferences", {}),
    )


@router.post("/token", response_model=TokenResponse)
async def token(req: LoginRequest, request: Request) -> TokenResponse:
    user = _USERS.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    access_token = create_session(
        subject=req.email,
        roles=user["roles"],
        user_agent=request.headers.get("user-agent", ""),
        client_ip=request.client.host,
        tenant_id=tenant_id,
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    auth = request.headers.get("authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
    elif COOKIE_NAME in request.cookies:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )
    ctx = validate_session(
        token, request.headers.get("user-agent", ""), request.client.host
    )
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_email = ctx["sub"]
    user_data = _USERS.get(user_email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(
        user_id=user_email,
        email=user_email,
        roles=list(ctx.get("roles", [])),
        tenant_id=user_data.get("tenant_id", "default"),
        preferences=user_data.get("preferences", {}),
    )


@router.post("/logout")
async def logout(response: Response) -> Dict[str, str]:
    """Clear authentication cookie."""
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "Logged out"}
