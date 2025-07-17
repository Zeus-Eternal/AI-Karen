"""Lightweight theme loader for the Streamlit UI."""
from __future__ import annotations

import importlib.resources
import os
from pathlib import Path

import streamlit as st

THEME_DIR = Path(__file__).resolve().parents[1] / "styles"


def load_css(theme: str = "light") -> str:
    """Return CSS for the requested theme or empty string if missing."""
    path = THEME_DIR / f"{theme}.css"
    if path.exists():
        return path.read_text()
    try:
        return (
            importlib.resources.files("ui_logic.themes")
            .joinpath(f"{theme}.css")
            .read_text()
        )
    except FileNotFoundError:
        return ""


def theme_exists(theme: str) -> bool:
    """Return ``True`` if a theme CSS file is available."""
    if (THEME_DIR / f"{theme}.css").exists():
        return True
    try:
        return (
            importlib.resources.files("ui_logic.themes")
            .joinpath(f"{theme}.css")
            .is_file()
        )
    except Exception:
        return False


def available_themes() -> list[str]:
    """Return a sorted list of available theme names."""
    names = {p.stem for p in THEME_DIR.glob("*.css")}
    try:
        pkg = importlib.resources.files("ui_logic.themes")
        names.update(p.stem for p in pkg.glob("*.css"))
    except FileNotFoundError:
        pass
    return sorted(names)


def get_default_theme() -> str:
    """Return the default theme set via ``KARI_UI_THEME`` or ``light``."""
    return os.getenv("KARI_UI_THEME", "light")


def apply_theme(theme: str = "light") -> None:
    """Inject theme CSS into the page if available."""
    css = load_css(theme)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def apply_default_theme() -> None:
    """Apply the theme configured via ``KARI_UI_THEME``."""
    apply_theme(get_default_theme())


__all__ = [
    "load_css",
    "apply_theme",
    "available_themes",
    "theme_exists",
    "get_default_theme",
    "apply_default_theme",
]
