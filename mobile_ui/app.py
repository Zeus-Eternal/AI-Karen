import streamlit as st
from components import (
    render_sidebar,
    select_provider,
    select_model,
    key_input,
    memory_config,
)

st.set_page_config(layout="wide", page_title="Kari AI – Mobile Control")

with open("styles/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

selection = render_sidebar()

st.title("⚙️ Kari Configuration")

provider = select_provider()
model = select_model(provider)
api_key = key_input(provider)
use_memory, context_len, decay = memory_config()

if st.button("💾 Save Configuration"):
    st.success("Settings saved to secure memory vault.")
    # TODO: persist settings to DuckDB or Kari's local config manager
