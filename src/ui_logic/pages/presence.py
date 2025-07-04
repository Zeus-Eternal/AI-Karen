"""Presence page logic."""

from typing import Dict

from ui_logic.components.presence import get_active_sessions, get_system_status


def get_live_sessions(user_ctx: Dict) -> Dict[str, list]:
    """Return live session data if user has appropriate role."""
    if "admin" not in user_ctx.get("roles", []):
        raise PermissionError("Unauthorized.")
    return {
        "sessions": get_active_sessions(),
        "status": get_system_status(),
    }
