"""Utility helpers for building flow inputs and formatting flow responses.

These functions encapsulate common patterns used by the API routes
when interacting with the orchestration runtime. They centralize the
construction of flow payloads and the formatting of flow results into
response payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

def build_flow_input(
    *,
    prompt: str,
    conversation_history: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    session_id: Optional[str],
    user_id: str = "anonymous",
) -> Dict[str, Any]:
    """Create a flow payload from request data."""
    return {
        "prompt": prompt,
        "conversation_history": conversation_history,
        "user_settings": user_settings,
        "context": context,
        "user_id": user_id,
        "session_id": session_id,
    }


def format_flow_response(result: Any, processing_time_ms: int) -> Dict[str, Any]:
    """Convert a flow result into a serializable response payload."""
    if isinstance(result, dict):
        data = result
    else:
        data = getattr(result, "data", result)
        if not isinstance(data, dict):
            data = {}

    return {
        "response": data.get("response", ""),
        "requires_plugin": data.get("requires_plugin", False),
        "plugin_to_execute": data.get("plugin_to_execute"),
        "plugin_parameters": data.get("plugin_parameters"),
        "memory_to_store": data.get("memory_to_store"),
        "suggested_actions": data.get("suggested_actions"),
        "ai_data": data.get("ai_data"),
        "proactive_suggestion": data.get("proactive_suggestion"),
        "processing_time_ms": processing_time_ms,
        "model_used": None,
        "confidence_score": None,
    }


__all__ = ["build_flow_input", "format_flow_response"]
