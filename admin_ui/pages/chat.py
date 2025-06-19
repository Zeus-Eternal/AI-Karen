import asyncio
import streamlit as st
from core.cortex.dispatch import CortexDispatcher

dispatcher = CortexDispatcher()

st.title("Kari Chat")

user_input = st.text_input("Say something:")
if user_input:
    result = asyncio.run(dispatcher.dispatch(user_input))
    st.write(result["response"])
