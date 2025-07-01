import streamlit as st
import logging

from logic.model_registry import get_models

def select_model(provider: str):
    options = [m["name"] for m in get_models(provider)]
    model = st.selectbox("Select Model", options)
    logging.info("[ui_config] Model chosen: %s", model)
    return model
