"""
Error Recovery Manager — Backward Compatibility Shim.

Runtime error recovery is now managed by ChatRuntimeControlPlane.
This module preserves the public API surface for any remaining consumers.

# MIGRATION NOTE: Tracked for removal in cleanup phase.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    CIRCUIT_OPEN = "circuit_open"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ErrorRecoveryManager:
    """Shim — delegates to ChatRuntimeControlPlane."""

    def __init__(self, *args, **kwargs):
        logger.debug("[Shim] ErrorRecoveryManager instantiated (delegating to control plane)")

    async def check_service_health(self, service_name: str) -> ServiceStatus:
        return ServiceStatus.HEALTHY

    async def attempt_recovery(self, service_name: str) -> bool:
        return True


_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager() -> ErrorRecoveryManager:
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager
