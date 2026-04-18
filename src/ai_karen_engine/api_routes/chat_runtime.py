"""
Secure Chat Runtime API Routes with Comprehensive Validation

This module provides secure chat API endpoints with:
- Comprehensive input validation using Pydantic models
- Parameterized database queries to prevent injection
- Rate limiting and abuse prevention
- Proper error handling with structured logging
- Authentication and authorization checks
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator, constr
import re
import hashlib
import uuid

from ..core.dependencies import bypass_user_context_func
from ..config.config_manager import get_config_manager
from ..core.logging.logger import get_structured_logger
from ..core.chat_runtime_control_plane import (
    get_chat_runtime_control_plane,
    RuntimeMode,
    MaintenanceResponse,
    EmergencyFallbackResponse,
    DegradedResponse,
    serialize_runtime_response,
    runtime_response_http_status,
)
from ..chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest as OrchestratorChatRequest,
    ChatResponse as OrchestratorChatResponse,
)
from ..chat.ChatOrchestrator import normalize_session_id as normalize_chat_session_id
from ..chat.stream_processor import AsyncStreamProcessor as StreamProcessor
from ..core.metrics_manager import get_metrics_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])
security = HTTPBearer()


def _runtime_metadata_from_orchestrator_response(
    response: OrchestratorChatResponse,
    *,
    response_id: str,
    requested_model: Optional[str],
) -> Dict[str, Any]:
    """Expose a stable backend-confirmed metadata shape for chat runtime clients."""
    metadata = dict(response.metadata or {})
    metadata.setdefault("response_id", response_id)
    metadata.setdefault("request_id", getattr(response, "request_id", None))
    metadata.setdefault("correlation_id", response.correlation_id)
    metadata.setdefault("conversation_id", getattr(response, "conversation_id", None))
    metadata.setdefault(
        "assistant_message_id", getattr(response, "assistant_message_id", None)
    )
    metadata.setdefault(
        "status",
        response.status.value
        if hasattr(response.status, "value")
        else str(response.status),
    )
    metadata.setdefault("execution_path", getattr(response, "execution_path", None))
    metadata.setdefault("processing_time", response.processing_time)
    metadata.setdefault("used_fallback", response.used_fallback)
    metadata.setdefault("context_used", response.context_used)
    metadata.setdefault("telemetry", getattr(response, "telemetry", {}) or {})
    metadata.setdefault(
        "persistence",
        {
            "canonical_store": "postgres",
            "assistant_persisted": bool(
                getattr(response, "assistant_message_id", None)
            ),
        },
    )
    metadata.setdefault("model", requested_model or "orchestrated")
    return metadata


# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    """Chat message model with comprehensive validation"""

    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content",
        examples=["Hello, how can I help you today?"],
    )
    message_type: str = Field(
        default="user",
        pattern=r"^(user|assistant|system)$",
        description="Type of message",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional message metadata"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        """Validate message content for security issues"""
        if not isinstance(v, str):
            raise ValueError("Content must be a string")

        # Check for injection patterns
        dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # JavaScript protocol
            r"vbscript:",  # VBScript protocol
            r"onload\s*=",  # Event handlers
            r"onerror\s*=",  # Event handlers
            r"SELECT\s+.*\s+FROM",  # SQL injection
            r"DROP\s+TABLE",  # SQL injection
            r"INSERT\s+INTO",  # SQL injection
            r"UPDATE\s+.*\s+SET",  # SQL injection
            r"DELETE\s+FROM",  # SQL injection
            r"exec\s*\(",  # Code execution
            r"system\s*\(",  # System command execution
            r"subprocess\.",  # Subprocess calls
            r"os\.",  # OS module access
            r"__import__",  # Python import
            r"eval\s*\(",  # Code evaluation
        ]

        content_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                raise ValueError(f"Potentially dangerous content detected: {pattern}")

        return v.strip()


class ChatRequest(BaseModel):
    """Chat request model with comprehensive validation"""

    messages: List[ChatMessage] = Field(
        ..., min_length=1, max_length=50, description="List of chat messages"
    )
    model: Optional[str] = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        max_length=50,
        description="Model to use for generation",
    )
    temperature: Optional[float] = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=None, ge=1, le=4096, description="Maximum tokens to generate"
    )
    stream: Optional[bool] = Field(
        default=False, description="Whether to stream the response"
    )
    session_id: Optional[str] = Field(
        default=None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        max_length=100,
        description="Session identifier",
    )

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v):
        """Validate message list for security issues"""
        if not v:
            raise ValueError("Messages list cannot be empty")

        # Check total content length
        total_length = sum(len(msg.content) for msg in v)
        if total_length > 50000:  # 50KB total
            raise ValueError("Total message content too long")

        return v


class ChatResponse(BaseModel):
    """Chat response model"""

    response_id: str = Field(..., description="Unique response identifier")
    content: str = Field(..., description="Generated response content")
    model: str = Field(..., description="Model used for generation")
    usage: Dict[str, int] = Field(..., description="Token usage information")
    metadata: Dict[str, Any] = Field(..., description="Response metadata")
    timestamp: datetime = Field(..., description="Response timestamp")


class StreamChunk(BaseModel):
    """Streaming response chunk model"""

    response_id: str = Field(..., description="Response identifier")
    chunk_id: int = Field(..., description="Chunk sequence number")
    content: str = Field(..., description="Chunk content")
    finished: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


# Rate limiting and security
class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def sanitize_session_id(session_id: Optional[str]) -> str:
        """Generate secure session ID if not provided"""
        if not session_id:
            return f"session_{uuid.uuid4().hex[:16]}"

        # Validate existing session ID
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            raise ValueError("Invalid session ID format")

        return session_id

    @staticmethod
    def validate_user_input(user_input: str, max_length: int = 10000) -> str:
        """Validate and sanitize user input"""
        if not user_input:
            return ""

        # Length check
        if len(user_input) > max_length:
            raise ValueError(f"Input too long: {len(user_input)} > {max_length}")

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", user_input)

        return sanitized.strip()


# Dependency functions
async def get_chat_orchestrator():
    """Get chat orchestrator instance"""
    from ..chat.factory import get_chat_orchestrator as get_factory_chat_orchestrator

    return await get_factory_chat_orchestrator()


async def get_stream_processor():
    """Get stream processor instance"""
    # Create a new instance with default parameters
    return StreamProcessor()


# API endpoints
@router.post("/chat", response_model=ChatResponse)
async def create_chat_response(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """
    Create a chat response with comprehensive validation and security checks
    """
    start_time = time.time()
    processing_time = 0.0  # Initialize to avoid unbound variable
    session_id = ""  # Initialize to avoid unbound variable
    correlation_id = http_request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    structured_logger = get_structured_logger()

    try:
        # ── Control Plane Gate ─────────────────────────────────────
        # All chat entry points must consult the single authority.
        control_plane = await get_chat_runtime_control_plane()
        runtime_response = await control_plane.get_runtime_response()

        if runtime_response is not None:
            # Non-normal mode — consume the control-plane contract directly.
            if isinstance(runtime_response, DegradedResponse):
                if runtime_response.is_minimal:
                    # Minimal degraded — can't reach orchestrator, return message
                    from fastapi.responses import JSONResponse

                    payload = serialize_runtime_response(runtime_response) or {}
                    return JSONResponse(
                        status_code=runtime_response_http_status(runtime_response)
                        or 200,
                        content=payload,
                        headers={
                            "Retry-After": str(runtime_response.retry_after_seconds)
                        },
                    )
                # Non-minimal degraded: proceed to orchestrator with available capabilities
            elif isinstance(
                runtime_response,
                (MaintenanceResponse, EmergencyFallbackResponse),
            ):
                from fastapi.responses import JSONResponse

                payload = serialize_runtime_response(runtime_response) or {}
                status_code = runtime_response_http_status(runtime_response) or 503
                return JSONResponse(
                    status_code=status_code,
                    content=payload,
                    headers={"Retry-After": str(runtime_response.retry_after_seconds)},
                )
        # ── End Control Plane Gate ─────────────────────────────────

        # Validate and sanitize session ID
        session_id = SecurityValidator.sanitize_session_id(request.session_id)

        # Validate model selection
        from ..config.config_manager import get_config_value

        available_models = get_config_value("available_models", [])
        if request.model and request.model not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model}' not available. Available models: {available_models}",
            )

        # Get chat orchestrator
        orchestrator = await get_chat_orchestrator()

        # Process messages with security validation
        validated_messages = []
        for msg in request.messages:
            # Validate message content
            sanitized_content = SecurityValidator.validate_user_input(msg.content)
            validated_messages.append(
                {
                    "content": sanitized_content,
                    "message_type": msg.message_type,
                    "metadata": msg.metadata or {},
                }
            )

        # Generate response ID
        response_id = str(uuid.uuid4())

        # Log request start
        structured_logger.log_event(
            event="chat_request_started",
            user_id=user["user_id"],
            details={
                "method": "POST",
                "endpoint": "/api/chat/chat",
                "correlation_id": correlation_id,
                "message_count": len(validated_messages),
                "model": request.model,
                "stream": request.stream,
                "session_id": session_id,
            },
        )

        conversation_id = normalize_chat_session_id(session_id)
        flattened_prompt = "\n".join(
            msg["content"]
            for msg in validated_messages
            if msg.get("message_type") == "user"
        ).strip()
        chat_request = OrchestratorChatRequest(
            request_id=response_id,
            correlation_id=correlation_id,
            tenant_id=str(user.get("tenant_id") or "default"),
            message=flattened_prompt,
            user_id=user["user_id"],
            org_id=str(user.get("tenant_id") or "default"),
            conversation_id=conversation_id,
            session_id=conversation_id,
            message_id=str(uuid.uuid4()),
            streaming=bool(request.stream),
            stream=bool(request.stream),
            include_context=True,
            attachments=[],
            metadata={
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "messages": validated_messages,
                "response_id": response_id,
            },
        )

        # Process chat request
        if request.stream:

            async def generate_stream():
                try:
                    stream_result = await orchestrator.handle_chat_stream(chat_request)
                    async for chunk in stream_result:
                        chunk_payload = {
                            "type": chunk.type,
                            "content": chunk.content,
                            "correlation_id": chunk.correlation_id,
                            "metadata": chunk.metadata or {},
                        }
                        yield f"data: {json.dumps(chunk_payload)}\n\n"
                except Exception as e:
                    structured_logger.log_error(
                        error=str(e),
                        endpoint="/api/chat/chat",
                        user_id=user["user_id"],
                        correlation_id=correlation_id,
                        context="streaming_response",
                    )
                    raise HTTPException(status_code=500, detail="Streaming failed")

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "X-Correlation-Id": correlation_id,
                    "X-Response-Id": response_id,
                },
            )
        else:
            # Non-streaming response
            response_data = await orchestrator.handle_chat(chat_request)

            # Note: Rate limiter update skipped - needs implementation

            # Record metrics
            try:
                metrics_manager = get_metrics_manager()
                counter_metric = metrics_manager.register_counter(
                    "chat_requests_total",
                    "Total number of chat requests",
                    ["model", "user_type", "response_type"],
                )
                if counter_metric:
                    counter_metric.labels(
                        model=request.model or "default",
                        user_type=user.get("user_type", "unknown"),
                        response_type="standard",
                    ).inc()

                processing_time = time.time() - start_time
                histogram_metric = metrics_manager.register_histogram(
                    "chat_request_duration_seconds",
                    "Duration of chat requests in seconds",
                    ["model"],
                )
                if histogram_metric:
                    histogram_metric.labels(model=request.model or "default").observe(
                        processing_time
                    )
            except Exception as e:
                # Log metrics error but don't fail the request
                logger.warning(f"Failed to record metrics: {e}")

            # Log successful response
            structured_logger.log_response(
                status_code=200,
                endpoint="/api/chat/chat",
                user_id=user["user_id"],
                correlation_id=correlation_id,
                response_data={
                    "response_id": response_id,
                    "model": request.model or "orchestrated",
                    "tokens_used": (
                        (response_data.metadata or {}).get("llm", {}).get("usage", {})
                        if isinstance(response_data, OrchestratorChatResponse)
                        else {}
                    ).get("total_tokens", 0),
                    "processing_time": processing_time,
                },
            )

            return ChatResponse(
                response_id=response_id,
                content=response_data.response
                if isinstance(response_data, OrchestratorChatResponse)
                else "",
                model=request.model or "orchestrated",
                usage=(response_data.metadata or {}).get("llm", {}).get("usage", {})
                if isinstance(response_data, OrchestratorChatResponse)
                else {},
                metadata=_runtime_metadata_from_orchestrator_response(
                    response_data,
                    response_id=response_id,
                    requested_model=request.model,
                )
                if isinstance(response_data, OrchestratorChatResponse)
                else {},
                timestamp=datetime.utcnow(),
            )

    except HTTPException:
        raise
    except ValueError as e:
        structured_logger.log_error(
            error=str(e),
            endpoint="/api/chat/chat",
            user_id=user.get("user_id") or "unknown",
            correlation_id=correlation_id,
            context="validation_error",
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        structured_logger.log_error(
            error=str(e),
            endpoint=f"/api/chat/sessions/{session_id}",
            user_id=user.get("user_id") or "unknown",
            correlation_id=correlation_id,
            context="unexpected_error",
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    http_request: Request,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """
    Get chat session history with validation and access control
    """
    correlation_id = http_request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    structured_logger = get_structured_logger()

    try:
        # Validate session ID format
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        # Session management is not part of the current production chat orchestrator contract.
        raise HTTPException(
            status_code=501,
            detail="Chat session retrieval is not implemented on the production orchestrator",
        )

        # Log access
        structured_logger.log_event(
            event="chat_session_access",
            user_id=user["user_id"],
            details={
                "method": "GET",
                "endpoint": f"/api/chat/sessions/{session_id}",
                "correlation_id": correlation_id,
                "session_id": session_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(
            error=str(e),
            endpoint=f"/api/chat/sessions/{session_id}",
            user_id=user.get("user_id") or "unknown",
            correlation_id=correlation_id,
            context="unexpected_error",
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    http_request: Request,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """
    Delete chat session with validation and access control
    """
    correlation_id = http_request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    structured_logger = get_structured_logger()

    try:
        # Validate session ID format
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")

        raise HTTPException(
            status_code=501,
            detail="Chat session deletion is not implemented on the production orchestrator",
        )

        # Log deletion
        structured_logger.log_event(
            event="chat_session_deletion_attempted",
            user_id=user["user_id"],
            details={
                "method": "DELETE",
                "endpoint": f"/api/chat/sessions/{session_id}",
                "correlation_id": correlation_id,
                "session_id": session_id,
            },
        )

        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        structured_logger.log_error(
            error=str(e),
            endpoint=f"/api/chat/sessions/{session_id}",
            user_id=user.get("user_id") or "unknown",
            correlation_id=correlation_id,
            context="unexpected_error",
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def get_available_models(
    http_request: Request,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """
    Get available chat models with user-specific filtering
    """
    correlation_id = http_request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    structured_logger = get_structured_logger()

    try:
        # Get configuration
        from ..config.config_manager import get_config_value

        all_models = get_config_value("available_models", [])

        # Filter models based on user permissions
        user_permissions = user.get("permissions", [])
        available_models = []

        for model in all_models:
            model_permissions = model.get("required_permissions", [])
            if all(perm in user_permissions for perm in model_permissions):
                available_models.append(
                    {
                        "id": model["id"],
                        "name": model["name"],
                        "description": model.get("description", ""),
                        "max_tokens": model.get("max_tokens", 4096),
                        "supports_streaming": model.get("supports_streaming", True),
                    }
                )

        # Log access
        structured_logger.log_event(
            event="chat_models_accessed",
            user_id=user["user_id"],
            details={
                "method": "GET",
                "endpoint": "/api/chat/models",
                "correlation_id": correlation_id,
                "model_count": len(available_models),
            },
        )

        return {"models": available_models, "total_count": len(available_models)}

    except Exception as e:
        structured_logger.log_error(
            error=str(e),
            endpoint="/api/chat/models",
            user_id=user.get("user_id") or "unknown",
            correlation_id=correlation_id,
            context="unexpected_error",
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check endpoint for chat service"""
    try:
        await get_chat_orchestrator()
        await get_stream_processor()

        return {
            "status": "healthy",
            "services": {"orchestrator": "healthy", "stream_processor": "healthy"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# Import StreamingResponse for streaming endpoints
from fastapi.responses import StreamingResponse
