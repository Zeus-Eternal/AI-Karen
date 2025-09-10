# mypy: ignore-errors
"""
Metrics configuration for Kari FastAPI Server.
Handles Prometheus setup, counters, and metrics manager integration.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger("kari")

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        Counter,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_ENABLED = True
except ImportError:
    PROMETHEUS_ENABLED = False
    logger.warning("Prometheus client not available, metrics disabled")

# Initialize metrics using the enhanced metrics manager
from ai_karen_engine.core.metrics_manager import get_metrics_manager


def initialize_metrics() -> Dict[str, Any]:
    """Initialize HTTP metrics using the safe metrics manager."""
    manager = get_metrics_manager()
    
    metrics = {}
    with manager.safe_metrics_context():
        metrics['REQUEST_COUNT'] = manager.register_counter(
            "kari_http_requests_total",
            "Total HTTP requests",
            ["method", "path", "status"]
        )
        metrics['REQUEST_LATENCY'] = manager.register_histogram(
            "kari_http_request_duration_seconds",
            "HTTP request latency",
            ["method", "path"]
        )
        metrics['ERROR_COUNT'] = manager.register_counter(
            "kari_http_errors_total",
            "Total HTTP errors",
            ["method", "path", "error_type"]
        )
    
    return metrics


# Initialize metrics safely
_http_metrics = initialize_metrics()
REQUEST_COUNT = _http_metrics['REQUEST_COUNT']
REQUEST_LATENCY = _http_metrics['REQUEST_LATENCY']
ERROR_COUNT = _http_metrics['ERROR_COUNT']