import psutil
import streamlit as st

st.title("Kari Dashboard")

cpu = psutil.cpu_percent(interval=0.1)
mem = psutil.virtual_memory().percent

st.metric("CPU %", cpu)
st.metric("Memory %", mem)
