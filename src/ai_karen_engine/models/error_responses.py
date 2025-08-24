from __future__ import annotations

"""Standardized error response models for API endpoints."""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebAPIErrorCode(str, Enum):
    """Generic error codes used across API endpoints."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SERVICE_ERROR = "SERVICE_ERROR"
    PLUGIN_ERROR = "PLUGIN_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    AI_PROCESSING_ERROR = "AI_PROCESSING_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WebAPIErrorResponse(BaseModel):
    """Standard error response returned by API routes."""

    error: str
    message: str
    type: WebAPIErrorCode
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: str


class ValidationErrorDetail(BaseModel):
    """Detailed information for validation errors."""

    field: str
    message: str
    invalid_value: Any


def create_error_response(
    error_code: WebAPIErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    user_message: Optional[str] = None,
) -> WebAPIErrorResponse:
    """Helper to create a :class:`WebAPIErrorResponse`."""

    return WebAPIErrorResponse(
        error=user_message or message,
        message=message,
        type=error_code,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat(),
    )
