"""
Performance and metrics engine.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import resource
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:  # optional dependency
    psutil = None  # type: ignore


class PerformanceEngine:
    def __init__(self) -> None:
        self.metrics: Dict[str, any] = {
            "memory_mb": 0.0,
            "cpu_pct": 0.0,
            "inference_times": [],  # type: List[float]
            "model_load_times": [],  # type: List[float]
            "queue_depth": 0,
        }
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self._task:
            self._task = asyncio.create_task(self._monitor())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _monitor(self) -> None:
        while True:
            try:
                self.metrics["memory_mb"] = self._get_memory_mb()
                self.metrics["cpu_pct"] = self._get_cpu_pct()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Perf monitor error: %s", exc)
                await asyncio.sleep(5)

    def _get_memory_mb(self) -> float:
        if psutil:
            return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return usage / 1024

    def _get_cpu_pct(self) -> float:
        if psutil:
            return psutil.Process(os.getpid()).cpu_percent()
        return 0.0

    async def record_inference_ms(self, duration_ms: float) -> None:
        self.metrics["inference_times"].append(duration_ms)
        self.metrics["inference_times"] = self.metrics["inference_times"][-200:]

    async def record_load_ms(self, duration_ms: float) -> None:
        self.metrics["model_load_times"].append(duration_ms)
        self.metrics["model_load_times"] = self.metrics["model_load_times"][-50:]

    def set_queue_depth(self, depth: int) -> None:
        self.metrics["queue_depth"] = depth

    async def snapshot(self) -> Dict[str, any]:
        return dict(self.metrics)
