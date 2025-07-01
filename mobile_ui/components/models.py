import streamlit as st
import pandas as pd
from logic.model_registry import MODEL_REGISTRY, get_models


def select_model(provider: str):
    st.subheader("\U0001F3AF Select Model")
    models = [m["name"] for m in get_models(provider)]
    return st.selectbox("Model", models)


def render_models():
    st.title("\U0001F9E0 Model Catalog")
    provider = st.selectbox("Choose Provider", list(MODEL_REGISTRY.keys()))
    data = get_models(provider)
    if data:
        st.table(pd.DataFrame(data))

