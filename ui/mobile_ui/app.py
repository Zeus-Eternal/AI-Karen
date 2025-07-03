#!/usr/bin/env python3
import pathlib

# "src" is now a proper package location; no path patching needed.

# ========== STANDARD IMPORTS ==========
import streamlit as st
from mobile_components.sidebar import render_sidebar
from mobile_components.provider_selector import select_provider
from config.config_manager import ConfigManager
from utils.model_loader import ensure_spacy_models, ensure_sklearn_installed

# ========== STYLING ==========
def load_styles():
    css_path = pathlib.Path(__file__).parent / "styles" / "styles.css"
    try:
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            return
    except Exception:
        pass

    fallback_css = ".stButton>button { border-radius: 8px; border: 1px solid #4CAF50; }"
    st.markdown(f"<style>{fallback_css}</style>", unsafe_allow_html=True)

# ========== MAIN ==========
def main():
    config = ConfigManager()
    st.set_page_config(page_title=f"{config.app_name} Mobile UI", layout="centered")
    load_styles()

    with st.spinner("🔍 Checking dependencies..."):
        ensure_spacy_models()
        ensure_sklearn_installed()

    selection = render_sidebar()
    if selection == "Chat":
        import pages.chat as chat_page
        chat_page.render_chat()
    elif selection == "Settings":
        import pages.settings as settings_page
        settings_page.render_settings()
    else:
        st.error(f"Unknown page: {selection}")

if __name__ == "__main__":
    main()
