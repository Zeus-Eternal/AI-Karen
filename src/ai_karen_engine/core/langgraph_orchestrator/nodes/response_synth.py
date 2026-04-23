"""Response synthesis node for LangGraph orchestration."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..contracts.orchestration_state import LangGraphOrchestrationState

logger = logging.getLogger(__name__)


@dataclass
class SynthesisConfig:
    """Configuration for response synthesis."""

    max_response_length: int = 100000
    include_tool_results: bool = True
    include_execution_summary: bool = True
    apply_safety_filter: bool = True


class ResponseSynthesisNode:
    """Deterministic response synthesis over orchestration state."""

    def __init__(self, config: Optional[SynthesisConfig] = None):
        self.config = config or SynthesisConfig()

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        logger.info("Response synthesis processing")
        try:
            state = await self.synthesize_response(state)
            logger.info("Response synthesis completed")
        except Exception as e:
            logger.error("Response synthesis error: %s", e)
            state.setdefault("errors", []).append(f"Response synthesis error: {e}")
        return state

    async def synthesize_response(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        logger.info("Response synthesis processing")
        try:
            response = self._compose_response(state)
            state["llm_response"] = response
            state["synthesis_metadata"] = {
                "response_length": len(response),
                "tool_results_count": len(state.get("tool_results") or []),
                "selected_provider": state.get("selected_provider"),
                "selected_model": state.get("selected_model"),
                "has_reasoning_result": bool(state.get("reasoning_result")),
            }
            state["response_summary"] = {
                "response_length": len(response),
                "included_tool_results": len(state.get("tool_results") or [])
                if self.config.include_tool_results
                else 0,
                "included_execution_summary": bool(
                    state.get("execution_summary") and self.config.include_execution_summary
                ),
                "included_reasoning_summary": bool(state.get("reasoning_result")),
            }
            if self.config.apply_safety_filter:
                state = self._apply_safety_filter(state)
        except Exception as e:
            logger.error("Response synthesis error: %s", e)
            state.setdefault("errors", []).append(f"Response synthesis error: {e}")

        return state

    def _compose_response(self, state: LangGraphOrchestrationState) -> str:
        messages = state.get("messages") or []
        last_user_message = self._extract_last_user_message(messages)
        tool_results = state.get("tool_results") or []
        execution_summary = state.get("execution_summary") or {}
        reasoning_result = state.get("reasoning_result") or {}

        parts: List[str] = []

        if last_user_message:
            parts.append(f"You asked: {last_user_message}.")

        if tool_results and self.config.include_tool_results:
            parts.append(self._format_tool_results(tool_results))

        if execution_summary and self.config.include_execution_summary:
            parts.append(
                "Execution summary: "
                f"{execution_summary.get('successful_executions', 0)} successful, "
                f"{execution_summary.get('failed_executions', 0)} failed."
            )

        if isinstance(reasoning_result, dict) and reasoning_result.get("summary"):
            parts.append(f"Reasoning summary: {reasoning_result['summary']}")

        if not parts:
            parts.append("I’m ready to help.")
        else:
            parts.append("If you want, I can go deeper on any part of this.")

        response = " ".join(parts)
        if len(response) > self.config.max_response_length:
            response = response[: self.config.max_response_length].rstrip() + "... (truncated)"

        return response

    def _extract_last_user_message(self, messages: List[Any]) -> Optional[str]:
        for message in reversed(messages):
            role = getattr(message, "type", None) or getattr(message, "role", None)
            content = getattr(message, "content", None)
            if role in {"human", "user"} and content:
                return str(content).strip()
        return None

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        rendered_results: List[str] = []
        for result in tool_results[:5]:
            tool_name = result.get("tool_name") or result.get("tool") or "tool"
            if result.get("success", result.get("status") == "success"):
                output = result.get("output")
                rendered_results.append(f"{tool_name}: {output}")
            else:
                rendered_results.append(
                    f"{tool_name}: failed ({result.get('error') or 'unknown error'})"
                )
        if not rendered_results:
            return ""
        return "Tool results: " + "; ".join(rendered_results)

    def _apply_safety_filter(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        response = state.get("llm_response", "")
        if not isinstance(response, str):
            return state

        safety_flags = state.get("safety_flags") or []
        if safety_flags and len(response) > 0:
            state["llm_response"] = response.replace("unsafe", "[filtered]")
        return state


async def response_synth_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for LangGraph orchestration."""
    node = ResponseSynthesisNode()
    return await node(state)
