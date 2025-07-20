"""Centralized icon definitions for the Streamlit UI."""

ICONS = {
    "chat": "💬",
    "memory": "🧠",
    "analytics": "📊",
    "plugins": "🧩",
    "presence": "👥",
    "iot": "📡",
    "task_manager": "✅",
    "admin": "🛡️",
    "settings": "⚙️",
}


def get_icon(name: str) -> str:
    """Return icon string for given name."""
    return ICONS.get(name, "")

__all__ = ["ICONS", "get_icon"]
