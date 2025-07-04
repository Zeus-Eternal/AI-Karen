import json
import streamlit as st
from services import config_manager


def render() -> None:
    """Render dynamic settings editor."""
    st.title("Configuration")
    config = config_manager.load_config()

    new_entries = {}
    for key, value in config.items():
        new_entries[key] = st.text_input(key, str(value))

    new_key = st.text_input("New Setting Key")
    new_val = st.text_input("New Setting Value")
    if new_key:
        new_entries[new_key] = new_val

    if st.button("Save"):
        for k, v in new_entries.items():
            try:
                # try to parse JSON numbers/bools
                new_entries[k] = json.loads(v)
            except Exception:
                new_entries[k] = v
        config_manager.save_config(new_entries)
        st.success("Settings updated")

