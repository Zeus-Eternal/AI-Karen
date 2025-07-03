import streamlit as st
from ui.mobile_ui.services.health_checker import get_system_health


def render() -> None:
    """Display runtime diagnostics and health status."""
    st.title("Diagnostics")
    with st.spinner("Collecting data..."):
        data = get_system_health()
    st.json(data)

