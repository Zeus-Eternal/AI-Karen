"""
Kari Data Explorer Logic
- Explore, filter, search, and profile tabular data
- Semantic search, summary stats, export/transform
"""

import pandas as pd
from typing import Dict, Any, Optional
from ui.utils.api import semantic_search_df, summarize_dataframe

def explore_data(df: pd.DataFrame, query: Optional[str] = None, actions: Optional[Dict[str, Any]] = None) -> Dict:
    """
    Returns filtered/explored DataFrame, summary, optionally search or transform.
    """
    result_df = df
    if query:
        result_df = semantic_search_df(df, query)
    summary = summarize_dataframe(result_df)
    return {
        "result": result_df.head(100).to_dict(orient="records"),
        "summary": summary
    }
