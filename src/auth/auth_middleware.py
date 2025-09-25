"""
Simple Authentication Middleware for AI-Karen
JWT token validation middleware with minimal complexity.
"""

import os
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth_service import get_auth_service

class SimpleAuthMiddleware:
    """Simple JWT authentication middleware"""
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.bearer_scheme = HTTPBearer(auto_error=False)
        
        # Auth mode from environment
        self.auth_mode = os.getenv("AUTH_MODE", "production").lower()
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            "/health", "/docs", "/redoc", "/openapi.json",
            "/auth/login", "/auth/register"
        }
    
    def is_public_endpoint(self, path: str) -> bool:
        """Check if endpoint is public"""
        # Exact matches
        if path in self.public_endpoints:
            return True
        
        # Prefix matches
        public_prefixes = ["/static/", "/assets/", "/_next/"]
        for prefix in public_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        # Try query parameter (for websockets, etc.)
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    async def authenticate_request(self, request: Request) -> Optional[dict]:
        """Authenticate request and return user data"""
        # Skip authentication for public endpoints
        if self.is_public_endpoint(request.url.path):
            return None
        
        # Skip authentication in development mode for specific patterns
        if self.auth_mode == "development":
            # Allow some endpoints in development
            dev_patterns = ["/api/health", "/api/debug"]
            for pattern in dev_patterns:
                if request.url.path.startswith(pattern):
                    return None
        
        # Extract token
        token = self.extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate token
        payload = self.auth_service.validate_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user data
        user = self.auth_service.get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return user context
        return {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "roles": user.roles,
            "token_payload": payload
        }

# Global middleware instance
_auth_middleware: Optional[SimpleAuthMiddleware] = None

def get_auth_middleware() -> SimpleAuthMiddleware:
    """Get auth middleware singleton"""
    global _auth_middleware
    if _auth_middleware is None:
        _auth_middleware = SimpleAuthMiddleware()
    return _auth_middleware

# FastAPI dependency for getting current user
async def get_current_user(request: Request) -> Optional[dict]:
    """FastAPI dependency to get current authenticated user"""
    middleware = get_auth_middleware()
    return await middleware.authenticate_request(request)

# FastAPI dependency for requiring authentication
async def require_auth(request: Request) -> dict:
    """FastAPI dependency that requires authentication"""
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user

# FastAPI dependency for requiring admin role
async def require_admin(request: Request) -> dict:
    """FastAPI dependency that requires admin role"""
    user = await require_auth(request)
    if "admin" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
