"""
Integration layer for connecting chat system with existing AI-Karen infrastructure.

This module provides integration points for:
- Authentication system integration
- Error handling and validation middleware
- Logging and monitoring hooks
- Database connection management
- Security middleware
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import HTTPConnection
from starlette.responses import Response

logger = logging.getLogger(__name__)


# Authentication Integration
class AuthIntegration:
    """Integration with existing authentication system."""
    
    def __init__(self):
        # This would integrate with existing auth system
        # For now, provide placeholder implementation
        pass
    
    async def get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get current authenticated user from request."""
        try:
            # Extract token from Authorization header
            auth_header = request.headers.get("authorization")
            if not auth_header:
                return None
            
            # Remove "Bearer " prefix
            token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header
            
            # This would integrate with existing JWT validation
            # For now, return a placeholder user
            if token and len(token) > 10:  # Basic validation
                return {
                    "id": "user_123",
                    "username": "test_user",
                    "email": "test@example.com",
                    "roles": ["user"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def validate_user_access(self, user_id: str, conversation_id: str) -> bool:
        """Validate if user has access to a conversation."""
        try:
            # This would check user permissions in the database
            # For now, allow all access
            return True
            
        except Exception as e:
            logger.error(f"Access validation error: {e}")
            return False


# Error Handling and Validation
class ErrorHandlingMiddleware:
    """Comprehensive error handling and validation middleware."""
    
    def __init__(self):
        self.error_handlers: Dict[type, Callable] = {}
        self.setup_default_handlers()
    
    def setup_default_handlers(self):
        """Setup default error handlers for common exceptions."""
        self.error_handlers.update({
            ValueError: self._handle_validation_error,
            HTTPException: self._handle_http_exception,
            Exception: self._handle_general_exception
        })
    
    def add_handler(self, exception_type: type, handler: Callable):
        """Add custom error handler."""
        self.error_handlers[exception_type] = handler
    
    async def handle_exception(self, request: Request, exc: Exception) -> Response:
        """Handle exceptions with appropriate handler."""
        exception_type = type(exc)
        
        # Find specific handler
        for exc_type_class, handler in self.error_handlers.items():
            if isinstance(exc, exc_type_class):
                return await handler(request, exc)
        
        # Use general handler as fallback
        return await self.error_handlers[Exception](request, exc)
    
    async def _handle_validation_error(self, request: Request, exc: ValueError) -> Response:
        """Handle validation errors."""
        return Response(
            content=self._format_error_response(
                error_type="validation_error",
                message=str(exc),
                details={"field": "validation"}
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
            media_type="application/json"
        )
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> Response:
        """Handle HTTP exceptions."""
        return Response(
            content=self._format_error_response(
                error_type="http_error",
                message=exc.detail,
                details={"status_code": exc.status_code}
            ),
            status_code=exc.status_code,
            media_type="application/json"
        )
    
    async def _handle_general_exception(self, request: Request, exc: Exception) -> Response:
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return Response(
            content=self._format_error_response(
                error_type="internal_error",
                message="An internal error occurred",
                details={"exception_type": type(exc).__name__}
            ),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )
    
    def _format_error_response(self, error_type: str, message: str, details: Dict[str, Any] = None) -> str:
        """Format standardized error response."""
        import json
        from datetime import datetime
        
        return json.dumps({
            "error": {
                "type": error_type,
                "message": message,
                "details": details or {}
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": getattr(self, '_request_id', 'unknown')
        })


# Security Middleware
class SecurityMiddleware:
    """Security middleware for chat operations."""
    
    def __init__(self):
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'"
        }
    
    async def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """Check if user exceeds rate limit."""
        try:
            current_time = time.time()
            user_limits = self.rate_limits.get(user_id, {})
            
            # Clean old entries (older than 1 hour)
            user_limits = {
                k: v for k, v in user_limits.items() 
                if current_time - v.get("timestamp", 0) < 3600
            }
            
            # Get current count for endpoint
            endpoint_key = f"{endpoint}_count"
            current_count = user_limits.get(endpoint_key, 0)
            
            # Check limits (example: 100 messages per hour)
            if endpoint == "send_message" and current_count >= 100:
                return False
            
            # Update count
            user_limits[endpoint_key] = current_count + 1
            user_limits["timestamp"] = current_time
            self.rate_limits[user_id] = user_limits
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error
    
    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response."""
        for header, value in self.security_headers.items():
            response.headers[header] = value
        return response
    
    def validate_input(self, data: Dict[str, Any], input_type: str) -> bool:
        """Validate input data for security."""
        try:
            if input_type == "message":
                content = data.get("content", "")
                
                # Check for dangerous content
                dangerous_patterns = [
                    "<script", "javascript:", "vbscript:", 
                    "onload=", "onerror=", "onclick=",
                    "eval(", "alert(", "confirm("
                ]
                
                for pattern in dangerous_patterns:
                    if pattern.lower() in content.lower():
                        logger.warning(f"Potentially dangerous content detected: {pattern}")
                        return False
                
                # Check content length
                if len(content) > 10000:
                    logger.warning("Message content too long")
                    return False
                
                return True
            
            elif input_type == "conversation":
                # Validate conversation data
                title = data.get("title", "")
                if len(title) > 200:
                    return False
                
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False


# Monitoring and Logging
class MonitoringIntegration:
    """Integration with monitoring and logging systems."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_success": 0,
            "requests_error": 0,
            "response_times": [],
            "active_connections": 0,
            "provider_health": {}
        }
    
    def log_request(self, endpoint: str, user_id: str, method: str = "POST"):
        """Log API request."""
        self.metrics["requests_total"] += 1
        
        logger.info(f"Chat API request: {method} {endpoint} - User: {user_id}")
    
    def log_success(self, endpoint: str, response_time: float, provider: str = None):
        """Log successful request."""
        self.metrics["requests_success"] += 1
        self.metrics["response_times"].append(response_time)
        
        if provider:
            self.metrics["provider_health"][provider] = {
                "last_success": time.time(),
                "status": "healthy"
            }
        
        logger.info(f"Chat API success: {endpoint} - Time: {response_time}ms - Provider: {provider}")
    
    def log_error(self, endpoint: str, error: str, error_type: str = "general"):
        """Log API error."""
        self.metrics["requests_error"] += 1
        
        logger.error(f"Chat API error: {endpoint} - Type: {error_type} - Error: {error}")
    
    def log_websocket_connect(self, user_id: str):
        """Log WebSocket connection."""
        self.metrics["active_connections"] += 1
        
        logger.info(f"WebSocket connected: User: {user_id}")
    
    def log_websocket_disconnect(self, user_id: str):
        """Log WebSocket disconnection."""
        self.metrics["active_connections"] = max(0, self.metrics["active_connections"] - 1)
        
        logger.info(f"WebSocket disconnected: User: {user_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        # Calculate average response time
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            **self.metrics,
            "avg_response_time": avg_response_time,
            "timestamp": time.time()
        }


# Database Integration
class DatabaseIntegration:
    """Integration with database connection management."""
    
    def __init__(self):
        # This would integrate with existing database configuration
        pass
    
    async def get_session(self) -> AsyncSession:
        """Get database session with proper configuration."""
        try:
            # This would use existing database connection management
            # For now, return a placeholder
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy.orm import sessionmaker
            
            # This would use existing configuration
            engine = create_async_engine("postgresql://user:password@localhost/chat_db")
            
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            return async_session()
            
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise


# Decorators for integration
def require_auth(func):
    """Decorator to require authentication."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would integrate with existing auth system
        # For now, just pass through
        return await func(*args, **kwargs)
    
    return wrapper


def validate_chat_input(input_type: str):
    """Decorator to validate chat input."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args
            request = None
            for arg in args:
                if hasattr(arg, 'headers'):  # FastAPI Request object
                    request = arg
                    break
            
            if not request:
                return await func(*args, **kwargs)
            
            # Validate input
            try:
                data = await request.json()
                security = SecurityMiddleware()
                
                if not security.validate_input(data, input_type):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid {input_type} data"
                    )
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Validation failed"
                )
        
        return wrapper
    
    return decorator


def monitor_performance(func):
    """Decorator to monitor performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Get endpoint name
            endpoint = func.__name__
            
            # Get user ID if available
            user_id = "unknown"
            for arg in args:
                if isinstance(arg, dict) and "user_id" in arg:
                    user_id = arg["user_id"]
                    break
            
            monitoring = MonitoringIntegration()
            monitoring.log_request(endpoint, user_id)
            
            result = await func(*args, **kwargs)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Log success
            monitoring.log_success(endpoint, response_time)
            
            return result
            
        except Exception as e:
            endpoint = func.__name__
            monitoring = MonitoringIntegration()
            monitoring.log_error(endpoint, str(e))
            raise
        
        return wrapper


# Main integration class
class ChatSystemIntegration:
    """Main integration class for the chat system."""
    
    def __init__(self):
        self.auth = AuthIntegration()
        self.error_handler = ErrorHandlingMiddleware()
        self.security = SecurityMiddleware()
        self.monitoring = MonitoringIntegration()
        self.database = DatabaseIntegration()
    
    async def get_authenticated_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get authenticated user with full validation."""
        user = await self.auth.get_current_user(request)
        
        if not user:
            return None
        
        # Validate user access
        # This would check specific permissions
        return user
    
    def apply_security_headers(self, response: Response) -> Response:
        """Apply security headers to response."""
        return self.security.add_security_headers(response)
    
    def validate_request_data(self, data: Dict[str, Any], endpoint: str) -> bool:
        """Validate request data."""
        return self.security.validate_input(data, endpoint)
    
    def log_api_call(self, endpoint: str, user_id: str, success: bool = True, response_time: float = 0, error: str = None):
        """Log API call with monitoring."""
        if success:
            self.monitoring.log_success(endpoint, response_time)
        else:
            self.monitoring.log_error(endpoint, error or "Unknown error")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        return self.monitoring.get_metrics()
    
    async def get_database_session(self) -> AsyncSession:
        """Get configured database session."""
        return await self.database.get_session()


# Global integration instance
integration = ChatSystemIntegration()