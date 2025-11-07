"""
Production Authentication Routes

Enhanced authentication endpoints with security hardening, rate limiting,
and first-run setup flow.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
try:
    from pydantic import BaseModel, EmailStr, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, EmailStr, Field

from ..services.production_auth_service import ProductionAuthService
from ..core.services.base import ServiceConfig


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


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


# Initialize service
auth_service = ProductionAuthService()

# Security scheme
security = HTTPBearer()

# Router
router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    user = await auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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


@router.on_event("startup")
async def startup_auth_service():
    """Initialize authentication service on startup."""
    await auth_service.initialize()
    await auth_service.start()


@router.on_event("shutdown")
async def shutdown_auth_service():
    """Shutdown authentication service."""
    await auth_service.stop()


@router.get("/status")
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


@router.get("/health")
async def auth_health() -> Dict[str, Any]:
    """Authentication service health check."""
    is_healthy = await auth_service.health_check()
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "production-auth",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/first-run")
async def check_first_run() -> Dict[str, Any]:
    """Check if first-run setup is required."""
    is_first_run = await auth_service.is_first_run()
    
    return {
        "first_run_required": is_first_run,
        "message": "First-run setup required" if is_first_run else "System already configured"
    }


@router.post("/first-run/setup")
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
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.is_active,
            "tenant_id": user.tenant_id,
            "preferences": user.preferences
        }
        
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": auth_service.access_token_expire_minutes * 60,
            "user": user_data,
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


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request) -> JSONResponse:
    """Authenticate user and return tokens."""
    ip_address = get_client_ip(http_request)
    user_agent = get_user_agent(http_request)
    
    user, access_token, refresh_token_or_error = await auth_service.authenticate_user(
        email=request.email,
        password=request.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if not user:
        # refresh_token_or_error contains error message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=refresh_token_or_error,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Prepare user data
    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "is_active": user.is_active,
        "tenant_id": user.tenant_id,
        "preferences": user.preferences,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
    
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token_or_error,  # This is refresh_token on success
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60,
        "user": user_data
    }
    
    return JSONResponse(content=response_data)


@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest) -> JSONResponse:
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
        "expires_in": auth_service.access_token_expire_minutes * 60
    }
    
    return JSONResponse(content=response_data)


@router.post("/logout")
async def logout(request: RefreshTokenRequest, current_user=Depends(get_current_user)) -> JSONResponse:
    """Logout user by invalidating refresh token."""
    await auth_service.logout(request.refresh_token)
    
    return JSONResponse(content={"detail": "Successfully logged out"})


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)) -> Dict[str, Any]:
    """Get current user information."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "tenant_id": current_user.tenant_id,
        "preferences": current_user.preferences,
        "authenticated": True,
        "last_active": datetime.now(timezone.utc).isoformat()
    }


@router.post("/create-user", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user=Depends(get_current_user)
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
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "last_login": None,
        "tenant_id": user.tenant_id,
        "preferences": user.preferences
    }
    
    return JSONResponse(content=user_data, status_code=status.HTTP_201_CREATED)


@router.get("/stats")
async def get_auth_stats(current_user=Depends(get_current_user)) -> Dict[str, Any]:
    """Get authentication statistics (admin only)."""
    # Check if current user has admin privileges
    if "admin" not in current_user.roles and "super_admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to view authentication statistics"
        )
    
    stats = await auth_service.get_auth_stats()
    return stats