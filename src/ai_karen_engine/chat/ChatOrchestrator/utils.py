import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def normalize_session_id(session_id: Optional[str]) -> str:
    """Return a UUID session id for downstream memory/orchestration services."""
    raw = str(session_id or "").strip()
    if not raw:
        return str(uuid.uuid4())

    candidates = [raw]
    if raw.startswith("chat_"):
        candidates.append(raw[len("chat_") :])

    for candidate in candidates:
        try:
            return str(uuid.UUID(candidate))
        except Exception:
            continue

    generated = str(uuid.uuid4())
    logger.warning(
        "Invalid session_id received; generated replacement.",
        extra={
            "provided_session_id": raw,
            "normalized_session_id": generated,
        },
    )
    return generated


def json_safe(value: Any) -> Any:
    """Convert response metadata into JSON-safe primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return str(value)


async def resolve_user_context(request: Any) -> Optional[Dict[str, Any]]:
    """Resolve user context from FastAPI request state or authenticated context."""
    # First check request state (set by middleware)
    try:
        if (
            hasattr(request, "state")
            and hasattr(request.state, "user")
            and request.state.user
        ):
            return request.state.user
    except AttributeError:
        pass

    # Best-effort fallback to dependency resolver
    try:
        from ai_karen_engine.core.dependencies import bypass_user_context_func

        return await bypass_user_context_func(request)
    except Exception:
        return None


def is_production_env() -> bool:
    """Check if the environment is production."""
    env = os.getenv("ENVIRONMENT", os.getenv("KARI_ENV", "development")).lower()
    return env in ("production", "prod")


async def resolve_display_name(
    auth_service: Any, user_id: str, request_context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """Resolve the display name for a given user ID."""
    if not user_id:
        return None

    # Fast path: Check context/request
    if request_context and isinstance(request_context, dict):
        if request_context.get("full_name"):
            return str(request_context["full_name"])
        if request_context.get("display_name"):
            return str(request_context["display_name"])

    # Try the auth service
    if auth_service and hasattr(auth_service, "get_user_display_name"):
        try:
            return await auth_service.get_user_display_name(user_id)
        except Exception:
            pass

    return None


def resolve_tenant_id(request_context: Optional[Dict[str, Any]] = None) -> str:
    """Resolve the tenant ID for a given request block."""
    if not request_context:
        return "default"

    tenant_id = (
        request_context.get("tenant_id") or request_context.get("org_id") or "default"
    )
    return str(tenant_id)


def build_user_identity_line(display_name: str) -> str:
    """Return a line to inject into the system prompt for user identity."""
    return f"The current user is: {display_name}."
