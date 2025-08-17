"""Storage backends for the rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis_asyncio  # type: ignore
except Exception:  # pragma: no cover
    redis_asyncio = None  # type: ignore


def build_limit_key(identifier: str, event_type: str, ip: str | None = None) -> str:
    """Construct a standardized rate-limit key.

    Args:
        identifier: Base identifier, typically `user:<email>` or `ip`.
        event_type: The type of event being limited (e.g., ``login_attempt``).
        ip: Optional IP address to scope the identifier.

    Returns:
        A namespaced key suitable for storing rate limit data.
    """

    suffix = f":{ip}" if ip else ""
    return f"rl:{event_type}:{identifier}{suffix}"


class RateLimitStore:
    """Abstract rate limit storage backend."""

    async def add_attempt(self, identifier: str, timestamp: float, window_seconds: int) -> None:
        raise NotImplementedError

    async def get_recent_attempts(self, identifier: str, cutoff: float) -> List[float]:
        raise NotImplementedError

    async def set_lockout(self, identifier: str, until: float) -> None:
        raise NotImplementedError

    async def get_lockout(self, identifier: str) -> Optional[float]:
        raise NotImplementedError

    async def clear(self, identifier: str) -> None:
        raise NotImplementedError

    async def cleanup(self, current_time: float, cutoff: float) -> None:
        raise NotImplementedError

    def stats(self, current_time: float) -> Dict[str, Any]:
        raise NotImplementedError


class InMemoryRateLimitStore(RateLimitStore):
    """Simple in-memory store for development and testing."""

    def __init__(self) -> None:
        self._attempts: Dict[str, List[float]] = defaultdict(list)
        self._lockouts: Dict[str, float] = {}

    async def add_attempt(self, identifier: str, timestamp: float, window_seconds: int) -> None:
        self._attempts[identifier].append(timestamp)

    async def get_recent_attempts(self, identifier: str, cutoff: float) -> List[float]:
        return [ts for ts in self._attempts.get(identifier, []) if ts > cutoff]

    async def set_lockout(self, identifier: str, until: float) -> None:
        self._lockouts[identifier] = until

    async def get_lockout(self, identifier: str) -> Optional[float]:
        return self._lockouts.get(identifier)

    async def clear(self, identifier: str) -> None:
        self._attempts.pop(identifier, None)
        self._lockouts.pop(identifier, None)

    async def cleanup(self, current_time: float, cutoff: float) -> None:
        for ident in list(self._attempts.keys()):
            self._attempts[ident] = [ts for ts in self._attempts[ident] if ts > cutoff]
            if not self._attempts[ident]:
                del self._attempts[ident]
        for ident in list(self._lockouts.keys()):
            if self._lockouts[ident] < current_time:
                del self._lockouts[ident]

    def stats(self, current_time: float) -> Dict[str, Any]:
        active_lockouts = sum(1 for t in self._lockouts.values() if t > current_time)
        return {
            "total_identifiers_tracked": len(self._attempts),
            "active_lockouts": active_lockouts,
            "total_lockouts": len(self._lockouts),
        }


class RedisRateLimitStore(RateLimitStore):
    """Redis-backed rate limit store for distributed environments."""

    def __init__(self, client: "redis_asyncio.Redis") -> None:  # pragma: no cover - runtime check
        if redis_asyncio is None:
            raise RuntimeError("redis module is required for RedisRateLimitStore")
        self.client = client

    @staticmethod
    def _attempts_key(identifier: str) -> str:
        return f"rl:attempts:{identifier}"

    @staticmethod
    def _lockout_key(identifier: str) -> str:
        return f"rl:lockout:{identifier}"

    async def add_attempt(self, identifier: str, timestamp: float, window_seconds: int) -> None:
        key = self._attempts_key(identifier)
        # Use timestamp as both member and score
        await self.client.zadd(key, {str(timestamp): timestamp})
        await self.client.expire(key, int(window_seconds * 2))

    async def get_recent_attempts(self, identifier: str, cutoff: float) -> List[float]:
        key = self._attempts_key(identifier)
        await self.client.zremrangebyscore(key, "-inf", cutoff)
        data = await self.client.zrange(key, 0, -1, withscores=True)
        return [float(score) for _, score in data]

    async def set_lockout(self, identifier: str, until: float) -> None:
        key = self._lockout_key(identifier)
        ttl = max(1, int(until - time.time()))
        await self.client.set(key, until, ex=ttl)

    async def get_lockout(self, identifier: str) -> Optional[float]:
        key = self._lockout_key(identifier)
        value = await self.client.get(key)
        return float(value) if value is not None else None

    async def clear(self, identifier: str) -> None:
        await self.client.delete(self._attempts_key(identifier), self._lockout_key(identifier))

    async def cleanup(self, current_time: float, cutoff: float) -> None:
        # Redis handles expiration; nothing needed
        return None

    def stats(self, current_time: float) -> Dict[str, Any]:
        # Collecting stats from Redis synchronously isn't straightforward;
        # return basic placeholders to satisfy interface.
        return {
            "total_identifiers_tracked": 0,
            "active_lockouts": 0,
            "total_lockouts": 0,
        }
