"""Dispatch incoming prompts to plugins."""

 

from __future__ import annotations

 
import asyncio
from typing import Any, Dict

from ..intent_engine import IntentEngine
from ..plugin_router import PluginRouter, AccessDenied
from ..reasoning.ice_integration import KariICEWrapper


class CortexDispatcher:
    """Connect IntentEngine to plugins."""

    def __init__(self) -> None:
        self.engine = IntentEngine()
        self.router = PluginRouter()
        self.ice = KariICEWrapper()

    async def dispatch(self, text: str, role: str = "user") -> Dict[str, Any]:
        """Route text to the appropriate plugin based on intent and role."""
 
        intent, conf, _category = self.engine.detect_intent(text)

        intent, conf, _ = self.engine.detect_intent(text)
 
        if intent == "deep_reasoning":
            result = self.ice.process(text)
            return {"intent": intent, "confidence": conf, "response": result}

        try:
            result = await self.router.dispatch(intent, {}, roles=[role])
        except AccessDenied:
            return {"error": "forbidden", "intent": intent, "confidence": conf}
        if result is None:
            return {"response": "No plugin for intent"}
        return {"intent": intent, "confidence": conf, "response": result}
