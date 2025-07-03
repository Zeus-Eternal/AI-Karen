import streamlit as st
import logging

from ai_karen_engine.integrations.llm_registry import registry as llm_registry

def _providers() -> list[str]:
    return list(llm_registry.list_models())

def select_provider():
    st.subheader("\U0001F9E0 LLM Provider")
    provider = st.selectbox("Choose a provider", _providers())
    logging.info("[provider_selector] Selected provider: %s", provider)
    return provider
