"""
Simple Authentication Routes for AI-Karen
Clean, production-ready auth endpoints with minimal complexity.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request

from .auth_service import (
    get_auth_service, 
    LoginRequest, 
    LoginResponse, 
    UserModel
)
from .auth_middleware import get_current_user, require_auth

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate user and return JWT token"""
    auth_service = get_auth_service()
    
    # Authenticate user
    user = auth_service.authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token, expires_in = auth_service.create_access_token(user)
    
    # Return response
    return LoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.is_active
        }
    )

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, Any]:
    """Get current user information"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "roles": current_user["roles"],
        "authenticated": True
    }

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(require_auth)) -> Dict[str, str]:
    """Logout user (client should discard token)"""
    # With JWT, we don't need to do anything server-side
    # The client should discard the token
    return {"detail": "Successfully logged out"}

@router.post("/register", response_model=LoginResponse)
async def register(
    email: str, 
    password: str, 
    full_name: str = None
) -> LoginResponse:
    """Register new user (optional endpoint)"""
    auth_service = get_auth_service()
    
    try:
        # Create user
        user = auth_service.create_user(email, password, full_name)
        
        # Create access token
        access_token, expires_in = auth_service.create_access_token(user)
        
        # Return response
        return LoginResponse(
            access_token=access_token,
            expires_in=expires_in,
            user={
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": user.roles,
                "is_active": user.is_active
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/dev-login", response_model=LoginResponse)
async def dev_login() -> LoginResponse:
    """Development login endpoint - automatically logs in as admin user"""
    import os
    
    # Check if dev login is enabled
    if not os.getenv("AUTH_ALLOW_DEV_LOGIN", "false").lower() in ("1", "true", "yes"):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Dev login is disabled"
        )
    
    auth_service = get_auth_service()
    
    # Get the default admin user
    users = auth_service._load_users()
    admin_email = "admin@example.com"
    
    if admin_email not in users:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default admin user not found"
        )
    
    user = UserModel(**users[admin_email])
    
    # Create access token
    access_token, expires_in = auth_service.create_access_token(user)
    
    # Return response
    return LoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "is_active": user.is_active
        }
    )

@router.get("/health")
async def auth_health() -> Dict[str, str]:
    """Authentication service health check"""
    auth_service = get_auth_service()
    
    try:
        # Test storage access
        users = auth_service._load_users()
        user_count = len(users)
        
        return {
            "status": "healthy",
            "service": "auth",
            "users": str(user_count),
            "storage": auth_service.storage_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth service unhealthy: {str(e)}"
        )
