from __future__ import annotations

try:
    from fastapi import APIRouter, HTTPException, Request, Response, status
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import APIRouter, HTTPException, Request, Response, status

from datetime import datetime, timedelta
from collections import defaultdict
try:
    from pydantic import BaseModel
except Exception:
    from ai_karen_engine.pydantic_stub import BaseModel
from typing import Any, Dict, List, Optional

from ai_karen_engine.utils.auth import (
    create_session,
    validate_session,
    SESSION_DURATION,
)
from ai_karen_engine.security.auth_manager import (
    authenticate,
    update_credentials,
    create_user,
    _USERS,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Session cookie configuration
COOKIE_NAME = "kari_session"

# Simple in-memory login rate limiter: max 5 attempts per minute per IP
_LOGIN_ATTEMPTS: Dict[str, List[datetime]] = defaultdict(list)
RATE_LIMIT = 5
RATE_WINDOW = timedelta(minutes=1)

# Persistent user store loaded via security.auth_manager


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    roles: Optional[List[str]] = None
    tenant_id: str = "default"
    preferences: Dict[str, Any] = {}


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


class UpdateCredentialsRequest(BaseModel):
    new_username: Optional[str] = None
    new_password: Optional[str] = None


@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, request: Request, response: Response) -> LoginResponse:
    if req.email in _USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    try:
        create_user(req.email, req.password, roles=req.roles, tenant_id=req.tenant_id, preferences=req.preferences)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    user = _USERS[req.email]
    token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id=user.get("tenant_id", "default"),
    )
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
        tenant_id=user.get("tenant_id", "default"),
        preferences=user.get("preferences", {}),
    )


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

    user = authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        ip,
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
    user = authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    access_token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
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


@router.post("/update_credentials", response_model=LoginResponse)
async def update_creds(
    req: UpdateCredentialsRequest, request: Request, response: Response
) -> LoginResponse:
    """Update the current user's credentials and return a new session."""
    auth = request.headers.get("authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
    elif COOKIE_NAME in request.cookies:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    ctx = validate_session(
        token, request.headers.get("user-agent", ""), request.client.host
    )
    if not ctx:
        raise HTTPException(status_code=401, detail="Invalid token")

    current_username = ctx["sub"]
    try:
        new_username = update_credentials(
            current_username, req.new_username, req.new_password
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = _USERS.get(new_username)
    tenant_id = user.get("tenant_id", "default")

    new_token = create_session(
        new_username,
        user.get("roles", []),
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id=tenant_id,
    )

    response.set_cookie(
        COOKIE_NAME,
        new_token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return LoginResponse(
        token=new_token,
        user_id=new_username,
        email=new_username,
        roles=user.get("roles", []),
        tenant_id=tenant_id,
        preferences=user.get("preferences", {}),
    )


@router.post("/logout")
async def logout(response: Response) -> Dict[str, str]:
    """Clear authentication cookie."""
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "Logged out"}
