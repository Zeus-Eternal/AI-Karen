from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .logger import get_logger

logger = get_logger("kari.telemetry")

class RuntimeTelemetry:
    """Helper for recording runtime performance and resource telemetry."""

    @staticmethod
    def record_latency(operation: str, duration_ms: float, **kwargs: Any):
        """Record the latency of a specific operation."""
        logger.event(
            "telemetry.latency",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )

    @staticmethod
    def record_resource_usage(resource_type: str, value: float, unit: str, **kwargs: Any):
        """Record the usage of a system resource."""
        logger.event(
            "telemetry.resource",
            resource_type=resource_type,
            value=value,
            unit=unit,
            **kwargs
        )

    @staticmethod
    def record_error(error_type: str, error_code: Optional[str] = None, **kwargs: Any):
        """Record a non-exception error event."""
        logger.event(
            "telemetry.error",
            error_type=error_type,
            error_code=error_code,
            **kwargs
        )
