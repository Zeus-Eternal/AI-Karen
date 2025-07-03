import streamlit as st
import asyncio
from ui.mobile_ui.utils import api_client

async def fetch_tasks():
    return await api_client.get("/tasks")

async def trigger_task(task_id: str):
    return await api_client.post(f"/tasks/{task_id}/run")

def render():
    st.header("Task Dashboard")
    tasks = asyncio.run(fetch_tasks())

    if tasks and not tasks.get("error"):
        for t in tasks:
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"**{t.get('name','task')}** - {t.get('status','pending')}")
            with col2:
                if st.button("Run", key=f"run_{t.get('id')}"):
                    asyncio.run(trigger_task(t.get('id')))
                    st.toast("Task triggered")
    else:
        st.info("No tasks found")
