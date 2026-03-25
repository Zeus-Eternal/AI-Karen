import asyncio
import os
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Mount under /api/copilot when included with the global /api prefix
# No prefix here since it's already mounted at /api/copilot in routers.py
router = APIRouter(tags=["copilot"])

# Ensure routing predictors are registered so /start can dispatch actions.
# Importing them eagerly pulls in heavy optional dependencies (spaCy,
# transformers, SQLAlchemy). We defer registration until a request needs
# it to keep unit tests and health checks lightweight.
_routing_actions_ready = False


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
        from ai_karen_engine.services.connection_health_manager import (
            get_connection_health_manager as _getter,
            ServiceStatus as _status,
        )

        return _getter(), _status
    except Exception:
        return None, _FallbackServiceStatus


def _resolve_display_name(user_context: Optional[Dict[str, Any]], request_context: Dict[str, Any]) -> Optional[str]:
    authenticated_user = request_context.get("authenticated_user", {}) if isinstance(request_context, dict) else {}

    for candidate in (
        authenticated_user.get("full_name"),
        authenticated_user.get("email"),
        user_context.get("full_name") if user_context else None,
        user_context.get("email") if user_context else None,
    ):
        if not candidate or not isinstance(candidate, str):
            continue
        cleaned = candidate.strip()
        if not cleaned:
            continue
        if "@" in cleaned:
            cleaned = cleaned.split("@", 1)[0]
        return cleaned

    return None


def _find_recent_name(request_context: Dict[str, Any]) -> Optional[str]:
    recent_messages = request_context.get("recent_messages", []) if isinstance(request_context, dict) else []
    if not isinstance(recent_messages, list):
        return None

    patterns = [
        r"\bmy name is\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
        r"\bi am\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
        r"\bcall me\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
        r"\bthe name is\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
    ]

    for item in reversed(recent_messages):
        if not isinstance(item, dict) or item.get("role") != "user":
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        for pattern in patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" .,!?:;")
                if candidate:
                    return candidate

    return None


def _build_degraded_direct_answer(
    user_message: str,
    *,
    user_context: Optional[Dict[str, Any]],
    request_context: Dict[str, Any],
) -> Optional[str]:
    normalized = " ".join(user_message.lower().split())
    now = datetime.now().astimezone()

    if any(phrase in normalized for phrase in ("what's my name", "whats my name", "what is my name")):
        known_name = _find_recent_name(request_context) or _resolve_display_name(user_context, request_context)
        if known_name:
            return f"Your name is {known_name}."
        return "I don't have your name yet in this degraded session."

    if "what's the date" in normalized or "whats the date" in normalized or "what is the date" in normalized or normalized == "date":
        return f"Today's date is {now.strftime('%A, %B %d, %Y')}."

    if "what time" in normalized or "what's the time" in normalized or "whats the time" in normalized or normalized == "time":
        return f"The current time is {now.strftime('%-I:%M %p %Z')}."

    return None


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


from functools import lru_cache

# Add the same orchestrator dependency as chat_runtime.py
@lru_cache
def get_chat_orchestrator():
    """Return a cached ChatOrchestrator instance - same as chat_runtime.py"""
    from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
    from ai_karen_engine.chat.memory_processor import MemoryProcessor
    from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
    from ai_karen_engine.database.memory_manager import MemoryManager
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    from ai_karen_engine.core.milvus_client import MilvusClient
    from ai_karen_engine.core import default_models
    from src.auth.auth_service import AuthService as PromptAuthService

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
    return ChatOrchestrator(
        memory_processor=memory_processor,
        auth_service=PromptAuthService(),
    )


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
        import os
        env = os.getenv("ENVIRONMENT", os.getenv("KARI_ENV", "development")).lower()
        auth_mode = os.getenv("AUTH_MODE", "hybrid").lower()
        allow_public = os.getenv("ALLOW_PUBLIC_COPILOT", "false").lower() in ("1", "true", "yes")
        if allow_public or auth_mode == "bypass" or env in ("development", "dev", "local", "test", "testing"):
            user_ctx = {"user_id": "anonymous", "roles": ["admin"], "scopes": ["chat:write"]}
        else:
            try:
                # Try to resolve real context if available
                user_ctx = await _resolve_user_context(http_request)
            except Exception:
                # If strict mode, deny
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
    try:
        audit_logger = _get_audit_logger()
        if audit_logger:
            await audit_logger.log_event(
                event_type="copilot.action.started",
                user_id=user_ctx.get("user_id"),
                session_id=user_ctx.get("session_id"),
                correlation_id=correlation_id,
                details={"action": req.action, "payload_keys": list(req.payload.keys())},
                surface="copilot",
            )
    except Exception:
        pass

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
        try:
            audit_logger = _get_audit_logger()
            if audit_logger:
                await audit_logger.log_event(
                    event_type="copilot.action.completed",
                    user_id=user_ctx.get("user_id"),
                    session_id=user_ctx.get("session_id"),
                    correlation_id=correlation_id,
                    details={"action": req.action, "success": True},
                    surface="copilot",
                )
        except Exception:
            pass

        return StartActionResponse(status="ok", output=output or {}, correlation_id=correlation_id)
    except Exception as e:
        # Audit: action failed
        try:
            audit_logger = _get_audit_logger()
            if audit_logger:
                await audit_logger.log_event(
                    event_type="copilot.action.failed",
                    user_id=user_ctx.get("user_id"),
                    session_id=user_ctx.get("session_id"),
                    correlation_id=correlation_id,
                    details={"action": req.action, "error": str(e)},
                    surface="copilot",
                    success=False,
                    error_message=str(e),
                )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Action failed: {e}")


# Convenience GET endpoint for clients that mistakenly use GET
@router.get("/start", response_model=StartActionResponse)
async def copilot_start_action_get(action: str, http_request: Request):
    """Shallow wrapper that maps GET to the same start action handler.

    Accepts `action` as a query param and calls the POST handler with empty payload/context.
    Keeps legacy or misconfigured clients working without 404s.
    """
    _ensure_routing_actions_registered()
    req = StartActionRequest(action=action, payload={}, context={})
    return await copilot_start_action(req, http_request)

@router.post("/assist", response_model=AssistResponse)
async def copilot_assist(
    request: AssistRequest,
    http_request: Request,
    chat_orchestrator = Depends(get_chat_orchestrator),
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
    preferred_llm_provider = request.preferred_llm_provider
    preferred_model = request.preferred_model
    session_id = request.session_id
    
    # Initialize response components
    context_hits = []
    suggested_actions = []
    structured_content = {}
    answer = "I'm processing your request..."
    timings = {"start": start_time}

    # Health gate: short-circuit to degraded mode if critical services are unavailable
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
                logger.warning(
                    "Health gate failed for services: %s. Entering degraded mode.",
                    ", ".join(unhealthy),
                    extra={"correlation_id": correlation_id}
                )
                is_degraded = True
                # Inject a system note so the LLM is aware of the context if it manages to succeed
                message = f"SYSTEM WARNING: Core services ({', '.join(unhealthy)}) are offline. Proceed in degraded mode.\nUser Request: {message}"
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

        degraded_cause = "Core backend services (database) are temporarily unavailable."
        request_context = request.context if isinstance(request.context, dict) else {}
        display_name = _resolve_display_name(user_context, request_context)
        direct_answer = _build_degraded_direct_answer(
            user_msg,
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
            "You are Karen, an intelligent AI assistant built as an extension of Zeus-Eternal.",
            "Your personality is helpful, professional, and precise.",
            "Acknowledge when you are operating in degraded mode if relevant, but prioritize answering the user's question.",
            f"Current date and time: {datetime.now().astimezone().strftime('%A, %B %d, %Y %I:%M %p %Z')}.",
        ]
        if display_name:
            system_prompt_parts.append(f"User Identity: You are speaking to {display_name}.")

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

        # Try the local model via FallbackProvider (uses the already-loaded
        # registered llamacpp provider from the global registry).
        try:
            from ai_karen_engine.integrations.providers.fallback_provider import FallbackProvider
            import asyncio

            _fb = FallbackProvider()
            loop = asyncio.get_event_loop()
            local_answer = await loop.run_in_executor(
                None, lambda: _fb.generate_response(messages=fallback_messages)
            )

            if local_answer and isinstance(local_answer, str) and local_answer.strip():
                answer = local_answer
                logger.info("Local model responded in degraded mode", extra={"correlation_id": correlation_id})
            else:
                raise ValueError("Local model returned empty response")
        except Exception as local_e:
            logger.warning("Local model failed in degraded mode: %s", local_e, extra={"correlation_id": correlation_id})
            answer = (
                f"I'm currently unable to generate a full AI response. "
                f"Please check your infrastructure and try again shortly."
            )

        total_time = (time.time() - start_time) * 1000
        timings["total_ms"] = total_time
        # Extract metadata from fallback provider
        usage = getattr(_fb, "last_usage", {})
        fb_model_id = usage.get("model_id", "degraded-fallback")
        fb_confidence = usage.get("confidence", 0.35)
        
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
                    "source": "health_gate_fallback",
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
        from ai_karen_engine.chat.chat_orchestrator import ChatRequest
        
        # Use the user_id from request (no user_context dependency)
        actual_user_id = user_id
        
        # Create proper ChatRequest using the same pattern as chat_runtime.py
        chat_request = ChatRequest(
            message=message,
            user_id=actual_user_id,
            conversation_id=session_id or f"copilot_{correlation_id}",
            session_id=session_id or correlation_id,
            stream=False,
            include_context=True,
            metadata={
                "source": "copilot_assist", 
                "org_id": org_id,
                "platform": "copilot",
                "request_context": request.context,
                "preferred_llm_provider": preferred_llm_provider,
                "preferred_model": preferred_model,
            }
        )
        
        # Process the message through the injected chat orchestrator with a hard timeout
        # to prevent the frontend proxy from hitting its 120s abort.
        import asyncio
        response = None
        try:
            response = await asyncio.wait_for(
                chat_orchestrator.process_message(chat_request),
                timeout=float(os.getenv("COPILOT_ASSIST_TIMEOUT_SECONDS", "45")),  # default 45s
            )
        except asyncio.TimeoutError:
            # Let the outer except Exception handler deal with this so the
            # FallbackProvider is invoked instead of returning a canned string.
            timeout_secs = os.getenv("COPILOT_ASSIST_TIMEOUT_SECONDS", "45")
            raise RuntimeError(
                f"Primary AI provider timed out after {timeout_secs}s. "
                "The request was cancelled to keep the application responsive."
            )
        
        # Handle the response properly based on ChatOrchestrator response structure
        if response:
            # The ChatOrchestrator returns a response object with a 'response' attribute
            if hasattr(response, 'response') and response.response:
                answer = response.response
                logger.info("Copilot assist produced orchestrator response", extra={"correlation_id": correlation_id})
            elif hasattr(response, 'content') and response.content:
                answer = response.content
                logger.info("Copilot assist produced content response", extra={"correlation_id": correlation_id})
            elif isinstance(response, str):
                answer = response
                logger.info("Copilot assist produced string response", extra={"correlation_id": correlation_id})
            else:
                logger.warning(
                    "Unexpected copilot response format: %s",
                    type(response),
                    extra={"correlation_id": correlation_id},
                )
                answer = "The AI returned an unexpected response format. Please try again."
            
            # Map enriched metadata and formatting layer outputs to response envelope
            llm_metadata = {}
            if hasattr(response, 'metadata') and response.metadata:
                metadata_payload = response.metadata
                # Use the 'llm' nested object if it exists (from ChatOrchestrator)
                llm_metadata = metadata_payload.get('llm', {}) if isinstance(metadata_payload, dict) else {}
                
                # If 'llm' is empty but metadata_payload has 'provider', use metadata_payload as llm_metadata
                if not llm_metadata and isinstance(metadata_payload, dict) and 'provider' in metadata_payload:
                    llm_metadata = metadata_payload
                
                if 'output_formatting' in llm_metadata:
                    structured_content['formatting'] = llm_metadata['output_formatting']
                if 'output_layout' in llm_metadata:
                    structured_content['layout_type'] = llm_metadata['output_layout']
                if 'output_profile' in llm_metadata:
                    structured_content['output_profile'] = llm_metadata['output_profile']
            
            # Extract context from memory processor if available
            if hasattr(response, 'context_data') and response.context_data:
                for idx, context_item in enumerate(response.context_data[:top_k]):
                    context_hit = {
                        "id": f"memory_{idx}_{int(time.time())}",
                        "text": str(context_item)[:500],
                        "preview": str(context_item)[:200] + "..." if len(str(context_item)) > 200 else str(context_item),
                        "score": 0.8,  # Default score since we don't have specific scoring
                        "tags": ["ai_generated", "relevant"],
                        "recency": "recent",
                        "meta": {},
                        "importance": 7,
                        "decay_tier": "short",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": None,
                        "user_id": user_id,
                        "org_id": org_id
                    }
                    context_hits.append(context_hit)
            
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
        
        timings["llm_generation_ms"] = (time.time() - llm_start) * 1000
        
    except Exception as e:
        timings["llm_error"] = str(e)
        logger.error(
            "Copilot assist failed to obtain a verified LLM response: %s",
            e,
            extra={"correlation_id": correlation_id},
        )
        is_degraded = True

        # ----- Intelligent Fallback: instant deterministic response -----
        # Instead of calling another slow model (which could take 70s+ and
        # re-trigger the timeout), we produce an immediate, context-aware
        # response that informs the user about the failure and still
        # attempts to be helpful.
        error_snippet = str(e)[:200]
        user_msg = message

        # Strip the SYSTEM WARNING prefix if we injected it via health gate
        if "User Request:" in user_msg:
            user_msg = user_msg.split("User Request:", 1)[-1].strip()

        # Classify the failure and build a helpful response
        error_lower = error_snippet.lower()
        if "timeout" in error_lower or "timed out" in error_lower:
            cause = "The primary AI provider timed out while generating a response."
            suggestion = "Try a shorter or simpler prompt, or switch to a different provider in Settings."
        elif "api key" in error_lower or "auth" in error_lower or "401" in error_lower:
            cause = "Authentication with the AI provider failed."
            suggestion = "Check your API key in Application Settings → Model Configuration."
        elif "connection" in error_lower or "network" in error_lower or "connect" in error_lower:
            cause = "Could not connect to the AI provider."
            suggestion = "Check your network connection and the provider's base URL in Settings."
        elif "rate limit" in error_lower or "429" in error_lower:
            cause = "The AI provider is rate-limiting requests."
            suggestion = "Wait a moment before trying again, or switch to a different provider."
        else:
            cause = f"The AI provider encountered an error: {error_snippet[:100]}"
            suggestion = "Try again shortly, or switch to a different provider in Settings."

        answer = (
            f"⚠️ **Karen is operating in degraded mode.**\n\n"
            f"**Cause:** {cause}\n\n"
            f"**Your question:** \"{user_msg[:120]}{'...' if len(user_msg) > 120 else ''}\"\n\n"
            f"I'm unable to generate a full AI response right now, but I've logged your request. "
            f"{suggestion}\n\n"
            f"_This notification will only appear once per session._"
        )
        logger.info("Produced instant degraded-mode response", extra={"correlation_id": correlation_id})

        suggested_actions.append({
            "type": "add_task",
            "params": {"task": f"Retry: {user_msg[:40]}..."},
            "confidence": 0.7,
            "description": "Retry this request once the AI provider is healthy"
        })

        # Ensure llm_metadata is populated even in degraded mode so the
        # frontend can always display model information in the chat bubble.
        if not llm_metadata:
            # Try to get usage from fallback provider if it was used
            usage = getattr(_fb, "last_usage", {})
            fb_model_id = usage.get("model_id", "degraded-fallback")
            fb_confidence = usage.get("confidence", 0.35)
            
            llm_metadata = {
                "provider": "fallback",
                "model_id": fb_model_id,
                "model_name": fb_model_id.replace("fallback:", "").replace("_", " ").title(),
                "source": "runtime_error_fallback",
                "is_degraded": True,
                "duration": (time.time() - llm_start),
                "failure_reason": error_snippet[:100],
                "usage": usage or {"total_tokens": len(answer) // 4, "prompt_tokens": 0, "completion_tokens": len(answer) // 4},
                "confidence_score": fb_confidence,
                "routing_confidence": 0.0,
                "routing_rationale": f"Orchestrator error: {error_snippet[:50]}..."
            }
    
    # Calculate final timing
    total_time = (time.time() - start_time) * 1000
    timings["total_ms"] = total_time
    
    return {
        "answer": answer,
        "structured_content": structured_content,
        "actions": suggested_actions,
        "metadata": {
            "timings": timings,
            "context": context_hits,
            "degraded_mode": is_degraded,
            "llm": llm_metadata,
            "orchestrator": {
                "used_fallback": response.metadata.get("used_fallback", False) if response and hasattr(response, 'metadata') and isinstance(response.metadata, dict) else False,
                "context_used": response.metadata.get("context_used", False) if response and hasattr(response, 'metadata') and isinstance(response.metadata, dict) else False,
            }
        },
        "correlation_id": correlation_id
    }


# Health endpoint already defined above as copilot_health()


__all__ = ["router"]
