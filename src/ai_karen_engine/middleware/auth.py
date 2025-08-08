"""Simple authentication middleware for FastAPI."""

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - fallback for tests
    from ai_karen_engine.fastapi_stub import Request, JSONResponse

from ai_karen_engine.auth.service import AuthService, get_auth_service
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.exceptions import (
    AuthError,
    SessionExpiredError,
    RateLimitExceededError,
)

# Global auth service instance (will be initialized lazily)
auth_service_instance: AuthService = None


async def auth_middleware(request: Request, call_next):
    """Simple bearer-token authentication middleware using AuthService."""
    global auth_service_instance
    
    # Initialize auth service if not already done
    if auth_service_instance is None:
        auth_service_instance = await get_auth_service()
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    token = auth_header.split(" ", 1)[1]
    try:
        user_data = await auth_service_instance.validate_session(
            session_token=token,
            user_agent=request.headers.get("user-agent", ""),
            ip_address=request.client.host if request.client else "",
        )
    except SessionExpiredError:
        return JSONResponse({"detail": "Session expired"}, status_code=401)
    except RateLimitExceededError:
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    except AuthError:
        return JSONResponse({"detail": "Authentication failed"}, status_code=401)
    except Exception:
        return JSONResponse({"detail": "Unauthorized"}, status_code=401)

    if not user_data:
        return JSONResponse({"detail": "Invalid session"}, status_code=401)

    if isinstance(user_data, UserData):
        request.state.user = user_data.user_id
        request.state.roles = list(user_data.roles)
    else:
        request.state.user = user_data.get("user_id")
        request.state.roles = user_data.get("roles", [])
    return await call_next(request)

