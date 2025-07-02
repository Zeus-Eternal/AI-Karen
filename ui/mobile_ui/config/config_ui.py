import streamlit as st
from services.model_registry import MODEL_PROVIDERS, get_models


def render_model_config():
    st.subheader("🧠 Model Configuration")

    # 1. Provider Selection
    provider_keys = list(MODEL_PROVIDERS.keys())
    selected_provider = st.selectbox("Select Model Provider", provider_keys)

    # 2. Load Available Models for Provider
    try:
        models = get_models(selected_provider)
    except Exception as e:
        st.error(f"🚨 Error loading models for provider '{selected_provider}': {str(e)}")
        models = []

    # 3. Handle string-based static model lists
    model_options = []
    if models and isinstance(models[0], str):
        model_options = models
        model_meta_list = [{"name": name} for name in models]
    elif models and isinstance(models[0], dict):
        model_options = [m["name"] for m in models]
        model_meta_list = models
    else:
        model_options = []
        model_meta_list = []

    # 4. Model Selection Dropdown
    selected_model = st.selectbox("Select Model", model_options)

    # 5. Retrieve Metadata for selected model (if any)
    model_metadata = next((m for m in model_meta_list if m.get("name") == selected_model), {})

    # 6. Save to Session State
    st.session_state["model_provider"] = selected_provider
    st.session_state["model_name"] = selected_model
    st.session_state["model_metadata"] = model_metadata

    # 7. Optional Debug View
    with st.expander("🔍 Model Metadata"):
        st.json(model_metadata)
