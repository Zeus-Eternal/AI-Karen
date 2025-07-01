import streamlit as st
import logging

def select_provider():
    st.subheader("\U0001F9E0 LLM Provider")
    provider = st.selectbox(
        "Choose a provider",
        [
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
        ],
    )
    logging.info("[ui_config] User selected provider: %s", provider)
    return provider
