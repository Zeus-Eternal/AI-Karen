from __future__ import annotations

import pathlib

from ai_karen_engine.self_refactor import SREScheduler, SelfRefactorEngine

class DummyEngine(SelfRefactorEngine):
    def __init__(self):
        # bypass parent __init__
        self.auto_merge = False

    def static_analysis(self):
        return ["issue"]

    def propose_patches(self, issues):
        return {}

    def test_patches(self, patches):
        return {}

    def reinforce(self, report):
        return pathlib.Path("queued")


def test_default_interval(monkeypatch):
    monkeypatch.delenv("SRE_INTERVAL", raising=False)
    sched = SREScheduler(DummyEngine())
    assert sched.interval == 7 * 24 * 3600


def test_interval_override(monkeypatch):
    monkeypatch.setenv("SRE_INTERVAL", "42")
    sched = SREScheduler(DummyEngine())
    assert sched.interval == 42.0
    sched.set_interval(10)
    assert sched.interval == 10


def test_queue_append(monkeypatch):
    sched = SREScheduler(DummyEngine())
    sched.start = lambda: None
    sched._running = True
    sched._loop()
    assert sched.review_queue == [pathlib.Path("queued")]
