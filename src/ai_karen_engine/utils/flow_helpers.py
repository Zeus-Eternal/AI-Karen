"""Utility helpers for building flow inputs and formatting flow responses.

These functions encapsulate common patterns used by the API routes
when interacting with the :class:`AIOrchestrator`.  They centralize the
construction of :class:`FlowInput` objects and the formatting of
:class:`FlowOutput` results into response payloads.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import (
    FlowInput,
    FlowOutput,
)


def build_flow_input(
    *,
    prompt: str,
    conversation_history: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    session_id: Optional[str],
    user_id: str = "anonymous",
) -> FlowInput:
    """Create a :class:`FlowInput` instance from request data."""
    return FlowInput(
        {
            "prompt": prompt,
            "conversation_history": conversation_history,
            "user_settings": user_settings,
            "context": context,
            "user_id": user_id,
            "session_id": session_id,
        }
    )


def format_flow_response(result: FlowOutput | Dict[str, Any], processing_time_ms: int) -> Dict[str, Any]:
    """Convert a :class:`FlowOutput` or dict into a serializable response payload."""
    # Extract data from result - handle both FlowOutput objects and plain dicts
    if hasattr(result, "data"):
        # FlowOutput object with .data attribute
        data = result.data
    else:
        # Plain dict - use it directly
        data = result

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
