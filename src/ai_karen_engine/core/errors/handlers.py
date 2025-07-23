"""
Error handlers and response formatting for AI Karen engine.
"""

from typing import Any, Dict, Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import logging
import traceback
import uuid

from .exceptions import (
    KarenError, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ServiceError, PluginError, MemoryError, AIProcessingError,
    RateLimitError, ConfigurationError
)

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    SERVICE_ERROR = "SERVICE_ERROR"
    PLUGIN_ERROR = "PLUGIN_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    AI_PROCESSING_ERROR = "AI_PROCESSING_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: str
    trace_id: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class ErrorHandler:
    """
    Centralized error handling and response formatting.
    """
    
    def __init__(self, include_traceback: bool = False):
        self.include_traceback = include_traceback
    
    def handle_exception(
        self, 
        error: Exception, 
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> ErrorResponse:
        """
        Handle any exception and return a standardized error response.
        
        Args:
            error: The exception to handle
            request_id: Optional request ID
            trace_id: Optional trace ID
            
        Returns:
            Standardized error response
        """
        # Generate IDs if not provided
        if not request_id:
            request_id = str(uuid.uuid4())
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Log the error
        logger.error(
            f"[{trace_id}] Error handling request {request_id}: {error}",
            exc_info=True
        )
        
        # Handle known Karen errors
        if isinstance(error, KarenError):
            return self._handle_karen_error(error, request_id, trace_id)
        
        # Handle common Python exceptions
        if isinstance(error, ValueError):
            return self._handle_validation_error(error, request_id, trace_id)
        
        if isinstance(error, PermissionError):
            return self._handle_authorization_error(error, request_id, trace_id)
        
        if isinstance(error, FileNotFoundError):
            return self._handle_not_found_error(error, request_id, trace_id)
        
        # Handle unknown errors
        return self._handle_internal_error(error, request_id, trace_id)
    
    def _handle_karen_error(
        self, 
        error: KarenError, 
        request_id: str, 
        trace_id: str
    ) -> ErrorResponse:
        """Handle KarenError instances."""
        error_code_map = {
            "VALIDATION_ERROR": ErrorCode.VALIDATION_ERROR,
            "AUTHENTICATION_ERROR": ErrorCode.AUTHENTICATION_ERROR,
            "AUTHORIZATION_ERROR": ErrorCode.AUTHORIZATION_ERROR,
            "NOT_FOUND": ErrorCode.NOT_FOUND,
            "SERVICE_ERROR": ErrorCode.SERVICE_ERROR,
            "PLUGIN_ERROR": ErrorCode.PLUGIN_ERROR,
            "MEMORY_ERROR": ErrorCode.MEMORY_ERROR,
            "AI_PROCESSING_ERROR": ErrorCode.AI_PROCESSING_ERROR,
            "RATE_LIMIT_EXCEEDED": ErrorCode.RATE_LIMIT_EXCEEDED,
            "CONFIGURATION_ERROR": ErrorCode.CONFIGURATION_ERROR,
        }
        
        error_code = error_code_map.get(error.error_code, ErrorCode.INTERNAL_ERROR)
        details = error.details.copy() if error.details else {}
        
        if self.include_traceback:
            details["traceback"] = traceback.format_exc()
        
        return ErrorResponse(
            error_code=error_code,
            message=error.message,
            details=details,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            trace_id=trace_id
        )
    
    def _handle_validation_error(
        self, 
        error: ValueError, 
        request_id: str, 
        trace_id: str
    ) -> ErrorResponse:
        """Handle ValueError as validation error."""
        details = {"original_error": str(error)}
        
        if self.include_traceback:
            details["traceback"] = traceback.format_exc()
        
        return ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=str(error),
            details=details,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            trace_id=trace_id
        )
    
    def _handle_authorization_error(
        self, 
        error: PermissionError, 
        request_id: str, 
        trace_id: str
    ) -> ErrorResponse:
        """Handle PermissionError as authorization error."""
        details = {"original_error": str(error)}
        
        if self.include_traceback:
            details["traceback"] = traceback.format_exc()
        
        return ErrorResponse(
            error_code=ErrorCode.AUTHORIZATION_ERROR,
            message="Access denied",
            details=details,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            trace_id=trace_id
        )
    
    def _handle_not_found_error(
        self, 
        error: FileNotFoundError, 
        request_id: str, 
        trace_id: str
    ) -> ErrorResponse:
        """Handle FileNotFoundError as not found error."""
        details = {"original_error": str(error)}
        
        if self.include_traceback:
            details["traceback"] = traceback.format_exc()
        
        return ErrorResponse(
            error_code=ErrorCode.NOT_FOUND,
            message="Resource not found",
            details=details,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            trace_id=trace_id
        )
    
    def _handle_internal_error(
        self, 
        error: Exception, 
        request_id: str, 
        trace_id: str
    ) -> ErrorResponse:
        """Handle unknown errors as internal errors."""
        details = {
            "error_type": type(error).__name__,
            "original_error": str(error)
        }
        
        if self.include_traceback:
            details["traceback"] = traceback.format_exc()
        
        return ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An internal error occurred",
            details=details,
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            trace_id=trace_id
        )
    
    def get_http_status_code(self, error_code: ErrorCode) -> int:
        """
        Get HTTP status code for error code.
        
        Args:
            error_code: Error code
            
        Returns:
            HTTP status code
        """
        status_map = {
            ErrorCode.VALIDATION_ERROR: 400,
            ErrorCode.AUTHENTICATION_ERROR: 401,
            ErrorCode.AUTHORIZATION_ERROR: 403,
            ErrorCode.NOT_FOUND: 404,
            ErrorCode.RATE_LIMIT_EXCEEDED: 429,
            ErrorCode.INTERNAL_ERROR: 500,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            ErrorCode.SERVICE_ERROR: 500,
            ErrorCode.PLUGIN_ERROR: 500,
            ErrorCode.MEMORY_ERROR: 500,
            ErrorCode.AI_PROCESSING_ERROR: 500,
            ErrorCode.CONFIGURATION_ERROR: 500,
        }
        
        return status_map.get(error_code, 500)


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def set_error_handler(handler: ErrorHandler) -> None:
    """Set the global error handler instance."""
    global _error_handler
    _error_handler = handler