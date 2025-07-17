"""Streamlit theme configuration helpers.

Environment variables
---------------------
KARI_UI_THEME : default theme name (light, dark, auto)
KARI_THEME_DIR : directory containing theme CSS files
"""

from __future__ import annotations

import os
from pathlib import Path

# Directory where theme CSS files reside
THEME_DIR = Path(os.getenv("KARI_THEME_DIR", Path(__file__).resolve().parents[2] / "src" / "ui_logic" / "themes"))

# Name of the theme to load by default
DEFAULT_THEME = os.getenv("KARI_UI_THEME", "light")


def load_theme(theme: str | None = None) -> str:
    """Return CSS contents for ``theme`` or the default theme."""
    theme_name = theme or DEFAULT_THEME
    css_path = THEME_DIR / f"{theme_name}.css"
    if not css_path.exists():
        css_path = THEME_DIR / f"{DEFAULT_THEME}.css"
    return css_path.read_text()


__all__ = ["THEME_DIR", "DEFAULT_THEME", "load_theme"]
