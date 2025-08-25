from __future__ import annotations

"""Simple circuit breaker implementation for graceful degradation."""

import time
from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    """Track failures and temporarily block calls when threshold exceeded."""

    failure_threshold: int = 3
    recovery_time: float = 30.0  # seconds

    _failures: int = 0
    _opened_until: float = 0.0

    def allow(self) -> bool:
        """Return True if calls are allowed."""
        if time.time() < self._opened_until:
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_until = 0.0

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_until = time.time() + self.recovery_time

    @property
    def state(self) -> str:
        return "open" if not self.allow() else "closed"
