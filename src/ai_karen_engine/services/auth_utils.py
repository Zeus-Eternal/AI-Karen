from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, Response, status

from ai_karen_engine.services.auth_service import auth_service

# Shared cookie name for authentication sessions
COOKIE_NAME = "kari_session"


def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from cookies or Authorization header."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    return token


def set_session_cookie(
    response: Response, session_token: str, max_age: int = 24 * 60 * 60
) -> None:
    """Set the authentication session cookie on the response."""
    response.set_cookie(
        COOKIE_NAME,
        session_token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="strict",
    )


async def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency to retrieve the current authenticated user."""
    session_token = get_session_token(request)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    user_data = await auth_service.validate_session(
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
