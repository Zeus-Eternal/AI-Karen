"""
Security Middleware - Phase 4.1.d
Production-ready security middleware with HTTPS enforcement, CORS allowlists, and security incident logging.
"""

import logging
import time
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import re

from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Graceful imports with fallback mechanisms
try:
    from ai_karen_engine.services.structured_logging import get_security_logger, SecurityEventType
    SECURITY_LOGGING_AVAILABLE = True
except ImportError:
    logger.warning("Security logging not available, using fallback")
    SECURITY_LOGGING_AVAILABLE = False

try:
    from ai_karen_engine.services.correlation_service import CorrelationService
    CORRELATION_AVAILABLE = True
except ImportError:
    logger.warning("Correlation service not available, using fallback")
    CORRELATION_AVAILABLE = False

class SecurityConfig:
    """Security configuration"""
    
    def __init__(self):
        # HTTPS enforcement - Disable for development
        import os
        environment = os.getenv("ENVIRONMENT", "development").lower()
        self.enforce_https = environment == "production"
        self.https_redirect = environment == "production"
        
        # CORS configuration - Allow both HTTP and HTTPS for development
        self.cors_allowed_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8020",
            "http://127.0.0.1:8020",
            "http://localhost:8010",
            "http://127.0.0.1:8010",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:39397",  # Browser preview port
            "http://127.0.0.1:44985",  # Current browser preview port
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            "https://localhost:8020",
            "https://127.0.0.1:8020",
            "https://localhost:8010",
            "https://127.0.0.1:8010",
            "https://localhost:8080",
            "https://127.0.0.1:8080",
            "https://127.0.0.1:39397",  # Browser preview port HTTPS
            "https://127.0.0.1:44985"   # Current browser preview port HTTPS
        ]
        self.cors_allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.cors_allowed_headers = [
            "Authorization",
            "Content-Type",
            "X-Correlation-Id",
            "X-Request-Id",
            "X-Trace-Id",
            "Cache-Control",
            "Accept",
            "Origin",
            "User-Agent",
            "X-CSRF-Token"
        ]
        self.cors_allow_credentials = True
        
        # Rate limiting
        self.rate_limit_enabled = True
        self.rate_limit_requests = 100
        self.rate_limit_window = 60  # seconds
        
        # Security headers
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        # Suspicious patterns
        self.suspicious_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            re.compile(r'union\s+select', re.IGNORECASE),
            re.compile(r'drop\s+table', re.IGNORECASE),
            re.compile(r'insert\s+into', re.IGNORECASE),
            re.compile(r'delete\s+from', re.IGNORECASE),
            re.compile(r'\.\./', re.IGNORECASE),
            re.compile(r'etc/passwd', re.IGNORECASE)
        ]

class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce HTTPS in production"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.security_logger = get_security_logger() if SECURITY_LOGGING_AVAILABLE else None
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID
        correlation_id = None
        if CORRELATION_AVAILABLE:
            headers = {key: value for key, value in request.headers.items()}
            correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        # Check if HTTPS enforcement is enabled
        if self.config.enforce_https:
            # Check if request is HTTPS
            is_https = (
                request.url.scheme == "https" or
                request.headers.get("x-forwarded-proto") == "https" or
                request.headers.get("x-forwarded-ssl") == "on"
            )
            
            if not is_https:
                # Log security incident
                if self.security_logger:
                    self.security_logger.log_suspicious_activity(
                        description="HTTP request to HTTPS-only endpoint",
                        ip_address=self._get_client_ip(request),
                        correlation_id=correlation_id,
                        endpoint=str(request.url.path),
                        method=request.method,
                        user_agent=request.headers.get("user-agent")
                    )
                
                if self.config.https_redirect:
                    # Redirect to HTTPS
                    https_url = str(request.url).replace("http://", "https://", 1)
                    return JSONResponse(
                        status_code=301,
                        content={"error": "HTTPS required", "redirect_url": https_url},
                        headers={"Location": https_url}
                    )
                else:
                    # Return error
                    return JSONResponse(
                        status_code=400,
                        content={"error": "HTTPS required for this endpoint"}
                    )
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.config.security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security logging"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.security_logger = get_security_logger() if SECURITY_LOGGING_AVAILABLE else None
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID
        correlation_id = None
        if CORRELATION_AVAILABLE:
            headers = {key: value for key, value in request.headers.items()}
            correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        if origin and not self._is_origin_allowed(origin):
            # Log security incident
            if self.security_logger:
                self.security_logger.log_suspicious_activity(
                    description=f"Request from disallowed origin: {origin}",
                    ip_address=self._get_client_ip(request),
                    correlation_id=correlation_id,
                    endpoint=str(request.url.path),
                    method=request.method,
                    origin=origin
                )
            
            return JSONResponse(
                status_code=403,
                content={"error": "Origin not allowed"}
            )
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, origin)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(response, origin)
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowlist"""
        if not origin:
            return False
        
        # Check exact matches
        if origin in self.config.cors_allowed_origins:
            return True
        
        # Check wildcard patterns
        for allowed_origin in self.config.cors_allowed_origins:
            if allowed_origin == "*":
                return True
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]
                if origin.endswith(domain):
                    return True
        
        return False
    
    def _add_cors_headers(self, response: Response, origin: str = None):
        """Add CORS headers to response"""
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_allowed_headers)
        
        if self.config.cors_allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to detect and log malicious input"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.security_logger = get_security_logger() if SECURITY_LOGGING_AVAILABLE else None
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID
        correlation_id = None
        if CORRELATION_AVAILABLE:
            headers = {key: value for key, value in request.headers.items()}
            correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        # Check URL path for suspicious patterns
        suspicious_patterns_found = []
        for pattern in self.config.suspicious_patterns:
            if pattern.search(str(request.url.path)):
                suspicious_patterns_found.append(pattern.pattern)
        
        # Check query parameters
        query_string = str(request.url.query)
        if query_string:
            for pattern in self.config.suspicious_patterns:
                if pattern.search(query_string):
                    suspicious_patterns_found.append(pattern.pattern)
        
        # Check headers for suspicious content
        for header_name, header_value in request.headers.items():
            if isinstance(header_value, str):
                for pattern in self.config.suspicious_patterns:
                    if pattern.search(header_value):
                        suspicious_patterns_found.append(pattern.pattern)
        
        # If suspicious patterns found, log and potentially block
        if suspicious_patterns_found:
            if self.security_logger:
                self.security_logger.log_security_event({
                    'event_type': SecurityEventType.MALICIOUS_INPUT_DETECTED,
                    'severity': 'HIGH',
                    'description': f'Malicious input patterns detected: {suspicious_patterns_found}',
                    'ip_address': self._get_client_ip(request),
                    'correlation_id': correlation_id,
                    'endpoint': str(request.url.path),
                    'method': request.method,
                    'patterns': suspicious_patterns_found,
                    'user_agent': request.headers.get('user-agent')
                })
            
            # For now, log but don't block - in production you might want to block
            logger.warning(f"Suspicious input detected: {suspicious_patterns_found}")
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with security logging"""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.security_logger = get_security_logger() if SECURITY_LOGGING_AVAILABLE else None
        
        # Import and configure enhanced rate limiter
        try:
            from ai_karen_engine.middleware.rate_limit import get_rate_limiter
            self.enhanced_limiter = get_rate_limiter()
            self.use_enhanced = True
        except ImportError:
            # Fallback to simple rate limiting
            self.request_counts = {}
            self.last_cleanup = time.time()
            self.use_enhanced = False
    
    async def dispatch(self, request: Request, call_next):
        if not self.config.rate_limit_enabled:
            return await call_next(request)
        
        if self.use_enhanced:
            return await self._enhanced_rate_limit(request, call_next)
        else:
            return await self._simple_rate_limit(request, call_next)
    
    async def _enhanced_rate_limit(self, request: Request, call_next):
        """Use enhanced rate limiter"""
        # Get correlation ID
        correlation_id = None
        if CORRELATION_AVAILABLE:
            headers = {key: value for key, value in request.headers.items()}
            correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_id = request.headers.get("x-user-id")
        user_type = request.headers.get("x-user-type")
        endpoint = str(request.url.path)
        
        try:
            # Check rate limit using enhanced limiter
            result = await self.enhanced_limiter.check_rate_limit(
                ip_address=client_ip,
                endpoint=endpoint,
                user_id=user_id,
                user_type=user_type
            )
            
            if not result.allowed:
                # Log rate limit violation
                if self.security_logger:
                    self.security_logger.log_rate_limit_violation(
                        user_id=user_id or "anonymous",
                        endpoint=endpoint,
                        limit=result.limit,
                        current_count=result.current_count,
                        correlation_id=correlation_id,
                        ip_address=client_ip,
                        method=request.method
                    )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Try again in {result.retry_after_seconds} seconds.",
                        "details": {
                            "rule": result.rule_name,
                            "limit": result.limit,
                            "window_seconds": result.window_seconds,
                            "current_count": result.current_count,
                            "reset_time": result.reset_time.isoformat(),
                        }
                    },
                    headers={
                        "Retry-After": str(result.retry_after_seconds),
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(max(0, result.limit - result.current_count)),
                        "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
                        "X-RateLimit-Rule": result.rule_name,
                    }
                )
            
            # Record the request
            await self.enhanced_limiter.record_request(
                ip_address=client_ip,
                endpoint=endpoint,
                user_id=user_id,
                user_type=user_type
            )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(result.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, result.limit - result.current_count - 1))
            response.headers["X-RateLimit-Reset"] = str(int(result.reset_time.timestamp()))
            response.headers["X-RateLimit-Rule"] = result.rule_name
            
            return response
            
        except Exception as e:
            # Log error but don't block requests
            if self.security_logger:
                self.security_logger.log_error(f"Enhanced rate limiting error: {e}")
            
            # Fallback to simple rate limiting
            return await self._simple_rate_limit(request, call_next)
    
    async def _simple_rate_limit(self, request: Request, call_next):
        """Fallback simple rate limiting"""
        # Get correlation ID
        correlation_id = None
        if CORRELATION_AVAILABLE:
            headers = {key: value for key, value in request.headers.items()}
            correlation_id = CorrelationService.get_or_create_correlation_id(headers)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = request.headers.get("x-user-id", "anonymous")
        client_key = f"{client_ip}:{user_id}"
        
        # Clean up old entries periodically
        current_time = time.time()
        if current_time - self.last_cleanup > 60:  # Cleanup every minute
            self._cleanup_old_entries(current_time)
            self.last_cleanup = current_time
        
        # Check rate limit
        window_start = current_time - self.config.rate_limit_window
        
        if client_key not in self.request_counts:
            self.request_counts[client_key] = []
        
        # Remove old requests outside the window
        self.request_counts[client_key] = [
            timestamp for timestamp in self.request_counts[client_key]
            if timestamp > window_start
        ]
        
        # Check if rate limit exceeded
        current_count = len(self.request_counts[client_key])
        if current_count >= self.config.rate_limit_requests:
            # Log rate limit violation
            if self.security_logger:
                self.security_logger.log_rate_limit_violation(
                    user_id=user_id,
                    endpoint=str(request.url.path),
                    limit=self.config.rate_limit_requests,
                    current_count=current_count,
                    correlation_id=correlation_id,
                    ip_address=client_ip,
                    method=request.method
                )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "limit": self.config.rate_limit_requests,
                    "window": self.config.rate_limit_window,
                    "retry_after": self.config.rate_limit_window
                },
                headers={"Retry-After": str(self.config.rate_limit_window)}
            )
        
        # Add current request to count
        self.request_counts[client_key].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(self.config.rate_limit_requests - current_count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(window_start + self.config.rate_limit_window))
        
        return response
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up old rate limit entries"""
        window_start = current_time - self.config.rate_limit_window
        
        for client_key in list(self.request_counts.keys()):
            self.request_counts[client_key] = [
                timestamp for timestamp in self.request_counts[client_key]
                if timestamp > window_start
            ]
            
            # Remove empty entries
            if not self.request_counts[client_key]:
                del self.request_counts[client_key]
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class SecurityMiddlewareStack:
    """Complete security middleware stack"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
    
    def add_to_app(self, app):
        """Add all security middleware to FastAPI app"""
        # Add middleware in reverse order (last added is executed first)
        
        # Rate limiting (outermost)
        app.add_middleware(RateLimitMiddleware, config=self.config)
        
        # Input validation
        app.add_middleware(InputValidationMiddleware, config=self.config)
        
        # CORS security
        app.add_middleware(CORSSecurityMiddleware, config=self.config)
        
        # HTTPS enforcement (innermost)
        app.add_middleware(HTTPSEnforcementMiddleware, config=self.config)
        
        logger.info("Security middleware stack configured")

# Global security configuration
_security_config: Optional[SecurityConfig] = None

def get_security_config() -> SecurityConfig:
    """Get global security configuration"""
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig()
    return _security_config

def init_security_config(
    enforce_https: bool = True,
    cors_allowed_origins: List[str] = None,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60
) -> SecurityConfig:
    """Initialize global security configuration"""
    global _security_config
    _security_config = SecurityConfig()
    
    _security_config.enforce_https = enforce_https
    if cors_allowed_origins:
        _security_config.cors_allowed_origins = cors_allowed_origins
    _security_config.rate_limit_requests = rate_limit_requests
    _security_config.rate_limit_window = rate_limit_window
    
    return _security_config

# Export main classes and functions
__all__ = [
    "SecurityConfig",
    "HTTPSEnforcementMiddleware",
    "CORSSecurityMiddleware", 
    "InputValidationMiddleware",
    "RateLimitMiddleware",
    "SecurityMiddlewareStack",
    "get_security_config",
    "init_security_config"
]