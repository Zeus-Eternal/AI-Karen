from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Response, status

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.auth.service import get_auth_service
from ai_karen_engine.auth.cookie_manager import get_cookie_manager

# Legacy cookie name for backward compatibility
COOKIE_NAME = "kari_session"


def get_session_token(request: Request) -> Optional[str]:
    """
    Extract session token from cookies or Authorization header.
    
    This function now uses the new cookie manager for enhanced security
    while maintaining backward compatibility.
    """
    cookie_manager = get_cookie_manager()
    
    # Try new session cookie first
    token = cookie_manager.get_session_token(request)
    
    # Fallback to legacy cookie name for backward compatibility
    if not token:
        token = request.cookies.get(COOKIE_NAME)
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    
    return token


def get_refresh_token(request: Request) -> Optional[str]:
    """Extract refresh token from secure HttpOnly cookies."""
    cookie_manager = get_cookie_manager()
    return cookie_manager.get_refresh_token(request)


def set_session_cookie(
    response: Response, session_token: str, max_age: int = 24 * 60 * 60
) -> None:
    """
    Set the authentication session cookie on the response.
    
    This function now uses the enhanced cookie manager with proper
    security flags and environment-based configuration.
    """
    cookie_manager = get_cookie_manager()
    
    # Calculate expiry datetime
    expires_at = datetime.utcnow() + timedelta(seconds=max_age)
    
    # Use new secure cookie manager
    cookie_manager.set_session_cookie(response, session_token, expires_at)
    
    # Also set legacy cookie for backward compatibility during transition
    secure_flag = (
        settings.auth.cookie_secure
        if settings.auth.cookie_secure is not None
        else settings.environment.lower() == "production"
    )
    response.set_cookie(
        COOKIE_NAME,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=secure_flag,
        samesite="strict",
    )


def set_refresh_token_cookie(
    response: Response, refresh_token: str, expires_at: Optional[datetime] = None
) -> None:
    """
    Set secure refresh token cookie with proper security flags.
    
    Args:
        response: FastAPI response object
        refresh_token: JWT refresh token to store
        expires_at: Optional expiry datetime
    """
    cookie_manager = get_cookie_manager()
    cookie_manager.set_refresh_token_cookie(response, refresh_token, expires_at)


def clear_auth_cookies(response: Response) -> None:
    """
    Clear all authentication cookies for logout.
    
    Args:
        response: FastAPI response object
    """
    cookie_manager = get_cookie_manager()
    cookie_manager.clear_all_auth_cookies(response)
    
    # Also clear legacy cookie
    response.set_cookie(
        COOKIE_NAME,
        "",
        max_age=0,
        httponly=True,
        secure=True,
        samesite="strict",
    )


def validate_cookie_security() -> Dict[str, Any]:
    """
    Validate current cookie security configuration.
    
    Returns:
        Dictionary with validation results and recommendations
    """
    cookie_manager = get_cookie_manager()
    return cookie_manager.validate_cookie_security()


async def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to retrieve the current authenticated user."""
    session_token = get_session_token(request)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    service = await get_auth_service()
    user_data = await service.validate_session(
        session_token=session_token,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return user_data
