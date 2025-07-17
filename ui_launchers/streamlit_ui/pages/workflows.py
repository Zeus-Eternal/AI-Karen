"""Streamlit placeholder for workflow builder page."""

import streamlit as st


def render_workflow_builder(user_ctx=None) -> None:
    """Display an informative message while the workflow UI is in development."""
    st.info(
        "The workflow builder UI is coming soon. "
        "You'll be able to design automations and RPA flows here."
    )


__all__ = ["render_workflow_builder"]
