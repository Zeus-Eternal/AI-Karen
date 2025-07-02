import streamlit as st
import logging

from logic.model_registry import get_models

def select_model(provider: str):
    options = [
        m.get("alias", m.get("model_name"))
        for m in get_models()
        if m.get("provider") == provider
    ]
    model = st.selectbox("Select Model", options)
    logging.info("[ui_config] Model chosen: %s", model)
    return model
