"""
Middleware setup for AI Karen FastAPI gateway.
"""

import os
from typing import List

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
except ImportError:
    FastAPI = object
    CORSMiddleware = object
    GZipMiddleware = object
    TrustedHostMiddleware = object

from ai_karen_engine.core.errors import error_middleware
from ai_karen_engine.core.logging import logging_middleware, get_logger

logger = get_logger(__name__)


def setup_cors_middleware(app: FastAPI) -> None:
    """
    Setup CORS middleware.
    
    Args:
        app: FastAPI application
    """
    # Get CORS configuration from environment
    allowed_origins = os.getenv("KAREN_CORS_ORIGINS", "*")
    allowed_methods = os.getenv("KAREN_CORS_METHODS", "*")
    allowed_headers = os.getenv("KAREN_CORS_HEADERS", "*")
    allow_credentials = os.getenv("KAREN_CORS_CREDENTIALS", "true").lower() == "true"
    
    # Parse origins
    if allowed_origins == "*":
        origins = ["*"]
    else:
        origins = [origin.strip() for origin in allowed_origins.split(",")]
    
    # Parse methods
    if allowed_methods == "*":
        methods = ["*"]
    else:
        methods = [method.strip() for method in allowed_methods.split(",")]
    
    # Parse headers
    if allowed_headers == "*":
        headers = ["*"]
    else:
        headers = [header.strip() for header in allowed_headers.split(",")]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=methods,
        allow_headers=headers,
    )
    
    logger.info(f"CORS middleware configured: origins={origins}")


def setup_compression_middleware(app: FastAPI) -> None:
    """
    Setup compression middleware.
    
    Args:
        app: FastAPI application
    """
    # Get compression configuration
    enable_compression = os.getenv("KAREN_ENABLE_COMPRESSION", "true").lower() == "true"
    min_size = int(os.getenv("KAREN_COMPRESSION_MIN_SIZE", "512"))
    
    if enable_compression:
        try:
            app.add_middleware(GZipMiddleware, minimum_size=min_size)
            logger.info(f"Compression middleware enabled: min_size={min_size}")
        except Exception as e:
            logger.warning(f"Failed to enable compression middleware: {e}")


def setup_trusted_host_middleware(app: FastAPI) -> None:
    """
    Setup trusted host middleware for security.
    
    Args:
        app: FastAPI application
    """
    # Get trusted hosts configuration
    trusted_hosts = os.getenv("KAREN_TRUSTED_HOSTS")
    
    if trusted_hosts:
        hosts = [host.strip() for host in trusted_hosts.split(",")]
        
        try:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
            logger.info(f"Trusted host middleware enabled: hosts={hosts}")
        except Exception as e:
            logger.warning(f"Failed to enable trusted host middleware: {e}")


def setup_security_headers_middleware(app: FastAPI) -> None:
    """
    Setup security headers middleware.
    
    Args:
        app: FastAPI application
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Add CSP header if not in debug mode
            if not os.getenv("KAREN_DEBUG", "false").lower() == "true":
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' data:; "
                    "connect-src 'self'"
                )
            
            return response
    
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")


def setup_rate_limiting_middleware(app: FastAPI) -> None:
    """
    Setup rate limiting middleware.
    
    Args:
        app: FastAPI application
    """
    # This is a placeholder for rate limiting middleware
    # In a production environment, you would use a proper rate limiting solution
    # like slowapi or implement custom rate limiting with Redis
    
    enable_rate_limiting = os.getenv("KAREN_ENABLE_RATE_LIMITING", "false").lower() == "true"
    
    if enable_rate_limiting:
        try:
            # Import slowapi if available
            from slowapi import Limiter, _rate_limit_exceeded_handler
            from slowapi.util import get_remote_address
            from slowapi.errors import RateLimitExceeded
            
            limiter = Limiter(key_func=get_remote_address)
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            
            logger.info("Rate limiting middleware enabled")
            
        except ImportError:
            logger.warning("Rate limiting requested but slowapi not available")


def setup_middleware(app: FastAPI, debug: bool = False) -> None:
    """
    Setup all middleware for the FastAPI application.
    
    Args:
        app: FastAPI application
        debug: Debug mode flag
    """
    logger.info("Setting up middleware")
    
    # Order matters for middleware - they are applied in reverse order
    
    # 1. Error handling (should be last to catch all errors)
    app.add_middleware(error_middleware(app, include_traceback=debug))
    
    # 2. Logging (should be early to log all requests)
    app.add_middleware(logging_middleware(app, include_request_body=debug))
    
    # 3. Security headers
    setup_security_headers_middleware(app)
    
    # 4. Rate limiting
    setup_rate_limiting_middleware(app)
    
    # 5. Trusted hosts (security)
    setup_trusted_host_middleware(app)
    
    # 6. Compression
    setup_compression_middleware(app)
    
    # 7. CORS (should be early for preflight requests)
    setup_cors_middleware(app)
    
    logger.info("Middleware setup completed")