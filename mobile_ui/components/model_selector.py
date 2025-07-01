import streamlit as st
import logging

MODELS = {
    "Local (Ollama)": ["llama3.2:latest", "mistral", "gemma"],
    "OpenRouter": ["openrouter/gpt-4", "openrouter/mistral-7b"],
    "Groq": ["llama3-8b-8192", "mixtral-8x7b"],
    "Anthropic": ["claude-3-opus", "claude-3-haiku"],
    "Together": ["together/llama3", "together/mixtral"],
    "Custom": ["<Manual Entry>"],
}

def select_model(provider: str):
    options = MODELS.get(provider, [])
    model = st.selectbox("Select Model", options)
    logging.info("[ui_config] Model chosen: %s", model)
    return model
