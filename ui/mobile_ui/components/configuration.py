import streamlit as st
from .provider import select_provider
from .models import select_model
from .memory import memory_config
from utils.api_client import persist_config


def render_configuration():
    st.title("\u2699\ufe0f Kari Configuration")
    provider = select_provider()
    model = select_model(provider)
    api_key = st.text_input(f"{provider} API Key", type="password")
    use_memory, context_len, decay = memory_config()

    if st.button("\U0001F4BE Save Configuration"):
        persist_config(
            {
                "provider": provider,
                "model": model,
                "api_key": api_key,
                "use_memory": use_memory,
                "context_length": context_len,
                "decay": decay,
            }
        )
        st.success("Settings saved.")

