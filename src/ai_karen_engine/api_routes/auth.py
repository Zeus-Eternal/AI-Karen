from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ai_karen_engine.utils.auth import create_session, validate_session

router = APIRouter(prefix="/api/auth")

# In-memory user store for demo purposes
_USERS: Dict[str, Dict[str, Any]] = {
    "admin": {"password": "admin", "roles": ["admin", "dev", "user"]},
    "user": {"password": "user", "roles": ["user"]},
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    roles: list[str]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    roles: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
    user = _USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    token = create_session(
        req.username,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id,
    )
    return LoginResponse(token=token, user_id=req.username, roles=user["roles"])


@router.post("/token", response_model=TokenResponse)
async def token(req: LoginRequest, request: Request) -> TokenResponse:
    """Issue an OAuth2-compatible bearer token."""
    user = _USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_session(req.username, user["roles"], request.headers.get("user-agent", ""), request.client.host)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return UserResponse(user_id=ctx["sub"], roles=list(ctx.get("roles", [])))
