"""Response synthesis node for LangGraph orchestration."""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai_karen_engine.services.response import ResponseContract, ResponseSanitizer, ResponseSynthesizer
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
        self._response_sanitizer = ResponseSanitizer()

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
                    
                    cortex = state.get("cortex")
                    intent = "general.chat"
                    subtype = None
                    requires_chat_capable_model = True
                    
                    if cortex and hasattr(cortex, "intent"):
                        intent = cortex.intent.primary_intent
                        subtype = getattr(cortex.intent, "subtype", None)
                        requires_chat_capable_model = getattr(cortex.intent, "requires_chat_capable_model", True)
                    elif isinstance(cortex, dict):
                        intent_data = cortex.get("intent", {})
                        if isinstance(intent_data, dict):
                            intent = intent_data.get("primary_intent", "general.chat")
                            subtype = intent_data.get("subtype")
                            requires_chat_capable_model = intent_data.get("requires_chat_capable_model", True)

                    contract = ResponseContract(
                        purpose="tool_synthesis" if tool_results else "chat",
                        intent=intent,
                        subtype=subtype,
                        requires_chat_capable_model=requires_chat_capable_model,
                        latest_user_message=last_user_message or "",
                        tool_results=tool_results if isinstance(tool_results, list) else [],
                        reasoning_summary=(reasoning_result.get("summary") if isinstance(reasoning_result, dict) else None),
                        runtime_metadata={
                            "requested_provider": requested_provider,
                            "requested_model": requested_model,
                            "selected_provider": provider_name,
                            "selected_model": model_name,
                        },
                    )
                    try:
                        generation_start = time.time()
                        synthesizer = ResponseSynthesizer(self._llm_router)
                        final_text, synthesis_metadata = await synthesizer.synthesize(
                            contract,
                            user_preferences=request_preferences,
                            conversation_id=state.get("session_id"),
                            stream=False,
                        )

                        if final_text.strip():
                            metadata_blob = synthesis_metadata.get("llm", synthesis_metadata)
                            llm_metadata = self._normalize_llm_metadata(
                                metadata_blob,
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
                                    message=last_user_message or "",
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

        fallback = self._compose_deterministic_fallback(
            last_user_message=last_user_message,
            tool_results=tool_results,
            execution_summary=execution_summary,
            reasoning_result=reasoning_result,
        )

        response = self._response_sanitizer.sanitize(fallback)
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


    def _compose_deterministic_fallback(
        self,
        *,
        last_user_message: Optional[str],
        tool_results: List[Dict[str, Any]],
        execution_summary: Dict[str, Any],
        reasoning_result: Dict[str, Any],
    ) -> str:
        if tool_results and self.config.include_tool_results:
            return self._format_tool_results(tool_results)
        if isinstance(reasoning_result, dict) and reasoning_result.get("summary"):
            return str(reasoning_result["summary"]).strip()
        if execution_summary and self.config.include_execution_summary:
            successful = execution_summary.get("successful_executions", 0)
            failed = execution_summary.get("failed_executions", 0)
            return f"I completed the request with {successful} successful step(s) and {failed} failed step(s)."
        return "I’m here and ready to help, but I’m currently operating with limited capacity. Please try again in a moment."

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
