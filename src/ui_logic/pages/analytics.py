"""
Kari Analytics Page
- Orchestrates: auto-parser, chart builder, data explorer
"""

from src.ui_logic.components.analytics.auto_parser import render_auto_parser
from src.ui_logic.components.analytics.chart_builder import render_chart_builder
from src.ui_logic.components.analytics.data_explorer import render_data_explorer


def analytics_page(user_ctx=None):
    render_auto_parser(user_ctx=user_ctx)
    render_chart_builder(user_ctx=user_ctx)
    render_data_explorer(user_ctx=user_ctx)
