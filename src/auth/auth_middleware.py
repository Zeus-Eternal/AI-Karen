"""Production authentication middleware for Kari AI."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Iterable, Optional

from fastapi import HTTPException, Request, status

from .auth_service import get_auth_service, user_account_to_dict

_PUBLIC_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/health",
    "/api/auth/status",
    "/api/auth/first-run",
    "/api/auth/first-run/setup",
    "/api/auth/register",
    "/api/auth/reset-password",
    "/api/auth/validate-session",
}
_PUBLIC_PREFIXES: Iterable[str] = (
    "/static/",
    "/public/",
    "/api/public/",
)


class ProductionAuthMiddleware:
    """Authenticate requests using the production auth service."""

    def __init__(self) -> None:
        self._service = None
        self._lock = asyncio.Lock()
        self.public_paths = frozenset(_PUBLIC_PATHS)
        self.public_prefixes = tuple(_PUBLIC_PREFIXES)

    async def _get_service(self):
        if self._service is None:
            async with self._lock:
                if self._service is None:
                    self._service = await get_auth_service()
        return self._service

    @staticmethod
    def _normalise_path(path: str) -> str:
        return path.split("?")[0]

    def is_public_endpoint(self, path: str) -> bool:
        candidate = self._normalise_path(path)
        if candidate in self.public_paths:
            return True
        return any(candidate.startswith(prefix) for prefix in self.public_prefixes)

    async def authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        if request.method.upper() == "OPTIONS":
            return None

        if self.is_public_endpoint(request.url.path):
            return None

        token = self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing",
            )

        service = await self._get_service()
        user = await service.validate_token(token)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
            )

        user_data = user_account_to_dict(user)
        if not user_data.get("is_verified", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required",
            )

        return user_data

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header.split(" ", 1)[1].strip()

        session_token = request.cookies.get("kari_session")
        if session_token:
            return session_token.strip()

        return None


_middleware: Optional[ProductionAuthMiddleware] = None


def get_auth_middleware() -> ProductionAuthMiddleware:
    global _middleware
    if _middleware is None:
        _middleware = ProductionAuthMiddleware()
    return _middleware


async def get_current_user(request: Request) -> Dict[str, Any]:
    middleware = get_auth_middleware()
    user = await middleware.authenticate_request(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


async def require_auth(request: Request) -> Dict[str, Any]:
    return await get_current_user(request)


async def require_admin(request: Request) -> Dict[str, Any]:
    user = await get_current_user(request)
    if "admin" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user
