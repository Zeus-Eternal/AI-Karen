import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import StreamingResponse

from ai_karen_engine.middleware.error_counter import error_counter_middleware
from ai_karen_engine.middleware.rate_limit import rate_limit_middleware
from ai_karen_engine.middleware.intelligent_error_handler import IntelligentErrorHandlerMiddleware
# REMOVED: RBAC and session persistence middleware - replaced with simple auth
from ai_karen_engine.server.http_validator import HTTPRequestValidator, ValidationConfig

logger = logging.getLogger(__name__)


def configure_middleware(
    app: FastAPI,
    settings: Any,
    request_count,
    request_latency,
    error_count,
) -> None:
    """Configure all FastAPI middleware."""
    if settings.https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="kari_session",
        same_site="lax",
        https_only=settings.https_redirect,
    )

    # Resolve CORS origins from multiple sources for compatibility
    # Priority: explicit env CORS_ORIGINS -> env KARI_CORS_ORIGINS -> settings -> defaults
    import os as _os
    _origins_source = (
        _os.getenv("CORS_ORIGINS")
        or _os.getenv("KARI_CORS_ORIGINS")
        or getattr(settings, "kari_cors_origins", "")
        or ""
    )
    origins = [o.strip() for o in _origins_source.split(",") if o.strip()]
    
    # Add default development origins if none specified
    env_name = (getattr(settings, "environment", "") or "").lower()
    if not origins and env_name in ("development", "dev", "local", ""):
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:8020",
            "http://127.0.0.1:8020",
            "http://localhost:8010",
            "http://127.0.0.1:8010",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
            "https://localhost:8020", 
            "https://127.0.0.1:8020",
            "https://localhost:8010",
            "https://127.0.0.1:8010",
            "https://localhost:8080",
            "https://127.0.0.1:8080"
        ]
    
    # Safety: de-duplicate while preserving order
    _seen = set()
    origins = [o for o in origins if not (o in _seen or _seen.add(o))]
    # Optional regex-based allowance, useful for dev ports/hosts
    cors_regex = _os.getenv("CORS_ALLOW_ORIGIN_REGEX")
    allow_dev_origins = _os.getenv("ALLOW_DEV_ORIGINS", "false").lower() in ("1", "true", "yes")
    # Default to permissive localhost regex in non-production or when explicitly enabled
    if not cors_regex and (allow_dev_origins or env_name in ("development", "dev", "local", "")):
        cors_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=cors_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
        max_age=600,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Ensure streaming responses are not served with a stale Content-Length.
    # Some upstream handlers and error paths may set Content-Length on a body
    # that is later streamed/altered (e.g., by compression), which can trigger
    # "Response content longer than Content-Length" in Uvicorn.
    @app.middleware("http")
    async def strip_content_length_for_streams(request: Request, call_next):
        response = await call_next(request)
        try:
            # Remove Content-Length for true streaming responses
            if isinstance(response, StreamingResponse):
                response.headers.pop("content-length", None)
                return response

            # Also remove when content is encoded (size may change after gzip/br)
            enc = response.headers.get("content-encoding", "").lower()
            if enc in ("gzip", "br", "deflate"):
                response.headers.pop("content-length", None)

        except Exception:
            # Do not interfere with the response in case of header mutations failing
            pass
        return response

    # REMOVED: RBAC middleware - replaced with simple auth role checking
    logger.info("🔐 Using simple auth system - RBAC middleware removed")

    # Add intelligent error handler (outermost - catches all errors)
    app.add_middleware(
        IntelligentErrorHandlerMiddleware,
        enable_intelligent_responses=True,
        debug_mode=getattr(settings, "environment", "").lower() != "production"
    )
    
    # REMOVED: Session persistence middleware - replaced with simple JWT auth
    logger.info("🔐 Using simple JWT auth - session persistence middleware removed")
    
    # Add extension authentication middleware
    @app.middleware("http")
    async def extension_auth_middleware(request: Request, call_next):
        """Extension-specific authentication middleware."""
        # Only apply to extension API endpoints
        if request.url.path.startswith("/api/extensions"):
            try:
                # Import here to avoid circular imports
                from server.security import extension_auth_manager
                
                # Skip authentication for health endpoints
                if request.url.path.endswith("/health") or request.url.path.endswith("/system/health"):
                    response = await call_next(request)
                    return response
                
                # Skip authentication for OPTIONS requests (CORS preflight)
                if request.method == "OPTIONS":
                    response = await call_next(request)
                    return response
                
                # For extension endpoints, ensure authentication context is available
                # The actual authentication will be handled by the endpoint dependencies
                # This middleware just adds logging and context preparation
                
                logger.debug(f"Extension API request: {request.method} {request.url.path}")
                
                # Add request metadata for extension authentication
                request.state.extension_api = True
                request.state.auth_required = True
                
                response = await call_next(request)
                return response
                
            except Exception as e:
                logger.error(f"Extension authentication middleware error: {e}")
                # Don't block the request, let endpoint handle authentication
                response = await call_next(request)
                return response
        else:
            # Non-extension endpoints, proceed normally
            response = await call_next(request)
            return response

    # Configure and register enhanced rate limiting middleware
    from ai_karen_engine.middleware.rate_limit import configure_rate_limiter
    
    # Check if rate limiting is enabled globally
    enable_rate_limiting = os.getenv("ENABLE_RATE_LIMITING", "false").lower() in ("1", "true", "yes")
    
    if enable_rate_limiting:
        # Configure rate limiter based on environment
        storage_type = "memory"  # Default to memory storage
        redis_url = None
        
        # Try to get Redis configuration from environment
        if os.getenv("REDIS_URL"):
            storage_type = "redis"
            redis_url = os.getenv("REDIS_URL")
        elif os.getenv("RATE_LIMIT_REDIS_URL"):
            storage_type = "redis"
            redis_url = os.getenv("RATE_LIMIT_REDIS_URL")
        
        configure_rate_limiter(storage_type=storage_type, redis_url=redis_url)
        
        # Register enhanced rate limiting middleware - disabled in bypass mode
        auth_mode = os.getenv("AUTH_MODE", "hybrid").lower()
        if auth_mode != "bypass":
            app.middleware("http")(rate_limit_middleware)
        else:
            logger.info("🔓 Skipping rate limiting middleware - AUTH_MODE=bypass")
    else:
        logger.info("🔓 Rate limiting disabled via ENABLE_RATE_LIMITING environment variable")
    # Temporarily disabled to fix runaway usage counter loop
    # app.middleware("http")(error_counter_middleware)

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Content-Security-Policy": "default-src 'self'",
                "Permissions-Policy": "geolocation=(), microphone=()",
            }
        )
        return response

    # Use globally configured validation framework or create default
    import sys
    current_module = sys.modules[__name__]
    validation_config = getattr(current_module, '_validation_config', None)
    enhanced_logger = getattr(current_module, '_enhanced_logger', None)
    
    if validation_config is None:
        # Fallback configuration if initialization failed
        validation_config = ValidationConfig(
            max_content_length=getattr(settings, "max_request_size", 10 * 1024 * 1024),
            log_invalid_requests=True,
            enable_security_analysis=True,
        )
        logger.warning("Using fallback validation configuration")
    
    # Ensure an enhanced logger is available even if initialization path was skipped
    if enhanced_logger is None:
        try:
            from ai_karen_engine.server.enhanced_logger import (
                EnhancedLogger,
                LoggingConfig,
            )
            default_logging_cfg = LoggingConfig(
                log_level="INFO",
                enable_security_logging=True,
                sanitize_data=True,
            )
            # Store on this module so other imports can find it
            import sys as _sys
            _mod = _sys.modules[__name__]
            setattr(_mod, "_enhanced_logger", EnhancedLogger(default_logging_cfg))
            enhanced_logger = getattr(_mod, "_enhanced_logger")
            logger.info("Enhanced logger initialized by middleware")
        except Exception:
            # Proceed without enhanced logger; fallback logging will be used
            pass

    http_validator = HTTPRequestValidator(validation_config)

    @app.middleware("http")
    async def request_monitoring_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Perform comprehensive request validation using the new validator
        validation_result = await http_validator.validate_request(request)

        if not validation_result.is_valid:
            # Get sanitized request data for logging
            sanitized_data = http_validator.sanitize_request_data(request)

            # Log invalid request with sanitized data (INFO level as per requirements)
            if enhanced_logger:
                # Use enhanced logger if available
                enhanced_logger.log_invalid_request(
                    {
                        "request_id": request_id,
                        "error_type": validation_result.error_type,
                        "error_message": validation_result.error_message,
                        "security_threat_level": validation_result.security_threat_level,
                        "sanitized_request": sanitized_data,
                        "validation_details": validation_result.validation_details,
                    },
                    error_type=validation_result.error_type or "validation_error"
                )
            else:
                # Fallback to standard logger
                logger.info(
                    "Invalid request blocked",
                    extra={
                        "request_id": request_id,
                        "error_type": validation_result.error_type,
                        "error_message": validation_result.error_message,
                        "security_threat_level": validation_result.security_threat_level,
                        "sanitized_request": sanitized_data,
                        "validation_details": validation_result.validation_details,
                    },
                )

            # Update error metrics
            error_count.labels(
                method=sanitized_data.get("method", "unknown"),
                path=sanitized_data.get("path", "/unknown"),
                error_type=validation_result.error_type or "validation_error",
            ).inc()

            # Return appropriate error response based on validation result
            from fastapi.responses import Response

            error_responses = {
                "malformed_request": (400, "Bad Request"),
                "invalid_method": (405, "Method Not Allowed"),
                "invalid_headers": (400, "Bad Request"),
                "content_too_large": (413, "Payload Too Large"),
                "security_threat": (403, "Forbidden"),
                "validation_error": (400, "Bad Request"),
            }

            status_code, status_text = error_responses.get(
                validation_result.error_type, (400, "Bad Request")
            )

            return Response(
                content=status_text,
                status_code=status_code,
                headers={
                    "Content-Type": "text/plain",
                    "X-Request-ID": request_id,
                    "X-Validation-Error": validation_result.error_type or "unknown",
                },
            )

        # Log valid request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "security_threat_level": validation_result.security_threat_level,
            },
        )

        start_time = datetime.now(timezone.utc)
        try:
            response = await call_next(request)
        except HTTPException:
            error_count.labels(
                method=request.method,
                path=request.url.path,
                error_type="http_exception",
            ).inc()
            raise
        except Exception as e:
            error_count.labels(
                method=request.method,
                path=request.url.path,
                error_type="unhandled_exception",
            ).inc()
            logger.error(
                "Unhandled exception", exc_info=True, extra={"request_id": request_id}
            )
            raise HTTPException(status_code=500, detail="Internal server error")

        process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        request_count.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        ).inc()

        request_latency.labels(method=request.method, path=request.url.path).observe(
            process_time
        )

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "duration": process_time,
                "status": response.status_code,
            },
        )

        return response
