import streamlit as st

MODEL_OPTIONS = {
    "Local (Ollama)": ["llama3.2:latest", "mistral", "codellama"],
    "HuggingFace": ["gpt2", "bloom", "falcon-7b"],
    "Groq": ["llama3-70b", "mixtral-8x7b"],
}


def select_model(provider: str):
    st.subheader("\U0001F3AF Select Model")
    return st.selectbox("Model", MODEL_OPTIONS.get(provider, []))


def render_models():
    st.title("\U0001F9E0 Model Settings")
    provider = st.selectbox("Choose Provider", list(MODEL_OPTIONS.keys()))
    select_model(provider)

