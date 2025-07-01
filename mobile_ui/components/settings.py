import streamlit as st
from logic.config_manager import load_config, save_config
from logic.model_registry import get_models


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


def render_settings():
    st.title("\u2699\ufe0f Kari Configuration")
    config = load_config()

    provider = st.selectbox("LLM Provider", PROVIDERS, index=PROVIDERS.index(config.get("provider", PROVIDERS[0])))
    models = [m["name"] for m in get_models(provider)]
    model_default = config.get("model") if config.get("model") in models else models[0]
    model = st.selectbox("Model", models, index=models.index(model_default))

    api_key = ""
    if provider != "Local (Ollama)":
        api_key = st.text_input(f"{provider} API Key", type="password", value=config.get("api_key", ""))

    st.subheader("Memory Settings")
    use_memory = st.checkbox("Enable Memory", value=config.get("use_memory", True))
    context_len = st.slider("Context Length", 50, 2048, value=config.get("context_length", 512))
    decay = st.slider("Memory Decay", 0.0, 1.0, value=config.get("decay", 0.1))

    persona = st.text_input("Persona", value=config.get("persona", "default"))

    if st.button("\U0001F4BE Save Configuration"):
        save_config({
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "use_memory": use_memory,
            "context_length": context_len,
            "decay": decay,
            "persona": persona,
        })
        st.success("Settings saved.")
