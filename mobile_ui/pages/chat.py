import streamlit as st

from components.chat import render_chat


def render_chat_page() -> None:
    """High-level chat page using reusable chat component."""
    st.markdown("## :speech_balloon: Chat")
    render_chat()


if __name__ == "__main__":
    render_chat_page()

