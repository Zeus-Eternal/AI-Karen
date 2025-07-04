"""
Kari Chart Builder Logic
- Builds charts from DataFrame, config-driven, export-ready
- Handles auto-viz (auto-chart), custom options, error handling
"""

import pandas as pd
from typing import Dict, Any
from ui.utils.chart_utils import create_chart, get_supported_chart_types

def build_chart(data: pd.DataFrame, chart_type: str, config: Dict[str, Any]) -> Any:
    """
    Create a chart object (e.g., Plotly, Matplotlib Figure) based on config.
    """
    if chart_type not in get_supported_chart_types():
        raise ValueError(f"Unsupported chart type: {chart_type}")
    return create_chart(data, chart_type, config)
