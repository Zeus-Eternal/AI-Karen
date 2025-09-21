"""FastAPI middleware components for Kari AI."""

from ai_karen_engine.middleware.error_counter import error_counter_middleware
from ai_karen_engine.middleware.rate_limit import rate_limit_middleware
from ai_karen_engine.middleware.intelligent_error_handler import (
    IntelligentErrorHandlerMiddleware,
    add_intelligent_error_handler
)

# REMOVED: Complex auth middleware - replaced with simple auth
# REMOVED: RBAC middleware - replaced with simple role checking
# REMOVED: Session persistence middleware - replaced with simple JWT

__all__ = [
    "error_counter_middleware",
    "rate_limit_middleware",
    "IntelligentErrorHandlerMiddleware",
    "add_intelligent_error_handler",
]
