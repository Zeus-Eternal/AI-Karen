from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .context import set_log_context, clear_log_context, RuntimeLogContext
from .logger import get_logger
from .events import RuntimeEvents

logger = get_logger("kari.middleware")

class RuntimeLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to bind request context and log request lifecycle."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Create context
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        # Determine client IP hash for privacy
        client_ip = request.client.host if request.client else "0.0.0.0"
        # In real prod we'd hash it properly, here just a placeholder
        client_ip_hash = f"hash_{client_ip[-4:]}"

        ctx = RuntimeLogContext(
            correlation_id=correlation_id,
            request_id=request_id,
            route=request.url.path,
            method=request.method,
            client_ip_hash=client_ip_hash,
            runtime_stage="ingress"
        )
        
        # 2. Bind to async context
        token = set_log_context(ctx)
        
        # Also attach to request state for downstream convenience
        request.state.correlation_id = correlation_id
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        logger.event(RuntimeEvents.REQUEST_STARTED)

        try:
            # 3. Process request
            response = await call_next(request)
            
            # Update context with response info
            duration_ms = (time.perf_counter() - start_time) * 1000
            ctx.status = str(response.status_code)
            ctx.latency_ms = duration_ms
            
            logger.event(RuntimeEvents.REQUEST_COMPLETED)
            
            # Add correlation header to response
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            # Handle failure
            duration_ms = (time.perf_counter() - start_time) * 1000
            ctx.status = "500"
            ctx.latency_ms = duration_ms
            ctx.error_type = exc.__class__.__name__
            
            logger.exception(RuntimeEvents.REQUEST_FAILED)
            raise

        finally:
            # 4. Cleanup
            clear_log_context()
