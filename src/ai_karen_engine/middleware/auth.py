"""Simple authentication middleware for FastAPI."""

# mypy: ignore-errors

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - fallback for tests
    from ai_karen_engine.fastapi_stub import Request, JSONResponse

import hashlib
from datetime import datetime

from ai_karen_engine.auth.exceptions import (
    AuthError,
    RateLimitExceededError,
    SessionExpiredError,
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.service import AuthService, get_auth_service
from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models.auth_models import ApiKey, Role, RolePermission

# Global auth service instance (will be initialized lazily)
auth_service_instance: AuthService = None


async def auth_middleware(request: Request, call_next):
    """Authenticate requests via bearer tokens or API keys with RBAC checks."""
    global auth_service_instance

    required_header = request.headers.get("X-Required-Scopes")
    required_scopes = (
        {s.strip() for s in required_header.split(",") if s.strip()}
        if required_header
        else set()
    )

    api_key = request.headers.get("X-API-Key")
    if api_key:
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        with get_db_session_context() as session:
            record = session.query(ApiKey).filter_by(hashed_key=hashed).first()
            if not record or (
                record.expires_at and record.expires_at < datetime.utcnow()
            ):
                return JSONResponse({"detail": "Invalid API key"}, status_code=401)
            allowed_scopes = set(record.scopes or [])
        if required_scopes and not required_scopes.issubset(allowed_scopes):
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        request.state.user = record.user_id
        request.state.roles = []
        request.state.scopes = list(allowed_scopes)
        return await call_next(request)

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
        roles = list(user_data.roles)
    else:
        request.state.user = user_data.get("user_id")
        roles = user_data.get("roles", [])
    request.state.roles = roles

    allowed_scopes = set()
    if required_scopes:
        with get_db_session_context() as session:
            perms = (
                session.query(RolePermission.permission)
                .join(Role, Role.role_id == RolePermission.role_id)
                .filter(Role.name.in_(roles))
                .all()
            )
            allowed_scopes = {p[0] for p in perms}
        if not required_scopes.issubset(allowed_scopes):
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
    request.state.scopes = list(allowed_scopes)
    return await call_next(request)
