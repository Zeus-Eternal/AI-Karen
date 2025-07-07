"""
Kari Data Explorer - Enterprise Production

- Universal, dependency-injected, RBAC-aware tabular explorer
- Semantic search, profiling, summary, and plugin-compat
- Full diagnostics, error trace, and performance meta for UI/admin
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
import pandas as pd

logger = logging.getLogger("kari.analytics.data_explorer")

# === Dependency Injection: Require actual implementations ===
try:
    from src.ui_logic.utils.api import semantic_search_df, summarize_dataframe
except ImportError:
    def semantic_search_df(*_, **__): raise NotImplementedError("semantic_search_df not available.")
    def summarize_dataframe(*_, **__): raise NotImplementedError("summarize_dataframe not available.")

# ===== RBAC ====
def check_rbac(user_roles: List[str], required: Union[str, List[str]]) -> bool:
    if isinstance(required, str):
        required = [required]
    return any(role in user_roles for role in required)

# ===== Data Explorer Core =====
def render_data_explorer(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    user_roles: Optional[List[str]] = None,
    query: Optional[str] = None,
    mode: str = "summary",
    semantic_model: Optional[Any] = None,
    rbac: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    semantic_search_fn: Optional[Callable] = None,
    summary_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Explore and profile data, with optional semantic search and RBAC.
    Args:
        data: DataFrame or serializable
        user_roles: Roles for RBAC
        query: Optional search query
        mode: "summary" | "semantic_search" | "full"
        semantic_model: Embedding model for semantic search
        rbac: RBAC config (require_role)
        config: Additional (max_rows, top_k, etc)
        semantic_search_fn: DI override for semantic_search_df
        summary_fn: DI override for summarize_dataframe
    Returns:
        Dict with keys: result, meta, success, error, (traceback if failed)
    """
    t0 = time.time()
    meta = {"mode": mode, "config": config or {}, "start": t0}
    user_roles = user_roles or []
    config = config or {}
    rbac = rbac or {}
    semantic_search_fn = semantic_search_fn or semantic_search_df
    summary_fn = summary_fn or summarize_dataframe

    # RBAC
    if rbac.get("require_role") and not check_rbac(user_roles, rbac["require_role"]):
        return {"success": False, "error": "Access denied", "result": None, "meta": meta}

    # Data ingest
    try:
        df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data.copy()
        meta["rows"] = len(df)
        meta["cols"] = list(df.columns)
    except Exception as ex:
        logger.error(f"Failed to coerce input to DataFrame: {ex}")
        meta["error_type"] = "DataFrameConversion"
        return {"success": False, "error": f"DataFrame conversion: {ex}", "result": None, "meta": meta}

    # Row/col cap
    max_rows = config.get("max_rows", 100_000)
    max_cols = config.get("max_cols", 100)
    if len(df) > max_rows or len(df.columns) > max_cols:
        meta.update({"error_type": "SizeLimit", "rows": len(df), "cols": len(df.columns)})
        return {
            "success": False,
            "error": f"Dataset too large ({len(df)} rows, {len(df.columns)} cols)",
            "result": None, "meta": meta
        }

    try:
        if mode == "semantic_search":
            if not query:
                return {"success": False, "error": "Missing search query", "result": None, "meta": meta}
            top_k = config.get("top_k", 10)
            result_df = semantic_search_fn(df, query, top_k=top_k, model=semantic_model)
            meta.update({"query": query, "top_k": top_k})
        elif mode == "summary":
            result_df, summary = summary_fn(df)
            meta["summary"] = summary
        elif mode == "full":
            cap = config.get("full_max_rows", 5000)
            if len(df) > cap:
                result_df = df.head(cap)
                meta["truncated"] = True
                meta["full_max_rows"] = cap
            else:
                result_df = df
        else:
            meta["error_type"] = "InvalidMode"
            return {"success": False, "error": f"Unknown mode: {mode}", "result": None, "meta": meta}
        elapsed = time.time() - t0
        meta["elapsed_sec"] = round(elapsed, 4)
        return {"success": True, "result": result_df, "meta": meta, "error": None}
    except Exception as ex:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Data explorer error: {ex}\n{tb}")
        meta["error_type"] = "ProcessingError"
        meta["traceback"] = tb
        return {"success": False, "error": str(ex), "result": None, "meta": meta}

# === API Exports ===
__all__ = [
    "render_data_explorer",
    "check_rbac",
]

# === High-level helper ===
def explore_data(
    df: pd.DataFrame,
    query: Optional[str] = None,
    actions: Optional[Dict[str, Any]] = None,
    semantic_search_fn: Optional[Callable] = None,
    summary_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Filter/search/explore DataFrame (headless, DI-ready)
    """
    semantic_search_fn = semantic_search_fn or semantic_search_df
    summary_fn = summary_fn or summarize_dataframe
    result_df = semantic_search_fn(df, query) if query else df
    result_df, summary = summary_fn(result_df)
    return {
        "result": result_df.head(100).to_dict(orient="records"),
        "summary": summary
    }
