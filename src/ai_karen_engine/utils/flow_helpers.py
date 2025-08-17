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
        prompt=prompt,
        conversation_history=conversation_history,
        user_settings=user_settings,
        context=context,
        user_id=user_id,
        session_id=session_id,
    )


def format_flow_response(result: FlowOutput, processing_time_ms: int) -> Dict[str, Any]:
    """Convert a :class:`FlowOutput` into a serializable response payload."""
    return {
        "response": result.response,
        "requires_plugin": result.requires_plugin,
        "plugin_to_execute": result.plugin_to_execute,
        "plugin_parameters": result.plugin_parameters,
        "memory_to_store": result.memory_to_store,
        "suggested_actions": result.suggested_actions,
        "ai_data": result.ai_data.model_dump() if result.ai_data else None,
        "proactive_suggestion": result.proactive_suggestion,
        "processing_time_ms": processing_time_ms,
        "model_used": getattr(result.ai_data, "model_used", None) if result.ai_data else None,
        "confidence_score": result.ai_data.confidence if result.ai_data else None,
    }


__all__ = ["build_flow_input", "format_flow_response"]
