"""Streamlit placeholder for workflow builder page."""

from typing import Dict

import streamlit as st


def render_workflow_builder(user_ctx: Dict | None = None) -> None:
    """Display an informative message while the workflow UI is in development."""
    st.info("Workflow builder under construction.")


__all__ = ["render_workflow_builder"]
