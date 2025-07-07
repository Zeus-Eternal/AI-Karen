"""Streamlit launcher for :func:`ui_logic.pages.admin.admin_page`."""

from src.ui_logic.pages.admin import admin_page as _admin_page


def admin_page(user_ctx=None):
    """Wrapper that forwards to :func:`ui_logic.pages.admin.admin_page`."""
    _admin_page(user_ctx=user_ctx)
