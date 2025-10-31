"""
Production Monitoring Middleware

Automatically collects production metrics from HTTP requests, authentication events,
and response formatting operations.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import time
import logging
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.production_monitoring_service import (
    get_production_monitoring_service
)

logger = get_logger(__name__)


class ProductionMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically collects production monitoring metrics
    from HTTP requests and responses.
    """

    def __init__(self, app, collect_detailed_metrics: bool = True):
        super().__init__(app)
        self.collect_detailed_metrics = collect_detailed_metrics
        self.monitoring_service = get_production_monitoring_service()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = str(request.url.path)
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Record API response time metrics
            self.monitoring_service.record_api_response_time(
                endpoint=path,
                method=method,
                response_time_ms=response_time_ms,
                status_code=response.status_code
            )
            
            # Check for authentication failures
            if response.status_code == 401:
                self.monitoring_service.record_authentication_failure(
                    failure_reason="unauthorized",
                    source_ip=client_ip,
                    user_agent=user_agent
                )
            elif response.status_code == 403:
                self.monitoring_service.record_authentication_failure(
                    failure_reason="forbidden",
                    source_ip=client_ip,
                    user_agent=user_agent
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            response_time_ms = (time.time() - start_time) * 1000
            
            self.monitoring_service.record_api_response_time(
                endpoint=path,
                method=method,
                response_time_ms=response_time_ms,
                status_code=500
            )
            
            logger.error(f"Request processing error: {e}")
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"