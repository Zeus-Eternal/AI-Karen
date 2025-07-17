"""Simple in-memory event bus simulating Redis Streams."""

from __future__ import annotations

import collections
import uuid
from dataclasses import dataclass
from typing import Any, Deque, Dict, List


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


_global_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return a module-level :class:`EventBus` singleton."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


__all__ = ["Event", "EventBus", "get_event_bus"]
