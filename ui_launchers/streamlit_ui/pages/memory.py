"""Streamlit launcher for :func:`ui_logic.pages.memory.memory_page`."""

from src.ui_logic.pages.memory import memory_page as _memory_page


def memory_page(user_ctx=None):
    """Wrapper that forwards to :func:`ui_logic.pages.memory.memory_page`."""
    _memory_page(user_ctx=user_ctx)
