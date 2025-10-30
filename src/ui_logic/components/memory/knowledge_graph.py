"""
Kari Knowledge Graph Panel Logic (Production)
- Visualizes relationships, facts, and concepts from the Neo4j-powered knowledge graph.
- RBAC: user, admin, analyst
- Auditable and query-driven.
"""

from typing import Any, Dict
import logging

import pandas as pd
import streamlit as st

from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_audit_logs

# Logger for permission denials and diagnostics
logger = logging.getLogger("kari.ui.knowledge_graph")


def get_user_ctx() -> Dict[str, Any]:
    """Return the authenticated user context for the knowledge graph."""

    user_id = st.session_state.get("user_id")
    roles = st.session_state.get("roles")

    if not user_id or not roles:
        logger.error("Knowledge graph requested without an authenticated session")
        raise PermissionError("You must be signed in to access the knowledge graph.")

    return {"user_id": user_id, "roles": roles}

def render_knowledge_graph_panel(user_ctx: Dict[str, Any]):
    st.subheader("🔗 Knowledge Graph Panel")
    # --- RBAC Enforcement ---
    try:
        require_roles(user_ctx, ["user", "admin", "analyst"])
    except PermissionError as e:
        st.error(str(e))
        return

    from ai_karen_engine.services.knowledge_graph_client import KnowledgeGraphClient
    kgc = KnowledgeGraphClient()

    # --- Query Controls ---
    st.markdown("**Graph Query Controls**")
    label = st.text_input("Node Label (e.g. Person, Concept)", value="Person")
    key = st.text_input("Node Property Key (optional)", value="name")
    value = st.text_input("Node Property Value (optional)", value="Zeus")

    rel_type = st.text_input("Relationship Type (optional)", value="")
    depth = st.slider("Traversal Depth", 1, 4, 2)

    if st.button("Find Related Concepts"):
        node_props = {key: value} if key and value else {}
        results = kgc.find_related_concepts(label, node_props, rel_type or None, depth)
        st.markdown(f"### Related Concepts to `{label}` [{value}]")
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No related concepts found.")

    if st.button("Show Concept Subgraph"):
        node_props = {key: value} if key and value else {}
        graph_paths = kgc.get_concept_graph(label, node_props, depth)
        st.markdown(f"### Subgraph (paths) for `{label}` [{value}]")
        st.write(graph_paths)

    # --- Audit Trail (admin/analyst only) ---
    try:
        require_roles(user_ctx, ["admin", "analyst"])
        if st.checkbox("Show Knowledge Graph Audit Trail"):
            audit = fetch_audit_logs(category="knowledge_graph", user_id=user_ctx["user_id"])
            if audit:
                df = pd.DataFrame(audit)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent audit logs.")
    except PermissionError as err:
        logger.info("Audit trail access denied: %s", err)
        st.info("You do not have permission to view audit logs.")

    # --- Health Status ---
    st.markdown("---")
    st.write("**Knowledge Graph DB Health:**", "🟢" if kgc.health() else "🔴")

# **Alias for compatibility** (import this name anywhere)
render_knowledge_graph = render_knowledge_graph_panel

# **Streamlit page entrypoint**
def main():
    try:
        user_ctx = get_user_ctx()
    except PermissionError as err:
        st.error(str(err))
        return

    render_knowledge_graph_panel(user_ctx)
