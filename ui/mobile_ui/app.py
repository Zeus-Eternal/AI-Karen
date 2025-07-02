#!/usr/bin/env python3
import sys
import pathlib

# ==== PATH PATCHING FOR IMPORTS ====
CURRENT_FILE = pathlib.Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]  # AI-Karen root
SRC_PATH = PROJECT_ROOT / "src"
MOBILE_UI_PATH = PROJECT_ROOT / "ui" / "mobile_ui"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

if str(MOBILE_UI_PATH) not in sys.path:
    sys.path.insert(0, str(MOBILE_UI_PATH))

# ========== STANDARD IMPORTS ==========
import streamlit as st
from components.sidebar import render_sidebar
from components.provider_selector import select_provider
from config.config_manager import ConfigManager
from utils.model_loader import ensure_spacy_models, ensure_sklearn_installed

# ========== STYLING ==========
def load_styles():
    try:
        with open("styles/styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
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
