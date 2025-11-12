"""
Chat Runtime API Routes
Unified chat endpoint for all platforms (Web UI, Desktop)
"""

import asyncio
import json
import re
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.chat import chat_orchestrator
from ai_karen_engine.chat.chat_orchestrator import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
)
from ai_karen_engine.core.config_manager import get_config
from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.response.factory import get_global_orchestrator
from ai_karen_engine.core.service_registry import get_service_registry
from ai_karen_engine.integrations.llm_registry import get_registry
from ai_karen_engine.services.tool_service import (
    ToolStatus,
    get_tool_service as get_global_tool_service,
)

try:
    from ai_karen_engine.chat.factory import get_chat_orchestrator as get_production_chat_orchestrator
except ImportError:
    get_production_chat_orchestrator = None

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
def get_chat_orchestrator() -> chat_orchestrator.ChatOrchestrator:
    """Return the production orchestrator or a lightweight fallback if unavailable."""
    if get_production_chat_orchestrator:
        try:
            orchestrator = get_production_chat_orchestrator()
            if orchestrator:
                logger.info("Using production ChatOrchestrator for chat runtime")
                return orchestrator
        except Exception as prod_err:  # pragma: no cover - defensive
            logger.warning(
                "Production ChatOrchestrator unavailable, falling back to lite orchestrator: %s",
                prod_err,
            )

    logger.info("Creating LiteChatOrchestrator for degraded mode support")

    class LiteChatOrchestrator(chat_orchestrator.ChatOrchestrator):
        """Minimal orchestrator that provides meaningful degraded-mode replies."""

        def __init__(self) -> None:
            super().__init__()
            self._restricted_ops = [
                "long_term_memory_write",
                "long_term_memory_read",
                "vector_memory_query",
            ]

        async def process_message(self, request):
            """Return either a full response or a streaming generator."""

            start_time = time.perf_counter()
            correlation_id = getattr(request, "session_id", str(uuid.uuid4()))
            message = getattr(request, "message", "")

            response_text, reasoning, extra_metadata = self._generate_response(message)

            base_metadata: Dict[str, Any] = {
                "fallback_mode": True,
                "mode": "minimal",
                "status": "degraded",
                "message": "AI services are initializing",
                "notice": (
                    "Responding with Kari's local lite assistant while full services load. "
                    "Some advanced features like deep memory search remain temporarily disabled."
                ),
                "restricted_operations": list(self._restricted_ops),
                "capabilities": {
                    "reasoning": "basic",
                    "qa": "lightweight",
                    "tools": "unavailable",
                },
                "reasoning_summary": reasoning,
            }
            if extra_metadata:
                base_metadata.update(extra_metadata)

            processing_time = time.perf_counter() - start_time
            base_metadata.setdefault("local_model", "lite-rule-engine")
            base_metadata["processing_time"] = processing_time
            base_metadata["response_length"] = len(response_text)

            if getattr(request, "stream", False):
                async def _stream_response() -> AsyncGenerator[ChatStreamChunk, None]:
                    yield ChatStreamChunk(
                        type="metadata",
                        content="",
                        correlation_id=correlation_id,
                        metadata=base_metadata,
                    )
                    for token in self._tokenize_response(response_text):
                        yield ChatStreamChunk(
                            type="content",
                            content=token,
                            correlation_id=correlation_id,
                            metadata={},
                        )
                    yield ChatStreamChunk(
                        type="complete",
                        content="",
                        correlation_id=correlation_id,
                        metadata=base_metadata,
                    )

                return _stream_response()

            return ChatResponse(
                response=response_text,
                correlation_id=correlation_id,
                processing_time=processing_time,
                used_fallback=True,
                metadata=base_metadata,
            )

        async def cancel_processing(
            self, conversation_id: str, correlation_id: Optional[str] = None
        ) -> List[str]:
            """No asynchronous processing is queued in lite mode, so nothing to cancel."""

            return []

        def _generate_response(self, message: str) -> Tuple[str, str, Dict[str, Any]]:
            normalized = (message or "").strip()
            lower_message = normalized.lower()
            reasoning_steps: List[str] = []

            if not normalized:
                reasoning_steps.append("Received empty input; prompting user for clarification.")
                response = (
                    "It looks like nothing was sent. I'm in minimal mode while the full AI spins up, "
                    "but I'm ready to help with questions or small tasks."
                )
                return response, "; ".join(reasoning_steps), {}

            if any(greeting in lower_message for greeting in ["hello", "hi", "hey", "good morning", "good evening"]):
                reasoning_steps.append("Detected greeting and crafted friendly acknowledgement.")
                response = (
                    "Hello! Kari's full AI services are still initializing, so I'm operating in minimal mode. "
                    "I can answer quick questions and keep you posted until everything is ready."
                )
                return response, "; ".join(reasoning_steps), {}

            if "what can you do" in lower_message or "help" in lower_message:
                reasoning_steps.append("User asked about capabilities; summarising degraded-mode abilities.")
                response = (
                    "Right now I'm running Kari's lite assistant while the full orchestrator comes online. "
                    "I can help with quick Q&A, light reasoning, and progress updates. "
                    "Features such as long-term memory or advanced tool calls are temporarily paused."
                )
                return response, "; ".join(reasoning_steps), {}

            if any(keyword in lower_message for keyword in ["code", "debug", "program"]):
                reasoning_steps.append("Detected coding intent; providing contextual response.")
                response = (
                    "I'd love to help with code. The deep analyzers are still waking up, but share your snippet "
                    "or question and I'll walk through it with lightweight reasoning."
                )
                return response, "; ".join(reasoning_steps), {}

            math_answer = self._handle_basic_math(lower_message)
            if math_answer is not None:
                reasoning_steps.append("Solved arithmetic expression in minimal mode.")
                response = (
                    f"While in minimal mode I can still reason through quick math. The answer is {math_answer}. "
                    "I'll have deeper analytical tools once the full stack loads."
                )
                return response, "; ".join(reasoning_steps), {}

            canned_answer = self._lookup_faq(lower_message)
            if canned_answer:
                reasoning_steps.append("Matched question against lite knowledge base.")
                return canned_answer, "; ".join(reasoning_steps), {}

            reasoning_steps.append("No template matched; generating supportive default message.")
            response = (
                "I'm currently running Kari's minimal chat mode. I don't have access to long-term memory or external tools yet, "
                "but I can still help reason through questions and keep you updated. Let me know what you need!"
            )
            return response, "; ".join(reasoning_steps), {}

        def _handle_basic_math(self, lower_message: str) -> Optional[str]:
            pattern = re.compile(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)")
            match = pattern.search(lower_message)
            if not match:
                return None

            left, operator_symbol, right = match.groups()
            try:
                left_val = float(left)
                right_val = float(right)
            except ValueError:
                return None

            if operator_symbol == "/" and right_val == 0:
                return "undefined (division by zero)"

            operations = {
                "+": left_val + right_val,
                "-": left_val - right_val,
                "*": left_val * right_val,
                "/": left_val / right_val,
            }

            result = operations.get(operator_symbol)
            if result is None:
                return None

            if isinstance(result, float) and result.is_integer():
                return str(int(result))
            return f"{result:.4f}".rstrip("0").rstrip(".")

        def _lookup_faq(self, lower_message: str) -> Optional[str]:
            faq_responses = {
                "who are you": (
                    "I'm Kari's lite assistant. While the full AI services initialize, I'm here to provide quick guidance and "
                    "basic answers."
                ),
                "status": (
                    "Core services are warming up. Minimal mode is active, so tool usage and deep memory are temporarily disabled."
                ),
                "where is my data": (
                    "Your data remains secure. Minimal mode avoids long-term memory writes until the full stack is verified."
                ),
            }

            for key, value in faq_responses.items():
                if key in lower_message:
                    return value
            return None

        def _tokenize_response(self, response: str) -> Iterable[str]:
            for token in response.split():
                yield f"{token} "

    return LiteChatOrchestrator()


# Chat Runtime Routes
@router.post("/chat/runtime", response_model=ChatRuntimeResponse)
async def chat_runtime(
    request: ChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: chat_orchestrator.ChatOrchestrator = Depends(get_chat_orchestrator),
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
    except asyncio.CancelledError:
        logger.info(
            "Chat runtime request cancelled",
            extra={
                "user_id": user_context.get("user_id"),
                "correlation_id": request_metadata.get("correlation_id"),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Generation cancelled",
        )
    except Exception as e:
        logger.error(
            "Chat runtime error",
            extra={
                "user_id": user_context.get("user_id"),
                "correlation_id": request_metadata.get("correlation_id"),
                "error": str(e),
            },
        )
        
        # Provide a graceful fallback response instead of crashing
        try:
            fallback_response = ChatRuntimeResponse(
                content="I'm experiencing technical difficulties right now. The AI services are initializing and will be available shortly. Please try again in a moment.",
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                metadata={
                    "platform": request.platform,
                    "correlation_id": request_metadata.get("correlation_id"),
                    "user_id": user_context.get("user_id"),
                    "fallback_mode": True,
                    "error_type": "initialization_error",
                    "processing_time": 0.0,
                    "latency_ms": 0.0,
                },
            )
            
            logger.info(
                "Chat runtime fallback response provided",
                extra={
                    "user_id": user_context.get("user_id"),
                    "correlation_id": request_metadata.get("correlation_id"),
                },
            )
            
            return fallback_response
        except Exception as fallback_error:
            logger.error(f"Failed to create fallback response: {fallback_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )


@router.post("/chat/runtime/stream")
async def chat_runtime_stream(
    request: ChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: chat_orchestrator.ChatOrchestrator = Depends(get_chat_orchestrator),
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

            stream_result = await chat_orchestrator.process_message(chat_request)

            if isinstance(stream_result, ChatResponse):
                total_latency = (time.time() - start_time) * 1000
                completion_data = {
                    **stream_result.metadata,
                    "total_tokens": 0,
                    "latency_ms": total_latency,
                    "first_token_latency_ms": total_latency,
                }
                if generation_hints and "requested_generation" not in completion_data:
                    completion_data["requested_generation"] = generation_hints
                if preferred_provider and "preferred_llm_provider" not in completion_data:
                    completion_data["preferred_llm_provider"] = preferred_provider
                if preferred_model and "preferred_model" not in completion_data:
                    completion_data["preferred_model"] = preferred_model
                yield f"data: {json.dumps({'type': 'token', 'data': {'token': stream_result.response}})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'data': completion_data})}\n\n"

                logger.info(
                    "Chat runtime stream completed (single response)",
                    extra={
                        "user_id": user_context.get("user_id"),
                        "correlation_id": correlation_id,
                    },
                )
                return

            async for chunk in stream_result:
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

        except asyncio.CancelledError:
            logger.info(
                "Chat runtime stream cancelled",
                extra={
                    "user_id": user_context.get("user_id"),
                    "correlation_id": correlation_id,
                },
            )
            yield "data: {\"type\": \"error\", \"data\": {\"message\": \"Generation cancelled\"}}\n\n"
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
    correlation_id: Optional[str] = None,
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: chat_orchestrator.ChatOrchestrator = Depends(get_chat_orchestrator),
) -> Dict[str, Any]:
    """
    Stop ongoing chat generation
    """
    try:
        correlation = correlation_id or request_metadata.get("correlation_id")

        logger.info(
            "Chat generation stop requested",
            extra={
                "user_id": user_context.get("user_id"),
                "conversation_id": conversation_id,
                "correlation_id": correlation,
            },
        )

        cancelled = await chat_orchestrator.cancel_processing(
            conversation_id=conversation_id,
            correlation_id=correlation_id,
        )

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active generation found for conversation",
            )

        return {
            "status": "stopped",
            "conversation_id": conversation_id,
            "correlation_ids": cancelled,
        }

    except ValueError as exc:
        logger.warning(
            "Invalid stop request",
            extra={
                "user_id": user_context.get("user_id"),
                "conversation_id": conversation_id,
                "error": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
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
        config = get_config()
        llm_registry = get_registry()
        service_registry = get_service_registry()

        # Resolve available tools from the global tool service
        tools_section: Dict[str, Any] = {"available": [], "metrics": {}}
        try:
            tool_service = get_global_tool_service()
            available_tools = tool_service.list_tools(status=ToolStatus.AVAILABLE)

            for tool_name in available_tools:
                metadata = tool_service.get_tool_metadata(tool_name)
                if metadata:
                    tools_section["available"].append(
                        {
                            "name": metadata.name,
                            "description": metadata.description,
                            "category": metadata.category.value,
                            "status": metadata.status.value,
                            "tags": list(metadata.tags),
                            "requires_auth": metadata.requires_auth,
                            "timeout": metadata.timeout,
                        }
                    )
                else:
                    tools_section["available"].append(
                        {
                            "name": tool_name,
                            "description": "",
                            "category": "unknown",
                            "status": "unknown",
                            "tags": [],
                            "requires_auth": False,
                            "timeout": None,
                        }
                    )

            tools_section["metrics"] = tool_service.get_service_stats()
        except Exception as tool_error:  # pragma: no cover - defensive
            logger.warning(
                "Tool service unavailable during chat config retrieval: %s",
                tool_error,
            )
            tools_section["error"] = str(tool_error)

        # Gather provider information from the LLM registry
        provider_details: List[Dict[str, Any]] = []
        registry_chain: List[str] = []
        try:
            registry_chain = llm_registry.default_chain()
            for provider_name in llm_registry.list_providers():
                provider_info = llm_registry.get_provider_info(provider_name) or {}
                provider_details.append(
                    {
                        "name": provider_name,
                        "description": provider_info.get("description", ""),
                        "default_model": provider_info.get("default_model")
                        or provider_info.get("model"),
                        "supports_streaming": bool(
                            provider_info.get("supports_streaming", False)
                        ),
                        "supports_embeddings": bool(
                            provider_info.get("supports_embeddings", False)
                        ),
                        "requires_api_key": bool(
                            provider_info.get("requires_api_key", False)
                        ),
                        "status": provider_info.get("health_status", "unknown"),
                        "last_health_check": provider_info.get("last_health_check"),
                    }
                )
        except Exception as registry_error:  # pragma: no cover - defensive
            logger.warning(
                "LLM registry unavailable during chat config retrieval: %s",
                registry_error,
            )

        # Determine routing preferences from user profiles and config defaults
        profile_data = config.user_profiles or {}
        active_profile_id = config.active_profile or profile_data.get(
            "active_profile"
        )
        profile_summaries: List[Dict[str, Any]] = []
        fallback_chain: List[str] = []
        default_provider = config.llm.provider
        default_model = config.llm.model

        for profile in profile_data.get("profiles", []):
            assignments = profile.get("assignments", {})
            profile_summary = {
                "id": profile.get("id"),
                "name": profile.get("name"),
                "is_active": profile.get("is_active", False),
                "fallback_chain": profile.get("fallback_chain", []),
                "assignments": assignments,
                "updated_at": profile.get("updated_at"),
            }
            profile_summaries.append(profile_summary)

            if profile.get("id") == active_profile_id or profile.get("is_active"):
                fallback_chain = profile.get("fallback_chain", fallback_chain)
                chat_assignment = assignments.get("chat", {})
                if isinstance(chat_assignment, dict):
                    default_provider = chat_assignment.get("provider", default_provider)
                    default_model = chat_assignment.get("model", default_model)

        routing_chain = fallback_chain or registry_chain

        # Derive service health information for observability in the UI
        services_summary: List[Dict[str, Any]] = []
        ready_states = {"ready", "degraded"}
        try:
            registered_services = service_registry.list_services()
            for service_name in registered_services.keys():
                info = service_registry.get_service_info(service_name)
                if not info:
                    continue

                services_summary.append(
                    {
                        "name": service_name,
                        "type": info.service_type.__name__,
                        "status": info.status.value,
                        "dependencies": [
                            {
                                "name": dependency.name,
                                "required": dependency.required,
                                "status": dependency.status.value,
                            }
                            for dependency in info.dependencies
                        ],
                        "error": info.error_message,
                        "initialization_time": info.initialization_time,
                    }
                )
        except Exception as service_error:  # pragma: no cover - defensive
            logger.warning(
                "Service registry introspection failed during chat config retrieval: %s",
                service_error,
            )

        ready_services = sum(
            1 for service in services_summary if service["status"] in ready_states
        )

        monitoring_config = config.monitoring
        web_ui_config = config.web_ui
        memory_config = config.memory or {}

        response_payload = {
            "user": {
                "id": user_context.get("user_id"),
                "tenant_id": user_context.get("tenant_id"),
                "roles": user_context.get("roles", []),
            },
            "environment": {
                "name": config.environment.value,
                "debug": bool(config.debug),
            },
            "llm": {
                "default_provider": default_provider,
                "default_model": default_model,
                "fallback_chain": routing_chain,
                "providers": provider_details,
                "streaming_enabled": any(
                    provider.get("supports_streaming") for provider in provider_details
                ),
                "profiles": profile_summaries,
                "active_profile": active_profile_id,
            },
            "tools": tools_section,
            "memory": {
                "enabled": bool(memory_config.get("enabled", True)),
                "provider": memory_config.get("provider", "local"),
                "embedding_dim": memory_config.get("embedding_dim"),
                "decay_lambda": memory_config.get("decay_lambda"),
                "ui_enabled": bool(web_ui_config.enable_memory_integration),
            },
            "services": {
                "registered": len(services_summary),
                "ready": ready_services,
                "items": services_summary,
            },
            "ui": {
                "platforms": list(web_ui_config.ui_sources),
                "session_timeout": web_ui_config.session_timeout,
                "max_history": web_ui_config.max_conversation_history,
                "theme": config.theme,
                "proactive_suggestions": bool(
                    web_ui_config.enable_proactive_suggestions
                ),
            },
            "limits": {
                "max_message_length": 10000,
                "max_tokens": config.llm.max_tokens,
                "temperature": config.llm.temperature,
            },
            "observability": {
                "metrics_enabled": monitoring_config.enable_metrics,
                "prometheus_port": monitoring_config.metrics_port,
                "prometheus_enabled": monitoring_config.prometheus_enabled,
                "tracing_enabled": monitoring_config.enable_tracing,
                "log_level": monitoring_config.log_level,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return response_payload

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
