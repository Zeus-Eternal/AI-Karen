import asyncio
from ai_karen_engine.plugin_router import get_plugin_router


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
        self.router = get_plugin_router()

    def route(self, _text: str) -> PluginWrapper:
        record = self.router.get_plugin("autonomous_task_handler")
        if not record:
            raise ValueError("autonomous_task_handler plugin not found")
        return PluginWrapper(record)

    def generate_reply(self, text: str) -> str:
        plugin = self.route(text)
        result = plugin.run(text)
        return str(result)
