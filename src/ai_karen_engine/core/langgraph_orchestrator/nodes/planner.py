import logging
from typing import Dict, Any, Optional, List
from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


def _compose_execution_plan(
    intent: str,
    analysis: Optional[Dict[str, Any]],
    tool_calls: List[Dict[str, Any]],
    safety_status: str,
) -> Dict[str, Any]:
    """Create a structured execution plan used by planner and dry-run analysis."""

    analysis = analysis or {}
    execution_plan: Dict[str, Any] = {
        "intent": intent,
        "steps": [],
        "tools_required": [call["tool"] for call in tool_calls],
        "estimated_time_seconds": 2,
        "complexity": "low",
        "metadata": {
            "confidence": analysis.get("confidence", 0.0),
            "requires_clarification": analysis.get("requires_clarification", False),
            "safety_status": safety_status,
        },
    }

    if intent in {"code_generation", "email_compose"}:
        execution_plan["steps"] = [
            "understand_requirements",
            "draft_solution",
            "review_and_refine",
        ]
        execution_plan["complexity"] = "medium"
        execution_plan["estimated_time_seconds"] = 6
    elif intent in {
        "time_query",
        "information_retrieval",
        "book_query",
    }:
        execution_plan["steps"] = [
            "gather_context",
            "invoke_tools" if tool_calls else "search_internal_memory",
            "synthesize_answer",
        ]
        execution_plan["complexity"] = "low"
        execution_plan["estimated_time_seconds"] = 4
    else:
        execution_plan["steps"] = ["analyze_prompt", "compose_response"]

    if safety_status == "review_required":
        execution_plan["requires_human_review"] = True

    return execution_plan


class PlannerNode:
    """Execution planning based on intent"""

    def __init__(self):
        pass

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Execution planning based on intent"""
        logger.info("Planning processing")

        try:
            intent = state.get("detected_intent", "general_chat") or "general_chat"
            analysis = state.get("intent_analysis") or {}
            tool_calls = state.get("tool_calls") or []
            safety_status = state.get("safety_status", "safe")

            execution_plan = _compose_execution_plan(
                intent,
                analysis,
                tool_calls,
                safety_status,
            )
            state["execution_plan"] = execution_plan

        except Exception as e:
            logger.error(f"Planning error: {e}")
            state.setdefault("errors", []).append(f"Planning error: {str(e)}")

        return state


async def planner_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for PlannerNode"""
    node = PlannerNode()
    return await node(state)
