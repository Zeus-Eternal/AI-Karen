import streamlit as st


def render_sidebar():
    st.sidebar.title("\U0001F9ED Navigation")
    return st.sidebar.radio("Go to", ["Home", "Settings", "Models", "Memory", "Diagnostics"])
