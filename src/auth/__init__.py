"""
Simple Authentication Package for AI-Karen
Minimal, production-ready JWT authentication system.
"""

from .auth_service import (
    AuthService,
    get_auth_service,
    ensure_production_auth_service_ready,
    shutdown_production_auth_service,
    get_production_auth_backend,
    LoginRequest,
    LoginResponse,
)

from .auth_middleware import (
    get_auth_middleware,
    get_current_user,
    require_auth,
    require_admin,
    AuthMiddleware,
)

from .auth_routes import router as auth_router

__all__ = [
    # Services
    "AuthService",
    "get_auth_service",
    "ensure_production_auth_service_ready",
    "shutdown_production_auth_service",
    "get_production_auth_backend",

    # Models
    "LoginRequest",
    "LoginResponse",

    # Middleware
    "get_auth_middleware",
    "AuthMiddleware",
    "get_current_user",
    "require_auth",
    "require_admin",
    
    # Routes
    "auth_router"
]
