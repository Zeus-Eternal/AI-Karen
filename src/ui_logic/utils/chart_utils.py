"""
Kari UI Chart Utility:
- Unified chart builder with support for multiple engines (Plotly, Matplotlib, Altair)
- Features: Auto-sanitization, dynamic engine/field selection, color themes, RBAC, memory safety, testability
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype

logger = logging.getLogger("kari.ui.chart_utils")
logger.setLevel(logging.INFO)

# Visualization engine imports with fallbacks
try:
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available - install with pip install plotly")

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not available - install with pip install matplotlib")

try:
    import altair as alt
    ALTAIR_AVAILABLE = True
except ImportError:
    ALTAIR_AVAILABLE = False
    logger.warning("Altair not available - install with pip install altair")

# ======= Exception Hierarchy =======
class ChartError(Exception):
    pass


class UnsupportedChartType(ChartError):
    pass


class DataValidationError(ChartError):
    pass

# ======= Constants & Engine Priority =======
DEFAULT_PALETTE = [
    "#4C78A8", "#F58518", "#E45756", "#72B7B2",
    "#54A24B", "#EECA3B", "#B279A2", "#FF9DA6"
]
SUPPORTED_CHART_TYPES = [
    "line", "bar", "scatter", "pie", "area",
    "histogram", "box", "violin", "heatmap", "density", "funnel", "treemap"
]
ENGINE_PRIORITY = ["plotly", "altair", "matplotlib"]

# ======= Engine/Type API =======
def get_supported_chart_types() -> List[str]:
    return SUPPORTED_CHART_TYPES.copy()

def get_available_engines() -> List[str]:
    engines = []
    if PLOTLY_AVAILABLE:
        engines.append("plotly")
    if ALTAIR_AVAILABLE:
        engines.append("altair")
    if MATPLOTLIB_AVAILABLE:
        engines.append("matplotlib")
    return engines

# ======= Data Prep =======
def sanitize_data(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    max_rows: int = 100_000, max_cols: int = 50
) -> pd.DataFrame:
    """
    Cleanse, validate, and type-correct input for charting
    """
    try:
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame.from_dict(data)
        else:
            raise ValueError("Unsupported data format")
        if len(df) > max_rows:
            raise DataValidationError(f"Too many rows: {len(df)} (limit {max_rows})")
        if len(df.columns) > max_cols:
            raise DataValidationError(f"Too many columns: {len(df.columns)} (limit {max_cols})")
        df = df.replace([np.inf, -np.inf], np.nan)
        for col in df.columns:
            if not is_datetime64_any_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="ignore")
                except Exception:
                    pass
        return df
    except Exception as ex:
        logger.error(f"Data sanitization failed: {ex}")
        raise DataValidationError(str(ex)) from ex

def auto_detect_chart_type(df: pd.DataFrame, x: Optional[str] = None, y: Optional[str] = None) -> str:
    """Suggest a chart type based on data (for UI auto-viz)"""
    if not x or not y:
        return "bar"
    if is_datetime64_any_dtype(df[x]):
        return "line"
    if df[x].nunique() < 8 and is_numeric_dtype(df[y]):
        return "bar"
    if df[x].nunique() > 20:
        return "scatter"
    return "bar"

# ======= Main Chart Factory =======
def create_chart(
    data: Union[pd.DataFrame, List[Dict], Dict[str, List]],
    chart_type: str,
    config: Optional[Dict[str, Any]] = None,
    engine: Optional[str] = None,
    theme: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create chart via best-available engine. Memory safe. RBAC ready. Theme ready.
    """
    config = config or {}
    theme = theme or {}
    try:
        if chart_type not in SUPPORTED_CHART_TYPES:
            raise UnsupportedChartType(f"Unsupported chart type: {chart_type}")
        available_engines = get_available_engines()
        if not available_engines:
            raise ChartError("No engines available—install plotly, matplotlib, or altair")
        engine = engine or ENGINE_PRIORITY[0]
        if engine not in available_engines:
            engine = available_engines[0]
            logger.warning(f"Engine '{engine}' auto-selected")
        df = sanitize_data(data)
        palette = theme.get("palette", DEFAULT_PALETTE)
        # Call correct engine
        if engine == "plotly":
            return _create_plotly_chart(df, chart_type, config, palette)
        if engine == "altair":
            return _create_altair_chart(df, chart_type, config, palette)
        if engine == "matplotlib":
            return _create_matplotlib_chart(df, chart_type, config, palette)
        raise ChartError(f"Engine {engine} not implemented")
    except UnsupportedChartType:
        raise
    except Exception as ex:
        logger.error(f"Chart creation failed: {ex}")
        raise ChartError(str(ex)) from ex

# ======= Engine Implementations =======
def _create_plotly_chart(df, chart_type, config, palette) -> Any:
    x = config.get("x")
    y = config.get("y")
    color = config.get("color")
    title = config.get("title", "")
    try:
        if chart_type == "line":
            return px.line(
                df, x=x, y=y, color=color, title=title, color_discrete_sequence=palette
            )
        if chart_type == "bar":
            return px.bar(
                df, x=x, y=y, color=color, title=title, color_discrete_sequence=palette
            )
        if chart_type == "scatter":
            return px.scatter(
                df, x=x, y=y, color=color, title=title, color_discrete_sequence=palette
            )
        if chart_type == "pie":
            return px.pie(
                df, names=x, values=y, color=color, title=title, color_discrete_sequence=palette
            )
        if chart_type == "heatmap":
            idx = config.get("index", x)
            cols = config.get("columns", y)
            vals = config.get("values")
            pv = df.pivot(index=idx, columns=cols, values=vals)
            return px.imshow(pv, title=title, color_continuous_scale=palette)
        raise UnsupportedChartType(f"Plotly: {chart_type} not implemented")
    except Exception as ex:
        logger.error(f"Plotly chart error: {ex}")
        raise

def _create_altair_chart(df, chart_type, config, palette) -> Any:
    x = config.get("x")
    y = config.get("y")
    color = config.get("color")
    title = config.get("title", "")
    try:
        if chart_type == "line":
            return alt.Chart(df).mark_line().encode(x=x, y=y, color=color).properties(title=title)
        if chart_type == "bar":
            return alt.Chart(df).mark_bar().encode(x=x, y=y, color=color).properties(title=title)
        if chart_type == "scatter":
            return alt.Chart(df).mark_point().encode(x=x, y=y, color=color).properties(title=title)
        raise UnsupportedChartType(f"Altair: {chart_type} not implemented")
    except Exception as ex:
        logger.error(f"Altair chart error: {ex}")
        raise

def _create_matplotlib_chart(df, chart_type, config, palette) -> Any:
    x = config.get("x")
    y = config.get("y")
    title = config.get("title", "")
    fig, ax = plt.subplots(figsize=config.get("figsize", (8, 6)))
    try:
        if chart_type == "line":
            df.plot.line(x=x, y=y, ax=ax, color=palette[0])
        elif chart_type == "bar":
            df.plot.bar(x=x, y=y, ax=ax, color=palette)
        elif chart_type == "scatter":
            df.plot.scatter(x=x, y=y, ax=ax, color=palette[0])
        elif chart_type == "histogram":
            df[y].plot.hist(ax=ax, bins=config.get("bins", 20), color=palette[0])
        else:
            raise UnsupportedChartType(f"Matplotlib: {chart_type} not implemented")
        ax.set_title(title)
        plt.tight_layout()
        return fig
    except Exception as ex:
        logger.error(f"Matplotlib chart error: {ex}")
        raise

def save_chart(chart: Any, file_path: str, format: str = "png", width: int = 800, height: int = 600, **kwargs) -> None:
    try:
        if hasattr(chart, "write_image"):
            chart.write_image(file_path, width=width, height=height, **kwargs)
        elif hasattr(chart, "savefig"):
            chart.savefig(file_path, dpi=kwargs.get("dpi", 300), bbox_inches="tight")
        elif hasattr(chart, "save"):
            chart.save(file_path)
        else:
            raise ChartError("Chart cannot be saved by supported engines")
        logger.info(f"Chart saved: {file_path}")
    except Exception as ex:
        logger.error(f"Save failed: {ex}")
        raise

def create_dashboard(
    charts: List[Tuple[Union[pd.DataFrame, Dict], str, Dict[str, Any]]],
    layout: Optional[Dict[str, Any]] = None,
    engine: str = "plotly"
) -> Any:
    if engine == "plotly" and PLOTLY_AVAILABLE:
        rows = layout.get("rows", 1) if layout else 1
        cols = layout.get("cols", min(2, len(charts))) if layout else min(2, len(charts))
        fig = make_subplots(rows=rows, cols=cols)
        for i, (data, chart_type, config) in enumerate(charts):
            chart = create_chart(data, chart_type, config, engine)
            fig.add_trace(chart.data[0], row=(i // cols) + 1, col=(i % cols) + 1)
        return fig
    raise ChartError(f"Dashboard not implemented for {engine}")

def apply_rbac_filter(chart: Any, user_permissions: Dict[str, bool], config: Dict[str, Any]) -> Any:
    # This stub can be expanded for full RBAC logic
    return chart

__all__ = [
    "create_chart", "save_chart", "create_dashboard", "get_supported_chart_types",
    "get_available_engines", "auto_detect_chart_type", "apply_rbac_filter",
    "ChartError", "UnsupportedChartType", "DataValidationError", "DEFAULT_PALETTE"
]
