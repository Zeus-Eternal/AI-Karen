"""Dispatch incoming prompts to plugins."""

import asyncio
from typing import Any, Dict

from ..intent_engine import IntentEngine
from ..plugin_router import PluginRouter


class CortexDispatcher:
    """Connect IntentEngine to plugins."""

    def __init__(self) -> None:
        self.engine = IntentEngine()
        self.router = PluginRouter()

    async def dispatch(self, text: str) -> Dict[str, Any]:
        intent, conf, _category = self.engine.detect_intent(text)
        handler = self.router.get_handler(intent)
        if not handler:
            return {"response": "No plugin for intent"}
        result = await handler({})
        return {"intent": intent, "confidence": conf, "response": result}
