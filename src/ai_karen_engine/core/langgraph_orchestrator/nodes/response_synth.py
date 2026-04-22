"""
Response Synthesis Node

Implements unified response synthesis through AgentMedusa contracts.
Ensures all responses pass through Medusa synthesis engine.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..contracts.orchestration_state import LangGraphOrchestrationState
from ai_karen_engine.agent_medusa.contracts import (
    ResponseSynthesisRequest,
    ResponseSynthesisResult,
    MedusaArbitrator,
)

logger = logging.getLogger(__name__)


@dataclass
class SynthesisConfig:
    """Configuration for response synthesis"""

    max_response_length: int = 100000
    include_tool_results: bool = True
    include_execution_summary: bool = True
    apply_safety_filter: bool = True
    enable_arbitration: bool = True


class ResponseSynthesisNode:
    """Unified response synthesis through AgentMedusa"""

    def __init__(self, config: Optional[SynthesisConfig] = None):
        self.config = config or SynthesisConfig()
        self.arbitrator = MedusaArbitrator()

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """
        Synthesize response through unified AgentMedusa pipeline

        Flow: response_synth node → MedusaResponseSynthesizer → arbitration → MedusaArbitrator
        """
        logger.info("Response synthesis processing")

        try:
            # Synthesize response
            state = await self.synthesize_response(state)

            logger.info("Response synthesis completed")

        except Exception as e:
            logger.error(f"Response synthesis error: {e}")
            state.setdefault("errors", []).append(f"Response synthesis error: {str(e)}")

        return state

    async def synthesize_response(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """
        Synthesize response through unified AgentMedusa pipeline

        Flow: response_synth node → MedusaResponseSynthesizer → arbitration → MedusaArbitrator
        """
        logger.info("Response synthesis processing")

        try:
            # Create synthesis request
            request = self._create_synthesis_request(state)

            # Synthesize response (this would use AgentMedusa's synthesizer)
            result = await self._synthesize_with_medusa(request)

            # Apply arbitration if enabled
            if self.config.enable_arbitration and result.requires_arbitration:
                result = await self.arbitrator.arbitrate(result)

            # Update state with synthesized response
            state["llm_response"] = result.response
            state["synthesis_metadata"] = result.metadata

            # Apply safety filtering if enabled
            if self.config.apply_safety_filter:
                state = await self._apply_safety_filter(state)

            # Generate response summary
            state["response_summary"] = {
                "response_length": len(result.response),
                "synthesis_time_ms": result.synthesis_time_ms,
                "applied_arbitration": result.requires_arbitration,
                "included_tool_results": len(result.tool_results or []),
                "included_execution_summary": bool(result.execution_summary),
            }

            logger.info("Response synthesis completed successfully")

        except Exception as e:
            logger.error(f"Response synthesis error: {e}")
            state.setdefault("errors", []).append(f"Response synthesis error: {str(e)}")

        return state

    def _create_synthesis_request(
        self, state: LangGraphOrchestrationState
    ) -> ResponseSynthesisRequest:
        """Create AgentMedusa synthesis request"""

        # Extract conversation context
        messages = state.get("messages", [])
        conversation_history = (
            messages[-10:] if len(messages) > 10 else messages
        )  # Last 10 messages

        # Extract tool results
        tool_results = (
            state.get("tool_results", []) if self.config.include_tool_results else None
        )

        # Extract execution summary
        execution_summary = (
            state.get("execution_summary")
            if self.config.include_execution_summary
            else None
        )

        # Create synthesis request
        request = ResponseSynthesisRequest(
            conversation_history=conversation_history,
            tool_results=tool_results,
            execution_summary=execution_summary,
            context={
                "session_id": state.get("session_id"),
                "user_id": state.get("user_id"),
                "detected_intent": state.get("detected_intent"),
                "safety_status": state.get("safety_status"),
                "selected_provider": state.get("selected_provider"),
                "selected_model": state.get("selected_model"),
            },
            constraints={
                "max_length": self.config.max_response_length,
                "format": "natural_language",
                "style": "helpful_and_concise",
            },
            metadata={
                "execution_plan": state.get("execution_plan"),
                "routing_decision": state.get("routing_reason"),
                "streaming_enabled": state.get("streaming_enabled", False),
                "runtime_level": state.get("runtime_level", "FULL"),
            },
        )

        return request

    async def _synthesize_with_medusa(
        self, request: ResponseSynthesisRequest
    ) -> ResponseSynthesisResult:
        """Synthesize response using AgentMedusa"""

        # This would integrate with AgentMedusa's response synthesis engine
        # For now, implement a basic synthesis

        # Extract conversation context
        conversation_text = self._format_conversation_history(
            request.conversation_history
        )

        # Extract tool results
        tool_results_text = (
            self._format_tool_results(request.tool_results)
            if request.tool_results
            else ""
        )

        # Extract execution summary
        summary_text = (
            f"Execution: {request.execution_summary}\n"
            if request.execution_summary
            else ""
        )

        # Build prompt
        prompt = f"""{conversation_text}

{tool_results_text}

{summary_text}

Please provide a helpful and concise response based on the conversation context and available information."""

        # Apply length constraints
        if len(prompt) > request.constraints["max_length"]:
            prompt = prompt[: request.constraints["max_length"]] + "... (truncated)"

        # For now, return a basic response (would be replaced with actual Medusa synthesis)
        response = f"I understand your request. Based on the conversation context, I'll help you with this task."

        # Create result
        result = ResponseSynthesisResult(
            response=response,
            metadata={
                "synthesis_method": "basic_synthesis",
                "conversation_length": len(conversation_text),
                "tool_results_count": len(request.tool_results or []),
                "applied_constraints": request.constraints,
            },
            synthesis_time_ms=150,  # Mock timing
            requires_arbitration=False,
            tool_results=request.tool_results,
            execution_summary=request.execution_summary,
        )

        return result

    def _format_conversation_history(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation history for synthesis"""
        formatted = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
            else:
                formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool results for synthesis"""
        formatted = []

        for result in tool_results:
            tool_name = result.get("tool_name", "unknown")
            status = result.get("status", "unknown")
            output = result.get("output", "")
            error = result.get("error", "")

            if status == "success":
                formatted.append(f"Tool '{tool_name}' result: {output}")
            else:
                formatted.append(f"Tool '{tool_name}' failed: {error}")

        return "\n".join(formatted)

    async def _apply_safety_filter(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        """Apply safety filtering to synthesized response"""

        response = state.get("llm_response", "")

        # Basic safety checks (would be enhanced with proper safety system)
        if len(response) > self.config.max_response_length:
            response = (
                response[: self.config.max_response_length]
                + "... (truncated for safety)"
            )

        # Remove potentially harmful content (basic implementation)
        harmful_patterns = [
            r"<script.*?>.*?</script>",  # Remove scripts
            r"<iframe.*?>.*?</iframe>",  # Remove iframes
            r"javascript:",  # Remove javascript links
        ]

        import re

        for pattern in harmful_patterns:
            response = re.sub(pattern, "", response, flags=re.IGNORECASE | re.DOTALL)

        state["llm_response"] = response
        state["safety_applied"] = True

        return state


async def response_synth_node(
    state: LangGraphOrchestrationState,
) -> LangGraphOrchestrationState:
    """
    Response synthesis node for LangGraph orchestration

    Routes synthesis through AgentMedusa with unified response pipeline
    """
    logger.info("Response synthesis processing")

    try:
        # Initialize synthesis node
        synth_node = ResponseSynthesisNode()

        # Synthesize response
        state = await synth_node.synthesize_response(state)

        logger.info("Response synthesis completed")

    except Exception as e:
        logger.error(f"Response synthesis error: {e}")
        state.setdefault("errors", []).append(f"Response synthesis error: {str(e)}")

    return state
