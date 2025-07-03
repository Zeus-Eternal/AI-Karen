"""Simple timer-based scheduler for SelfRefactorEngine."""

from __future__ import annotations

import os
import threading
from typing import Optional

from src.self_refactor.engine import SelfRefactorEngine


class SREScheduler:
    """Run the self-refactor loop at a configurable interval."""

    DEFAULT_INTERVAL = 7 * 24 * 3600

    def __init__(
        self, engine: SelfRefactorEngine, interval: float | None = None
    ) -> None:
        env_val = os.getenv("SRE_INTERVAL")
        self.engine = engine
        self.interval = interval or (
            float(env_val) if env_val else self.DEFAULT_INTERVAL
        )
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

    def set_interval(self, interval: float) -> None:
        """Update the run interval. Restart the timer if running."""
        self.interval = interval
        if self._running:
            self.stop()
            self.start()

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
        self._running = False
