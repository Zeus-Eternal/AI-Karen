import streamlit as st
from core.soft_reasoning_engine import SoftReasoningEngine

engine = SoftReasoningEngine()

st.title("Memory Matrix")

query = st.text_input("Query text")
if query:
    results = engine.query(query)
    st.write(results)
