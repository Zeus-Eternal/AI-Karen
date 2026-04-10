import os
import inspect
import logging
import time
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, AsyncIterator, cast
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse


from ai_karen_engine.chat.ChatOrchestrator import (
    ProcessingStatus,
    ChatRequest,
    ChatResponse,
)
from ai_karen_engine.core.chat_runtime_control_plane import (
    get_chat_runtime_control_plane,
    DegradedResponse,
    EmergencyFallbackResponse,
    serialize_runtime_response,
    runtime_response_http_status,
)
from ai_karen_engine.core.degraded_mode import generate_degraded_mode_response

if TYPE_CHECKING:
    from pydantic import BaseModel, ConfigDict, Field
else:
    from ai_karen_engine.pydantic_stub import (
        BaseModel as BaseModel,
        ConfigDict as ConfigDict,
        Field as Field,
    )

    try:
        from pydantic import (
            BaseModel as BaseModel,
            ConfigDict as ConfigDict,
            Field as Field,
        )
    except ImportError:
        pass

logger = logging.getLogger(__name__)

# Create router without prefix for automatic discovery alignment
router = APIRouter(tags=["copilot"])

print("DEBUG: Copilot router created")


class SuggestedAction(BaseModel):
    type: str = Field(
        ..., examples=["add_task", "pin_memory", "open_doc", "export_note"]
    )
    params: Dict[str, Any] = Field(default_factory=dict)
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

    metadata = {
        "runtime": payload,
        "mode": payload.get("mode", "degraded"),
        "degraded_mode": True,
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


from ai_karen_engine.chat.ChatOrchestrator import (
    ChatRequest,
    ChatResponse,
    normalize_session_id as _normalize_session_id,
    resolve_user_context as _resolve_user_context,
    json_safe as _json_safe,
    is_production_env as _is_production_env,
)


async def _get_chat_orchestrator():
    """Return the ChatOrchestrator for processing chat requests."""
    try:
        from ai_karen_engine.chat.factory import get_chat_orchestrator

        orchestrator = await get_chat_orchestrator()
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

    try:
        # Get runtime control plane
        runtime_plane = await get_chat_runtime_control_plane()
        degraded_continuation_response: Optional[DegradedResponse] = None

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
                    "Copilot continuing through degraded mode",
                    extra={"correlation_id": correlation_id},
                )
                degraded_continuation_response = response
            else:
                payload = serialize_runtime_response(response) or {}
                payload["correlation_id"] = correlation_id
                status_code = runtime_response_http_status(response) or 503
                return JSONResponse(
                    status_code=status_code,
                    content=payload,
                    headers={"X-Correlation-Id": correlation_id},
                )

        # Normal/degraded-chat path: execute via ChatOrchestrator.
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
                )
            raise
        if isinstance(orchestrator_response, ChatResponse):
            response_text = str(orchestrator_response.response or "").strip()
            if degraded_continuation_response is not None and (
                not response_text
                or response_text.lower().startswith("limited assistant with:")
                or response_text == degraded_continuation_response.message
            ):
                logger.info(
                    "Copilot replacing placeholder degraded text with degraded shim response",
                    extra={"correlation_id": correlation_id},
                )
                return _build_degraded_assist_response(
                    degraded=degraded_continuation_response,
                    user_message=request.message,
                    correlation_id=correlation_id,
                    status_code=200,
                )

            action_models = [
                SuggestedAction(
                    type=str(action.get("type", "unknown")),
                    params=(
                        action.get("params")
                        if isinstance(action.get("params"), dict)
                        else {
                            k: v
                            for k, v in action.items()
                            if k not in {"type", "confidence", "description"}
                        }
                    ),
                    confidence=float(action.get("confidence", 0.8)),
                    description=action.get("description"),
                )
                for action in (orchestrator_response.actions or [])
                if isinstance(action, dict)
            ]

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
            status_code=runtime_response_http_status(fallback) or 503,
            content=payload,
            headers={"X-Correlation-Id": correlation_id},
        )


__all__ = ["router"]
