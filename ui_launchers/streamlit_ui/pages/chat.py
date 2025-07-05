"""Streamlit launcher for :func:`ui_logic.pages.chat.chat_page`."""

from ui_logic.pages.chat import chat_page as _chat_page


def chat_page(user_ctx=None):
    """Wrapper that forwards to :func:`ui_logic.pages.chat.chat_page`."""
    _chat_page(user_ctx=user_ctx)
