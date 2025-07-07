"""
Kari Session Explorer UI (Streamlit)
- UI-only: All business logic in session_core.py
"""

import streamlit as st
import pandas as pd
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any

from ui_logic.components.memory.session_core import (
    get_session_records,
    get_audit_logs_for_entry,
)

def render_session_explorer(user_ctx: Dict[str, Any]):
    try:
        st.title("🧠 Session Memory Explorer")
        st.markdown(
            "<div style='color: #666; margin-bottom: 1.2em;'>"
            "Explore and audit your AI memory sessions. Filter by session, user, and time."
            "</div>",
            unsafe_allow_html=True
        )
        # --- Filters ---
        session_id = st.text_input("Session ID (leave blank for recent sessions)", value="")
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.utcnow() - timedelta(days=7),
                key="session_start_date"
            )
        with date_col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.utcnow(),
                key="session_end_date"
            )

        filter_user = st.text_input("User ID (optional)", value="")
        limit = st.slider("Limit", 10, 1000, 200)

        # --- Fetch session memory ---
        with st.spinner("Loading memory session data..."):
            try:
                records = get_session_records(
                    user_ctx=user_ctx,
                    session_id=session_id or None,
                    user_id=filter_user or user_ctx.get("user_id"),
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.max.time()),
                    limit=limit
                )
            except PermissionError:
                st.error("🔒 You don't have permission to view memory sessions.")
                return
            except Exception as ex:
                st.error(f"Failed to fetch session memory: {ex}")
                st.code(traceback.format_exc())
                return

        if not records:
            st.info("No memory records found for this filter.")
            return

        df = pd.DataFrame(records)
        if not df.empty:
            st.markdown("### Memory Entries")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No memory records available to display.")

        st.markdown("---")
        st.subheader("🔎 Memory Entry Details")
        entry_idx = st.number_input(
            "Select Entry Index",
            min_value=0, max_value=max(0, len(df) - 1),
            value=0,
            step=1
        )
        if not df.empty:
            entry = df.iloc[entry_idx].to_dict()
            st.json(entry, expanded=False)

            # Audit logs for this entry (admin only)
            if "admin" in user_ctx.get("roles", []):
                with st.expander("📝 Audit Logs for Entry"):
                    audit_logs = get_audit_logs_for_entry(user_ctx, entry)
                    if audit_logs:
                        st.dataframe(pd.DataFrame(audit_logs), use_container_width=True)
                    else:
                        st.info("No audit logs for this entry.")

    except Exception:
        st.error("Critical error in Session Explorer.")
        st.code(traceback.format_exc())

render_session_explorer_panel = render_session_explorer

__all__ = [
    "render_session_explorer",
    "render_session_explorer_panel",
]
