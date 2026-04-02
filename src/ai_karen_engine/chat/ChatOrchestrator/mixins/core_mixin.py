from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from contextlib import suppress
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Dict, List, Optional, Union, AsyncIterator, cast, TYPE_CHECKING

# Configure logger for this module
logger = logging.getLogger(__name__)

# Optional hooks import with fallback
# Optional hooks import with fallback
try:
    from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext, HookExecutionSummary
    HOOKS_AVAILABLE = True
except ImportError:
    HOOKS_AVAILABLE = False
    
    class _HookTypesFallback:
        PRE_MESSAGE = "pre_message"
        MESSAGE_PROCESSED = "message_processed"
        POST_MESSAGE = "post_message"
        MESSAGE_FAILED = "message_failed"
    
    class _HookContextFallback:
        def __init__(self, hook_type: str, data: Dict[str, Any], user_context=None, metadata=None, timestamp=None):
            self.hook_type = hook_type
            self.data = data
            self.user_context = user_context or {}
            self.metadata = metadata or {}
            self.timestamp = timestamp or datetime.utcnow()
    
    class _HookExecutionSummaryFallback:
        def __init__(self, hook_type: str = "", total_hooks: int = 0, successful_hooks: int = 0, failed_hooks: int = 0, total_execution_time_ms: float = 0.0, results: Optional[list] = None, **kwargs):
            self.hook_type = hook_type
            self.total_hooks = total_hooks
            self.successful_hooks = successful_hooks
            self.failed_hooks = failed_hooks
            self.total_execution_time_ms = total_execution_time_ms
            self.results = results or []
    
    def _get_hook_manager_fallback() -> Optional[HookManager]:
        return None

    HookTypes = _HookTypesFallback  # type: ignore
    HookContext = _HookContextFallback  # type: ignore
    HookExecutionSummary = _HookExecutionSummaryFallback # type: ignore
    get_hook_manager = _get_hook_manager_fallback # type: ignore

# Type checking models and services
if TYPE_CHECKING:
    from ai_karen_engine.hooks.hook_manager import HookManager
    from ..models import (
        ProcessingStatus, ErrorType, ChatRequest, ProcessingResult,
        ChatResponse, ChatStreamChunk, ProcessingContext
    )
else:
    from ..models import (
        ProcessingStatus, ErrorType, ChatRequest, ProcessingResult, 
        ChatResponse, ChatStreamChunk, ProcessingContext
    )

from services.memory.nlp_service_manager import nlp_service_manager
from ai_karen_engine.models.shared_types import MessageRole
if TYPE_CHECKING:
    from ai_karen_engine.chat.ChatOrchestrator.base import ChatOrchestratorProtocol
    Base = ChatOrchestratorProtocol
else:
    Base = object

class ChatCoreMixin(Base):
    """Main message processing logic for ChatOrchestrator."""

    async def process_message(
        self,
        request: ChatRequest
    ) -> Union[ChatResponse, AsyncGenerator[ChatStreamChunk, None]]:
        """
        Process a chat message with full NLP integration and error handling.
        """
        context = ProcessingContext(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            metadata=request.metadata,
            request=request,
        )

        await self._register_context(context)
        self._total_requests += 1

        if request.stream:

            async def streaming_wrapper() -> AsyncGenerator[ChatStreamChunk, None]:
                task = asyncio.current_task()
                if task:
                    await self._register_task(context.correlation_id, task)
                try:
                    async for chunk in self._process_streaming(request, context):
                        if context.cancel_event.is_set():
                            context.status = ProcessingStatus.CANCELLED
                            context.cancelled = True
                            yield ChatStreamChunk(
                                type="error",
                                content="Generation cancelled",
                                correlation_id=context.correlation_id,
                                metadata={"error_type": ErrorType.REQUEST_CANCELLED.value}
                            )
                            break
                        yield chunk
                except asyncio.CancelledError:
                    context.status = ProcessingStatus.CANCELLED
                    context.cancelled = True
                    yield ChatStreamChunk(
                        type="error",
                        content="Generation cancelled",
                        correlation_id=context.correlation_id,
                        metadata={"error_type": ErrorType.REQUEST_CANCELLED.value}
                    )
                finally:
                    await self._cleanup_context(context.correlation_id)

            return streaming_wrapper()

        task = asyncio.current_task()
        if task:
            await self._register_task(context.correlation_id, task)

        try:
            return await self._process_traditional(request, context)
        finally:
            await self._cleanup_context(context.correlation_id)

    async def _process_traditional(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> ChatResponse:
        """Process message with traditional request-response pattern."""
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING
        
        start_time = time.time()
        hook_manager: Any = get_hook_manager()
        
        pre_message_context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={
                "message": request.message,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
                "timestamp": context.request_timestamp.isoformat(),
                "correlation_id": context.correlation_id,
                "attachments": request.attachments,
                "metadata": request.metadata
            },
            user_context={
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id
            }
        )
        
        pre_hook_summary = await self._trigger_hooks_with_timeout(
            hook_manager, pre_message_context
        ) if HOOKS_AVAILABLE and hook_manager else HookExecutionSummary(hook_type="pre_message", total_hooks=0, successful_hooks=0, failed_hooks=0, total_execution_time_ms=0.0, results=[])
        
        result: Optional[ProcessingResult] = None
        processing_time: float = 0.0

        try:
            # Result can be a ProcessingResult or AsyncIterator depending on the model/provider
            result_or_gen = await self._process_with_retry(request, context)
            
            if isinstance(result_or_gen, ProcessingResult):
                result = result_or_gen
            elif hasattr(result_or_gen, "__aiter__"):
                # Pathological case: streaming iterator returned in non-streaming path
                # We collect it into a single response
                full_content = ""
                async for chunk in cast(AsyncIterator[str], result_or_gen):
                    full_content += chunk
                result = ProcessingResult(
                    success=True,
                    response=full_content,
                    correlation_id=context.correlation_id,
                    llm_metadata={"source": "sync_collection_fallback"},
                    processing_time=time.time() - start_time
                )
            
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            
            if result and result.success:
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
                
                memory_writeback = await self._orchestrate_post_response_memory_writeback(
                    request, context, result
                )
                
                message_processed_context = HookContext(
                    hook_type=HookTypes.MESSAGE_PROCESSED,
                    data={
                        "message": request.message,
                        "response": result.response,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "parsed_message": result.parsed_message.__dict__ if result.parsed_message else None,
                        "embeddings_count": len(result.embeddings) if result.embeddings else 0,
                        "context_used": bool(result.context),
                        "used_fallback": result.used_fallback,
                        "retry_count": context.retry_count
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id
                    }
                )
                
                processed_hook_summary = await self._trigger_hooks_with_timeout(
                    hook_manager, message_processed_context
                ) if HOOKS_AVAILABLE and hook_manager else HookExecutionSummary(hook_type="message_processed", total_hooks=0, successful_hooks=0, failed_hooks=0, total_execution_time_ms=0.0, results=[])
                
                metadata = {
                    "parsed_entities": len(result.parsed_message.entities) if result.parsed_message else 0,
                    "embedding_dimension": len(result.embeddings) if result.embeddings else 0,
                    "retry_count": context.retry_count,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                    "processed_hooks_executed": processed_hook_summary.successful_hooks,
                    **context.metadata
                }
                
                if result.context:
                    metadata["context_summary"] = result.context.get("context_summary", "Context retrieved")
                    metadata["memories_used"] = len(result.context.get("memories", []))
                    metadata["retrieval_time"] = result.context.get("retrieval_time", 0.0)
                    metadata["total_memories_considered"] = result.context.get("total_memories_considered", 0)

                post_message_context = HookContext(
                    hook_type=HookTypes.POST_MESSAGE,
                    data={
                        "message": request.message,
                        "response": result.response,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "metadata": metadata,
                        "hook_results": {
                            "pre_message": [r.__dict__ for r in pre_hook_summary.results],
                            "message_processed": [r.__dict__ for r in processed_hook_summary.results]
                        }
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id
                    }
                )
                
                post_hook_summary = await self._trigger_hooks_with_timeout(
                    hook_manager, post_message_context
                ) if HOOKS_AVAILABLE and hook_manager else HookExecutionSummary(hook_type="post_message", total_hooks=0, successful_hooks=0, failed_hooks=0, total_execution_time_ms=0.0, results=[])
                
                metadata["post_hooks_executed"] = post_hook_summary.successful_hooks
                metadata["total_hooks_executed"] = (
                    pre_hook_summary.successful_hooks +
                    processed_hook_summary.successful_hooks +
                    post_hook_summary.successful_hooks
                )

                if result.llm_metadata:
                    metadata["llm"] = result.llm_metadata
                metadata["memory_writeback"] = memory_writeback

                return ChatResponse(
                    response=result.response or "",
                    correlation_id=context.correlation_id,
                    processing_time=processing_time,
                    status=context.status,
                    used_fallback=result.used_fallback,
                    context_used=bool(result.context),
                    structured_content=result.structured_content or {},
                    actions=result.actions or [],
                    metadata=metadata,
                    error=result.error,
                    error_type=result.error_type
                )
            else:
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
                
                eff_res = result if result else ProcessingResult(success=False, error="Invalid response type", error_type=ErrorType.UNKNOWN_ERROR, correlation_id=context.correlation_id)

                message_failed_context = HookContext(
                    hook_type=HookTypes.MESSAGE_FAILED,
                    data={
                        "message": request.message,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "error": eff_res.error,
                        "error_type": eff_res.error_type.value if eff_res.error_type else "unknown",
                        "retry_count": context.retry_count,
                        "used_fallback": eff_res.used_fallback
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id
                    }
                )
                
                failed_hook_summary = await self._trigger_hooks_with_timeout(
                    hook_manager, message_failed_context
                ) if HOOKS_AVAILABLE and hook_manager else HookExecutionSummary(hook_type="message_failed", total_hooks=0, successful_hooks=0, failed_hooks=0, total_execution_time_ms=0.0, results=[])
                
                error_metadata = {
                    "error": eff_res.error,
                    "error_type": eff_res.error_type.value if eff_res.error_type else "unknown",
                    "retry_count": context.retry_count,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                    "failed_hooks_executed": failed_hook_summary.successful_hooks,
                }

                if eff_res.llm_metadata:
                    error_metadata["llm"] = eff_res.llm_metadata

                return ChatResponse(
                    response=f"I apologize, but I encountered an error processing your message: {eff_res.error}",
                    correlation_id=context.correlation_id,
                    processing_time=processing_time,
                    status=context.status,
                    used_fallback=True,
                    context_used=False,
                    metadata=error_metadata,
                    error=eff_res.error,
                    error_type=eff_res.error_type
                )
                
        except asyncio.CancelledError:
            context.status = ProcessingStatus.CANCELLED
            context.cancelled = True
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            self._failed_requests += 1
            context.status = ProcessingStatus.FAILED
            logger.error(f"Unexpected error in chat processing: {e}", exc_info=True)
            return ChatResponse(
                response="I apologize, but I encountered an unexpected error. Please try again.",
                correlation_id=context.correlation_id,
                processing_time=processing_time,
                status=ProcessingStatus.FAILED,
                used_fallback=True,
                context_used=False,
                error=str(e),
                error_type=ErrorType.UNKNOWN_ERROR,
                metadata={"error": str(e)}
            )
        finally:
            context.processing_end = datetime.utcnow()

    async def _process_streaming(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Process message with streaming response."""
        start_time = time.time()
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING
        hook_manager: Any = get_hook_manager()
        
        pre_message_context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={
                "message": request.message,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id,
                "timestamp": context.request_timestamp.isoformat(),
                "correlation_id": context.correlation_id,
                "attachments": request.attachments,
                "metadata": request.metadata,
                "streaming": True
            },
            user_context={
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "session_id": request.session_id
            }
        )
        
        if HOOKS_AVAILABLE and hook_manager:
            pre_hook_summary = await hook_manager.trigger_hooks(pre_message_context)
        else:
            pre_hook_summary = HookExecutionSummary(hook_type="pre_message_streaming", total_hooks=0, successful_hooks=0, failed_hooks=0, total_execution_time_ms=0.0, results=[])
        
        try:
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            yield ChatStreamChunk(
                type="metadata",
                content="",
                correlation_id=context.correlation_id,
                metadata={
                    "status": "processing",
                    "user_id": context.user_id,
                    "conversation_id": context.conversation_id,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks
                }
            )
            
            result_or_gen = await self._process_with_retry(request, context, stream=True)
            
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            result: Optional[ProcessingResult] = None
            full_response = ""
            
            # Handle AsyncIterator (standard streaming)
            if hasattr(result_or_gen, "__aiter__"):
                async for token in cast(AsyncIterator[str], result_or_gen):
                    if context.cancel_event.is_set():
                        break
                    full_response += token
                    yield ChatStreamChunk(
                        type="content",
                        content=token,
                        correlation_id=context.correlation_id
                    )
                
                result = ProcessingResult(
                    success=True,
                    response=full_response,
                    correlation_id=context.correlation_id,
                    llm_metadata={"streaming": True},
                    processing_time=time.time() - start_time
                )
            # Handle direct ProcessingResult (e.g. if streaming failed and returned a regular response)
            elif isinstance(result_or_gen, ProcessingResult):
                result = result_or_gen
                if result.success and result.response:
                    yield ChatStreamChunk(
                        type="content",
                        content=result.response,
                        correlation_id=context.correlation_id
                    )
            
            if result and result.success and result.response:
                memory_writeback = await self._orchestrate_post_response_memory_writeback(
                    request, context, result
                )

                completion_metadata = {
                    "processing_time": result.processing_time,
                    "used_fallback": result.used_fallback,
                    "retry_count": context.retry_count,
                    "memory_writeback": memory_writeback,
                }
                
                yield ChatStreamChunk(
                    type="complete", 
                    content="", 
                    correlation_id=context.correlation_id, 
                    metadata=completion_metadata
                )
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
            elif result:
                error_metadata = {
                    "error_type": result.error_type.value if result.error_type else "unknown",
                    "retry_count": context.retry_count,
                }
                yield ChatStreamChunk(
                    type="error", 
                    content=result.error or "Processing failed", 
                    correlation_id=context.correlation_id, 
                    metadata=error_metadata
                )
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
            else:
                yield ChatStreamChunk(
                    type="error",
                    content="An unexpected error occurred during streaming.",
                    correlation_id=context.correlation_id,
                    metadata={"error_type": ErrorType.UNKNOWN_ERROR.value}
                )
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
                
        except asyncio.CancelledError:
            context.status = ProcessingStatus.CANCELLED
            context.cancelled = True
            yield ChatStreamChunk(
                type="error",
                content="Generation cancelled",
                correlation_id=context.correlation_id,
                metadata={"error_type": ErrorType.REQUEST_CANCELLED.value}
            )
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield ChatStreamChunk(
                type="error",
                content=f"Streaming error: {str(e)}",
                correlation_id=context.correlation_id,
                metadata={"error_type": ErrorType.UNKNOWN_ERROR.value}
            )
            self._failed_requests += 1
            context.status = ProcessingStatus.FAILED
        finally:
            context.processing_end = datetime.utcnow()

    async def _process_with_retry(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Process message with retry logic and exponential backoff."""
        last_error = None
        last_error_type = ErrorType.UNKNOWN_ERROR
        
        for attempt in range(self.retry_config.max_attempts):
            context.retry_count = attempt
            if context.cancel_event.is_set():
                raise asyncio.CancelledError()

            if attempt > 0:
                context.status = ProcessingStatus.RETRYING
                self._retry_attempts += 1
                
                delay = min(self.retry_config.initial_delay * (self.retry_config.backoff_factor ** (attempt - 1)), self.retry_config.max_delay) if self.retry_config.exponential_backoff else self.retry_config.initial_delay
                await asyncio.sleep(delay)
            
            try:
                result = await self._process_message_core(request, context, stream=stream)
                if stream and hasattr(result, "__aiter__"):
                    return cast(AsyncIterator[str], result)
                
                if isinstance(result, ProcessingResult) and result.success:
                    return result
                elif isinstance(result, ProcessingResult):
                    last_error = result.error if hasattr(result, 'error') else "Unknown error"
                    last_error_type = result.error_type or ErrorType.UNKNOWN_ERROR
            except asyncio.CancelledError:
                context.status = ProcessingStatus.CANCELLED
                context.cancelled = True
                raise
            except asyncio.TimeoutError:
                last_error = f"Processing timeout after {self.timeout_seconds}s"
                last_error_type = ErrorType.TIMEOUT_ERROR
            except Exception as e:
                last_error = str(e)
                last_error_type = ErrorType.UNKNOWN_ERROR
        
        return ProcessingResult(success=False, error=last_error, error_type=last_error_type, correlation_id=context.correlation_id)

    async def _process_message_core(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Core message processing with NLP integration."""
        start_time = time.time()
        try:
            return await asyncio.wait_for(self._process_message_internal(request, context, stream=stream), timeout=self.timeout_seconds)
        except asyncio.CancelledError:
            return ProcessingResult(success=False, error="Processing cancelled", error_type=ErrorType.REQUEST_CANCELLED, processing_time=time.time() - start_time, correlation_id=context.correlation_id)
        except asyncio.TimeoutError:
            return ProcessingResult(success=False, error=f"Processing timeout after {self.timeout_seconds}s", error_type=ErrorType.TIMEOUT_ERROR, processing_time=time.time() - start_time, correlation_id=context.correlation_id)

    async def _process_message_internal(
        self,
        request: ChatRequest,
        context: ProcessingContext,
        stream: bool = False
    ) -> Union[ProcessingResult, AsyncIterator[str]]:
        """Internal message processing with enhanced instruction processing and context integration."""
        start_time = time.time()
        parsed_message = None
        embeddings = None
        used_fallback = False

        if context.cancel_event.is_set():
            raise asyncio.CancelledError()
        
        try:
            try:
                parsed_message = await nlp_service_manager.parse_message(request.message)
                if parsed_message.used_fallback:
                    used_fallback = True
                    self._fallback_usage += 1
            except Exception as e:
                return ProcessingResult(success=False, error=f"Message parsing failed: {str(e)}", error_type=ErrorType.NLP_PARSING_ERROR, processing_time=time.time() - start_time, correlation_id=context.correlation_id)
            
            try:
                from ai_karen_engine.chat.instruction_processor import InstructionContext
                instruction_context = InstructionContext(user_id=request.user_id, conversation_id=request.conversation_id, session_id=request.session_id, message_history=[request.message], metadata=request.metadata)
                extracted_instructions = await self.instruction_processor.extract_instructions(request.message, instruction_context)
                if extracted_instructions:
                    await self.instruction_processor.store_instructions(extracted_instructions, instruction_context)
                active_instructions = await self.instruction_processor.get_active_instructions(instruction_context)
            except Exception as e:
                active_instructions = []
            
            try:
                embeddings = await nlp_service_manager.get_embeddings(request.message)
            except Exception as e:
                return ProcessingResult(success=False, error=f"Embedding generation failed: {str(e)}", error_type=ErrorType.EMBEDDING_ERROR, processing_time=time.time() - start_time, correlation_id=context.correlation_id)
            
            if self.memory_processor:
                try:
                    await self.memory_processor.extract_memories(request.message, parsed_message, embeddings, request.user_id, request.conversation_id)
                except Exception:
                    pass
            
            attachment_context = {}
            if request.attachments and self.file_attachment_service:
                try:
                    attachment_context = await self._process_attachments(request.attachments, request.user_id, request.conversation_id)
                except Exception:
                    pass
            
            integrated_context = None
            if request.include_context:
                try:
                    raw_context = await self._retrieve_context(embeddings, parsed_message, request.user_id, request.conversation_id)
                    if attachment_context: raw_context["attachments"] = attachment_context
                    if active_instructions:
                        raw_context["instructions"] = [{"type": inst.type.value, "content": inst.content, "priority": inst.priority.value, "scope": inst.scope.value, "confidence": inst.confidence} for inst in active_instructions]
                    integrated_context = await self.context_integrator.integrate_context(raw_context, request.message, request.user_id, request.conversation_id)
                except Exception:
                    pass
            
            try:
                result = await self._generate_ai_response_enhanced(
                    request.message, 
                    parsed_message, 
                    embeddings, 
                    integrated_context, 
                    active_instructions, 
                    context,
                    stream=stream
                )
                
                if stream and isinstance(result, AsyncIterator):
                    return result
                    
                res_tuple = cast(tuple[str, dict[str, Any], bool], result)
                ai_response, llm_metadata, llm_used_fallback = res_tuple

                try:
                    from ai_karen_engine.chat.response_formatter import ResponseContext as FormatterContext
                    formatter_ctx = FormatterContext(user_query=request.message, response_content=ai_response, session_data={"correlation_id": context.correlation_id})
                    formatted_result = await self.output_layer.format_response(ai_response, formatter_ctx)
                    ai_response = formatted_result.get("content", ai_response)
                    if "metadata" in formatted_result:
                        llm_metadata["output_formatting"] = formatted_result["metadata"]
                except Exception:
                    pass

                synth_result = ProcessingResult(
                    success=True, 
                    response=ai_response, 
                    parsed_message=parsed_message, 
                    embeddings=embeddings, 
                    context=integrated_context.to_dict() if integrated_context else {}, 
                    processing_time=time.time() - start_time, 
                    used_fallback=used_fallback or llm_used_fallback, 
                    correlation_id=context.correlation_id, 
                    llm_metadata=llm_metadata
                )
                
                return synth_result

            except Exception as e:
                return ProcessingResult(success=False, error=f"AI response generation failed: {str(e)}", error_type=ErrorType.AI_MODEL_ERROR, processing_time=time.time() - start_time, correlation_id=context.correlation_id, llm_metadata={})
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            return ProcessingResult(success=False, error=f"Unexpected processing error: {str(e)}", error_type=ErrorType.UNKNOWN_ERROR, processing_time=time.time() - start_time, correlation_id=context.correlation_id)

    async def cancel_processing(self, *, conversation_id: Optional[str] = None, correlation_id: Optional[str] = None) -> List[str]:
        """Cancel active processing contexts."""
        if not conversation_id and not correlation_id:
            raise ValueError("Either conversation_id or correlation_id must be provided")

        async with self._contexts_lock: snapshot = list(self._active_contexts.items())
        target_ids = [cid for cid, ctx in snapshot if (correlation_id and cid == correlation_id) or (conversation_id and ctx.conversation_id == conversation_id)]

        cancelled = []
        for cid in target_ids:
            async with self._contexts_lock: ctx = self._active_contexts.get(cid)
            if not ctx: continue
            if not ctx.cancel_event.is_set():
                ctx.cancel_event.set()
                ctx.cancelled = True
                ctx.status = ProcessingStatus.CANCELLED
            async with self._tasks_lock:
                task = self._active_tasks.get(cid)
                if task and not task.done(): task.cancel()
            cancelled.append(cid)
        return cancelled

    async def _register_context(self, context: ProcessingContext) -> None:
        async with self._contexts_lock: self._active_contexts[context.correlation_id] = context

    async def _register_task(self, correlation_id: str, task: asyncio.Task) -> None:
        async with self._tasks_lock: self._active_tasks[correlation_id] = task

    async def _cleanup_context(self, correlation_id: str) -> None:
        async with self._tasks_lock: task = self._active_tasks.pop(correlation_id, None)
        current_task = asyncio.current_task()
        if task and task is not current_task and not task.done():
            with suppress(asyncio.CancelledError):
                task.cancel()
        async with self._contexts_lock: self._active_contexts.pop(correlation_id, None)
    
    async def _retrieve_context(self, embeddings: List[float], parsed_message: Any, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Retrieve relevant context."""
        if not self.memory_processor:
            return {"memories": [], "conversation_history": [], "user_preferences": {}, "entities": [{"text": ent[0], "label": ent[1]} for ent in parsed_message.entities], "embedding_similarity_threshold": 0.7, "context_summary": "Memory processor not available"}
        
        try:
            memory_context = await self.memory_processor.get_relevant_context(embeddings, parsed_message, user_id, conversation_id)
            return memory_context.to_dict()
        except Exception as e:
            return {"memories": [], "entities": [{"text": ent[0], "label": ent[1]} for ent in parsed_message.entities], "preferences": [], "facts": [], "relationships": [], "context_summary": f"Context retrieval failed: {str(e)}", "retrieval_time": 0.0, "total_memories_considered": 0, "embedding_similarity_threshold": 0.7}
    
    async def _process_attachments(self, attachments: List[Dict[str, Any]], user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Process file attachments."""
        if not self.file_attachment_service: return {"error": "File attachment service not available"}
        attachment_context: Dict[str, Any] = {"files": [], "total_files": len(attachments), "processing_errors": []}
        for attachment in attachments:
            attachment_id = attachment.get("id") or attachment.get("file_id")
            if not attachment_id: continue
            try:
                file_info = await self.file_attachment_service.get_file_info(attachment_id)
                if not file_info:
                    attachment_context["processing_errors"].append(f"File {attachment_id} not found")
                    continue
                attachment_context["files"].append({"file_id": attachment_id, "status": file_info.processing_status.value})
            except Exception as e:
                attachment_context["processing_errors"].append(f"Failed to process {attachment_id}: {str(e)}")
        return attachment_context
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        avg_processing_time = sum(self._processing_times) / len(self._processing_times) if self._processing_times else 0.0
        success_rate = self._successful_requests / self._total_requests if self._total_requests > 0 else 0.0
        return {"total_requests": self._total_requests, "successful_requests": self._successful_requests, "failed_requests": self._failed_requests, "success_rate": success_rate, "retry_attempts": self._retry_attempts, "fallback_usage": self._fallback_usage, "avg_processing_time": avg_processing_time, "active_contexts": len(self._active_contexts)}
    
    def get_active_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active processing contexts."""
        return {correlation_id: {"user_id": ctx.user_id, "conversation_id": ctx.conversation_id, "status": ctx.status.value} for correlation_id, ctx in self._active_contexts.items()}
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_attempts = 0
        self._fallback_usage = 0
        self._processing_times.clear()
        logger.info("ChatOrchestrator statistics reset")
