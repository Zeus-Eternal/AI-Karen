"""Utility helpers."""

import secrets
import time
from typing import Optional
import time
import threading


def make_request_id() -> str:
    return secrets.token_hex(8)


class Stopwatch:
    def __init__(self) -> None:
        self.start = time.perf_counter()

    def ms(self) -> float:
        return (time.perf_counter() - self.start) * 1000.0


def mask_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return token
    if len(token) <= 6:
        return "***"
    return token[:3] + "***" + token[-3:]


class RateLimiter:
    """Simple fixed window rate limiter."""

    def __init__(self, limit: int, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._window_start = int(time.time())
        self._count = 0

    def allow(self) -> bool:
        now = int(time.time())
        with self._lock:
            if now - self._window_start >= self.window_seconds:
                self._window_start = now
                self._count = 0
            if self._count >= self.limit:
                return False
            self._count += 1
            return True
