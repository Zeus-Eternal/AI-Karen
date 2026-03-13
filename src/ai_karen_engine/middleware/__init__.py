"""FastAPI middleware components for Kari AI."""

from ai_karen_engine.middleware.error_counter import error_counter_middleware
from ai_karen_engine.middleware.rate_limit import rate_limit_middleware
from ai_karen_engine.middleware.intelligent_error_handler import (
    IntelligentErrorHandlerMiddleware,
    add_intelligent_error_handler
)
from ai_karen_engine.middleware.safety_middleware import (
    SafetyMiddleware,
    SafetyMiddlewareConfig,
    SafetyAction
)
from ai_karen_engine.middleware.safety_config import SafetyMiddlewareConfig
from ai_karen_engine.middleware.content_safety_checker import ContentSafetyChecker
from ai_karen_engine.middleware.authorization_checker import AuthorizationChecker
from ai_karen_engine.middleware.safety_error_handler import SafetyErrorHandler

# REMOVED: Complex auth middleware - replaced with simple auth
# REMOVED: RBAC middleware - replaced with simple role checking
# REMOVED: Session persistence middleware - replaced with simple JWT

__all__ = [
    "error_counter_middleware",
    "rate_limit_middleware",
    "IntelligentErrorHandlerMiddleware",
    "add_intelligent_error_handler",
    "SafetyMiddleware",
    "SafetyMiddlewareConfig",
    "SafetyAction",
    "ContentSafetyChecker",
    "AuthorizationChecker",
    "SafetyErrorHandler",
]
