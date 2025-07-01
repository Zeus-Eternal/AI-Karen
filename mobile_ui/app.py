import sys
from pathlib import Path

# 🔥 Inject project root into sys.path to enable deep imports like src.*
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 🧠 Core UI framework
import streamlit as st

# 🧩 Modular UI panels
from components.sidebar import render_sidebar
from components.chat import render_chat
from components.settings import render_settings
from components.memory import render_memory
from components.models import render_models
from components.diagnostics import render_diagnostics
from utils.model_loader import ensure_spacy_models, ensure_sklearn_installed


def load_styles() -> None:
    """Inject custom CSS if available."""
    css_path = Path("styles/styles.css")
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ styles.css not found. Skipping custom UI styles.")


def dispatch_selection(selection: str) -> None:
    """Dispatch the current sidebar selection to the correct view."""
    try:
        if selection == "Home":
            render_chat()
        elif selection == "Settings":
            render_settings()
        elif selection == "Models":
            render_models()
        elif selection == "Memory":
            render_memory()
        elif selection == "Diagnostics":
            render_diagnostics()
        else:
            st.error(f"Unknown section: {selection}")
    except Exception as e:
        st.error(f"🔥 Failed to render view '{selection}': {e}")


def main() -> None:
    """Main entry point for Kari Mobile UI."""
    st.set_page_config(
        layout="wide",
        page_title="Kari AI – Mobile UI",
        page_icon="🤖",
        initial_sidebar_state="expanded",
    )

    # Ensure base NLP dependencies are available
    ensure_spacy_models()
    ensure_sklearn_installed()

    load_styles()
    selection = render_sidebar()
    dispatch_selection(selection)

    # 🔍 Boot diagnostics
    st.sidebar.caption(f"🧠 Root Path: `{ROOT}`")
    st.sidebar.caption("✅ System Initialized")


if __name__ == "__main__":
    print(f"[BOOT] Project root injected: {ROOT}")
    print(f"[BOOT] sys.path: {sys.path[:3]}")
    main()
