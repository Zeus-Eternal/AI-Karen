"""
Kari Streamlit UI Entrypoint
- No business logic
- Only UI layout, page router, session mgmt, and theme injection
"""

import streamlit as st
from helpers.session import get_user_context
from config.routing import PAGE_MAP

# Theme injection (uses streamlit's built-in/theming with CSS from the repo)
def inject_theme():
    from pathlib import Path
    # Resolve theme path relative to repo root to avoid missing file issues
    theme_css = Path(__file__).resolve().parents[2] / "src" / "ui_logic" / "themes" / "light.css"
    st.markdown(f"<style>{theme_css.read_text()}</style>", unsafe_allow_html=True)

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
