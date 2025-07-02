import streamlit as st
from logic.config_manager import load_config, save_config
from logic.model_registry import get_models, list_providers

LOCAL_PROVIDERS = {"local", "ollama_cpp"}


def render_settings():
    st.title("\u2699\ufe0f Kari Configuration")
    config = load_config()

    providers = list_providers()
    if any(m.get("provider") == "custom_provider" for m in get_models()):
        providers.append("custom_provider")
    provider = st.selectbox(
        "LLM Provider",
        providers,
        index=providers.index(config.get("provider", providers[0])) if providers else 0,
    )
    models = [
        m.get("alias", m.get("model_name"))
        for m in get_models()
        if m.get("provider") == provider
    ]
    model_default = config.get("model") if config.get("model") in models else models[0]
    model = st.selectbox("Model", models, index=models.index(model_default))

    api_key = ""
    if provider not in LOCAL_PROVIDERS:
        api_key = st.text_input(
            f"{provider} API Key",
            type="password",
            value=config.get("api_key", ""),
        )

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
