import streamlit as st
import asyncio
from utils import api_client

async def send_message(text: str, role: str = "user"):
    return await api_client.post("/chat", {"text": text, "role": role})

def render():
    st.header("Chat Interface")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # display history
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)

    user_input = st.chat_input("Message")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            placeholder = st.empty()
            data = asyncio.run(send_message(user_input))
            if data and not data.get("error"):
                response = data.get("response", "")
                st.session_state.chat_history.append(("assistant", response))
                placeholder.markdown(response)
            else:
                placeholder.error(data.get("error", "error"))
