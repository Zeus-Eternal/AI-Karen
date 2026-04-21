import json
import asyncio
import os
import inspect
import logging
import time
import uuid
import re
from typing import Any, Dict, List, Optional
from typing import TYPE_CHECKING
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.responses import JSONResponse, StreamingResponse

from ai_karen_engine.core.chat_runtime_control_plane import (
    get_chat_runtime_control_plane,
    DegradedResponse,
    DegradedCapabilities,
    EmergencyFallbackResponse,
    serialize_runtime_response,
    runtime_response_http_status,
    RuntimeConstants,
)
from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response
from ai_karen_engine.core.dependencies import bypass_user_context_func
from ai_karen_engine.models.shared_types import (
    CanonicalChatRequest,
    CanonicalChatResponse,
)
from ai_karen_engine.utils.chat_helpers import (
    normalize_session_id as _normalize_session_id,
    resolve_user_context as _resolve_user_context,
    json_safe as _json_safe,
)

from pydantic import BaseModel, ConfigDict, Field


def _is_placeholder_response(response_text: str) -> bool:
    """Detect if orchestrator response contains static placeholder text that should trigger fallback."""
    text = str(response_text or "").strip()
    if not text:
        return True

    lowered = text.lower()

    # Punctuation-only payloads are placeholders/noise.
    if all(ch in set(".-_=`'\"!?,:;()[]{}|/\\ \n\t") for ch in lowered):
        return True

    # IMPORTANT: do not treat all short responses as placeholders.
    # Legitimate replies like "Hi!" or "Yes." must pass through.
    known_prefixes = (
        RuntimeConstants.DEGRADED_BRAIN_ERROR.lower(),
        RuntimeConstants.EMERGENCY_UNAVAILABLE.lower(),
        "service is temporarily operating with limited capabilities",
        "i understand you're asking about:",
        "i'm currently operating with limited capabilities",
        "limited assistant with:",
        "error: generation failed",
    )
    if any(lowered.startswith(prefix) for prefix in known_prefixes):
        return True

    # Detect known synthetic long-form scaffolds that should not be returned as final user content.
    if (
        "the requested topic" in lowered
        and lowered.count("a reliable approach to") >= 3
    ):
        return True

    return False


_INTERNAL_ANALYSIS_PREFIX_MARKERS = (
    "to complete the session continuity summary",
    "session continuity summary:",
    "since the user has greeted again without a specific new request",
    "this is not a complete meaningful response",
)

_INTERNAL_ANALYSIS_LINE_PATTERNS = (
    r"^\s*to complete the session continuity summary.*$",
    r"^\s*session continuity summary:\s*.*$",
    r"^\s*in summary:\s*$",
    r"^\s*let'?s see if we can make sure the chat response is complete.*$",
    r"^\s*i(?:'|\u2019)ll acknowledge their greeting and be ready to assist.*$",
)


def _strip_internal_analysis_leakage(response_text: str) -> str:
    """Remove known internal-analysis scaffold text from model-visible output."""
    original = str(response_text or "").replace("\r\n", "\n")
    cleaned = original
    lowered = cleaned.lower()

    for marker in _INTERNAL_ANALYSIS_PREFIX_MARKERS:
        index = lowered.find(marker)
        # Only trim from marker onward when scaffold appears near the beginning.
        # This avoids cutting valid content that happens to contain similar phrases later.
        if 0 <= index <= 240:
            cleaned = cleaned[:index]
            lowered = cleaned.lower()

    for pattern in _INTERNAL_ANALYSIS_LINE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    cleaned = re.sub(r"^\s*=+\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()
    if cleaned:
        return cleaned
    return original.strip()


def _sanitize_user_visible_text(response_text: str) -> str:
    """Avoid returning low-information punctuation-only payloads to clients."""
    text = _strip_internal_analysis_leakage(str(response_text or "")).strip()
    if not text:
        return ""
    if len(text) == 1 and not text.isalnum():
        return ""
    if all(ch in set(".-_=`'\"!?,:;()[]{}|/\\ \n\t") for ch in text):
        return ""
    return text


def _is_plain_heading_line(line: str) -> bool:
    """Heuristic for plain (non-markdown) section headings."""
    stripped = (line or "").strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "-", "*", ">", "`")):
        return False
    if len(stripped) > 80:
        return False
    if stripped.endswith((".", "!", "?", ":", ";", ",")):
        return False
    if re.search(r"\d{2,}", stripped):
        return False
    words = [w for w in stripped.split() if w]
    known_single_word_headings = {
        "introduction",
        "conclusion",
        "summary",
        "overview",
        "appendix",
    }
    if len(words) == 1 and stripped.lower() not in known_single_word_headings:
        return False
    if len(words) > 8:
        return False
    alpha_words = [w for w in words if re.search(r"[A-Za-z]", w)]
    if not alpha_words:
        return False
    title_like = sum(1 for w in alpha_words if w[:1].isupper())
    return title_like >= max(1, int(len(alpha_words) * 0.6))


def _canonical_heading(line: str) -> str:
    stripped = (line or "").strip()
    if stripped.startswith("#"):
        stripped = re.sub(r"^#+\s*", "", stripped)
    return re.sub(r"\s+", " ", stripped).strip().lower()


def _collapse_repeated_sentences(text: str) -> str:
    """Collapse obvious consecutive repeated sentences in long-form text."""
    raw = str(text or "").strip()
    if not raw:
        return raw

    # Keep newline structure roughly stable by processing paragraph blocks.
    blocks = [blk for blk in re.split(r"\n{2,}", raw) if blk.strip()]
    collapsed_blocks: List[str] = []

    for block in blocks:
        sentence_parts = re.split(r"(?<=[.!?])\s+", block.strip())
        normalized_prev = ""
        kept: List[str] = []
        repeat_run = 0

        for sentence in sentence_parts:
            stripped = sentence.strip()
            if not stripped:
                continue
            normalized = re.sub(r"\s+", " ", stripped).lower()
            if normalized == normalized_prev:
                repeat_run += 1
                # Keep at most one copy of consecutive duplicates.
                if repeat_run >= 1:
                    continue
            else:
                repeat_run = 0
                normalized_prev = normalized
            kept.append(stripped)

        collapsed_blocks.append(" ".join(kept).strip())

    return "\n\n".join(blk for blk in collapsed_blocks if blk).strip()


def _dedupe_and_markdown_sections(text: str) -> str:
    """Remove repeated section blocks and normalize plain headings into markdown."""
    lines = str(text or "").replace("\r\n", "\n").split("\n")
    if not lines:
        return str(text or "")

    has_markdown_heading = any(re.match(r"^\s*#{1,6}\s+\S", ln) for ln in lines)

    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"heading": None, "is_heading": False, "body": []}

    def push_current() -> None:
        if current["heading"] is None and not current["body"]:
            return
        sections.append(
            {
                "heading": current["heading"],
                "is_heading": current["is_heading"],
                "body": list(current["body"]),
            }
        )

    for line in lines:
        is_md_heading = bool(re.match(r"^\s*#{1,6}\s+\S", line))
        is_plain_heading = _is_plain_heading_line(line)
        if is_md_heading or is_plain_heading:
            push_current()
            current = {
                "heading": line.strip(),
                "is_heading": True,
                "body": [],
            }
            continue
        current["body"].append(line)
    push_current()

    # Dedupe repeated sections with same heading + equivalent body
    seen_sections: set[tuple[str, str]] = set()
    deduped: List[Dict[str, Any]] = []
    for idx, sec in enumerate(sections):
        heading = sec.get("heading")
        body_lines = sec.get("body", [])
        body_text = _collapse_repeated_sentences("\n".join(body_lines).strip())
        if heading:
            key = (_canonical_heading(heading), re.sub(r"\s+", " ", body_text).strip())
            if key in seen_sections:
                continue
            seen_sections.add(key)
        deduped.append(sec)

    # Render with markdown headings if plain headings were used
    output: List[str] = []
    heading_index = 0
    for sec in deduped:
        heading = sec.get("heading")
        body_lines = sec.get("body", [])
        if heading:
            cleaned_heading = re.sub(r"^#+\s*", "", heading).strip()
            if has_markdown_heading:
                output.append(
                    f"## {cleaned_heading}"
                    if not heading.lstrip().startswith("#")
                    else heading
                )
            else:
                output.append(
                    f"# {cleaned_heading}"
                    if heading_index == 0
                    else f"## {cleaned_heading}"
                )
            heading_index += 1
        if body_lines:
            body_text = _collapse_repeated_sentences("\n".join(body_lines).strip())
            if body_text:
                output.append(body_text)

    rendered = "\n\n".join(chunk.strip() for chunk in output if str(chunk).strip())
    rendered = re.sub(r"\n{3,}", "\n\n", rendered).strip()
    return rendered or str(text or "").strip()


def _should_enforce_article_format(user_message: str, response_text: str) -> bool:
    user_lower = str(user_message or "").lower()
    response = str(response_text or "")
    article_triggers = (
        "full article",
        "write an article",
        "article on",
        "long-form",
        "blog post",
    )
    if any(trigger in user_lower for trigger in article_triggers):
        return True

    # If response already appears section-heavy, apply cleanup.
    plain_heading_count = sum(
        1 for ln in response.splitlines() if _is_plain_heading_line(ln)
    )
    markdown_heading_count = len(re.findall(r"(?m)^\s*#{1,6}\s+\S", response))
    return (plain_heading_count + markdown_heading_count) >= 4 and len(response) >= 500


def _finalize_user_visible_text(response_text: str, user_message: str) -> str:
    """Final pass for user-visible text quality and article structure cleanup."""
    sanitized = _sanitize_user_visible_text(response_text)
    if not sanitized:
        return ""
    if _should_enforce_article_format(user_message, sanitized):
        return _dedupe_and_markdown_sections(sanitized)
    return sanitized


def _finalize_runtime_payload_text(
    payload: Dict[str, Any], user_message: str
) -> Dict[str, Any]:
    """Apply final user-visible cleanup to runtime payload text fields."""
    updated = dict(payload or {})
    candidate_keys = ("answer", "message", "response", "final", "content")
    for key in candidate_keys:
        value = updated.get(key)
        if isinstance(value, str) and value.strip():
            updated[key] = _finalize_user_visible_text(value, user_message)
    return updated


def _extract_stream_text(payload: Dict[str, Any]) -> str:
    """Extract user-visible response text from a runtime payload."""
    for key in ("answer", "message", "response", "final", "content"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _normalize_processing_status(status: Any, default: str = "processing") -> str:
    """Normalize processing status values to stable snake_case keys."""
    if status is None:
        return default

    raw_status = getattr(status, "value", status)
    status_text = str(raw_status or "").strip().lower()
    if not status_text:
        return default

    return status_text.replace("-", "_").replace(" ", "_")


def _build_degraded_sse_events(
    payload: Dict[str, Any], correlation_id: str
) -> List[Dict[str, Any]]:
    """Build client-compatible SSE events for degraded/fallback payloads."""
    text = _extract_stream_text(payload)
    status = _normalize_processing_status(
        payload.get("mode") or payload.get("status"),
        "degraded",
    )
    status_message = _PROCESSING_STATUS_MESSAGES.get(
        status, f"Karen is {status.replace('_', ' ')}..."
    )
    metadata = {
        **payload,
        "status": status,
        "status_message": status_message,
        "degraded_mode": True,
    }
    events: List[Dict[str, Any]] = [
        {
            "type": "status",
            "content": status_message,
            "correlation_id": correlation_id,
            "metadata": {
                "status": status,
                "status_message": status_message,
                "degraded_mode": True,
            },
        }
    ]
    if text:
        events.append(
            {
                "type": "content",
                "content": text,
                "correlation_id": correlation_id,
                "metadata": metadata,
            }
        )
    events.append(
        {
            "type": "complete",
            "content": "",
            "correlation_id": correlation_id,
            "metadata": metadata,
        }
    )
    return events


logger = logging.getLogger(__name__)

# Create router without prefix for automatic discovery alignment
router = APIRouter(tags=["copilot"])


class SuggestedAction(BaseModel):
    type: str = Field(
        ..., examples=["add_task", "pin_memory", "open_doc", "export_note"]
    )
    params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    description: Optional[str] = None


class AssistRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)
    top_k: int = Field(6, ge=1, le=50)
    context: Dict[str, Any] = Field(default_factory=dict)
    preferred_llm_provider: Optional[str] = None
    preferred_model: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False


class AssistResponse(BaseModel):
    answer: str
    structured_content: Dict[str, Any] = Field(default_factory=dict)
    actions: List[SuggestedAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str


class StartActionRequest(BaseModel):
    action: str = Field(
        ..., description="Registered action/predictor name, e.g. routing.select"
    )
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class StartActionResponse(BaseModel):
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "")


def _assist_response_json(
    *,
    answer: str,
    structured_content: Optional[Dict[str, Any]] = None,
    actions: Optional[List[SuggestedAction]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    correlation_id: str,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "answer": answer,
            "structured_content": structured_content or {},
            "actions": [action.model_dump() for action in (actions or [])],
            "metadata": metadata or {},
            "correlation_id": correlation_id,
        },
    )


def _build_degraded_assist_response(
    *,
    degraded: DegradedResponse,
    user_message: str,
    correlation_id: str,
    status_code: int = 200,
    is_fallback: bool = False,
    fallback_provider: Optional[str] = None,
    fallback_model: Optional[str] = None,
) -> JSONResponse:
    """Return a useful degraded assistant payload (not just a mode banner)."""
    payload = serialize_runtime_response(degraded) or {}
    shim = generate_degraded_mode_response(user_message)
    shim_answer = str(
        (
            shim.get("final")
            or shim.get("message")
            or shim.get("response")
            or shim.get("answer")
            or ""
        )
    ).strip()
    answer = shim_answer or degraded.message

    # Use distinct metadata based on whether this is a fallback or static degraded response
    if is_fallback and fallback_provider and fallback_model:
        # This is a degraded LLM success (actual AI content from fallback)
        metadata = {
            "runtime": payload,
            "mode": payload.get("mode", "degraded"),
            "degraded_mode": True,
            "capabilities": vars(degraded.capabilities)
            if degraded.capabilities
            else {},
            "is_minimal": getattr(degraded, "is_minimal", True),
            "retry_after_seconds": getattr(degraded, "retry_after_seconds", 30),
            "system_status_code": getattr(degraded, "system_status_code", 503),
            "support_hint": getattr(degraded, "support_hint", ""),
            "llm": {
                "provider": fallback_provider,
                "model_name": fallback_model,
                "source": "degraded_fallback_llm",
                "is_degraded": True,
                "fallback_level": "nlp_service",
                "failure_reason": degraded.message,
            },
        }
    else:
        # This is a static fallback response
        metadata = {
            "runtime": payload,
            "mode": payload.get("mode", "degraded"),
            "degraded_mode": True,
            "capabilities": vars(degraded.capabilities)
            if degraded.capabilities
            else {},
            "is_minimal": getattr(degraded, "is_minimal", True),
            "retry_after_seconds": getattr(degraded, "retry_after_seconds", 30),
            "system_status_code": getattr(degraded, "system_status_code", 503),
            "support_hint": getattr(degraded, "support_hint", ""),
            "llm": {
                "provider": "system",
                "model_name": "Degraded Mode",
                "source": "runtime_control_plane",
                "is_degraded": True,
                "fallback_level": "degraded",
                "failure_reason": degraded.message,
            },
        }

    return _assist_response_json(
        answer=answer,
        structured_content={},
        actions=[],
        metadata=metadata,
        correlation_id=correlation_id,
        status_code=status_code,
    )


from ai_karen_engine.models.shared_types import (
    CanonicalChatRequest,
    CanonicalChatResponse,
)
from ai_karen_engine.utils.chat_helpers import (
    normalize_session_id,
    resolve_user_context,
    json_safe,
    is_production_env,
)


async def _get_chat_orchestrator():
    """Return the LangGraphOrchestrator for processing chat requests."""
    try:
        from ai_karen_engine.core.langgraph_orchestrator import get_default_orchestrator

        orchestrator = await get_default_orchestrator()
        logger.info(
            "Successfully retrieved ChatOrchestrator", extra={"correlation_id": "debug"}
        )
        return orchestrator
    except Exception as exc:
        logger.error(
            "Failed to get chat orchestrator: %s",
            exc,
            extra={"correlation_id": "debug"},
        )
        raise HTTPException(status_code=503, detail="Chat service unavailable")


def _get_predictor_registry():
    """Return the predictor registry with graceful fallback."""

    try:
        from ai_karen_engine.core.predictors import predictor_registry as registry

        return registry
    except Exception:
        return {}


def _get_audit_logger():
    """Lazily import the audit logger to avoid heavy startup costs."""

    try:
        from ai_karen_engine.services.audit_logger import get_audit_logger as _getter

        return _getter()
    except Exception:
        return None


class _AuditLoggerProtocol:
    async def log_event(self, *args: Any, **kwargs: Any) -> Any: ...


async def _log_audit_event(**kwargs: Any) -> None:
    """Best-effort audit logging with compatibility for partial shims."""
    try:
        audit_logger = _get_audit_logger()
        if audit_logger is not None and hasattr(audit_logger, "log_audit_event"):
            audit_logger.log_audit_event(**kwargs)
    except Exception:
        pass


def _ensure_routing_actions_registered() -> None:
    """Ensure routing actions are registered for the /start endpoint."""
    try:
        from ai_karen_engine.integrations.copilotkit.routing_actions import (
            ensure_kire_actions_registered,
        )

        ensure_kire_actions_registered()
    except Exception:
        # Best-effort; if not present, action registry may be empty until lazily imported elsewhere
        pass


@router.get("/health")
async def copilot_health():
    """Lightweight health check for copilot routes to verify wiring.

    Returns minimal info without invoking heavy dependencies.
    """
    try:
        registry = _get_predictor_registry()
        if hasattr(registry, "keys"):
            registered = list(registry.keys())
        else:
            registered = []
    except Exception:
        registered = []

    return {
        "status": "ok",
        "registered_actions": registered,
        "timestamp": int(time.time()),
    }


@router.post("/start", response_model=StartActionResponse)
async def copilot_start_action(
    http_request: Request,
    # In dev/bypass we allow anonymous; compute context inside to avoid hard 401
    user_ctx: Optional[Dict[str, Any]] = None,
):
    """Generic CopilotKit action starter. Routes to predictor-registered actions."""
    _ensure_routing_actions_registered()
    correlation_id = (
        http_request.headers.get("X-Correlation-Id") or f"copilot_{int(time.time())}"
    )

    # Parse request body manually
    try:
        body = await http_request.json()
        req = StartActionRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Resolve user context: prefer provided; otherwise permissive in dev/bypass
    if user_ctx is None:
        auth_mode = os.getenv("AUTH_MODE", "hybrid").lower()
        allow_public = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        if not _is_production_env() and (allow_public or auth_mode == "bypass"):
            user_ctx = {
                "user_id": "anonymous",
                "roles": ["admin"],
                "scopes": ["chat:write"],
            }
        else:
            try:
                # Try to resolve real context if available
                user_ctx = await _resolve_user_context(http_request)
            except Exception:
                # If strict mode, deny
                raise HTTPException(status_code=401, detail="Unauthorized")
            if user_ctx is None:
                raise HTTPException(status_code=401, detail="Unauthorized")

    # RBAC: basic scope check; allow admin or chat:write by default
    try:
        allow_public = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        if not allow_public:
            # Simple role checking - admin or user role required
            user_roles = user_ctx.get("roles", [])
            if not any(role in user_roles for role in ["admin", "user"]):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions - user or admin role required",
                )
    except Exception:
        # If RBAC service not configured, proceed in permissive mode
        pass

    # Audit: action started
    await _log_audit_event(
        event_type="copilot.action.started",
        user_id=user_ctx.get("user_id"),
        session_id=user_ctx.get("session_id"),
        correlation_id=correlation_id,
        details={"action": req.action, "payload_keys": list(req.payload.keys())},
        surface="copilot",
    )

    # Dispatch to predictor registry
    registry = _get_predictor_registry()
    handler_getter = getattr(registry, "get", lambda *_: None)
    handler = handler_getter(req.action)
    if handler is None:
        # Try late registration of routing actions, then re-check
        try:
            from ai_karen_engine.integrations.copilotkit.routing_actions import (
                ensure_kire_actions_registered,
            )

            ensure_kire_actions_registered()
            # Also import actions directly for side-effects if available
            try:
                import ai_karen_engine.routing.actions  # noqa: F401
            except Exception:
                pass
        except Exception:
            pass
        registry = _get_predictor_registry()
        handler_getter = getattr(registry, "get", lambda *_: None)
        handler = handler_getter(req.action)
        if handler is None:
            available = []
            try:
                registry = _get_predictor_registry()
                available = list(registry.keys()) if hasattr(registry, "keys") else []
            except Exception:
                available = []
            raise HTTPException(
                status_code=404,
                detail=f"Unknown action: {req.action}. Available: {available}",
            )

    try:
        import inspect

        # Normalize user context and pass payload/context
        args = (user_ctx, req.payload, req.context)
        if inspect.iscoroutinefunction(handler):
            output = await handler(*args)
        else:
            output = handler(*args)

        # Audit: action completed
        await _log_audit_event(
            event_type="copilot.action.completed",
            user_id=user_ctx.get("user_id"),
            session_id=user_ctx.get("session_id"),
            correlation_id=correlation_id,
            details={"action": req.action, "success": True},
            surface="copilot",
        )

        return StartActionResponse(
            status="ok", output=output or {}, correlation_id=correlation_id
        )
    except Exception as e:
        # Audit: action failed
        await _log_audit_event(
            event_type="copilot.action.failed",
            user_id=user_ctx.get("user_id"),
            session_id=user_ctx.get("session_id"),
            correlation_id=correlation_id,
            details={"action": req.action, "error": str(e)},
            surface="copilot",
            success=False,
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Action failed: {e}")


# Convenience GET endpoint for clients that mistakenly use GET
@router.get("/start", response_model=StartActionResponse)
async def copilot_start_action_get(action: str, http_request: Request):
    """Shallow wrapper that maps GET to the same start action handler.

    Accepts `action` as a query param and calls the POST handler with empty payload/context.
    Keeps legacy or misconfigured clients working without 404s.
    """
    _ensure_routing_actions_registered()
    return await copilot_start_action(http_request=http_request)


@router.post("/assist")
async def copilot_assist(
    request: AssistRequest,
    http_request: Request,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """Copilot assist endpoint using runtime control plane."""
    start_time = time.time()
    correlation_id = get_correlation_id(http_request) or f"copilot_{int(time.time())}"

    logger.info(
        "Copilot assist request received",
        extra={
            "correlation_id": correlation_id,
            "user_id": request.user_id,
            "message_length": len(request.message),
        },
    )

    degraded_continuation_response: Optional[DegradedResponse] = None

    try:
        # Get runtime control plane
        runtime_plane = await get_chat_runtime_control_plane()

        # Get runtime response based on current mode
        response = await runtime_plane.get_runtime_response(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            correlation_id=correlation_id,
        )

        if response is not None:
            if isinstance(response, DegradedResponse):
                logger.info(
                    "Copilot in degraded mode — will attempt orchestrator before returning degraded fallback",
                    extra={"correlation_id": correlation_id},
                )
                degraded_continuation_response = response
            elif isinstance(response, EmergencyFallbackResponse):
                payload = serialize_runtime_response(response) or {}
                payload["correlation_id"] = correlation_id
                status_code = runtime_response_http_status(response) or 503
                return JSONResponse(
                    status_code=status_code,
                    content=payload,
                    headers={"X-Correlation-Id": correlation_id},
                )
            else:
                payload = serialize_runtime_response(response) or {}
                payload = _finalize_runtime_payload_text(payload, request.message)
                payload["correlation_id"] = correlation_id
                status_code = runtime_response_http_status(response) or 503
                return JSONResponse(
                    status_code=status_code,
                    content=payload,
                    headers={"X-Correlation-Id": correlation_id},
                )

        # If no runtime response, proceed with factory-wired orchestrator
        logger.info(
            "Copilot proceeding with orchestrator",
            extra={"correlation_id": correlation_id},
        )
        try:
            orchestrator = await _get_chat_orchestrator()
        except Exception as orchestrator_error:
            if degraded_continuation_response is not None:
                logger.warning(
                    "Copilot degraded continuation falling back to degraded response: %s",
                    orchestrator_error,
                    extra={"correlation_id": correlation_id},
                )
                return _build_degraded_assist_response(
                    degraded=degraded_continuation_response,
                    user_message=request.message,
                    correlation_id=correlation_id,
                    status_code=runtime_response_http_status(
                        degraded_continuation_response
                    )
                    or 200,
                    is_fallback=False,
                )
            raise

        conversation_id = _normalize_session_id(request.session_id)
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        chat_request = ChatRequest(
            correlation_id=correlation_id,
            tenant_id=str(request.org_id or "default"),
            message=request.message,
            user_id=request.user_id,
            org_id=request.org_id,
            conversation_id=conversation_id,
            session_id=conversation_id,
            streaming=False,
            stream=False,
            include_context=True,
            attachments=[],
            metadata={
                "surface": "copilot",
                "top_k": request.top_k,
                "context": _json_safe(request.context or {}),
                "preferred_llm_provider": request.preferred_llm_provider,
                "preferred_model": request.preferred_model,
            },
        )

        try:
            orchestrator_response = await orchestrator.handle_chat(chat_request)
        except Exception as orchestrator_error:
            if degraded_continuation_response is not None:
                logger.warning(
                    "Copilot degraded continuation encountered orchestrator error: %s",
                    orchestrator_error,
                    extra={"correlation_id": correlation_id},
                )
                return _build_degraded_assist_response(
                    degraded=degraded_continuation_response,
                    user_message=request.message,
                    correlation_id=correlation_id,
                    status_code=runtime_response_http_status(
                        degraded_continuation_response
                    )
                    or 200,
                    is_fallback=False,
                )
            raise
        if isinstance(orchestrator_response, ChatResponse):
            response_text = _finalize_user_visible_text(
                str(orchestrator_response.response or "").strip(),
                request.message,
            )
            # Check if response contains placeholder text that should trigger NLP fallback
            if _is_placeholder_response(response_text):
                logger.info(
                    "Copilot detected placeholder response, attempting NLP fallback",
                    extra={"correlation_id": correlation_id},
                )

                # Try NLP service fallback
                nlp_manager = None
                nlp_result = None
                try:
                    from ai_karen_engine.memory.nlp_service_manager import (
                        NLPServiceManager,
                    )

                    nlp_manager = NLPServiceManager()

                    # Determine fallback model from control plane
                    fallback_provider, fallback_model = (
                        runtime_plane.get_fallback_provider()
                    )

                    nlp_result = None
                    if nlp_manager:
                        try:
                            nlp_result = await nlp_manager.generate_response(
                                model_id=fallback_model,
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are Karen, a helpful AI assistant. You are currently in degraded mode with limited capabilities, but you should still provide a helpful, coherent, and natural response to the user's question. Keep your response concise but informative, and maintain a friendly tone. If you cannot answer the question fully, explain what you can and cannot do. The user asked: '{user_message}'. Provide a direct and helpful response based on your knowledge.",
                                    },
                                    {"role": "user", "content": request.message},
                                ],
                                correlation_id=correlation_id,
                                max_tokens=600,
                                temperature=0.7,
                            )
                        except Exception as nlp_error:
                            logger.warning(
                                "NLP manager generate_response error: %s",
                                nlp_error,
                                extra={"correlation_id": correlation_id},
                            )

                    if (
                        nlp_result
                        and nlp_result.get("success")
                        and nlp_result.get("content")
                    ):
                        content = nlp_result.get("content", "")
                        logger.info(
                            "Degraded mode response content: %s",
                            content[:200] + "..." if len(content) > 200 else content,
                            extra={"correlation_id": correlation_id},
                        )

                    if (
                        nlp_result
                        and nlp_result.get("success")
                        and nlp_result.get("content")
                    ):
                        # NLP fallback succeeded - return actual AI content with degraded LLM metadata
                        logger.info(
                            "Copilot NLP fallback succeeded",
                            extra={"correlation_id": correlation_id},
                        )

                        return _assist_response_json(
                            answer=_finalize_user_visible_text(
                                str(nlp_result["content"] or ""),
                                request.message,
                            ),
                            structured_content={},
                            actions=[],
                            metadata={
                                "status": "success",
                                "processing_time": time.time() - start_time,
                                "conversation_id": conversation_id,
                                "used_fallback": True,
                                "llm": {
                                    "provider": fallback_provider,
                                    "model_name": fallback_model,
                                    "source": RuntimeConstants.SOURCE_DEGRADED_LLM,
                                    "is_degraded": True,
                                    "fallback_level": "nlp_service",
                                },
                            },
                            correlation_id=correlation_id,
                            status_code=200,
                        )

                    nlp_manager = NLPServiceManager()

                    # Determine fallback model from control plane
                    fallback_provider, fallback_model = (
                        runtime_plane.get_fallback_provider()
                    )

                    nlp_manager = NLPServiceManager()

                    # Determine fallback model from control plane
                    fallback_provider, fallback_model = (
                        runtime_plane.get_fallback_provider()
                    )
                    nlp_result = None
                    if nlp_manager:
                        try:
                            nlp_result = await nlp_manager.generate_response(
                                model_id=fallback_model,
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are Karen, a helpful AI assistant. You are currently in degraded mode with limited capabilities, but you should still provide a helpful, coherent, and natural response to the user's question. Keep your response concise but informative, and maintain a friendly tone. If you cannot answer the question fully, explain what you can and cannot do. The user asked: '{user_message}'. Provide a direct and helpful response based on your knowledge.",
                                    },
                                    {"role": "user", "content": request.message},
                                ],
                                correlation_id=correlation_id,
                                max_tokens=600,
                                temperature=0.7,
                            )
                        except Exception as nlp_error:
                            logger.warning(
                                "NLP manager generate_response error: %s",
                                nlp_error,
                                extra={"correlation_id": correlation_id},
                            )

                    if (
                        nlp_result
                        and nlp_result.get("success")
                        and nlp_result.get("content")
                    ):
                        content = nlp_result.get("content", "")
                        logger.info(
                            "Degraded mode response content: %s",
                            content[:200] + "..." if len(content) > 200 else content,
                            extra={"correlation_id": correlation_id},
                        )

                    if (
                        nlp_result
                        and nlp_result.get("success")
                        and nlp_result.get("content")
                    ):
                        # NLP fallback succeeded - return actual AI content with degraded LLM metadata
                        logger.info(
                            "Copilot NLP fallback succeeded",
                            extra={"correlation_id": correlation_id},
                        )

                        return _assist_response_json(
                            answer=_finalize_user_visible_text(
                                str(nlp_result["content"] or ""),
                                request.message,
                            ),
                            structured_content={},
                            actions=[],
                            metadata={
                                "status": "success",
                                "processing_time": time.time() - start_time,
                                "conversation_id": conversation_id,
                                "used_fallback": True,
                                "llm": {
                                    "provider": fallback_provider,
                                    "model_name": fallback_model,
                                    "source": RuntimeConstants.SOURCE_DEGRADED_LLM,
                                    "is_degraded": True,
                                    "fallback_level": "nlp_service",
                                },
                            },
                            correlation_id=correlation_id,
                            status_code=200,
                        )
                    else:
                        logger.warning(
                            "Copilot NLP fallback failed to generate content",
                            extra={"correlation_id": correlation_id},
                        )

                except Exception as nlp_error:
                    logger.warning(
                        "Copilot NLP fallback error: %s",
                        nlp_error,
                        extra={"correlation_id": correlation_id},
                    )
                    # Try with a simpler system prompt if the complex one failed
                    if nlp_manager:
                        try:
                            logger.info(
                                "Attempting NLP fallback with simpler prompt",
                                extra={"correlation_id": correlation_id},
                            )
                            simple_nlp_result = await nlp_manager.generate_response(
                                model_id="phi-3-mini",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a helpful assistant. Answer the user's question simply and directly.",
                                    },
                                    {"role": "user", "content": request.message},
                                ],
                                correlation_id=correlation_id,
                                max_tokens=300,
                                temperature=0.7,
                            )

                            if simple_nlp_result.get(
                                "success"
                            ) and simple_nlp_result.get("content"):
                                logger.info(
                                    "Simple NLP fallback succeeded",
                                    extra={"correlation_id": correlation_id},
                                )
                                nlp_result = simple_nlp_result
                        except Exception as simple_error:
                            logger.warning(
                                "Simple NLP fallback also failed: %s",
                                simple_error,
                                extra={"correlation_id": correlation_id},
                            )

            # Check if we should return a final degraded response (hard failure)
            if _is_placeholder_response(response_text):
                logger.info(
                    "Copilot returned placeholder text and fallback failed - returning degraded shim",
                    extra={"correlation_id": correlation_id},
                )

                # Use existing degraded response or create a default one
                if degraded_continuation_response is None:
                    degraded_continuation_response = DegradedResponse(
                        mode="degraded",
                        message="I'm currently experiencing some technical difficulties and can only provide limited responses. I'm Karen - your AI assistant. While I'm in degraded mode, I may not be able to answer complex questions fully, but I'll do my best to help with simple requests. For the best experience, please try again later when the system is fully operational.",
                        capabilities=DegradedCapabilities(
                            memory_available=False,
                            tools_available=True,
                            plugins_available=True,
                            external_providers_available=True,
                            streaming_supported=False,
                            local_model_available=False,
                            description="Degraded mode active - system experiencing issues",
                        ),
                        is_minimal=True,
                        retry_after_seconds=30,
                        system_status_code=503,
                        support_hint="Please try again in a few moments",
                    )

                return _build_degraded_assist_response(
                    degraded=degraded_continuation_response,
                    user_message=request.message,
                    correlation_id=correlation_id,
                    status_code=200,
                    is_fallback=False,
                )

            action_models = []
            for action in orchestrator_response.actions or []:
                if not isinstance(action, dict):
                    continue
                params_value = action.get("params")
                if isinstance(params_value, dict):
                    params = params_value
                else:
                    params = {
                        k: v
                        for k, v in action.items()
                        if k not in {"type", "confidence", "description"}
                    } or {}
                action_models.append(
                    SuggestedAction(
                        type=str(action.get("type", "unknown")),
                        params=params,
                        confidence=float(action.get("confidence", 0.8)),
                        description=action.get("description"),
                    )
                )

            metadata: Dict[str, Any] = _json_safe(orchestrator_response.metadata or {})
            metadata["status"] = str(orchestrator_response.status.value)
            metadata["processing_time"] = orchestrator_response.processing_time
            metadata["conversation_id"] = orchestrator_response.conversation_id
            metadata["used_fallback"] = orchestrator_response.used_fallback

            return _assist_response_json(
                answer=response_text,
                structured_content=_json_safe(
                    orchestrator_response.structured_content or {}
                ),
                actions=action_models,
                metadata=metadata,
                correlation_id=correlation_id,
                status_code=200,
            )

        raise RuntimeError("Unexpected ChatOrchestrator response type")

    except Exception as e:
        logger.error(
            f"Copilot assist failed: {e}",
            extra={"correlation_id": correlation_id},
        )

        fallback = EmergencyFallbackResponse()
        payload = serialize_runtime_response(fallback) or {}
        payload["correlation_id"] = correlation_id
        return JSONResponse(
            status_code=200,
            content=payload,
            headers={"X-Correlation-Id": correlation_id},
        )


_PROCESSING_STATUS_MESSAGES = {
    "initializing": "Karen is initializing the request pipeline...",
    "processing": "Karen is analyzing your message...",
    "extracting_context": "Karen is retrieving relevant context and memories...",
    "generating_response": "Karen is generating a response...",
    "streaming": "Karen is composing the response...",
    "executing_tools": "Karen is executing tools and integrations...",
    "recording_memory": "Karen is recording insights from this conversation...",
    "post_processing": "Karen is finalizing the response...",
    "completed": "Response complete.",
    "degraded": "Karen is running in degraded mode...",
    "failed": "Processing failed. Retrying or falling back...",
    "cancelled": "Request was cancelled.",
    "retrying": "Retrying with an alternative provider...",
}


@router.post("/assist/stream")
async def copilot_assist_stream(
    request: AssistRequest,
    http_request: Request,
    user: Dict[str, Any] = Depends(bypass_user_context_func),
):
    """Streaming copilot assist endpoint with real-time processing status via SSE."""
    correlation_id = (
        get_correlation_id(http_request) or f"copilot_stream_{int(time.time())}"
    )

    logger.info(
        "Copilot assist stream request received",
        extra={
            "correlation_id": correlation_id,
            "user_id": request.user_id,
            "message_length": len(request.message),
        },
    )

    degraded_continuation_response: Optional[DegradedResponse] = None
    preflight_timeout_seconds = 12.0

    try:
        runtime_plane = await asyncio.wait_for(
            get_chat_runtime_control_plane(),
            timeout=preflight_timeout_seconds,
        )

        response = await asyncio.wait_for(
            runtime_plane.get_runtime_response(
                user_id=request.user_id,
                message=request.message,
                session_id=request.session_id,
                correlation_id=correlation_id,
            ),
            timeout=preflight_timeout_seconds,
        )

        if response is not None:
            if isinstance(response, EmergencyFallbackResponse):
                payload = serialize_runtime_response(response) or {}
                payload["correlation_id"] = correlation_id

                async def stream_emergency_fallback():
                    for event in _build_degraded_sse_events(payload, correlation_id):
                        yield f"data: {json.dumps(event)}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(
                    stream_emergency_fallback(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Correlation-Id": correlation_id,
                    },
                )

            elif isinstance(response, DegradedResponse):
                degraded_continuation_response = response
                logger.info(
                    "Copilot in degraded mode — will attempt orchestrator before returning degraded fallback",
                    extra={"correlation_id": correlation_id},
                )
            else:
                logger.info(
                    "Copilot proceeding with orchestrator",
                    extra={"correlation_id": correlation_id},
                )

        if isinstance(response, DegradedResponse):
            logger.info(
                "Copilot proceeding with orchestrator with degraded continuation",
                extra={"correlation_id": correlation_id},
            )

    except Exception as runtime_exc:
        logger.error(
            "Runtime control plane error: %s",
            runtime_exc,
            extra={"correlation_id": correlation_id},
        )
        degraded_continuation_response = DegradedResponse(
            mode="degraded",
            message="I'm currently experiencing some technical difficulties and can only provide limited responses. I'm Karen - your AI assistant. While I'm in degraded mode, I may not be able to answer complex questions fully, but I'll do my best to help with simple requests. For the best experience, please try again later when the system is fully operational.",
            capabilities=DegradedCapabilities(
                memory_available=False,
                tools_available=True,
                plugins_available=True,
                external_providers_available=True,
                streaming_supported=False,
                local_model_available=False,
                description="Degraded mode active - runtime control plane unavailable",
            ),
            is_minimal=True,
            retry_after_seconds=30,
            system_status_code=503,
            support_hint="Please try again in a few moments",
        )

    try:
        orchestrator = await asyncio.wait_for(
            _get_chat_orchestrator(),
            timeout=preflight_timeout_seconds,
        )
    except Exception as exc:
        logger.error(
            "Stream setup: orchestrator unavailable: %s",
            exc,
            extra={"correlation_id": correlation_id},
        )
        payload = (
            serialize_runtime_response(
                degraded_continuation_response or EmergencyFallbackResponse()
            )
            or {}
        )
        payload["correlation_id"] = correlation_id

        async def stream_degraded_fallback():
            for event in _build_degraded_sse_events(payload, correlation_id):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_degraded_fallback(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Correlation-Id": correlation_id,
            },
        )

    conversation_id = _normalize_session_id(request.session_id)
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    chat_request = ChatRequest(
        correlation_id=correlation_id,
        tenant_id=str(request.org_id or "default"),
        message=request.message,
        user_id=request.user_id,
        org_id=request.org_id,
        conversation_id=conversation_id,
        session_id=conversation_id,
        streaming=True,
        stream=True,
        include_context=True,
        attachments=[],
        metadata={
            "surface": "copilot",
            "top_k": request.top_k,
            "context": _json_safe(request.context or {}),
            "preferred_llm_provider": request.preferred_llm_provider,
            "preferred_model": request.preferred_model,
        },
    )

    async def generate_stream():
        try:
            # Emit an immediate status event so clients know the stream is alive
            # while orchestrator startup/provider warmup is in progress.
            initial_payload = {
                "type": "status",
                "content": _PROCESSING_STATUS_MESSAGES.get(
                    "initializing",
                    "Karen is initializing the request pipeline...",
                ),
                "correlation_id": correlation_id,
                "metadata": {
                    "status": "initializing",
                    "status_message": _PROCESSING_STATUS_MESSAGES.get(
                        "initializing",
                        "Karen is initializing the request pipeline...",
                    ),
                },
            }
            yield f"data: {json.dumps(initial_payload)}\n\n"

            chunk_stream = await orchestrator.handle_chat_stream(chat_request)

            collected_content = ""
            async for chunk in chunk_stream:
                if chunk.type == "metadata":
                    status = _normalize_processing_status(
                        (chunk.metadata or {}).get("status"),
                        "processing",
                    )
                    status_message = _PROCESSING_STATUS_MESSAGES.get(
                        status,
                        f"Karen is {status.replace('_', ' ')}...",
                    )

                    payload = {
                        "type": "status",
                        "content": status_message,
                        "correlation_id": chunk.correlation_id,
                        "metadata": {
                            **(chunk.metadata or {}),
                            "status": status,
                            "status_message": status_message,
                        },
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                elif chunk.type == "content":
                    collected_content += chunk.content or ""
                    payload = {
                        "type": "content",
                        "content": chunk.content or "",
                        "correlation_id": chunk.correlation_id,
                        "metadata": chunk.metadata or {},
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                elif chunk.type == "error":
                    if degraded_continuation_response:
                        fallback_payload = (
                            serialize_runtime_response(degraded_continuation_response)
                            or {}
                        )
                        fallback_payload["correlation_id"] = correlation_id
                        for event in _build_degraded_sse_events(
                            fallback_payload, correlation_id
                        ):
                            yield f"data: {json.dumps(event)}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    payload = {
                        "type": "error",
                        "content": chunk.content or "Processing failed",
                        "correlation_id": chunk.correlation_id,
                        "metadata": chunk.metadata or {},
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                elif chunk.type == "complete":
                    completion_metadata = chunk.metadata or {}

                    # Detect system fallback responses and mark as degraded
                    llm_info = completion_metadata.get("llm", {})
                    if (
                        llm_info.get("provider") == "system"
                        or llm_info.get("model_id") == "auto"
                    ):
                        completion_metadata["degraded_mode"] = True
                        if "llm" not in completion_metadata:
                            completion_metadata["llm"] = {}
                        completion_metadata["llm"]["is_degraded"] = True
                        completion_metadata["llm"]["fallback_level"] = "system"
                        completion_metadata["llm"]["failure_reason"] = (
                            "Using system fallback response"
                        )

                    if _is_placeholder_response(collected_content):
                        shim = generate_degraded_mode_response(request.message)
                        response_text = _finalize_user_visible_text(
                            str(
                                (
                                    shim.get("final")
                                    or shim.get("message")
                                    or shim.get("response")
                                    or shim.get("answer")
                                    or ""
                                )
                            ).strip(),
                            request.message,
                        )
                        if not response_text:
                            response_text = (
                                "I’m having trouble generating a full response right now. "
                                "Please try again in a moment."
                            )
                        degraded_metadata = {
                            "status": "degraded",
                            "mode": "degraded",
                            "used_fallback": True,
                            "degraded_mode": True,
                            "runtime": {
                                "mode": "degraded",
                            },
                            "llm": {
                                "provider": "system",
                                "model_name": "Degraded Mode",
                                "source": "runtime_control_plane",
                                "is_degraded": True,
                                "fallback_level": "system",
                                "failure_reason": "Using system fallback response",
                            },
                        }
                        status_payload = {
                            "type": "status",
                            "content": _PROCESSING_STATUS_MESSAGES.get(
                                "degraded",
                                "Karen is running in degraded mode...",
                            ),
                            "correlation_id": correlation_id,
                            "metadata": degraded_metadata,
                        }
                        yield f"data: {json.dumps(status_payload)}\n\n"

                        payload = {
                            "type": "complete",
                            "content": response_text,
                            "correlation_id": correlation_id,
                            "metadata": degraded_metadata,
                        }
                        yield f"data: {json.dumps(payload)}\n\n"
                        yield "data: [DONE]\n\n"
                        return

                    final_status = _normalize_processing_status(
                        completion_metadata.get("status", "completed"),
                        "completed",
                    )
                    final_message = _PROCESSING_STATUS_MESSAGES.get(
                        final_status, f"Karen is {final_status.replace('_', ' ')}..."
                    )
                    final_content = _finalize_user_visible_text(
                        str(
                            chunk.content
                            or completion_metadata.get("formatted_content")
                            or collected_content
                            or ""
                        ),
                        request.message,
                    )
                    if not final_content and _is_placeholder_response(
                        collected_content
                    ):
                        final_content = (
                            "I’m having trouble generating a full response right now. "
                            "Please try again in a moment."
                        )

                    payload = {
                        "type": "complete",
                        "content": final_content,
                        "correlation_id": chunk.correlation_id,
                        "metadata": {
                            **completion_metadata,
                            "status": final_status,
                            "status_message": final_message,
                        },
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                else:
                    payload = {
                        "type": chunk.type,
                        "content": chunk.content or "",
                        "correlation_id": chunk.correlation_id,
                        "metadata": chunk.metadata or {},
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as stream_error:
            logger.error(
                "Streaming error in copilot assist: %s",
                stream_error,
                extra={"correlation_id": correlation_id},
            )

            if degraded_continuation_response:
                fallback_payload = (
                    serialize_runtime_response(degraded_continuation_response) or {}
                )
                fallback_payload["correlation_id"] = correlation_id
                for event in _build_degraded_sse_events(
                    fallback_payload, correlation_id
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                yield "data: [DONE]\n\n"
                return

            error_payload = {
                "type": "error",
                "content": "Streaming error: " + str(stream_error),
                "correlation_id": correlation_id,
                "metadata": {"error_type": "stream_error"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            yield "data: [DONE]\n\n"
            return

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Correlation-Id": correlation_id,
        },
    )


__all__ = ["router"]
