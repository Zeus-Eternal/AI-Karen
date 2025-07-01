import streamlit as st
from logic.memory_controller import sync_memory, flush_memory

def memory_config():
    st.subheader("\U0001F9E0 Memory Configuration")
    use_memory = st.checkbox("Enable Memory", value=True)
    context_len = st.slider("Context Length", 50, 2048, 512)
    decay = st.slider("Memory Decay Rate", 0.0, 1.0, 0.1)
    return use_memory, context_len, decay


def render_memory():
    st.title("\U0001F4E6 Memory Settings")
    
    short_term = st.checkbox("Short-Term", value=True)
    long_term = st.checkbox("Long-Term", value=False)
    persistent = st.checkbox("Persistent", value=True)

    st.progress(0.3, text="Redis")
    st.progress(0.5, text="DuckDB")
    st.progress(0.1, text="Milvus")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("\u27f3 Sync"):
            sync_memory()
            st.success("Synced")
    with col2:
        if st.button("\U0001F5D1 Flush"):
            flush_memory()
            st.warning("Flushed")
            
    memory_config()

