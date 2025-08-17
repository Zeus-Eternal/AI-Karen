from typing import Awaitable, List


class AutomationManager:
    """Simple scheduler for asynchronous automation tasks."""

    def __init__(self) -> None:
        self.queue: List[Awaitable] = []

    def add_task(self, coro: Awaitable) -> None:
        """Add a coroutine to the queue."""
        self.queue.append(coro)

    async def run_all(self) -> list:
        """Run all queued tasks sequentially and return their results."""
        results = []
        for task in self.queue:
            results.append(await task)
        self.queue.clear()
        return results

