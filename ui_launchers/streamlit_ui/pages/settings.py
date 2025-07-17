"""Settings Page - simplified with tabbed groups."""

import streamlit as st
from ui_logic.themes.theme_manager import render_theme_switcher


def render_settings():
    st.title("Settings")
    tabs = st.tabs(["Profile", "Theme", "Integrations", "Notifications"])
    with tabs[0]:
        st.header("User Profile")
        st.text_input("Display Name")
    with tabs[1]:
        st.header("Theme")
        render_theme_switcher(st.session_state.get("user_ctx", {}))
    with tabs[2]:
        st.header("Integrations")
        st.write("Configure your AI providers, webhooks, etc.")
    with tabs[3]:
        st.header("Notifications")
        st.write("Manage email & Slack alerts")


if __name__ == "__main__":
    render_settings()
