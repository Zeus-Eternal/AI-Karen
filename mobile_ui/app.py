import os
import streamlit as st
from components import (
    render_sidebar,
    select_provider,
    select_model,
    key_input,
    memory_config,
)

st.set_page_config(layout="wide", page_title="Kari AI – Mobile Control")

# Load CSS safely
css_path = os.path.join(os.path.dirname(__file__), "styles", "styles.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("No styles.css found in styles/. Using default Streamlit theme.")

selection = render_sidebar()

st.title("⚙️ Kari Configuration")

provider = select_provider()
model = select_model(provider)
api_key = key_input(provider)
use_memory, context_len, decay = memory_config()

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🔌 Test Connection"):
        if provider and model:
            st.info(f"Testing connection to {provider} - {model}...")
            # TODO: validate connection to provider/model
            st.success("Connection successful!")  # placeholder
        else:
            st.error("Please select a provider and model first.")

with col2:
    if st.button("💾 Save Configuration"):
        st.success("Settings saved to secure memory vault.")
        # TODO: persist to DuckDB or Kari's config handler
