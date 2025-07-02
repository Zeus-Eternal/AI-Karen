import streamlit as st
import pandas as pd
from logic.model_registry import get_ready_models, list_ready_providers


def select_model(provider: str):
    st.subheader("\U0001F3AF Select Model")
    models = [
        m.get("alias", m.get("model_name"))
        for m in get_ready_models()
        if m.get("provider") == provider
    ]
    return st.selectbox("Model", models)


def render_models():
    st.title("\U0001F9E0 Model Catalog")
    provider = st.selectbox("Choose Provider", list_ready_providers())
    data = [m for m in get_ready_models() if m.get("provider") == provider]
    if data:
        st.table(pd.DataFrame(data))
