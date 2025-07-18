"""Simple in-memory and Redis-backed event bus."""

from __future__ import annotations

import collections
import json
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, List, Optional, Union

from ai_karen_engine.config import config_manager

# Optional Redis dependency
try:
    import redis  # type: ignore
except ImportError:
    redis = None


@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float


class EventBus:
    """In-memory FIFO event bus."""

    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
    ) -> str:
        eid = str(uuid.uuid4())
        self._queue.append(Event(eid, capsule, event_type, payload, risk))
        return eid

    def consume(self) -> List[Event]:
        events = list(self._queue)
        self._queue.clear()
        return events


class RedisEventBus(EventBus):
    """Redis-backed event bus (list semantics)."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        list_key: str = "kari:events",
    ) -> None:
        # Initialize Redis connection
        super().__init__()
        if redis_client:
            self.redis = redis_client
        else:
            if redis is None:
                raise ImportError("redis package is required for RedisEventBus")
            # default to URL from env or standard localhost
            url = config_manager.get_config_value("redis", "url", default=None)
            if url:
                self.redis = redis.from_url(url)
            else:
                self.redis = redis.Redis()
        self.list_key = list_key

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
    ) -> str:
        eid = str(uuid.uuid4())
        ev = Event(eid, capsule, event_type, payload, risk)
        self.redis.rpush(self.list_key, json.dumps(asdict(ev)))
        return eid

    def consume(self) -> List[Event]:
        raw = self.redis.lrange(self.list_key, 0, -1)
        if raw:
            self.redis.delete(self.list_key)
        events: List[Event] = []
        for item in raw:
            if isinstance(item, bytes):
                item = item.decode()
            data = json.loads(item)
            events.append(Event(**data))
        return events


# Singleton accessor
_global_bus: Union[EventBus, RedisEventBus, None] = None


def get_event_bus() -> Union[EventBus, RedisEventBus]:
    """Return a singleton EventBus, switching to Redis if configured."""
    global _global_bus
    if _global_bus is not None:
        return _global_bus

    backend = config_manager.get_config_value("event_bus", "backend", default="memory")
    if backend.lower() == "redis" and redis is not None:
        try:
            _global_bus = RedisEventBus()
        except Exception:
            _global_bus = EventBus()
    else:
        _global_bus = EventBus()

    return _global_bus


__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
