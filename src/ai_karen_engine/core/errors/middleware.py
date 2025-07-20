"""
Error handling middleware for FastAPI applications.
"""

from typing import Callable
import logging
import uuid

try:
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    # Fallback for when FastAPI is not available
    Request = object
    Response = object
    JSONResponse = object
    BaseHTTPMiddleware = object

from .handlers import get_error_handler, ErrorHandler

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions and return standardized error responses.
    """
    
    def __init__(self, app, error_handler: ErrorHandler = None):
        super().__init__(app)
        self.error_handler = error_handler or get_error_handler()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any exceptions.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Get or generate trace ID
        trace_id = getattr(request.state, 'trace_id', None)
        if not trace_id:
            trace_id = str(uuid.uuid4())
            request.state.trace_id = trace_id
        
        # Get or generate request ID
        request_id = getattr(request.state, 'request_id', None)
        if not request_id:
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as error:
            # Handle the exception using the error handler
            error_response = self.error_handler.handle_exception(
                error=error,
                request_id=request_id,
                trace_id=trace_id
            )
            
            # Get appropriate HTTP status code
            status_code = self.error_handler.get_http_status_code(error_response.error_code)
            
            # Return JSON error response
            return JSONResponse(
                status_code=status_code,
                content=error_response.dict(),
                headers={
                    "X-Request-ID": request_id,
                    "X-Trace-ID": trace_id
                }
            )


def error_middleware(app, include_traceback: bool = False) -> ErrorHandlingMiddleware:
    """
    Create error handling middleware for FastAPI app.
    
    Args:
        app: FastAPI application
        include_traceback: Whether to include traceback in error responses
        
    Returns:
        Error handling middleware instance
    """
    error_handler = ErrorHandler(include_traceback=include_traceback)
    return ErrorHandlingMiddleware(app, error_handler)