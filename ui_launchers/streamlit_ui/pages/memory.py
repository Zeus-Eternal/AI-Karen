# ui_launchers/streamlit_ui/pages/memory.py

import os
import time
import streamlit as st
import pandas as pd
import json

from typing import Dict, Any, List, Optional

# --- Import Kari memory interface ---
try:
    from ai_karen_engine.core.memory import (
        recall_context,
        update_memory,
        flush_duckdb_to_postgres,
        postgres,
        duckdb,
        redis,
        ElasticClient,
        logger as memory_logger,
    )
    from ai_karen_engine.clients.database.milvus_client import MilvusClient
except ImportError:
    st.error("MemoryManager not found; install Kari backend.")
    st.stop()

try:
    milvus_client = MilvusClient()
except Exception:
    milvus_client = None

# --- Evil Glory: Config ---
MEMORY_LIMIT = 100
PAGE_SIZE = 25

# --- Backend health check helpers ---
def backend_status(name: str, backend) -> str:
    if backend is None:
        return ":red[Offline]"
    try:
        if hasattr(backend, "health"):
            return ":green[Healthy]" if backend.health() else ":orange[Degraded]"
        return ":green[Available]"
    except Exception:
        return ":red[Error]"

def get_status_legend():
    return {
        "Elastic": backend_status("Elastic", ElasticClient),
        "Milvus": backend_status("Milvus", milvus_client),
        "Postgres": backend_status("Postgres", postgres),
        "Redis": backend_status("Redis", redis),
        "DuckDB": backend_status("DuckDB", duckdb),
    }

# --- Evil Twin Observability: Log last 50 errors ---
def get_recent_memory_logs(n=50):
    # Assumes Kari uses a file handler or in-memory log capture for memory
    import logging
    records = []
    for handler in memory_logger.handlers:
        if hasattr(handler, "buffer"):
            for record in handler.buffer[-n:]:
                records.append(logging.Formatter().format(record))
    return records[-n:]

# --- Evil Prompt: Sidebar Filters ---
st.sidebar.header("Memory Context Recall")
user_id = st.sidebar.text_input("User ID", value="anonymous")
session_id = st.sidebar.text_input("Session ID (optional)", value="")
query = st.sidebar.text_input("Search Query", value="")
limit = st.sidebar.slider("Limit", min_value=1, max_value=MEMORY_LIMIT, value=25)
use_all_backends = st.sidebar.checkbox("Search All Backends", value=True)
selected_backend = st.sidebar.selectbox(
    "Backend (if not All)", 
    ["Elastic", "Milvus", "Postgres", "Redis", "DuckDB"], 
    index=0
)
time_filter_days = st.sidebar.number_input("Time Filter (last N days, 0=all)", min_value=0, max_value=365, value=0)
show_metrics = st.sidebar.checkbox("Show Metrics Dashboard", value=True)
show_logs = st.sidebar.checkbox("Show Backend Logs", value=False)

st.title("🧠 Kari Memory Mesh")
st.caption("Modular memory mesh for *recall, diagnostics, and backend status*.")

# --- Backend Status Panel ---
st.subheader("Backend Status")
status_legend = get_status_legend()
cols = st.columns(len(status_legend))
for i, (name, status) in enumerate(status_legend.items()):
    cols[i].markdown(f"**{name}:** {status}")

st.divider()

# --- Recall Operation ---
st.subheader("Recall Context")
user_ctx = {"user_id": user_id}
if session_id:
    user_ctx["session_id"] = session_id

# Backend priority (as per config)
backend_map = {
    "Elastic": "elastic",
    "Milvus": "milvus",
    "Postgres": "postgres",
    "Redis": "redis",
    "DuckDB": "duckdb"
}
if use_all_backends:
    backends = [b for b in backend_map.values()]
else:
    backends = [backend_map[selected_backend]]

# Optional: time range filter
if time_filter_days > 0:
    time_cutoff = time.time() - 86400 * time_filter_days
    time_range = (time_cutoff, time.time())
else:
    time_range = None

with st.spinner("Recalling context..."):
    try:
        results = recall_context(
            user_ctx,
            query,
            limit=limit,
            # Optionally inject more params (time_range, backends) if supported in your backend
        )
    except Exception as ex:
        st.error(f"Recall error: {ex}")
        results = []

# --- Display Results ---
if not results:
    st.info("No memory found for your query/context.")
else:
    # Normalize for display
    df = pd.DataFrame(results)
    if "timestamp" in df:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
    # Display backend/source column if available
    if "backend" not in df and use_all_backends:
        df["backend"] = "mixed"
    # Slice to page
    if len(df) > PAGE_SIZE:
        st.write(f"Showing latest {PAGE_SIZE} of {len(df)} results:")
        df = df.head(PAGE_SIZE)
    st.dataframe(df, use_container_width=True)
    with st.expander("Show raw JSON"):
        st.code(json.dumps(results, indent=2))

# --- Metrics Dashboard ---
if show_metrics:
    st.subheader("Memory Metrics (live)")
    try:
        from ai_karen_engine.core.memory.manager import get_metrics
        metrics = get_metrics()
    except Exception:
        metrics = {}
    st.json(metrics)

# --- Backend Error Logs ---
if show_logs:
    st.subheader("Backend Error Log (last 50)")
    logs = get_recent_memory_logs(50)
    if logs:
        for line in logs:
            st.text(line)
    else:
        st.info("No recent errors found.")

# --- Flush Controls (for admin/dev only, hidden in prod) ---
if st.sidebar.button("Flush DuckDB → Postgres", help="For admins only, dev use!"):
    if postgres and duckdb:
        try:
            flush_duckdb_to_postgres(postgres, os.getenv("DUCKDB_PATH", "kari_mem.duckdb"))
            st.success("Flush triggered.")
        except Exception as ex:
            st.error(f"Flush failed: {ex}")
    else:
        st.warning("Flush not available: Postgres or DuckDB unavailable.")

st.markdown("---")
st.caption("Kari AI Memory Mesh · All operations are fully audited · Evil Twin © 2025")

