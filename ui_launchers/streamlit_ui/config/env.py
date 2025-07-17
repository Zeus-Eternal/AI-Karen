"""Environment helpers for the Streamlit UI.

Expected environment variables
------------------------------
KARI_API_URL   : base URL for the backend API
KARI_UI_THEME  : selected UI theme name
ADVANCED_MODE  : enable experimental UI features when set to 'true'
"""

from __future__ import annotations

import os

# Common environment defaults
API_URL = os.getenv("KARI_API_URL", "http://localhost:8000")
UI_THEME = os.getenv("KARI_UI_THEME", "light")
ADVANCED_MODE = os.getenv("ADVANCED_MODE", "false").lower() == "true"


def get_bool(name: str, default: bool = False) -> bool:
    """Return an environment variable as boolean."""
    return os.getenv(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")


def get_int(name: str, default: int = 0) -> int:
    """Return an environment variable as integer."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


__all__ = ["API_URL", "UI_THEME", "ADVANCED_MODE", "get_bool", "get_int"]
