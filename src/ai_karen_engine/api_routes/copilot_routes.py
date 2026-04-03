import os
import inspect
import logging
import time
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, AsyncIterator, cast
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse

# Import ChatOrchestrator dependency
from ai_karen_engine.core.dependencies import ChatOrchestrator_Dep
from ai_karen_engine.chat.ChatOrchestrator import ProcessingStatus, ChatRequest, ChatResponse
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

# Mount under /api/copilot when included with the global /api prefix
# No prefix here since it's already mounted at /api/copilot in routers.py
router = APIRouter(tags=["copilot"])


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
    action: str = Field(..., description="Registered action/predictor name, e.g. routing.select")
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


def _get_chat_orchestrator():
    """Return the ChatOrchestrator for processing chat requests."""
    try:
        from ai_karen_engine.chat.factory import get_chat_orchestrator
        orchestrator = get_chat_orchestrator()
        logger.info("Successfully retrieved ChatOrchestrator", extra={"correlation_id": "debug"})
        return orchestrator
    except Exception as exc:
        logger.error("Failed to get chat orchestrator: %s", exc, extra={"correlation_id": "debug"})
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
    async def log_event(self, *args: Any, **kwargs: Any) -> Any:
        ...


async def _log_audit_event(**kwargs: Any) -> None:
    """Best-effort audit logging with compatibility for partial shims."""
    try:
        audit_logger = _get_audit_logger()
        if audit_logger is not None and hasattr(audit_logger, 'log_audit_event'):
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
    correlation_id = http_request.headers.get("X-Correlation-Id") or f"copilot_{int(time.time())}"
    
    # Parse request body manually
    try:
        body = await http_request.json()
        req = StartActionRequest(**body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Resolve user context: prefer provided; otherwise permissive in dev/bypass
    if user_ctx is None:
        auth_mode = os.getenv("AUTH_MODE", "hybrid").lower()
        allow_public = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in ("1", "true", "yes")
        if not _is_production_env() and (
            allow_public or auth_mode == "bypass"
        ):
            user_ctx = {"user_id": "anonymous", "roles": ["admin"], "scopes": ["chat:write"]}
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
        allow_public = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in ("1", "true", "yes")
        if not allow_public:
            # Simple role checking - admin or user role required
            user_roles = user_ctx.get("roles", [])
            if not any(role in user_roles for role in ["admin", "user"]):
                raise HTTPException(status_code=403, detail="Insufficient permissions - user or admin role required")
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
            raise HTTPException(status_code=404, detail=f"Unknown action: {req.action}. Available: {available}")

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

        return StartActionResponse(status="ok", output=output or {}, correlation_id=correlation_id)
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


@router.post("/assist", response_model=AssistResponse)
async def copilot_assist(
    request: AssistRequest,
    http_request: Request,
    chat_orchestrator: Any = Depends(ChatOrchestrator_Dep),  # Use ChatOrchestrator as absolute source of truth
):
    """Thin copilot ingress that delegates chat lifecycle authority to ChatOrchestrator."""
    start_time = time.time()
    correlation_id = get_correlation_id(http_request) or f"copilot_{int(time.time())}"
    
    # Log input parameters
    logger.info("Starting copilot assist", extra={
        "correlation_id": correlation_id,
        "user_id": request.user_id,
        "message_length": len(request.message),
        "session_id": request.session_id,
        "preferred_llm_provider": request.preferred_llm_provider,
        "preferred_model": request.preferred_model,
    })
    
    # Extract request data
    message = request.message
    org_id = request.org_id
    request_context = dict(request.context) if isinstance(request.context, dict) else {}
    session_id = _normalize_session_id(
        request.session_id
        or request_context.get("session_id")
        or request_context.get("conversation_id")
    )
    conversation_id = _normalize_session_id(
        request_context.get("conversation_id") or session_id
    )
    
    # Get user context from request state first, then fall back to authenticated context
    user_context = None
    try:
        user_context = getattr(http_request.state, "user", None)
    except AttributeError:
        user_context = None

    authenticated_context = (
        request_context.get("authenticated_user")
        if isinstance(request_context.get("authenticated_user"), dict)
        else None
    )
    if not isinstance(user_context, dict) and authenticated_context:
        user_context = authenticated_context

    authenticated_user_id = None
    if isinstance(user_context, dict):
        authenticated_user_id = str(user_context.get("user_id") or "").strip() or None
    if not authenticated_user_id and authenticated_context:
        authenticated_user_id = str(authenticated_context.get("user_id") or "").strip() or None

    request_user_id = str(request.user_id or "").strip() or None
    user_id = authenticated_user_id or request_user_id or "anonymous"
    tenant_id = str(
        (user_context or {}).get("tenant_id")
        or (authenticated_context or {}).get("tenant_id")
        or org_id
        or "default"
    )
    
    allow_public_copilot = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in ("1", "true", "yes")
    auth_context = {
        "allow_anonymous": not bool(authenticated_user_id),
        "public_copilot_enabled": allow_public_copilot,
        "request_user_id": request.user_id,
    }
    if isinstance(user_context, dict):
        auth_context["user_context"] = _json_safe(user_context)
        access_token = user_context.get("access_token") or user_context.get("token")
        if access_token:
            auth_context["access_token"] = access_token

    try:
        chat_request = ChatRequest(
            request_id=str(uuid.uuid4()),
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            message=message,
            user_id=user_id,
            org_id=org_id or tenant_id,
            conversation_id=conversation_id,
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            stream=request.stream,
            streaming=request.stream,
            include_context=True,
            metadata={
                "source": "copilot",
                "platform": "copilot",
                "request_context": request_context,
                "auth_context": auth_context,
                "preferred_llm_provider": request.preferred_llm_provider,
                "preferred_model": request.preferred_model,
                "top_k": request.top_k,
                "correlation_id": correlation_id,
            },
        )
        
        logger.info("ChatRequest created successfully", extra={"correlation_id": correlation_id})
        
        if request.stream:
            orchestrator_gen = await chat_orchestrator.handle_chat_stream(chat_request)
            
            if orchestrator_gen is None:
                logger.error("ChatOrchestrator returned None for streaming request", extra={"correlation_id": correlation_id})
                return JSONResponse(
                    content={"error": "Chat service unavailable", "correlation_id": correlation_id},
                    status_code=503
                )
            
            async def stream_generator():
                import json
                try:
                    async for chunk in orchestrator_gen:
                        chunk_dict = {
                            "type": chunk.type,
                            "content": chunk.content,
                            "correlation_id": chunk.correlation_id,
                            "metadata": _json_safe(chunk.metadata) if chunk.metadata else {}
                        }
                        yield f"data: {json.dumps(chunk_dict)}\n\n"
                except Exception as e:
                    logger.error(f"Error in stream generator: {e}", extra={"correlation_id": correlation_id})
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                    
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={"X-Correlation-Id": correlation_id}
            )
            
        response_raw = await chat_orchestrator.handle_chat(chat_request)
        if response_raw is None:
            logger.error("ChatOrchestrator returned None for non-streaming request", extra={"correlation_id": correlation_id})
            raise HTTPException(status_code=503, detail="Chat service returned no response")
            
        response = cast(ChatResponse, response_raw)
        
        # Calculate timing
        total_time_ms = (time.time() - start_time) * 1000
        
        # Log ChatResponse
        logger.info("Received ChatResponse", extra={
            "correlation_id": correlation_id,
            "response_length": len(getattr(response, "response", "") or ""),
            "status": str(getattr(response, "status", "unknown")),
        })
        
        # Extract response data
        metadata_dict: Dict[str, Any] = getattr(response, "metadata", {}) or {}
        metadata_dict["total_ms"] = total_time_ms
        metadata_dict["conversation_id"] = getattr(response, "conversation_id", conversation_id)
        metadata_dict["assistant_message_id"] = getattr(response, "assistant_message_id", None)
        metadata_dict["execution_path"] = getattr(response, "execution_path", None)
        telemetry = getattr(response, "telemetry", {}) or {}
        if telemetry:
            metadata_dict["telemetry"] = telemetry

        llm_metadata = metadata_dict.get("llm")
        if isinstance(llm_metadata, dict):
            preferred_failure_reason = str(llm_metadata.get("preferred_failure_reason") or "").strip()
            failure_reason = str(llm_metadata.get("failure_reason") or "").strip()
            if preferred_failure_reason:
                llm_metadata["failure_reason"] = preferred_failure_reason
                if not llm_metadata.get("raw_failure_reason") and failure_reason and failure_reason != preferred_failure_reason:
                    llm_metadata["raw_failure_reason"] = failure_reason

        # Handle failures explicitly
        if getattr(response_raw, "status", None) == ProcessingStatus.FAILED:
            logger.warning(f"Orchestrator reported failure for {correlation_id}: {getattr(response_raw, 'error', 'Unknown error')}")
            metadata_dict["is_error_response"] = True
            metadata_dict["error_type"] = str(getattr(response_raw, "error_type", "unknown"))

        # Map actions safely
        raw_actions = getattr(response, "actions", []) or []
        mapped_actions = []
        for a in raw_actions:
            if isinstance(a, dict) and "type" in a:
                mapped_actions.append(SuggestedAction(
                    type=a["type"],
                    params=a.get("params", {}),
                    confidence=a.get("confidence", 0.9),
                    description=a.get("description")
                ))

        logger.warning(
            "copilot_assist returning JSON response",
            extra={
                "correlation_id": correlation_id,
                "status": str(getattr(response, "status", "unknown")),
                "answer_length": len(str(getattr(response, "response", "") or "")),
                "metadata_keys": list(metadata_dict.keys()),
            },
        )

        return _assist_response_json(
            answer=str(getattr(response, "response", "No response generated")),
            structured_content=_json_safe(getattr(response, "structured_content", {})),
            actions=mapped_actions,
            metadata=_json_safe(metadata_dict),
            correlation_id=correlation_id,
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(
            "Copilot assist failed with %s: %s\n%s",
            type(e).__name__, e, error_trace,
            extra={"correlation_id": correlation_id, "user_id": user_id, "session_id": session_id},
        )
        
        if _is_production_env():
            if isinstance(e, HTTPException):
                safe_detail = e.detail
                if not isinstance(safe_detail, dict):
                    safe_detail = {
                        "message": str(e.detail) if e.detail else "Copilot request failed",
                }
                safe_detail = {
                    **safe_detail,
                    "correlation_id": correlation_id,
                }
                raise HTTPException(status_code=e.status_code, detail=safe_detail) from e

            error_message = str(e).strip() or "Copilot request failed"
            error_code = f"copilot_{type(e).__name__.lower()}"
            return JSONResponse(
                status_code=503,
                content={
                    "user_message": error_message,
                    "error": error_message,
                    "detail": error_message,
                    "error_code": error_code,
                    "exception_type": type(e).__name__,
                    "correlation_id": correlation_id,
                },
            )
        
        return _assist_response_json(
            answer="I'm sorry, but I'm experiencing technical difficulties right now. Please try again later.",
            structured_content={},
            actions=[],
            metadata={
                "error": str(e),
                "correlation_id": correlation_id,
                "total_ms": (time.time() - start_time) * 1000,
            },
            correlation_id=correlation_id,
        )
        

__all__ = ["router"]
