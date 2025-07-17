import types

import ai_karen_engine.event_bus as eb


class FakeRedisClient:
    def __init__(self):
        self.stream = []

    def xadd(self, stream, data):
        eid = f"{len(self.stream)+1}-0"
        self.stream.append((eid, data))
        return eid

    def xrange(self, stream, min='-', max='+'):
        return list(self.stream)

    def delete(self, stream):
        self.stream = []


def reset(bus_module):
    bus_module._global_bus = None


def test_memory_bus(monkeypatch):
    monkeypatch.setattr(eb.config_manager, "get_config_value", lambda k, default=None: "memory")
    reset(eb)
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.EventBus)
    eid = bus.publish("caps", "ping", {"a": 1})
    events = bus.consume()
    assert events and events[0].id == eid


def test_redis_bus(monkeypatch):
    monkeypatch.setattr(eb.config_manager, "get_config_value", lambda k, default=None: "redis")
    fake_mod = types.SimpleNamespace(Redis=lambda: FakeRedisClient())
    monkeypatch.setattr(eb, "redis", fake_mod)
    reset(eb)
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.RedisEventBus)
    bus.publish("c", "t", {"x": 2})
    events = bus.consume()
    assert events and events[0].capsule == "c"


def test_redis_fallback(monkeypatch):
    monkeypatch.setattr(eb.config_manager, "get_config_value", lambda k, default=None: "redis")
    monkeypatch.setattr(eb, "redis", None)
    reset(eb)
    bus = eb.get_event_bus()
    assert isinstance(bus, eb.EventBus)
