"""
Kari Plugins Page
- Orchestrates: plugin manager, plugin store, workflow builder
"""

from src.ui_logic.components.plugins.plugin_manager import render_plugin_manager
from src.ui_logic.components.plugins.plugin_store import render_plugin_store
from src.ui_logic.components.plugins.workflow_builder import \
    render_workflow_builder


def plugins_page(user_ctx=None):
    render_plugin_store(user_ctx=user_ctx)
    render_plugin_manager(user_ctx=user_ctx)
    render_workflow_builder(user_ctx=user_ctx)
