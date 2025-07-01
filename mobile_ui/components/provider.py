import streamlit as st


def select_provider():
    st.subheader("\U0001F50C LLM Provider")
    return st.selectbox("Choose a provider", ["Local (Ollama)", "HuggingFace", "Groq"])

