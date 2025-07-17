"""Lightweight theme loader for the Streamlit UI."""
from __future__ import annotations

import importlib.resources
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


def apply_theme(theme: str = "light") -> None:
    """Inject theme CSS into the page if available."""
    css = load_css(theme)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


__all__ = ["load_css", "apply_theme"]
