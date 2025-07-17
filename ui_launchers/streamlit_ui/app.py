"""
Kari Streamlit UI Entrypoint
- No business logic
- Only UI layout, page router, session mgmt, and theme injection
"""

import streamlit as st
from helpers.session import get_user_context
from config.routing import DEFAULT_PAGE, PAGE_MAP
from helpers.icons import ICONS
from ui_logic.themes.theme_manager import (
    apply_default_theme,
    render_theme_switcher,
)


def render_sidebar(user_ctx) -> str:
    """Render navigation sidebar and return selected page."""
    st.sidebar.title("Kari AI")
    st.sidebar.markdown("---")

    primary = {
        "Chat": "chat",
        "Home": "home",
        "Memory": "memory",
        "Analytics": "analytics",
    }
    secondary = {
        "Plugins": "plugins",
        "Settings": "settings",
        "Admin": "admin",
    }

    def label(name):
        key = primary.get(name) or secondary.get(name)
        return f"{ICONS.get(key, '')} {name}"

    page = st.session_state.get("page", DEFAULT_PAGE)
    choice = st.sidebar.radio(
        "Navigate",
        list(primary.keys()),
        index=list(primary.values()).index(page) if page in primary.values() else 0,
        format_func=label,
    )
    with st.sidebar.expander("More"):
        more = st.radio(
            "More",
            list(secondary.keys()),
            index=list(secondary.values()).index(page) if page in secondary.values() else 0,
            format_func=label,
            label_visibility="collapsed",
        )
        if more:
            choice = more

    st.sidebar.markdown("---")
    render_theme_switcher(user_ctx)
    st.session_state["page"] = primary.get(choice) or secondary.get(choice)
    return st.session_state["page"]


def inject_theme(user_ctx):
    """Apply the current theme to the page."""
    apply_default_theme(user_ctx)


def main():
    user_ctx = get_user_context()
    inject_theme(user_ctx)

    page = render_sidebar(user_ctx)
    PAGE_MAP.get(page, PAGE_MAP[DEFAULT_PAGE])(user_ctx=user_ctx)


if __name__ == "__main__":
    main()
