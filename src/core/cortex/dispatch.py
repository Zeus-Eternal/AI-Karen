"""Dispatch incoming prompts to plugins."""

 

from __future__ import annotations

 
import asyncio
from typing import Any, Dict

from ai_karen_engine.core.intent_engine import IntentEngine
from ai_karen_engine.plugin_router import get_plugin_router, AccessDenied
from ai_karen_engine.core.reasoning.ice_integration import KariICEWrapper


class CortexDispatcher:
    """Connect IntentEngine to plugins."""

    def __init__(self) -> None:
        self.engine = IntentEngine()
        self.router = get_plugin_router()
        self.ice = KariICEWrapper()

    async def dispatch(self, text: str, role: str = "user") -> Dict[str, Any]:
        """Route text to the appropriate plugin based on intent and role."""
 
        intent, conf, _ = self.engine.detect_intent(text)
 
        if intent == "deep_reasoning":
            result = self.ice.process(text)
            return {"intent": intent, "confidence": conf, "response": result}

        try:
            result = await self.router.dispatch(intent, {"prompt": text}, roles=[role])
        except AccessDenied:
            return {"error": "forbidden", "intent": intent, "confidence": conf}
        if result is None:
            fallback = await self.router.dispatch("hf_generate", {"prompt": text}, roles=[role])
            if fallback is not None:
                return {"intent": "hf_generate", "confidence": conf, "response": fallback}
            return {
                "intent": "unknown",
                "confidence": conf,
                "response": "unknown intent",
            }
        return {"intent": intent, "confidence": conf, "response": result}
