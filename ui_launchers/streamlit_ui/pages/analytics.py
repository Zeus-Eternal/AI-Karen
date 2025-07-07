"""Streamlit launcher for :func:`ui_logic.pages.analytics.analytics_page`."""

from ui_logic.pages.analytics import analytics_page as _analytics_page


def analytics_page(user_ctx=None):
    """Wrapper that forwards to :func:`ui_logic.pages.analytics.analytics_page`."""
    _analytics_page(user_ctx=user_ctx)
