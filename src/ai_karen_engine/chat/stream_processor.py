import asyncio
import contextlib
from typing import Optional


class StreamProcessor:
    """Process chat streams with a heartbeat to monitor liveness."""

    def __init__(self, heartbeat_interval: float = 30.0) -> None:
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the heartbeat loop."""
        # Schedule the heartbeat loop as a background task. Using
        # ``asyncio.create_task`` ensures the coroutine is properly
        # registered with the event loop and prevents ``coroutine was
        # never awaited`` warnings when the processor shuts down.
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def shutdown(self) -> None:
        """Cancel and await the heartbeat task."""
        if self._heartbeat_task is None:
            return
        self._heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._heartbeat_task
        self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:  # pragma: no cover - loop
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            pass
