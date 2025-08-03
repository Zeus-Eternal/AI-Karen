import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.sessions import SessionMiddleware

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
        https_only=True,
    )

    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
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

    @app.middleware("http")
    async def request_monitoring_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
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
        except Exception:
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
