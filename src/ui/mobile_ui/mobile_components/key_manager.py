import streamlit as st

LOCAL_PROVIDERS = {"local", "ollama_cpp"}


def key_input(provider: str):
    if provider in LOCAL_PROVIDERS:
        return None
    return st.text_input(
        f"Enter your API key for {provider}", type="password", key=f"{provider}_key"
    )
