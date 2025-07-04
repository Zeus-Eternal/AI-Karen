"""Streamlit wrapper for the presence page."""

from ui_logic.pages.presence import get_live_sessions


def presence_page(user_ctx=None):
    data = get_live_sessions(user_ctx or {})
    # In a real UI we would build tables/graphs here
    import streamlit as st

    st.header("Live Sessions")
    st.write(data)
