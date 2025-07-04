"""
Kari UI Chart Utility
- Unified chart builder for analytics, memory, model, and admin dashboards
- Handles auto-sanitization, dynamic chart selection, color-palette, and RBAC display
- Production-ready: used by Streamlit, Plotly, Matplotlib, and future React/JS bridges
"""

import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any, List, Union
import logging
import seaborn as sns

logger = logging.getLogger("kari.ui.chart_utils")
logger.setLevel(logging.INFO)

# --- Default color palette (override with themes) ---
DEFAULT_PALETTE = [
    "#BB00FF", "#00C2FF", "#00FFAA", "#FFE156", "#FF6F61", "#41436A", "#2F4858", "#364F6B"
]

def sanitize_data(data: Union[pd.DataFrame, List[Dict], Dict[str, List]]) -> pd.DataFrame:
    """Normalize any input to DataFrame, clean NaNs/inf, enforce safe types."""
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        df = pd.DataFrame.from_dict(data)
    else:
        raise ValueError("Unsupported data format for charting.")

    # Clean
    df = df.replace([float("inf"), float("-inf")], None)
    df = df.dropna(axis=1, how="all")
    df = df.fillna("")
    return df

def plot_line(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    x: str,
    y: Union[str, List[str]],
    title: str = "",
    palette: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """Line chart: returns Plotly Figure for UI embedding."""
    df = sanitize_data(data)
    fig = px.line(df, x=x, y=y, title=title, color_discrete_sequence=palette or DEFAULT_PALETTE, **kwargs)
    logger.info(f"Line chart generated: {title}")
    return fig

def plot_bar(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    x: str,
    y: Union[str, List[str]],
    title: str = "",
    orientation: str = "v",
    palette: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """Bar chart: returns Plotly Figure."""
    df = sanitize_data(data)
    fig = px.bar(df, x=x, y=y, title=title, orientation=orientation, color_discrete_sequence=palette or DEFAULT_PALETTE, **kwargs)
    logger.info(f"Bar chart generated: {title}")
    return fig

def plot_pie(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    names: str,
    values: str,
    title: str = "",
    palette: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """Pie chart: Plotly."""
    df = sanitize_data(data)
    fig = px.pie(df, names=names, values=values, title=title, color_discrete_sequence=palette or DEFAULT_PALETTE, **kwargs)
    logger.info(f"Pie chart generated: {title}")
    return fig

def plot_scatter(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    x: str,
    y: str,
    color: Optional[str] = None,
    size: Optional[str] = None,
    title: str = "",
    palette: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """Scatter plot: Plotly."""
    df = sanitize_data(data)
    fig = px.scatter(df, x=x, y=y, color=color, size=size, title=title, color_discrete_sequence=palette or DEFAULT_PALETTE, **kwargs)
    logger.info(f"Scatter plot generated: {title}")
    return fig

def plot_hist(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    x: str,
    bins: int = 20,
    title: str = "",
    palette: Optional[List[str]] = None,
    **kwargs
) -> Any:
    """Histogram: Matplotlib (raw for ultra-performance in batch/exports)."""
    df = sanitize_data(data)
    plt.figure(figsize=(8, 4))
    plt.hist(df[x], bins=bins, color=(palette or DEFAULT_PALETTE)[0])
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel("Frequency")
    logger.info(f"Histogram generated: {title}")
    return plt

def plot_heatmap(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    title: str = "",
    cmap: str = "coolwarm",
    annot: bool = False,
    **kwargs
) -> Any:
    """Heatmap: Seaborn/Matplotlib."""
    df = sanitize_data(data)
    corr = df.corr(numeric_only=True)
    plt.figure(figsize=(10, 6))
    sns.heatmap(corr, annot=annot, cmap=cmap)
    plt.title(title)
    logger.info(f"Heatmap generated: {title}")
    return plt

def quick_chart(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    chart_type: str = "line",
    **kwargs
) -> Any:
    """Auto-selects and builds the chart based on type."""
    chart_type = chart_type.lower()
    if chart_type == "line":
        return plot_line(data, **kwargs)
    elif chart_type == "bar":
        return plot_bar(data, **kwargs)
    elif chart_type == "pie":
        return plot_pie(data, **kwargs)
    elif chart_type == "scatter":
        return plot_scatter(data, **kwargs)
    elif chart_type == "hist":
        return plot_hist(data, **kwargs)
    elif chart_type == "heatmap":
        return plot_heatmap(data, **kwargs)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

# --- Usage Example (dev/test) ---
if __name__ == "__main__":
    # Fake data example
    data = [
        {"epoch": 1, "accuracy": 0.8, "loss": 0.3},
        {"epoch": 2, "accuracy": 0.85, "loss": 0.25},
        {"epoch": 3, "accuracy": 0.88, "loss": 0.2},
    ]
    fig = quick_chart(data, chart_type="line", x="epoch", y="accuracy", title="Accuracy over Epochs")
    fig.show()
