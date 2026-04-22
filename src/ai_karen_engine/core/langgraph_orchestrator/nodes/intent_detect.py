import logging
from typing import List, Dict, Any
from ..contracts.orchestration_state import LangGraphOrchestrationState
from ..decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class IntentDetectNode:
    """Intent detection and classification"""

    def __init__(self, decision_engine=None):
        self._decision_engine = decision_engine or DecisionEngine()

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Intent detection and classification"""
        logger.info("Intent detection processing")

        try:
            messages = state.get("messages", [])
            if not messages:
                state["detected_intent"] = "unknown"
                state["intent_confidence"] = 0.0
                state["intent_analysis"] = {"reason": "no_messages"}
                return state

            prompt = (
                messages[-1].content
                if hasattr(messages[-1], "content")
                else str(messages[-1])
            )
            context = state.get("memory_context") or {}

            analysis = await self._decision_engine.analyze_intent(prompt, context)
            state["intent_analysis"] = analysis
            state["detected_intent"] = analysis.get(
                "primary_intent", analysis.get("intent", "unknown")
            )
            state["intent_confidence"] = analysis.get("confidence", 0.0)
            reasoning_metadata = (
                analysis.get("metadata", {}) if isinstance(analysis, dict) else {}
            )
            if reasoning_metadata:
                state.setdefault("warnings", []).extend(
                    [
                        warning
                        for warning in [
                            f"Reasoning identified knowledge gaps: {', '.join(reasoning_metadata.get('knowledge_gaps', [])[:3])}"
                            if reasoning_metadata.get("knowledge_gaps")
                            else None
                        ]
                        if warning
                    ]
                )

            suggested_tools = analysis.get("suggested_tools", []) or []
            entities = analysis.get("entities", []) or []
            tool_calls: List[Dict[str, Any]] = []

            for tool_name in suggested_tools:
                parameters: Dict[str, Any] = {}
                for entity in entities:
                    entity_type = (entity.get("type") or "").lower()
                    value = entity.get("value")
                    if not value:
                        continue
                    if entity_type == "location":
                        parameters.setdefault("location", value)
                    elif entity_type == "book":
                        parameters.setdefault("book_title", value)
                    elif entity_type == "time":
                        parameters.setdefault("time_reference", value)

                tool_calls.append({"tool": tool_name, "parameters": parameters})

            state["tool_calls"] = tool_calls or None

            if analysis.get("requires_clarification"):
                state.setdefault("warnings", []).append(
                    "Intent engine suggests clarifying user request"
                )

        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            state.setdefault("errors", []).append(f"Intent detection error: {str(e)}")

        return state


async def intent_detect_node(
    state: LangGraphOrchestrationState,
    decision_engine=None,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for IntentDetectNode"""
    node = IntentDetectNode(decision_engine)
    return await node(state)
