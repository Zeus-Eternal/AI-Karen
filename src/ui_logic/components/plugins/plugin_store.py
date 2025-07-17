"""
Kari Plugin Store Logic
- Curated plugin listing, search, and marketplace ops
"""

from typing import Dict, List
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_store_plugins,
    search_plugins,
    fetch_audit_logs,
)

import streamlit as st

def list_store_plugins(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "developer"]):
        raise PermissionError("Insufficient privileges to access plugin store.")
    return fetch_store_plugins()

def search_plugin_marketplace(user_ctx: Dict, query: str) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "developer"]):
        raise PermissionError("Insufficient privileges to search plugin marketplace.")
    return search_plugins(query)

def get_plugin_store_audit(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges for plugin store audit.")
    return fetch_audit_logs(category="plugin_store", user_id=user_ctx["user_id"])[-limit:][::-1]


def render_plugin_store(user_ctx: Dict):
    """Placeholder UI for plugin marketplace."""
    st.subheader("Plugin Store")
    st.info("Plugin store not available.")


__all__ = [
    "list_store_plugins",
    "search_plugin_marketplace",
    "get_plugin_store_audit",
    "render_plugin_store",
]
