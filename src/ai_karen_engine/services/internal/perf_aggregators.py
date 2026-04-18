"""Internal performance aggregator helpers for production monitoring."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional


class PerformanceAggregator:
    """Collects and aggregates service metrics for monitoring loops."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._metrics: Dict[str, List[float]] = defaultdict(list)

    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        self._metrics[name].append(float(value))

    async def collect_metrics(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for name, values in self._metrics.items():
            if values:
                out[name] = values[-1]
        return out
