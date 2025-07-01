import streamlit as st


def memory_config():
    st.subheader("\U0001F9E0 Memory Configuration")
    use_memory = st.toggle("Enable Memory (Redis + Milvus)")
    context_length = st.slider(
        "Context Memory Window (Tokens)", 128, 8192, 2048
    )
    decay_rate = st.slider("Memory Decay Rate \u03bb", 0.01, 1.0, 0.1)
    return use_memory, context_length, decay_rate
