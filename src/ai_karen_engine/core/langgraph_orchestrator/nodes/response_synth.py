"""Response synthesis node for LangGraph orchestration."""

import json
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

    def __init__(self, config: Optional[SynthesisConfig] = None, llm_router: Optional[Any] = None):
        self.config = config or SynthesisConfig()
        self._llm_router = llm_router

    async def __call__(
        self, state: LangGraphOrchestrationState
    ) -> LangGraphOrchestrationState:
        logger.info("Response synthesis processing")
        try:
            response = await self._compose_response(state)
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
            logger.info("Response synthesis completed")
        except Exception as e:
            logger.error("Response synthesis error: %s", e)
            state.setdefault("errors", []).append(f"Response synthesis error: {e}")
        return state

    async def _compose_response(self, state: LangGraphOrchestrationState) -> str:
        messages = state.get("messages") or []
        last_user_message = self._extract_last_user_message(messages)
        tool_results = state.get("tool_results") or []
        execution_summary = state.get("execution_summary") or {}
        reasoning_result = state.get("reasoning_result") or {}

        # If we have an LLM router and it can provide a healthy fallback or local provider,
        # use it to synthesize a natural response that includes the tool results.
        if self._llm_router:
            try:
                from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest
                
                # Check if we have a functional provider
                selection = await self._llm_router.select_provider(
                    ChatRequest(message=last_user_message or "")
                )
                
                if selection:
                    provider_name, model_name = selection
                    
                    # Construct a synthesis prompt
                    if tool_results:
                        tool_data = json.dumps(tool_results, indent=2)
                        synthesis_prompt = f"""
                        You are Karen, an intelligent assistant.
                        Synthesize a natural, helpful response for the user based on the tool results provided below.
                        
                        User's latest message: {last_user_message}
                        
                        Tool Results:
                        {tool_data}
                        
                        Respond directly to the user. If a tool failed, acknowledge it gracefully.
                        """
                    else:
                        synthesis_prompt = f"""
                        You are Karen, an intelligent assistant.
                        Respond naturally to the user.
                        
                        User's latest message: {last_user_message}
                        """
                    
                    try:
                        # Try primary provider via process_chat_request
                        response_gen = self._llm_router.process_chat_request(
                            ChatRequest(message=synthesis_prompt, stream=False)
                        )
                        
                        final_text = ""
                        metadata = {}
                        async for chunk in response_gen:
                            if isinstance(chunk, str):
                                final_text += chunk
                            elif isinstance(chunk, dict):
                                # Capture metadata if provided in chunks
                                metadata.update(chunk.get("metadata", {}).get("llm", {}))
                        
                        if final_text.strip():
                            # Store metadata for successful generation
                            # Merge initial selection with actual results from generator
                            state["llm_metadata"] = {
                                "requested_provider": provider_name,
                                "requested_model": model_name,
                                "actual_provider": provider_name,
                                "actual_model": model_name,
                                "runtime_engine": provider_name,
                                "response_source": "live_model",
                                "degraded_mode": False,
                                "used_fallback": False,
                                **metadata, # Override with actual results (e.g. if internal fallback happened)
                            }
                            
                            # Ensure actual_provider matches provider if provided in metadata
                            if "provider" in metadata:
                                state["llm_metadata"]["actual_provider"] = metadata["provider"]
                            if "source" in metadata:
                                state["llm_metadata"]["response_source"] = metadata["source"]
                            if "used_fallback" in metadata:
                                state["llm_metadata"]["used_fallback"] = metadata["used_fallback"]
                                state["llm_metadata"]["degraded_mode"] = metadata["used_fallback"]
                            
                            logger.info(
                                f"LLM synthesis successful. Actual provider: {state['llm_metadata'].get('actual_provider')}"
                            )
                            return final_text.strip()
                    
                    except Exception as provider_error:
                        # Primary provider failed - try fallback chain
                        logger.warning(
                            f"Primary provider {provider_name} failed: {provider_error}. "
                            "Attempting degraded runtime fallback to vLLM/Transformers."
                        )
                        
                        try:
                            fallback_result = await self._llm_router.generate_with_degraded_runtime_fallback(
                                request=ChatRequest(message=synthesis_prompt, stream=False),
                                requested_provider=provider_name,
                                requested_model=model_name or "unknown",
                                failure_reason=str(provider_error),
                            )
                            
                            if fallback_result and fallback_result.get("content"):
                                # Store fallback metadata
                                fallback_metadata = fallback_result.get("metadata", {}).get("llm", {})
                                state["llm_metadata"] = fallback_metadata
                                logger.info(
                                    f"Fallback successful: {fallback_metadata.get('provider', 'unknown')} "
                                    f"(requested: {provider_name})"
                                )
                                return fallback_result["content"]
                            
                            # Fallback also failed
                            logger.error(
                                "All providers failed including fallback chain. "
                                "Falling back to deterministic response."
                            )
                        
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback chain execution failed: {fallback_error}. "
                                "Falling back to deterministic response."
                            )
            
            except Exception as e:
                logger.warning(f"LLM-based synthesis failed, falling back to deterministic: {e}")

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
    llm_router: Optional[Any] = None,
) -> LangGraphOrchestrationState:
    """Convenience wrapper for LangGraph orchestration."""
    node = ResponseSynthesisNode(llm_router=llm_router)
    return await node(state)
