"""
Production-ready ChatOrchestrator with spaCy and DistilBERT integration.

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
    from pydantic import BaseModel, Field
except ImportError:
    from ..pydantic_stub import BaseModel, Field

from ..services.nlp_service_manager import nlp_service_manager
from ..services.spacy_service import ParsedMessage
from ..models.shared_types import ChatMessage, MessageRole

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
        retry_config: Optional[RetryConfig] = None,
        timeout_seconds: float = 30.0,
        enable_monitoring: bool = True
    ):
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
        
        logger.info("ChatOrchestrator initialized with NLP integration")
    
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
        
        try:
            # Process with retry logic
            result = await self._process_with_retry(request, context)
            
            processing_time = time.time() - start_time
            self._processing_times.append(processing_time)
            
            if result.success:
                self._successful_requests += 1
                context.status = ProcessingStatus.COMPLETED
                
                return ChatResponse(
                    response=result.response or "",
                    correlation_id=context.correlation_id,
                    processing_time=processing_time,
                    used_fallback=result.used_fallback,
                    context_used=bool(result.context),
                    metadata={
                        "parsed_entities": len(result.parsed_message.entities) if result.parsed_message else 0,
                        "embedding_dimension": len(result.embeddings) if result.embeddings else 0,
                        "retry_count": context.retry_count,
                        **context.metadata
                    }
                )
            else:
                self._failed_requests += 1
                context.status = ProcessingStatus.FAILED
                
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
                        "retry_count": context.retry_count
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
        
        try:
            # Send initial metadata chunk
            yield ChatStreamChunk(
                type="metadata",
                content="",
                correlation_id=context.correlation_id,
                metadata={
                    "status": "processing",
                    "user_id": context.user_id,
                    "conversation_id": context.conversation_id
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
        """Internal message processing with NLP services."""
        start_time = time.time()
        parsed_message = None
        embeddings = None
        retrieved_context = None
        used_fallback = False
        
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
            
            # Step 2: Generate embeddings with DistilBERT
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
            
            # Step 3: Retrieve context (if enabled)
            if request.include_context:
                try:
                    retrieved_context = await self._retrieve_context(
                        embeddings,
                        parsed_message,
                        request.user_id,
                        request.conversation_id
                    )
                    logger.debug(f"Retrieved context: {len(retrieved_context.get('memories', []))} memories")
                    
                except Exception as e:
                    logger.warning(f"Context retrieval failed: {e}")
                    # Don't fail the entire request for context retrieval errors
                    retrieved_context = {}
            
            # Step 4: Generate AI response
            try:
                ai_response = await self._generate_ai_response(
                    request.message,
                    parsed_message,
                    embeddings,
                    retrieved_context,
                    context
                )
                
                return ProcessingResult(
                    success=True,
                    response=ai_response,
                    parsed_message=parsed_message,
                    embeddings=embeddings,
                    context=retrieved_context,
                    processing_time=time.time() - start_time,
                    used_fallback=used_fallback,
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
        """Retrieve relevant context for the message."""
        # This is a placeholder for memory/context retrieval
        # In the actual implementation, this would integrate with:
        # - Memory storage system
        # - Vector similarity search
        # - Conversation history
        # - User preferences
        
        context = {
            "memories": [],
            "conversation_history": [],
            "user_preferences": {},
            "entities": [{"text": ent[0], "label": ent[1]} for ent in parsed_message.entities],
            "embedding_similarity_threshold": 0.7
        }
        
        # Simulate context retrieval delay
        await asyncio.sleep(0.1)
        
        return context
    
    async def _generate_ai_response(
        self,
        message: str,
        parsed_message: ParsedMessage,
        embeddings: List[float],
        context: Optional[Dict[str, Any]],
        processing_context: ProcessingContext
    ) -> str:
        """Generate AI response using the processed information."""
        # This is a placeholder for AI model integration
        # In the actual implementation, this would integrate with:
        # - LLM service (OpenAI, local models, etc.)
        # - Context building from retrieved memories
        # - Response generation with streaming support
        
        # Build context string
        context_info = ""
        if context and context.get("entities"):
            entities = [f"{ent['label']}: {ent['text']}" for ent in context["entities"]]
            if entities:
                context_info = f" (Entities detected: {', '.join(entities)})"
        
        # Simulate AI processing delay
        await asyncio.sleep(0.5)
        
        # Generate a contextual response
        response = f"I understand your message: '{message}'{context_info}. "
        
        if parsed_message.entities:
            response += f"I noticed {len(parsed_message.entities)} important entities in your message. "
        
        if parsed_message.used_fallback:
            response += "I processed your message using fallback parsing. "
        
        response += "How can I help you further?"
        
        return response
    
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