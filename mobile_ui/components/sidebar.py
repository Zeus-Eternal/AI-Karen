import streamlit as st
from logic.model_registry import get_models, list_providers, ensure_model_downloaded
from logic.config_manager import update_config, load_config, get_status
import streamlit as st
import pandas as pd
from logic.model_registry import get_models, list_providers, ensure_model_downloaded


def select_model(provider: str):
    st.subheader("\U0001F3AF Select Model")
    models = [m["name"] for m in get_models(provider)]
    selected = st.selectbox("Model", models)
    if st.button("Ensure Model Ready"):
        ensure_model_downloaded(selected, provider)
        st.success(f"{selected} is ready to go.")
    return selected


def render_models():
    st.title("\U0001F9E0 Model Catalog")
    provider = st.selectbox("Choose Provider", list_providers())
    data = get_models(provider)
    if data:
        st.table(pd.DataFrame(data))

def render_sidebar():
    st.sidebar.title("⚙️ LLM Configuration")
    config = load_config()

    # Providers and initial selection
    providers = list_providers()
    current_provider = config.get("provider")
    if current_provider not in providers and providers:
        current_provider = providers[0]

    selected_provider = st.sidebar.selectbox(
        "LLM Provider",
        providers,
        index=providers.index(current_provider) if current_provider in providers else 0,
    )

    if selected_provider != config.get("provider"):
        update_config(provider=selected_provider)
        config["provider"] = selected_provider

    # Get models for selected provider
    models_list = get_models(selected_provider)
    model_names = [m["name"] for m in models_list]

    current_model = config.get("model")
    if current_model not in model_names and model_names:
        current_model = model_names[0]

    selected_model = st.sidebar.selectbox(
        "Model",
        model_names,
        index=model_names.index(current_model) if current_model in model_names else 0,
    )

    if selected_model != config.get("model"):
        update_config(model=selected_model)
        config["model"] = selected_model

    # Auto-download if Local (Ollama)
    if selected_provider.lower().startswith("local"):
        ensure_model_downloaded(selected_model)

    # Status display
    status = get_status()
    emoji = {"Ready": "🟢", "Pending Config": "🟡", "Invalid": "🔴"}.get(status, "❔")
    st.sidebar.markdown(f"**Status:** {emoji} {status}")

    # Navigation
    return st.sidebar.radio("🧭 Navigate", ["Chat", "Settings", "Models", "Memory", "Diagnostics"])
