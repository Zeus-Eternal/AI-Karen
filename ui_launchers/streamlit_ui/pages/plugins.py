"""Streamlit launcher for :func:`ui_logic.pages.plugins.plugins_page`."""

from src.ui_logic.pages.plugins import plugins_page as _plugins_page


def plugins_page(user_ctx=None):
    """Wrapper that forwards to :func:`ui_logic.pages.plugins.plugins_page`."""
    _plugins_page(user_ctx=user_ctx)
