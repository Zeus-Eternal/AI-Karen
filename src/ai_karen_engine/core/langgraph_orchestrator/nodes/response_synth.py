"""Response synthesis node for LangGraph orchestration."""

import json
import logging
import time
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
        request_config = state.get("request_config") or {}
        request_preferences = dict(request_config) if isinstance(request_config, dict) else {}
        requested_provider = request_preferences.get("preferred_llm_provider")
        requested_model = request_preferences.get("preferred_model")

        if self._llm_router:
            try:
                from ai_karen_engine.services.models.routing.llm_router_service import ChatRequest

                selection = await self._llm_router.select_provider(
                    ChatRequest(
                        message=last_user_message or "",
                        preferred_model=requested_model,
                        stream=bool(state.get("streaming_enabled")),
                        conversation_id=state.get("session_id"),
                    ),
                    user_preferences=request_preferences,
                )

                if selection:
                    provider_name, model_name = selection
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
                        generation_start = time.time()
                        response_gen = self._llm_router.process_chat_request(
                            ChatRequest(
                                message=synthesis_prompt,
                                stream=False,
                                preferred_model=requested_model,
                                conversation_id=state.get("session_id"),
                            ),
                            user_preferences=request_preferences,
                        )

                        final_text = ""
                        metadata: Dict[str, Any] = {}
                        async for chunk in response_gen:
                            if isinstance(chunk, str):
                                final_text += chunk
                            elif isinstance(chunk, dict):
                                chunk_metadata = chunk.get("metadata", {})
                                if isinstance(chunk_metadata, dict):
                                    llm_metadata = chunk_metadata.get("llm", {})
                                    if isinstance(llm_metadata, dict):
                                        metadata.update(llm_metadata)

                        if final_text.strip():
                            llm_metadata = self._normalize_llm_metadata(
                                metadata,
                                requested_provider=requested_provider or provider_name,
                                requested_model=requested_model or model_name,
                                selected_provider=provider_name,
                                selected_model=model_name,
                                latency_ms=(time.time() - generation_start) * 1000,
                                streaming_enabled=bool(state.get("streaming_enabled")),
                            )
                            self._store_llm_metadata(state, llm_metadata)
                            logger.info(
                                "LLM synthesis successful. Actual provider: %s",
                                llm_metadata.get("actual_provider"),
                            )
                            return final_text.strip()

                    except Exception as provider_error:
                        logger.warning(
                            "Primary provider %s failed: %s. Attempting degraded runtime fallback.",
                            provider_name,
                            provider_error,
                        )

                        try:
                            fallback_result = await self._llm_router.generate_with_degraded_runtime_fallback(
                                request=ChatRequest(
                                    message=synthesis_prompt,
                                    stream=False,
                                    preferred_model=requested_model,
                                    conversation_id=state.get("session_id"),
                                ),
                                requested_provider=requested_provider or provider_name,
                                requested_model=requested_model or model_name or "unknown",
                                failure_reason=str(provider_error),
                            )

                            if fallback_result and fallback_result.get("content"):
                                fallback_metadata = (
                                    fallback_result.get("metadata", {}).get("llm", {})
                                )
                                llm_metadata = self._normalize_llm_metadata(
                                    fallback_metadata,
                                    requested_provider=requested_provider or provider_name,
                                    requested_model=requested_model or model_name,
                                    selected_provider=provider_name,
                                    selected_model=model_name,
                                    latency_ms=None,
                                    streaming_enabled=bool(state.get("streaming_enabled")),
                                )
                                self._store_llm_metadata(state, llm_metadata)
                                logger.info(
                                    "Fallback successful: %s (requested: %s)",
                                    llm_metadata.get("actual_provider"),
                                    llm_metadata.get("requested_provider"),
                                )
                                return str(fallback_result["content"]).strip()

                            logger.error(
                                "All providers failed including fallback chain. "
                                "Falling back to deterministic response."
                            )
                        except Exception as fallback_error:
                            logger.error(
                                "Fallback chain execution failed: %s. "
                                "Falling back to deterministic response.",
                                fallback_error,
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

        emergency_metadata = self._normalize_llm_metadata(
            {
                "actual_provider": "emergency_static",
                "actual_model": "none",
                "runtime_engine": "none",
                "response_source": "emergency_static",
                "fallback_level": 99,
                "degraded_mode": True,
                "degradation_reason": "all_live_providers_failed",
            },
            requested_provider=requested_provider,
            requested_model=requested_model,
            selected_provider="emergency_static",
            selected_model="none",
            latency_ms=None,
            streaming_enabled=bool(state.get("streaming_enabled")),
        )
        self._store_llm_metadata(state, emergency_metadata)
        return response

    @staticmethod
    def _store_llm_metadata(
        state: LangGraphOrchestrationState, llm_metadata: Dict[str, Any]
    ) -> None:
        state["llm_metadata"] = llm_metadata
        response_metadata = {
            **(state.get("response_metadata") or {}),
            "llm": llm_metadata,
            "degraded_mode": bool(llm_metadata.get("degraded_mode")),
            "response_source": llm_metadata.get("response_source"),
            "actual_provider": llm_metadata.get("actual_provider"),
            "actual_model": llm_metadata.get("actual_model"),
        }
        state["response_metadata"] = response_metadata
        state["degraded_mode"] = bool(llm_metadata.get("degraded_mode"))

    @staticmethod
    def _normalize_llm_metadata(
        metadata: Dict[str, Any],
        *,
        requested_provider: Optional[Any],
        requested_model: Optional[Any],
        selected_provider: Optional[Any],
        selected_model: Optional[Any],
        latency_ms: Optional[float],
        streaming_enabled: bool,
    ) -> Dict[str, Any]:
        llm = dict(metadata or {})
        actual_provider = (
            llm.get("actual_provider") or llm.get("provider") or selected_provider or "unknown"
        )
        actual_model = (
            llm.get("actual_model")
            or llm.get("model_id")
            or llm.get("model_name")
            or selected_model
            or "auto"
        )
        resolved_requested_provider = (
            llm.get("requested_provider") or requested_provider or actual_provider
        )
        resolved_requested_model = llm.get("requested_model") or requested_model or actual_model
        provider_changed = (
            str(resolved_requested_provider or "").strip()
            and str(actual_provider or "").strip()
            and str(resolved_requested_provider).strip().lower()
            != str(actual_provider).strip().lower()
        )
        response_source = (
            llm.get("response_source")
            or ("live_model" if actual_provider != "emergency_static" else "emergency_static")
        )
        degraded_mode = bool(
            llm.get("degraded_mode")
            or llm.get("is_degraded")
            or llm.get("used_fallback")
            or provider_changed
            or response_source != "live_model"
        )
        llm.update(
            {
                "requested_provider": resolved_requested_provider,
                "requested_model": resolved_requested_model,
                "actual_provider": actual_provider,
                "actual_model": actual_model,
                "provider": actual_provider,
                "model_id": actual_model,
                "model_name": llm.get("model_name") or actual_model,
                "runtime_engine": llm.get("runtime_engine")
                or str(actual_provider).replace("builtin_", ""),
                "response_source": response_source,
                "source": llm.get("source") or response_source,
                "fallback_level": int(llm.get("fallback_level") or (1 if provider_changed else 0)),
                "degraded_mode": degraded_mode,
                "is_degraded": degraded_mode,
                "used_fallback": bool(llm.get("used_fallback") or degraded_mode),
                "streaming_enabled": streaming_enabled,
            }
        )
        if latency_ms is not None:
            llm["latency_ms"] = latency_ms
            llm["duration"] = latency_ms / 1000
        if degraded_mode and not llm.get("degradation_reason"):
            llm["degradation_reason"] = "requested_provider_unavailable" if provider_changed else "provider_fallback"
        return llm

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
