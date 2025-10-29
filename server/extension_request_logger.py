"""
Extension request/response logging system for troubleshooting.
Provides detailed logging and tracing of extension API requests.
"""

import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import asyncio
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class RequestTrace:
    """Request trace information."""
    trace_id: str
    timestamp: datetime
    method: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    body: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class ResponseTrace:
    """Response trace information."""
    trace_id: str
    status_code: int
    headers: Dict[str, str]
    body: Optional[str] = None
    response_time_ms: float = 0
    error: Optional[str] = None

@dataclass
class RequestResponseLog:
    """Complete request/response log entry."""
    trace_id: str
    request: RequestTrace
    response: Optional[ResponseTrace] = None
    duration_ms: float = 0
    error: Optional[str] = None
    auth_info: Optional[Dict[str, Any]] = None
    extension_context: Optional[Dict[str, Any]] = None

class ExtensionRequestLogger:
    """Advanced request/response logger for extension APIs."""

    def __init__(self, max_logs: int = 1000, max_body_size: int = 10000):
        self.max_logs = max_logs
        self.max_body_size = max_body_size
        self.logs: deque = deque(maxlen=max_logs)
        self.active_requests: Dict[str, RequestResponseLog] = {}
        self.filters: List[Callable] = []
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        }
        self.sensitive_body_fields = {
            'password', 'token', 'secret', 'key', 'credential'
        }

    def add_filter(self, filter_func: Callable[[RequestResponseLog], bool]):
        """Add a filter function to determine which requests to log."""
        self.filters.append(filter_func)

    def should_log_request(self, log_entry: RequestResponseLog) -> bool:
        """Determine if request should be logged based on filters."""
        if not self.filters:
            return True
        
        return any(filter_func(log_entry) for filter_func in self.filters)

    async def log_request(
        self, 
        request: Request, 
        auth_info: Optional[Dict[str, Any]] = None,
        extension_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log incoming request and return trace ID."""
        try:
            trace_id = str(uuid.uuid4())
            
            # Extract request information
            request_trace = RequestTrace(
                trace_id=trace_id,
                timestamp=datetime.utcnow(),
                method=request.method,
                path=str(request.url.path),
                query_params=dict(request.query_params),
                headers=self._sanitize_headers(dict(request.headers)),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get('user-agent'),
                user_id=auth_info.get('user_id') if auth_info else None,
                tenant_id=auth_info.get('tenant_id') if auth_info else None
            )
            
            # Read and sanitize request body
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.body()
                    if body:
                        body_str = body.decode('utf-8')
                        request_trace.body = self._sanitize_body(body_str)
                except Exception as e:
                    logger.warning(f"Could not read request body: {e}")
                    request_trace.body = f"<Error reading body: {e}>"
            
            # Create log entry
            log_entry = RequestResponseLog(
                trace_id=trace_id,
                request=request_trace,
                auth_info=auth_info,
                extension_context=extension_context
            )
            
            # Store active request
            self.active_requests[trace_id] = log_entry
            
            logger.debug(f"Logged request {trace_id}: {request.method} {request.url.path}")
            return trace_id
            
        except Exception as e:
            logger.error(f"Error logging request: {e}")
            return str(uuid.uuid4())  # Return a trace ID even on error

    async def log_response(
        self, 
        trace_id: str, 
        response: Response, 
        start_time: float,
        error: Optional[str] = None
    ):
        """Log response for a traced request."""
        try:
            if trace_id not in self.active_requests:
                logger.warning(f"No active request found for trace ID {trace_id}")
                return
            
            log_entry = self.active_requests[trace_id]
            duration_ms = (time.time() - start_time) * 1000
            
            # Create response trace
            response_trace = ResponseTrace(
                trace_id=trace_id,
                status_code=response.status_code,
                headers=self._sanitize_headers(dict(response.headers)),
                response_time_ms=duration_ms,
                error=error
            )
            
            # Try to capture response body for debugging
            if hasattr(response, 'body') and response.body:
                try:
                    body_str = response.body.decode('utf-8') if isinstance(response.body, bytes) else str(response.body)
                    response_trace.body = self._sanitize_body(body_str)
                except Exception as e:
                    logger.debug(f"Could not capture response body: {e}")
            
            # Update log entry
            log_entry.response = response_trace
            log_entry.duration_ms = duration_ms
            log_entry.error = error
            
            # Check if should log this request
            if self.should_log_request(log_entry):
                self.logs.append(log_entry)
            
            # Remove from active requests
            del self.active_requests[trace_id]
            
            logger.debug(f"Logged response {trace_id}: {response.status_code} ({duration_ms:.2f}ms)")
            
        except Exception as e:
            logger.error(f"Error logging response for trace {trace_id}: {e}")

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                if key.lower() == 'authorization' and value.startswith('Bearer '):
                    # Show token type but mask the actual token
                    sanitized[key] = f"Bearer ***{value[-8:]}"
                else:
                    sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _sanitize_body(self, body: str) -> str:
        """Sanitize sensitive information in request/response body."""
        try:
            # Limit body size
            if len(body) > self.max_body_size:
                body = body[:self.max_body_size] + "...<truncated>"
            
            # Try to parse as JSON and sanitize sensitive fields
            try:
                data = json.loads(body)
                sanitized_data = self._sanitize_json_data(data)
                return json.dumps(sanitized_data, indent=2)
            except json.JSONDecodeError:
                # Not JSON, return as-is (could add more sanitization for other formats)
                return body
                
        except Exception as e:
            logger.warning(f"Error sanitizing body: {e}")
            return "<Error sanitizing body>"

    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if key.lower() in self.sensitive_body_fields:
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_json_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_json_data(item) for item in data]
        else:
            return data

    def get_logs(
        self, 
        limit: int = 100, 
        extension_name: Optional[str] = None,
        status_code: Optional[int] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered logs."""
        try:
            filtered_logs = []
            
            for log_entry in reversed(list(self.logs)):
                # Apply filters
                if extension_name and not self._matches_extension(log_entry, extension_name):
                    continue
                
                if status_code and (not log_entry.response or log_entry.response.status_code != status_code):
                    continue
                
                if user_id and log_entry.request.user_id != user_id:
                    continue
                
                if since and log_entry.request.timestamp < since:
                    continue
                
                # Convert to dict for JSON serialization
                log_dict = {
                    'trace_id': log_entry.trace_id,
                    'request': asdict(log_entry.request),
                    'response': asdict(log_entry.response) if log_entry.response else None,
                    'duration_ms': log_entry.duration_ms,
                    'error': log_entry.error,
                    'auth_info': log_entry.auth_info,
                    'extension_context': log_entry.extension_context
                }
                
                # Convert datetime objects to ISO strings
                log_dict['request']['timestamp'] = log_entry.request.timestamp.isoformat()
                
                filtered_logs.append(log_dict)
                
                if len(filtered_logs) >= limit:
                    break
            
            return filtered_logs
            
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []

    def _matches_extension(self, log_entry: RequestResponseLog, extension_name: str) -> bool:
        """Check if log entry matches extension name."""
        # Check if path contains extension name
        if f"/extensions/{extension_name}" in log_entry.request.path:
            return True
        
        # Check extension context
        if log_entry.extension_context and log_entry.extension_context.get('name') == extension_name:
            return True
        
        return False

    def get_request_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get request statistics for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_logs = [
                log for log in self.logs 
                if log.request.timestamp > cutoff_time
            ]
            
            if not recent_logs:
                return {
                    'total_requests': 0,
                    'time_period_hours': hours,
                    'stats': {}
                }
            
            # Calculate statistics
            total_requests = len(recent_logs)
            successful_requests = sum(1 for log in recent_logs 
                                    if log.response and 200 <= log.response.status_code < 400)
            error_requests = total_requests - successful_requests
            
            response_times = [log.duration_ms for log in recent_logs if log.duration_ms > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Status code distribution
            status_codes = {}
            for log in recent_logs:
                if log.response:
                    code = log.response.status_code
                    status_codes[code] = status_codes.get(code, 0) + 1
            
            # Method distribution
            methods = {}
            for log in recent_logs:
                method = log.request.method
                methods[method] = methods.get(method, 0) + 1
            
            # Top paths
            paths = {}
            for log in recent_logs:
                path = log.request.path
                paths[path] = paths.get(path, 0) + 1
            
            top_paths = sorted(paths.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'error_requests': error_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'average_response_time_ms': avg_response_time,
                'time_period_hours': hours,
                'status_code_distribution': status_codes,
                'method_distribution': methods,
                'top_paths': top_paths,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating request stats: {e}")
            return {'error': str(e)}

    def get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific trace."""
        try:
            # Check active requests first
            if trace_id in self.active_requests:
                log_entry = self.active_requests[trace_id]
                return {
                    'trace_id': trace_id,
                    'status': 'active',
                    'request': asdict(log_entry.request),
                    'response': None,
                    'auth_info': log_entry.auth_info,
                    'extension_context': log_entry.extension_context
                }
            
            # Search completed logs
            for log_entry in self.logs:
                if log_entry.trace_id == trace_id:
                    return {
                        'trace_id': trace_id,
                        'status': 'completed',
                        'request': asdict(log_entry.request),
                        'response': asdict(log_entry.response) if log_entry.response else None,
                        'duration_ms': log_entry.duration_ms,
                        'error': log_entry.error,
                        'auth_info': log_entry.auth_info,
                        'extension_context': log_entry.extension_context
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting trace details for {trace_id}: {e}")
            return None

    def clear_logs(self, older_than_hours: Optional[int] = None):
        """Clear logs, optionally only those older than specified hours."""
        try:
            if older_than_hours is None:
                self.logs.clear()
                logger.info("Cleared all request logs")
            else:
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
                original_count = len(self.logs)
                
                # Filter out old logs
                self.logs = deque(
                    (log for log in self.logs if log.request.timestamp > cutoff_time),
                    maxlen=self.max_logs
                )
                
                cleared_count = original_count - len(self.logs)
                logger.info(f"Cleared {cleared_count} request logs older than {older_than_hours} hours")
                
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")

class ExtensionRequestLoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic request/response logging."""

    def __init__(self, app, request_logger: ExtensionRequestLogger):
        super().__init__(app)
        self.request_logger = request_logger

    async def dispatch(self, request: Request, call_next):
        # Only log extension API requests
        if not request.url.path.startswith('/api/extensions/') and not request.url.path.startswith('/api/debug/'):
            return await call_next(request)

        start_time = time.time()
        trace_id = None
        
        try:
            # Log request
            trace_id = await self.request_logger.log_request(request)
            
            # Add trace ID to request state
            request.state.trace_id = trace_id
            
            # Process request
            response = await call_next(request)
            
            # Log response
            await self.request_logger.log_response(trace_id, response, start_time)
            
            # Add trace ID to response headers for debugging
            response.headers['X-Trace-ID'] = trace_id
            
            return response
            
        except Exception as e:
            # Log error response
            if trace_id:
                error_response = Response(status_code=500)
                await self.request_logger.log_response(trace_id, error_response, start_time, str(e))
            
            raise

# Global request logger instance
extension_request_logger = ExtensionRequestLogger()

# Default filters
def extension_api_filter(log_entry: RequestResponseLog) -> bool:
    """Filter to log only extension API requests."""
    return (
        log_entry.request.path.startswith('/api/extensions/') or 
        log_entry.request.path.startswith('/api/debug/')
    )

def error_requests_filter(log_entry: RequestResponseLog) -> bool:
    """Filter to log only error requests."""
    return (
        log_entry.response is None or 
        log_entry.response.status_code >= 400 or 
        log_entry.error is not None
    )

# Add default filters
extension_request_logger.add_filter(extension_api_filter)