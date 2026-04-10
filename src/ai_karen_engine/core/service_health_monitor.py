"""
Service Health Monitor — Backward Compatibility Shim.

Dependency health monitoring is now centralized in ChatRuntimeControlPlane
via real dependency probes (PostgreSQL, Redis, ChatOrchestrator, etc.).
This module preserves the public API surface for any remaining consumers.

# MIGRATION NOTE: Tracked for removal in cleanup phase.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .error_recovery_manager import ErrorRecoveryManager, ServiceStatus

logger = logging.getLogger(__name__)


class ServiceHealthMonitor:
    """Shim — delegates to ChatRuntimeControlPlane."""

    def __init__(self, *args, **kwargs):
        logger.debug("[Shim] ServiceHealthMonitor instantiated (delegating to control plane)")

    async def check_health(self, service_name: str) -> Dict[str, Any]:
        return {"service": service_name, "status": "delegated_to_control_plane"}


_service_health_monitor: Optional[ServiceHealthMonitor] = None


def get_service_health_monitor() -> ServiceHealthMonitor:
    global _service_health_monitor
    if _service_health_monitor is None:
        _service_health_monitor = ServiceHealthMonitor()
    return _service_health_monitor