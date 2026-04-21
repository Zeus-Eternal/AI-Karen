import logging
from dataclasses import asdict
from typing import Optional

from ai_karen_engine.memory.distilbert_service import DistilBertService, SafetyResult
from ai_karen_engine.memory.profile_manager import Guardrails
from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)

def _ensure_safety_service(self) -> DistilBertService:
    """Lazy instantiate the safety service."""

    if getattr(self, "_safety_service", None) is None:
        self._safety_service = DistilBertService()
    return self._safety_service

async def safety_gate_node(self, state: LangGraphOrchestrationState) -> LangGraphOrchestrationState:
    """Safety and guardrails gate"""
    logger.info("Safety gate processing")

    try:
        errors = state.setdefault("errors", [])
        warnings = state.setdefault("warnings", [])
        messages = state.get("messages", [])

        if not messages:
            state["safety_status"] = "safe"
            state["safety_evaluation"] = {"reason": "no_messages"}
            return state

        last_message = (
            messages[-1].content
            if hasattr(messages[-1], "content")
            else str(messages[-1])
        )

        profile = self._profile_manager.get_active_profile()
        guardrails: Optional[Guardrails] = getattr(profile, "guardrails", None)

        if guardrails and not guardrails.content_filtering:
            state["safety_status"] = "safe"
            state["safety_evaluation"] = {"reason": "guardrails_disabled"}
            return state

        safety_service = _ensure_safety_service(self)
        evaluation: SafetyResult = await safety_service.filter_safety(last_message)
        state["safety_evaluation"] = asdict(evaluation)

        if not evaluation.is_safe and evaluation.flagged_categories:
            state["safety_status"] = "review_required"
            state["safety_flags"] = evaluation.flagged_categories
            state["requires_approval"] = True
            warnings.append(
                "Safety service flagged content for review: "
                + ", ".join(evaluation.flagged_categories)
            )
        elif evaluation.is_safe:
            state["safety_status"] = "safe"
            state["safety_flags"] = []
        else:
            state["safety_status"] = "unsafe"
            errors.append("Content failed safety evaluation")

    except Exception as e:
        logger.error(f"Safety gate error: {e}")
        state["safety_status"] = "unsafe"
        state.setdefault("errors", []).append(f"Safety check error: {str(e)}")

    return state
