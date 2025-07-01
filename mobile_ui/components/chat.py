import streamlit as st


def render_chat():
    st.title("\U0001F4AC Chat with Kari")
    user_input = st.chat_input("Type your message")
    if user_input:
        st.chat_message("user").write(user_input)
        # TODO: replace with real call to Kari’s brain
        st.chat_message("assistant").write("\u26A1 Response from Kari goes here.")

