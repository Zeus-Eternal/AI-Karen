"""
Chat Runtime API Routes
Production-grade unified chat endpoint for all platforms (Web, Desktop, Mobile)
Backed by:
- Prompt-first orchestration
- LLM registry routing (KIRE-style)
- Fallback-safe Lite orchestrator
- Structured logging & metrics
- SSE streaming
"""

import asyncio
import html
import json
import time
import uuid
from datetime import datetime, timezone
from functools import lru_cache, wraps
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional, Tuple, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Fallback for environments where pydantic is vendored internally
    from ai_karen_engine.pydantic_stub import BaseModel, Field, validator  # type: ignore

from ai_karen_engine.chat.chat_orchestrator import ChatRequest
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


# =========================================================
# ChatConfig - centralized runtime tuning (hydrated)
# =========================================================

class ChatConfig:
    """Production chat configuration (hydrated from global config when available)."""

    MAX_MESSAGE_LENGTH: int = 10000
    MAX_TOKENS_DEFAULT: int = 4096
    STREAM_TIMEOUT: float = 30.0
    FALLBACK_ENABLED: bool = True

    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60  # seconds

    CACHE_SIZE_USER_PREFS: int = 1000
    CACHE_SIZE_PROVIDER_ROUTING: int = 100

    @classmethod
    def hydrate_from_app_config(cls) -> None:
        try:
            config = get_config()
            chat_cfg = getattr(config, "chat", None)
            llm_cfg = getattr(config, "llm", None)

            if chat_cfg:
                cls.MAX_MESSAGE_LENGTH = int(
                    getattr(chat_cfg, "max_message_length", cls.MAX_MESSAGE_LENGTH)
                )
                cls.STREAM_TIMEOUT = float(
                    getattr(chat_cfg, "stream_timeout", cls.STREAM_TIMEOUT)
                )
                cls.FALLBACK_ENABLED = bool(
                    getattr(chat_cfg, "fallback_enabled", cls.FALLBACK_ENABLED)
                )

            if llm_cfg:
                cls.MAX_TOKENS_DEFAULT = int(
                    getattr(llm_cfg, "max_tokens", cls.MAX_TOKENS_DEFAULT)
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ChatConfig hydration failed; using safe defaults",
                extra={"error": str(exc)},
            )


ChatConfig.hydrate_from_app_config()


# =========================================================
# Exceptions
# =========================================================

class ChatRuntimeError(Exception):
    """Base exception for chat runtime errors."""


class ValidationError(ChatRuntimeError):
    """Request validation errors."""


class ServiceUnavailableError(ChatRuntimeError):
    """Service initialization / availability errors."""


class RateLimitExceededError(ChatRuntimeError):
    """Rate limiting errors."""


# =========================================================
# Models
# =========================================================

class ChatMessage(BaseModel):
    """Enhanced chat message model with validation."""

    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(
        ...,
        min_length=1,
        max_length=ChatConfig.MAX_MESSAGE_LENGTH,
        description="Message content",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator("role")
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant", "system"):
            raise ValueError("role must be user, assistant, or system")
        return v

    @validator("content")
    def sanitize_content(cls, v: str) -> str:
        v = str(v)
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return html.escape(v)


class ToolCall(BaseModel):
    """Tool call record."""

    id: str = Field(..., description="Unique tool call ID")
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    status: str = Field(default="pending", description="Tool execution status")


class MemoryOperation(BaseModel):
    """Memory operation audit entry."""

    id: str = Field(..., description="Unique operation ID")
    operation_type: str = Field(..., description="store | retrieve | update | delete")
    memory_tier: str = Field(..., description="short_term | long_term | persistent")
    content: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SanitizedChatRuntimeRequest(BaseModel):
    """Production chat request model with strict validation & sanitization."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=ChatConfig.MAX_MESSAGE_LENGTH,
        description="User message",
    )
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tools: Optional[List[str]] = Field(default_factory=list)
    memory_context: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    platform: Optional[str] = Field(default="web")
    conversation_id: Optional[str] = None
    stream: bool = Field(default=True)
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)

    @validator("message")
    def sanitize_message(cls, v: str) -> str:
        msg = (v or "").strip()
        if not msg:
            raise ValidationError("Message cannot be empty")
        if len(msg) > ChatConfig.MAX_MESSAGE_LENGTH:
            raise ValidationError(
                f"Message exceeds maximum length of {ChatConfig.MAX_MESSAGE_LENGTH} characters"
            )
        return html.escape(msg)

    @validator("tools")
    def validate_tools(cls, v: List[str]) -> List[str]:
        if not v:
            return v
        try:
            tool_service = get_global_tool_service()
            valid = set(tool_service.list_tools())
            for name in v:
                if name not in valid:
                    raise ValidationError(f"Invalid tool requested: {name}")
        except Exception:
            # Defer failures to actual tool resolution time.
            pass
        return v

    @validator("temperature")
    def validate_temperature(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 2.0):
            raise ValidationError("Temperature must be between 0.0 and 2.0")
        return v


class ChatRuntimeResponse(BaseModel):
    """Chat runtime response payload."""

    content: str = Field(..., description="Response content")
    tool_calls: List[ToolCall] = Field(default_factory=list)
    memory_operations: List[MemoryOperation] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatError(BaseModel):
    """Structured error response."""

    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    suggestion: Optional[str] = None


class StopRequest(BaseModel):
    """Stop request body."""

    conversation_id: str = Field(..., min_length=1)
    correlation_id: Optional[str] = None


# =========================================================
# Utility: Metadata & Validation
# =========================================================

async def get_request_metadata(request: Request) -> Dict[str, Any]:
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


async def validate_chat_request(
    request: SanitizedChatRuntimeRequest,
) -> SanitizedChatRuntimeRequest:
    if request.max_tokens is not None:
        if request.max_tokens <= 0:
            raise ValidationError("max_tokens must be greater than zero")
        if request.max_tokens > 100000:
            raise ValidationError("max_tokens exceeds reasonable limit")
    return request


# =========================================================
# Rate Limiter (in-memory, per user/IP)
# =========================================================

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._store: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, key: str) -> None:
        now = time.time()
        async with self._lock:
            recent = [t for t in self._store.get(key, []) if t > now - self.window]
            if len(recent) >= self.max_requests:
                raise RateLimitExceededError("Rate limit exceeded for this identity.")
            recent.append(now)
            self._store[key] = recent


rate_limiter = RateLimiter(
    max_requests=ChatConfig.RATE_LIMIT_REQUESTS,
    window_seconds=ChatConfig.RATE_LIMIT_WINDOW,
)


# =========================================================
# Preference & Routing Cache
# =========================================================

@lru_cache(maxsize=ChatConfig.CACHE_SIZE_USER_PREFS)
def _cache_user_preferences(
    user_id: str, platform: str
) -> Tuple[Optional[str], Optional[str]]:
    try:
        config = get_config()
        profile_data = getattr(config, "user_profiles", {}) or {}
        for profile in profile_data.get("profiles", []):
            if not profile.get("is_active", False):
                continue
            assignments = profile.get("assignments", {})
            chat_assignment = assignments.get("chat", {})
            if isinstance(chat_assignment, dict):
                return chat_assignment.get("provider"), chat_assignment.get("model")
    except Exception:  # noqa: BLE001
        pass
    return None, None


@lru_cache(maxsize=ChatConfig.CACHE_SIZE_PROVIDER_ROUTING)
def _cache_provider_routing(provider: str, model: str) -> Dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "cached_at": time.time(),
    }


def _extract_generation_preferences(
    request: SanitizedChatRuntimeRequest,
) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    hints: Dict[str, Any] = {}

    def first(values: Iterable[Optional[str]]) -> Optional[str]:
        for v in values:
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    user_prefs = request.user_preferences or {}
    context_prefs = (request.context or {}).get("llm_preferences", {}) or {}

    cached_provider, cached_model = _cache_user_preferences(
        user_prefs.get("user_id", "default"), request.platform or "web"
    )

    provider = first(
        (
            request.provider,
            user_prefs.get("preferred_llm_provider"),
            context_prefs.get("preferred_llm_provider"),
            cached_provider,
        )
    )
    if provider:
        hints["provider"] = provider

    model = first(
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
        t = user_prefs.get("temperature")
        if isinstance(t, (int, float)):
            temperature = float(t)
    if temperature is not None:
        hints["temperature"] = max(0.0, min(2.0, float(temperature)))

    max_tokens = request.max_tokens
    if max_tokens is None:
        mt = user_prefs.get("max_tokens")
        if isinstance(mt, int) and mt > 0:
            max_tokens = mt
    if max_tokens is not None:
        hints["max_tokens"] = min(int(max_tokens), 100000)

    return provider, model, hints


# =========================================================
# Circuit Breaker
# =========================================================

class CircuitBreaker:
    """Async circuit breaker used by the lite orchestrator."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, HALF_OPEN, OPEN

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            if self.state == "OPEN":
                if now - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise ServiceUnavailableError("Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                return result
            except Exception as exc:  # noqa: BLE001
                self.failures += 1
                self.last_failure_time = now
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                raise ServiceUnavailableError(f"Circuit breaker triggered: {exc}") from exc

        return wrapper


# =========================================================
# LiteChatOrchestrator - hardened fallback
# =========================================================

class LiteChatOrchestrator:
    """
    Ultra-reliable minimal orchestrator when primary orchestration is unavailable.

    - No external network calls
    - No long-term writes
    - Deterministic, safe, logged
    """

    def __init__(self) -> None:
        self._restricted_ops = [
            "long_term_memory_write",
            "long_term_memory_read",
            "vector_memory_query",
        ]
        self._breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

    async def process_message(self, request: ChatRequest):
        from ai_karen_engine.chat.chat_orchestrator import ChatResponse, ChatStreamChunk

        @self._breaker
        async def _run():
            start_time = time.perf_counter()
            correlation_id = getattr(request, "session_id", str(uuid.uuid4()))
            message = str(getattr(request, "message", "") or "")

            response_text, reasoning, extra_metadata = self._generate_response(message)

            base_metadata: Dict[str, Any] = {
                "fallback_mode": True,
                "mode": "lite",
                "status": "degraded",
                "message": "Kari lite orchestrator handling request.",
                "restricted_operations": list(self._restricted_ops),
                "capabilities": {
                    "reasoning": "basic",
                    "qa": "lightweight",
                    "tools": "disabled",
                },
                "reasoning_summary": reasoning,
            }
            base_metadata.update(extra_metadata or {})

            processing_time = time.perf_counter() - start_time
            base_metadata.setdefault("local_model", "kari-lite-rule-engine")
            base_metadata["processing_time"] = processing_time
            base_metadata["response_length"] = len(response_text)

            if getattr(request, "stream", False):

                async def _stream() -> AsyncGenerator[ChatStreamChunk, None]:
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

                return _stream()

            return ChatResponse(
                response=response_text,
                correlation_id=correlation_id,
                processing_time=processing_time,
                used_fallback=True,
                metadata=base_metadata,
            )

        return await _run()

    async def cancel_processing(
        self, conversation_id: str, correlation_id: Optional[str] = None
    ) -> List[str]:
        # Lite has no queued async work; nothing to cancel.
        return []

    async def _emergency_fallback(self, request: ChatRequest):
        from ai_karen_engine.chat.chat_orchestrator import ChatResponse, ChatStreamChunk

        fallback_text = (
            "Degraded safety mode active. Core orchestrator unavailable; responding with minimal guarantees."
        )
        correlation_id = getattr(request, "session_id", "unknown")

        if getattr(request, "stream", False):

            async def _stream():
                yield ChatStreamChunk(
                    type="metadata",
                    content="",
                    correlation_id=correlation_id,
                    metadata={"emergency_mode": True, "status": "degraded"},
                )
                yield ChatStreamChunk(
                    type="content",
                    content=fallback_text,
                    correlation_id=correlation_id,
                    metadata={},
                )
                yield ChatStreamChunk(
                    type="complete",
                    content="",
                    correlation_id=correlation_id,
                    metadata={"emergency_mode": True},
                )

            return _stream()

        return ChatResponse(
            response=fallback_text,
            correlation_id=correlation_id,
            processing_time=0.05,
            used_fallback=True,
            metadata={"emergency_mode": True},
        )

    def _generate_response(
        self, message: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        import re

        normalized = (message or "").strip()
        lower = normalized.lower()
        reasoning: List[str] = []

        if not normalized:
            reasoning.append("Empty input; returning guidance from lite mode.")
            return (
                "Lite runtime online. Send a prompt and I will handle it safely while full systems operate separately.",
                "; ".join(reasoning),
                {},
            )

        if any(g in lower for g in ("hello", " hi", "hey", "good morning", "good evening")):
            reasoning.append("Greeting detected.")
            return (
                "Kari's chat runtime is active. Primary brain routes above; I'm the hardened safety net.",
                "; ".join(reasoning),
                {},
            )

        if any(q in lower for q in ("what can you do", "help", "capabilities")):
            reasoning.append("Capabilities inquiry.")
            return (
                "This path guarantees a response even if advanced subsystems fail. I keep messages safe, contextual, and deterministic.",
                "; ".join(reasoning),
                {},
            )

        if any(k in lower for k in ("code", "debug", "python", "javascript", "typescript")):
            reasoning.append("Technical-intent detected.")
            return (
                "I can outline logic and safeguards here. Full deep-dive is handled via Kari's main orchestrator layer.",
                "; ".join(reasoning),
                {},
            )

        # arithmetic
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", lower)
        if m:
            a_str, op, b_str = m.groups()
            try:
                a = float(a_str)
                b = float(b_str)
                if op == "/" and b == 0:
                    result = "undefined (division by zero)"
                else:
                    if op == "+":
                        val = a + b
                    elif op == "-":
                        val = a - b
                    elif op == "*":
                        val = a * b
                    else:
                        val = a / b
                    result = (
                        str(int(val))
                        if float(val).is_integer()
                        else f"{val:.4f}".rstrip("0").rstrip(".")
                    )
                reasoning.append("Inline arithmetic solved in lite mode.")
                return (
                    f"The result is {result}.",
                    "; ".join(reasoning),
                    {},
                )
            except Exception:  # noqa: BLE001
                pass

        pm = re.search(r"(\d+)\s*percent\s*of\s*(\d+)", lower)
        if pm:
            pct, base = pm.groups()
            try:
                val = (float(pct) / 100.0) * float(base)
                result = str(int(val)) if float(val).is_integer() else f"{val:.2f}"
                reasoning.append("Percentage calculation handled.")
                return (
                    f"{pct}% of {base} is {result}.",
                    "; ".join(reasoning),
                    {},
                )
            except Exception:  # noqa: BLE001
                pass

        faq = {
            "who are you": (
                "This is Kari's resilient chat runtime fallback. If anything upstream breaks, I don't."
            ),
            "status": (
                "If you're seeing this style, the system is prioritizing safety and resilience while core services are verified."
            ),
            "where is my data": (
                "Lite mode avoids long-term writes while upstream health is uncertain. Persistent policies live in the main services."
            ),
        }
        for key, text in faq.items():
            if key in lower:
                reasoning.append(f"Matched FAQ: {key}")
                return text, "; ".join(reasoning), {}

        reasoning.append("Default safe fallback message used.")
        return (
            "Lite runtime is active. I ensure a stable response path while Kari's advanced stack operates above.",
            "; ".join(reasoning),
            {},
        )

    def _tokenize_response(self, response: str) -> Iterable[str]:
        words = response.split()
        for i, w in enumerate(words):
            yield w + (" " if i < len(words) - 1 else "")


# =========================================================
# Orchestrator Resolver (Primary + Fallback)
# =========================================================

@lru_cache
def get_chat_orchestrator() -> Any:
    """
    Resolve the primary orchestrator with automatic Lite fallback.
    """
    try:
        from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator as PrimaryChatOrchestrator

        orchestrator = PrimaryChatOrchestrator()
        logger.info("Using PrimaryChatOrchestrator for chat runtime")
        return orchestrator
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "PrimaryChatOrchestrator init failed; using LiteChatOrchestrator",
            extra={"error": str(exc)},
        )
        return LiteChatOrchestrator()


# =========================================================
# Logging & Metrics
# =========================================================

def log_chat_event(
    event_type: str,
    user_id: str,
    correlation_id: str,
    level: str = "info",
    **extra: Any,
) -> None:
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    log_fn = getattr(logger, level, logger.info)
    log_fn(f"chat-runtime:{event_type}", extra=payload)


class ChatMetrics:
    @staticmethod
    def record_request(
        latency_ms: float,
        success: bool,
        platform: str,
        used_fallback: bool = False,
    ) -> None:
        logger.info(
            "chat-metrics:request",
            extra={
                "latency_ms": round(latency_ms, 2),
                "success": success,
                "platform": platform,
                "fallback": used_fallback,
            },
        )

    @staticmethod
    def record_fallback_used(reason: str) -> None:
        logger.info("chat-metrics:fallback_used", extra={"reason": reason})

    @staticmethod
    def record_streaming_metrics(
        total_tokens: int,
        first_token_latency_ms: float,
        total_latency_ms: float,
    ) -> None:
        logger.info(
            "chat-metrics:streaming",
            extra={
                "total_tokens": total_tokens,
                "first_token_latency_ms": round(first_token_latency_ms, 2),
                "total_latency_ms": round(total_latency_ms, 2),
            },
        )


# =========================================================
# /chat/runtime  (Non-streaming)
# =========================================================

@router.post("/chat/runtime", response_model=ChatRuntimeResponse)
async def chat_runtime(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: Any = Depends(get_chat_orchestrator),
) -> ChatRuntimeResponse:
    start_time = time.time()
    correlation_id = request_metadata.get("correlation_id")
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_id = user_context.get("user_id", "anonymous")
    platform = request.platform or "web"
    identity_key = f"{user_id}:{request_metadata.get('ip_address', 'unknown')}"

    try:
        await rate_limiter.check(identity_key)

        log_chat_event(
            "chat_request_received",
            user_id,
            correlation_id,
            message_length=len(request.message),
            platform=platform,
            conversation_id=conversation_id,
        )

        reg = get_registry()
        _routed = await reg.get_provider_with_routing(
            user_ctx={"user_id": user_id},
            query=request.message,
            task_type="chat",
            khrp_step="output_rendering",
            requirements={},
        )
        kire_decision = _routed.get("decision")

        user_provider, user_model, generation_hints = _extract_generation_preferences(
            request
        )
        preferred_provider = user_provider or (
            getattr(kire_decision, "provider", None) if kire_decision else None
        )
        preferred_model = user_model or (
            getattr(kire_decision, "model", None) if kire_decision else None
        )

        metadata_payload: Dict[str, Any] = {
            **(request.context or {}),
            "platform": platform,
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
                "provider": getattr(kire_decision, "provider", None),
                "model": getattr(kire_decision, "model", None),
                "reason": getattr(kire_decision, "reasoning", ""),
                "confidence": getattr(kire_decision, "confidence", 0.0),
                "fallback_chain": getattr(kire_decision, "fallback_chain", []),
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

        latency_ms = (time.time() - start_time) * 1000.0
        used_fallback = bool(getattr(orchestrator_response, "used_fallback", False))

        ChatMetrics.record_request(latency_ms, True, platform, used_fallback)
        if used_fallback:
            ChatMetrics.record_fallback_used("orchestrator_fallback")

        response_metadata: Dict[str, Any] = {
            "platform": platform,
            "correlation_id": getattr(
                orchestrator_response, "correlation_id", correlation_id
            ),
            "user_id": user_id,
            "processing_time": getattr(
                orchestrator_response, "processing_time", latency_ms / 1000.0
            ),
            "latency_ms": latency_ms,
            **getattr(orchestrator_response, "metadata", {}),
        }

        if generation_hints and "requested_generation" not in response_metadata:
            response_metadata["requested_generation"] = generation_hints
        if preferred_provider and "preferred_llm_provider" not in response_metadata:
            response_metadata["preferred_llm_provider"] = preferred_provider
        if preferred_model and "preferred_model" not in response_metadata:
            response_metadata["preferred_model"] = preferred_model
        if kire_decision and "kire_metadata" not in response_metadata:
            response_metadata["kire_metadata"] = {
                "provider": getattr(kire_decision, "provider", None),
                "model": getattr(kire_decision, "model", None),
                "reason": getattr(kire_decision, "reasoning", ""),
                "confidence": getattr(kire_decision, "confidence", 0.0),
            }

        response = ChatRuntimeResponse(
            content=getattr(orchestrator_response, "response", ""),
            conversation_id=conversation_id,
            metadata=response_metadata,
        )

        log_chat_event(
            "chat_response_sent",
            user_id,
            correlation_id,
            response_length=len(response.content),
            latency_ms=latency_ms,
            used_fallback=used_fallback,
        )

        return response

    except RateLimitExceededError as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, False, platform, False)
        log_chat_event(
            "chat_rate_limited",
            user_id,
            correlation_id,
            level="warning",
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except (ValidationError, ServiceUnavailableError) as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, False, platform, True)
        log_chat_event(
            "chat_request_failed",
            user_id,
            correlation_id,
            level="warning",
            error_type=type(exc).__name__,
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        status_code = (
            status.HTTP_400_BAD_REQUEST
            if isinstance(exc, ValidationError)
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    except asyncio.CancelledError:
        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, False, platform, False)
        log_chat_event(
            "chat_request_cancelled",
            user_id,
            correlation_id,
            level="info",
            latency_ms=latency_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Generation cancelled",
        )

    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, False, platform, True)
        log_chat_event(
            "chat_request_error",
            user_id,
            correlation_id,
            level="error",
            error_type=type(exc).__name__,
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        fallback_response = ChatRuntimeResponse(
            content=(
                "Runtime is in a degraded state. A safe fallback response path "
                "handled this request while core services stabilize."
            ),
            conversation_id=conversation_id,
            metadata={
                "platform": platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "fallback_mode": True,
                "error_type": "unhandled_exception",
                "processing_time": latency_ms / 1000.0,
                "latency_ms": latency_ms,
                "emergency_fallback": True,
            },
        )
        log_chat_event(
            "chat_fallback_used",
            user_id,
            correlation_id,
            level="warning",
            fallback_reason="unhandled_exception",
        )
        return fallback_response


# =========================================================
# /chat/runtime/stream  (SSE streaming)
# =========================================================

@router.post("/chat/runtime/stream")
async def chat_runtime_stream(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: Any = Depends(get_chat_orchestrator),
) -> StreamingResponse:
    platform = request.platform or "web"

    async def generate_stream():
        start_time = time.time()
        first_token_time: Optional[float] = None
        token_count = 0
        correlation_id = request_metadata.get("correlation_id")
        conversation_id = request.conversation_id or str(uuid.uuid4())
        user_id = user_context.get("user_id", "anonymous")
        identity_key = f"{user_id}:{request_metadata.get('ip_address', 'unknown')}"

        try:
            await rate_limiter.check(identity_key)

            log_chat_event(
                "chat_stream_started",
                user_id,
                correlation_id,
                platform=platform,
                conversation_id=conversation_id,
            )

            reg = get_registry()
            _routed = await reg.get_provider_with_routing(
                user_ctx={"user_id": user_id},
                query=request.message,
                task_type="chat",
                khrp_step="output_rendering",
                requirements={},
            )
            kire_decision = _routed.get("decision")

            user_provider, user_model, generation_hints = _extract_generation_preferences(
                request
            )
            preferred_provider = user_provider or (
                getattr(kire_decision, "provider", None) if kire_decision else None
            )
            preferred_model = user_model or (
                getattr(kire_decision, "model", None) if kire_decision else None
            )

            metadata_event: Dict[str, Any] = {
                "type": "metadata",
                "data": {
                    "conversation_id": conversation_id,
                    "correlation_id": correlation_id,
                    "user_id": user_id,
                    "platform": platform,
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
                    "provider": getattr(kire_decision, "provider", None),
                    "model": getattr(kire_decision, "model", None),
                    "reason": getattr(kire_decision, "reasoning", ""),
                    "confidence": getattr(kire_decision, "confidence", 0.0),
                    "fallback_chain": getattr(kire_decision, "fallback_chain", []),
                }

            yield f"data: {json.dumps(metadata_event)}\n\n"

            metadata_payload: Dict[str, Any] = {
                **(request.context or {}),
                "platform": platform,
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
                    "provider": getattr(kire_decision, "provider", None),
                    "model": getattr(kire_decision, "model", None),
                    "reason": getattr(kire_decision, "reasoning", ""),
                    "confidence": getattr(kire_decision, "confidence", 0.0),
                    "fallback_chain": getattr(kire_decision, "fallback_chain", []),
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

            async with asyncio.timeout(ChatConfig.STREAM_TIMEOUT):
                stream = await chat_orchestrator.process_message(chat_request)

                async for chunk in stream:
                    ctype = getattr(chunk, "type", None)

                    if ctype == "content":
                        if first_token_time is None:
                            first_token_time = time.time()
                        token_count += 1
                        yield (
                            "data: "
                            + json.dumps(
                                {"type": "token", "data": {"token": chunk.content}}
                            )
                            + "\n\n"
                        )

                    elif ctype == "metadata":
                        yield (
                            "data: "
                            + json.dumps(
                                {"type": "metadata", "data": chunk.metadata}
                            )
                            + "\n\n"
                        )

                    elif ctype == "error":
                        yield (
                            "data: "
                            + json.dumps(
                                {
                                    "type": "error",
                                    "data": {
                                        "message": chunk.content,
                                        **(chunk.metadata or {}),
                                    },
                                }
                            )
                            + "\n\n"
                        )

                    elif ctype == "complete":
                        total_latency_ms = (time.time() - start_time) * 1000.0
                        first_latency_ms = (
                            (first_token_time - start_time) * 1000.0
                            if first_token_time
                            else total_latency_ms
                        )

                        completion_data: Dict[str, Any] = {
                            **(chunk.metadata or {}),
                            "total_tokens": token_count,
                            "latency_ms": total_latency_ms,
                            "first_token_latency_ms": first_latency_ms,
                        }

                        if generation_hints and "requested_generation" not in completion_data:
                            completion_data["requested_generation"] = generation_hints
                        if (
                            preferred_provider
                            and "preferred_llm_provider" not in completion_data
                        ):
                            completion_data[
                                "preferred_llm_provider"
                            ] = preferred_provider
                        if preferred_model and "preferred_model" not in completion_data:
                            completion_data["preferred_model"] = preferred_model

                        yield (
                            "data: "
                            + json.dumps(
                                {"type": "complete", "data": completion_data}
                            )
                            + "\n\n"
                        )

                        ChatMetrics.record_streaming_metrics(
                            token_count, first_latency_ms, total_latency_ms
                        )

            log_chat_event(
                "chat_stream_completed",
                user_id,
                correlation_id,
                token_count=token_count,
                total_latency_ms=(time.time() - start_time) * 1000.0,
            )

        except RateLimitExceededError as exc:
            log_chat_event(
                "chat_stream_rate_limited",
                user_id,
                correlation_id,
                level="warning",
                error_message=str(exc),
            )
            yield (
                "data: "
                + json.dumps({"type": "error", "data": {"message": str(exc)}})
                + "\n\n"
            )

        except asyncio.TimeoutError:
            log_chat_event(
                "chat_stream_timeout",
                user_id,
                correlation_id,
                level="warning",
                timeout_seconds=ChatConfig.STREAM_TIMEOUT,
            )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "data": {"message": "Stream timeout exceeded"},
                    }
                )
                + "\n\n"
            )

        except asyncio.CancelledError:
            log_chat_event(
                "chat_stream_cancelled",
                user_id,
                correlation_id,
                level="info",
            )
            yield (
                'data: {"type": "error", "data": {"message": "Generation cancelled"}}\n\n'
            )

        except Exception as exc:  # noqa: BLE001
            log_chat_event(
                "chat_stream_error",
                user_id,
                correlation_id,
                level="error",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "data": {"message": "Stream processing error"},
                    }
                )
                + "\n\n"
            )

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


# =========================================================
# /chat/runtime/stop
# =========================================================

@router.post("/chat/runtime/stop")
async def stop_chat_generation(
    body: StopRequest,
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
    chat_orchestrator: Any = Depends(get_chat_orchestrator),
) -> Dict[str, Any]:
    conversation_id = body.conversation_id
    correlation_id = body.correlation_id or request_metadata.get("correlation_id")
    user_id = user_context.get("user_id", "anonymous")

    try:
        if not conversation_id or len(conversation_id) > 100:
            raise ValidationError("Invalid conversation ID")

        log_chat_event(
            "chat_stop_requested",
            user_id,
            correlation_id,
            conversation_id=conversation_id,
            requested_correlation_id=body.correlation_id,
        )

        cancelled_ids: List[str] = []
        if hasattr(chat_orchestrator, "cancel_processing"):
            cancelled_ids = await chat_orchestrator.cancel_processing(
                conversation_id=conversation_id,
                correlation_id=body.correlation_id,
            )

        log_chat_event(
            "chat_generation_stopped",
            user_id,
            correlation_id,
            cancelled_ids=cancelled_ids,
        )

        return {
            "status": "stopped",
            "conversation_id": conversation_id,
            "correlation_ids": cancelled_ids,
            "stopped_at": datetime.now(timezone.utc).isoformat(),
        }

    except ValidationError as exc:
        log_chat_event(
            "chat_stop_validation_failed",
            user_id,
            correlation_id,
            level="warning",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:  # noqa: BLE001
        log_chat_event(
            "chat_stop_failed",
            user_id,
            correlation_id,
            level="error",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop generation",
        ) from exc


# =========================================================
# /chat/runtime/config
# =========================================================

@router.get("/chat/runtime/config")
async def get_chat_config(
    user_context: Dict[str, Any] = Depends(get_current_user_context),
) -> Dict[str, Any]:
    user_id = user_context.get("user_id", "anonymous")

    try:
        config = get_config()
        llm_registry = get_registry()
        service_registry = get_service_registry()

        def _cfg_get(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

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
        except Exception as tool_error:  # noqa: BLE001
            logger.warning(
                "Tool service unavailable during chat config retrieval",
                extra={"error": str(tool_error), "user_id": user_id},
            )
            tools_section["error"] = str(tool_error)

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
        except Exception as registry_error:  # noqa: BLE001
            logger.warning(
                "LLM registry unavailable during chat config retrieval",
                extra={"error": str(registry_error), "user_id": user_id},
            )

        profile_data = getattr(config, "user_profiles", {}) or {}
        active_profile_id = getattr(config, "active_profile", None) or profile_data.get(
            "active_profile"
        )
        profile_summaries: List[Dict[str, Any]] = []
        fallback_chain: List[str] = []
        default_provider = _cfg_get(config.llm, "provider", None)
        default_model = _cfg_get(config.llm, "model", None)

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
        except Exception as service_error:  # noqa: BLE001
            logger.warning(
                "Service registry introspection failed during chat config retrieval",
                extra={"error": str(service_error), "user_id": user_id},
            )

        ready_services = sum(
            1 for service in services_summary if service["status"] in ready_states
        )

        monitoring_config = getattr(config, "monitoring", {})
        web_ui_config = getattr(config, "web_ui", {})
        memory_config = getattr(config, "memory", {}) or {}

        response_payload = {
            "user": {
                "id": user_context.get("user_id"),
                "tenant_id": user_context.get("tenant_id"),
                "roles": user_context.get("roles", []),
            },
            "environment": {
                "name": getattr(getattr(config, "environment", None), "value", None),
                "debug": bool(getattr(config, "debug", False)),
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
                "enabled": bool(_cfg_get(memory_config, "enabled", True)),
                "provider": _cfg_get(memory_config, "provider", "local"),
                "embedding_dim": _cfg_get(memory_config, "embedding_dim", None),
                "decay_lambda": _cfg_get(memory_config, "decay_lambda", None),
                "ui_enabled": bool(
                    _cfg_get(web_ui_config, "enable_memory_integration", False)
                ),
            },
            "services": {
                "registered": len(services_summary),
                "ready": ready_services,
                "items": services_summary,
            },
            "ui": {
                "platforms": list(_cfg_get(web_ui_config, "ui_sources", [])),
                "session_timeout": _cfg_get(web_ui_config, "session_timeout", None),
                "max_history": _cfg_get(web_ui_config, "max_conversation_history", None),
                "theme": getattr(config, "theme", None),
                "proactive_suggestions": bool(
                    _cfg_get(web_ui_config, "enable_proactive_suggestions", False)
                ),
            },
            "limits": {
                "max_message_length": ChatConfig.MAX_MESSAGE_LENGTH,
                "max_tokens": _cfg_get(
                    config.llm, "max_tokens", ChatConfig.MAX_TOKENS_DEFAULT
                ),
                "temperature": _cfg_get(config.llm, "temperature", None),
            },
            "observability": {
                "metrics_enabled": bool(
                    _cfg_get(monitoring_config, "enable_metrics", False)
                ),
                "prometheus_port": _cfg_get(monitoring_config, "metrics_port", None),
                "prometheus_enabled": bool(
                    _cfg_get(monitoring_config, "prometheus_enabled", False)
                ),
                "tracing_enabled": bool(
                    _cfg_get(monitoring_config, "enable_tracing", False)
                ),
                "log_level": _cfg_get(monitoring_config, "log_level", None),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Chat runtime configuration retrieved",
            extra={"user_id": user_id, "profile": active_profile_id},
        )
        return response_payload

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Failed to get chat configuration",
            extra={"user_id": user_id, "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get configuration",
        ) from exc


# =========================================================
# /chat/runtime/health
# =========================================================

@router.get("/chat/runtime/health")
async def chat_runtime_health() -> Dict[str, Any]:
    try:
        service_registry = get_service_registry()
        services_status: Dict[str, Any] = {}
        for name in service_registry.list_services().keys():
            info = service_registry.get_service_info(name)
            if info:
                services_status[name] = {
                    "status": info.status.value,
                    "initialized": info.initialized,
                    "error": info.error_message,
                }

        cfg = get_config()
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "chat-runtime",
            "version": "2.0.0",
            "environment": cfg.environment.value,
            "services": services_status,
            "config": {
                "max_message_length": ChatConfig.MAX_MESSAGE_LENGTH,
                "stream_timeout": ChatConfig.STREAM_TIMEOUT,
                "fallback_enabled": ChatConfig.FALLBACK_ENABLED,
            },
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "chat-runtime",
            "version": "2.0.0",
            "error": str(exc),
        }


# =========================================================
# /chat/runtime/response-core  (backward-compatible)
# =========================================================

@router.post("/chat/runtime/response-core", response_model=ChatRuntimeResponse)
async def chat_runtime_response_core(
    request: SanitizedChatRuntimeRequest = Depends(validate_chat_request),
    user_context: Dict[str, Any] = Depends(get_current_user_context),
    request_metadata: Dict[str, Any] = Depends(get_request_metadata),
) -> ChatRuntimeResponse:
    start_time = time.time()
    correlation_id = request_metadata.get("correlation_id")
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_id = user_context.get("user_id", "anonymous")
    platform = request.platform or "web"

    try:
        log_chat_event(
            "response_core_request_received",
            user_id,
            correlation_id,
            platform=platform,
            message_length=len(request.message),
        )

        response_orchestrator = get_global_orchestrator(user_id=user_id)
        ui_caps = {
            "platform": platform,
            "conversation_id": conversation_id,
            "tools": request.tools or [],
            "memory_context": request.memory_context,
            "user_preferences": request.user_preferences or {},
        }

        result = response_orchestrator.respond(request.message, ui_caps=ui_caps)

        if isinstance(result, dict):
            content = result.get("content", "")
            orchestrator_metadata: Dict[str, Any] = {
                "intent": result.get("intent"),
                "persona": result.get("persona"),
                "mood": result.get("mood"),
            }
            orchestrator_metadata.update(result.get("metadata", {}) or {})
            if "onboarding" in result:
                orchestrator_metadata["onboarding"] = result["onboarding"]
        else:
            content = str(result)
            orchestrator_metadata = {}

        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, True, platform, False)

        response = ChatRuntimeResponse(
            content=content,
            conversation_id=conversation_id,
            metadata={
                **orchestrator_metadata,
                "platform": platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "processing_time": latency_ms / 1000.0,
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
            latency_ms=latency_ms,
        )

        return response

    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.time() - start_time) * 1000.0
        ChatMetrics.record_request(latency_ms, False, platform, True)
        log_chat_event(
            "response_core_error",
            user_id,
            correlation_id,
            level="error",
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        return ChatRuntimeResponse(
            content=(
                "Response-core encountered an internal error and returned a safe fallback message."
            ),
            conversation_id=conversation_id,
            metadata={
                "platform": platform,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "processing_time": latency_ms / 1000.0,
                "latency_ms": latency_ms,
                "error": str(exc),
                "orchestrator": "response_core",
                "used_fallback": True,
            },
        )
