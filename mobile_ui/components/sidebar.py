import streamlit as st


def render_sidebar() -> str:
    st.sidebar.title("\U0001F464 Kari Mobile")
    st.sidebar.write("Welcome!")
    selection = st.sidebar.radio(
        "Navigation", ["Home", "Settings", "Models", "Memory", "Diagnostics"]
    )
    return selection
