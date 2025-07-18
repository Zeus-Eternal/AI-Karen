import types
import importlib
import pytest

import ai_karen_engine.event_bus as eb
from ai_karen_engine.config import config_manager

class FakeRedisClient:
    def __init__(self):
        self.storage = []

    def rpush(self, key, val):
        self.storage.append(val)

    def lrange(self, key, start, end):
        if end == -1:
            end = len(self.storage) - 1
        return self.storage[start:end+1]

    def delete(self, key):
        self.storage.clear()


def reset_bus():
    eb._global_bus = None


def test_in_memory_bus(monkeypatch):
    # force memory backend
    monkeypatch.setattr(config_manager, "get_config_value", lambda section, key, default=None: "memory")
    reset_bus()
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.EventBus)

    eid = bus.publish("caps", "test", {"a": 1})
    events = bus.consume()
    assert len(events) == 1
    assert events[0].id == eid
    assert events[0].capsule == "caps"
    assert events[0].payload == {"a": 1}


def test_redis_bus(monkeypatch):
    # force redis backend
    monkeypatch.setattr(config_manager, "get_config_value", lambda section, key, default=None: "redis")
    # stub redis module
    fake_client = FakeRedisClient()
    fake_redis_module = types.SimpleNamespace(from_url=lambda url: fake_client, Redis=lambda: fake_client)
    monkeypatch.setattr(eb, "redis", fake_redis_module)

    reset_bus()
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.RedisEventBus)

    eid = bus.publish("caps", "ping", {"x": 2})
    events = bus.consume()
    assert len(events) == 1
    assert events[0].id == eid
    assert events[0].capsule == "caps"
    assert events[0].payload == {"x": 2}


def test_redis_fallback_to_memory(monkeypatch):
    # force redis backend but remove redis dependency
    monkeypatch.setattr(config_manager, "get_config_value", lambda section, key, default=None: "redis")
    monkeypatch.setattr(eb, "redis", None)

    reset_bus()
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.EventBus)
