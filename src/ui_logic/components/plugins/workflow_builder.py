"""
Kari Workflow Builder Logic
- Drag/drop automation, RPA, and workflow CRUD
"""

from typing import Dict, List
import streamlit as st
from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import (
    fetch_user_workflows,
    create_workflow,
    delete_workflow,
    update_workflow,
    fetch_audit_logs,
)

def get_workflows(user_ctx: Dict) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["user", "admin", "developer"]):
        raise PermissionError("Insufficient privileges to view workflows.")
    return fetch_user_workflows(user_ctx["user_id"])

def create_new_workflow(user_ctx: Dict, workflow: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to create workflow.")
    return create_workflow(user_ctx["user_id"], workflow)

def delete_existing_workflow(user_ctx: Dict, workflow_id: str) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to delete workflow.")
    return delete_workflow(user_ctx["user_id"], workflow_id)

def update_existing_workflow(user_ctx: Dict, workflow_id: str, updates: Dict) -> bool:
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges to update workflow.")
    return update_workflow(user_ctx["user_id"], workflow_id, updates)

def get_workflow_audit_trail(user_ctx: Dict, limit: int = 25):
    if not user_ctx or not require_roles(user_ctx, ["admin", "developer"]):
        raise PermissionError("Insufficient privileges for workflow audit.")
    return fetch_audit_logs(category="workflow", user_id=user_ctx["user_id"])[-limit:][::-1]

def render_workflow_builder(user_ctx: Dict) -> None:
    """Placeholder UI for workflow building."""
    
    st.subheader("Workflow Builder")
    st.info("Workflow builder under construction.")


__all__ = [
    "get_workflows",
    "create_new_workflow",
    "delete_existing_workflow",
    "update_existing_workflow",
    "get_workflow_audit_trail",
    "render_workflow_builder",
]
