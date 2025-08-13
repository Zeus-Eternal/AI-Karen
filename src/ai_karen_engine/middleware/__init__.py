"""FastAPI middleware components for Kari AI."""

from ai_karen_engine.middleware.auth import auth_middleware
from ai_karen_engine.middleware.error_counter import error_counter_middleware
from ai_karen_engine.middleware.rate_limit import rate_limit_middleware
from ai_karen_engine.middleware.rbac import setup_rbac, require_scopes

__all__ = [
    "auth_middleware",
    "setup_rbac",
    "require_scopes",
    "error_counter_middleware",
    "rate_limit_middleware",
]
