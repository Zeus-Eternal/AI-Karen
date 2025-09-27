"""Production reasoning endpoints for the Kari API."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response
from ai_karen_engine.core.service_registry import get_service_registry, initialize_services
from ai_karen_engine.models.shared_types import FlowInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reasoning", tags=["reasoning"])


class ReasoningRequest(BaseModel):
    """Payload sent from the web UI reasoning client."""

    input: str = Field(..., min_length=1, description="User input that needs analysis")
    context: Dict[str, Any] = Field(default_factory=dict, description="Optional reasoning context")


class ReasoningResponse(BaseModel):
    """Standard response envelope returned to the frontend."""

    success: bool
    response: Dict[str, Any]
    reasoning_method: str
    fallback_used: bool
    errors: Optional[Dict[str, Any]] = None


def _normalize_response_payload(payload: Any) -> Dict[str, Any]:
    """Convert orchestrator or fallback outputs into a consistent shape."""

    if isinstance(payload, dict):
        normalized = dict(payload)
        normalized.setdefault("type", "text")
        if "content" not in normalized:
            normalized["content"] = str(payload)
        return normalized

    if hasattr(payload, "model_dump"):
        try:
            return _normalize_response_payload(payload.model_dump())
        except Exception:  # pragma: no cover - defensive
            pass

    if hasattr(payload, "dict"):
        try:
            return _normalize_response_payload(payload.dict())
        except Exception:  # pragma: no cover - defensive
            pass

    if hasattr(payload, "__dict__"):
        return _normalize_response_payload(vars(payload))

    return {"content": str(payload), "type": "text", "metadata": {"raw_type": type(payload).__name__}}


def _enhanced_simple_fallback(user_input: str) -> Dict[str, Any]:
    """Return a user friendly fallback response when everything else fails."""

    text = user_input.strip().lower()

    if any(word in text for word in ["function", "code", "python", "javascript", "programming", "algorithm"]):
        content = (
            "I can help with coding questions! You asked about: "
            f"{user_input}\n\nWhile I'm in fallback mode, here are a few tips:\n"
            "1. Break the problem into small steps.\n"
            "2. Use descriptive variable names.\n"
            "3. Add comments explaining tricky logic.\n"
            "4. Test incrementally to verify each change.\n\n"
            "Let me know what part you'd like to dive into."
        )
    elif text.endswith("?") or any(word in text for word in ["what", "how", "why", "when", "where", "help"]):
        content = (
            f"I understand you're asking: {user_input}\n\n"
            "I'm operating with limited capabilities right now, but I'm still here to help."
            " Can you share more specific details so I can provide better guidance?"
        )
    elif any(word in text for word in ["hello", "hi", "hey", "greetings"]):
        content = (
            "Hello! I'm Karen, your AI assistant. I'm currently in a reduced capability mode,"
            " but I can still help with many questions. What would you like to work on today?"
        )
    elif any(word in text for word in ["create", "make", "build", "write", "generate"]):
        content = (
            f"I'd love to help with: {user_input}\n\n"
            "I'm in fallback mode, so my responses may be more high-level."
            " Could you outline the steps or details you're looking for so we can tackle it together?"
        )
    else:
        content = (
            f"I received your message: {user_input}\n\n"
            "I'm experiencing limited functionality at the moment,"
            " but I still want to assist. Could you rephrase or provide more context?"
        )

    return {
        "content": content,
        "type": "text",
        "metadata": {
            "fallback_mode": True,
            "local_processing": True,
            "enhanced_simple_response": True,
        },
    }


async def _orchestrator_available(registry: Any) -> bool:
    """Ensure the AI orchestrator is initialized and ready."""

    try:
        services = registry.list_services()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unable to list services: %s", exc)
        services = {}

    if services.get("ai_orchestrator", {}).get("status") == "ready":
        return True

    try:
        await initialize_services()
        services = registry.list_services()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Service initialization failed: %s", exc)
        return False

    return services.get("ai_orchestrator", {}).get("status") == "ready"


@router.post("/analyze", response_model=ReasoningResponse)
async def analyze_reasoning(request: ReasoningRequest) -> ReasoningResponse:
    """Primary reasoning endpoint used by the production web UI."""

    user_input = request.input.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Input cannot be empty")

    context = request.context or {}

    try:
        registry = get_service_registry()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Service registry unavailable: %s", exc)
        fallback_payload = _normalize_response_payload(
            generate_degraded_mode_response(user_input=user_input, context=context)
        )
        return ReasoningResponse(
            success=True,
            response=fallback_payload,
            reasoning_method="local_fallback",
            fallback_used=True,
            errors={"registry_error": str(exc)},
        )

    orchestrator_ready = await _orchestrator_available(registry)

    if orchestrator_ready:
        try:
            orchestrator = await registry.get_service("ai_orchestrator")
            flow_input = FlowInput(
                prompt=user_input,
                context=context,
                user_id=context.get("user_id", "anonymous"),
                conversation_history=context.get("conversation_history", []),
                user_settings=context.get("user_settings", {}),
            )

            flow_output = await orchestrator.conversation_processing_flow(flow_input)
            payload = _normalize_response_payload(flow_output)

            return ReasoningResponse(
                success=True,
                response=payload,
                reasoning_method="ai_orchestrator",
                fallback_used=False,
            )
        except Exception as exc:
            logger.warning("AI orchestrator reasoning failed, using fallback: %s", exc)
            try:
                fallback_payload = _normalize_response_payload(
                    generate_degraded_mode_response(user_input=user_input, context=context)
                )
            except Exception as fallback_error:  # pragma: no cover - defensive
                logger.error("Degraded mode reasoning failed: %s", fallback_error)
                fallback_payload = _enhanced_simple_fallback(user_input)
                return ReasoningResponse(
                    success=True,
                    response=fallback_payload,
                    reasoning_method="enhanced_simple_fallback",
                    fallback_used=True,
                    errors={
                        "ai_error": str(exc),
                        "fallback_error": str(fallback_error),
                    },
                )

            return ReasoningResponse(
                success=True,
                response=fallback_payload,
                reasoning_method="local_fallback",
                fallback_used=True,
                errors={"ai_error": str(exc)},
            )

    # Orchestrator not available even after initialization attempts
    try:
        fallback_payload = _normalize_response_payload(
            generate_degraded_mode_response(user_input=user_input, context=context)
        )
    except Exception as fallback_error:  # pragma: no cover - defensive
        logger.error("Failed to generate degraded mode response: %s", fallback_error)
        fallback_payload = _enhanced_simple_fallback(user_input)
        return ReasoningResponse(
            success=True,
            response=fallback_payload,
            reasoning_method="enhanced_simple_fallback",
            fallback_used=True,
            errors={"fallback_error": str(fallback_error)},
        )

    return ReasoningResponse(
        success=True,
        response=fallback_payload,
        reasoning_method="local_fallback",
        fallback_used=True,
        errors={"reason": "ai_orchestrator_unavailable"},
    )

