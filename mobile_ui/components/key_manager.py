import streamlit as st


def key_input(provider: str):
    if provider == "Local (Ollama)":
        return None
    return st.text_input(
        f"Enter your API key for {provider}", type="password", key=f"{provider}_key"
    )
