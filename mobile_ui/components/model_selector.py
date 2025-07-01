import streamlit as st
import logging

MODELS = {
    "Local (Ollama)": ["llama3.2:latest", "mistral", "gemma"],
    "OpenAI": ["gpt-4o", "gpt-3.5-turbo"],
    "Anthropic": ["claude-3-opus", "claude-3-haiku"],
    "Gemini": ["gemini-pro", "gemini-pro-vision"],
    "Groq": ["llama3-8b-8192", "mixtral-8x7b"],
    "HuggingFace": ["gpt2", "bloom"],
    "Cohere": ["command-r", "command-r-plus"],
    "OpenRouter": ["openrouter/gpt-4", "openrouter/mistral-7b"],
    "Together": ["together/llama3", "together/mixtral"],
    "Custom": ["<Manual Entry>"],
}

def select_model(provider: str):
    options = MODELS.get(provider, [])
    model = st.selectbox("Select Model", options)
    logging.info("[ui_config] Model chosen: %s", model)
    return model
