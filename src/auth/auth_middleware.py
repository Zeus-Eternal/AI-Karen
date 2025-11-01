"""Production authentication middleware for Kari AI."""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request, status

from .auth_service import get_auth_service

_PUBLIC_ENDPOINTS = {
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/status",
    "/api/auth/health",
    "/api/auth/first-run",
    "/api/auth/first-run/setup",
}
_PUBLIC_PREFIXES = (
    "/docs",
    "/openapi.json",
    "/health",
    "/metrics",
    "/static/",
)


class AuthMiddleware:
    """JWT authentication middleware."""

    def __init__(self) -> None:
        extra_public = os.getenv("KARI_PUBLIC_ENDPOINTS", "")
        self._public_paths = set(_PUBLIC_ENDPOINTS)
        if extra_public:
            for path in extra_public.split(","):
                cleaned = path.strip()
                if cleaned:
                    self._public_paths.add(cleaned)

    def is_public_endpoint(self, path: str) -> bool:
        if not path:
            return False
        normalized = path.rstrip("/") or "/"
        if normalized in self._public_paths:
            return True
        return normalized.startswith(_PUBLIC_PREFIXES)

    async def authenticate_request(self, request: Request) -> Dict[str, Any]:
        """Authenticate a request using the Authorization header."""
        if self.is_public_endpoint(request.url.path):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if hasattr(request.state, "user") and request.state.user:
            return request.state.user

        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
            )

        service = await get_auth_service()
        user_context = await service.verify_token(token)
        if not user_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        request.state.user = user_context
        return user_context


_auth_middleware: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Return the singleton authentication middleware."""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = AuthMiddleware()
    return _auth_middleware


async def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI dependency returning the authenticated user."""
    middleware = get_auth_middleware()
    return await middleware.authenticate_request(request)


async def require_auth(request: Request) -> Dict[str, Any]:
    """Dependency enforcing authentication."""
    return await get_current_user(request)


async def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency enforcing admin access."""
    user = await get_current_user(request)
    roles = user.get("roles", [])
    if "admin" not in roles and "super_admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
