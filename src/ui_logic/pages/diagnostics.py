"""Administrative diagnostics panel."""

from __future__ import annotations

import os
import shutil
from typing import Dict, List

import streamlit as st

from ai_karen_engine.services.health_checker import get_system_health
from ai_karen_engine.services.metrics_service import MetricsService
from ai_karen_engine.services.provider_health_monitor import ProviderHealthMonitor
from ui_logic.pages._shared import format_timedelta, require_page_access

try:  # pragma: no cover - psutil is an optional dependency
    import psutil
except Exception:  # pragma: no cover - streamlit surface
    psutil = None


REQUIRED_ROLES = ["admin"]
FEATURE_FLAG = "enable_admin_panel"

PROVIDER_ENV_REQUIREMENTS: Dict[str, List[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "google": ["GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"],
    "huggingface": ["HUGGINGFACE_API_TOKEN"],
    "cohere": ["COHERE_API_KEY"],
    "llamacpp": [],
}


def _collect_provider_health(monitor: ProviderHealthMonitor) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for provider, env_keys in PROVIDER_ENV_REQUIREMENTS.items():
        missing = [var for var in env_keys if not os.getenv(var)]
        is_healthy = not missing
        monitor.update_provider_health(
            provider,
            is_healthy=is_healthy,
            response_time=None,
            error_message=", ".join(missing) if missing else None,
        )

        health = monitor.get_provider_health(provider)
        rows.append(
            {
                "Provider": provider,
                "Status": health.status.value,
                "Last Check": health.last_check.isoformat(),
                "Success Rate": f"{health.success_rate:.0%}",
                "Note": "Missing env vars: " + ", ".join(missing) if missing else "",
            }
        )
    return rows


def _render_system_metrics() -> None:
    health = get_system_health()
    runtime = health.get("runtime", {})
    memory = health.get("memory", {})

    uptime = format_timedelta(runtime.get("uptime"))
    col_uptime, col_pid, col_python = st.columns(3)
    col_uptime.metric("Uptime", uptime)
    col_pid.metric("Process ID", runtime.get("pid", "n/a"))
    col_python.metric("Python", runtime.get("python_version", "n/a"))

    if memory:
        col_total, col_used, col_percent = st.columns(3)
        col_total.metric("RAM Total", f"{memory.get('total', 0) / (1024**3):.2f} GiB")
        col_used.metric("RAM Used", f"{memory.get('used', 0) / (1024**3):.2f} GiB")
        col_percent.metric("RAM Utilisation", f"{memory.get('percent', 0):.1f}%")

    if psutil:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        load_col, disk_col = st.columns(2)
        load_col.metric("CPU Load", f"{cpu_percent:.1f}%")
        usage = shutil.disk_usage(os.getcwd())
        disk_col.metric(
            "Disk Space",
            f"{usage.used / (1024**3):.1f} GiB / {usage.total / (1024**3):.1f} GiB",
        )


def _render_metrics_service(metrics: MetricsService) -> None:
    if psutil:
        metrics.fallback_collector.set_gauge("system_cpu_percent", psutil.cpu_percent(interval=0.05))
        metrics.fallback_collector.set_gauge("system_memory_percent", psutil.virtual_memory().percent)

    stats = metrics.fallback_collector.get_stats()
    st.markdown("### Internal Metrics Snapshot")
    st.json(stats, expanded=False)


def render_page(user_ctx: Dict | None = None) -> None:
    """Render the diagnostics dashboard."""

    require_page_access(
        user_ctx,
        required_roles=REQUIRED_ROLES,
        feature_flag=FEATURE_FLAG,
        feature_name="Admin diagnostics",
    )

    st.title("🩺 Kari Diagnostics")
    st.caption("Live view of system health, provider readiness and instrumentation counters.")

    st.subheader("Runtime metrics")
    _render_system_metrics()

    st.markdown("---")
    st.subheader("Provider readiness")
    monitor = ProviderHealthMonitor()
    provider_rows = _collect_provider_health(monitor)
    st.table(provider_rows)

    st.markdown("---")
    metrics_service: MetricsService = st.session_state.setdefault(
        "diagnostics_metrics_service",
        MetricsService(),
    )
    _render_metrics_service(metrics_service)

