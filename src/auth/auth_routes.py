"""Production authentication routes proxy."""

from src.ai_karen_engine.api_routes.production_auth_routes import (
    router as production_auth_router,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    FirstRunSetupRequest,
    CreateUserRequest,
    UserResponse,
)

router = production_auth_router

__all__ = [
    "router",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "FirstRunSetupRequest",
    "CreateUserRequest",
    "UserResponse",
]
