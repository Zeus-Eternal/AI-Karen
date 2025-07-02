import time
import streamlit as st

from logic.config_manager import load_config, update_config
from logic.model_registry import get_ready_models, get_model_meta
from logic.runtime_dispatcher import dispatch_runtime


def render_chat_page() -> None:
    st.markdown("## :speech_balloon: Chat")
    
    models = [m.get("model_name") for m in get_ready_models()]
    if not models:
        st.warning("No models available")
        return

    config = load_config()
    active_name = config.get("model", models[0])

    selected = st.selectbox(
        "Active Model",
        models,
        index=models.index(active_name) if active_name in models else 0,
    )
    if selected != active_name:
        update_config(model=selected)
        active_name = selected

    meta = get_model_meta(active_name)
    if not meta:
        st.error("Model metadata not found")
        return

    st.markdown(f"### \U0001f4ac Chat with `{meta.get('model_name', active_name)}`")

    user_input = st.chat_input("Type your message here...")
    if user_input:
        st.chat_message("user").write(user_input)
        start = time.perf_counter()
        with st.spinner("Thinking..."):
            response = dispatch_runtime(meta, user_input)
        duration = time.perf_counter() - start
        st.chat_message("ai").write(response)
        token_count = len(response.split())
        st.markdown("---")
        st.caption(
            f"Provider: {meta.get('provider')} | Runtime: {meta.get('runtime')} | "
            f"Tokens: {token_count} | Time: {duration:.2f}s"
        )


if __name__ == "__main__":
    render_chat_page()
