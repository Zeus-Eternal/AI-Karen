"""
Kari Plugins Page
- Orchestrates: plugin manager, plugin store, workflow builder
"""

from ui_logic.components.plugins.plugin_manager import render_plugin_manager
from ui_logic.components.plugins.plugin_store import render_plugin_store
from ui_logic.components.plugins.workflow_builder import (
    render_workflow_builder,
)
import streamlit as st


def plugins_page(user_ctx=None):
    """Display plugin store, manager, and workflows in tabs."""
    store_tab, manager_tab, workflow_tab = st.tabs(
        ["Store", "Installed", "Workflows"]
    )
    with store_tab:
        render_plugin_store(user_ctx=user_ctx)
    with manager_tab:
        render_plugin_manager(user_ctx=user_ctx)
    with workflow_tab:
        render_workflow_builder(user_ctx=user_ctx)
