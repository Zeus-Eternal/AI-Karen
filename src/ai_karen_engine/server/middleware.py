import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .http_validator import HTTPRequestValidator, ValidationConfig

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

    origins = [origin.strip() for origin in settings.kari_cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
        max_age=600,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

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

    # Initialize HTTP validator with configuration
    validation_config = ValidationConfig(
        max_content_length=getattr(settings, 'max_request_size', 10 * 1024 * 1024),
        log_invalid_requests=True,
        enable_security_analysis=True
    )
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
            logger.info(
                "Invalid request blocked",
                extra={
                    "request_id": request_id,
                    "error_type": validation_result.error_type,
                    "error_message": validation_result.error_message,
                    "security_threat_level": validation_result.security_threat_level,
                    "sanitized_request": sanitized_data,
                    "validation_details": validation_result.validation_details
                }
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
                "validation_error": (400, "Bad Request")
            }
            
            status_code, status_text = error_responses.get(
                validation_result.error_type, 
                (400, "Bad Request")
            )
            
            return Response(
                content=status_text,
                status_code=status_code,
                headers={
                    "Content-Type": "text/plain",
                    "X-Request-ID": request_id,
                    "X-Validation-Error": validation_result.error_type or "unknown"
                }
            )

        # Log valid request start
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "security_threat_level": validation_result.security_threat_level
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
            logger.error("Unhandled exception", exc_info=True, extra={"request_id": request_id})
            raise HTTPException(status_code=500, detail="Internal server error")

        process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        request_count.labels(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
        ).inc()

        request_latency.labels(method=request.method, path=request.url.path).observe(process_time)

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "duration": process_time,
                "status": response.status_code,
            },
        )

        return response
