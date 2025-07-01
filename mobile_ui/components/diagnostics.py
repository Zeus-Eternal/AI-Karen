import streamlit as st
from logic.health_checker import get_system_health

def render_diagnostics():
    st.title("\U0001F9EA Diagnostics")
    health = get_system_health()
    st.write(health)