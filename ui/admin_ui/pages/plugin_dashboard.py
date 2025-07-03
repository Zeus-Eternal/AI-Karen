import asyncio
import streamlit as st
from ui.mobile_ui.utils import api_client


async def _get_all():
    return await api_client.get("/plugins/all")


async def _get_enabled():
    return await api_client.get("/plugins")


async def _toggle(intent: str, enable: bool):
    path = f"/plugins/{intent}/enable" if enable else f"/plugins/{intent}/disable"
    return await api_client.post(path)


def render() -> None:
    st.header("Plugin Dashboard")
    all_plugins = asyncio.run(_get_all()) or []
    enabled = set(asyncio.run(_get_enabled()) or [])
    for intent in all_plugins:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(intent)
        with col2:
            current = intent in enabled
            checked = st.checkbox("enabled", value=current, key=intent)
            if checked != current:
                asyncio.run(_toggle(intent, checked))
                st.experimental_rerun()

