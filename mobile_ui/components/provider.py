import streamlit as st
import logging

from src.integrations.llm_registry import registry as llm_registry


def _available_providers() -> list[str]:
    """Return provider names from the LLM registry."""
    return list(llm_registry.list_models())


def select_provider() -> str:
    """Return the chosen LLM provider from the sidebar."""
    st.subheader("\U0001F50C LLM Provider")
    providers = _available_providers()
    provider = st.selectbox("Choose a provider", providers)
    logging.info("[ui_config] Provider selected: %s", provider)
    return provider

