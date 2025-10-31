"""
Minimal Authentication Middleware for AI-Karen
No authentication required - open access system.
"""

import os
from typing import Optional
from fastapi import Request

class NoAuthMiddleware:
    """No authentication middleware - allows all requests"""
    
    def __init__(self):
        # Always allow access
        pass
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public (all endpoints are public in no-auth mode)"""
        # In no-auth mode, all endpoints are considered public
        return True
    
    async def authenticate_request(self, request: Request) -> Optional[dict]:
        """Return default user context for all requests"""
        # Return a simple default user for all requests
        return {
            "user_id": "default_user",
            "email": "user@example.com",
            "full_name": "Default User",
            "roles": ["user", "admin"],
            "tenant_id": "default",
            "is_active": True,
        }

# Global middleware instance
_auth_middleware: Optional[NoAuthMiddleware] = None

def get_auth_middleware() -> NoAuthMiddleware:
    """Get auth middleware singleton"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = NoAuthMiddleware()
    return _auth_middleware

# FastAPI dependency for getting current user
async def get_current_user(request: Request) -> dict:
    """FastAPI dependency to get current user (always returns default user)"""
    middleware = get_auth_middleware()
    return await middleware.authenticate_request(request)

# FastAPI dependency for requiring authentication (no-op)
async def require_auth(request: Request) -> dict:
    """FastAPI dependency that returns default user (no auth required)"""
    return await get_current_user(request)

# FastAPI dependency for requiring admin role (no-op)
async def require_admin(request: Request) -> dict:
    """FastAPI dependency that returns default user (no auth required)"""
    return await get_current_user(request)
