"""Simple database-backed rate limiting middleware with fallback support."""

# mypy: ignore-errors

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

try:
    from fastapi import Request
    from fastapi.responses import JSONResponse
except Exception:  # pragma: no cover - fallback for tests
    from ai_karen_engine.fastapi_stub import Request, JSONResponse

from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.database.models import RateLimit
from ai_karen_engine.services.usage_service import UsageService

# In-memory fallback rate limiting when database is unavailable
_memory_rate_limits: Dict[str, Dict] = {}
logger = logging.getLogger(__name__)


def _get_memory_rate_limit(identifier: str) -> Dict:
    """Get or create in-memory rate limit record."""
    now = datetime.utcnow()
    
    if identifier not in _memory_rate_limits:
        _memory_rate_limits[identifier] = {
            "current_count": 0,
            "window_reset": now + timedelta(seconds=60),
            "max_count": 60,
            "window_sec": 60
        }
    
    limit = _memory_rate_limits[identifier]
    
    # Reset window if expired
    if limit["window_reset"] < now:
        limit["current_count"] = 0
        limit["window_reset"] = now + timedelta(seconds=limit["window_sec"])
    
    return limit


def _check_memory_rate_limit(identifier: str) -> bool:
    """Check if request should be rate limited using in-memory storage."""
    limit = _get_memory_rate_limit(identifier)
    
    if limit["current_count"] >= limit["max_count"]:
        return True  # Rate limited
    
    limit["current_count"] += 1
    return False  # Allow request


async def rate_limit_middleware(request: Request, call_next):
    """Enforce simple fixed-window rate limits with database fallback to memory."""
    identifier: Optional[str] = getattr(request.state, "user", None)
    if not identifier:
        identifier = request.headers.get("X-API-Key") or request.client.host

    # Try database-backed rate limiting first
    try:
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
                    try:
                        UsageService.increment("errors", user_id=identifier)
                    except Exception:
                        pass  # Don't fail if usage service is unavailable
                    return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
                
                limit.current_count += 1
                session.commit()
                
    except Exception as e:
        # Database is unavailable, fall back to in-memory rate limiting
        logger.warning(f"Database unavailable for rate limiting, using memory fallback: {e}")
        
        if _check_memory_rate_limit(identifier):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

    return await call_next(request)
