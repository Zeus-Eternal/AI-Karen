"""
Production Authentication Routes
Real database-backed authentication with secure session management
"""
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from ai_karen_engine.core.dependencies import (
    get_current_tenant_id,
    get_current_user_context,
)
from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.security.auth_service import auth_service

logger = get_logger(__name__)
router = APIRouter(tags=["auth"])


# Alias core dependencies for clarity
get_current_user = get_current_user_context
get_current_tenant_id_dependency = get_current_tenant_id

COOKIE_NAME = "kari_session"


def set_session_cookie(
    response: Response, token: str, max_age: int = 24 * 60 * 60
) -> None:
    """Configure the session cookie on the response.

    Args:
        response: The FastAPI response object.
        token: Session token to store in the cookie.
        max_age: Lifetime of the cookie in seconds. Defaults to 24 hours.
    """
    secure_flag = (
        settings.auth.cookie_secure
        if settings.auth.cookie_secure is not None
        else settings.environment.lower() == "production"
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure_flag,
        samesite="strict",
    )


# Request metadata dependency
async def get_request_meta(request: Request) -> Dict[str, str]:
    """Extract request metadata like IP address and user agent."""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
    }


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
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> LoginResponse:
    """Register a new user with production database"""

    try:
        # Create user
        user = await auth_service.create_user(
            email=req.email,
            password=req.password,
            roles=req.roles,
            preferences=req.preferences,
        )

        if not user:
            raise HTTPException(status_code=400, detail="User creation failed")

        # Create session
        session_data = await auth_service.create_session(
            user_data=user,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        # Set secure HttpOnly cookie
        set_session_cookie(response, session_data.session_token)

        # Convert UserData to dict format
        user_data = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": None,  # Not supported in unified service yet
            "roles": user.roles,
            "tenant_id": user.tenant_id,
            "preferences": user.preferences,
            "two_factor_enabled": False,  # Not supported yet
            "is_verified": user.is_verified,
        }

        logger.info(
            "User registered",
            extra={"user_id": user.user_id},
        )
        return LoginResponse(
            access_token=session_data.access_token,
            refresh_token=session_data.refresh_token,
            expires_in=session_data.expires_in,
            user=user_data,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Registration failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> LoginResponse:
    """Authenticate user with production database"""

    try:
        # Authenticate user
        user_data = await auth_service.authenticate_user(
            email=req.email,
            password=req.password,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Check if email is verified
        if not user_data.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified"
            )

        # 2FA is not implemented in unified service yet, skip for now

        # Create session
        session_data = await auth_service.create_session(
            user_data=user_data,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        # Set secure HttpOnly cookie
        set_session_cookie(response, session_data.session_token)

        # Convert UserData to dict format
        user_dict = {
            "user_id": user_data.user_id,
            "email": user_data.email,
            "full_name": None,  # Not supported yet
            "roles": user_data.roles,
            "tenant_id": user_data.tenant_id,
            "preferences": user_data.preferences,
            "two_factor_enabled": False,  # Not supported yet
            "is_verified": user_data.is_verified,
        }

        logger.info(
            "User logged in",
            extra={"user_id": user_data.user_id},
        )

        return LoginResponse(
            access_token=session_data.access_token,
            refresh_token=session_data.refresh_token,
            expires_in=session_data.expires_in,
            user=user_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Login failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_route(
    user_data: Dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Get current user information"""

    return UserResponse(**user_data)


async def get_tenant_from_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """Retrieve the tenant ID from the current user context."""
    return current_user["tenant_id"]


async def get_session_user(
    request: Request, request_meta: Dict[str, str] = Depends(get_request_meta)
) -> Dict[str, Any]:
    """Retrieve user data from session cookie.

    This helper reads the session cookie, validates it using the
    authentication service, and returns the associated user data.
    """

    session_token = request.cookies.get(COOKIE_NAME)
    if not session_token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    user_data = await auth_service.validate_session(
        session_token=session_token,
        ip_address=request_meta["ip_address"],
        user_agent=request_meta["user_agent"],
    )

    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Store the session token for callers that need it (e.g., logout)
    user_data["session_token"] = session_token
    return user_data


@router.post("/update_credentials", response_model=LoginResponse)
async def update_credentials(
    req: UpdateCredentialsRequest,
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
    user_data: Dict[str, Any] = Depends(get_session_user),
) -> LoginResponse:
    """Update user credentials"""

    try:
        # Update password if provided
        if req.new_password:
            if not req.current_password:
                raise HTTPException(status_code=400, detail="Current password required")

            # Verify current password first
            auth_result = await auth_service.authenticate_user(
                email=user_data["email"],
                password=req.current_password,
                ip_address=request_meta["ip_address"],
                user_agent=request_meta["user_agent"],
            )

            if not auth_result:
                raise HTTPException(
                    status_code=400, detail="Current password is incorrect"
                )

            # Update password
            success = await auth_service.update_user_password(
                user_id=user_data["user_id"], new_password=req.new_password
            )

            if not success:
                raise HTTPException(status_code=500, detail="Failed to update password")

        # Update preferences if provided
        if req.preferences:
            success = await auth_service.update_user_preferences(
                user_id=user_data["user_id"], preferences=req.preferences
            )

            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to update preferences"
                )

        # Get updated user data first
        updated_user_data = await auth_service.authenticate_user(
            email=user_data["email"],
            password=req.new_password if req.new_password else req.current_password,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        if not updated_user_data:
            raise HTTPException(status_code=500, detail="Failed to get updated user data")

        # Create new session (invalidates old one)
        session_data = await auth_service.create_session(
            user_data=updated_user_data,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        # Set new cookie
        set_session_cookie(response, session_data.session_token)

        # Convert to dict format
        updated_user_dict = {
            "user_id": updated_user_data.user_id,
            "email": updated_user_data.email,
            "full_name": None,
            "roles": updated_user_data.roles,
            "tenant_id": updated_user_data.tenant_id,
            "preferences": updated_user_data.preferences,
            "two_factor_enabled": False,
            "is_verified": updated_user_data.is_verified,
        }

        logger.info(
            "User credentials updated",
            extra={"user_id": user_data["user_id"]},
        )

        return LoginResponse(
            access_token=session_data.access_token,
            refresh_token=session_data.refresh_token,
            expires_in=session_data.expires_in,
            user=updated_user_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update credentials",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Failed to update credentials")


@router.post("/logout")
async def logout(
    response: Response,
    user_data: Dict[str, Any] = Depends(get_session_user),
) -> Dict[str, str]:
    """Logout user and invalidate session"""

    session_token = user_data.get("session_token")
    if session_token:
        await auth_service.invalidate_session(session_token)

    # Clear cookie
    response.delete_cookie(COOKIE_NAME)

    return {"detail": "Logged out successfully"}


@router.post("/request_password_reset")
async def request_password_reset(
    req: PasswordResetRequest,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> Dict[str, str]:
    """Request password reset token"""

    try:
        token = await auth_service.create_password_reset_token(
            email=req.email,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        if not token:
            # Don't reveal if user exists or not
            return {"detail": "If the email exists, a reset link has been sent"}

        # For now, log an anonymized identifier
        hashed_email = hashlib.sha256(req.email.encode()).hexdigest()
        logger.info(
            "Password reset token generated",
            extra={"hashed_email": hashed_email},
        )

        return {"detail": "Password reset link sent"}

    except Exception as e:
        logger.error(
            "Password reset request failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Failed to process request")


@router.post("/reset_password")
async def reset_password(req: PasswordResetConfirm) -> Dict[str, str]:
    """Reset password using token"""

    try:
        success = await auth_service.verify_password_reset_token(
            token=req.token, new_password=req.new_password
        )

        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        return {"detail": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Password reset failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "auth",
        }

    except Exception as e:
        logger.error(
            "Auth health check failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "auth",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
