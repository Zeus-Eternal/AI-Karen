"""
Correlation Middleware for Request Tracking
Adds correlation ID to all requests and manages request context.
"""

import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ai_karen_engine.services.correlation_service import CorrelationService


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or create correlation ID
        headers = {key.lower(): value for key, value in request.headers.items()}
        correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        # Set in context
        CorrelationService.set_correlation_id(correlation_id)
        
        # Add to request state for easy access
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = correlation_id
        
        return response


def get_request_correlation_id(request: Request) -> str:
    """Get correlation ID from request state"""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))