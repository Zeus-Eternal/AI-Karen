import asyncio
import os
import logging
import time
import uuid
from functools import lru_cache
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, cast

from fastapi import APIRouter, Request, HTTPException, Depends
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
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

from ai_karen_engine.chat.identity_context import (
    build_user_identity_line,
    extract_recent_name,
    is_identity_lookup,
    resolve_display_name,
)

# Mount under /api/copilot when included with the global /api prefix
# No prefix here since it's already mounted at /api/copilot in routers.py
router = APIRouter(tags=["copilot"])

# Ensure routing predictors are registered so /start can dispatch actions.
# Importing them eagerly pulls in heavy optional dependencies (spaCy,
# transformers, SQLAlchemy). We defer registration until a request needs
# it to keep unit tests and health checks lightweight.
_routing_actions_ready = False


def _is_production_env() -> bool:
    env = os.getenv("ENVIRONMENT", os.getenv("KARI_ENV", "development")).lower()
    return env in ("production", "prod")


def _allow_copilot_degraded_response() -> bool:
    value = os.getenv("COPILOT_ALLOW_DEGRADED_RESPONSE", "true").lower()
    return value in ("1", "true", "yes", "on")


def _get_saved_model_selection() -> tuple[str, Optional[str]]:
    """Resolve the persisted provider/model selection from local settings."""

    try:
        from services.memory.settings_manager import get_settings_manager

        settings = get_settings_manager()
        provider = str(settings.get_setting("provider", "llama-cpp") or "llama-cpp").strip()
        model = settings.get_setting("model")
        model_value = str(model).strip() if model else None

        aliases = {
            "local": "llamacpp",
            "llama-cpp": "llamacpp",
            "llama_cpp": "llamacpp",
        }
        return aliases.get(provider.lower(), provider.lower()), model_value
    except Exception:
        return "llamacpp", None


def _ensure_routing_actions_registered() -> None:
    global _routing_actions_ready
    if _routing_actions_ready:
        return

    try:
        from ai_karen_engine.integrations.copilotkit.routing_actions import (
            ensure_kire_actions_registered,
        )

        ensure_kire_actions_registered()
        _routing_actions_ready = True
    except Exception:
        # Best-effort; if not present, action registry may be empty until lazily imported elsewhere
        pass

# Optional imports removed: heavyweight services are resolved lazily where required.

# Legacy RBAC helper is unused here; provide a stub to avoid heavy imports.
async def check_rbac_scope(*args, **kwargs):  # pragma: no cover - compatibility shim
    return True


async def _resolve_user_context(request: Request) -> Optional[Dict[str, Any]]:
    """Best-effort user context resolution without heavy imports."""

    # First check if user context is already set on request state (by our wrapper)
    try:
        if hasattr(request.state, 'user') and request.state.user:
            return request.state.user
    except AttributeError:
        pass
    
    try:
        from ai_karen_engine.core.dependencies import get_current_user_context
    except Exception:
        return None

    try:
        return await get_current_user_context(request)  # type: ignore[arg-type]
    except Exception:
        return None


def _get_audit_logger():
    """Lazily import the audit logger to avoid heavy startup costs."""

    try:
        from ai_karen_engine.services.audit_logger import get_audit_logger as _getter

        return _getter()
    except Exception:
        return None


class _AuditLoggerProtocol(Protocol):
    async def log_event(self, *args: Any, **kwargs: Any) -> Any:
        ...


def _get_predictor_registry():
    """Return the predictor registry with graceful fallback."""

    try:
        from ai_karen_engine.core.predictors import predictor_registry as registry

        return registry
    except Exception:
        return {}


class _FallbackServiceStatus:
    HEALTHY = "healthy"


def _get_connection_health_manager():
    """Lazily import the connection health manager components."""

    try:
        from services.memory.connection_health_manager import (
            get_connection_health_manager as _getter,
            ServiceStatus as _status,
        )

        return _getter(), _status
    except Exception:
        return None, _FallbackServiceStatus


async def _log_audit_event(**kwargs: Any) -> None:
    """Best-effort audit logging with compatibility for partial shims."""
    try:
        audit_logger = cast(Optional[_AuditLoggerProtocol], _get_audit_logger())
        if audit_logger is not None:
            await audit_logger.log_event(**kwargs)
    except Exception:
        pass


async def _build_degraded_direct_answer(
    user_message: str,
    *,
    auth_service: Optional[Any],
    user_id: Optional[str],
    user_context: Optional[Dict[str, Any]],
    request_context: Dict[str, Any],
) -> Optional[str]:
    normalized = " ".join(user_message.lower().split())
    now = datetime.now().astimezone()

    if is_identity_lookup(normalized):
        known_name = extract_recent_name(request_context) or await resolve_display_name(
            auth_service=auth_service,
            user_id=user_id,
            user_context=user_context,
            request_context=request_context,
        )
        if known_name:
            return f"Your name is {known_name}."
        return "I don't have your name yet in this degraded session."

    if "what's the date" in normalized or "whats the date" in normalized or "what is the date" in normalized or normalized == "date":
        return f"Today's date is {now.strftime('%A, %B %d, %Y')}."

    if "what time" in normalized or "what's the time" in normalized or "whats the time" in normalized or normalized == "time":
        return f"The current time is {now.strftime('%-I:%M %p %Z')}."

    return None


def _is_first_turn(request_context: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(request_context, dict):
        return True

    recent_messages = request_context.get("recent_messages", [])
    if not isinstance(recent_messages, list):
        return True

    meaningful_messages = 0
    for item in recent_messages:
        if not isinstance(item, dict):
            continue
        if str(item.get("content", "")).strip():
            meaningful_messages += 1

    return meaningful_messages == 0


def _classify_provider_failure(error_message: str) -> Dict[str, Any]:
    """Classify provider/runtime failures for user-facing fallback messaging."""

    snippet = str(error_message or "").strip()
    lowered = snippet.lower()

    safety_markers = (
        "content failed safety evaluation",
        "blocked by safety",
        "safety filter",
        "safety filters",
        "safety policy",
        "content blocked",
        "moderation",
        "policy violation",
    )
    if any(marker in lowered for marker in safety_markers):
        return {
            "category": "safety_blocked",
            "is_degraded": False,
            "cause": "The AI provider blocked this request under its safety policy.",
            "suggestion": "Try rephrasing the request or asking for a safer, higher-level version.",
            "quote_user_request": False,
        }

    if "timeout" in lowered or "timed out" in lowered:
        return {
            "category": "timeout",
            "is_degraded": True,
            "cause": "The primary AI provider timed out while generating a response.",
            "suggestion": "Try a shorter or simpler prompt, or switch to a different provider in Settings.",
            "quote_user_request": True,
        }

    if "api key" in lowered or "auth" in lowered or "401" in lowered:
        return {
            "category": "authentication_error",
            "is_degraded": True,
            "cause": "Authentication with the AI provider failed.",
            "suggestion": "Check your API key in Application Settings -> Model Configuration.",
            "quote_user_request": True,
        }

    if "connection" in lowered or "network" in lowered or "connect" in lowered:
        return {
            "category": "connection_error",
            "is_degraded": True,
            "cause": "Could not connect to the AI provider.",
            "suggestion": "Check your network connection and the provider's base URL in Settings.",
            "quote_user_request": True,
        }

    if "rate limit" in lowered or "429" in lowered:
        return {
            "category": "rate_limited",
            "is_degraded": True,
            "cause": "The AI provider is rate-limiting requests.",
            "suggestion": "Wait a moment before trying again, or switch to a different provider.",
            "quote_user_request": True,
        }

    return {
        "category": "provider_error",
        "is_degraded": True,
        "cause": f"The AI provider encountered an error: {snippet[:100]}",
        "suggestion": "Try again shortly, or switch to a different provider in Settings.",
        "quote_user_request": True,
    }


def _normalize_session_id(session_id: Optional[str]) -> str:
    """Return a UUID session id for downstream memory/orchestration services."""

    raw = str(session_id or "").strip()
    if not raw:
        return str(uuid.uuid4())

    candidates = [raw]
    if raw.startswith("chat_"):
        candidates.append(raw[len("chat_"):])

    for candidate in candidates:
        try:
            return str(uuid.UUID(candidate))
        except Exception:
            continue

    generated = str(uuid.uuid4())
    logger.warning("Invalid session_id received for copilot assist; generated replacement.", extra={
        "provided_session_id": raw,
        "normalized_session_id": generated,
    })
    return generated


class ContextHit(BaseModel):
    id: str
    text: str
    preview: Optional[str] = None
    score: float
    tags: List[str] = Field(default_factory=list)
    recency: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(5, ge=1, le=10)
    decay_tier: str = Field("short")
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    org_id: Optional[str] = None


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


class AssistResponse(BaseModel):
    answer: str
    structured_content: Dict[str, Any] = Field(default_factory=dict)
    actions: List[SuggestedAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "")


def _json_safe(value: Any) -> Any:
    """Convert response metadata into JSON-safe primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


@lru_cache
def get_langgraph_orchestrator():
    """Return the shared LangGraph orchestrator used by the production orchestration API."""
    from ai_karen_engine.core.langgraph_orchestrator import get_default_orchestrator

    return get_default_orchestrator()


@lru_cache
def get_prompt_auth_service():
    """Return the lightweight auth service used for identity-aware degraded replies."""
    try:
        from auth.auth_service import AuthService as PromptAuthService
        return PromptAuthService()
    except Exception:
        try:
            from src.auth.auth_service import AuthService as PromptAuthService
            return PromptAuthService()
        except Exception:
            logger.warning("Prompt auth service unavailable; continuing without identity auth support.")
            return None


def _build_orchestration_messages(
    request_context: Optional[Dict[str, Any]],
    user_message: str,
) -> List[Any]:
    """Build LangChain messages from recent UI history plus the current turn."""
    messages: List[Any] = []

    recent_messages = request_context.get("recent_messages", []) if isinstance(request_context, dict) else []
    if isinstance(recent_messages, list):
        for item in recent_messages[-6:]:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            if role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

    messages.append(HumanMessage(content=user_message))
    return messages


class StartActionRequest(BaseModel):
    action: str = Field(..., description="Registered action/predictor name, e.g. routing.select")
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class StartActionResponse(BaseModel):
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str


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
            # Minimal safe fallbacks for profile-related actions to keep the UI usable
            if req.action == "routing.profile.list":
                try:
                    from ai_karen_engine.config.user_profiles import get_user_profiles_manager
                    upm = get_user_profiles_manager()
                    profiles = upm.list_profiles()
                    active = upm.get_active_profile()
                    out = {
                        "active_profile": active.id if active else None,
                        "profiles": [
                            {
                                "id": p.id,
                                "name": p.name,
                                "is_active": bool(active and p.id == active.id),
                                "assignments_count": len(p.assignments or {}),
                                "fallback_chain": p.fallback_chain,
                            }
                            for p in profiles
                        ],
                    }
                    return StartActionResponse(status="ok", output=out, correlation_id=correlation_id)
                except Exception:
                    # Graceful empty response so the UI can render
                    out = {"active_profile": None, "profiles": []}
                    return StartActionResponse(status="ok", output=out, correlation_id=correlation_id)

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
    orchestrator = Depends(get_langgraph_orchestrator),
    auth_service = Depends(get_prompt_auth_service),
):
    """Production-ready copilot assist endpoint with real AI integration."""
    _ensure_routing_actions_registered()
    start_time = time.time()
    correlation_id = get_correlation_id(http_request) or f"copilot_{int(time.time())}"
    is_degraded = False
    
    # Get user context from request state (set by our authentication wrapper)
    user_context = None
    try:
        user_context = getattr(http_request.state, "user", None)
    except AttributeError:
        user_context = None

    # Use authenticated user_id if available, otherwise fall back to request user_id
    authenticated_user_id = user_context.get("user_id") if user_context else None
    user_id = authenticated_user_id or request.user_id or "anonymous"
    message = request.message
    org_id = request.org_id
    top_k = request.top_k
    saved_provider, saved_model = _get_saved_model_selection()
    preferred_llm_provider = str(request.preferred_llm_provider or saved_provider or "llamacpp").strip()
    preferred_model = request.preferred_model or saved_model
    session_id = _normalize_session_id(request.session_id)
    allow_public_copilot = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in ("1", "true", "yes")
    auth_context = {
        # This route already admitted the request. Preserve authenticated context
        # when available, otherwise grant limited anonymous chat access instead
        # of letting the orchestration auth gate reject the request a second time.
        "allow_anonymous": bool(user_context is None),
        "public_copilot_enabled": allow_public_copilot,
        "request_user_id": request.user_id,
    }
    if isinstance(user_context, dict):
        auth_context["user_context"] = _json_safe(user_context)
        access_token = user_context.get("access_token") or user_context.get("token")
        if access_token:
            auth_context["access_token"] = access_token

    # Initialize response components
    context_hits = []
    suggested_actions = []
    structured_content = {}
    answer = "I'm processing your request..."
    timings: Dict[str, Any] = {"start": start_time}
    llm_metadata: Dict[str, Any] = {}
    response: Optional[Any] = None
    response_metadata: Optional[Dict[str, Any]] = None
    _fb = None
    degraded_cause: Optional[str] = None

    # Health gate: advisory signal for degraded conditions. Do not short-circuit
    # the response path unless later execution actually fails.
    try:
        if os.getenv("COPILOT_ASSIST_HEALTH_GATE", "true").lower() in ("1", "true", "yes"):
            mgr, status_cls = _get_connection_health_manager()
            if mgr is None:
                raise RuntimeError("connection health manager unavailable")
            unhealthy: List[str] = []
            critical_services: List[str] = ["database"]
            if os.getenv("MILVUS_REQUIRED", "false").lower() in ("1", "true", "yes"):
                critical_services.append("milvus")
            for svc in critical_services:
                status = None
                try:
                    status = mgr.get_service_status(svc)
                except Exception:
                    status = None
                status_is_healthy = bool(
                    status and getattr(status, "status", getattr(status, "value", None)) == status_cls.HEALTHY
                )
                if not status_is_healthy:
                    try:
                        # Perform a quick active check with a tight timeout
                        checked = await asyncio.wait_for(mgr.check_service_health(svc), timeout=1.0)
                        status = checked
                    except Exception:
                        pass
                    status_is_healthy = bool(
                        status and getattr(status, "status", getattr(status, "value", None)) == status_cls.HEALTHY
                    )
                    if not status_is_healthy:
                        unhealthy.append(svc)
            if unhealthy:
                if _is_production_env() and not _allow_copilot_degraded_response():
                    raise HTTPException(
                        status_code=503,
                        detail=f"Critical services unavailable: {', '.join(unhealthy)}",
                    )
                logger.warning(
                    "Health gate failed for services: %s. Continuing with orchestrator/local routing before degrading.",
                    ", ".join(unhealthy),
                    extra={"correlation_id": correlation_id}
                )
                degraded_cause = f"Core backend services ({', '.join(unhealthy)}) are temporarily unavailable."
    except Exception:
        # Health gate failures should never block the main flow
        pass

    # If the health gate already flagged degraded mode, skip the full orchestrator
    # (which depends on the database) and try the local model directly.
    if is_degraded:
        logger.info(
            "Health gate flagged degraded mode – trying local model directly",
            extra={"correlation_id": correlation_id},
        )
        # Extract the original user message from the injected system warning
        user_msg = message
        if "User Request:" in user_msg:
            user_msg = user_msg.split("User Request:", 1)[-1].strip()

        degraded_cause = degraded_cause or "Core backend services are temporarily unavailable."
        request_context = request.context if isinstance(request.context, dict) else {}
        is_first_turn = _is_first_turn(request_context)
        display_name = await resolve_display_name(
            auth_service=auth_service,
            user_id=user_id,
            user_context=user_context,
            request_context=request_context,
        )
        direct_answer = await _build_degraded_direct_answer(
            user_msg,
            auth_service=auth_service,
            user_id=user_id,
            user_context=user_context,
            request_context=request_context,
        )

        if direct_answer:
            total_time = (time.time() - start_time) * 1000
            timings["total_ms"] = total_time
            return {
                "answer": direct_answer,
                "structured_content": structured_content,
                "actions": suggested_actions,
                "metadata": {
                    "timings": timings,
                    "context": context_hits,
                    "degraded_mode": True,
                    "degraded_cause": degraded_cause,
                    "llm": {
                        "provider": "system",
                        "model_id": "degraded-direct-answer",
                        "model_name": "Deterministic Degraded Answer",
                        "source": "health_gate_direct",
                        "is_degraded": True,
                        "duration": total_time / 1000,
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "confidence_score": 1.0,
                        "routing_confidence": 1.0,
                        "routing_rationale": "Used deterministic degraded-mode answer for a grounded identity/date/time request.",
                    },
                    "orchestrator": {
                        "used_fallback": True,
                        "context_used": bool(request_context.get("recent_messages")),
                    },
                },
                "correlation_id": correlation_id,
            }

        # Create a basic message list for the fallback provider to ensure 
        # proper template application (prevents hallucinations).
        system_prompt_parts = [
            "You are Karen, an intelligent AI assistant built by Zeus-Eternal with love.",
            "Your personality is helpful, professional, and precise.",
            "You are currently operating in degraded mode because some core backend services are unavailable.",
            "Do not claim that systems are fully operational, normal, healthy, or functioning normally.",
            "Be truthful that you are in degraded mode when answering.",
            "If this is the first turn, greet the user briefly before answering.",
            "If you know the user's display name, use it naturally in the greeting.",
            "Keep the degraded-mode acknowledgement brief and then answer the user's request directly.",
            f"Current date and time: {datetime.now().astimezone().strftime('%A, %B %d, %Y %I:%M %p %Z')}.",
            f"First turn in conversation: {'yes' if is_first_turn else 'no'}.",
        ]
        if display_name:
            system_prompt_parts.append(build_user_identity_line(display_name))

        fallback_messages = [
            {
                "role": "system", 
                "content": " ".join(system_prompt_parts),
            },
        ]

        recent_messages = request_context.get("recent_messages", [])
        if isinstance(recent_messages, list):
            for item in recent_messages[-6:]:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = str(item.get("content", "")).strip()
                if role in {"user", "assistant"} and content:
                    fallback_messages.append({"role": role, "content": content})

        fallback_messages.append({"role": "user", "content": user_msg})

        greeting = f"Hi {display_name}. " if is_first_turn and display_name else ("Hi. " if is_first_turn else "")
        answer = (
            f"{greeting}I'm in degraded mode right now because core backend services are unavailable. "
            f"I received your request and can keep the conversation moving, but I can't safely run the full response pipeline yet. "
            f"Please try again shortly once the core services recover."
        )
        logger.info("Produced deterministic health-gate degraded response", extra={"correlation_id": correlation_id})

        total_time = (time.time() - start_time) * 1000
        timings["total_ms"] = total_time
        # Extract metadata from fallback provider
        usage = {"prompt_tokens": 0, "completion_tokens": len(answer) // 4, "total_tokens": len(answer) // 4}
        fb_model_id = "degraded-direct-fallback"
        fb_confidence = 0.5
        
        return {
            "answer": answer,
            "structured_content": structured_content,
            "actions": suggested_actions,
            "metadata": {
                "timings": timings,
                "context": context_hits,
                "degraded_mode": True,
                "degraded_cause": degraded_cause,
                "llm": {
                    "provider": "system",
                    "model_id": fb_model_id,
                    "model_name": fb_model_id.replace("fallback:", "").replace("_", " ").title(),
                    "source": "health_gate_direct",
                    "is_degraded": True,
                    "duration": total_time / 1000,
                    "usage": usage,
                    "confidence_score": fb_confidence,
                    "routing_confidence": 0.0,
                    "routing_rationale": f"Health check failed: {degraded_cause or 'system unhealthy'}"
                },
                "orchestrator": {
                    "used_fallback": True,
                    "context_used": False,
                },
            },
            "correlation_id": correlation_id,
        }

    # Try to get real AI response using the injected chat orchestrator
    llm_start = time.time()
    try:
        orchestration_messages = _build_orchestration_messages(request.context, message)

        # Process through the shared LangGraph orchestrator with a hard timeout
        # to prevent the frontend proxy from hitting its 120s abort.
        try:
            assist_timeout_seconds = float(
                os.getenv("COPILOT_ASSIST_TIMEOUT_SECONDS", "45")
            )
            response = await asyncio.wait_for(
                orchestrator.process(
                    messages=orchestration_messages,
                    user_id=user_id,
                    session_id=session_id or correlation_id,
                    config={
                        "source": "copilot_assist",
                        "org_id": org_id,
                        "platform": "copilot",
                        "streaming_enabled": False,
                        "request_context": request.context,
                        "auth_context": auth_context,
                        "preferred_llm_provider": preferred_llm_provider,
                        "preferred_model": preferred_model,
                    },
                ),
                timeout=assist_timeout_seconds,
            )
        except asyncio.TimeoutError:
            # Let the outer except Exception handler deal with this so the
            # FallbackProvider is invoked instead of returning a canned string.
            timeout_secs = os.getenv("COPILOT_ASSIST_TIMEOUT_SECONDS", "90")
            raise RuntimeError(
                f"Primary AI provider timed out after {timeout_secs}s. "
                "The request was cancelled to keep the application responsive."
            )
        
        # Handle the response using the LangGraph orchestration state structure
        if isinstance(response, dict):
            answer = str(response.get("response") or "").strip()
            response_metadata = cast(Optional[Dict[str, Any]], response.get("response_metadata"))
            if not answer:
                response_errors = response.get("errors")
                response_warnings = response.get("warnings")
                if isinstance(response_errors, list) and response_errors:
                    raise RuntimeError(str(response_errors[-1]))
                if isinstance(response_warnings, list) and response_warnings:
                    raise RuntimeError(str(response_warnings[-1]))
                raise RuntimeError("No response returned.")
            logger.info("Copilot assist produced LangGraph orchestrator response", extra={"correlation_id": correlation_id})

            metadata_provider = response_metadata.get("provider") if isinstance(response_metadata, dict) else None
            metadata_model = response_metadata.get("model") if isinstance(response_metadata, dict) else None
            selected_provider = str(response.get("selected_provider") or metadata_provider or "fallback")
            selected_model = str(response.get("selected_model") or metadata_model or "unknown")
            llm_metadata = {
                "provider": selected_provider,
                "model_id": selected_model,
                "model_name": selected_model.replace("_", " ").title(),
                "source": "langgraph_orchestrator",
                "is_degraded": selected_provider == "fallback",
                "duration": (time.time() - llm_start),
                "usage": {},
                "confidence_score": 0.75 if selected_provider != "fallback" else 0.35,
                "routing_confidence": 0.0,
                "routing_rationale": response.get("routing_reason") or "LangGraph orchestration route",
            }

            memory_context = response.get("memory_context")
            if isinstance(memory_context, dict):
                summary = memory_context.get("context_summary")
                if summary:
                    context_hits.append(
                        {
                            "id": f"context_{int(time.time())}",
                            "text": str(summary)[:500],
                            "preview": str(summary)[:200] + "..." if len(str(summary)) > 200 else str(summary),
                            "score": 0.8,
                            "tags": ["langgraph", "memory_context"],
                            "recency": "recent",
                            "meta": _json_safe(memory_context),
                            "importance": 7,
                            "decay_tier": "short",
                            "created_at": datetime.now().isoformat(),
                            "updated_at": None,
                            "user_id": user_id,
                            "org_id": org_id,
                        }
                    )

            # Generate intelligent actions based on the response and message content
            message_lower = message.lower()
            if any(word in message_lower for word in ["code", "debug", "error", "fix", "programming"]):
                suggested_actions.append({
                    "type": "open_doc",
                    "params": {"doc_type": "code_reference", "topic": "debugging"},
                    "confidence": 0.8,
                    "description": "Open debugging documentation"
                })
            
            if any(word in message_lower for word in ["remember", "save", "store", "important"]):
                suggested_actions.append({
                    "type": "pin_memory",
                    "params": {"content": message, "importance": "high"},
                    "confidence": 0.9,
                    "description": "Save this information to memory"
                })
            
            if any(word in message_lower for word in ["task", "todo", "remind", "follow"]):
                suggested_actions.append({
                    "type": "add_task",
                    "params": {"task": f"Follow up: {message[:50]}..."},
                    "confidence": 0.7,
                    "description": "Add as a task to track"
                })
            
            # Always suggest export for longer responses
            if len(answer) > 200:
                suggested_actions.append({
                    "type": "export_note",
                    "params": {"title": f"AI Response: {message[:30]}...", "content": answer},
                    "confidence": 0.6,
                    "description": "Export this response as a note"
                })
        else:
            raise RuntimeError("Unexpected orchestration response.")
        
        timings["llm_generation_ms"] = (time.time() - llm_start) * 1000
        
    except Exception as e:
        timings["llm_error"] = str(e)
        logger.error(
            "Copilot assist failed to obtain a verified LLM response: %s",
            e,
            extra={"correlation_id": correlation_id},
        )
        if _is_production_env() and not _allow_copilot_degraded_response():
            raise HTTPException(
                status_code=503,
                detail="Copilot provider unavailable",
            ) from e
        fallback_answer: Optional[str] = None
        fallback_usage: Dict[str, Any] = {}
        fallback_model_id = "degraded-fallback"
        fallback_provider_name = "fallback"
        fallback_reason = str(e)[:200]
        failure_info = _classify_provider_failure(fallback_reason)
        is_degraded = bool(failure_info["is_degraded"])

        try:
            from ai_karen_engine.config.config_manager import (
                get_default_model,
                get_default_provider,
            )
            from ai_karen_engine.integrations.providers.fallback_provider import (
                FallbackProvider,
            )

            configured_provider = str(preferred_llm_provider or get_default_provider() or "llamacpp").strip()
            configured_provider = "llamacpp" if configured_provider == "local" else configured_provider
            configured_model = str(
                preferred_model
                or get_default_model("llamacpp" if configured_provider == "llamacpp" else configured_provider)
                or get_default_model()
            ).strip()

            fallback_messages = _build_orchestration_messages(request.context, message)
            _fb = FallbackProvider(model=configured_model)
            fallback_answer = str(
                _fb.generate_text(
                    fallback_messages,
                    model=configured_model,
                    provider=configured_provider,
                )
            ).strip()
            fallback_usage = cast(Dict[str, Any], getattr(_fb, "last_usage", {}) or {})
            fallback_model_id = str(fallback_usage.get("model_id") or configured_model or fallback_model_id)
            fallback_provider_name = str(fallback_usage.get("source") or configured_provider or fallback_provider_name)

            if fallback_answer:
                answer = fallback_answer
                llm_metadata = {
                    "provider": configured_provider,
                    "model_id": fallback_model_id,
                    "model_name": fallback_model_id.replace("fallback:", "").replace("_", " ").title(),
                    "source": "configured_fallback_provider",
                    "is_degraded": True,
                    "duration": (time.time() - llm_start),
                    "failure_reason": fallback_reason,
                    "usage": fallback_usage or {
                        "total_tokens": len(answer) // 4,
                        "prompt_tokens": 0,
                        "completion_tokens": len(answer) // 4,
                    },
                    "confidence_score": float(fallback_usage.get("confidence", 0.5)),
                    "routing_confidence": 0.0,
                    "routing_rationale": (
                        f"Primary orchestration failed; used configured fallback model "
                        f"{configured_model} via {configured_provider}."
                    ),
                }
                logger.info(
                    "Copilot assist used configured fallback model",
                    extra={
                        "correlation_id": correlation_id,
                        "configured_provider": configured_provider,
                        "configured_model": configured_model,
                        "resolved_model_id": fallback_model_id,
                    },
                )
        except Exception as fallback_exc:
            logger.warning(
                "Configured fallback provider failed after orchestration error: %s",
                fallback_exc,
                extra={"correlation_id": correlation_id},
            )

        if not fallback_answer:
            # ----- Final deterministic fallback only if configured fallback also failed -----
            error_snippet = str(e)[:200]
            user_msg = message

            if "User Request:" in user_msg:
                user_msg = user_msg.split("User Request:", 1)[-1].strip()

            cause = str(failure_info["cause"])
            suggestion = str(failure_info["suggestion"])
            if failure_info["category"] == "safety_blocked":
                answer = (
                    "Karen couldn't complete that request because the AI provider blocked it under its safety policy.\n\n"
                    "I can still help with a safer rewrite, a higher-level summary, or a narrower technical question.\n\n"
                    f"{suggestion}"
                )
            else:
                quoted_request = (
                    f"Your question: \"{user_msg[:120]}{'...' if len(user_msg) > 120 else ''}\"\n\n"
                    if failure_info["quote_user_request"]
                    else ""
                )
                answer = (
                    f"Karen is operating in degraded mode.\n\n"
                    f"Cause: {cause}\n\n"
                    f"{quoted_request}"
                    f"I'm unable to generate a full AI response right now, but I've logged your request. "
                    f"{suggestion}"
                )
            logger.info("Produced final deterministic degraded response", extra={"correlation_id": correlation_id})

            suggested_actions.append({
                "type": "add_task",
                "params": {"task": f"Retry: {user_msg[:40]}..."},
                "confidence": 0.7,
                "description": "Retry this request once the AI provider is healthy"
            })

            if not llm_metadata:
                llm_metadata = {
                    "provider": "fallback",
                    "model_id": fallback_model_id,
                    "model_name": fallback_model_id.replace("fallback:", "").replace("_", " ").title(),
                    "source": "runtime_error_fallback",
                    "is_degraded": bool(failure_info["is_degraded"]),
                    "failure_category": failure_info["category"],
                    "duration": (time.time() - llm_start),
                    "failure_reason": error_snippet[:100],
                    "usage": fallback_usage or {
                        "total_tokens": len(answer) // 4,
                        "prompt_tokens": 0,
                        "completion_tokens": len(answer) // 4,
                    },
                    "confidence_score": float(fallback_usage.get("confidence", 0.35)),
                    "routing_confidence": 0.0,
                    "routing_rationale": f"Orchestrator error: {error_snippet[:50]}...",
                }
    
    # Calculate final timing
    total_time = (time.time() - start_time) * 1000
    timings["total_ms"] = total_time
    
    return {
        "answer": answer,
        "structured_content": _json_safe(structured_content),
        "actions": _json_safe(suggested_actions),
        "metadata": {
            "timings": _json_safe(timings),
            "context": _json_safe(context_hits),
            "degraded_mode": is_degraded,
            "failure_category": llm_metadata.get("failure_category") if isinstance(llm_metadata, dict) else None,
            "llm": _json_safe(llm_metadata),
            "orchestrator": {
                "used_fallback": response_metadata.get("used_fallback", False) if isinstance(response_metadata, dict) else False,
                "context_used": response_metadata.get("context_used", False) if isinstance(response_metadata, dict) else False,
            }
        },
        "correlation_id": correlation_id
    }


# Health endpoint already defined above as copilot_health()


__all__ = ["router"]
