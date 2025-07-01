import streamlit as st
import logging

from src.integrations.llm_registry import registry as llm_registry


def _providers() -> list[str]:
    """Return available provider names."""
    return list(llm_registry.list_models())

def select_provider():
    st.subheader("\U0001F9E0 LLM Provider")
    provider = st.selectbox("Choose a provider", _providers())
    logging.info("[ui_config] User selected provider: %s", provider)
    return provider
