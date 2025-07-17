"""
Kari Analytics Chart Builder - Enterprise Production Version

- Full dependency injection (chart engine, config, logging)
- Hard limits, auto field inference, and UX fallbacks
- Modular: engine switch (Plotly/Altair/Matplotlib/future), DI, headless, plugin-ready
- Full error trace/diagnostics, typed exceptions, logging, and metrics-ready
- 100% testable: pass in custom creator for A/B/E2E tests
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union
import traceback
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype

# ================== Exceptions ==================
class ChartBuilderError(Exception):
    pass

class InvalidChartConfig(ChartBuilderError):
    pass

class DataValidationError(ChartBuilderError):
    pass

# ================== Constants ===================
DEFAULT_CHART_TYPES = [
    "line", "bar", "scatter", "pie", "area",
    "histogram", "box", "violin", "heatmap"
]
DEFAULT_MAX_ROWS = 1_000_000
DEFAULT_MAX_COLS = 100

# ================== ChartBuilder =================
class ChartBuilder:
    """
    ChartBuilder: Enterprise-ready chart orchestration for Kari
    - Supports dependency injection for chart engine and logger
    - Safeguards for row/column limits
    """
    def __init__(
        self,
        chart_creator: Optional[Callable[[pd.DataFrame, str, Dict[str, Any]], Any]] = None,
        supported_chart_types: Optional[List[str]] = None,
        max_rows: int = DEFAULT_MAX_ROWS,
        max_cols: int = DEFAULT_MAX_COLS,
        logger: Optional[logging.Logger] = None,
    ):
        self.chart_creator = chart_creator or self._not_implemented_chart_creator
        self.supported_chart_types = supported_chart_types or DEFAULT_CHART_TYPES
        self.max_rows = max_rows
        self.max_cols = max_cols
        self.logger = logger or logging.getLogger("kari.analytics.chart_builder")

    def get_supported_chart_types(self) -> List[str]:
        return list(self.supported_chart_types)

    def infer_data_fields(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        try:
            if df is None or df.empty:
                return {"numeric": [], "categorical": [], "datetime": [], "all": []}
            if len(df) > self.max_rows:
                raise DataValidationError(f"Data exceeds row limit ({self.max_rows})")
            if len(df.columns) > self.max_cols:
                raise DataValidationError(f"Data exceeds col limit ({self.max_cols})")
            numeric, categorical, datetime_cols = [], [], []
            for col in df.columns:
                if is_numeric_dtype(df[col]):
                    numeric.append(col)
                elif is_datetime64_any_dtype(df[col]):
                    datetime_cols.append(col)
                else:
                    categorical.append(col)
            return {
                "numeric": numeric,
                "categorical": categorical,
                "datetime": datetime_cols,
                "all": df.columns.tolist()
            }
        except Exception as ex:
            self.logger.error(f"Field inference failed: {ex}")
            raise DataValidationError(f"Data field inference failed: {ex}") from ex

    def validate_chart_config(
        self, chart_type: str, config: Dict[str, Any], fields: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        try:
            ctype = chart_type.lower()
            if ctype not in self.supported_chart_types:
                raise InvalidChartConfig(f"Unsupported chart type: {ctype}")
            cfg = dict(config) if config else {}
            # Pie: needs labels (x), not y; all others need x/y
            if "x" not in cfg:
                if ctype == "pie":
                    cfg["x"] = fields["categorical"][0] if fields["categorical"] else fields["all"][0]
                else:
                    cfg["x"] = fields["datetime"][0] if fields["datetime"] else (
                        fields["categorical"][0] if fields["categorical"] else fields["all"][0]
                    )
            if ctype != "pie" and "y" not in cfg:
                cfg["y"] = fields["numeric"][0] if fields["numeric"] else None
            # Validate
            if ctype == "pie":
                if not cfg.get("x"):
                    raise InvalidChartConfig("Pie chart requires a label ('x') field.")
            else:
                if not cfg.get("x") or not cfg.get("y"):
                    raise InvalidChartConfig(f"{ctype} chart requires both x and y fields.")
            return cfg
        except Exception as ex:
            self.logger.error(f"Chart config validation failed: {ex}")
            raise InvalidChartConfig(f"Chart config invalid: {ex}") from ex

    def build_chart(
        self,
        data: Union[pd.DataFrame, Dict[str, List], List[Dict]],
        chart_type: str,
        config: Optional[Dict[str, Any]] = None,
        fail_safe: bool = True,
    ) -> Union[Any, Dict[str, Any]]:
        try:
            df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data.copy()
            fields = self.infer_data_fields(df)
            cfg = self.validate_chart_config(chart_type, config, fields)
            chart = self.chart_creator(df, chart_type.lower(), cfg)
            self.logger.info(f"Chart built: {chart_type} | x={cfg.get('x')} y={cfg.get('y')}")
            return chart
        except Exception as ex:
            tb = traceback.format_exc()
            self.logger.error(f"Chart build failed: {ex}\n{tb}")
            if fail_safe:
                return self._create_error_response(
                    error=str(ex),
                    traceback=tb,
                    chart_type=chart_type,
                    config=config,
                    fields=fields if 'fields' in locals() else {},
                )
            else:
                raise ChartBuilderError(f"Chart failed: {ex}") from ex

    @staticmethod
    def _not_implemented_chart_creator(df, chart_type, config):
        raise NotImplementedError("No chart engine wired. Inject Plotly/Altair engine.")

    @staticmethod
    def _create_error_response(
        error: str,
        traceback: str,
        chart_type: str,
        config: Dict[str, Any],
        fields: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        return {
            "error": error,
            "traceback": traceback,
            "chart_type": chart_type,
            "config": config,
            "fields": fields,
            "success": False,
            "message": f"Chart build failed: {error}",
        }

# ====== Factory & Module-level API ======

def _plotly_chart_creator(df: pd.DataFrame, chart_type: str, config: Dict[str, Any]) -> Any:
    import plotly.express as px
    ctype = chart_type.lower()
    opts = config.copy()
    if ctype == "bar":
        return px.bar(df, x=opts["x"], y=opts["y"], color=opts.get("color"))
    if ctype == "line":
        return px.line(df, x=opts["x"], y=opts["y"], color=opts.get("color"))
    if ctype == "scatter":
        return px.scatter(df, x=opts["x"], y=opts["y"], color=opts.get("color"))
    if ctype == "pie":
        return px.pie(df, names=opts["x"], values=opts.get("y"))
    if ctype == "area":
        return px.area(df, x=opts["x"], y=opts["y"], color=opts.get("color"))
    if ctype == "histogram":
        return px.histogram(df, x=opts["x"], y=opts.get("y"), color=opts.get("color"))
    if ctype == "box":
        return px.box(df, x=opts.get("x"), y=opts["y"], color=opts.get("color"))
    if ctype == "violin":
        return px.violin(df, x=opts.get("x"), y=opts["y"], color=opts.get("color"))
    if ctype == "heatmap":
        return px.density_heatmap(df, x=opts["x"], y=opts["y"])
    raise InvalidChartConfig(f"Unsupported chart type for plotly: {ctype}")

def create_chart_builder(engine: str = "plotly") -> ChartBuilder:
    """
    Factory for the production chart builder.
    """
    if engine == "plotly":
        return ChartBuilder(chart_creator=_plotly_chart_creator)
    # Optionally: Add altair/matplotlib support here.
    raise NotImplementedError(f"Engine '{engine}' not supported yet")

def render_chart_builder(
    data: Union[pd.DataFrame, Dict[str, List], List[Dict]],
    chart_type: str,
    config: Optional[Dict[str, Any]] = None,
    fail_safe: bool = True,
    engine: str = "plotly"
) -> Any:
    builder = create_chart_builder(engine=engine)
    return builder.build_chart(data, chart_type, config, fail_safe)

def infer_chart_fields(df: pd.DataFrame) -> Dict[str, List[str]]:
    builder = create_chart_builder()
    return builder.infer_data_fields(df)

def get_chart_schema(df: pd.DataFrame) -> Dict[str, List[str]]:
    builder = create_chart_builder()
    return {
        "chart_types": builder.get_supported_chart_types(),
        **builder.infer_data_fields(df),
    }

# ==== QUICK CHART RENDER (Streamlit demo/prod bridge) ====
def render_quick_charts(
    df: pd.DataFrame,
    chart_types: Optional[List[str]] = None,
    title: Optional[str] = "Quick Charts",
    engine: str = "plotly",
    container=None,
):
    """
    Render quick chart preview panel, for dashboards or EDA.
    """
    import streamlit as st
    chart_types = chart_types or DEFAULT_CHART_TYPES
    builder = create_chart_builder(engine)
    st_container = container if container is not None else st

    st_container.subheader(title or "Quick Charts")
    fields = builder.infer_data_fields(df)
    choices = [c for c in chart_types if c in builder.get_supported_chart_types()]

    chart_type = st_container.selectbox("Chart type", choices)
    cfg = {}

    # x/y auto-select
    if chart_type == "pie":
        cfg["x"] = st_container.selectbox("Labels (x)", fields["categorical"] or fields["all"])
        if fields["numeric"]:
            cfg["y"] = st_container.selectbox("Values (y/size)", fields["numeric"])
    else:
        cfg["x"] = st_container.selectbox("X axis", fields["datetime"] or fields["categorical"] or fields["all"])
        cfg["y"] = st_container.selectbox("Y axis", fields["numeric"] or fields["all"])

    # Build chart
    result = builder.build_chart(df, chart_type, cfg)
    if isinstance(result, dict) and not result.get("success", True):
        st_container.error(result.get("message", "Chart error"))
        st_container.code(result.get("traceback", ""), language="python")
    else:
        import plotly.graph_objects as go
        st_container.plotly_chart(result, use_container_width=True)

CHART_TYPES = DEFAULT_CHART_TYPES

__all__ = [
    "ChartBuilder",
    "create_chart_builder",
    "render_chart_builder",
    "infer_chart_fields",
    "get_chart_schema",
    "render_quick_charts",
    "CHART_TYPES",
    "ChartBuilderError",
    "InvalidChartConfig",
    "DataValidationError",
]
