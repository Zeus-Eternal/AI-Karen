"""Decision engine compatibility module."""

from __future__ import annotations

from typing import Any, Dict, List


class DecisionEngine:
    """Lightweight decision engine used by compatibility paths and tests."""

    def __init__(self) -> None:
        self._decision_rules: List[Dict[str, Any]] = []
        self._tool_registry: Dict[str, Dict[str, Any]] = {
            "get_current_date": {},
            "get_current_time": {},
            "get_weather": {},
        }

    def get_available_tools(self) -> List[str]:
        return list(self._tool_registry.keys())

    async def analyze_intent(self, prompt: str, _context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        text = (prompt or "").lower()
        if "weather" in text:
            primary_intent = "weather_query"
            confidence = 0.8
            tools = ["get_weather"]
            entities = [{"type": "location", "value": prompt.split("in", 1)[-1].strip()}] if " in " in prompt.lower() else []
        elif "time" in text:
            primary_intent = "time_query"
            confidence = 0.8
            tools = ["get_current_time"]
            entities = []
        elif "date" in text:
            primary_intent = "date_query"
            confidence = 0.8
            tools = ["get_current_date"]
            entities = []
        else:
            primary_intent = "conversation"
            confidence = 0.6
            tools = []
            entities = []
        return {
            "primary_intent": primary_intent,
            "confidence": confidence,
            "suggested_tools": tools,
            "entities": entities,
        }


__all__ = ["DecisionEngine"]

