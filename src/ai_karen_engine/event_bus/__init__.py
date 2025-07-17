"""Simple in-memory event bus simulating Redis Streams."""

from __future__ import annotations

import collections
import json
import uuid
from dataclasses import dataclass
from typing import Any, Deque, Dict, List

from ai_karen_engine.config import config_manager

try:  # Optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dep
    redis = None


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


class RedisEventBus:
    """Redis-backed implementation using a single stream."""

    def __init__(self, redis_client: "redis.Redis | None" = None, stream: str = "kari:events") -> None:
        if redis_client is not None:
            self.redis = redis_client
        else:
            if redis is None:
                raise ImportError("redis package is required for RedisEventBus")
            self.redis = redis.Redis()
        self.stream = stream

    def publish(self, capsule: str, event_type: str, payload: Dict[str, Any], risk: float = 0.0) -> str:
        data = {
            "capsule": capsule,
            "type": event_type,
            "payload": json.dumps(payload),
            "risk": risk,
        }
        eid = self.redis.xadd(self.stream, data)
        return str(eid)

    def consume(self) -> List[Event]:
        entries = self.redis.xrange(self.stream, min="-", max="+")
        events = []
        for eid, data in entries:
            try:
                payload = json.loads(data.get("payload", "{}"))
            except Exception:
                payload = {}
            events.append(
                Event(
                    str(eid),
                    data.get("capsule", ""),
                    data.get("type", ""),
                    payload,
                    float(data.get("risk", 0.0)),
                )
            )
        if entries:
            self.redis.delete(self.stream)
        return events


_global_bus: EventBus | RedisEventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is not None:
        return _global_bus
    backend = config_manager.get_config_value("event_bus", "memory")
    if backend == "redis":
        try:
            _global_bus = RedisEventBus()
        except Exception:
            _global_bus = EventBus()
    else:
        _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
