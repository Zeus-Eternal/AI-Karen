"""
Health monitoring for server components.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any, Dict

logger = logging.getLogger(__name__)


class HealthMonitor:
    def __init__(self) -> None:
        self.status: Dict[str, str] = {
            "server": "starting",
            "models": "unknown",
            "performance": "unknown",
            "karen_integration": "unknown",
        }
        self.last_check = None
        self._task: asyncio.Task | None = None
        self._check_interval = 30

    async def start(self) -> None:
        if not self._task:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while True:
            try:
                await self._evaluate()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Health loop error: %s", exc)
                await asyncio.sleep(self._check_interval)

    async def _evaluate(self) -> None:
        disk_ok = self._check_disk()
        self.status["server"] = "healthy" if disk_ok else "degraded"
        self.last_check = asyncio.get_running_loop().time()

    def _check_disk(self) -> bool:
        usage = shutil.disk_usage(".")
        # consider unhealthy if free < 1GB
        return usage.free > 1_000_000_000

    async def snapshot(self) -> Dict[str, Any]:
        return {
            "status": dict(self.status),
            "last_check": self.last_check,
        }

