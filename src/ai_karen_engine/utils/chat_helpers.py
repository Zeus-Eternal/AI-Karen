import re
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


def strip_internal_analysis_leakage(text: str) -> str:
    """Remove common model thought leakage or internal markers."""
    if not text:
        return ""

    # Remove common thought tags
    cleaned = re.sub(
        r"<(thought|analysis|internal|reasoning)>.*?</\1>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove unclosed thought tags
    cleaned = re.sub(
        r"<(thought|analysis|internal|reasoning)>.*$",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Remove "Analysis:" or "Internal:" prefixes if they start the response
    cleaned = re.sub(
        r"^(Analysis|Internal|Thought|Reasoning):\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return cleaned.strip()


def is_low_information_content(content: str) -> bool:
    """Check if the content is functionally empty or low value."""
    text = str(content or "").strip()
    if not text:
        return True
    if len(text) == 1 and not text.isalnum():
        return True
    # If it only consists of punctuation or whitespace
    punctuation_only_chars = set(".-_=`'\"!?,:;()[]{}|/\\ \n\t")
    if all(ch in punctuation_only_chars for ch in text):
        return True
    return False


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


def _extract_recent_history_lines(history: Any, limit: int = 6) -> List[str]:
    lines: List[str] = []
    if not isinstance(history, list):
        return lines
    for item in history[-limit:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if not role or not content:
            continue
        lines.append(f"{role.title()}: {content}")
    return lines


def _extract_fact_lines(items: Any, limit: int = 4) -> List[str]:
    lines: List[str] = []
    if not isinstance(items, list):
        return lines
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        lines.append(f"- {content}")
    return lines


def build_structured_context_sections(
    request_context: Dict[str, Any],
    integrated_context: Dict[str, Any],
) -> List[str]:
    """Build a list of structured context sections for the system prompt."""
    sections: List[str] = []

    user_fact_lines = _extract_fact_lines(request_context.get("user_facts"), limit=4)
    if user_fact_lines:
        sections.append("Known user facts:\n" + "\n".join(user_fact_lines))

    project_fact_lines = _extract_fact_lines(
        request_context.get("project_facts"), limit=4
    )
    if project_fact_lines:
        sections.append("Known project facts:\n" + "\n".join(project_fact_lines))

    episodic_lines = _extract_fact_lines(
        request_context.get("episodic_items"), limit=3
    )
    if episodic_lines:
        sections.append("Relevant episodic memory:\n" + "\n".join(episodic_lines))

    semantic_long_term_lines = _extract_fact_lines(
        request_context.get("semantic_long_term_items"), limit=3
    )
    if semantic_long_term_lines:
        sections.append(
            "Relevant long-term knowledge:\n" + "\n".join(semantic_long_term_lines)
        )

    recalled_item_lines = _extract_fact_lines(
        request_context.get("recalled_items"), limit=4
    )
    if recalled_item_lines:
        sections.append("Curated recalled context:\n" + "\n".join(recalled_item_lines))

    if isinstance(integrated_context, dict):
        memory_items = integrated_context.get("memories", [])
        if isinstance(memory_items, list) and memory_items:
            memory_lines = _extract_fact_lines(memory_items, limit=5)
            if memory_lines:
                sections.append("Relevant memory context:\n" + "\n".join(memory_lines))

        instruction_items = integrated_context.get("instructions", [])
        if isinstance(instruction_items, list) and instruction_items:
            instruction_lines = _extract_fact_lines(instruction_items, limit=5)
            if instruction_lines:
                sections.append("Active instructions:\n" + "\n".join(instruction_lines))

    return sections


def wants_long_form_markdown_article(
    current_user_message: str,
    recent_messages: Any,
) -> bool:
    """Detect if the user is asking for a long-form article/blog post."""
    text_parts: List[str] = [str(current_user_message or "").lower()]
    if isinstance(recent_messages, list):
        for item in recent_messages[-6:]:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip().lower()
            if role == "user" and content:
                text_parts.append(content)

    combined = "\n".join(text_parts)
    long_form_markers = (
        "full article",
        "write an article",
        "blog article",
        "blog post",
        "full post",
        "in-depth article",
        "technical write-up",
        "comprehensive guide",
    )
    return any(marker in combined for marker in long_form_markers)
