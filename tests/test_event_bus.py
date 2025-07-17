import importlib
import types

import ai_karen_engine.event_bus as eb

class FakeRedis:
    def __init__(self):
        self.values = []
    def rpush(self, key, val):
        self.values.append(val)
    def lrange(self, key, start, end):
        if end == -1:
            end = len(self.values) - 1
        return self.values[start:end+1]
    def delete(self, key):
        self.values.clear()


def test_in_memory_event_bus(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    eb._global_bus = None
    importlib.reload(eb)
    bus = eb.get_event_bus()
    eid = bus.publish("caps", "test", {"a": 1})
    events = bus.consume()
    assert events and events[0].id == eid
    assert eb._global_bus is bus
    eb._global_bus = None


def test_redis_event_bus(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost/0")
    fake = FakeRedis()
    importlib.reload(eb)
    eb._global_bus = None
    fake_mod = types.SimpleNamespace(from_url=lambda url: fake)
    monkeypatch.setattr(eb, "redis", fake_mod)
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.RedisEventBus)
    eid = bus.publish("caps", "ping", {"x": 2})
    events = bus.consume()
    assert events[0].id == eid
    assert events[0].payload == {"x": 2}
    eb._global_bus = None
