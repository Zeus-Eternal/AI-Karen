import streamlit as st
from logic.health_checker import get_system_health


def render_diagnostics() -> None:
    """Display runtime diagnostics in the UI."""
    st.title("\U0001F9EA Diagnostics")
    health = get_system_health()

    st.subheader("Runtime")
    st.json(health.get("runtime"))

    st.subheader("Memory")
    st.json(health.get("memory"))

    st.subheader("LLM Backends")
    st.json(health.get("llm_backends"))

    st.subheader("Packages")
    st.json(health.get("packages"))

    st.subheader("spaCy Models")
    st.write(", ".join(health.get("spacy_models", [])))

