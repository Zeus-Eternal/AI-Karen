"""
Unified error handling system for AI Karen engine.
"""

from .exceptions import (
    KarenError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ServiceError,
    PluginError,
    MemoryError,
    AIProcessingError
)
from .handlers import ErrorHandler, ErrorResponse, ErrorCode, get_error_handler
from .middleware import error_middleware

__all__ = [
    "KarenError",
    "ValidationError", 
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ServiceError",
    "PluginError",
    "MemoryError",
    "AIProcessingError",
    "ErrorHandler",
    "ErrorResponse",
    "ErrorCode",
    "get_error_handler",
    "error_middleware"
]