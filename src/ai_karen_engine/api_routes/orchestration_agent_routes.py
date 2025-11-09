"""
API Routes for OrchestrationAgent returning strict JSON envelopes.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.services.orchestration_agent import (
    OrchestrationAgent,
    OrchestrationInput,
    get_orchestration_agent,
)

router = APIRouter(tags=["orchestration-agent"])
logger = logging.getLogger(__name__)


class OrchestrationRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    llm_preferences: Optional[Dict[str, str]] = Field(None, description="{preferred_llm_provider, preferred_model}")
    context: Optional[Dict[str, Any]] = None


def get_agent() -> OrchestrationAgent:
    return get_orchestration_agent()


@router.post("/orchestration-agent/respond")
async def orchestrate_respond(
    request: OrchestrationRequest,
    agent: OrchestrationAgent = Depends(get_agent),
):
    """Return a strict JSON response envelope for the provided message."""
    started = datetime.utcnow()
    try:
        inp = OrchestrationInput(
            message=request.message,
            conversation_history=request.conversation_history,
            session_id=request.session_id,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            llm_preferences=request.llm_preferences,
            context=request.context,
        )
        envelope = await agent.orchestrate_response(inp)

        # Ensure strict envelope shape
        if not isinstance(envelope, dict) or not {"final", "meta", "suggestions", "alerts"}.issubset(envelope.keys()):
            raise RuntimeError("OrchestrationAgent returned malformed envelope")

        # Add timing annotation while preserving strict envelope (meta only)
        envelope["meta"].setdefault("processing_time_ms", int((datetime.utcnow() - started).total_seconds() * 1000))
        return envelope

    except Exception as e:
        logger.exception("OrchestrationAgent failure: %s", e)
        # Return a strict envelope error with degraded annotation to satisfy Req 11
        return {
            "final": "I’m sorry, I ran into an issue processing that. You can retry, switch provider, or ask for a shorter reply.",
            "meta": {
                "annotations": ["Degraded Mode"],
                "confidence": 0.2,
                "error": str(e),
                "processing_time_ms": int((datetime.utcnow() - started).total_seconds() * 1000),
            },
            "suggestions": [
                "Retry now",
                "Try a different provider",
                "Reduce scope or tokens",
            ],
            "alerts": [],
        }

