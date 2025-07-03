import streamlit as st
import json
import os

SETTINGS_FILE = "config/secrets.json"


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_settings(data):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)


def settings_panel():
    st.sidebar.header("\u2699\ufe0f Settings")

    with st.sidebar.expander("User Credentials", expanded=True):
        user_name = st.text_input("Username", value=st.session_state.get("user_name", "zeus"))
        llm_api_key = st.text_input("LLM API Key", type="password")
        search_api_key = st.text_input("Search API Key", type="password")

    with st.sidebar.expander("Model Settings"):
        model = st.selectbox("Select Model", ["llama3", "mistral", "zephyr", "custom"])
        enable_dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
        enable_debug = st.toggle("Debug Mode", value=st.session_state.get("debug_mode", False))

    if st.sidebar.button("\ud83d\udcbe Save Settings"):
        settings_data = {
            "user_name": user_name,
            "llm_api_key": llm_api_key,
            "search_api_key": search_api_key,
            "model": model,
            "dark_mode": enable_dark_mode,
            "debug_mode": enable_debug,
        }
        st.session_state.update(settings_data)
        save_settings(settings_data)
        st.success("Settings saved!")

    if "user_name" not in st.session_state:
        st.session_state.update(load_settings())
