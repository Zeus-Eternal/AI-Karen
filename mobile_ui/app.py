import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from sections import (
    chat_interface,
    task_dashboard,
    settings,
)

PAGES = {
    "🧠 Chat": chat_interface,
    "📆 Tasks": task_dashboard,
}

st.set_page_config(page_title="Kari Mobile UI", layout="wide")

settings.settings_panel()

st.sidebar.title("🧠 Kari Control Panel (Mobile)")
selection = st.sidebar.radio("📱 Navigate", list(PAGES.keys()))

PAGES[selection].render()
