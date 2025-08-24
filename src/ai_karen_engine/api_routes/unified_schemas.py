"""
Unified API Schemas and Error Handling - Phase 4.1.a
Provides strict contract validation and standardized error responses across all endpoints.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from fastapi import HTTPException, Request, status
    from fastapi.exceptions import RequestValidationError

    FASTAPI_AVAILABLE = True
except ImportError:
    # Graceful fallback for environments without FastAPI
    HTTPException = None
    Request = None
    status = None
    RequestValidationError = None
    FASTAPI_AVAILABLE = False

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# Error classification
class ErrorType(str, Enum):
    """Standardized error types"""

    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    CONFLICT_ERROR = "conflict_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVICE_ERROR = "service_error"
    INTERNAL_ERROR = "internal_error"


# Field-level validation error
class FieldError(BaseModel):
    """Individual field validation error"""

    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")
    invalid_value: Optional[Any] = Field(
        None, description="The invalid value that was provided"
    )


# Unified error response schema
class ErrorResponse(BaseModel):
    """Standardized error envelope for all API responses"""

    error: ErrorType = Field(..., description="Error type classification")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error context"
    )
    field_errors: Optional[List[FieldError]] = Field(
        None, description="Field-level validation errors"
    )
    correlation_id: str = Field(..., description="Request correlation ID for tracing")
    timestamp: datetime = Field(..., description="Error timestamp")
    path: str = Field(..., description="API path where error occurred")
    status_code: int = Field(..., description="HTTP status code")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# Success response wrapper
class SuccessResponse(BaseModel):
    """Standardized success envelope for consistent responses"""

    success: bool = Field(True, description="Operation success indicator")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Success message")
    correlation_id: str = Field(..., description="Request correlation ID for tracing")
    timestamp: datetime = Field(..., description="Response timestamp")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# Validation utilities
class ValidationUtils:
    """Utilities for request/response validation"""

    @staticmethod
    def validate_user_id(user_id: str) -> str:
        """Validate user ID format"""
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty")

        if len(user_id) > 255:
            raise ValueError("User ID cannot exceed 255 characters")

        # Basic format validation - alphanumeric, hyphens, underscores
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", user_id):
            raise ValueError("User ID contains invalid characters")

        return user_id.strip()

    @staticmethod
    def validate_org_id(org_id: Optional[str]) -> Optional[str]:
        """Validate organization ID format"""
        if org_id is None:
            return None

        if not org_id.strip():
            return None

        if len(org_id) > 255:
            raise ValueError("Organization ID cannot exceed 255 characters")

        # Basic format validation
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", org_id):
            raise ValueError("Organization ID contains invalid characters")

        return org_id.strip()

    @staticmethod
    def validate_text_content(
        text: str, min_length: int = 1, max_length: int = 16000
    ) -> str:
        """Validate text content"""
        if not text or not text.strip():
            raise ValueError("Text content cannot be empty")

        text = text.strip()

        if len(text) < min_length:
            raise ValueError(f"Text content must be at least {min_length} characters")

        if len(text) > max_length:
            raise ValueError(f"Text content cannot exceed {max_length} characters")

        return text

    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """Validate and normalize tags"""
        if not tags:
            return []

        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError("All tags must be strings")

            tag = tag.strip().lower()
            if not tag:
                continue

            if len(tag) > 50:
                raise ValueError("Individual tags cannot exceed 50 characters")

            # Basic format validation for tags
            import re

            if not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                raise ValueError(f"Tag '{tag}' contains invalid characters")

            if tag not in validated_tags:  # Remove duplicates
                validated_tags.append(tag)

        if len(validated_tags) > 20:
            raise ValueError("Cannot have more than 20 tags")

        return validated_tags

    @staticmethod
    def validate_importance(importance: int) -> int:
        """Validate importance score"""
        if not isinstance(importance, int):
            raise ValueError("Importance must be an integer")

        if importance < 1 or importance > 10:
            raise ValueError("Importance must be between 1 and 10")

        return importance

    @staticmethod
    def validate_decay_tier(decay: str) -> str:
        """Validate decay tier"""
        valid_tiers = ["short", "medium", "long", "pinned"]
        if decay not in valid_tiers:
            raise ValueError(f"Decay tier must be one of: {', '.join(valid_tiers)}")

        return decay

    @staticmethod
    def validate_top_k(top_k: int, max_value: int = 50) -> int:
        """Validate top_k parameter"""
        if not isinstance(top_k, int):
            raise ValueError("top_k must be an integer")

        if top_k < 1:
            raise ValueError("top_k must be at least 1")

        if top_k > max_value:
            raise ValueError(f"top_k cannot exceed {max_value}")

        return top_k


# Error handling utilities
class ErrorHandler:
    """Centralized error handling for API routes"""

    @staticmethod
    def create_error_response(
        error_type: ErrorType,
        message: str,
        correlation_id: str,
        path: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[FieldError]] = None,
    ) -> ErrorResponse:
        """Create standardized error response"""
        return ErrorResponse(
            error=error_type,
            message=message,
            details=details,
            field_errors=field_errors,
            correlation_id=correlation_id,
            timestamp=datetime.now().isoformat(),
            path=path,
            status_code=status_code,
        )

    @staticmethod
    def create_validation_error_response(
        validation_errors: List[Dict[str, Any]], correlation_id: str, path: str
    ) -> ErrorResponse:
        """Create validation error response from Pydantic errors"""
        field_errors = []

        for error in validation_errors:
            field_path = ".".join(str(loc) for loc in error.get("loc", []))
            field_errors.append(
                FieldError(
                    field=field_path,
                    message=error.get("msg", "Validation failed"),
                    code=error.get("type", "validation_error"),
                    invalid_value=error.get("input"),
                )
            )

        if not FASTAPI_AVAILABLE:
            status_code = 422
        else:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

        return ErrorHandler.create_error_response(
            error_type=ErrorType.VALIDATION_ERROR,
            message="Request validation failed",
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
            field_errors=field_errors,
        )

    @staticmethod
    def create_authentication_error_response(
        correlation_id: str, path: str, message: str = "Authentication required"
    ) -> ErrorResponse:
        """Create authentication error response"""
        status_code = 401 if not FASTAPI_AVAILABLE else status.HTTP_401_UNAUTHORIZED

        return ErrorHandler.create_error_response(
            error_type=ErrorType.AUTHENTICATION_ERROR,
            message=message,
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
        )

    @staticmethod
    def create_authorization_error_response(
        correlation_id: str, path: str, message: str = "Insufficient permissions"
    ) -> ErrorResponse:
        """Create authorization error response"""
        status_code = 403 if not FASTAPI_AVAILABLE else status.HTTP_403_FORBIDDEN

        return ErrorHandler.create_error_response(
            error_type=ErrorType.AUTHORIZATION_ERROR,
            message=message,
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
        )

    @staticmethod
    def create_not_found_error_response(
        correlation_id: str, path: str, resource: str = "Resource"
    ) -> ErrorResponse:
        """Create not found error response"""
        status_code = 404 if not FASTAPI_AVAILABLE else status.HTTP_404_NOT_FOUND

        return ErrorHandler.create_error_response(
            error_type=ErrorType.NOT_FOUND_ERROR,
            message=f"{resource} not found",
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
        )

    @staticmethod
    def create_service_error_response(
        correlation_id: str, path: str, service_name: str, error: Exception
    ) -> ErrorResponse:
        """Create service error response"""
        status_code = (
            503 if not FASTAPI_AVAILABLE else status.HTTP_503_SERVICE_UNAVAILABLE
        )

        return ErrorHandler.create_error_response(
            error_type=ErrorType.SERVICE_ERROR,
            message=f"{service_name} service error",
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
            details={"service": service_name, "error": str(error)},
        )

    @staticmethod
    def create_internal_error_response(
        correlation_id: str, path: str, error: Exception
    ) -> ErrorResponse:
        """Create internal server error response"""
        status_code = (
            500 if not FASTAPI_AVAILABLE else status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        return ErrorHandler.create_error_response(
            error_type=ErrorType.INTERNAL_ERROR,
            message="Internal server error",
            correlation_id=correlation_id,
            path=path,
            status_code=status_code,
            details={"error": str(error)},
        )


# Exception handlers for FastAPI (only available if FastAPI is installed)
if FASTAPI_AVAILABLE:

    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors"""
        correlation_id = request.headers.get("X-Correlation-Id", "unknown")

        error_response = ErrorHandler.create_validation_error_response(
            validation_errors=exc.errors(),
            correlation_id=correlation_id,
            path=str(request.url.path),
        )

        logger.warning(
            f"Validation error on {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "errors": exc.errors(),
                "status_code": 422,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response.model_dump(mode="json"),
        )

    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with standardized format"""
        correlation_id = request.headers.get("X-Correlation-Id", "unknown")

        # If the exception detail is already a dict (from our error responses), use it
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            raise exc

        # Otherwise, wrap in our standard format
        error_type = ErrorType.INTERNAL_ERROR
        if exc.status_code == 401:
            error_type = ErrorType.AUTHENTICATION_ERROR
        elif exc.status_code == 403:
            error_type = ErrorType.AUTHORIZATION_ERROR
        elif exc.status_code == 404:
            error_type = ErrorType.NOT_FOUND_ERROR
        elif exc.status_code == 409:
            error_type = ErrorType.CONFLICT_ERROR
        elif exc.status_code == 429:
            error_type = ErrorType.RATE_LIMIT_ERROR
        elif 500 <= exc.status_code < 600:
            error_type = ErrorType.SERVICE_ERROR

        error_response = ErrorHandler.create_error_response(
            error_type=error_type,
            message=str(exc.detail),
            correlation_id=correlation_id,
            path=str(request.url.path),
            status_code=exc.status_code,
        )

        logger.error(
            f"HTTP exception on {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "status_code": exc.status_code,
                "detail": exc.detail,
            },
        )

        raise HTTPException(
            status_code=exc.status_code, detail=error_response.model_dump(mode="json")
        )

else:
    # Fallback handlers when FastAPI is not available
    validation_exception_handler = None
    http_exception_handler = None

# Export all public components
__all__ = [
    "ErrorType",
    "FieldError",
    "ErrorResponse",
    "SuccessResponse",
    "ValidationUtils",
    "ErrorHandler",
    "validation_exception_handler",
    "http_exception_handler",
]
