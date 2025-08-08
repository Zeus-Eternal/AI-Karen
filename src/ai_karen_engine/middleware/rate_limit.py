"""Simple database-backed rate limiting middleware."""

# mypy: ignore-errors

from datetime import datetime, timedelta
from typing import Optional

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - fallback for tests
    from ai_karen_engine.fastapi_stub import Request, JSONResponse

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import RateLimit
from ai_karen_engine.services.usage_service import UsageService


async def rate_limit_middleware(request: Request, call_next):
    """Enforce simple fixed-window rate limits from the database."""
    identifier: Optional[str] = getattr(request.state, "user", None)
    if not identifier:
        identifier = request.headers.get("X-API-Key") or request.client.host

    with get_db_session_context() as session:
        limit = session.query(RateLimit).filter_by(key=identifier).first()
        now = datetime.utcnow()
        if limit is None:
            # No existing limit record; allow request and create default record
            limit = RateLimit(
                key=identifier,
                limit_name="default",
                window_sec=60,
                max_count=60,
                current_count=1,
                window_reset=now + timedelta(seconds=60),
            )
            session.add(limit)
            session.commit()
        else:
            if limit.window_reset and limit.window_reset < now:
                limit.current_count = 0
                limit.window_reset = now + timedelta(seconds=limit.window_sec or 60)
            if limit.current_count >= (limit.max_count or 0):
                UsageService.increment("errors", user_id=identifier)
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
            limit.current_count += 1
            session.commit()

    return await call_next(request)
