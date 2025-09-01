"""
Enhanced Authentication Routes with Session Persistence

This module provides enhanced authentication routes that implement secure
session persistence across page refreshes using JWT tokens with HttpOnly cookies.
Extends the existing auth.py with refresh token functionality and enhanced security.
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.core.dependencies import (
    get_current_tenant_id,
    get_current_user_context,
)
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.auth.service import AuthService, get_auth_service
from ai_karen_engine.auth.tokens import EnhancedTokenManager
from ai_karen_engine.auth.cookie_manager import SessionCookieManager, get_cookie_manager
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.core.cache import get_request_deduplicator
from ai_karen_engine.auth.exceptions import (
    AuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    AccountLockedError,
    SessionExpiredError,
    SessionNotFoundError,
    RateLimitExceededError,
    SecurityError,
    AnomalyDetectedError,
    SuspiciousActivityError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ai_karen_engine.auth.security_monitor import EnhancedSecurityMonitor
from ai_karen_engine.auth.csrf_protection import CSRFProtectionMiddleware, validate_csrf_token
from ai_karen_engine.services.audit_logging import get_audit_logger

logger = get_logger(__name__)
audit_logger = get_audit_logger()
router = APIRouter(tags=["auth-session"], prefix="/auth")

# Global instances (will be initialized lazily)
auth_service_instance: Optional[AuthService] = None
token_manager_instance: Optional[EnhancedTokenManager] = None
cookie_manager_instance: Optional[SessionCookieManager] = None
security_monitor_instance: Optional[EnhancedSecurityMonitor] = None
csrf_protection_instance: Optional[CSRFProtectionMiddleware] = None
refresh_deduplicator = get_request_deduplicator()


async def get_auth_service_instance() -> AuthService:
    """Get the auth service instance, initializing it if necessary."""
    global auth_service_instance
    if auth_service_instance is None:
        auth_service_instance = await get_auth_service()
    return auth_service_instance


async def get_token_manager() -> EnhancedTokenManager:
    """Get the token manager instance, initializing it if necessary."""
    global token_manager_instance
    if token_manager_instance is None:
        auth_config = AuthConfig.from_env()
        token_manager_instance = EnhancedTokenManager(auth_config.jwt)
    return token_manager_instance


def get_cookie_manager_instance() -> SessionCookieManager:
    """Get the cookie manager instance, initializing it if necessary."""
    global cookie_manager_instance
    if cookie_manager_instance is None:
        cookie_manager_instance = get_cookie_manager()
    return cookie_manager_instance


async def get_security_monitor() -> EnhancedSecurityMonitor:
    """Get the security monitor instance, initializing it if necessary."""
    global security_monitor_instance
    if security_monitor_instance is None:
        auth_config = AuthConfig.from_env()
        security_monitor_instance = EnhancedSecurityMonitor(auth_config)
    return security_monitor_instance


def get_csrf_protection() -> CSRFProtectionMiddleware:
    """Get the CSRF protection instance, initializing it if necessary."""
    global csrf_protection_instance
    if csrf_protection_instance is None:
        auth_config = AuthConfig.from_env()
        csrf_protection_instance = CSRFProtectionMiddleware(auth_config)
    return csrf_protection_instance


# Request metadata dependency
async def get_request_meta(request: Request) -> Dict[str, str]:
    """Extract request metadata like IP address and user agent."""
    xff = request.headers.get("x-forwarded-for")
    ip = (
        xff.split(",")[0].strip()
        if xff
        else (request.client.host if request.client else "unknown")
    )
    return {
        "ip_address": ip,
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
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LongLivedTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    token_type_description: str = "long_lived"


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


# Enhanced Authentication Routes


@router.post("/register", response_model=LoginResponse)
async def register(
    req: RegisterRequest,
    response: Response,
    request: Request,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> LoginResponse:
    """Register a new user with enhanced session persistence and security monitoring"""

    try:
        # Security monitoring - check for suspicious activity before registration
        security_monitor = await get_security_monitor()
        await security_monitor.check_authentication_security(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            email=req.email,
            endpoint="register",
        )
        
        # CSRF protection for state-changing operation
        csrf_protection = get_csrf_protection()
        await csrf_protection.validate_csrf_protection(request)
        # Create user
        auth_service = await get_auth_service_instance()
        user = await auth_service.create_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            roles=req.roles,
            preferences=req.preferences,
            tenant_id=req.tenant_id,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        if not user:
            raise HTTPException(status_code=400, detail="User creation failed")

        # Create tokens using enhanced token manager
        token_manager = await get_token_manager()
        access_token = await token_manager.create_access_token(user)
        refresh_token = await token_manager.create_refresh_token(user)

        # Create session for backward compatibility
        session_data = await auth_service.create_session(
            user_data=user,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        # Set secure HttpOnly cookies
        cookie_manager = get_cookie_manager_instance()
        cookie_manager.set_refresh_token_cookie(
            response, 
            refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        cookie_manager.set_session_cookie(response, session_data.session_token)
        
        # Generate CSRF token for future requests
        csrf_protection = get_csrf_protection()
        csrf_token = csrf_protection.generate_csrf_response(
            response, 
            user_id=user.user_id,
            secure=request.url.scheme == "https"
        )

        # Convert UserData to dict format
        user_data = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "tenant_id": user.tenant_id,
            "preferences": user.preferences,
            "two_factor_enabled": False,  # Not supported yet
            "is_verified": user.is_verified,
        }

        # Record successful registration for security monitoring
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=True,
            email=req.email,
        )

        # Audit log successful registration
        audit_logger.log_login_success(
            user_id=user.user_id,
            email=req.email,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            tenant_id=user.tenant_id,
            session_id=session_data.session_token,
            login_count=1,  # First login for new user
            registration=True
        )

        logger.info(
            "User registered with session persistence",
            extra={"user_id": user.user_id},
        )
        
        return LoginResponse(
            access_token=access_token,
            expires_in=15 * 60,  # 15 minutes
            user=user_data,
        )

    except UserAlreadyExistsError as e:
        # Record failed registration attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="user_already_exists",
        )
        
        # Audit log failed registration
        audit_logger.log_login_failure(
            email=req.email,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            failure_reason="user_already_exists"
        )
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        # Record failed registration attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="validation_error",
        )
        raise HTTPException(status_code=400, detail=str(e))
    except RateLimitExceededError as e:
        retry_after = e.details.get("retry_after") if isinstance(e.details, dict) else None
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers=headers,
        )
    except (SecurityError, AnomalyDetectedError, SuspiciousActivityError) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except AuthError as e:
        # Record failed registration attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="auth_error",
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Record failed registration attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="internal_error",
        )
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
    request: Request,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> LoginResponse:
    """Authenticate user with enhanced session persistence and security monitoring"""

    try:
        # Security monitoring - check for suspicious activity before login
        security_monitor = await get_security_monitor()
        await security_monitor.check_authentication_security(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            email=req.email,
            endpoint="login",
        )
        
        # CSRF protection for state-changing operation
        csrf_protection = get_csrf_protection()
        await csrf_protection.validate_csrf_protection(request)
        # Authenticate user
        auth_service = await get_auth_service_instance()
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

        # Create tokens using enhanced token manager
        token_manager = await get_token_manager()
        access_token = await token_manager.create_access_token(user_data)
        refresh_token = await token_manager.create_refresh_token(user_data)

        # Create session for backward compatibility
        session_data = await auth_service.create_session(
            user_data=user_data,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
        )

        # Set secure HttpOnly cookies
        cookie_manager = get_cookie_manager_instance()
        cookie_manager.set_refresh_token_cookie(
            response, 
            refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        cookie_manager.set_session_cookie(response, session_data.session_token)
        
        # Generate CSRF token for future requests
        csrf_protection = get_csrf_protection()
        csrf_token = csrf_protection.generate_csrf_response(
            response, 
            user_id=user_data.user_id,
            secure=request.url.scheme == "https"
        )

        # Convert UserData to dict format
        user_dict = {
            "user_id": user_data.user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "roles": user_data.roles,
            "tenant_id": user_data.tenant_id,
            "preferences": user_data.preferences,
            "two_factor_enabled": False,  # Not supported yet
            "is_verified": user_data.is_verified,
        }

        # Record successful login for security monitoring
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=True,
            email=req.email,
        )

        # Audit log successful login
        audit_logger.log_login_success(
            user_id=user_data.user_id,
            email=req.email,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            tenant_id=user_data.tenant_id,
            session_id=session_data.session_token
        )

        logger.info(
            "User logged in with session persistence",
            extra={"user_id": user_data.user_id},
        )

        return LoginResponse(
            access_token=access_token,
            expires_in=15 * 60,  # 15 minutes
            user=user_dict,
        )

    except InvalidCredentialsError:
        # Record failed login attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="invalid_credentials",
        )
        
        # Audit log failed login
        audit_logger.log_login_failure(
            email=req.email,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            failure_reason="invalid_credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    except AccountLockedError as e:
        # Record failed login attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="account_locked",
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, detail=str(e)
        )
    except RateLimitExceededError as e:
        retry_after = e.details.get("retry_after") if isinstance(e.details, dict) else None
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers=headers,
        )
    except (SecurityError, AnomalyDetectedError, SuspiciousActivityError) as e:
        raise HTTPException(status_code=403, detail="Authentication blocked")
    except HTTPException:
        raise
    except Exception as e:
        # Record failed login attempt
        security_monitor = await get_security_monitor()
        await security_monitor.record_authentication_result(
            ip_address=request_meta["ip_address"],
            user_agent=request_meta["user_agent"],
            success=False,
            email=req.email,
            failure_reason="internal_error",
        )
        logger.error(
            "Login failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/create-long-lived-token", response_model=LongLivedTokenResponse)
async def create_long_lived_token(
    request: Request,
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
    user_data: Dict[str, Any] = Depends(get_current_user_context),
) -> LongLivedTokenResponse:
    """Create a long-lived access token (24 hours) for API stability after successful authentication"""

    try:
        # CSRF protection for state-changing operation
        csrf_protection = get_csrf_protection()
        await csrf_protection.validate_csrf_protection(request)
        
        # Get token manager
        token_manager = await get_token_manager()
        
        # Reconstruct UserData from the current user data
        from ai_karen_engine.auth.models import UserData
        user_data_obj = UserData(
            user_id=user_data["user_id"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            tenant_id=user_data["tenant_id"],
            roles=user_data["roles"],
            is_verified=user_data["is_verified"],
            is_active=True,
            preferences=user_data.get("preferences", {})
        )

        # Create long-lived access token (24 hours)
        long_lived_token = await token_manager.create_access_token(
            user_data_obj, 
            long_lived=True
        )

        # Audit log long-lived token creation
        from ai_karen_engine.services.audit_logging import AuditEvent
        audit_event = AuditEvent(
            event_type="token_creation",
            user_id=user_data["user_id"],
            tenant_id=user_data["tenant_id"],
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            resource_type="long_lived_access_token",
            action="create",
            outcome="success",
            details={
                "token_type": "long_lived_access",
                "expires_in_seconds": 24 * 60 * 60,
                "expires_in_hours": 24
            },
            timestamp=datetime.now(timezone.utc)
        )
        audit_logger.log_audit_event(audit_event)

        logger.info(
            "Long-lived token created successfully",
            extra={
                "user_id": user_data["user_id"],
                "ip_address": request_meta["ip_address"],
                "expires_in_hours": 24
            },
        )

        return LongLivedTokenResponse(
            access_token=long_lived_token,
            expires_in=24 * 60 * 60,  # 24 hours in seconds
            token_type_description="long_lived"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Long-lived token creation failed",
            error=str(e),
            user_id=user_data.get("user_id"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Failed to create long-lived token")


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> RefreshTokenResponse:
    """Refresh access token using refresh token from HttpOnly cookie with deduplication"""

    # Get refresh token from cookie first to use for deduplication key
    cookie_manager = get_cookie_manager_instance()
    refresh_token = cookie_manager.get_refresh_token(request)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token not found"
        )

    # Deduplicate simultaneous refresh requests for the same token
    return await refresh_deduplicator.deduplicate(
        _perform_token_refresh, 
        refresh_token, 
        response, 
        request_meta
    )


async def _perform_token_refresh(
    refresh_token: str,
    response: Response,
    request_meta: Dict[str, str]
) -> RefreshTokenResponse:
    """Internal method to perform token refresh (used by deduplicator)"""
    
    try:
        # Get token manager and auth service
        token_manager = await get_token_manager()
        auth_service = await get_auth_service_instance()
        cookie_manager = get_cookie_manager_instance()

        # Validate refresh token
        try:
            payload = await token_manager.validate_refresh_token(refresh_token)
        except TokenExpiredError:
            # Clear expired refresh token cookie
            cookie_manager.clear_refresh_token_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except InvalidTokenError:
            # Clear invalid refresh token cookie
            cookie_manager.clear_refresh_token_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user data from payload
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )

        # Get current user data from auth service
        # Note: In a real implementation, you'd fetch from database
        # For now, reconstruct from token payload
        from ai_karen_engine.auth.models import UserData
        user_data = UserData(
            user_id=user_id,
            email=payload.get("email", ""),
            full_name=None,  # Not in refresh token
            tenant_id=payload.get("tenant_id", "default"),
            roles=[],  # Not in refresh token
            is_verified=True,  # Assume verified if they have a refresh token
            is_active=True,
            preferences={}
        )

        # Rotate tokens for enhanced security
        new_access_token, new_refresh_token, refresh_expires_at = await token_manager.rotate_tokens(
            refresh_token, user_data
        )

        # Update refresh token cookie with new token
        cookie_manager.set_refresh_token_cookie(
            response, 
            new_refresh_token,
            expires_at=refresh_expires_at
        )

        # Audit log token refresh success
        audit_logger.log_token_refresh_success(
            user_id=user_id,
            ip_address=request_meta["ip_address"],
            user_agent=request_meta.get("user_agent"),
            tenant_id=payload.get("tenant_id", "default"),
            correlation_id=request_meta.get("correlation_id")
        )

        logger.info(
            "Tokens rotated successfully",
            extra={
                "user_id": user_id,
                "ip_address": request_meta["ip_address"]
            },
        )

        return RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=15 * 60,  # 15 minutes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Token refresh failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> Dict[str, str]:
    """Logout user and invalidate all tokens and cookies with CSRF protection"""

    try:
        # CSRF protection for state-changing operation
        csrf_protection = get_csrf_protection()
        await csrf_protection.validate_csrf_protection(request)
        cookie_manager = get_cookie_manager_instance()
        
        # Get tokens from cookies
        refresh_token = cookie_manager.get_refresh_token(request)
        session_token = cookie_manager.get_session_token(request)

        # Revoke refresh token if present
        if refresh_token:
            try:
                token_manager = await get_token_manager()
                await token_manager.revoke_token(refresh_token)
            except Exception as e:
                logger.warning(f"Failed to revoke refresh token: {e}")

        # Invalidate session if present
        if session_token:
            try:
                auth_service = await get_auth_service_instance()
                await auth_service.invalidate_session(session_token, reason="logout")
            except Exception as e:
                logger.warning(f"Failed to invalidate session: {e}")

        # Clear all authentication cookies
        cookie_manager.clear_all_auth_cookies(response)
        
        # Clear CSRF protection
        csrf_protection.clear_csrf_protection(response)

        # Audit log successful logout
        # Try to extract user_id from token if available
        user_id = None
        if refresh_token:
            try:
                token_manager = await get_token_manager()
                payload = await token_manager.validate_refresh_token(refresh_token)
                user_id = payload.get("sub")
            except Exception:
                pass  # Token might be expired/invalid, that's ok for logout
        
        if user_id:
            audit_logger.log_logout_success(
                user_id=user_id,
                ip_address=request_meta["ip_address"],
                user_agent=request_meta.get("user_agent")
            )

        logger.info(
            "User logged out successfully",
            extra={
                "ip_address": request_meta["ip_address"],
                "has_refresh_token": refresh_token is not None,
                "has_session_token": session_token is not None,
            },
        )

        return {"detail": "Logged out successfully"}

    except Exception as e:
        logger.error(
            "Logout failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        # Still clear cookies even if logout fails
        cookie_manager = get_cookie_manager_instance()
        cookie_manager.clear_all_auth_cookies(response)
        
        # Clear CSRF protection
        csrf_protection = get_csrf_protection()
        csrf_protection.clear_csrf_protection(response)
        
        return {"detail": "Logged out successfully"}


# Using get_current_user_context from core dependencies instead of custom implementation


@router.get("/me", response_model=UserResponse)
async def get_current_user_route(
    user_data: Dict[str, Any] = Depends(get_current_user_context),
) -> UserResponse:
    """Get current user information from access token"""
    return UserResponse(**user_data)


# Enhanced session validation middleware for protected routes
async def validate_session_middleware(
    request: Request,
    request_meta: Dict[str, str] = Depends(get_request_meta)
) -> Dict[str, Any]:
    """
    Enhanced session validation middleware with improved error handling.
    
    Uses the enhanced session validator to provide better error messages
    and prevent duplicate validation attempts.
    """
    from ai_karen_engine.auth.enhanced_session_validator import get_session_validator
    
    session_validator = get_session_validator()
    return await session_validator.validate_request_authentication(
        request, 
        allow_session_fallback=True
    )


# Optional authentication dependency for routes that don't require auth
async def get_current_user_optional(
    request: Request,
    request_meta: Dict[str, str] = Depends(get_request_meta)
) -> Optional[Dict[str, Any]]:
    """
    Get current user optionally (returns None if not authenticated).
    
    This dependency is useful for routes that can work with or without authentication.
    """
    from ai_karen_engine.auth.enhanced_session_validator import get_session_validator
    
    session_validator = get_session_validator()
    return await session_validator.validate_optional_authentication(request)


# CSRF Token endpoint
@router.get("/csrf-token")
async def get_csrf_token(
    response: Response,
    request: Request,
    user_data: Dict[str, Any] = Depends(get_current_user_context),
) -> Dict[str, str]:
    """Get CSRF token for authenticated user"""
    
    csrf_protection = get_csrf_protection()
    csrf_token = csrf_protection.generate_csrf_response(
        response,
        user_id=user_data["user_id"],
        secure=request.url.scheme == "https"
    )
    
    return {
        "csrf_token": csrf_token,
        "expires_in": 3600,  # 1 hour
    }


# Security statistics endpoint
@router.get("/security-stats")
async def get_security_stats(
    user_data: Dict[str, Any] = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """Get security statistics (admin only)"""
    
    # Check if user has admin role
    if "admin" not in user_data.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    security_monitor = await get_security_monitor()
    stats = security_monitor.get_security_stats()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "security_stats": stats,
    }


# Session validation endpoint
@router.get("/validate-session")
async def validate_session(
    request: Request,
    request_meta: Dict[str, str] = Depends(get_request_meta),
) -> Dict[str, Any]:
    """Validate current session and return user data if valid"""
    try:
        # Use enhanced session validator for consistent validation
        from ai_karen_engine.auth.enhanced_session_validator import get_session_validator
        
        session_validator = get_session_validator()
        user_data = await session_validator.validate_request_authentication(
            request, 
            allow_session_fallback=True
        )
        
        return {
            "valid": True,
            "user": user_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail,
            "status_code": e.status_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return {
            "valid": False,
            "error": "Session validation failed",
            "status_code": 500,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Health check
@router.get("/health")
async def auth_session_health_check():
    """Health check for enhanced authentication system"""

    try:
        # Test token manager
        token_manager = await get_token_manager()
        
        # Test cookie manager
        cookie_manager = get_cookie_manager_instance()
        cookie_security = cookie_manager.validate_cookie_security()
        
        # Test security monitor
        security_monitor = await get_security_monitor()
        security_stats = security_monitor.get_security_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "auth-session",
            "features": {
                "token_rotation": True,
                "secure_cookies": True,
                "session_persistence": True,
                "security_monitoring": True,
                "csrf_protection": True,
                "rate_limiting": security_stats["rate_limiting"]["enabled"],
                "anomaly_detection": security_stats["anomaly_detection"]["enabled"],
            },
            "cookie_security": cookie_security,
            "security_summary": {
                "total_alerts_24h": security_stats["alerts"]["total_alerts"],
                "monitored_users": security_stats["anomaly_detection"]["monitored_users"],
                "monitored_ips": security_stats["anomaly_detection"]["monitored_ips"],
            },
        }

    except Exception as e:
        logger.error(
            "Auth session health check failed",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "auth-session",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }