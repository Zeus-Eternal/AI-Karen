"""
Logging middleware for FastAPI applications.
"""

from typing import Callable
import time
import uuid

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    # Fallback for when FastAPI is not available
    Request = object
    Response = object
    BaseHTTPMiddleware = object

from .logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    """
    
    def __init__(self, app, include_request_body: bool = False, include_response_body: bool = False):
        super().__init__(app)
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Generate request ID if not present
        request_id = getattr(request.state, 'request_id', None)
        if not request_id:
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        # Generate trace ID if not present
        trace_id = getattr(request.state, 'trace_id', None)
        if not trace_id:
            trace_id = str(uuid.uuid4())
            request.state.trace_id = trace_id
        
        # Set logging context
        logger.set_context(
            request_id=request_id,
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        # Log request
        start_time = time.time()
        
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        }
        
        # Include request body if configured
        if self.include_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_info["body"] = body.decode('utf-8')[:1000]  # Limit body size
            except Exception as e:
                request_info["body_error"] = str(e)
        
        logger.info("Request started", **request_info)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            response_info = {
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "headers": dict(response.headers)
            }
            
            # Include response body if configured and status is error
            if self.include_response_body and response.status_code >= 400:
                try:
                    # Note: This is tricky with streaming responses
                    # For now, we'll skip body logging for responses
                    pass
                except Exception as e:
                    response_info["body_error"] = str(e)
            
            # Log based on status code
            if response.status_code >= 500:
                logger.error("Request completed with server error", **response_info)
            elif response.status_code >= 400:
                logger.warning("Request completed with client error", **response_info)
            else:
                logger.info("Request completed successfully", **response_info)
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as error:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log exception
            logger.exception(
                "Request failed with exception",
                error_type=type(error).__name__,
                error_message=str(error),
                process_time=round(process_time, 4)
            )
            
            # Re-raise the exception to be handled by error middleware
            raise
        
        finally:
            # Clear logging context
            logger.clear_context()


def logging_middleware(
    app, 
    include_request_body: bool = False, 
    include_response_body: bool = False
) -> LoggingMiddleware:
    """
    Create logging middleware for FastAPI app.
    
    Args:
        app: FastAPI application
        include_request_body: Whether to log request bodies
        include_response_body: Whether to log response bodies
        
    Returns:
        Logging middleware instance
    """
    return LoggingMiddleware(
        app, 
        include_request_body=include_request_body,
        include_response_body=include_response_body
    )