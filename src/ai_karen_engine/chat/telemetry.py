"""
Telemetry utilities for stage-by-stage latency tracking.
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, Any

logger = logging.getLogger(__name__)


@contextmanager
def track_latency(stage_name: str, correlation_id: str):
    """Context manager to track stage latency."""
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.info(
            f"Stage latency: {stage_name} | "
            f"correlation_id={correlation_id} | "
            f"duration_ms={duration_ms:.2f}"
        )
