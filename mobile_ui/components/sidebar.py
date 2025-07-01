import streamlit as st
from logic.model_registry import get_models, list_providers
from logic.config_manager import update_config, load_config, get_status

def render_sidebar():
    st.sidebar.title("\U0001F9ED Navigation")
    config = load_config()

    providers = list_providers()
    provider = st.sidebar.selectbox(
        "LLM Provider",
        providers,
        index=providers.index(config.get("provider", providers[0])) if providers else 0,
    )
    if provider != config.get("provider"):
        update_config(provider=provider)

    models = [m["name"] for m in get_models(provider)]
    model_default = config.get("model") if config.get("model") in models else models[0]
    model = st.sidebar.selectbox("Model", models, index=models.index(model_default))
    if model != config.get("model"):
        update_config(model=model)

    status = get_status()
    emoji = {"Ready": "🟢", "Pending Config": "🟡", "Invalid": "🔴"}.get(status, "❔")
    st.sidebar.markdown(f"**Status:** {emoji} {status}")
    return st.sidebar.radio("Go to", ["Home", "Settings", "Models", "Memory", "Diagnostics"])
