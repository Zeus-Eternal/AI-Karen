from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import (
    Optional,
    List,
    Dict,
    Any,
    Union,
    TYPE_CHECKING,
    Tuple,
    cast,
    AsyncIterator,
)
from types import SimpleNamespace

from ai_karen_engine.chat.ChatOrchestrator.models import (
    ProcessingContext,
    ProcessingResult,
    ChatRequest,
    ProcessingStatus,
    ErrorType,
)
from ai_karen_engine.core.chat_runtime_control_plane import RuntimeConstants
from ai_karen_engine.models.shared_types import ChatMessage, MessageRole

if TYPE_CHECKING:
    import time
    from ..models import ChatRequest, ProcessingContext, ProcessingResult
    from ..base import ChatOrchestratorProtocol

    Base = ChatOrchestratorProtocol
else:
    from ..models import ProcessingResult

    Base = object

logger = logging.getLogger(__name__)


def _normalize_provider_name(provider: Optional[str]) -> str:
    value = str(provider or "").strip().lower()
    if value in {"llama-cpp", "llama_cpp", "local"}:
        return "llamacpp"
    return value


def _normalize_model_name(model_id: Optional[str]) -> str:
    value = str(model_id or "").strip().lower()
    if not value:
        return ""
    value = value.split(":", 1)[-1].split("/", 1)[-1]
    if value.endswith(".gguf"):
        value = value[:-5]
    elif value.endswith(".bin"):
        value = value[:-4]
    return value.replace("_", "-")


def _is_low_information_content(content: str) -> bool:
    text = str(content or "").strip()
    if not text:
        return True
    if len(text) == 1 and not text.isalnum():
        return True
    if all(ch in set(".-_=`'\"!?,:;()[]{}|/\\ \n\t") for ch in text):
        return True
    return False


class ChatLLMMixin(Base):
    """Methods for LLM routing, trials, and fallback logic with enhanced metrics."""

    def _resolve_generation_max_tokens(
        self,
        prompt: str,
        context: ProcessingContext,
    ) -> int:
        """Choose a sensible max token budget for the current request."""
        metadata = dict((getattr(context, "metadata", {}) or {}))

        for key in ("max_tokens", "max_output_tokens"):
            raw_value = metadata.get(key)
            if isinstance(raw_value, int) and raw_value > 0:
                return raw_value
            if isinstance(raw_value, str) and raw_value.isdigit():
                parsed = int(raw_value)
                if parsed > 0:
                    return parsed

        prompt_text = str(prompt or "").lower()
        request_context = metadata.get("request_context")
        if isinstance(request_context, dict):
            recent_messages = request_context.get("recent_messages")
            if isinstance(recent_messages, list):
                for item in recent_messages[-6:]:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("role", "")).strip().lower() != "user":
                        continue
                    content = str(item.get("content", "")).strip().lower()
                    if content:
                        prompt_text += "\n" + content

        longform_markers = (
            "full article",
            "write an article",
            "blog article",
            "blog post",
            "long-form",
            "in-depth",
            "comprehensive",
            "detailed guide",
            "essay",
        )
        if any(marker in prompt_text for marker in longform_markers):
            return 2200

        return 800

    async def _generate_ai_response_enhanced(
        self,
        message: str,
        parsed_message: Any,
        embeddings: Optional[List[float]],
        integrated_context: Optional[Any],
        active_instructions: List[Any],
        context: ProcessingContext,
        stream: bool = False,
    ) -> Union[Tuple[str, Dict[str, Any], bool], AsyncIterator[str]]:
        """
        Orchestrated entry point for AI response generation with fallback trials.
        Returns (response_text, llm_metadata, used_fallback_bool).
        """
        # 0. Validate Request
        if not context.request:
            logger.error(f"Missing request in context for {context.correlation_id}")
            return "Execution Error: Missing Request Context", {}, False

        # Cast self to the Protocol to ensure Pylance recognizes the methods from other mixins
        orch = cast("ChatOrchestratorProtocol", self)
        request = context.request

        # 1. Build prompts and history
        persona_prompt = await orch._get_persona_system_prompt(context)
        message_history = await orch._build_chat_messages(context)

        # 2. Try Agentic Workflow if requested or warranted
        # Current logic: explicitly requested via metadata or complex tool intention
        if context.metadata.get("agent_mode") or context.metadata.get("force_agent"):
            logger.info(f"Triggering agentic workflow for {context.correlation_id}")
            # Ensure we pass the actual ChatRequest from context
            agent_result = await orch._orchestrate_agentic_workflow(
                request=request, context=context
            )
            if agent_result and agent_result.success:
                return agent_result.response or "", agent_result.llm_metadata, False

        # 3. Try Trial Plan
        # A) User-chosen model
        user_result, user_failure_reason = await orch._try_user_chosen_llm(
            request=request,
            context=context,
            persona_prompt=persona_prompt,
            message_history=message_history,
            stream=stream,
        )

        if stream and isinstance(user_result, AsyncIterator):
            return user_result

        result = user_result

        # 3. Fallback to system defaults if no user selection or trial failed
        if not result or (not isinstance(result, AsyncIterator) and not result.success):
            orch = cast("ChatOrchestratorProtocol", self)
            result = await orch._try_system_default_llms(
                request=context.request,
                context=context,
                persona_prompt=persona_prompt,
                message_history=message_history,
                stream=stream,
                initial_failure_reason=user_failure_reason,
            )

            if stream and isinstance(result, AsyncIterator):
                return result

        # 4. Final results extraction
        if not result:
            result = self._generate_degraded_response(context, [])

        if hasattr(result, "__aiter__"):
            return cast(AsyncIterator[str], result)

        final_res = cast(ProcessingResult, result)
        return (
            final_res.response or "",
            final_res.llm_metadata,
            final_res.used_fallback,
        )

    async def _try_user_chosen_llm(
        self,
        request: Any,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False,
    ) -> Tuple[Optional[Union[ProcessingResult, AsyncIterator[str]]], Optional[str]]:
        """Try the specific LLM requested by the user, if any."""
        metadata = getattr(request, "metadata", {})
        model_id = metadata.get("model_id") or metadata.get("preferred_model")
        provider = metadata.get("provider") or metadata.get("preferred_llm_provider")

        if not model_id:
            return None, None

        logger.info(f"Attempting user-chosen model: {model_id} ({provider})")

        try:
            result = await self._generate_ai_response(
                model_id=model_id,
                provider=provider,
                prompt=getattr(request, "message", ""),
                system_prompt=persona_prompt,
                history=message_history,
                context=context,
                stream=stream,
            )

            if stream and hasattr(result, "__aiter__"):
                return cast(AsyncIterator[str], result), None

            if isinstance(result, dict):
                if result.get("success") is False:
                    raise RuntimeError(
                        str(
                            result.get("error")
                            or result.get("content")
                            or "Provider generation failed"
                        )
                    )
                self._verify_model_output(result, model_id)
                metadata = self._build_llm_metadata(
                    result,
                    source="requested_model",
                    additional={
                        "requested_provider": provider,
                        "requested_model": model_id,
                    },
                )
                return ProcessingResult(
                    success=True,
                    response=result.get("content", ""),
                    structured_content=result.get("structured_content") or {},
                    actions=result.get("actions") or [],
                    llm_metadata=metadata,
                    context=context.metadata,
                    used_fallback=False,
                ), None

            final_res = cast(ProcessingResult, result)
            self._verify_model_output(final_res.response, model_id)
            return final_res, None
        except Exception as exc:
            logger.warning(f"User-chosen model {model_id} failed: {exc}")
            return None, str(exc).strip()

        return None, None

    async def _try_system_default_llms(
        self,
        request: Any,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False,
        initial_failure_reason: Optional[str] = None,
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Execute the fallback chain through system defaults and local models."""
        # Use the centralized LLM router instead of old fallback router
        from ai_karen_engine.memory.llm_router import (
            LLMRouter,
            ChatRequest as RouterChatRequest,
        )

        router = LLMRouter()

        # Convert orchestrator request to router request
        router_request = RouterChatRequest(
            message=getattr(request, "message", ""),
            context=getattr(request, "metadata", {}),
            preferred_model=getattr(request, "metadata", {}).get("model_id"),
            user_preferences=getattr(request, "metadata", {}),
        )

        # Get provider selection from centralized router
        try:
            provider_selection = await router.select_provider(router_request)
            if provider_selection:
                provider, model = provider_selection
                trial_plan = [{"model_id": model, "provider": provider}]
                logger.info(f"Selected provider: {provider} with model: {model}")
            else:
                # Fallback to old system if new router fails
                trial_plan = self.fallback_router.get_trial_plan(request)
                logger.warning("Provider selection failed, using fallback router")
        except Exception as e:
            logger.error(f"Provider selection error: {e}, using fallback router")
            trial_plan = self.fallback_router.get_trial_plan(request)
        request_metadata = getattr(request, "metadata", {}) or {}
        preferred_model = request_metadata.get("model_id") or request_metadata.get(
            "preferred_model"
        )
        preferred_provider = request_metadata.get("provider") or request_metadata.get(
            "preferred_llm_provider"
        )

        attempted_models = []
        preferred_failure_reason: Optional[str] = initial_failure_reason
        for trial in trial_plan:
            model_id = trial.get("model_id")
            provider = trial.get("provider")
            if not model_id:
                continue

            attempted_models.append(f"{provider}:{model_id}")

            try:
                start_time = time.time()
                logger.info(
                    f"Attempting to generate response with provider: {provider}, model: {model_id}"
                )
                result = await self._generate_ai_response(
                    model_id=model_id,
                    provider=provider,
                    prompt=getattr(request, "message", ""),
                    system_prompt=persona_prompt,
                    history=message_history,
                    context=context,
                    stream=stream,
                )

                if stream and hasattr(result, "__aiter__"):
                    return cast(AsyncIterator[str], result)

                if isinstance(result, dict):
                    if result.get("success") is False:
                        raise RuntimeError(
                            str(
                                result.get("error")
                                or result.get("content")
                                or "Provider generation failed"
                            )
                        )
                    # Verify non-empty output
                    self._verify_model_output(result, model_id)

                    duration = time.time() - start_time
                    preferred_selection_failed = bool(
                        preferred_model or preferred_provider
                    )
                    actual_provider = result.get("provider") or provider
                    actual_model_id = result.get("model_id") or model_id
                    normalized_preferred_model = _normalize_model_name(preferred_model)
                    normalized_actual_model = _normalize_model_name(actual_model_id)
                    normalized_preferred_provider = _normalize_provider_name(
                        preferred_provider
                    )
                    normalized_actual_provider = _normalize_provider_name(
                        actual_provider
                    )
                    selection_mismatch = bool(
                        normalized_preferred_model
                        and normalized_actual_model
                        and normalized_preferred_model != normalized_actual_model
                    ) or bool(
                        normalized_preferred_provider
                        and normalized_actual_provider
                        and normalized_preferred_provider != normalized_actual_provider
                    )
                    preferred_selection_mismatch = bool(
                        preferred_selection_failed and selection_mismatch
                    )
                    used_fallback = (
                        len(attempted_models) > 1 or preferred_selection_mismatch
                    )
                    is_degraded = bool(result.get("is_degraded", False))
                    resolved_failure_reason = (
                        result.get("failure_reason")
                        or (preferred_failure_reason if is_degraded else None)
                        or (
                            f"Requested provider/model {preferred_provider or 'default'}"
                            f"{('/' + preferred_model) if preferred_model else ''} could not be used; "
                            f"continued with {actual_provider or 'fallback'}"
                            f"{('/' + actual_model_id) if actual_model_id else ''}."
                            if is_degraded and preferred_selection_mismatch
                            else None
                        )
                    )
                    metadata = self._build_llm_metadata(
                        {
                            **result,
                            "provider": actual_provider,
                            "model_id": actual_model_id,
                            "is_degraded": is_degraded,
                            "failure_reason": resolved_failure_reason,
                            "routing_rationale": result.get("routing_rationale")
                            or (
                                f"Preferred selection failed with: {preferred_failure_reason}. Fallback chain selected "
                                f"{actual_provider or 'fallback'}"
                                f"{('/' + actual_model_id) if actual_model_id else ''}."
                                if preferred_selection_failed
                                and preferred_selection_mismatch
                                and preferred_failure_reason
                                else (
                                    f"Preferred selection could not be used; fallback chain selected "
                                    f"{actual_provider or 'fallback'}"
                                    f"{('/' + actual_model_id) if actual_model_id else ''}."
                                    if preferred_selection_mismatch
                                    else None
                                )
                            ),
                            "fallback_level": result.get("fallback_level")
                            or (
                                "provider_selection"
                                if preferred_selection_mismatch
                                else ("system_default" if used_fallback else None)
                            ),
                        },
                        source="fallback_chain",
                        additional={
                            "attempted_models": attempted_models,
                            "trial_index": len(attempted_models) - 1,
                            "duration": duration,
                            "requested_provider": preferred_provider,
                            "requested_model": preferred_model,
                            "preferred_failure_reason": preferred_failure_reason,
                        },
                    )
                    return ProcessingResult(
                        success=True,
                        response=result.get("content", ""),
                        structured_content=result.get("structured_content") or {},
                        actions=result.get("actions") or [],
                        llm_metadata=metadata,
                        context=context.metadata,
                        used_fallback=used_fallback,
                        processing_time=duration,
                    )
            except Exception as exc:
                logger.warning(f"Trial failed for {provider}:{model_id}: {exc}")
                logger.info(
                    f"Continuing with next provider in fallback chain. Attempted so far: {attempted_models}"
                )
                should_capture_failure = False
                if preferred_provider or preferred_model:
                    provider_matches = bool(
                        _normalize_provider_name(preferred_provider)
                        and _normalize_provider_name(provider)
                        and _normalize_provider_name(preferred_provider)
                        == _normalize_provider_name(provider)
                    )
                    model_matches = bool(
                        _normalize_model_name(preferred_model)
                        and _normalize_model_name(model_id)
                        and _normalize_model_name(preferred_model)
                        == _normalize_model_name(model_id)
                    )
                    should_capture_failure = provider_matches or model_matches
                elif len(attempted_models) == 1:
                    should_capture_failure = True

                if should_capture_failure and not preferred_failure_reason:
                    preferred_failure_reason = (
                        str(exc).strip() or f"{provider}:{model_id} failed"
                    )
                continue

        return self._generate_degraded_response(context, attempted_models)

    async def _generate_ai_response(
        self,
        model_id: str,
        provider: Optional[str],
        prompt: str,
        system_prompt: str,
        history: List[ChatMessage],
        context: ProcessingContext,
        stream: bool = False,
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Low-level call to the NLP service manager for generation."""
        # Use absolute import for service manager
        from ai_karen_engine.memory.nlp_service_manager import nlp_service_manager

        # `history` already contains the prompt sequence assembled by the prompt
        # mixin, including the active system prompt and current user turn.
        # Duplicating those entries here causes completion-style models to keep
        # extending a synthetic multi-turn transcript.
        messages: List[Dict[str, Any]] = []
        for m in history:
            if hasattr(m, "model_dump"):
                payload = m.model_dump(mode="json")
            else:
                role = m.role.value if hasattr(m.role, "value") else str(m.role)
                timestamp = getattr(m, "timestamp", None)
                payload = {
                    "id": str(getattr(m, "id", "") or ""),
                    "role": role,
                    "content": m.content,
                    "timestamp": (
                        timestamp.isoformat()
                        if timestamp is not None and hasattr(timestamp, "isoformat")
                        else str(timestamp or "")
                    ),
                }
            messages.append(payload)

        if not messages:
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt).model_dump(
                    mode="json"
                ),
                ChatMessage(role=MessageRole.USER, content=prompt).model_dump(
                    mode="json"
                ),
            ]

        if stream:
            max_tokens = self._resolve_generation_max_tokens(prompt, context)
            return nlp_service_manager.generate_response_stream(
                model_id=model_id or "default",
                provider=provider,
                messages=messages,
                correlation_id=context.correlation_id,
                max_tokens=max_tokens,
            )

        max_tokens = self._resolve_generation_max_tokens(prompt, context)
        response = await nlp_service_manager.generate_response(
            model_id=model_id or "default",
            provider=provider,
            messages=messages,
            correlation_id=context.correlation_id,
            stream=False,
            max_tokens=max_tokens,
        )

        if isinstance(response, dict):
            nested_metadata = response.get("metadata")
            if isinstance(nested_metadata, dict):
                for key in (
                    "provider",
                    "model_id",
                    "model_name",
                    "is_degraded",
                    "failure_reason",
                    "preferred_failure_reason",
                    "routing_rationale",
                    "routing_strategy",
                    "routing_confidence",
                    "fallback_level",
                    "attempted_models",
                    "requested_provider",
                    "requested_model",
                    "duration",
                    "usage",
                    "tokens_per_second",
                ):
                    if key not in response and key in nested_metadata:
                        response[key] = nested_metadata[key]

        return response

    def _verify_model_output(
        self, result: Union[Dict[str, Any], str, None], model_id: str
    ) -> None:
        """Ensure the LLM response is not empty and structurally valid."""
        from ..models import LLMResponseVerificationError

        content = ""
        if isinstance(result, dict):
            content = (result.get("content") or "").strip()
            # If we requested structured output, check for that too
            if (
                not content
                and not result.get("structured_content")
                and not result.get("tool_calls")
            ):
                logger.error(f"Model {model_id} returned empty dict: {result}")
                raise LLMResponseVerificationError(
                    f"Model {model_id} returned empty structured response."
                )
        elif isinstance(result, str):
            content = result.strip()

        if not content and not (
            isinstance(result, dict)
            and (result.get("structured_content") or result.get("tool_calls"))
        ):
            logger.error(f"Model {model_id} returned empty content.")
            raise LLMResponseVerificationError(
                f"Model {model_id} returned empty response.",
                metadata={
                    "model_id": model_id,
                    "result_keys": list(result.keys())
                    if isinstance(result, dict)
                    else [],
                },
            )
        if _is_low_information_content(content):
            logger.error(f"Model {model_id} returned low-information content.")
            raise LLMResponseVerificationError(
                f"Model {model_id} returned low-information response.",
                metadata={
                    "model_id": model_id,
                    "content_preview": content[:20],
                },
            )

    def _build_llm_metadata(
        self,
        result: Union[Dict[str, Any], SimpleNamespace],
        source: str,
        additional: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a serializable metadata payload with enhanced metrics tracking."""

        provider = (
            getattr(result, "actual_provider", getattr(result, "provider", None))
            if not isinstance(result, dict)
            else result.get("actual_provider") or result.get("provider")
        )
        requested_provider = (
            getattr(result, "requested_provider", None)
            if not isinstance(result, dict)
            else result.get("requested_provider")
        ) or (additional.get("requested_provider") if additional else None)

        model_id = (
            getattr(result, "model_id", None)
            if not isinstance(result, dict)
            else result.get("model_id")
        )
        model_name = (
            (
                getattr(result, "model_name", None)
                or self._get_model_display_name(model_id)
            )
            if not isinstance(result, dict)
            else (result.get("model_name") or self._get_model_display_name(model_id))
        )

        # Ensure we have a provider and model for consistent metadata
        if not provider:
            provider = "llamacpp"  # Default fallback provider
        if not model_id and not model_name:
            model_name = "Phi-3-mini-4k-instruct-q4.gguf"  # Default model

        tags = (
            list(getattr(result, "tags", []) or [])
            if not isinstance(result, dict)
            else list(result.get("tags", []) or [])
        )
        is_degraded = (
            bool(getattr(result, "is_degraded", False))
            if not isinstance(result, dict)
            else bool(result.get("is_degraded", False))
        )

        # If actual differs from requested, it's degraded/fallback
        if (
            not is_degraded
            and requested_provider
            and provider
            and requested_provider != provider
        ):
            is_degraded = True

        # Ensure degraded mode is set if fallback was used
        if not is_degraded and additional and additional.get("used_fallback"):
            is_degraded = True

        metadata: Dict[str, Any] = {
            "source": source,
            "provider": provider,
            "requested_provider": requested_provider,
            "model_id": model_id,
            "model_name": model_name,
            "tags": tags,
            "is_degraded": is_degraded,
            "generation_date": datetime.now().isoformat(),
        }

        failure_reason = (
            getattr(result, "failure_reason", None)
            if not isinstance(result, dict)
            else result.get("failure_reason")
        )
        if failure_reason:
            metadata["failure_reason"] = failure_reason

        extra = (
            getattr(result, "metadata", None)
            if not isinstance(result, dict)
            else result.get("metadata", {})
        )
        if not isinstance(extra, dict):
            extra = {}

        duration = extra.get("duration") or (
            getattr(result, "duration", None)
            if not isinstance(result, dict)
            else result.get("duration")
        )
        usage = extra.get("usage") or (
            getattr(result, "usage", None)
            if not isinstance(result, dict)
            else result.get("usage")
        )
        finish_reason = (
            (usage or {}).get("finish_reason")
            if isinstance(usage, dict)
            else (
                getattr(result, "finish_reason", None)
                if not isinstance(result, dict)
                else result.get("finish_reason")
            )
        )

        metadata["routing_confidence"] = (
            extra.get("routing_confidence")
            or getattr(result, "routing_confidence", 0.0)
            if not isinstance(result, dict)
            else result.get("routing_confidence", 0.0)
        )
        metadata["routing_rationale"] = (
            extra.get("routing_rationale") or getattr(result, "routing_rationale", None)
            if not isinstance(result, dict)
            else result.get("routing_rationale")
        )
        metadata["routing_strategy"] = (
            extra.get("routing_strategy") or getattr(result, "routing_strategy", None)
            if not isinstance(result, dict)
            else result.get("routing_strategy")
        )

        for key in (
            "requested_provider",
            "requested_model",
            "fallback_level",
            "attempted_models",
            "trial_index",
            "preferred_failure_reason",
        ):
            value = extra.get(key)
            if value is None and additional:
                value = additional.get(key)

            if value is not None:
                metadata[key] = value

        if duration is not None:
            metadata["duration"] = duration
        if usage is not None:
            metadata["usage"] = usage
        if finish_reason:
            metadata["finish_reason"] = finish_reason

        if duration and isinstance(usage, dict) and duration > 0:
            comp_tokens = usage.get("completion_tokens") or usage.get("total_tokens", 0)
            if comp_tokens:
                metadata["tokens_per_second"] = round(comp_tokens / duration, 2)

        if additional:
            metadata.update(additional)
        return metadata

    def _generate_degraded_response(
        self, context: ProcessingContext, attempted: List[str]
    ) -> ProcessingResult:
        """Final safety net when all LLM options are exhausted."""
        return ProcessingResult(
            success=False,
            response=RuntimeConstants.DEGRADED_BRAIN_ERROR,
            used_fallback=True,
            llm_metadata={
                "source": RuntimeConstants.SOURCE_DEGRADED_STATIC,
                "is_degraded": True,
                "attempted_models": attempted,
                "generated_by_model": False,
                "fallback_kind": "static_degraded_message",
            },
            context=context.metadata,
        )
