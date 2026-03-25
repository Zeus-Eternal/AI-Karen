"""
Production Authentication Routes

Enhanced authentication endpoints with security hardening, rate limiting,
and first-run setup flow.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
try:
    from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, EmailStr, Field, field_validator, model_validator

from ..auth.models import UserData
from ..auth.session import get_current_user as get_authenticated_user
from ..auth.rbac_middleware import get_rbac_manager
from ..services import AuthService
from ..core.services.base import ServiceConfig


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=1)
    
    @model_validator(mode='after')
    def validate_login_identifier(self):
        """Ensure either email or username is provided."""
        if not self.email and not self.username:
            raise ValueError('Either email or username must be provided')
        return self


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    permissions: List[str]


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class FirstRunSetupRequest(BaseModel):
    """First-run admin setup request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    confirm_password: str = Field(..., min_length=8)


class CreateUserRequest(BaseModel):
    """Create user request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    roles: Optional[list] = Field(default=["user"])


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    email: str
    full_name: str
    roles: list
    is_active: bool
    created_at: str
    last_login: Optional[str]
    tenant_id: str
    preferences: Dict[str, Any]


class UpdateProfileRequest(BaseModel):
    """Update the current user's profile."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, min_length=1)
    preferences: Optional[Dict[str, Any]] = None

    @model_validator(mode='after')
    def validate_payload(self):
        if self.email is None and self.full_name is None and self.preferences is None:
            raise ValueError("At least one profile field must be provided")
        return self


class ChangePasswordRequest(BaseModel):
    """Change the current user's password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)
    confirm_password: str = Field(..., min_length=1)

    @model_validator(mode='after')
    def validate_passwords(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirmation do not match")
        return self


# Initialize service with default configuration
# Use model_construct to bypass Pydantic validation for required fields
from ai_karen_engine.services.auth_service import AuthConfig
auth_config = AuthConfig.model_construct(
    name="auth_service",
    version="1.0.0"
)
auth_service = AuthService(config=auth_config)

# Router - prefix is empty since routes already include /auth/ prefix
router = APIRouter(prefix="", tags=["authentication"])


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent from request."""
    return request.headers.get("User-Agent", "unknown")


def _serialize_permissions(user_payload: Dict[str, Any]) -> List[str]:
    """Resolve canonical permission strings for the authenticated user."""

    rbac_manager = get_rbac_manager()
    user = UserData.from_dict(user_payload)
    permissions = {
        permission.value if hasattr(permission, "value") else str(permission)
        for permission in rbac_manager.get_user_permissions(user)
    }
    return sorted(permissions)


def _serialize_user_response(user: Any) -> Dict[str, Any]:
    """Normalize a user-like object into the public response shape."""

    user_id = str(getattr(user, "id", None) or getattr(user, "user_id", ""))
    created_at = getattr(user, "created_at", None)
    last_login = getattr(user, "last_login", None)
    tenant_id = getattr(user, "tenant_id", "default")

    return {
        "user_id": user_id,
        "email": getattr(user, "email", ""),
        "full_name": getattr(user, "full_name", "") or "",
        "roles": list(getattr(user, "roles", []) or []),
        "is_active": getattr(user, "status", None).value == "active" if getattr(user, "status", None) else getattr(user, "is_active", True),
        "created_at": created_at.isoformat() if created_at else datetime.now(timezone.utc).isoformat(),
        "last_login": last_login.isoformat() if last_login else None,
        "tenant_id": str(tenant_id) if tenant_id is not None else "default",
        "preferences": dict(getattr(user, "preferences", {}) or {}),
    }


# Startup/shutdown handlers commented out to prevent blocking during app startup
# The AuthService is already initialized when the module loads
# @router.on_event("startup")
# async def startup_auth_service():
#     """Initialize authentication service on startup."""
#     await auth_service.initialize()
#     await auth_service.start()


# @router.on_event("shutdown")
# async def shutdown_auth_service():
#     """Shutdown authentication service."""
#     await auth_service.stop()


@router.get("/auth/status")
async def auth_status() -> Dict[str, Any]:
    """Get authentication service status."""
    stats = await auth_service.get_auth_stats()
    
    return {
        "status": "healthy",
        "service": "production-auth",
        "mode": "jwt-authentication",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "authentication": True,
            "authorization": True,
            "rate_limiting": True,
            "account_lockout": True,
            "password_strength": True,
            "audit_logging": True
        },
        "stats": stats
    }


@router.get("/auth/health")
async def auth_health() -> Dict[str, Any]:
    """Authentication service health check."""
    is_healthy = await auth_service.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "production-auth",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/auth/first-run")
async def check_first_run() -> Dict[str, Any]:
    """Check if first-run setup is required."""
    is_first_run = await auth_service.is_first_run()
    
    return {
        "first_run_required": is_first_run,
        "message": "First-run setup required" if is_first_run else "System already configured"
    }


@router.post("/auth/first-run/setup")
async def first_run_setup(request: FirstRunSetupRequest, http_request: Request) -> JSONResponse:
    """Set up the first admin user."""
    # Check if first-run setup is actually needed
    if not await auth_service.is_first_run():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="First-run setup already completed"
        )
    
    # Validate password confirmation
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    try:
        # Create first admin user
        user = await auth_service.create_first_admin(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        # Authenticate the new admin user
        ip_address = get_client_ip(http_request)
        user_agent = get_user_agent(http_request)
        
        auth_user, access_token, refresh_token = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not auth_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate newly created admin user"
            )
        
        # Return login response
        user_data = {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.status.value == "active",
            "tenant_id": user.tenant_id,
            "preferences": user.preferences
        }
        
        permissions = _serialize_permissions(user_data)
        user_data["permissions"] = permissions

        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.config.access_token_expire_minutes * 60,
            "user": user_data,
            "permissions": permissions,
            "message": "First admin user created and authenticated successfully"
        }
        
        return JSONResponse(content=response_data, status_code=status.HTTP_201_CREATED)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin user: {str(e)}"
        )


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request) -> JSONResponse:
    """Authenticate user and return tokens."""
    import logging
    logging.warning("==== LOGIN ENDPOINT HIT ====")
    ip_address = get_client_ip(http_request)
    user_agent = get_user_agent(http_request)
    
    # Determine login identifier (email or username)
    login_identifier = request.email or request.username
    
    logging.warning(f"=== LOGIN: auth_service type is {type(auth_service)} ===")
    logging.warning("=== LOGIN: calling auth_service.authenticate_user ===")
    import asyncio
    logging.warning("=== LOGIN: yielding to event loop ===")
    await asyncio.sleep(0)
    logging.warning("=== LOGIN: event loop yielded successfully ===")
    
    import logging
    logging.warning("=== LOGIN: creating coroutine ===")
    coro = auth_service.authenticate_user(
        login_identifier,  # positional string
        request.password,  # positional string
        ip_address=ip_address,
        user_agent=user_agent
    )
    logging.warning(f"=== LOGIN: created coroutine: {type(coro)} ===")
    
    logging.warning("=== LOGIN: awaiting coroutine ===")
    user, access_token, refresh_token_or_error = await coro
    logging.warning("=== LOGIN: auth_service.authenticate_user RETURNED ===")
    
    if not user:
        # refresh_token_or_error contains error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=refresh_token_or_error,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logging.warning("=== LOGIN: preparing user data ===")
    user_data = {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "is_active": user.status.value == "active",
        "tenant_id": user.tenant_id,
        "preferences": user.preferences,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
    logging.warning("=== LOGIN: user data prepared ===")
    
    logging.warning("=== LOGIN: serializing permissions ===")
    permissions = _serialize_permissions(user_data)
    user_data["permissions"] = permissions
    logging.warning(f"=== LOGIN: permissions serialized: {len(permissions)} items ===")

    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token_or_error,  # This is refresh_token on success
        "token_type": "bearer",
        "expires_in": auth_service.config.access_token_expire_minutes * 60,
        "user": user_data,
        "permissions": permissions
    }
    logging.warning("=== LOGIN: response data prepared ===")

    # Create response and set HttpOnly cookie for enhanced security
    logging.warning("=== LOGIN: creating JSONResponse ===")
    response = JSONResponse(content=response_data)
    logging.warning("=== LOGIN: JSONResponse created ===")

    # Determine if we should use secure cookies (HTTPS only)
    is_secure = http_request.url.scheme == "https"

    # Set the kari_session cookie with the access token
    # This allows the auth middleware to authenticate requests via cookie
    response.set_cookie(
        key="kari_session",
        value=access_token,
        max_age=auth_service.config.access_token_expire_minutes * 60,  # Convert to seconds
        httponly=True,  # Prevent JavaScript access (XSS protection)
        secure=is_secure,  # Only send over HTTPS in production
        samesite="lax",  # CSRF protection while allowing navigation
        path="/",  # Available for all routes
    )

    return response


@router.post("/auth/refresh")
async def refresh_token(request: RefreshTokenRequest, http_request: Request) -> JSONResponse:
    """Refresh access token using refresh token."""
    access_token, error = await auth_service.refresh_access_token(request.refresh_token)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.config.access_token_expire_minutes * 60
    }

    response = JSONResponse(content=response_data)
    response.set_cookie(
        key="kari_session",
        value=access_token,
        max_age=auth_service.config.access_token_expire_minutes * 60,
        httponly=True,
        secure=http_request.url.scheme == "https",
        samesite="lax",
        path="/",
    )

    return response


@router.post("/auth/logout")
async def logout(
    request: RefreshTokenRequest,
    current_user=Depends(get_authenticated_user),
) -> JSONResponse:
    """Logout user by invalidating refresh token."""
    await auth_service.logout(request.refresh_token)

    response = JSONResponse(content={"detail": "Successfully logged out"})
    response.delete_cookie("kari_session", path="/")
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return response


@router.get("/auth/validate-session")
async def validate_session(current_user=Depends(get_authenticated_user)) -> Dict[str, Any]:
    """Validate current session and return user information."""
    user_payload = _serialize_user_response(current_user)
    permissions = _serialize_permissions(user_payload)
    user_payload["permissions"] = permissions
    return {
        "valid": True,
        "user": user_payload,
        "permissions": permissions,
        "authenticated": True,
        "session_valid": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_authenticated_user)) -> Dict[str, Any]:
    """Get current user information."""
    response = _serialize_user_response(current_user)
    response["authenticated"] = True
    response["last_active"] = datetime.now(timezone.utc).isoformat()
    return response


@router.put("/auth/me", response_model=UserResponse)
async def update_current_user_info(
    request: UpdateProfileRequest,
    current_user=Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """Update current user information."""

    current_user_id = str(getattr(current_user, "id", None) or getattr(current_user, "user_id", ""))

    updated_user, error = await auth_service.update_user_profile(
        current_user_id,
        email=str(request.email) if request.email is not None else None,
        full_name=request.full_name,
        preferences=request.preferences,
    )

    if not updated_user:
        status_code = status.HTTP_400_BAD_REQUEST
        if error == "User not found":
            status_code = status.HTTP_404_NOT_FOUND
        elif error == "User with this email already exists":
            status_code = status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=error or "Failed to update profile")

    return _serialize_user_response(updated_user)


@router.post("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user=Depends(get_authenticated_user),
) -> Dict[str, str]:
    """Change the current user's password."""

    current_user_id = str(getattr(current_user, "id", None) or getattr(current_user, "user_id", ""))

    error = await auth_service.change_user_password(
        current_user_id,
        request.current_password,
        request.new_password,
    )

    if error:
        status_code = status.HTTP_400_BAD_REQUEST
        if error == "Current password is incorrect":
            status_code = status.HTTP_401_UNAUTHORIZED
        elif error == "User not found":
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=error)

    return {"detail": "Password updated successfully"}


@router.post("/auth/create-user", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user=Depends(get_authenticated_user)
) -> JSONResponse:
    """Create a new user (admin only)."""
    # Check if current user has admin privileges
    if "admin" not in current_user.roles and "super_admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to create users"
        )
    
    user, error = await auth_service.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        roles=request.roles
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    user_data = {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "is_active": user.status.value == "active",
        "created_at": user.created_at.isoformat(),
        "last_login": None,
        "tenant_id": user.tenant_id,
        "preferences": user.preferences
    }
    
    return JSONResponse(content=user_data, status_code=status.HTTP_201_CREATED)


@router.get("/auth/stats", response_model=None)
async def get_auth_stats(current_user=Depends(get_authenticated_user)) -> Dict[str, Any]:
    """Get authentication statistics (admin only)."""
    # Check if current user has admin privileges
    if "admin" not in current_user.roles and "super_admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to view authentication statistics"
        )
    
    stats = await auth_service.get_auth_stats()
    return stats


@router.get("/auth/security/context")
async def get_security_context(current_user=Depends(get_authenticated_user)) -> Dict[str, Any]:
    """Get security context for authenticated user."""
    return {
        "userRoles": current_user.get("roles", []),
        "securityMode": "safe",  # Default to safe mode
        "canAccessSensitive": current_user.get("roles", []).intersection(["admin", "super_admin"]) != set(),
        "redactionLevel": "partial"  # Default to partial redaction
    }
