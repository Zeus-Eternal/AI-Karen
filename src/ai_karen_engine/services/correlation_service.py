"""
Correlation ID Tracking Service - Phase 4.1.d
Production-ready correlation ID generation and propagation for request tracing.
"""

import logging
import uuid
from contextvars import ContextVar
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Context variable for correlation ID propagation
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

class CorrelationService:
    """Service for managing correlation IDs across request lifecycle"""
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def extract_correlation_id(headers: Dict[str, str]) -> Optional[str]:
        """Extract correlation ID from request headers"""
        # Check multiple possible header names
        possible_headers = [
            'X-Correlation-Id',
            'X-Correlation-ID', 
            'X-Request-Id',
            'X-Request-ID',
            'X-Trace-Id',
            'X-Trace-ID'
        ]
        
        for header_name in possible_headers:
            if header_name in headers:
                correlation_id = headers[header_name]
                if correlation_id and correlation_id.strip():
                    return correlation_id.strip()
        
        return None
    
    @staticmethod
    def get_or_create_correlation_id(headers: Dict[str, str] = None) -> str:
        """Get existing correlation ID or create a new one"""
        headers = headers or {}
        
        # First try to get from context
        correlation_id = correlation_id_context.get()
        if correlation_id:
            return correlation_id
        
        # Then try to extract from headers
        correlation_id = CorrelationService.extract_correlation_id(headers)
        if correlation_id:
            return correlation_id
        
        # Finally generate a new one
        return CorrelationService.generate_correlation_id()
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Set correlation ID in context"""
        correlation_id_context.set(correlation_id)
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID from context"""
        return correlation_id_context.get()
    
    @staticmethod
    def create_headers_with_correlation_id(correlation_id: str, 
                                         existing_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Create headers dict with correlation ID"""
        headers = existing_headers.copy() if existing_headers else {}
        headers['X-Correlation-Id'] = correlation_id
        return headers
    
    @staticmethod
    def create_log_extra(correlation_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Create extra dict for structured logging with correlation ID"""
        correlation_id = correlation_id or CorrelationService.get_correlation_id()
        extra = {"correlation_id": correlation_id} if correlation_id else {}
        extra.update(kwargs)
        return extra

class CorrelationMiddleware:
    """Middleware for handling correlation ID propagation in FastAPI"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract headers
            headers = dict(scope.get("headers", []))
            header_dict = {
                key.decode(): value.decode() 
                for key, value in headers.items()
            }
            
            # Get or create correlation ID
            correlation_id = CorrelationService.get_or_create_correlation_id(header_dict)
            
            # Set in context
            CorrelationService.set_correlation_id(correlation_id)
            
            # Add to response headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-correlation-id", correlation_id.encode()))
                    message["headers"] = headers
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

class CorrelationLogger:
    """Logger wrapper that automatically includes correlation ID"""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def _log_with_correlation(self, level: int, msg: str, *args, **kwargs):
        """Log message with correlation ID"""
        correlation_id = CorrelationService.get_correlation_id()
        extra = kwargs.get('extra', {})
        if correlation_id:
            extra['correlation_id'] = correlation_id
        kwargs['extra'] = extra
        self.logger.log(level, msg, *args, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with correlation ID"""
        self._log_with_correlation(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with correlation ID"""
        self._log_with_correlation(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with correlation ID"""
        self._log_with_correlation(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with correlation ID"""
        self._log_with_correlation(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with correlation ID"""
        self._log_with_correlation(logging.CRITICAL, msg, *args, **kwargs)

class CorrelationHTTPClient:
    """HTTP client wrapper that propagates correlation IDs"""
    
    def __init__(self, base_client=None):
        self.base_client = base_client
        
        # Try to import httpx or requests as fallback
        try:
            import httpx
            self.client = base_client or httpx.AsyncClient()
            self.client_type = "httpx"
        except ImportError:
            try:
                import requests
                self.client = base_client or requests.Session()
                self.client_type = "requests"
            except ImportError:
                logger.warning("No HTTP client available (httpx or requests)")
                self.client = None
                self.client_type = None
    
    def _add_correlation_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """Add correlation ID to headers"""
        headers = headers or {}
        correlation_id = CorrelationService.get_correlation_id()
        if correlation_id:
            headers = CorrelationService.create_headers_with_correlation_id(
                correlation_id, headers
            )
        return headers
    
    async def get(self, url: str, headers: Dict[str, str] = None, **kwargs):
        """GET request with correlation ID propagation"""
        if not self.client:
            raise RuntimeError("No HTTP client available")
        
        headers = self._add_correlation_headers(headers)
        
        if self.client_type == "httpx":
            return await self.client.get(url, headers=headers, **kwargs)
        else:
            # For requests, we'd need to use a thread pool
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.client.get(url, headers=headers, **kwargs)
            )
    
    async def post(self, url: str, headers: Dict[str, str] = None, **kwargs):
        """POST request with correlation ID propagation"""
        if not self.client:
            raise RuntimeError("No HTTP client available")
        
        headers = self._add_correlation_headers(headers)
        
        if self.client_type == "httpx":
            return await self.client.post(url, headers=headers, **kwargs)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.client.post(url, headers=headers, **kwargs)
            )
    
    async def put(self, url: str, headers: Dict[str, str] = None, **kwargs):
        """PUT request with correlation ID propagation"""
        if not self.client:
            raise RuntimeError("No HTTP client available")
        
        headers = self._add_correlation_headers(headers)
        
        if self.client_type == "httpx":
            return await self.client.put(url, headers=headers, **kwargs)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.client.put(url, headers=headers, **kwargs)
            )
    
    async def delete(self, url: str, headers: Dict[str, str] = None, **kwargs):
        """DELETE request with correlation ID propagation"""
        if not self.client:
            raise RuntimeError("No HTTP client available")
        
        headers = self._add_correlation_headers(headers)
        
        if self.client_type == "httpx":
            return await self.client.delete(url, headers=headers, **kwargs)
        else:
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, lambda: self.client.delete(url, headers=headers, **kwargs)
            )

class CorrelationTracker:
    """Utility class for tracking correlation across service boundaries"""
    
    def __init__(self):
        self.traces = {}
    
    def start_trace(self, correlation_id: str, operation: str, metadata: Dict[str, Any] = None):
        """Start tracking an operation"""
        self.traces[correlation_id] = {
            "correlation_id": correlation_id,
            "operation": operation,
            "start_time": datetime.utcnow(),
            "metadata": metadata or {},
            "spans": []
        }
    
    def add_span(self, correlation_id: str, span_name: str, duration: float, 
                metadata: Dict[str, Any] = None):
        """Add a span to the trace"""
        if correlation_id in self.traces:
            self.traces[correlation_id]["spans"].append({
                "name": span_name,
                "duration": duration,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            })
    
    def end_trace(self, correlation_id: str, status: str = "success", 
                 metadata: Dict[str, Any] = None):
        """End tracking an operation"""
        if correlation_id in self.traces:
            trace = self.traces[correlation_id]
            trace["end_time"] = datetime.utcnow()
            trace["total_duration"] = (trace["end_time"] - trace["start_time"]).total_seconds()
            trace["status"] = status
            if metadata:
                trace["metadata"].update(metadata)
            
            # Log the complete trace
            logger.info(
                f"Trace completed: {trace['operation']} in {trace['total_duration']:.3f}s",
                extra=CorrelationService.create_log_extra(
                    correlation_id,
                    trace_data=trace,
                    operation=trace['operation'],
                    duration=trace['total_duration'],
                    status=status,
                    spans_count=len(trace['spans'])
                )
            )
            
            # Clean up
            del self.traces[correlation_id]
    
    def get_trace(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get current trace data"""
        return self.traces.get(correlation_id)

# Global instances
_correlation_tracker: Optional[CorrelationTracker] = None
_correlation_http_client: Optional[CorrelationHTTPClient] = None

def get_correlation_tracker() -> CorrelationTracker:
    """Get global correlation tracker instance"""
    global _correlation_tracker
    if _correlation_tracker is None:
        _correlation_tracker = CorrelationTracker()
    return _correlation_tracker

def get_correlation_http_client() -> CorrelationHTTPClient:
    """Get global correlation HTTP client instance"""
    global _correlation_http_client
    if _correlation_http_client is None:
        _correlation_http_client = CorrelationHTTPClient()
    return _correlation_http_client

def create_correlation_logger(name: str) -> CorrelationLogger:
    """Create a correlation-aware logger"""
    return CorrelationLogger(name)

# Export main classes and functions
__all__ = [
    "CorrelationService",
    "CorrelationMiddleware", 
    "CorrelationLogger",
    "CorrelationHTTPClient",
    "CorrelationTracker",
    "get_correlation_tracker",
    "get_correlation_http_client",
    "create_correlation_logger"
]