from fastapi.responses import JSONResponse
from ai_karen_engine.core.errors.handlers import get_error_handler


def handle_api_exception(error: Exception, user_message: str | None = None) -> JSONResponse:
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
    return JSONResponse(status_code=status_code, content=error_response.model_dump(mode="json"))
