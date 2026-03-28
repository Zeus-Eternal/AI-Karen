from __future__ import annotations

import re
from typing import Any, Dict, Optional


_RECENT_NAME_PATTERNS = [
    r"\bmy name is\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
    r"\bi am\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
    r"\bcall me\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
    r"\bthe name is\s+([A-Za-z][A-Za-z0-9_\- ]{0,40})",
]

_IDENTITY_QUERY_PATTERNS = (
    "what's my name",
    "whats my name",
    "what is my name",
    "do you know my name",
    "you should have my name",
    "you should know my name",
    "tell me my name",
    "who am i",
    "who i am",
)


def _extract_candidate(container: Any, key: str) -> Optional[str]:
    if container is None:
        return None

    if isinstance(container, dict):
        value = container.get(key)
    else:
        value = getattr(container, key, None)

    return value if isinstance(value, str) else None


def _normalize_display_name(candidate: Optional[str]) -> Optional[str]:
    if not candidate:
        return None

    cleaned = candidate.strip()
    if not cleaned:
        return None

    if "@" in cleaned:
        cleaned = cleaned.split("@", 1)[0].strip()

    return cleaned or None


def extract_recent_name(request_context: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(request_context, dict):
        return None

    recent_messages = request_context.get("recent_messages", [])
    if not isinstance(recent_messages, list):
        return None

    for item in reversed(recent_messages):
        if not isinstance(item, dict) or item.get("role") != "user":
            continue

        content = str(item.get("content", "")).strip()
        if not content:
            continue

        for pattern in _RECENT_NAME_PATTERNS:
            match = re.search(pattern, content, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" .,!?:;")
                if candidate:
                    return candidate

    return None


def is_identity_lookup(user_message: str) -> bool:
    normalized = " ".join(user_message.lower().split())
    return any(pattern in normalized for pattern in _IDENTITY_QUERY_PATTERNS)


async def resolve_display_name(
    *,
    auth_service: Optional[Any] = None,
    user_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None,
    request_context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    request_context = request_context if isinstance(request_context, dict) else {}
    authenticated_user = request_context.get("authenticated_user", {})
    conversation_profile = request_context.get("conversation_profile", {})
    authenticated_preferences = (
        authenticated_user.get("preferences", {})
        if isinstance(authenticated_user, dict)
        else getattr(authenticated_user, "preferences", {}) or {}
    )
    user_preferences = (
        user_context.get("preferences", {})
        if isinstance(user_context, dict)
        else getattr(user_context, "preferences", {}) or {}
    )

    for candidate in (
        _extract_candidate(conversation_profile, "preferred_address_name"),
        _extract_candidate(conversation_profile, "display_name"),
        _extract_candidate(authenticated_preferences, "preferred_address_name"),
        _extract_candidate(authenticated_user, "full_name"),
        _extract_candidate(authenticated_user, "email"),
        _extract_candidate(user_preferences, "preferred_address_name"),
        _extract_candidate(user_context, "full_name"),
        _extract_candidate(user_context, "email"),
    ):
        normalized = _normalize_display_name(candidate)
        if normalized:
            return normalized

    if auth_service and user_id:
        try:
            user_info = await auth_service.get_user(user_id)
            user_info_preferences = (
                user_info.get("preferences", {})
                if isinstance(user_info, dict)
                else getattr(user_info, "preferences", {}) or {}
            )
            for candidate in (
                _extract_candidate(user_info_preferences, "preferred_address_name"),
                _extract_candidate(user_info, "full_name"),
                _extract_candidate(user_info, "email"),
            ):
                normalized = _normalize_display_name(candidate)
                if normalized:
                    return normalized
        except Exception:
            pass

    if user_id == "frontend_user":
        return "Zeus"

    return None


def build_user_identity_line(display_name: str) -> str:
    return (
        f"User Identity: You are speaking to {display_name}. "
        f"Address the user as {display_name} when greeting them or referring to them directly."
    )
