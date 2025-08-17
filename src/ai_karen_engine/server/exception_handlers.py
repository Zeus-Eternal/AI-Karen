"""
Custom exception handlers for FastAPI.

This module provides custom exception handlers that properly handle
JSON serialization of datetime objects and other non-serializable types.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai_karen_engine.server.json_encoder import custom_json_dumps

logger = logging.getLogger(__name__)


async def custom_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Custom HTTP exception handler that properly serializes datetime objects.

    Args:
        request: The FastAPI request object
        exc: The HTTPException that was raised

    Returns:
        JSONResponse with properly serialized content
    """
    # Extract exception details
    status_code = exc.status_code
    detail = exc.detail

    # Create response content
    content: Dict[str, Any] = {"detail": detail}

    # Add additional context if available
    if hasattr(exc, "headers") and exc.headers:
        # Don't include headers in response content, but log them
        logger.debug(f"HTTP exception headers: {exc.headers}")

    # Add timestamp and request info for debugging
    if logger.isEnabledFor(logging.DEBUG):
        content.update(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path),
                "method": request.method,
            }
        )

    try:
        # Use custom JSON encoder to handle datetime objects
        json_content = custom_json_dumps(content)

        return JSONResponse(
            status_code=status_code,
            content=json.loads(json_content),  # Parse back to dict for JSONResponse
            headers=getattr(exc, "headers", None),
        )
    except Exception as json_error:
        # Fallback if JSON serialization still fails
        logger.error(f"Failed to serialize exception response: {json_error}")

        # Create a minimal safe response
        safe_content = {
            "detail": str(detail) if detail else "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": "serialization_error",
        }

        return JSONResponse(
            status_code=status_code,
            content=safe_content,
            headers=getattr(exc, "headers", None),
        )


async def custom_starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Custom Starlette HTTP exception handler.

    Args:
        request: The request object
        exc: The Starlette HTTPException

    Returns:
        JSONResponse with properly serialized content
    """
    # Convert Starlette exception to FastAPI format
    fastapi_exc = HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
        headers=getattr(exc, "headers", None),
    )

    return await custom_http_exception_handler(request, fastapi_exc)


async def custom_validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Custom validation exception handler.

    Args:
        request: The request object
        exc: The validation exception

    Returns:
        JSONResponse with validation error details
    """
    logger.warning(f"Validation error on {request.method} {request.url.path}: {exc}")

    content = {
        "detail": "Validation error",
        "message": str(exc),
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path),
        "method": request.method,
    }

    try:
        json_content = custom_json_dumps(content)
        return JSONResponse(status_code=422, content=json.loads(json_content))
    except Exception as json_error:
        logger.error(f"Failed to serialize validation error response: {json_error}")

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "message": "Unable to serialize error details",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


async def custom_general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Custom general exception handler for unhandled exceptions.

    Args:
        request: The request object
        exc: The unhandled exception

    Returns:
        JSONResponse with error details
    """
    logger.exception(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}"
    )

    content = {
        "detail": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url.path),
        "method": request.method,
    }

    # Add exception details in debug mode
    if logger.isEnabledFor(logging.DEBUG):
        content.update(
            {"exception_type": type(exc).__name__, "exception_message": str(exc)}
        )

    try:
        json_content = custom_json_dumps(content)
        return JSONResponse(status_code=500, content=json.loads(json_content))
    except Exception as json_error:
        logger.error(f"Failed to serialize general error response: {json_error}")

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": "Unable to serialize error details",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


def setup_exception_handlers(app) -> None:
    """
    Setup custom exception handlers for the FastAPI app.

    Args:
        app: The FastAPI application instance
    """
    # Import here to avoid circular imports
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    # Add custom exception handlers
    app.add_exception_handler(HTTPException, custom_http_exception_handler)
    app.add_exception_handler(
        StarletteHTTPException, custom_starlette_http_exception_handler
    )
    app.add_exception_handler(
        RequestValidationError, custom_validation_exception_handler
    )
    app.add_exception_handler(Exception, custom_general_exception_handler)

    logger.info("Custom exception handlers registered")
