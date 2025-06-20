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
    """Basic text router mapping keywords to plugin intents."""

    def __init__(self) -> None:
        self.router = BaseRouter()

    def route(self, text: str) -> PluginWrapper:
        text = text.lower()
        for intent, record in self.router.intent_map.items():
            if intent in text:
                return PluginWrapper(record)

        fallback = self.router.get_plugin("autonomous_task_handler")
        if not fallback:
            raise ValueError("autonomous_task_handler plugin not found")
        return PluginWrapper(fallback)
