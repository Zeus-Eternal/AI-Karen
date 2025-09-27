"""
Chat Runtime API Routes
Unified chat endpoint for all platforms (Web UI, Streamlit, Desktop)
"""

import json
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.response.factory import get_global_orchestrator
from ai_karen_engine.integrations.llm_registry import get_registry

logger = get_logger(__name__)
router = APIRouter(tags=["chat-runtime"])


# Request/Response Models
class ChatMessage(BaseModel):
    """Chat message model"""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Tool call model"""

    id: str = Field(..., description="Unique tool call ID")
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    result: Optional[Any] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Tool execution error")
    execution_time: Optional[float] = Field(
        None, description="Tool execution time in seconds"
    )
    status: str = Field(default="pending", description="Tool execution status")


class MemoryOperation(BaseModel):
    """Memory operation model"""

    id: str = Field(..., description="Unique operation ID")
    operation_type: str = Field(
        ..., description="Operation type: store, retrieve, update, delete"
    )
    memory_tier: str = Field(
        ..., description="Memory tier: short_term, long_term, persistent"
    )
    content: Dict[str, Any] = Field(
        default_factory=dict, description="Operation content"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = Field(default=True, description="Operation success status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Operation metadata"
    )


class ChatRuntimeRequest(BaseModel):
    """Chat runtime request model"""

    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Chat context"
    )
    tools: Optional[List[str]] = Field(
        default_factory=list, description="Available tools"
    )
    memory_context: Optional[str] = Field(None, description="Memory context identifier")
    user_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="User preferences"
    )
    platform: Optional[str] = Field(default="web", description="Platform identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    stream: bool = Field(default=True, description="Enable streaming response")
    model: Optional[str] = Field(
        default=None, description="Explicit model identifier requested by the client"
    )
    provider: Optional[str] = Field(
        default=None, description="Explicit provider requested by the client"
    )
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=2.0, description="Requested sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None, gt=0, description="Requested maximum tokens for the response"
    )


class ChatRuntimeResponse(BaseModel):
    """Chat runtime response model"""

    content: str = Field(..., description="Response content")
    tool_calls: List[ToolCall] = Field(
        default_factory=list, description="Tool calls made"
    )
    memory_operations: List[MemoryOperation] = Field(
        default_factory=list, description="Memory operations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatError(BaseModel):
    """Chat error model"""

    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Error details"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Dependency functions
async def get_request_metadata(request: Request) -> Dict[str, Any]:
    """Extract request metadata"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "platform": request.headers.get("x-platform", "web"),
        "client_id": request.headers.get("x-client-id", "unknown"),
        "correlation_id": request.headers.get("x-correlation-id", str(uuid.uuid4())),
    }


async def validate_chat_request(request: ChatRuntimeRequest) -> ChatRuntimeRequest:
    """Validate chat request"""
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty"
        )

    if len(request.message) > 10000:  # 10KB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message too long (max 10KB)",
        )

    if request.max_tokens is not None and request.max_tokens <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must be greater than zero",
        )

    return request


def _extract_generation_preferences(
    request: ChatRuntimeRequest,
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Derive generation hints from the request and associated metadata."""

    hints: Dict[str, Any] = {}

    def _first_non_empty(values: Iterable[Optional[str]]) -> Optional[str]:
        for value in values:
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned:
                    return cleaned
        return None

    user_prefs = request.user_preferences or {}
    context_prefs = {}
    if request.context and isinstance(request.context, dict):
        context_prefs = request.context.get("llm_preferences", {}) or {}

    provider = _first_non_empty(
        (
            request.provider,
            user_prefs.get("preferred_llm_provider"),
            context_prefs.get("preferred_llm_provider"),
        )
    )
    if provider:
        hints["provider"] = provider

    model = _first_non_empty(
        (
            request.model,
            user_prefs.get("preferred_model"),
            context_prefs.get("preferred_model"),
        )
    )
    if model:
        hints["model"] = model

    temperature = request.temperature
    if temperature is None:
        temp_from_prefs = user_prefs.get("temperature") if isinstance(user_prefs, dict) else None
        if isinstance(temp_from_prefs, (int, float)):
            temperature = float(temp_from_prefs)
    if temperature is not None:
        hints["temperature"] = temperature

    max_tokens = request.max_tokens
    if max_tokens is None:
        tokens_from_prefs = user_prefs.get("max_tokens") if isinstance(user_prefs, dict) else None
        if isinstance(tokens_from_prefs, int) and tokens_from_prefs > 0:
            max_tokens = tokens_from_prefs
    if max_tokens is not None:
        hints["max_tokens"] = max_tokens

    return provider, model, hints


# Orchestrator dependency
@lru_cache
def get_chat_orchestrator() -> ChatOrchestrator:
    """Return a cached ChatOrchestrator instance."""
    from ai_karen_engine.chat.memory_processor import MemoryProcessor
    from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
    from ai_karen_engine.database.memory_manager import MemoryManager
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    from ai_karen_engine.core.milvus_client import MilvusClient
    from ai_karen_engine.core import default_models

    try:
        # Initialize required components for memory manager
        db_client = MultiTenantPostgresClient()
        milvus_client = MilvusClient()
        
        # Load embedding manager (async operation handled gracefully)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                embedding_manager = None
            else:
                loop.run_until_complete(default_models.load_default_models())
                embedding_manager = default_models.get_embedding_manager()
        except Exception as e:
            logger.warning(f"Failed to load embedding manager: {e}")
            embedding_manager = None
        
        # Create memory manager instance
        memory_manager = MemoryManager(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=embedding_manager
        )
    except Exception as e:
        logger.warning(f"Failed to create memory manager: {e}")
        memory_manager = None

    memory_processor = MemoryProcessor(
        spacy_service=nlp_service_manager.spacy_service,
        distilbert_service=nlp_service_manager.distilbert_service,
        memory_manager=memory_manager,
    )
    return ChatOrchestrator(memory_processor=memory_processor)


# Chat Runtime Routes
@router.post("/chat/runtime", response_model=ChatRuntimeResponse)
async def chat_runtime(
    request: ChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> ChatRuntimeResponse:
    """
    Main chat runtime endpoint for non-streaming responses
    """
    try:
        start_time = time.time()
        correlation_id = request_metadata.get("correlation_id")
        conversation_id = request.conversation_id or str(uuid.uuid4())

        logger.info(
            "Chat runtime request received",
            extra={
                "user_id": user_context.get("user_id"),
                "platform": request.platform,
                "correlation_id": correlation_id,
                "message_length": len(request.message),
            },
        )

        # Route via LLMRegistry.get_provider_with_routing to select provider/model
        reg = get_registry()
        _routed = await reg.get_provider_with_routing(
            user_ctx={"user_id": user_context.get("user_id", "anon")},
            query=request.message,
            task_type="chat",
            khrp_step="output_rendering",
            requirements={}
        )
        kire_decision = _routed.get("decision")

        user_provider, user_model, generation_hints = _extract_generation_preferences(request)
        preferred_provider = user_provider or (
            getattr(kire_decision, "provider", None) if kire_decision else None
        )
        preferred_model = user_model or (
            getattr(kire_decision, "model", None) if kire_decision else None
        )

        metadata_payload: Dict[str, Any] = {
            **(request.context or {}),
            "platform": request.platform,
            "request_metadata": request_metadata,
        }
        if generation_hints:
            metadata_payload["requested_generation"] = generation_hints
        if preferred_provider:
            metadata_payload["preferred_llm_provider"] = preferred_provider
        if preferred_model:
            metadata_payload["preferred_model"] = preferred_model
        if kire_decision:
            metadata_payload["kire"] = {
                "provider": kire_decision.provider,
                "model": kire_decision.model,
                "reason": kire_decision.reasoning,
                "confidence": kire_decision.confidence,
                "fallback_chain": kire_decision.fallback_chain,
            }

        chat_request = ChatRequest(
            message=request.message,
            user_id=user_context.get("user_id"),
            conversation_id=conversation_id,
            session_id=correlation_id,
            stream=False,
            include_context=True,
            metadata=metadata_payload,
        )

        orchestrator_response = await chat_orchestrator.process_message(chat_request)

        latency_ms = (time.time() - start_time) * 1000

        response_metadata: Dict[str, Any] = {
            "platform": request.platform,
            "correlation_id": orchestrator_response.correlation_id,
            "user_id": user_context.get("user_id"),
            "processing_time": orchestrator_response.processing_time,
            "latency_ms": latency_ms,
            **orchestrator_response.metadata,
        }
        if generation_hints and "requested_generation" not in response_metadata:
            response_metadata["requested_generation"] = generation_hints
        if preferred_provider and "preferred_llm_provider" not in response_metadata:
            response_metadata["preferred_llm_provider"] = preferred_provider
        if preferred_model and "preferred_model" not in response_metadata:
            response_metadata["preferred_model"] = preferred_model
        if kire_decision:
            response_metadata.setdefault("kire_metadata", {
                "provider": kire_decision.provider,
                "model": kire_decision.model,
                "reason": kire_decision.reasoning,
                "confidence": kire_decision.confidence,
            })

        response = ChatRuntimeResponse(
            content=orchestrator_response.response,
            conversation_id=conversation_id,
            metadata=response_metadata,
        )

        logger.info(
            "Chat runtime response generated",
            extra={
                "user_id": user_context.get("user_id"),
                "correlation_id": correlation_id,
                "response_length": len(response.content),
                "latency_ms": latency_ms,
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Chat runtime error",
            extra={
                "user_id": user_context.get("user_id"),
                "correlation_id": request_metadata.get("correlation_id"),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/chat/runtime/stream")
async def chat_runtime_stream(
    request: ChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> StreamingResponse:
    """
    Streaming chat runtime endpoint using Server-Sent Events
    """

    async def generate_stream():
        start_time = time.time()
        first_token_time = None
        token_count = 0
        correlation_id = request_metadata.get("correlation_id")
        conversation_id = request.conversation_id or str(uuid.uuid4())

        try:
            logger.info(
                "Chat runtime stream started",
                extra={
                    "user_id": user_context.get("user_id"),
                    "platform": request.platform,
                    "correlation_id": correlation_id,
                },
            )

            # KIRE routing for streaming via registry; send early metadata with selection
            reg = get_registry()
            _routed = await reg.get_provider_with_routing(
                user_ctx={"user_id": user_context.get("user_id", "anon")},
                query=request.message,
                task_type="chat",
                khrp_step="output_rendering",
                requirements={}
            )
            kire_decision = _routed.get("decision")

            user_provider, user_model, generation_hints = _extract_generation_preferences(request)
            preferred_provider = user_provider or (
                getattr(kire_decision, "provider", None) if kire_decision else None
            )
            preferred_model = user_model or (
                getattr(kire_decision, "model", None) if kire_decision else None
            )

            metadata_event = {
                "type": "metadata",
                "data": {
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                },
            }
            if generation_hints:
                metadata_event["data"]["requested_generation"] = generation_hints
            if preferred_provider:
                metadata_event["data"]["preferred_llm_provider"] = preferred_provider
            if preferred_model:
                metadata_event["data"]["preferred_model"] = preferred_model
            if kire_decision:
                metadata_event["data"]["kire"] = {
                    "provider": getattr(kire_decision, "provider", "unknown"),
                    "model": getattr(kire_decision, "model", "unknown"),
                    "reason": getattr(kire_decision, "reasoning", ""),
                    "confidence": getattr(kire_decision, "confidence", 0.0),
                    "fallback_chain": getattr(kire_decision, "fallback_chain", []),
                }

            yield f"data: {json.dumps(metadata_event)}\n\n"

            metadata_payload: Dict[str, Any] = {
                **(request.context or {}),
                "platform": request.platform,
                "request_metadata": request_metadata,
            }
            if generation_hints:
                metadata_payload["requested_generation"] = generation_hints
            if preferred_provider:
                metadata_payload["preferred_llm_provider"] = preferred_provider
            if preferred_model:
                metadata_payload["preferred_model"] = preferred_model
            if kire_decision:
                metadata_payload["kire"] = {
                    "provider": kire_decision.provider,
                    "model": kire_decision.model,
                    "reason": kire_decision.reasoning,
                    "confidence": kire_decision.confidence,
                    "fallback_chain": kire_decision.fallback_chain,
                }

            chat_request = ChatRequest(
                message=request.message,
                user_id=user_context.get("user_id"),
                conversation_id=conversation_id,
                session_id=correlation_id,
                stream=True,
                include_context=True,
                metadata=metadata_payload,
            )

            stream = await chat_orchestrator.process_message(chat_request)

            async for chunk in stream:
                if chunk.type == "content":
                    if first_token_time is None:
                        first_token_time = time.time()
                    token_count += 1
                    yield f"data: {json.dumps({'type': 'token', 'data': {'token': chunk.content}})}\n\n"
                elif chunk.type == "metadata":
                    yield f"data: {json.dumps({'type': 'metadata', 'data': chunk.metadata})}\n\n"
                elif chunk.type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': chunk.content, **chunk.metadata}})}\n\n"
                elif chunk.type == "complete":
                    total_latency = (time.time() - start_time) * 1000
                    first_latency = (
                        (first_token_time - start_time) * 1000
                        if first_token_time
                        else total_latency
                    )
                    completion_data = {
                        **chunk.metadata,
                        "total_tokens": token_count,
                        "latency_ms": total_latency,
                        "first_token_latency_ms": first_latency,
                    }
                    if generation_hints and "requested_generation" not in completion_data:
                        completion_data["requested_generation"] = generation_hints
                    if preferred_provider and "preferred_llm_provider" not in completion_data:
                        completion_data["preferred_llm_provider"] = preferred_provider
                    if preferred_model and "preferred_model" not in completion_data:
                        completion_data["preferred_model"] = preferred_model
                    yield f"data: {json.dumps({'type': 'complete', 'data': completion_data})}\n\n"

            logger.info(
                "Chat runtime stream completed",
                extra={
                    "user_id": user_context.get("user_id"),
                    "correlation_id": correlation_id,
                },
            )

        except Exception as e:
            logger.error(
                "Chat runtime stream error",
                extra={
                    "user_id": user_context.get("user_id"),
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Stream processing error'}})}\n\n"

    # Stream as Server-Sent Events and avoid gzip to reduce latency
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Encoding": "identity",  # Hint middleware/proxies not to compress
        },
    )


@router.post("/chat/runtime/stop")
async def stop_chat_generation(
    conversation_id: str,
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
) -> Dict[str, str]:
    """
    Stop ongoing chat generation
    """
    try:
        logger.info(
            "Chat generation stop requested",
            extra={
                "user_id": user_context.get("user_id"),
                "conversation_id": conversation_id,
                "correlation_id": request_metadata.get("correlation_id"),
            },
        )

        # TODO: Implement actual stop logic
        # This would involve cancelling ongoing LLM requests and tool executions

        return {"status": "stopped", "conversation_id": conversation_id}

    except Exception as e:
        logger.error(
            "Failed to stop chat generation",
            extra={
                "user_id": user_context.get("user_id"),
                "conversation_id": conversation_id,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop generation",
        )


@router.get("/chat/runtime/health")
async def chat_runtime_health() -> Dict[str, Any]:
    """
    Health check for chat runtime
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "chat-runtime",
        "version": "1.0.0",
    }


@router.post("/chat/runtime/response-core", response_model=ChatRuntimeResponse)
async def chat_runtime_response_core(
    request: ChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
) -> ChatRuntimeResponse:
    """
    Chat runtime endpoint using Response Core orchestrator
    
    This endpoint provides an alternative to the standard chat runtime
    using the Response Core orchestrator with local-first processing.
    """
    try:
        start_time = time.time()
        correlation_id = request_metadata.get("correlation_id")
        conversation_id = request.conversation_id or str(uuid.uuid4())
        user_id = user_context.get("user_id", "anonymous")

        logger.info(
            "Response Core chat runtime request received",
            extra={
                "user_id": user_id,
                "platform": request.platform,
                "correlation_id": correlation_id,
                "message_length": len(request.message),
            },
        )

        # Get Response Core orchestrator
        response_orchestrator = get_global_orchestrator(user_id=user_id)
        
        # Process through Response Core using the ResponseOrchestrator API
        ui_caps = {
            "platform": request.platform,
            "conversation_id": conversation_id,
            "tools": request.tools or [],
            "memory_context": request.memory_context,
            "user_preferences": request.user_preferences or {},
        }

        result = response_orchestrator.respond(
            request.message,
            ui_caps=ui_caps,
        )

        # ResponseOrchestrator returns a structured payload; extract content
        if isinstance(result, dict):
            content = result.get("content", "")
            orchestrator_metadata = {
                "intent": result.get("intent"),
                "persona": result.get("persona"),
                "mood": result.get("mood"),
            }

            orchestrator_metadata.update(result.get("metadata", {}))

            if "onboarding" in result:
                orchestrator_metadata["onboarding"] = result["onboarding"]
        else:
            content = str(result)
            orchestrator_metadata = {}

        latency_ms = (time.time() - start_time) * 1000

        response = ChatRuntimeResponse(
            content=content,
            conversation_id=conversation_id,
            metadata={
                **orchestrator_metadata,
                "platform": request.platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "processing_time": latency_ms / 1000,
                "latency_ms": latency_ms,
                "orchestrator": "response_core",
                "local_processing": True,
                "prompt_driven": True,
            },
        )

        logger.info(
            "Response Core chat runtime response sent",
            extra={
                "user_id": user_id,
                "correlation_id": correlation_id,
                "latency_ms": latency_ms,
                "response_length": len(content),
            },
        )

        return response

    except Exception as e:
        logger.error(
            "Response Core chat runtime error",
            extra={
                "user_id": user_context.get("user_id"),
                "correlation_id": request_metadata.get("correlation_id"),
                "error": str(e),
            },
        )
        
        # Return error response
        return ChatRuntimeResponse(
            content=f"I apologize, but I encountered an error: {str(e)}",
            conversation_id=request.conversation_id or "error",
            metadata={
                "platform": request.platform,
                "correlation_id": request_metadata.get("correlation_id"),
                "user_id": user_context.get("user_id"),
                "processing_time": (time.time() - start_time),
                "error": str(e),
                "orchestrator": "response_core",
                "used_fallback": True,
            },
        )


@router.get("/chat/runtime/config")
async def get_chat_config(
    user_context: Dict[str, Any] = Depends(get_current_user_context),
) -> Dict[str, Any]:
    """
    Get chat configuration for the current user
    """
    try:
        # TODO: Implement actual config retrieval based on user context
        config = {
            "user_id": user_context.get("user_id"),
            "available_tools": [],  # Will be populated by ToolRegistry
            "memory_enabled": True,
            "streaming_enabled": True,
            "max_message_length": 10000,
            "supported_platforms": ["web", "streamlit", "desktop"],
            "default_model": "local",  # Local-first approach
        }

        return config

    except Exception as e:
        logger.error(
            "Failed to get chat config",
            extra={
                "user_id": user_context.get("user_id"),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get configuration",
        )
