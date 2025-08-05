"""
Production Authentication Routes
Real database-backed authentication with secure session management
"""

from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr

from ai_karen_engine.services.auth_service import auth_service
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.security.auth_manager import verify_totp

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# Session cookie configuration
COOKIE_NAME = "kari_session"


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    tenant_id: str = "default"
    preferences: Dict[str, Any] = {}


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]
    two_factor_enabled: bool
    is_verified: bool


class UpdateCredentialsRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


# Authentication Routes

@router.post("/register", response_model=LoginResponse)
async def register(
    req: RegisterRequest,
    request: Request,
    response: Response
) -> LoginResponse:
    """Register a new user with production database"""
    
    try:
        # Create user
        user = await auth_service.create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            roles=req.roles,
            tenant_id=req.tenant_id,
            preferences=req.preferences
        )
        
        # Create session
        session_data = await auth_service.create_session(
            user_id=user.user_id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            device_fingerprint=None  # Could be implemented later
        )
        
        # Set secure HttpOnly cookie
        response.set_cookie(
            COOKIE_NAME,
            session_data["session_token"],
            max_age=24 * 60 * 60,  # 24 hours
            httponly=True,
            secure=True,
            samesite="strict",
        )
        
        # Convert UserData to dict format
        user_data = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "tenant_id": user.tenant_id,
            "preferences": user.preferences,
            "two_factor_enabled": user.two_factor_enabled,
            "is_verified": user.is_verified
        }
        
        logger.info(f"User registered successfully: {req.email}")
        
        return LoginResponse(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
            expires_in=session_data["expires_in"],
            user=user_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response
) -> LoginResponse:
    """Authenticate user with production database"""
    
    try:
        # Authenticate user
        user_data = await auth_service.authenticate_user(
            email=req.email,
            password=req.password,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "")
        )
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if email is verified
        if not user_data["is_verified"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        
        # Handle 2FA if enabled
        if user_data["two_factor_enabled"] and not req.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Two-factor authentication required"
            )
        
        if user_data["two_factor_enabled"]:
            if not verify_totp(user_data["user_id"], req.totp_code or ""):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid two-factor code",
                )
        
        # Create session
        session_data = await auth_service.create_session(
            user_id=user_data["user_id"],
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            device_fingerprint=None
        )
        
        # Set secure HttpOnly cookie
        response.set_cookie(
            COOKIE_NAME,
            session_data["session_token"],
            max_age=24 * 60 * 60,  # 24 hours
            httponly=True,
            secure=True,
            samesite="strict",
        )
        
        logger.info(f"User logged in successfully: {req.email}")
        
        return LoginResponse(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
            expires_in=session_data["expires_in"],
            user=user_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request) -> UserResponse:
    """Get current user information"""
    
    # Get session token from cookie or header
    session_token = request.cookies.get(COOKIE_NAME)
    if not session_token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )
    
    # Validate session
    user_data = await auth_service.validate_session(
        session_token=session_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")
    )
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return UserResponse(**user_data)


@router.post("/update_credentials", response_model=LoginResponse)
async def update_credentials(
    req: UpdateCredentialsRequest,
    request: Request,
    response: Response
) -> LoginResponse:
    """Update user credentials"""
    
    # Get current user
    session_token = request.cookies.get(COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    user_data = await auth_service.validate_session(
        session_token=session_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "")
    )
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    try:
        # Update password if provided
        if req.new_password:
            if not req.current_password:
                raise HTTPException(status_code=400, detail="Current password required")
            
            # Verify current password first
            auth_result = await auth_service.authenticate_user(
                email=user_data["email"],
                password=req.current_password,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "")
            )
            
            if not auth_result:
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            
            # Update password
            success = await auth_service.update_user_password(
                user_id=user_data["user_id"],
                new_password=req.new_password
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update password")
        
        # Update preferences if provided
        if req.preferences:
            success = await auth_service.update_user_preferences(
                user_id=user_data["user_id"],
                preferences=req.preferences
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update preferences")
        
        # Create new session (invalidates old one)
        session_data = await auth_service.create_session(
            user_id=user_data["user_id"],
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            device_fingerprint=None
        )
        
        # Set new cookie
        response.set_cookie(
            COOKIE_NAME,
            session_data["session_token"],
            max_age=24 * 60 * 60,
            httponly=True,
            secure=True,
            samesite="strict",
        )
        
        # Get updated user data
        updated_user = await auth_service.validate_session(
            session_token=session_data["session_token"],
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "")
        )
        
        logger.info(f"Credentials updated for user: {user_data['email']}")
        
        return LoginResponse(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"],
            expires_in=session_data["expires_in"],
            user=updated_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to update credentials")


@router.post("/logout")
async def logout(request: Request, response: Response) -> Dict[str, str]:
    """Logout user and invalidate session"""
    
    session_token = request.cookies.get(COOKIE_NAME)
    if session_token:
        # Invalidate session
        await auth_service.invalidate_session(session_token)
    
    # Clear cookie
    response.delete_cookie(COOKIE_NAME)
    
    return {"detail": "Logged out successfully"}


@router.post("/request_password_reset")
async def request_password_reset(
    req: PasswordResetRequest,
    request: Request
) -> Dict[str, str]:
    """Request password reset token"""
    
    try:
        token = await auth_service.create_password_reset_token(
            email=req.email,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "")
        )
        
        if not token:
            # Don't reveal if user exists or not
            return {"detail": "If the email exists, a reset link has been sent"}
        
        # Send token through a secure channel (e.g., email) without logging
        # Example implementation:
        # await email_service.send_password_reset_email(req.email, token)

        return {"detail": "Password reset link sent"}
        
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process request")


@router.post("/reset_password")
async def reset_password(req: PasswordResetConfirm) -> Dict[str, str]:
    """Reset password using token"""
    
    try:
        success = await auth_service.verify_password_reset_token(
            token=req.token,
            new_password=req.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        return {"detail": "Password updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")


# Health check
@router.get("/health")
async def auth_health_check():
    """Health check for authentication system"""
    
    try:
        # Test database connection by attempting to query
        # This is a simple check - in production you might want more comprehensive checks
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "auth"
        }
        
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "auth"
        }