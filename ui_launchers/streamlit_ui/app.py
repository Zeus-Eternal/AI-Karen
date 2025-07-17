"""
Kari Streamlit UI Entrypoint
- No business logic
- Only UI layout, page router, session mgmt, and theme injection
"""

import importlib.resources
import streamlit as st
from helpers.session import get_user_context
from config.routing import PAGE_MAP

# Theme injection (uses streamlit's built-in/theming with CSS from the repo)
def inject_theme():
    """Inject the default theme CSS bundled with ``ui_logic``."""
    css_path = importlib.resources.files("ui_logic.themes").joinpath("light.css")
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

def main():
    inject_theme()
    st.sidebar.title("Kari AI")
    st.sidebar.markdown("---")
    user_ctx = get_user_context()
    # Page Routing
    page = st.sidebar.radio("Navigate", list(PAGE_MAP.keys()), index=0)
    st.sidebar.markdown("---")
    # Launch page
    PAGE_MAP[page](user_ctx=user_ctx)

if __name__ == "__main__":
    main()
