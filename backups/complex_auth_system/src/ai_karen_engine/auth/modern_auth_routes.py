"""
Modern Authentication Routes - 2024 Edition
Clean, secure authentication endpoints with modern best practices
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from .enhanced_auth_service import get_enhanced_auth_service, EnhancedAuthService
from .modern_auth_middleware import ModernJWTManager, ModernSecurityConfig, CSRFProtection

import logging
logger = logging.getLogger(__name__)

# Initialize components
config = ModernSecurityConfig()
jwt_manager = ModernJWTManager(config)
csrf_protection = CSRFProtection(config)

router = APIRouter(tags=["modern-auth"], prefix="/auth")

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    remember_me: bool = False
    device_fingerprint: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    csrf_token: Optional[str] = None
    session_id: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    tenant_id: str
    is_verified: bool
    preferences: Dict[str, Any]
    last_login: Optional[datetime]

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class UpdatePreferencesRequest(BaseModel):
    preferences: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Utility functions
async def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    xff = request.headers.get("x-forwarded-for")
    ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "unknown")
    
    return {
        "ip_address": ip,
        "user_agent": request.headers.get("user-agent", ""),
        "device_fingerprint": request.headers.get("x-device-fingerprint")
    }

def set_secure_cookie(response: Response, name: str, value: str, max_age: int = None):
    """Set secure cookie with proper flags"""
    response.set_cookie(
        name,
        value,
        max_age=max_age or config.session_max_age,
        httponly=True,
        secure=config.session_cookie_secure,
        samesite=config.session_cookie_samesite,
        path="/"
    )

# Authentication Routes

@router.post("/register", response_model=LoginResponse)
async def register(
    req: RegisterRequest,
    response: Response,
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> LoginResponse:
    """Register new user with modern security"""
    
    if not req.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted"
        )
    
    client_info = await get_client_info(request)
    
    try:
        # Create user
        user_data = await auth_service.register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        
        # Create session
        session_data = await auth_service.create_session(
            user_data=user_data,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            device_fingerprint=client_info["device_fingerprint"]
        )
        
        # Create tokens
        access_token = jwt_manager.create_access_token(user_data)
        refresh_token = jwt_manager.create_refresh_token(user_data)
        
        # Set secure session cookie
        set_secure_cookie(response, config.session_cookie_name, session_data["session_id"])
        
        # Generate CSRF token
        csrf_token = csrf_protection.generate_csrf_token(session_data["session_id"])
        set_secure_cookie(response, config.csrf_cookie_name, csrf_token)
        
        logger.info(f"User registered successfully: {user_data['email']}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=config.jwt_access_token_expire_minutes * 60,
            user=user_data,
            csrf_token=csrf_token,
            session_id=session_data["session_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    response: Response,
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> LoginResponse:
    """Login user with enhanced security"""
    
    client_info = await get_client_info(request)
    
    try:
        # Authenticate user
        user_data = await auth_service.authenticate_user(
            email=req.email,
            password=req.password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            device_fingerprint=req.device_fingerprint or client_info["device_fingerprint"]
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create session
        session_data = await auth_service.create_session(
            user_data=user_data,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            device_fingerprint=req.device_fingerprint or client_info["device_fingerprint"]
        )
        
        # Create tokens with extended expiry if remember_me
        if req.remember_me:
            # Extend token expiry for remember me
            user_data_extended = user_data.copy()
            access_token = jwt_manager.create_access_token(user_data_extended)
            refresh_token = jwt_manager.create_refresh_token(user_data_extended)
            cookie_max_age = 30 * 24 * 60 * 60  # 30 days
        else:
            access_token = jwt_manager.create_access_token(user_data)
            refresh_token = jwt_manager.create_refresh_token(user_data)
            cookie_max_age = config.session_max_age
        
        # Set secure session cookie
        set_secure_cookie(response, config.session_cookie_name, session_data["session_id"], cookie_max_age)
        
        # Generate CSRF token
        csrf_token = csrf_protection.generate_csrf_token(session_data["session_id"])
        set_secure_cookie(response, config.csrf_cookie_name, csrf_token, cookie_max_age)
        
        logger.info(f"User logged in successfully: {user_data['email']}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=config.jwt_access_token_expire_minutes * 60,
            user=user_data,
            csrf_token=csrf_token,
            session_id=session_data["session_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/refresh")
async def refresh_token(
    req: RefreshTokenRequest,
    response: Response,
    request: Request
) -> Dict[str, Any]:
    """Refresh access token"""
    
    try:
        # Verify refresh token
        payload = jwt_manager.verify_token(req.refresh_token, "refresh")
        
        # Create new access token
        user_data = {
            "user_id": payload["sub"],
            "email": payload.get("email", ""),
            "roles": payload.get("roles", []),
            "tenant_id": payload.get("tenant_id", "default")
        }
        
        new_access_token = jwt_manager.create_access_token(user_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": config.jwt_access_token_expire_minutes * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> UserResponse:
    """Get current user information"""
    
    # Get session from cookie
    session_id = request.cookies.get(config.session_cookie_name)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    client_info = await get_client_info(request)
    
    try:
        user_data = await auth_service.validate_session(
            session_id=session_id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> Dict[str, str]:
    """Logout user and invalidate session"""
    
    session_id = request.cookies.get(config.session_cookie_name)
    
    if session_id:
        try:
            await auth_service.invalidate_session(session_id)
        except Exception as e:
            logger.error(f"Session invalidation error: {e}")
    
    # Clear cookies
    response.delete_cookie(config.session_cookie_name, path="/")
    response.delete_cookie(config.csrf_cookie_name, path="/")
    
    return {"detail": "Logged out successfully"}

@router.post("/update-password")
async def update_password(
    req: UpdatePasswordRequest,
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> Dict[str, str]:
    """Update user password"""
    
    # Get current user from session
    session_id = request.cookies.get(config.session_cookie_name)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    client_info = await get_client_info(request)
    
    try:
        user_data = await auth_service.validate_session(
            session_id=session_id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        # Verify current password by attempting authentication
        auth_result = await auth_service.authenticate_user(
            email=user_data["email"],
            password=req.current_password,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        success = await auth_service.update_user_password(
            user_id=user_data["user_id"],
            new_password=req.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        logger.info(f"Password updated for user: {user_data['email']}")
        return {"detail": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

@router.post("/update-preferences")
async def update_preferences(
    req: UpdatePreferencesRequest,
    request: Request,
    auth_service: EnhancedAuthService = Depends(get_enhanced_auth_service)
) -> Dict[str, str]:
    """Update user preferences"""
    
    # Get current user from session
    session_id = request.cookies.get(config.session_cookie_name)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session"
        )
    
    client_info = await get_client_info(request)
    
    try:
        user_data = await auth_service.validate_session(
            session_id=session_id,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session"
            )
        
        # Update preferences
        success = await auth_service.update_user_preferences(
            user_id=user_data["user_id"],
            preferences=req.preferences
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences"
            )
        
        return {"detail": "Preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preferences update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )

# Health and utility endpoints

@router.get("/health")
async def auth_health() -> Dict[str, Any]:
    """Authentication service health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "modern-auth",
        "version": "2024.1"
    }

@router.get("/demo-users")
async def get_demo_users() -> Dict[str, Any]:
    """Get demo user credentials for testing"""
    return {
        "demo_users": [
            {
                "email": "admin@kari.ai",
                "password": "password123",
                "roles": ["super_admin", "admin", "user"],
                "description": "Main admin user with full privileges"
            }
        ],
        "note": "Demo credentials for development and testing. Change passwords in production.",
        "password_requirements": {
            "min_length": 8,
            "required_types": "At least 3 of: uppercase, lowercase, digits, special characters"
        }
    }

# Export router
__all__ = ["router"]
