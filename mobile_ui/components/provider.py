import streamlit as st
import logging

PROVIDERS = [
    "Local (Ollama)",
    "OpenAI",
    "Anthropic",
    "Gemini",
    "Groq",
    "HuggingFace",
    "Cohere",
    "OpenRouter",
    "Together",
    "Custom",
]


def select_provider() -> str:
    """Return the chosen LLM provider from the sidebar."""
    st.subheader("\U0001F50C LLM Provider")
    provider = st.selectbox("Choose a provider", PROVIDERS)
    logging.info("[ui_config] Provider selected: %s", provider)
    return provider

