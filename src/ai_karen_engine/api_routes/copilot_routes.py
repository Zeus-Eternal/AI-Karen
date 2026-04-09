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
)

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

        # Get runtime response based on current mode
        response = await runtime_plane.get_runtime_response(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            correlation_id=correlation_id,
        )

        # Handle different response types
        if hasattr(response, "mode"):
            # Structured runtime response (maintenance, emergency, etc.)
            if response.mode == "maintenance":
                return JSONResponse(
                    status_code=response.system_status_code,
                    content={
                        "mode": response.mode,
                        "message": response.message,
                        "estimated_completion_time": response.estimated_completion_time.isoformat()
                        if response.estimated_completion_time
                        else None,
                        "notification_supported": response.notification_supported,
                        "notification_request_allowed": response.notification_request_allowed,
                        "retry_after_seconds": response.retry_after_seconds,
                        "correlation_id": correlation_id,
                    },
                    headers={"X-Correlation-Id": correlation_id},
                )
            elif response.mode == "emergency_fallback":
                return JSONResponse(
                    status_code=response.system_status_code,
                    content={
                        "mode": response.mode,
                        "message": response.message,
                        "retry_after_seconds": response.retry_after_seconds,
                        "correlation_id": correlation_id,
                    },
                    headers={"X-Correlation-Id": correlation_id},
                )
            elif response.mode == "degraded":
                # For now, return degraded response
                return JSONResponse(
                    status_code=200,
                    content={
                        "mode": response.mode,
                        "message": response.message,
                        "correlation_id": correlation_id,
                    },
                    headers={"X-Correlation-Id": correlation_id},
                )

        # Normal mode response - would be chat orchestrator output
        # For now, return a placeholder
        return JSONResponse(
            status_code=200,
            content={
                "mode": "normal",
                "answer": "Chat functionality is temporarily disabled for maintenance.",
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    except Exception as e:
        logger.error(
            f"Copilot assist failed: {e}",
            extra={"correlation_id": correlation_id},
        )

        # Return emergency fallback on any error
        return JSONResponse(
            status_code=503,
            content={
                "mode": "emergency_fallback",
                "message": "Service temporarily unavailable",
                "retry_after_seconds": 60,
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-Id": correlation_id},
        )


__all__ = ["router"]
