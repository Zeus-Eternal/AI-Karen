"""Utilities for standardized API error handling."""

import logging
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, cast

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ai_karen_engine.core.errors.handlers import get_error_handler

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def handle_api_exception(
    error: Exception, user_message: str | None = None
) -> JSONResponse:
    """Convert exceptions to standardized JSON responses for API routes.

    Args:
        error: The caught exception.
        user_message: Optional message to override the default error message.

    Returns:
        JSONResponse: Response containing standardized error information.
    """
    handler = get_error_handler()
    error_response = handler.handle_exception(error)
    if user_message:
        error_response.message = user_message
    status_code = handler.get_http_status_code(error_response.error_code)
    return JSONResponse(status_code=status_code, content=error_response.dict())


def handle_api_errors(user_message: str | None = None) -> Callable[[F], F]:
    """Decorator to standardize API error handling for route functions.

    Args:
        user_message: Optional message to override the default error message
            when an exception is raised.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Let FastAPI handle HTTPExceptions as-is
                raise
            except Exception as error:  # noqa: BLE001
                logger.exception("Unhandled API error")
                return handle_api_exception(error, user_message)

        return cast(F, wrapper)

    return decorator


__all__ = ["handle_api_exception", "handle_api_errors"]
