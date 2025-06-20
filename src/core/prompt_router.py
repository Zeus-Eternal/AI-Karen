import asyncio
from core.plugin_router import PluginRouter as BaseRouter


class PluginWrapper:
    def __init__(self, record):
        self.manifest = record.manifest
        self._handler = record.handler

    def run(self, subtask: str):
        """Execute the underlying plugin handler synchronously."""
        return asyncio.run(self._handler({"subtask": subtask}))


class PromptRouter:
    """Very small router that always returns the autonomous_task_handler plugin."""

    def __init__(self) -> None:
        self.router = BaseRouter()

    def route(self, _text: str) -> PluginWrapper:
        record = self.router.get_plugin("autonomous_task_handler")
        if not record:
            raise ValueError("autonomous_task_handler plugin not found")
        return PluginWrapper(record)
