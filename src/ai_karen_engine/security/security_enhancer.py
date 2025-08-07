"""Security enhancement utilities for authentication services.

This module defines three lightweight components used to harden the
``AuthService`` implementation:

``RateLimiter``
    Throttles authentication attempts using an in-memory fixed window.
``AuditLogger``
    Records authentication events and optionally forwards metrics to a
    user supplied hook.
``SecurityEnhancer``
    Convenience wrapper bundling the two components and providing helper
    methods for the authentication service.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Deque, Dict, List, Optional

from ai_karen_engine.core.logging import get_logger

# mypy: ignore-errors

logger = get_logger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter.

    Parameters
    ----------
    max_calls:
        Maximum number of allowed calls within ``period`` seconds.
    period:
        Time window in seconds for rate limiting.
    """

    def __init__(self, max_calls: int, period: float) -> None:
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        """Return ``True`` if another call for ``key`` is allowed."""

        now = time.monotonic()
        calls = self._calls[key]
        # Drop timestamps outside the current window
        while calls and now - calls[0] > self.period:
            calls.popleft()
        if len(calls) >= self.max_calls:
            return False
        calls.append(now)
        return True


@dataclass
class AuditEvent:
    event: str
    data: Dict[str, object]
    timestamp: datetime


class AuditLogger:
    """Capture authentication events and forward metrics."""

    def __init__(
        self,
        metrics_hook: Optional[Callable[[str, Dict[str, object]], None]] = None,
    ) -> None:
        self.metrics_hook = metrics_hook
        self.events: List[AuditEvent] = []

    def log_event(self, event: str, data: Optional[Dict[str, object]] = None) -> None:
        record = AuditEvent(event=event, data=data or {}, timestamp=datetime.utcnow())
        self.events.append(record)
        logger.info(
            "AUTH EVENT",
            event=event,
            timestamp=record.timestamp.isoformat(),
            **record.data,
        )
        if self.metrics_hook:
            self.metrics_hook(event, record.data)


class SecurityEnhancer:
    """Bundle rate limiting and audit logging helpers."""

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        audit_logger: Optional[AuditLogger] = None,
    ) -> None:
        self.rate_limiter = rate_limiter
        self.audit_logger = audit_logger

    def allow_auth_attempt(self, key: str) -> bool:
        """Check rate limit for ``key`` and log if blocked."""

        if not self.rate_limiter:
            return True
        allowed = self.rate_limiter.allow(key)
        if not allowed and self.audit_logger:
            self.audit_logger.log_event("rate_limit_exceeded", {"key": key})
        return allowed

    def log_event(self, event: str, data: Optional[Dict[str, object]] = None) -> None:
        if self.audit_logger:
            self.audit_logger.log_event(event, data)
