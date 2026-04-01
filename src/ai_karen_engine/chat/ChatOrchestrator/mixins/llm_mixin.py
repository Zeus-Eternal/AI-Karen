from __future__ import annotations
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING, Tuple, cast, AsyncIterator
from types import SimpleNamespace

from ai_karen_engine.chat.ChatOrchestrator.models import ProcessingResult

if TYPE_CHECKING:
    import time
    from ai_karen_engine.models.shared_types import ChatMessage
    from ..models import ChatRequest, ProcessingContext, ProcessingResult
    from ..base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    from ..models import ProcessingResult
    Base = object

logger = logging.getLogger(__name__)

class ChatLLMMixin(Base):
    """Methods for LLM routing, trials, and fallback logic with enhanced metrics."""

    async def _generate_ai_response_enhanced(
        self,
        message: str,
        parsed_message: Any,
        embeddings: Optional[List[float]],
        integrated_context: Optional[Any],
        active_instructions: List[Any],
        context: ProcessingContext,
        stream: bool = False
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
                request=request,
                context=context
            )
            if agent_result and agent_result.success:
                return agent_result.response or "", agent_result.llm_metadata, False
        
        # 3. Try Trial Plan
        # A) User-chosen model
        result = await orch._try_user_chosen_llm(
            request=request,
            context=context,
            persona_prompt=persona_prompt,
            message_history=message_history,
            stream=stream
        )
        
        if stream and isinstance(result, AsyncIterator):
            return result
        
        # 3. Fallback to system defaults if no user selection or trial failed
        if not result or (not isinstance(result, AsyncIterator) and not result.success):
            orch = cast("ChatOrchestratorProtocol", self)
            result = await orch._try_system_default_llms(
                request=context.request,
                context=context,
                persona_prompt=persona_prompt,
                message_history=message_history,
                stream=stream
            )
            
            if stream and isinstance(result, AsyncIterator):
                return result
            
        # 4. Final results extraction
        if not result:
            result = self._generate_degraded_response(context, [])
            
        if hasattr(result, "__aiter__"):
            return cast(AsyncIterator[str], result)
            
        final_res = cast(ProcessingResult, result)
        return final_res.response or "", final_res.llm_metadata, final_res.used_fallback

    async def _try_user_chosen_llm(
        self,
        request: Any,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False
    ) -> Union[Optional[ProcessingResult], AsyncIterator[str]]:
        """Try the specific LLM requested by the user, if any."""
        metadata = getattr(request, "metadata", {})
        if not metadata.get("model_id"):
            return None
            
        model_id = metadata["model_id"]
        provider = metadata.get("provider")
        
        logger.info(f"Attempting user-chosen model: {model_id} ({provider})")
        
        try:
            result = await self._generate_ai_response(
                model_id=model_id,
                provider=provider,
                prompt=getattr(request, "message", ""),
                system_prompt=persona_prompt,
                history=message_history,
                context=context,
                stream=stream
            )
            
            if stream and hasattr(result, "__aiter__"):
                return cast(AsyncIterator[str], result)
            
            final_res = cast(ProcessingResult, result)
            # Verify non-empty output
            self._verify_model_output(final_res.response, model_id)
            
            return final_res
        except Exception as exc:
            logger.warning(f"User-chosen model {model_id} failed: {exc}")
            
        return None

    async def _try_system_default_llms(
        self,
        request: Any,
        context: ProcessingContext,
        persona_prompt: str,
        message_history: List[ChatMessage],
        stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Execute the fallback chain through system defaults and local models."""
        trial_plan = self.fallback_router.get_trial_plan(request)
        
        attempted_models = []
        for trial in trial_plan:
            model_id = trial.get("model_id")
            provider = trial.get("provider")
            if not model_id: continue
            
            attempted_models.append(f"{provider}:{model_id}")
            
            try:
                start_time = time.time()
                result = await self._generate_ai_response(
                    model_id=model_id,
                    provider=provider,
                    prompt=getattr(request, "message", ""),
                    system_prompt=persona_prompt,
                    history=message_history,
                    context=context,
                    stream=stream
                )
                
                if stream and hasattr(result, "__aiter__"):
                    return cast(AsyncIterator[str], result)
                
                if isinstance(result, dict):
                    # Verify non-empty output
                    self._verify_model_output(result, model_id)
                    
                    duration = time.time() - start_time
                    metadata = self._build_llm_metadata(
                        result, 
                        source="fallback_chain",
                        additional={
                            "attempted_models": attempted_models,
                            "trial_index": len(attempted_models) - 1,
                            "duration": duration
                        }
                    )
                    return ProcessingResult(
                        success=True,
                        response=result.get("content", ""),
                        structured_content=result.get("structured_content") or {},
                        actions=result.get("actions") or [],
                        llm_metadata=metadata,
                        context=context.metadata,
                        used_fallback=len(attempted_models) > 1,
                        processing_time=duration
                    )
            except Exception as exc:
                logger.warning(f"Trial failed for {provider}:{model_id}: {exc}")
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
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Low-level call to the NLP service manager for generation."""
        # Use absolute import for service manager
        from services.memory.nlp_service_manager import nlp_service_manager
        
        messages = [{"role": "system", "content": system_prompt}]
        # Convert ChatMessage objects to the dict format expected by nlp_service_manager
        formatted_history: List[Dict[str, str]] = []
        for m in history:
            role = m.role.value if hasattr(m.role, "value") else str(m.role)
            formatted_history.append({"role": role, "content": m.content})
            
        messages.extend(formatted_history)
        messages.append({"role": "user", "content": prompt})
        
        if stream:
            return nlp_service_manager.generate_response_stream(
                model_id=model_id or "default",
                provider=provider,
                messages=messages,
                correlation_id=context.correlation_id
            )
        
        response = await nlp_service_manager.generate_response(
            model_id=model_id or "default",
            provider=provider,
            messages=messages,
            correlation_id=context.correlation_id,
            stream=False 
        )
        
        return response

    def _verify_model_output(self, result: Union[Dict[str, Any], str, None], model_id: str) -> None:
        """Ensure the LLM response is not empty and structurally valid."""
        from ..models import LLMResponseVerificationError
        
        content = ""
        if isinstance(result, dict):
            content = result.get("content", "").strip()
            # If we requested structured output, check for that too
            if not content and not result.get("structured_content") and not result.get("tool_calls"):
                logger.error(f"Model {model_id} returned empty dict: {result}")
                raise LLMResponseVerificationError(f"Model {model_id} returned empty structured response.")
        elif isinstance(result, str):
            content = result.strip()
        
        if not content and not (isinstance(result, dict) and (result.get("structured_content") or result.get("tool_calls"))):
            logger.error(f"Model {model_id} returned empty content.")
            raise LLMResponseVerificationError(
                f"Model {model_id} returned empty response.",
                metadata={"model_id": model_id, "result_keys": list(result.keys()) if isinstance(result, dict) else []}
            )

    def _build_llm_metadata(
        self,
        result: Union[Dict[str, Any], SimpleNamespace],
        source: str,
        additional: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a serializable metadata payload with enhanced metrics tracking."""
        
        provider = getattr(result, "provider", None) if not isinstance(result, dict) else result.get("provider")
        model_id = getattr(result, "model_id", None) if not isinstance(result, dict) else result.get("model_id")
        model_name = (getattr(result, "model_name", None) or self._get_model_display_name(model_id)) if not isinstance(result, dict) else (result.get("model_name") or self._get_model_display_name(model_id))
        tags = list(getattr(result, "tags", []) or []) if not isinstance(result, dict) else list(result.get("tags", []) or [])
        is_degraded = bool(getattr(result, "is_degraded", False)) if not isinstance(result, dict) else bool(result.get("is_degraded", False))

        metadata: Dict[str, Any] = {
            "source": source,
            "provider": provider,
            "model_id": model_id,
            "model_name": model_name,
            "tags": tags,
            "is_degraded": is_degraded,
            "generation_date": datetime.now().isoformat(),
        }

        failure_reason = getattr(result, "failure_reason", None) if not isinstance(result, dict) else result.get("failure_reason")
        if failure_reason: metadata["failure_reason"] = failure_reason

        extra = getattr(result, "metadata", None) if not isinstance(result, dict) else result.get("metadata", {})
        if not isinstance(extra, dict): extra = {}

        duration = extra.get("duration") or (getattr(result, "duration", None) if not isinstance(result, dict) else result.get("duration"))
        usage = extra.get("usage") or (getattr(result, "usage", None) if not isinstance(result, dict) else result.get("usage"))
        finish_reason = (usage or {}).get("finish_reason") if isinstance(usage, dict) else (getattr(result, "finish_reason", None) if not isinstance(result, dict) else result.get("finish_reason"))

        metadata["routing_confidence"] = extra.get("routing_confidence") or getattr(result, "routing_confidence", 0.0) if not isinstance(result, dict) else result.get("routing_confidence", 0.0)
        metadata["routing_rationale"] = extra.get("routing_rationale") or getattr(result, "routing_rationale", None) if not isinstance(result, dict) else result.get("routing_rationale")
        metadata["routing_strategy"] = extra.get("routing_strategy") or getattr(result, "routing_strategy", None) if not isinstance(result, dict) else result.get("routing_strategy")

        if duration is not None: metadata["duration"] = duration
        if usage is not None: metadata["usage"] = usage
        if finish_reason: metadata["finish_reason"] = finish_reason

        if duration and isinstance(usage, dict) and duration > 0:
            comp_tokens = usage.get("completion_tokens") or usage.get("total_tokens", 0)
            if comp_tokens: metadata["tokens_per_second"] = round(comp_tokens / duration, 2)
        
        if additional: metadata.update(additional)
        return metadata

    def _generate_degraded_response(self, context: ProcessingContext, attempted: List[str]) -> ProcessingResult:
        """Final safety net when all LLM options are exhausted."""
        return ProcessingResult(
            success=False,
            response="I'm having trouble connecting to my brain right now. Please try again in a moment.",
            llm_metadata={
                "source": "degraded_fallback",
                "is_degraded": True,
                "attempted_models": attempted
            },
            context=context.metadata
        )
