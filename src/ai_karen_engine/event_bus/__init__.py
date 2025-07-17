"""Simple in-memory and Redis-backed event bus."""

from __future__ import annotations

import collections
import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, List, Optional


@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float


class EventBus:
    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()

    def publish(self, capsule: str, event_type: str, payload: Dict[str, Any], risk: float = 0.0) -> str:
        eid = str(uuid.uuid4())
        self._queue.append(Event(eid, capsule, event_type, payload, risk))
        return eid

    def consume(self) -> List[Event]:
        events = list(self._queue)
        self._queue.clear()
        return events


try:  # pragma: no cover - optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dep
    redis = None


class RedisEventBus(EventBus):
    """Redis-backed event bus using simple list semantics."""

    def __init__(self, url: str, key: str = "kari:events", redis_client: Optional["redis.Redis"] = None) -> None:
        if redis_client is not None:
            self.redis = redis_client
        else:
            if redis is None:
                raise ImportError("redis package is required for RedisEventBus")
            self.redis = redis.from_url(url)
        self.key = key

    def publish(self, capsule: str, event_type: str, payload: Dict[str, Any], risk: float = 0.0) -> str:  # type: ignore[override]
        eid = str(uuid.uuid4())
        event = Event(eid, capsule, event_type, payload, risk)
        self.redis.rpush(self.key, json.dumps(asdict(event)))
        return eid

    def consume(self) -> List[Event]:  # type: ignore[override]
        raw = self.redis.lrange(self.key, 0, -1)
        self.redis.delete(self.key)
        events: List[Event] = []
        for item in raw:
            if isinstance(item, bytes):
                item = item.decode()
            data = json.loads(item)
            events.append(Event(**data))
        return events


_global_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url and redis is not None:
            try:
                _global_bus = RedisEventBus(redis_url)
            except Exception:  # pragma: no cover - fallback on error
                _global_bus = EventBus()
        else:
            _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
