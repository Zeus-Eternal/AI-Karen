"""
Simple Authentication Package for AI-Karen
Minimal, production-ready JWT authentication system.
"""

from .auth_service import (
    get_auth_service,
    SimpleAuthService,
    UserModel,
    LoginRequest,
    LoginResponse
)

from .auth_middleware import (
    get_auth_middleware,
    get_current_user,
    require_auth,
    require_admin,
    SimpleAuthMiddleware
)

from .auth_routes import router as auth_router

__all__ = [
    # Services
    "get_auth_service",
    "SimpleAuthService",
    
    # Models
    "UserModel",
    "LoginRequest", 
    "LoginResponse",
    
    # Middleware
    "get_auth_middleware",
    "SimpleAuthMiddleware",
    "get_current_user",
    "require_auth",
    "require_admin",
    
    # Routes
    "auth_router"
]
