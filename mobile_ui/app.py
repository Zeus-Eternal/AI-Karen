import streamlit as st
from components.sidebar import render_sidebar
from components.chat import render_chat
from components.settings import render_settings
from components.memory import render_memory
from components.models import render_models
from components.diagnostics import render_diagnostics


def load_styles() -> None:
    """Inject custom CSS if available."""
    try:
        with open("styles/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("styles.css not found. Skipping custom styles.")


def main() -> None:
    st.set_page_config(layout="wide", page_title="Kari AI – Mobile UI")
    load_styles()

    selection = render_sidebar()

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


if __name__ == "__main__":
    main()

