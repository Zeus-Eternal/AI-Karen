from __future__ import annotations

from typing import Dict

from ai_karen_engine.extensions.resource_monitor import ResourceMonitor, ResourceUsage


class MetricsDashboard:
    """Simple metrics dashboard for extensions."""

    def __init__(self, monitor: ResourceMonitor) -> None:
        self.monitor = monitor

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """Return resource usage metrics for all extensions."""
        usage = self.monitor.get_all_usage()
        return {name: usage_record.__dict__ for name, usage_record in usage.items()}

