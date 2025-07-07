"""
Kari Memory Analytics Logic (Production)
- Visualizes memory usage, retrieval, hit/miss/decay, and operational metrics.
- RBAC: admin, analyst (full); user (read-only, no audit trail)
- Prompt-first, audit-trailed, fully compatible with Kari/PromptRouter
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import traceback
from functools import wraps

from ui_logic.hooks.rbac import require_roles
from ui_logic.utils.api import fetch_memory_metrics, fetch_audit_logs, fetch_memory_analytics

# Configure logging
logger = logging.getLogger("kari.memory.analytics")
logger.setLevel(logging.INFO)

# --- Error Classes ---
class MemoryAnalyticsError(Exception):
    pass


class PermissionDeniedError(MemoryAnalyticsError):
    pass


class DataFetchError(MemoryAnalyticsError):
    pass

def log_analytics_operation(func):
    """Decorator to log analytics operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"{func.__name__} completed in {duration:.2f}s",
                extra={"duration": duration, "op": func.__name__}
            )
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {str(e)}", exc_info=True)
            raise
    return wrapper

@log_analytics_operation
def fetch_memory_data(
    time_range: str = "7d",
    session_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    user_id: Optional[str] = None
) -> pd.DataFrame:
    """Fetch memory metrics with robust error handling."""
    try:
        # Convert time range to datetime
        now = datetime.utcnow()
        start_date = None
        if time_range == "24h":
            start_date = now - timedelta(hours=24)
        elif time_range == "7d":
            start_date = now - timedelta(days=7)
        elif time_range == "30d":
            start_date = now - timedelta(days=30)
        # else "All": start_date = None

        metrics = fetch_memory_metrics(
            start_date=start_date,
            end_date=now,
            session_id=session_id,
            metric_type=None if metric_type == "All" else metric_type,
            user_id=user_id
        )
        if not metrics:
            return pd.DataFrame()
        df = pd.DataFrame(metrics)
        # Ensure required columns for summary/trend charts
        for col in ["precision", "recall", "decay", "miss"]:
            if col not in df.columns:
                df[col] = np.nan
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch/process memory data: {e}")
        raise DataFetchError(str(e)) from e

def render_metric(label: str, value: Any, help_str: str = ""):
    st.metric(label, value, help=help_str)

def render_time_series(df: pd.DataFrame, metrics: List[str]):
    if df.empty or "timestamp" not in df.columns:
        st.warning("No time series data available for trends.")
        return
    plot_df = df.set_index("timestamp")[metrics].fillna(0)
    st.line_chart(plot_df)

def render_memory_analytics(user_ctx: Dict[str, Any]):
    """
    Main memory analytics panel, RBAC-enforced, prompt-first, with audit trail.
    """
    try:
        # RBAC: Only allow users with 'analyst' or 'admin' full access, users get read-only (no audit).
        roles = user_ctx.get("roles", [])
        is_full = False
        try:
            require_roles(user_ctx, ["analyst", "admin"])
            is_full = True
        except PermissionError:
            if "user" not in roles:
                st.error("🔒 You don't have permission to view memory analytics.")
                logger.warning(f"Permission denied for user {user_ctx.get('user_id')}", extra={"roles": roles})
                return

        st.title("🧠 Kari Memory Analytics")
        st.markdown(
            "<div style='color: #666; margin-bottom: 1.2em;'>"
            "Analyze Kari's memory efficiency, precision, decay, and operational logs."
            "</div>", unsafe_allow_html=True)

        # --- Query Controls ---
        with st.expander("🔍 Filter Options", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                time_range = st.selectbox(
                    "Time Window", ["24h", "7d", "30d", "All"], index=1, key="time_range"
                )
            with col2:
                session_id = st.text_input(
                    "Session ID", value=str(user_ctx.get("session_id", "")), key="session_id"
                )
            with col3:
                metric_type = st.selectbox(
                    "Metric Type", ["All", "Recall", "Write", "Decay", "Miss"], index=0, key="metric_type"
                )

        # --- Load Data ---
        with st.spinner("Loading memory metrics..."):
            try:
                df = fetch_memory_data(
                    time_range=time_range,
                    session_id=session_id if session_id else None,
                    metric_type=metric_type,
                    user_id=user_ctx["user_id"]
                )
            except DataFetchError as e:
                st.error(f"Failed to load memory data: {e}")
                return

        if df.empty:
            st.info("No memory metrics found for the selected filters.")
            return

        # --- Summary Metrics ---
        st.subheader("📈 Memory Performance Overview")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric("Total Ops", len(df), "Total operations in filter range")
        with c2:
            render_metric("Avg Precision", f"{df['precision'].mean():.2f}", "Average top-5 retrieval precision")
        with c3:
            render_metric("Avg Recall", f"{df['recall'].mean():.2f}", "Average recall score")
        with c4:
            render_metric("Avg Decay", f"{df['decay'].mean():.2f}", "Mean vector decay factor")

        # --- Trends ---
        st.subheader("🕒 Trends Over Time")
        render_time_series(df, ["precision", "recall", "decay"])

        # --- Detail Table ---
        st.subheader("🔍 Detailed Memory Log")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_order=[c for c in ["timestamp", "operation", "precision", "recall", "decay", "miss", "duration_ms"] if c in df.columns]
        )

        # --- Audit Trail (analyst/admin only) ---
        if is_full:
            with st.expander("📝 Audit Trail"):
                try:
                    audit_logs = fetch_audit_logs(
                        category="memory_analytics",
                        user_id=user_ctx["user_id"],
                        limit=50
                    )
                    if audit_logs:
                        st.dataframe(pd.DataFrame(audit_logs), use_container_width=True)
                    else:
                        st.info("No audit logs found.")
                except Exception as e:
                    st.warning(f"Audit log fetch error: {e}")

        st.caption("Memory Analytics Panel v2.0 – Kari remembers every query, tracks every byte. 🦹‍♂️")

    except Exception as e:
        st.error("A critical error occurred in the memory analytics panel.")
        logger.critical(
            f"Memory analytics render failed: {str(e)}\n{traceback.format_exc()}",
            extra={"user": user_ctx.get('user_id')}
        )
        if st.session_state.get("show_debug_info", False):
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())

# Panel alias for imports
render_memory_analytics_panel = render_memory_analytics

# --- API-Ready Utility for plugin/prompt use ---
@log_analytics_operation
def get_memory_analytics(user_ctx: Dict[str, Any]) -> Dict[str, Any]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst", "user"]):
        raise PermissionDeniedError("Insufficient privileges for memory analytics.")
    return fetch_memory_analytics(user_ctx.get("user_id"))

@log_analytics_operation
def get_memory_audit(user_ctx: Dict[str, Any], limit: int = 25) -> List[Dict]:
    if not user_ctx or not require_roles(user_ctx, ["admin", "analyst"]):
        raise PermissionDeniedError("Insufficient privileges for memory audit.")
    return fetch_audit_logs(category="memory", user_id=user_ctx["user_id"])[-limit:][::-1]
