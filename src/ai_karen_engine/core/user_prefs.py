from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class UserPrefs:
    preferred_model: str = "ollama:llama3.2"
    show_degraded_banner: bool = False
    ui: Dict[str, Any] | None = None


def get_user_prefs() -> UserPrefs:
    """Return default user preferences.
    This is a simple placeholder until a real implementation is provided.
    """
    return UserPrefs(ui={"theme": "light"})
