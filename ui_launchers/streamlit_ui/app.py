"""
Kari Streamlit UI Entrypoint
- No business logic
- Only UI layout, page router, session mgmt, and theme injection
"""

import streamlit as st
from helpers.session import get_user_context
from config.routing import PAGE_MAP
from helpers.icons import ICONS
from ui_logic.themes.theme_manager import (
    apply_default_theme,
    render_theme_switcher,
)

def render_sidebar(page: str, user_ctx) -> str:
    """Render primary and secondary navigation sidebar."""
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

    choice = st.sidebar.radio(
        "Navigate",
        list(primary.keys()),
        index=list(primary.keys()).index(page) if page in primary else 0,
        format_func=label,
    )
    with st.sidebar.expander("More"):
        more = st.radio(
            "More",
            list(secondary.keys()),
            index=list(secondary.keys()).index(page) if page in secondary else 0,
            format_func=label,
            label_visibility="collapsed",
        )
        if more:
            choice = more

    st.sidebar.markdown("---")
    render_theme_switcher(user_ctx)
    return choice


def inject_theme(user_ctx):
    """Apply the current theme to the page."""
    apply_default_theme(user_ctx)


def main():
    user_ctx = get_user_context()
    inject_theme(user_ctx)

    current_page = st.experimental_get_query_params().get("page", ["Home"])[0]
    page = render_sidebar(current_page, user_ctx)
    st.experimental_set_query_params(page=page)

    PAGE_MAP[page](user_ctx=user_ctx)

if __name__ == "__main__":
    main()
