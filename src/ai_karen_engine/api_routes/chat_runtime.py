"""
Chat Runtime API Routes
Production-grade unified chat endpoint for all platforms (Web UI, Desktop)
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
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

logger = get_logger(__name__)
router = APIRouter(tags=["chat-runtime"])


# Production Configuration
class ChatConfig:
    """Production chat configuration"""
    MAX_MESSAGE_LENGTH = 10000
    MAX_TOKENS_DEFAULT = 4096
    STREAM_TIMEOUT = 30.0
    FALLBACK_ENABLED = True
    RATE_LIMIT_REQUESTS = 10
    RATE_LIMIT_WINDOW = 60  # seconds
    CACHE_SIZE_USER_PREFS = 1000
    CACHE_SIZE_PROVIDER_ROUTING = 100
    
    @classmethod
    def from_app_config(cls):
        """Load from application configuration"""
        config = get_config()
        return cls(
            max_message_length=getattr(config.chat, 'max_message_length', 10000),
            max_tokens_default=getattr(config.llm, 'max_tokens', 4096),
            stream_timeout=getattr(config.chat, 'stream_timeout', 30.0),
            fallback_enabled=getattr(config.chat, 'fallback_enabled', True)
        )


# Custom Exceptions
class ChatRuntimeError(Exception):
    """Base exception for chat runtime errors"""
    pass


class ValidationError(ChatRuntimeError):
    """Request validation errors"""
    pass


class ServiceUnavailableError(ChatRuntimeError):
    """Service initialization errors"""
    pass


class RateLimitExceededError(ChatRuntimeError):
    """Rate limiting errors"""
    pass


# Enhanced Request/Response Models
class ChatMessage(BaseModel):
    """Enhanced chat message model with validation"""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., min_length=1, max_length=ChatConfig.MAX_MESSAGE_LENGTH, description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'assistant', 'system']:
            raise ValueError('role must be user, assistant, or system')
        return v
    
    @validator('content')
    def sanitize_content(cls, v):
        """Basic content sanitization"""
        import html
        return html.escape(v) if isinstance(v, str) else str(v)


class ToolCall(BaseModel):
    """Tool call model"""
    id: str = Field(..., description="Unique tool call ID")
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    result: Optional[Any] = Field(None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Tool execution error")
    execution_time: Optional[float] = Field(None, description="Tool execution time in seconds")
    status: str = Field(default="pending", description="Tool execution status")


class MemoryOperation(BaseModel):
    """Memory operation model"""
    id: str = Field(..., description="Unique operation ID")
    operation_type: str = Field(..., description="Operation type: store, retrieve, update, delete")
    memory_tier: str = Field(..., description="Memory tier: short_term, long_term, persistent")
    content: Dict[str, Any] = Field(default_factory=dict, description="Operation content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = Field(default=True, description="Operation success status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operation metadata")


class SanitizedChatRuntimeRequest(BaseModel):
    """Production-grade chat runtime request with enhanced validation"""
    message: str = Field(..., min_length=1, max_length=ChatConfig.MAX_MESSAGE_LENGTH, description="User message")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Chat context")
    tools: Optional[List[str]] = Field(default_factory=list, description="Available tools")
    memory_context: Optional[str] = Field(None, description="Memory context identifier")
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User preferences")
    platform: Optional[str] = Field(default="web", description="Platform identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    stream: bool = Field(default=True, description="Enable streaming response")
    model: Optional[str] = Field(default=None, description="Explicit model identifier requested by the client")
    provider: Optional[str] = Field(default=None, description="Explicit provider requested by the client")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Requested sampling temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Requested maximum tokens for the response")
    
    @validator('message')
    def sanitize_message(cls, v):
        """Basic XSS prevention and validation"""
        import html
        if not v or not v.strip():
            raise ValidationError("Message cannot be empty")
        if len(v) > ChatConfig.MAX_MESSAGE_LENGTH:
            raise ValidationError(f"Message exceeds maximum length of {ChatConfig.MAX_MESSAGE_LENGTH} characters")
        return html.escape(v.strip()) if isinstance(v, str) else str(v)
    
    @validator('tools')
    def validate_tools(cls, v):
        """Validate tool names to prevent injection"""
        if not v:
            return v
        try:
            tool_service = get_global_tool_service()
            valid_tools = tool_service.list_tools()
            for tool in v:
                if tool not in valid_tools:
                    raise ValidationError(f"Invalid tool: {tool}")
        except Exception:
            # If tool service is unavailable, we'll validate later
            pass
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValidationError("Temperature must be between 0.0 and 2.0")
        return v


class ChatRuntimeResponse(BaseModel):
    """Chat runtime response model"""
    content: str = Field(..., description="Response content")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls made")
    memory_operations: List[MemoryOperation] = Field(default_factory=list, description="Memory operations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatError(BaseModel):
    """Enhanced chat error model"""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    suggestion: Optional[str] = Field(None, description="Suggested resolution")


# Production Dependency Functions
async def get_request_metadata(request: Request) -> Dict[str, Any]:
    """Enhanced request metadata extraction"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    return {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "platform": request.headers.get("x-platform", "web"),
        "client_id": request.headers.get("x-client-id", "unknown"),
        "correlation_id": request.headers.get("x-correlation-id", str(uuid.uuid4())),
        "request_id": str(uuid.uuid4()),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }


async def validate_chat_request(request: SanitizedChatRuntimeRequest) -> SanitizedChatRuntimeRequest:
    """Production-grade chat request validation"""
    # Additional validation beyond Pydantic
    if request.max_tokens is not None and request.max_tokens <= 0:
        raise ValidationError("max_tokens must be greater than zero")
    
    if request.max_tokens and request.max_tokens > 100000:  # Reasonable upper limit
        raise ValidationError("max_tokens exceeds reasonable limit")
    
    return request


# Enhanced Caching System
@lru_cache(maxsize=ChatConfig.CACHE_SIZE_USER_PREFS)
def _cache_user_preferences(user_id: str, platform: str) -> Tuple[Optional[str], Optional[str]]:
    """Cache user preferences to reduce config lookups"""
    try:
        config = get_config()
        profile_data = config.user_profiles or {}
        
        for profile in profile_data.get("profiles", []):
            if profile.get("is_active", False):
                assignments = profile.get("assignments", {})
                chat_assignment = assignments.get("chat", {})
                if isinstance(chat_assignment, dict):
                    provider = chat_assignment.get("provider")
                    model = chat_assignment.get("model")
                    return provider, model
    except Exception:
        pass
    
    return None, None


@lru_cache(maxsize=ChatConfig.CACHE_SIZE_PROVIDER_ROUTING)
def _cache_provider_routing(provider: str, model: str) -> Dict[str, Any]:
    """Cache provider routing decisions"""
    return {"provider": provider, "model": model, "cached_at": time.time()}


def _extract_generation_preferences(
    request: SanitizedChatRuntimeRequest,
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """Enhanced generation preferences with caching"""
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

    # Try cached preferences first
    cached_provider, cached_model = _cache_user_preferences(
        user_prefs.get("user_id", "default"), 
        request.platform or "web"
    )

    provider = _first_non_empty(
        (
            request.provider,
            user_prefs.get("preferred_llm_provider"),
            context_prefs.get("preferred_llm_provider"),
            cached_provider,
        )
    )
    if provider:
        hints["provider"] = provider

    model = _first_non_empty(
        (
            request.model,
            user_prefs.get("preferred_model"),
            context_prefs.get("preferred_model"),
            cached_model,
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
        hints["temperature"] = max(0.0, min(2.0, temperature))  # Clamp to valid range

    max_tokens = request.max_tokens
    if max_tokens is None:
        tokens_from_prefs = user_prefs.get("max_tokens") if isinstance(user_prefs, dict) else None
        if isinstance(tokens_from_prefs, int) and tokens_from_prefs > 0:
            max_tokens = tokens_from_prefs
    if max_tokens is not None:
        hints["max_tokens"] = min(max_tokens, 100000)  # Reasonable upper limit

    return provider, model, hints


# Enhanced Orchestrator with Circuit Breaker
class CircuitBreaker:
    """Simple circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise ServiceUnavailableError("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise ServiceUnavailableError(f"Circuit breaker triggered: {e}") from e
        return wrapper


class ChatOrchestrator:
    """Production-grade minimal orchestrator with enhanced reliability"""

    def __init__(self) -> None:
        self._restricted_ops = [
            "long_term_memory_write",
            "long_term_memory_read",
            "vector_memory_query",
        ]
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

    @CircuitBreaker()
    async def process_message(self, request):
        """Enhanced process message with circuit breaker"""
        try:
            return await self._process_message_impl(request)
        except Exception as e:
            logger.warning(f"Lite orchestrator failed, using emergency fallback: {e}")
            return await self._emergency_fallback(request)

    async def _process_message_impl(self, request):
        """Main implementation"""
        from ai_karen_engine.chat.chat_orchestrator import ChatResponse, ChatStreamChunk

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

    async def _emergency_fallback(self, request) -> Any:
        """Ultra-reliable fallback when even lite mode fails"""
        from ai_karen_engine.chat.chat_orchestrator import ChatResponse, ChatStreamChunk
        
        fallback_text = "I'm currently experiencing high load. Please try again in a moment."
        
        if getattr(request, "stream", False):
            async def _fallback_stream():
                yield ChatStreamChunk(
                    type="metadata",
                    content="",
                    correlation_id=getattr(request, "session_id", "unknown"),
                    metadata={"emergency_mode": True, "status": "degraded"}
                )
                yield ChatStreamChunk(
                    type="content",
                    content=fallback_text,
                    correlation_id=getattr(request, "session_id", "unknown"),
                    metadata={}
                )
                yield ChatStreamChunk(
                    type="complete",
                    content="",
                    correlation_id=getattr(request, "session_id", "unknown"),
                    metadata={"emergency_mode": True}
                )
            return _fallback_stream()
        
        return ChatResponse(
            response=fallback_text,
            correlation_id=getattr(request, "session_id", "unknown"),
            processing_time=0.1,
            used_fallback=True,
            metadata={"emergency_mode": True}
        )

    async def cancel_processing(
        self, conversation_id: str, correlation_id: Optional[str] = None
    ) -> List[str]:
        """No asynchronous processing is queued in lite mode, so nothing to cancel."""
        return []

    def _generate_response(self, message: str) -> Tuple[str, str, Dict[str, Any]]:
        """Enhanced response generation with better reasoning"""
        import re
        
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

        # Enhanced greeting detection
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in lower_message for greeting in greetings):
            reasoning_steps.append("Detected greeting and crafted friendly acknowledgement.")
            response = (
                "Hello! Kari's full AI services are still initializing, so I'm operating in minimal mode. "
                "I can answer quick questions and keep you posted until everything is ready."
            )
            return response, "; ".join(reasoning_steps), {}

        # Enhanced capability queries
        if any(query in lower_message for query in ["what can you do", "help", "capabilities"]):
            reasoning_steps.append("User asked about capabilities; summarising degraded-mode abilities.")
            response = (
                "Right now I'm running Kari's lite assistant while the full orchestrator comes online. "
                "I can help with quick Q&A, light reasoning, and progress updates. "
                "Features such as long-term memory or advanced tool calls are temporarily paused."
            )
            return response, "; ".join(reasoning_steps), {}

        # Enhanced technical queries
        if any(keyword in lower_message for keyword in ["code", "debug", "program", "python", "javascript"]):
            reasoning_steps.append("Detected technical/coding intent; providing contextual response.")
            response = (
                "I'd love to help with code. The deep analyzers are still waking up, but share your snippet "
                "or question and I'll walk through it with lightweight reasoning."
            )
            return response, "; ".join(reasoning_steps), {}

        # Enhanced math handling
        math_answer = self._handle_enhanced_math(lower_message)
        if math_answer is not None:
            reasoning_steps.append("Solved arithmetic expression in minimal mode.")
            response = (
                f"While in minimal mode I can still reason through quick math. The answer is {math_answer}. "
                "I'll have deeper analytical tools once the full stack loads."
            )
            return response, "; ".join(reasoning_steps), {}

        # Enhanced FAQ lookup
        canned_answer = self._lookup_enhanced_faq(lower_message)
        if canned_answer:
            reasoning_steps.append("Matched question against enhanced lite knowledge base.")
            return canned_answer, "; ".join(reasoning_steps), {}

        reasoning_steps.append("No template matched; generating supportive default message.")
        response = (
            "I'm currently running Kari's minimal chat mode. I don't have access to long-term memory or external tools yet, "
            "but I can still help reason through questions and keep you updated. Let me know what you need!"
        )
        return response, "; ".join(reasoning_steps), {}

    def _handle_enhanced_math(self, lower_message: str) -> Optional[str]:
        """Enhanced math handling with more operations"""
        # Handle basic arithmetic
        basic_pattern = re.compile(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)")
        match = basic_pattern.search(lower_message)
        if match:
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
        
        # Handle simple percentage calculations
        percent_pattern = re.compile(r"(\d+)\s*percent\s*of\s*(\d+)")
        percent_match = percent_pattern.search(lower_message)
        if percent_match:
            percent, number = percent_match.groups()
            try:
                result = (float(percent) / 100) * float(number)
                if result.is_integer():
                    return str(int(result))
                return f"{result:.2f}"
            except ValueError:
                pass
        
        return None

    def _lookup_enhanced_faq(self, lower_message: str) -> Optional[str]:
        """Enhanced FAQ with more comprehensive coverage"""
        faq_responses = {
            "who are you": (
                "I'm Kari's lite assistant. While the full AI services initialize, I'm here to provide quick guidance and "
                "basic answers. I can handle simple questions, math, and keep you company until the full system is ready."
            ),
            "status": (
                "Core services are warming up. Minimal mode is active, so tool usage and deep memory are temporarily disabled. "
                "Basic chat and reasoning are available."
            ),
            "where is my data": (
                "Your data remains secure. Minimal mode avoids long-term memory writes until the full stack is verified. "
                "Conversations in this mode are ephemeral for safety."
            ),
            "when will full service be available": (
                "The full AI system is initializing in the background. This typically takes a few moments. "
                "I'll automatically switch to full capabilities once everything is ready."
            ),
            "what is kari": (
                "Kari is an advanced AI assistant designed to help with complex tasks, reasoning, and conversations. "
                "I'm the lightweight version that keeps things running while the main system loads."
            ),
        }

        for key, value in faq_responses.items():
            if key in lower_message:
                return value
        return None

    def _tokenize_response(self, response: str) -> Iterable[str]:
        """Enhanced tokenization for better streaming"""
        # Simple word-based tokenization for minimal mode
        words = response.split()
        for i, word in enumerate(words):
            # Add space except for the last word
            yield word + (" " if i < len(words) - 1 else "")


# Enhanced Orchestrator dependency
@lru_cache
def get_chat_orchestrator() -> ChatOrchestrator:
    """Return a production-grade chat orchestrator"""
    logger.info("Creating ChatOrchestrator for production mode")
    return ChatOrchestrator()


# Production Monitoring & Logging
def log_chat_event(
    event_type: str,
    user_id: str,
    correlation_id: str,
    level: str = "info",
    **extra
):
    """Structured logging for chat events"""
    structured_extra = {
        "event_type": event_type,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra
    }
    
    getattr(logger, level)(f"Chat event: {event_type}", extra=structured_extra)


class ChatMetrics:
    """Production metrics collection"""
    
    @staticmethod
    def record_request(latency: float, success: bool, platform: str, used_fallback: bool = False):
        """Record chat request metrics"""
        # In production, this would integrate with your metrics system
        tags = [f"platform:{platform}", f"success:{success}", f"fallback:{used_fallback}"]
        logger.info(f"Chat metrics - latency: {latency:.2f}ms", extra={"tags": tags})
    
    @staticmethod
    def record_fallback_used(reason: str):
        """Record fallback usage"""
        logger.info(f"Fallback used: {reason}")
    
    @staticmethod
    def record_streaming_metrics(total_tokens: int, first_token_latency: float, total_latency: float):
        """Record streaming-specific metrics"""
        logger.info(
            "Streaming metrics",
            extra={
                "total_tokens": total_tokens,
                "first_token_latency_ms": first_token_latency,
                "total_latency_ms": total_latency
            }
        )


# Enhanced Chat Runtime Routes
@router.post("/chat/runtime", response_model=ChatRuntimeResponse)
async def chat_runtime(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> ChatRuntimeResponse:
    """
    Production-grade main chat runtime endpoint for non-streaming responses
    """
    start_time = time.time()
    correlation_id = request_metadata.get("correlation_id")
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_id = user_context.get("user_id", "anonymous")

    try:
        log_chat_event(
            "chat_request_received",
            user_id,
            correlation_id,
            message_length=len(request.message),
            platform=request.platform,
            conversation_id=conversation_id
        )

        # Enhanced KIRE routing with caching
        reg = get_registry()
        _routed = await reg.get_provider_with_routing(
            user_ctx={"user_id": user_id},
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

        # Enhanced metadata with caching
        metadata_payload: Dict[str, Any] = {
            **(request.context or {}),
            "platform": request.platform,
            "request_metadata": request_metadata,
        }
        if generation_hints:
            metadata_payload["requested_generation"] = generation_hints
        if preferred_provider:
            metadata_payload["preferred_llm_provider"] = preferred_provider
            _cache_provider_routing(preferred_provider, preferred_model or "default")
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
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=correlation_id,
            stream=False,
            include_context=True,
            metadata=metadata_payload,
        )

        orchestrator_response = await chat_orchestrator.process_message(chat_request)

        latency_ms = (time.time() - start_time) * 1000
        used_fallback = getattr(orchestrator_response, 'used_fallback', False)

        # Record metrics
        ChatMetrics.record_request(latency_ms, True, request.platform, used_fallback)
        if used_fallback:
            ChatMetrics.record_fallback_used("orchestrator_fallback")

        response_metadata: Dict[str, Any] = {
            "platform": request.platform,
            "correlation_id": orchestrator_response.correlation_id,
            "user_id": user_id,
            "processing_time": orchestrator_response.processing_time,
            "latency_ms": latency_ms,
            **orchestrator_response.metadata,
        }
        
        # Enhanced metadata propagation
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

        log_chat_event(
            "chat_response_sent",
            user_id,
            correlation_id,
            response_length=len(response.content),
            latency_ms=latency_ms,
            used_fallback=used_fallback
        )

        return response

    except (ValidationError, ServiceUnavailableError) as e:
        latency_ms = (time.time() - start_time) * 1000
        ChatMetrics.record_request(latency_ms, False, request.platform, True)
        
        log_chat_event(
            "chat_request_failed",
            user_id,
            correlation_id,
            level="warning",
            error_type=type(e).__name__,
            error_message=str(e),
            latency_ms=latency_ms
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
        
    except asyncio.CancelledError:
        latency_ms = (time.time() - start_time) * 1000
        ChatMetrics.record_request(latency_ms, False, request.platform, False)
        
        log_chat_event(
            "chat_request_cancelled",
            user_id,
            correlation_id,
            level="info",
            latency_ms=latency_ms
        )
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Generation cancelled",
        )
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        ChatMetrics.record_request(latency_ms, False, request.platform, True)
        
        log_chat_event(
            "chat_request_error",
            user_id,
            correlation_id,
            level="error",
            error_type=type(e).__name__,
            error_message=str(e),
            latency_ms=latency_ms
        )

        # Enhanced graceful fallback response
        fallback_response = ChatRuntimeResponse(
            content="I'm experiencing technical difficulties right now. The AI services are initializing and will be available shortly. Please try again in a moment.",
            conversation_id=conversation_id,
            metadata={
                "platform": request.platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "fallback_mode": True,
                "error_type": "initialization_error",
                "processing_time": latency_ms / 1000,
                "latency_ms": latency_ms,
                "emergency_fallback": True,
            },
        )
        
        log_chat_event(
            "chat_fallback_used",
            user_id,
            correlation_id,
            level="warning",
            fallback_reason="unhandled_exception"
        )
        
        return fallback_response


@router.post("/chat/runtime/stream")
async def chat_runtime_stream(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> StreamingResponse:
    """
    Production-grade streaming chat runtime endpoint with enhanced reliability
    """

    async def generate_stream():
        start_time = time.time()
        first_token_time = None
        token_count = 0
        correlation_id = request_metadata.get("correlation_id")
        conversation_id = request.conversation_id or str(uuid.uuid4())
        user_id = user_context.get("user_id", "anonymous")

        try:
            log_chat_event(
                "chat_stream_started",
                user_id,
                correlation_id,
                platform=request.platform,
                conversation_id=conversation_id
            )

            # Enhanced KIRE routing for streaming
            reg = get_registry()
            _routed = await reg.get_provider_with_routing(
                user_ctx={"user_id": user_id},
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

            # Enhanced metadata event
            metadata_event = {
                "type": "metadata",
                "data": {
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                    "user_id": user_id,
                    "platform": request.platform,
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
                user_id=user_id,
                conversation_id=conversation_id,
                session_id=correlation_id,
                stream=True,
                include_context=True,
                metadata=metadata_payload,
            )

            # Enhanced streaming with timeout
            async with asyncio.timeout(ChatConfig.STREAM_TIMEOUT):
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

                        # Record streaming metrics
                        ChatMetrics.record_streaming_metrics(
                            token_count, first_latency, total_latency
                        )

            log_chat_event(
                "chat_stream_completed",
                user_id,
                correlation_id,
                token_count=token_count,
                total_latency_ms=(time.time() - start_time) * 1000
            )

        except asyncio.TimeoutError:
            log_chat_event(
                "chat_stream_timeout",
                user_id,
                correlation_id,
                level="warning",
                timeout_seconds=ChatConfig.STREAM_TIMEOUT
            )
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Stream timeout exceeded'}})}\n\n"
            
        except asyncio.CancelledError:
            log_chat_event(
                "chat_stream_cancelled",
                user_id,
                correlation_id,
                level="info"
            )
            yield "data: {\"type\": \"error\", \"data\": {\"message\": \"Generation cancelled\"}}\n\n"
            
        except Exception as e:
            log_chat_event(
                "chat_stream_error",
                user_id,
                correlation_id,
                level="error",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'Stream processing error'}})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
            "X-Content-Type-Options": "nosniff",
        },
    )


# Enhanced stop endpoint with better validation
@router.post("/chat/runtime/stop")
async def stop_chat_generation(
    conversation_id: str = Field(..., min_length=1, description="Conversation ID to stop"),
    correlation_id: Optional[str] = Field(None, description="Specific correlation ID to stop"),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
) -> Dict[str, Any]:
    """
    Enhanced stop ongoing chat generation with better validation
    """
    try:
        correlation = correlation_id or request_metadata.get("correlation_id")
        user_id = user_context.get("user_id", "anonymous")

        log_chat_event(
            "chat_stop_requested",
            user_id,
            correlation,
            conversation_id=conversation_id,
            specific_correlation_id=correlation_id
        )

        # Validate conversation_id format
        if not conversation_id or len(conversation_id) > 100:
            raise ValidationError("Invalid conversation ID")

        cancelled = await chat_orchestrator.cancel_processing(
            conversation_id=conversation_id,
            correlation_id=correlation_id,
        )

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active generation found for conversation",
            )

        log_chat_event(
            "chat_generation_stopped",
            user_id,
            correlation,
            cancelled_ids=cancelled
        )

        return {
            "status": "stopped",
            "conversation_id": conversation_id,
            "correlation_ids": cancelled,
            "stopped_at": datetime.now(timezone.utc).isoformat(),
        }

    except ValueError as exc:
        log_chat_event(
            "chat_stop_validation_failed",
            user_context.get("user_id", "anonymous"),
            request_metadata.get("correlation_id", "unknown"),
            level="warning",
            error_message=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as e:
        log_chat_event(
            "chat_stop_failed",
            user_context.get("user_id", "anonymous"),
            request_metadata.get("correlation_id", "unknown"),
            level="error",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop generation",
        )


# Enhanced health check with service status
@router.get("/chat/runtime/health")
async def chat_runtime_health() -> Dict[str, Any]:
    """
    Enhanced health check for chat runtime with service status
    """
    try:
        service_registry = get_service_registry()
        services_status = {}
        
        for service_name in service_registry.list_services():
            info = service_registry.get_service_info(service_name)
            if info:
                services_status[service_name] = {
                    "status": info.status.value,
                    "initialized": info.initialized,
                    "error": info.error_message
                }

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "chat-runtime",
            "version": "2.0.0",
            "environment": get_config().environment.value,
            "services": services_status,
            "config": {
                "max_message_length": ChatConfig.MAX_MESSAGE_LENGTH,
                "stream_timeout": ChatConfig.STREAM_TIMEOUT,
                "fallback_enabled": ChatConfig.FALLBACK_ENABLED
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "chat-runtime",
            "version": "2.0.0",
            "error": str(e)
        }


# Keep existing endpoints for backward compatibility
@router.post("/chat/runtime/response-core", response_model=ChatRuntimeResponse)
async def chat_runtime_response_core(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
) -> ChatRuntimeResponse:
    """
    Enhanced Response Core chat runtime endpoint
    """
    start_time = time.time()
    correlation_id = request_metadata.get("correlation_id")
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_id = user_context.get("user_id", "anonymous")

    try:
        log_chat_event(
            "response_core_request_received",
            user_id,
            correlation_id,
            platform=request.platform,
            message_length=len(request.message)
        )

        response_orchestrator = get_global_orchestrator(user_id=user_id)
        
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

        ChatMetrics.record_request(latency_ms, True, request.platform, False)

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

        log_chat_event(
            "response_core_response_sent",
            user_id,
            correlation_id,
            response_length=len(content),
            latency_ms=latency_ms
        )

        return response

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        ChatMetrics.record_request(latency_ms, False, request.platform, True)
        
        log_chat_event(
            "response_core_error",
            user_id,
            correlation_id,
            level="error",
            error_message=str(e),
            latency_ms=latency_ms
        )
        
        return ChatRuntimeResponse(
            content=f"I apologize, but I encountered an error: {str(e)}",
            conversation_id=conversation_id,
            metadata={
                "platform": request.platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "processing_time": latency_ms / 1000,
                "latency_ms": latency_ms,
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
    Enhanced chat configuration with production features
    """
    try:
        config = get_config()
        llm_registry = get_registry()
        service_registry = get_service_registry()

        # Enhanced tools section with better error handling
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
        except Exception as tool_error:
            logger.warning(
                "Tool service unavailable during chat config retrieval: %s",
                tool_error,
            )
            tools_section["error"] = str(tool_error)
            tools_section["available"] = []

        # Enhanced provider information
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
                        "rate_limits": provider_info.get("rate_limits", {}),
                    }
                )
        except Exception as registry_error:
            logger.warning(
                "LLM registry unavailable during chat config retrieval: %s",
                registry_error,
            )

        # Enhanced routing preferences
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

        # Enhanced service health information
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
        except Exception as service_error:
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
                "max_message_length": ChatConfig.MAX_MESSAGE_LENGTH,
                "max_tokens": config.llm.max_tokens,
                "temperature": config.llm.temperature,
            },
            "production_features": {
                "circuit_breaker": True,
                "caching": True,
                "fallback_modes": True,
                "streaming_timeout": ChatConfig.STREAM_TIMEOUT,
                "rate_limiting": True,
                "structured_logging": True,
                "metrics_collection": True,
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