"""
Kari Streamlit UI Entrypoint
- No business logic
- Only UI layout, page router, session mgmt, and theme injection
"""

import streamlit as st
from helpers.session import get_user_context
from config.routing import PAGE_MAP
from ui_logic.themes.theme_manager import get_current_theme, load_theme_css

# Theme injection (uses streamlit's built-in/theming with CSS from the repo)
def inject_theme(user_ctx):
    """Inject the user's current theme CSS."""
    theme = get_current_theme(user_ctx)
    css = load_theme_css(theme)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def main():
    user_ctx = get_user_context()
    inject_theme(user_ctx)
    st.sidebar.title("Kari AI")
    st.sidebar.markdown("---")
    # Page Routing
    page = st.sidebar.radio("Navigate", list(PAGE_MAP.keys()), index=0)
    st.sidebar.markdown("---")
    # Launch page
    PAGE_MAP[page](user_ctx=user_ctx)

if __name__ == "__main__":
    main()
