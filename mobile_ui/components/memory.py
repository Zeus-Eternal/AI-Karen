import streamlit as st


def memory_config():
    st.subheader("\U0001F9E0 Memory Configuration")
    use_memory = st.checkbox("Enable Memory", value=True)
    context_len = st.slider("Context Length", 50, 2048, 512)
    decay = st.slider("Memory Decay Rate", 0.0, 1.0, 0.1)
    return use_memory, context_len, decay


def render_memory():
    st.title("\U0001F4E6 Memory Settings")
    memory_config()

