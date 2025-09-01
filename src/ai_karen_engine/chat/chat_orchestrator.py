"""
ChatOrchestrator with spaCy and DistilBERT integration.

This module implements the core chat orchestrator that coordinates message processing
with NLP services, retry logic, error handling, and context management.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from enum import Enum
import json

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
from ai_karen_engine.services.spacy_service import ParsedMessage
from ai_karen_engine.models.shared_types import ChatMessage, MessageRole
from ai_karen_engine.chat.memory_processor import MemoryProcessor, MemoryContext
from ai_karen_engine.chat.file_attachment_service import FileAttachmentService
from ai_karen_engine.chat.multimedia_service import MultimediaService
from ai_karen_engine.chat.code_execution_service import CodeExecutionService
from ai_karen_engine.chat.tool_integration_service import ToolIntegrationService
from ai_karen_engine.chat.instruction_processor import InstructionProcessor, InstructionContext, InstructionScope
from ai_karen_engine.chat.context_integrator import ContextIntegrator
from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext, HookExecutionSummary
# Note: LLM orchestrator import moved to method level to avoid circular dependency

logger = logging.getLogger(__name__)


class ProcessingStatus(str, Enum):
    """Status of message processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ErrorType(str, Enum):
    """Types of processing errors."""
    NLP_PARSING_ERROR = "nlp_parsing_error"
    EMBEDDING_ERROR = "embedding_error"
    CONTEXT_RETRIEVAL_ERROR = "context_retrieval_error"
    AI_MODEL_ERROR = "ai_model_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True


@dataclass
class ProcessingContext:
    """Context for message processing."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    conversation_id: str = ""
    session_id: Optional[str] = None
    request_timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    retry_count: int = 0
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of message processing."""
    success: bool
    response: Optional[str] = None
    parsed_message: Optional[ParsedMessage] = None
    embeddings: Optional[List[float]] = None
    context: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    processing_time: float = 0.0
    used_fallback: bool = False
    correlation_id: str = ""


class ChatRequest(BaseModel):
    """Request for chat processing."""
    message: str = Field(..., description="User message to process")
    user_id: str = Field(..., description="ID of the user")
    conversation_id: str = Field(..., description="ID of the conversation")
    session_id: Optional[str] = Field(None, description="Session ID for correlation")
    stream: bool = Field(True, description="Whether to stream the response")
    include_context: bool = Field(True, description="Whether to include memory context")
    attachments: List[str] = Field(default_factory=list, description="List of file attachment IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ChatResponse(BaseModel):
    """Response from chat processing."""
    response: str = Field(..., description="AI response")
    correlation_id: str = Field(..., description="Request correlation ID")
    processing_time: float = Field(..., description="Total processing time in seconds")
    used_fallback: bool = Field(False, description="Whether fallback processing was used")
    context_used: bool = Field(False, description="Whether memory context was used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class ChatStreamChunk(BaseModel):
    """Chunk of streaming chat response."""
    type: str = Field(..., description="Type of chunk: content, metadata, complete, error")
    content: str = Field("", description="Content of the chunk")
    correlation_id: str = Field(..., description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Chunk timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class ChatOrchestrator:
    """
    Production-ready chat orchestrator with spaCy and DistilBERT integration.
    
    Features:
    - Message processing pipeline with spaCy parsing and DistilBERT embeddings
    - Retry logic with exponential backoff for failed processing
    - Comprehensive error handling with graceful degradation
    - Request correlation and context management
    """
    
    def __init__(
        self,
        memory_processor: Optional[MemoryProcessor] = None,
        file_attachment_service: Optional[FileAttachmentService] = None,
        multimedia_service: Optional[MultimediaService] = None,
        code_execution_service: Optional[CodeExecutionService] = None,
        tool_integration_service: Optional[ToolIntegrationService] = None,
        instruction_processor: Optional[InstructionProcessor] = None,
        context_integrator: Optional[ContextIntegrator] = None,
        retry_config: Optional[RetryConfig] = None,
        timeout_seconds: float = 30.0,
        enable_monitoring: bool = True
    ):
        self.memory_processor = memory_processor
        self.file_attachment_service = file_attachment_service
        self.multimedia_service = multimedia_service
        self.code_execution_service = code_execution_service
        self.tool_integration_service = tool_integration_service
        self.instruction_processor = instruction_processor or InstructionProcessor()
        self.context_integrator = context_integrator or ContextIntegrator()
        self.retry_config = retry_config or RetryConfig()
        self.timeout_seconds = timeout_seconds
        self.enable_monitoring = enable_monitoring
        
        # Processing metrics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_attempts = 0
        self._fallback_usage = 0
        self._processing_times: List[float] = []
        
        # Active processing contexts
        self._active_contexts: Dict[str, ProcessingContext] = {}
        
        logger.info("ChatOrchestrator initialized with enhanced instruction processing and context integration")
    
    async def process_message(
        self,
        request: ChatRequest
    ) -> Union[ChatResponse, AsyncGenerator[ChatStreamChunk, None]]:
        """
        Process a chat message with full NLP integration and error handling.
        
        Args:
            request: Chat request containing message and metadata
            
        Returns:
            ChatResponse for non-streaming or AsyncGenerator for streaming
        """
        # Create processing context
        context = ProcessingContext(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        self._active_contexts[context.correlation_id] = context
        self._total_requests += 1
        
        try:
            if request.stream:
                return self._process_streaming(request, context)
            else:
                return await self._process_traditional(request, context)
        finally:
            # Clean up context
            if context.correlation_id in self._active_contexts:
                del self._active_contexts[context.correlation_id]
    
    async def _process_traditional(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> ChatResponse:
        """Process message with traditional request-response pattern."""
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING
        
        start_time = time.time()
        hook_manager = get_hook_manager()
        
        # Trigger pre-message hooks
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
        
        try:
            pre_hook_summary = await hook_manager.trigger_hooks(pre_message_context)
            logger.debug(f"Pre-message hooks executed: {pre_hook_summary.successful_hooks}/{pre_hook_summary.total_hooks}")
        except Exception as e:
            logger.warning(f"Pre-message hooks failed: {e}")
            # Create empty summary for failed hooks
            from ai_karen_engine.hooks.models import HookExecutionSummary
            pre_hook_summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[]
            )
        
        try:
            # Process with retry logic
            result = await self._process_with_retry(request, context)
            
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            
            if result.success:
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
                
                # Trigger message processed hooks
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
                
                try:
                    processed_hook_summary = await hook_manager.trigger_hooks(message_processed_context)
                    logger.debug(f"Message processed hooks executed: {processed_hook_summary.successful_hooks}/{processed_hook_summary.total_hooks}")
                except Exception as e:
                    logger.warning(f"Message processed hooks failed: {e}")
                    from ai_karen_engine.hooks.models import HookExecutionSummary
                    processed_hook_summary = HookExecutionSummary(
                        hook_type=HookTypes.MESSAGE_PROCESSED,
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[]
                    )
                
                # Build metadata with context information
                metadata = {
                    "parsed_entities": len(result.parsed_message.entities) if result.parsed_message else 0,
                    "embedding_dimension": len(result.embeddings) if result.embeddings else 0,
                    "retry_count": context.retry_count,
                    "pre_hooks_executed": pre_hook_summary.successful_hooks,
                    "processed_hooks_executed": processed_hook_summary.successful_hooks,
                    **context.metadata
                }
                
                # Add context summary if available
                if result.context:
                    metadata["context_summary"] = result.context.get("context_summary", "Context retrieved")
                    metadata["memories_used"] = len(result.context.get("memories", []))
                    metadata["retrieval_time"] = result.context.get("retrieval_time", 0.0)
                    metadata["total_memories_considered"] = result.context.get("total_memories_considered", 0)
                
                # Trigger post-message hooks
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
                
                try:
                    post_hook_summary = await hook_manager.trigger_hooks(post_message_context)
                    logger.debug(f"Post-message hooks executed: {post_hook_summary.successful_hooks}/{post_hook_summary.total_hooks}")
                except Exception as e:
                    logger.warning(f"Post-message hooks failed: {e}")
                    from ai_karen_engine.hooks.models import HookExecutionSummary
                    post_hook_summary = HookExecutionSummary(
                        hook_type=HookTypes.POST_MESSAGE,
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[]
                    )
                
                # Add hook execution summary to metadata
                metadata["post_hooks_executed"] = post_hook_summary.successful_hooks
                metadata["total_hooks_executed"] = (
                    pre_hook_summary.successful_hooks + 
                    processed_hook_summary.successful_hooks + 
                    post_hook_summary.successful_hooks
                )
                
                return ChatResponse(
                    response=result.response or "",
                    correlation_id=context.correlation_id,
                    processing_time=processing_time,
                    used_fallback=result.used_fallback,
                    context_used=bool(result.context),
                    metadata=metadata
                )
            else:
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
                
                # Trigger message failed hooks
                message_failed_context = HookContext(
                    hook_type=HookTypes.MESSAGE_FAILED,
                    data={
                        "message": request.message,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id,
                        "correlation_id": context.correlation_id,
                        "processing_time": processing_time,
                        "error": result.error,
                        "error_type": result.error_type.value if result.error_type else "unknown",
                        "retry_count": context.retry_count,
                        "used_fallback": result.used_fallback
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id,
                        "session_id": request.session_id
                    }
                )
                
                try:
                    failed_hook_summary = await hook_manager.trigger_hooks(message_failed_context)
                    logger.debug(f"Message failed hooks executed: {failed_hook_summary.successful_hooks}/{failed_hook_summary.total_hooks}")
                except Exception as e:
                    logger.warning(f"Message failed hooks failed: {e}")
                    from ai_karen_engine.hooks.models import HookExecutionSummary
                    failed_hook_summary = HookExecutionSummary(
                        hook_type=HookTypes.MESSAGE_FAILED,
                        total_hooks=0,
                        successful_hooks=0,
                        failed_hooks=0,
                        total_execution_time_ms=0.0,
                        results=[]
                    )
                
                # Return error response
                return ChatResponse(
                    response=f"I apologize, but I encountered an error processing your message: {result.error}",
                    correlation_id=context.correlation_id,
                    processing_time=processing_time,
                    used_fallback=True,
                    context_used=False,
                    metadata={
                        "error": result.error,
                        "error_type": result.error_type.value if result.error_type else "unknown",
                        "retry_count": context.retry_count,
                        "pre_hooks_executed": pre_hook_summary.successful_hooks,
                        "failed_hooks_executed": failed_hook_summary.successful_hooks
                    }
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            self._failed_requests += 1
            context.status = ProcessingStatus.FAILED
            
            logger.error(f"Unexpected error in chat processing: {e}", exc_info=True)
            
            return ChatResponse(
                response="I apologize, but I encountered an unexpected error. Please try again.",
                correlation_id=context.correlation_id,
                processing_time=processing_time,
                used_fallback=True,
                context_used=False,
                metadata={
                    "error": str(e),
                    "error_type": ErrorType.UNKNOWN_ERROR.value
                }
            )
        finally:
            context.processing_end = datetime.utcnow()
    
    async def _process_streaming(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Process message with streaming response."""
        context.processing_start = datetime.utcnow()
        context.status = ProcessingStatus.PROCESSING
        hook_manager = get_hook_manager()
        
        # Trigger pre-message hooks for streaming
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
        
        pre_hook_summary = await hook_manager.trigger_hooks(pre_message_context)
        logger.debug(f"Pre-message hooks executed (streaming): {pre_hook_summary.successful_hooks}/{pre_hook_summary.total_hooks}")
        
        try:
            # Send initial metadata chunk
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
            
            # Process with retry logic
            result = await self._process_with_retry(request, context)
            
            if result.success and result.response:
                # Stream the response content
                words = result.response.split()
                for i, word in enumerate(words):
                    content = word + (" " if i < len(words) - 1 else "")
                    yield ChatStreamChunk(
                        type="content",
                        content=content,
                        correlation_id=context.correlation_id
                    )
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.05)
                
                # Send completion chunk
                yield ChatStreamChunk(
                    type="complete",
                    content="",
                    correlation_id=context.correlation_id,
                    metadata={
                        "processing_time": result.processing_time,
                        "used_fallback": result.used_fallback,
                        "context_used": bool(result.context),
                        "retry_count": context.retry_count
                    }
                )
                
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
                
            else:
                # Send error chunk
                yield ChatStreamChunk(
                    type="error",
                    content=result.error or "Processing failed",
                    correlation_id=context.correlation_id,
                    metadata={
                        "error_type": result.error_type.value if result.error_type else "unknown",
                        "retry_count": context.retry_count
                    }
                )
                
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
                
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
        context: ProcessingContext
    ) -> ProcessingResult:
        """Process message with retry logic and exponential backoff."""
        last_error = None
        last_error_type = ErrorType.UNKNOWN_ERROR
        
        for attempt in range(self.retry_config.max_attempts):
            context.retry_count = attempt
            
            if attempt > 0:
                context.status = ProcessingStatus.RETRYING
                self._retry_attempts += 1
                
                # Calculate delay with exponential backoff
                if self.retry_config.exponential_backoff:
                    delay = min(
                        self.retry_config.initial_delay * (self.retry_config.backoff_factor ** (attempt - 1)),
                        self.retry_config.max_delay
                    )
                else:
                    delay = self.retry_config.initial_delay
                
                logger.info(f"Retrying request {context.correlation_id}, attempt {attempt + 1}, delay: {delay}s")
                await asyncio.sleep(delay)
            
            try:
                # Process the message
                result = await self._process_message_core(request, context)
                
                if result.success:
                    return result
                else:
                    last_error = result.error
                    last_error_type = result.error_type or ErrorType.UNKNOWN_ERROR
                    
            except asyncio.TimeoutError:
                last_error = f"Processing timeout after {self.timeout_seconds}s"
                last_error_type = ErrorType.TIMEOUT_ERROR
                logger.warning(f"Timeout on attempt {attempt + 1} for {context.correlation_id}")
                
            except Exception as e:
                last_error = str(e)
                last_error_type = ErrorType.UNKNOWN_ERROR
                logger.error(f"Error on attempt {attempt + 1} for {context.correlation_id}: {e}")
        
        # All retries failed
        return ProcessingResult(
            success=False,
            error=last_error,
            error_type=last_error_type,
            correlation_id=context.correlation_id
        )
    
    async def _process_message_core(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> ProcessingResult:
        """Core message processing with NLP integration."""
        start_time = time.time()
        
        try:
            # Apply timeout to the entire processing
            return await asyncio.wait_for(
                self._process_message_internal(request, context),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            return ProcessingResult(
                success=False,
                error=f"Processing timeout after {self.timeout_seconds}s",
                error_type=ErrorType.TIMEOUT_ERROR,
                processing_time=time.time() - start_time,
                correlation_id=context.correlation_id
            )
    
    async def _process_message_internal(
        self,
        request: ChatRequest,
        context: ProcessingContext
    ) -> ProcessingResult:
        """Internal message processing with enhanced instruction processing and context integration."""
        start_time = time.time()
        parsed_message = None
        embeddings = None
        retrieved_context = None
        used_fallback = False
        extracted_instructions = []
        
        try:
            # Step 1: Parse message with spaCy
            try:
                parsed_message = await nlp_service_manager.parse_message(request.message)
                if parsed_message.used_fallback:
                    used_fallback = True
                    self._fallback_usage += 1
                    
                logger.debug(f"Parsed message: {len(parsed_message.tokens)} tokens, "
                           f"{len(parsed_message.entities)} entities")
                           
            except Exception as e:
                logger.error(f"spaCy parsing failed: {e}")
                return ProcessingResult(
                    success=False,
                    error=f"Message parsing failed: {str(e)}",
                    error_type=ErrorType.NLP_PARSING_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id
                )
            
            # Step 2: Extract and process instructions
            try:
                instruction_context = InstructionContext(
                    user_id=request.user_id,
                    conversation_id=request.conversation_id,
                    session_id=request.session_id,
                    message_history=[request.message],
                    metadata=request.metadata
                )
                
                # Extract instructions from current message
                extracted_instructions = await self.instruction_processor.extract_instructions(
                    request.message, instruction_context
                )
                
                # Store instructions for persistence
                if extracted_instructions:
                    await self.instruction_processor.store_instructions(
                        extracted_instructions, instruction_context
                    )
                    logger.debug(f"Extracted and stored {len(extracted_instructions)} instructions")
                
                # Get active instructions for context
                active_instructions = await self.instruction_processor.get_active_instructions(
                    instruction_context
                )
                
                logger.debug(f"Found {len(active_instructions)} active instructions")
                
            except Exception as e:
                logger.warning(f"Instruction processing failed: {e}")
                # Don't fail the entire request for instruction processing errors
                extracted_instructions = []
                active_instructions = []
            
            # Step 3: Generate embeddings with DistilBERT
            try:
                embeddings = await nlp_service_manager.get_embeddings(request.message)
                logger.debug(f"Generated embeddings: {len(embeddings)} dimensions")
                
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                return ProcessingResult(
                    success=False,
                    error=f"Embedding generation failed: {str(e)}",
                    error_type=ErrorType.EMBEDDING_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id
                )
            
            # Step 4: Extract and store memories (if memory processor available)
            extracted_memories = []
            if self.memory_processor:
                try:
                    extracted_memories = await self.memory_processor.extract_memories(
                        request.message,
                        parsed_message,
                        embeddings,
                        request.user_id,
                        request.conversation_id
                    )
                    logger.debug(f"Extracted {len(extracted_memories)} memories")
                    
                except Exception as e:
                    logger.warning(f"Memory extraction failed: {e}")
                    # Don't fail the entire request for memory extraction errors
            
            # Step 4: Process file attachments (if any)
            attachment_context = {}
            if request.attachments and self.file_attachment_service:
                try:
                    attachment_context = await self._process_attachments(
                        request.attachments,
                        request.user_id,
                        request.conversation_id
                    )
                    logger.debug(f"Processed {len(request.attachments)} attachments")
                    
                except Exception as e:
                    logger.warning(f"Attachment processing failed: {e}")
                    # Don't fail the entire request for attachment processing errors
                    attachment_context = {"error": str(e)}
            
            # Step 5: Retrieve and integrate context (if enabled)
            integrated_context = None
            if request.include_context:
                try:
                    # Get raw context from memory processor
                    raw_context = await self._retrieve_context(
                        embeddings,
                        parsed_message,
                        request.user_id,
                        request.conversation_id
                    )
                    
                    # Merge attachment context into raw context
                    if attachment_context:
                        raw_context["attachments"] = attachment_context
                    
                    # Add instructions to raw context
                    if active_instructions:
                        raw_context["instructions"] = [
                            {
                                "type": inst.type.value,
                                "content": inst.content,
                                "priority": inst.priority.value,
                                "scope": inst.scope.value,
                                "confidence": inst.confidence
                            }
                            for inst in active_instructions
                        ]
                    
                    # Use context integrator for enhanced context processing
                    integrated_context = await self.context_integrator.integrate_context(
                        raw_context,
                        request.message,
                        request.user_id,
                        request.conversation_id
                    )
                    
                    logger.debug(f"Integrated context: {integrated_context.context_summary}")
                    
                except Exception as e:
                    logger.warning(f"Context integration failed: {e}")
                    # Don't fail the entire request for context integration errors
                    integrated_context = None
            
            # Step 6: Generate AI response with enhanced context and instructions
            try:
                ai_response = await self._generate_ai_response_enhanced(
                    request.message,
                    parsed_message,
                    embeddings,
                    integrated_context,
                    active_instructions,
                    context
                )
                
                return ProcessingResult(
                    success=True,
                    response=ai_response,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    context=integrated_context.to_dict() if integrated_context else {},
                    processing_time=time.time() - start_time,
                    used_fallback=True,  # Always true when using fallback response
                    correlation_id=context.correlation_id
                )
                
            except Exception as e:
                logger.error(f"AI response generation failed: {e}")
                return ProcessingResult(
                    success=False,
                    error=f"AI response generation failed: {str(e)}",
                    error_type=ErrorType.AI_MODEL_ERROR,
                    processing_time=time.time() - start_time,
                    correlation_id=context.correlation_id
                )
                
        except Exception as e:
            logger.error(f"Unexpected error in message processing: {e}", exc_info=True)
            return ProcessingResult(
                success=False,
                error=f"Unexpected processing error: {str(e)}",
                error_type=ErrorType.UNKNOWN_ERROR,
                processing_time=time.time() - start_time,
                correlation_id=context.correlation_id
            )
    
    async def _retrieve_context(
        self,
        embeddings: List[float],
        parsed_message: ParsedMessage,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Retrieve relevant context for the message using MemoryProcessor."""
        if not self.memory_processor:
            # Fallback context when memory processor is not available
            return {
                "memories": [],
                "conversation_history": [],
                "user_preferences": {},
                "entities": [{"text": ent[0], "label": ent[1]} for ent in parsed_message.entities],
                "embedding_similarity_threshold": 0.7,
                "context_summary": "Memory processor not available"
            }
        
        try:
            # Use MemoryProcessor to get relevant context
            memory_context = await self.memory_processor.get_relevant_context(
                embeddings,
                parsed_message,
                user_id,
                conversation_id
            )
            
            # Convert MemoryContext to dictionary format
            context = {
                "memories": [
                    {
                        "id": mem.id,
                        "content": mem.content,
                        "type": mem.memory_type.value,
                        "similarity_score": mem.similarity_score,
                        "recency_score": mem.recency_score,
                        "combined_score": mem.combined_score,
                        "created_at": mem.created_at.isoformat(),
                        "metadata": mem.metadata
                    }
                    for mem in memory_context.memories
                ],
                "entities": memory_context.entities,
                "preferences": memory_context.preferences,
                "facts": memory_context.facts,
                "relationships": memory_context.relationships,
                "context_summary": memory_context.context_summary,
                "retrieval_time": memory_context.retrieval_time,
                "total_memories_considered": memory_context.total_memories_considered,
                "embedding_similarity_threshold": self.memory_processor.similarity_threshold
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Memory context retrieval failed: {e}")
            # Return fallback context on error
            return {
                "memories": [],
                "entities": [{"text": ent[0], "label": ent[1]} for ent in parsed_message.entities],
                "preferences": [],
                "facts": [],
                "relationships": [],
                "context_summary": f"Context retrieval failed: {str(e)}",
                "retrieval_time": 0.0,
                "total_memories_considered": 0,
                "embedding_similarity_threshold": 0.7
            }
    
    async def _generate_ai_response_enhanced(
        self,
        message: str,
        parsed_message: ParsedMessage,
        embeddings: List[float],
        integrated_context: Optional[Any],  # IntegratedContext object
        active_instructions: List[Any],     # List of ExtractedInstruction objects
        processing_context: ProcessingContext
    ) -> str:
        """Generate AI response using enhanced context integration and instruction following with proper LLM fallback hierarchy."""
        # Check for code execution requests
        code_execution_result = await self._handle_code_execution_request(
            message, processing_context
        )
        if code_execution_result:
            return code_execution_result
        
        # Check for tool execution requests
        tool_execution_result = await self._handle_tool_execution_request(
            message, processing_context
        )
        if tool_execution_result:
            return tool_execution_result
        
        # Build enhanced prompt with instructions and context
        enhanced_prompt = await self._build_enhanced_prompt(
            message, integrated_context, active_instructions
        )
        
        # Implement proper LLM response hierarchy:
        # 1. User's chosen LLM (like Llama)
        # 2. System default LLMs if user choice fails  
        # 3. Hardcoded responses as final fallback
        
        # Get user preferences from processing context
        user_llm_choice = processing_context.metadata.get('preferred_llm_provider', 'local')
        user_model_choice = processing_context.metadata.get('preferred_model', 'tinyllama-1.1b')
        
        logger.info(f"Attempting LLM response with user choice: {user_llm_choice}:{user_model_choice}")
        
        # Step 1: Try user's chosen LLM
        try:
            response = await self._try_user_chosen_llm(
                enhanced_prompt, message, parsed_message, integrated_context, active_instructions, 
                user_llm_choice, user_model_choice
            )
            if response:
                logger.info(f"Successfully generated response using user's chosen LLM: {user_llm_choice}")
                return response
        except Exception as e:
            logger.warning(f"User's chosen LLM ({user_llm_choice}) failed: {e}")
        
        # Step 2: Try system default LLMs
        try:
            response = await self._try_system_default_llms(
                enhanced_prompt, message, parsed_message, integrated_context, active_instructions
            )
            if response:
                logger.info("Successfully generated response using system default LLM")
                return response
        except Exception as e:
            logger.warning(f"System default LLMs failed: {e}")
        
        # Step 3: Use hardcoded fallback response
        logger.info("All LLM providers failed, using hardcoded fallback response")
        return await self._generate_enhanced_fallback_response(
            message, parsed_message, integrated_context, active_instructions
        )
    
    async def _try_user_chosen_llm(
        self,
        enhanced_prompt: str,
        message: str,
        parsed_message: ParsedMessage,
        integrated_context: Optional[Any],
        active_instructions: List[Any],
        provider: str,
        model: str
    ) -> Optional[str]:
        """Try to generate response using user's chosen LLM provider and model."""
        try:
            from ai_karen_engine.llm_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            
            # Try to get the specific provider/model combination
            model_id = f"{provider}:{model}"
            model_info = orchestrator.registry.get(model_id)
            
            if not model_info:
                logger.debug(f"User's chosen model {model_id} not available in registry")
                return None
            
            # Check if this is a code-related request for enhanced assistance
            if self._is_code_related_message(message):
                # Get code suggestions if available
                code_suggestions = await orchestrator.get_code_suggestions(
                    message, 
                    language=self._detect_programming_language(message)
                )

                if code_suggestions:
                    # Use CopilotKit for code-related responses
                    copilot_response = orchestrator.route_with_copilotkit(
                        enhanced_prompt, 
                        context=integrated_context.to_dict() if integrated_context else {}
                    )
                    
                    # Add code suggestions to the response
                    suggestions_text = "\n\nCode suggestions:\n"
                    for i, suggestion in enumerate(code_suggestions[:3], 1):  # Limit to top 3
                        suggestions_text += f"{i}. {suggestion.get('explanation', 'Code suggestion')}\n"
                        suggestions_text += f"   ```{suggestion.get('language', 'python')}\n"
                        suggestions_text += f"   {suggestion.get('content', '')}\n"
                        suggestions_text += f"   ```\n"
                    copilot_response += suggestions_text
                    
                    return copilot_response
            # Use the user's chosen LLM for response generation
            response = orchestrator.route(enhanced_prompt, skill="conversation")
            
            # Get contextual suggestions if available
            try:
                contextual_suggestions = await orchestrator.get_contextual_suggestions(
                    message, 
                    integrated_context.to_dict() if integrated_context else {}
                )
                
                # Add contextual suggestions if available
                if contextual_suggestions:
                    suggestions_text = "\n\nSuggestions:\n"
                    for i, suggestion in enumerate(contextual_suggestions[:2], 1):  # Limit to top 2
                        if suggestion.get('actionable', True):
                            suggestions_text += f"• {suggestion.get('content', 'AI suggestion')}\n"
                    response += suggestions_text
            except Exception as e:
                logger.debug(f"Failed to get contextual suggestions: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"User's chosen LLM ({provider}:{model}) failed: {e}")
            return None
    
    async def _try_system_default_llms(
        self,
        enhanced_prompt: str,
        message: str,
        parsed_message: ParsedMessage,
        integrated_context: Optional[Any],
        active_instructions: List[Any]
    ) -> Optional[str]:
        """Try to generate response using system default LLMs in priority order."""
        try:
            from ai_karen_engine.llm_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            
            # Define system default LLMs in priority order
            default_providers = [
                "local:tinyllama-1.1b",  # Local TinyLlama fallback first
                "openai:gpt-3.5-turbo",
                "gemini:gemini-1.5-flash",
                "deepseek:deepseek-chat",
                "huggingface:microsoft/DialoGPT-large"
            ]
            
            for provider_model in default_providers:
                try:
                    provider, model = provider_model.split(":", 1)
                    model_id = f"{provider}:{model}"
                    model_info = orchestrator.registry.get(model_id)
                    
                    if not model_info:
                        logger.debug(f"System default model {model_id} not available")
                        continue
                    
                    logger.info(f"Trying system default LLM: {model_id}")
                    
                    # Use enhanced routing for response generation
                    response = await orchestrator.enhanced_route(
                        enhanced_prompt,
                        skill="conversation"
                    )
                    
                    if response:
                        logger.info(f"Successfully used system default LLM: {model_id}")
                        return response
                        
                except Exception as e:
                    logger.debug(f"System default LLM {provider_model} failed: {e}")
                    continue
            
            # If no specific models work, try generic routing
            logger.info("Trying generic LLM routing as final system default")
            response = orchestrator.route(enhanced_prompt, skill="conversation")
            return response
            
        except Exception as e:
            logger.error(f"All system default LLMs failed: {e}")
            
        # Try local model fallback as final attempt
        logger.info("Attempting local model fallback with TinyLlama")
        return await self._try_local_model_fallback(enhanced_prompt, message, parsed_message, integrated_context, active_instructions)
    
    async def _try_local_model_fallback(
        self,
        enhanced_prompt: str,
        message: str,
        parsed_message: ParsedMessage,
        integrated_context: Optional[Any],
        active_instructions: List[Any]
    ) -> Optional[str]:
        """Try to use local models as final fallback when all remote providers fail.
        
        Fallback hierarchy:
        1. llama-cpp models (GGUF files)
        2. transformers models (GPT-2, etc.)
        3. spaCy-based intelligent responses
        4. None (triggers degraded mode)
        """
        logger.info("Starting comprehensive local model fallback")
        
        # 1. Try llama-cpp models (GGUF)
        response = await self._try_llamacpp_models(enhanced_prompt, message)
        if response:
            return response
        
        # 2. Try transformers models
        response = await self._try_transformers_models(enhanced_prompt, message)
        if response:
            return response
        
        # 3. Try spaCy-based intelligent responses
        response = await self._try_spacy_intelligent_response(enhanced_prompt, message, parsed_message)
        if response:
            return response
        
        # 4. All local models failed
        logger.error("All local model fallbacks failed - system should enter degraded mode")
        return None
    
    async def _try_llamacpp_models(self, enhanced_prompt: str, message: str) -> Optional[str]:
        """Try to use llama-cpp models (GGUF files)."""
        try:
            from pathlib import Path
            from ai_karen_engine.inference.llamacpp_runtime import LlamaCppRuntime
            
            if not LlamaCppRuntime.is_available():
                logger.debug("llama-cpp-python not available")
                return None
            
            models_dir = Path("models/llama-cpp")
            if not models_dir.exists():
                logger.debug("llama-cpp models directory not found")
                return None
            
            # Try all GGUF files in the directory
            gguf_files = list(models_dir.glob("*.gguf"))
            logger.info(f"Found {len(gguf_files)} GGUF files to try")
            
            for gguf_file in gguf_files:
                try:
                    logger.info(f"Trying llama-cpp model: {gguf_file.name}")
                    
                    # Try with conservative settings first
                    runtime = LlamaCppRuntime(
                        model_path=str(gguf_file),
                        n_ctx=512,  # Small context to reduce memory usage
                        n_batch=128,  # Small batch size
                        n_gpu_layers=0,  # CPU only for compatibility
                        verbose=False
                    )
                    
                    if not runtime.is_loaded():
                        logger.warning(f"Failed to load {gguf_file.name}")
                        continue
                    
                    # Generate response
                    response = runtime.generate(
                        prompt=enhanced_prompt,
                        max_tokens=128,  # Shorter response for fallback
                        temperature=0.7,
                        stream=False
                    )
                    
                    if response and response.strip():
                        logger.info(f"✅ Successfully used llama-cpp model: {gguf_file.name}")
                        return response.strip()
                        
                except Exception as e:
                    logger.debug(f"llama-cpp model {gguf_file.name} failed: {e}")
                    continue
            
            logger.info("No working llama-cpp models found")
            return None
            
        except Exception as e:
            logger.debug(f"llama-cpp fallback failed: {e}")
            return None
    
    async def _try_transformers_models(self, enhanced_prompt: str, message: str) -> Optional[str]:
        """Try to use transformers models (GPT-2, etc.)."""
        try:
            from pathlib import Path
            
            # Check if transformers is available
            try:
                import transformers
                from transformers import AutoTokenizer, AutoModelForCausalLM
            except ImportError:
                logger.debug("transformers library not available")
                return None
            
            models_dir = Path("models/transformers")
            if not models_dir.exists():
                logger.debug("transformers models directory not found")
                return None
            
            # Try all model directories
            model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
            logger.info(f"Found {len(model_dirs)} transformers models to try")
            
            for model_dir in model_dirs:
                try:
                    logger.info(f"Trying transformers model: {model_dir.name}")
                    
                    # Load tokenizer and model
                    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
                    model = AutoModelForCausalLM.from_pretrained(str(model_dir))
                    
                    # Add pad token if not present
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    
                    # Encode input
                    inputs = tokenizer.encode(enhanced_prompt, return_tensors="pt", max_length=512, truncation=True)
                    
                    # Generate response
                    import torch
                    with torch.no_grad():
                        outputs = model.generate(
                            inputs,
                            max_length=inputs.shape[1] + 64,  # Short response for fallback
                            temperature=0.7,
                            do_sample=True,
                            pad_token_id=tokenizer.eos_token_id,
                            num_return_sequences=1
                        )
                    
                    # Decode response
                    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    # Extract only the generated part
                    if response.startswith(enhanced_prompt):
                        response = response[len(enhanced_prompt):].strip()
                    
                    if response:
                        logger.info(f"✅ Successfully used transformers model: {model_dir.name}")
                        return response
                        
                except Exception as e:
                    logger.debug(f"transformers model {model_dir.name} failed: {e}")
                    continue
            
            logger.info("No working transformers models found")
            return None
            
        except Exception as e:
            logger.debug(f"transformers fallback failed: {e}")
            return None
    
    async def _try_spacy_intelligent_response(
        self, 
        enhanced_prompt: str, 
        message: str, 
        parsed_message: ParsedMessage
    ) -> Optional[str]:
        """Generate intelligent responses using spaCy NLP analysis."""
        try:
            import spacy
            
            # Load spaCy model
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.debug("spaCy model en_core_web_sm not available")
                return None
            
            logger.info("Using spaCy for intelligent response generation")
            
            # Analyze the message
            doc = nlp(message)
            
            # Extract key information
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            pos_tags = [(token.text, token.pos_) for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ']]
            
            # Determine response type based on analysis
            response_parts = []
            
            # Greeting detection
            greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
            if any(greeting in message.lower() for greeting in greetings):
                response_parts.append("Hello! I'm here to help you.")
            
            # Question detection
            if message.strip().endswith('?') or any(word in message.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
                if entities:
                    entity_text = entities[0][0]
                    response_parts.append(f"I understand you're asking about {entity_text}.")
                else:
                    response_parts.append("That's an interesting question.")
                
                response_parts.append("While I'm running in local mode with limited capabilities, I can still help with basic information and tasks.")
            
            # Task/request detection
            elif any(word in message.lower() for word in ['help', 'create', 'make', 'build', 'write', 'generate']):
                response_parts.append("I'd be happy to help with that task.")
                if entities:
                    entity_text = entities[0][0]
                    response_parts.append(f"I notice you mentioned {entity_text}.")
                response_parts.append("I'm currently running in local mode, so I can provide basic assistance and guidance.")
            
            # Entity-based responses
            elif entities:
                entity_text, entity_type = entities[0]
                if entity_type == "PERSON":
                    response_parts.append(f"I see you mentioned {entity_text}.")
                elif entity_type in ["ORG", "GPE"]:
                    response_parts.append(f"You're referring to {entity_text}.")
                else:
                    response_parts.append(f"I notice you mentioned {entity_text}.")
            
            # Default response
            if not response_parts:
                response_parts.append("I understand your message.")
                if pos_tags:
                    key_words = [word for word, pos in pos_tags[:3]]
                    response_parts.append(f"I can see this relates to {', '.join(key_words)}.")
                response_parts.append("I'm currently running in local mode with spaCy-based processing.")
            
            # Add helpful context
            response_parts.append("How can I assist you further?")
            
            response = " ".join(response_parts)
            logger.info("✅ Generated spaCy-based intelligent response")
            return response
            
        except Exception as e:
            logger.debug(f"spaCy intelligent response failed: {e}")
            return None
    
    async def _build_enhanced_prompt(
        self,
        message: str,
        integrated_context: Optional[Any],
        active_instructions: List[Any]
    ) -> str:
        """Build enhanced prompt with instructions and context."""
        prompt_parts = []
        
        # Add active instructions to prompt
        if active_instructions:
            # Create instruction context for prompt enhancement
            instruction_context = InstructionContext(
                user_id="",  # Will be filled by caller
                conversation_id="",  # Will be filled by caller
                active_instructions=active_instructions
            )
            
            enhanced_prompt = await self.instruction_processor.apply_instructions_to_prompt(
                message, active_instructions, instruction_context
            )
            prompt_parts.append(enhanced_prompt)
        else:
            prompt_parts.append(message)
        
        # Add integrated context if available
        if integrated_context:
            if integrated_context.primary_context:
                prompt_parts.insert(-1, f"CONTEXT:\n{integrated_context.primary_context}")
            
            if integrated_context.supporting_context:
                prompt_parts.insert(-1, f"ADDITIONAL INFO:\n{integrated_context.supporting_context}")
        
        return "\n\n".join(prompt_parts)
    
    async def _generate_enhanced_fallback_response(
        self,
        message: str,
        parsed_message: ParsedMessage,
        integrated_context: Optional[Any],
        active_instructions: List[Any]
    ) -> str:
        """Generate enhanced fallback response with instruction awareness."""
        # Simulate AI processing delay
        await asyncio.sleep(0.5)
        
        response_parts = []
        
        # Acknowledge instructions if present
        if active_instructions:
            high_priority_instructions = [
                inst for inst in active_instructions 
                if inst.priority.value == "high"
            ]
            
            if high_priority_instructions:
                response_parts.append("I'll keep your instructions in mind:")
                for inst in high_priority_instructions[:2]:  # Limit to top 2
                    response_parts.append(f"- {inst.content}")
                response_parts.append("")  # Empty line
        
        # Build contextual response
        context_info = ""
        if integrated_context and integrated_context.items_included:
            context_types = set(item.type.value for item in integrated_context.items_included)
            if context_types:
                context_info = f" (Using context: {', '.join(context_types)})"
        
        # Add entity information
        entity_info = ""
        if parsed_message.entities:
            entity_info = f" I noticed {len(parsed_message.entities)} important entities in your message."
        
        # Add attachment information
        attachment_info = ""
        if (integrated_context and 
            any(item.type.value == "attachments" for item in integrated_context.items_included)):
            attachment_info = " I've also processed your file attachments."
        
        # Main response
        main_response = f"I understand your message: '{message}'{context_info}.{entity_info}{attachment_info}"
        response_parts.append(main_response)
        
        # Add fallback notice if needed
        if parsed_message.used_fallback:
            response_parts.append("(Note: I processed your message using fallback parsing.)")
        
        # Add context summary if available
        if integrated_context and integrated_context.context_summary:
            response_parts.append(f"Context: {integrated_context.context_summary}")
        
        response_parts.append("How can I help you further?")
        
        return " ".join(response_parts)

    async def _generate_ai_response(
        self,
        message: str,
        parsed_message: ParsedMessage,
        embeddings: List[float],
        context: Optional[Dict[str, Any]],
        processing_context: ProcessingContext
    ) -> str:
        """Generate AI response using the processed information with CopilotKit integration."""
        # Check for code execution requests
        code_execution_result = await self._handle_code_execution_request(
            message, processing_context
        )
        if code_execution_result:
            return code_execution_result
        
        # Check for tool execution requests
        tool_execution_result = await self._handle_tool_execution_request(
            message, processing_context
        )
        if tool_execution_result:
            return tool_execution_result
        
        # Try to use CopilotKit for enhanced AI response generation
        try:
            from ai_karen_engine.llm_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            
            # Check if this is a code-related request for CopilotKit code assistance
            if self._is_code_related_message(message):
                # Get code suggestions from CopilotKit if available
                code_suggestions = await orchestrator.get_code_suggestions(
                    message, 
                    language=self._detect_programming_language(message)
                )
                
                if code_suggestions:
                    # Use CopilotKit for code-related responses
                    copilot_response = orchestrator.route_with_copilotkit(
                        message, 
                        context=context
                    )
                    
                    # Add code suggestions to the response
                    if code_suggestions:
                        suggestions_text = "\n\nCode suggestions:\n"
                        for i, suggestion in enumerate(code_suggestions[:3], 1):  # Limit to top 3
                            suggestions_text += f"{i}. {suggestion.get('explanation', 'Code suggestion')}\n"
                            suggestions_text += f"   ```{suggestion.get('language', 'python')}\n"
                            suggestions_text += f"   {suggestion.get('content', '')}\n"
                            suggestions_text += f"   ```\n"
                        copilot_response += suggestions_text
                    
                    return copilot_response
            
            # Get contextual suggestions from CopilotKit
            contextual_suggestions = await orchestrator.get_contextual_suggestions(
                message, 
                context or {}
            )
            
            # Use CopilotKit for enhanced response generation
            copilot_response = orchestrator.route_with_copilotkit(
                message, 
                context=context
            )
            
            # Add contextual suggestions if available
            if contextual_suggestions:
                suggestions_text = "\n\nSuggestions:\n"
                for i, suggestion in enumerate(contextual_suggestions[:2], 1):  # Limit to top 2
                    if suggestion.get('actionable', True):
                        suggestions_text += f"• {suggestion.get('content', 'AI suggestion')}\n"
                copilot_response += suggestions_text
            
            return copilot_response
            
        except Exception as e:
            logger.warning(f"CopilotKit integration failed, falling back to standard response: {e}")
            # Fall back to standard response generation
            pass
        
        # Standard response generation (fallback)
        # Build context string
        context_info = ""
        if context and context.get("entities"):
            entities = []
            for ent in context["entities"]:
                if isinstance(ent, dict):
                    entities.append(f"{ent.get('label', 'UNKNOWN')}: {ent.get('text', '')}")
                elif isinstance(ent, (list, tuple)) and len(ent) >= 2:
                    entities.append(f"{ent[1]}: {ent[0]}")
            if entities:
                context_info = f" (Entities detected: {', '.join(entities)})"
        
        # Add attachment information if available
        attachment_info = ""
        if context and context.get("attachments"):
            attachments = context["attachments"]
            if attachments.get("total_files", 0) > 0:
                attachment_info = f" I also processed {attachments['total_files']} file attachment(s)."
                
                # Add extracted content summary
                if attachments.get("extracted_content"):
                    content_count = len(attachments["extracted_content"])
                    attachment_info += f" I extracted content from {content_count} file(s)."
                
                # Add multimedia analysis summary
                if attachments.get("multimedia_analysis"):
                    media_count = len(attachments["multimedia_analysis"])
                    attachment_info += f" I analyzed {media_count} multimedia file(s)."
        
        # Simulate AI processing delay
        await asyncio.sleep(0.5)
        
        # Generate a contextual response
        response = f"I understand your message: '{message}'{context_info}.{attachment_info} "
        
        if parsed_message.entities:
            response += f"I noticed {len(parsed_message.entities)} important entities in your message. "
        
        if parsed_message.used_fallback:
            response += "I processed your message using fallback parsing. "
        
        response += "How can I help you further?"
        
        return response
    
    def _is_code_related_message(self, message: str) -> bool:
        """Determine if a message is code-related."""
        code_indicators = [
            "code", "function", "class", "method", "variable", "debug", "error",
            "syntax", "compile", "import", "export", "def ", "class ", "function ",
            "```", "python", "javascript", "typescript", "java", "c++", "rust",
            "go", "php", "ruby", "swift", "kotlin", "scala", "html", "css", "sql",
            "algorithm", "programming", "coding", "script", "api", "library",
            "framework", "database", "query", "regex", "json", "xml", "yaml"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in code_indicators)
    
    def _detect_programming_language(self, message: str) -> str:
        """Detect the programming language mentioned in the message."""
        language_patterns = {
            "python": ["python", "py", "django", "flask", "pandas", "numpy"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "typescript": ["typescript", "ts"],
            "java": ["java", "spring", "maven", "gradle"],
            "cpp": ["c++", "cpp", "cxx"],
            "c": ["c language", " c "],
            "rust": ["rust", "cargo"],
            "go": ["golang", "go lang"],
            "php": ["php", "laravel", "symfony"],
            "ruby": ["ruby", "rails"],
            "swift": ["swift", "ios"],
            "kotlin": ["kotlin", "android"],
            "scala": ["scala"],
            "html": ["html", "markup"],
            "css": ["css", "scss", "sass"],
            "sql": ["sql", "mysql", "postgresql", "sqlite"],
            "bash": ["bash", "shell", "sh"],
            "powershell": ["powershell", "ps1"]
        }
        
        message_lower = message.lower()
        
        for language, patterns in language_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return language
        
        # Default to Python if no specific language detected
        return "python"
    
    async def _handle_code_execution_request(
        self,
        message: str,
        processing_context: ProcessingContext
    ) -> Optional[str]:
        """Handle code execution requests detected in the message."""
        if not self.code_execution_service:
            return None
        
        # Simple pattern matching for code execution requests
        import re
        
        # Look for code blocks
        code_block_pattern = r'```(\w+)?\n(.*?)\n```'
        code_matches = re.findall(code_block_pattern, message, re.DOTALL)
        
        if not code_matches:
            # Look for inline code execution requests
            execution_patterns = [
                r'execute\s+(?:this\s+)?(\w+)\s+code[:\s]+(.*)',
                r'run\s+(?:this\s+)?(\w+)[:\s]+(.*)',
                r'calculate[:\s]+(.*)',
                r'eval(?:uate)?[:\s]+(.*)'
            ]
            
            for pattern in execution_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        language, code = match.groups()
                        code_matches = [(language.lower(), code.strip())]
                    else:
                        # Default to Python for calculations
                        code_matches = [('python', match.group(1).strip())]
                    break
        
        if not code_matches:
            return None
        
        try:
            # Execute the first code block found
            language_str, code = code_matches[0]
            
            # Map language strings to CodeLanguage enum
            language_mapping = {
                'python': 'python',
                'py': 'python',
                'javascript': 'javascript',
                'js': 'javascript',
                'bash': 'bash',
                'sh': 'bash',
                'sql': 'sql',
                '': 'python'  # Default to Python
            }
            
            language = language_mapping.get(language_str.lower(), 'python')
            
            # Import required classes
            from ai_karen_engine.chat.code_execution_service import (
                CodeExecutionRequest, CodeLanguage, SecurityLevel
            )
            
            # Create execution request
            exec_request = CodeExecutionRequest(
                code=code,
                language=CodeLanguage(language),
                user_id=processing_context.user_id,
                conversation_id=processing_context.conversation_id,
                security_level=SecurityLevel.STRICT,
                metadata={"triggered_by_chat": True}
            )
            
            # Execute code
            result = await self.code_execution_service.execute_code(exec_request)
            
            if result.success and result.result:
                execution_result = result.result
                response = f"I executed your {language} code:\n\n"
                
                if execution_result.stdout:
                    response += f"**Output:**\n```\n{execution_result.stdout}\n```\n\n"
                
                if execution_result.stderr:
                    response += f"**Errors:**\n```\n{execution_result.stderr}\n```\n\n"
                
                response += f"**Execution completed in {execution_result.execution_time:.2f} seconds**"
                
                if execution_result.visualization_data:
                    response += "\n\n*Visualization data available*"
                
                return response
            else:
                return f"I attempted to execute your {language} code, but encountered an error: {result.message}"
                
        except Exception as e:
            logger.error(f"Code execution handling failed: {e}")
            return f"I detected a code execution request, but encountered an error: {str(e)}"
    
    async def _handle_tool_execution_request(
        self,
        message: str,
        processing_context: ProcessingContext
    ) -> Optional[str]:
        """Handle tool execution requests detected in the message."""
        if not self.tool_integration_service:
            return None
        
        # Simple pattern matching for tool execution requests
        import re
        
        # Look for tool execution patterns
        tool_patterns = [
            r'use\s+(?:the\s+)?(\w+)\s+tool\s+(?:with\s+|to\s+)?(.*)',
            r'run\s+(?:the\s+)?(\w+)\s+tool\s+(?:with\s+|on\s+)?(.*)',
            r'execute\s+(?:the\s+)?(\w+)\s+tool\s+(?:with\s+)?(.*)',
            r'calculate\s+(.*)',  # For calculator tool
            r'analyze\s+(?:this\s+)?text[:\s]+(.*)',  # For text analyzer
        ]
        
        tool_name = None
        tool_params = {}
        
        for pattern in tool_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                if pattern.endswith(r'calculate\s+(.*)'):
                    tool_name = "calculator"
                    tool_params = {"expression": match.group(1).strip()}
                elif pattern.endswith(r'analyze\s+(?:this\s+)?text[:\s]+(.*)'):
                    tool_name = "text_analyzer"
                    tool_params = {"text": match.group(1).strip(), "analysis_type": "basic"}
                else:
                    tool_name = match.group(1).lower()
                    param_text = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # Simple parameter parsing
                    if tool_name == "calculator" and param_text:
                        tool_params = {"expression": param_text}
                    elif tool_name == "text_analyzer" and param_text:
                        tool_params = {"text": param_text, "analysis_type": "basic"}
                
                break
        
        if not tool_name:
            return None
        
        try:
            # Import required classes
            from ai_karen_engine.chat.tool_integration_service import ToolExecutionContext
            
            # Create execution context
            context = ToolExecutionContext(
                user_id=processing_context.user_id,
                conversation_id=processing_context.conversation_id,
                metadata={"triggered_by_chat": True}
            )
            
            # Execute tool
            result = await self.tool_integration_service.execute_tool(
                tool_name, tool_params, context
            )
            
            if result.success:
                response = f"I used the **{tool_name}** tool:\n\n"
                
                # Format result based on tool type
                if tool_name == "calculator":
                    calc_result = result.result
                    response += f"**Expression:** {calc_result.get('expression', 'N/A')}\n"
                    response += f"**Result:** {calc_result.get('result', 'N/A')}\n"
                    response += f"**Type:** {calc_result.get('type', 'N/A')}"
                
                elif tool_name == "text_analyzer":
                    analysis = result.result
                    response += f"**Text Length:** {analysis.get('text_length', 0)} characters\n"
                    response += f"**Word Count:** {analysis.get('word_count', 0)} words\n"
                    response += f"**Sentence Count:** {analysis.get('sentence_count', 0)} sentences"
                    
                    if 'sentiment' in analysis:
                        response += f"\n**Sentiment:** {analysis['sentiment']}"
                    
                    if 'keywords' in analysis:
                        keywords = analysis['keywords'][:5]  # Top 5 keywords
                        keyword_list = [f"{kw['word']} ({kw['frequency']})" for kw in keywords]
                        response += f"\n**Top Keywords:** {', '.join(keyword_list)}"
                
                else:
                    # Generic result formatting
                    response += f"**Result:** {result.result}"
                
                response += f"\n\n*Execution completed in {result.execution_time:.2f} seconds*"
                
                return response
            else:
                return f"I attempted to use the **{tool_name}** tool, but encountered an error: {result.error_message}"
                
        except Exception as e:
            logger.error(f"Tool execution handling failed: {e}")
            return f"I detected a tool execution request, but encountered an error: {str(e)}"
    
    async def _process_attachments(
        self,
        attachment_ids: List[str],
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Process file attachments and extract relevant information."""
        if not self.file_attachment_service:
            return {"error": "File attachment service not available"}
        
        attachment_context = {
            "files": [],
            "extracted_content": [],
            "multimedia_analysis": [],
            "total_files": len(attachment_ids),
            "processing_errors": []
        }
        
        for attachment_id in attachment_ids:
            try:
                # Get file information
                file_info = await self.file_attachment_service.get_file_info(attachment_id)
                if not file_info:
                    attachment_context["processing_errors"].append(
                        f"File {attachment_id} not found"
                    )
                    continue
                
                # Add basic file info
                file_data = {
                    "file_id": attachment_id,
                    "processing_status": file_info.processing_status.value,
                    "extracted_content": file_info.extracted_content,
                    "analysis_results": file_info.analysis_results
                }
                
                attachment_context["files"].append(file_data)
                
                # Add extracted content if available
                if file_info.extracted_content:
                    attachment_context["extracted_content"].append({
                        "file_id": attachment_id,
                        "content": file_info.extracted_content[:1000]  # Limit content size
                    })
                
                # Process multimedia if service is available and file is multimedia
                if (self.multimedia_service and 
                    file_info.analysis_results and 
                    attachment_id in self.file_attachment_service._file_metadata):
                    
                    metadata = self.file_attachment_service._file_metadata[attachment_id]
                    if metadata.file_type.value in ["image", "audio", "video"]:
                        try:
                            # Get basic multimedia analysis
                            multimedia_info = {
                                "file_id": attachment_id,
                                "media_type": metadata.file_type.value,
                                "basic_analysis": file_info.analysis_results
                            }
                            attachment_context["multimedia_analysis"].append(multimedia_info)
                            
                        except Exception as e:
                            logger.warning(f"Multimedia analysis failed for {attachment_id}: {e}")
                            attachment_context["processing_errors"].append(
                                f"Multimedia analysis failed for {attachment_id}: {str(e)}"
                            )
                
            except Exception as e:
                logger.error(f"Failed to process attachment {attachment_id}: {e}")
                attachment_context["processing_errors"].append(
                    f"Failed to process {attachment_id}: {str(e)}"
                )
        
        return attachment_context
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        avg_processing_time = (
            sum(self._processing_times) / len(self._processing_times)
            if self._processing_times else 0.0
        )
        
        success_rate = (
            self._successful_requests / self._total_requests
            if self._total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": success_rate,
            "retry_attempts": self._retry_attempts,
            "fallback_usage": self._fallback_usage,
            "avg_processing_time": avg_processing_time,
            "active_contexts": len(self._active_contexts),
            "recent_processing_times": self._processing_times[-10:] if self._processing_times else []
        }
    
    def get_active_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active processing contexts."""
        return {
            correlation_id: {
                "user_id": ctx.user_id,
                "conversation_id": ctx.conversation_id,
                "status": ctx.status.value,
                "retry_count": ctx.retry_count,
                "processing_start": ctx.processing_start.isoformat() if ctx.processing_start else None,
                "duration": (
                    (datetime.utcnow() - ctx.processing_start).total_seconds()
                    if ctx.processing_start else 0
                )
            }
            for correlation_id, ctx in self._active_contexts.items()
        }
    
    def reset_stats(self):
        """Reset processing statistics."""
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._retry_attempts = 0
        self._fallback_usage = 0
        self._processing_times.clear()
        logger.info("ChatOrchestrator statistics reset")
