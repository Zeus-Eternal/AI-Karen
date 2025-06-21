"""Simple timer-based scheduler for SelfRefactorEngine."""

from __future__ import annotations

import threading
from typing import Optional

from .engine import SelfRefactorEngine


class SREScheduler:
    """Run the self-refactor loop at a fixed interval."""

    def __init__(self, engine: SelfRefactorEngine, interval: float = 3600.0) -> None:
        self.engine = engine
        self.interval = interval
        self._timer: Optional[threading.Timer] = None
        self._running = False

    def _loop(self) -> None:
        self._running = False
        self.start()
        issues = self.engine.static_analysis()
        if not issues:
            return
        patches = self.engine.propose_patches(issues)
        report = self.engine.test_patches(patches)
        self.engine.reinforce(report)

    def start(self) -> None:
        if not self._running:
            self._timer = threading.Timer(self.interval, self._loop)
            self._timer.daemon = True
            self._timer.start()
            self._running = True

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._running = False
