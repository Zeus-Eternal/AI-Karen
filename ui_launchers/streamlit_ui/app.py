"""Kari Streamlit UI Entrypoint."""

import streamlit as st
from ui_launchers.streamlit_ui.helpers.session import get_user_context
from ui_launchers.streamlit_ui.config.routing import PAGE_MAP
from ui_launchers.streamlit_ui.helpers.icons import ICONS
from ui_logic.themes.theme_manager import (
    apply_default_theme,
    render_theme_switcher,
)

def render_sidebar(user_ctx) -> None:
    """Primary and secondary navigation sidebar."""
    st.sidebar.title("Navigation")

    primary = ["Home", "Chat", "Settings"]
    secondary = ["Plugins", "Analytics", "Automation", "Admin"]

    for p in primary:
        if st.sidebar.button(p):
            st.session_state["page"] = p

    with st.sidebar.expander("More"):
        for p in secondary:
            if st.sidebar.button(p):
                st.session_state["page"] = p

    st.sidebar.markdown("---")
    render_theme_switcher(user_ctx)


def inject_theme(user_ctx):
    """Apply the current theme to the page."""
    apply_default_theme(user_ctx)


def main():
    user_ctx = get_user_context()
    inject_theme(user_ctx)
    page = st.experimental_get_query_params().get("page", ["Home"])[0]
    page = st.session_state.get("page", page)
    render_sidebar(user_ctx)
    st.experimental_set_query_params(page=st.session_state.get("page", page))
    page = st.session_state.get("page", page)
    PAGE_MAP.get(page, PAGE_MAP["Home"])(user_ctx=user_ctx)

if __name__ == "__main__":
    main()
