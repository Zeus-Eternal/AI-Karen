from __future__ import annotations


from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ai_karen_engine.utils.auth import create_session, validate_session
from ai_karen_engine.security.auth_manager import (
    authenticate,
    update_credentials,
    _USERS,
)

router = APIRouter(prefix="/api/auth")

<<<<<<< Updated upstream
# Persistent user store managed by ``auth_manager``
=======
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
            "ui": {"theme": "dark", "language": "en"}
        }
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
            "ui": {"theme": "light", "language": "en"}
        }
    },
}
>>>>>>> Stashed changes


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    roles: list[str]
    tenant_id: str
    preferences: Dict[str, Any]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    tenant_id: str
    preferences: Dict[str, Any]


class UpdateCredentialsRequest(BaseModel):
    new_username: str | None = None
    new_password: str | None = None


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
<<<<<<< Updated upstream
    user = authenticate(req.username, req.password)
    if not user:
=======
    user = _USERS.get(req.email)
    if not user or user["password"] != req.password:
>>>>>>> Stashed changes
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tenant_id = user.get("tenant_id", request.headers.get("X-Tenant-ID", "default"))
    token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id,
    )
    return LoginResponse(
        token=token, 
        user_id=req.email, 
        email=req.email,
        roles=user["roles"],
        tenant_id=tenant_id,
        preferences=user.get("preferences", {})
    )


@router.post("/token", response_model=TokenResponse)
async def token(req: LoginRequest, request: Request) -> TokenResponse:
    """Issue an OAuth2-compatible bearer token."""
<<<<<<< Updated upstream
    user = authenticate(req.username, req.password)
    if not user:
=======
    user = _USERS.get(req.email)
    if not user or user["password"] != req.password:
>>>>>>> Stashed changes
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tenant_id = user.get("tenant_id", request.headers.get("X-Tenant-ID", "default"))
    token = create_session(req.email, user["roles"], request.headers.get("user-agent", ""), request.client.host, tenant_id)
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
<<<<<<< Updated upstream
    return UserResponse(user_id=ctx["sub"], roles=list(ctx.get("roles", [])))


@router.post("/update_credentials", response_model=LoginResponse)
async def update_creds(req: UpdateCredentialsRequest, request: Request) -> LoginResponse:
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(None, 1)[1]
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    username = update_credentials(ctx["sub"], req.new_username, req.new_password)
    user = _USERS[username]
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    new_token = create_session(
        username,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id,
    )
    return LoginResponse(token=new_token, user_id=username, roles=user["roles"])
=======
    
    # Get user data from our in-memory store
    user_email = ctx["sub"]
    user_data = _USERS.get(user_email)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserResponse(
        user_id=user_email,
        email=user_email,
        roles=list(ctx.get("roles", [])),
        tenant_id=user_data.get("tenant_id", "default"),
        preferences=user_data.get("preferences", {})
    )
>>>>>>> Stashed changes
