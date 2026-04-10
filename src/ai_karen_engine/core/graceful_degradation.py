"""
Graceful Degradation — Backward Compatibility Shim.

Degradation orchestration is now managed by ChatRuntimeControlPlane.
This module preserves the public API surface for any remaining consumers.

# MIGRATION NOTE: Tracked for removal in cleanup phase.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .error_recovery_manager import ErrorRecoveryManager, ServiceStatus
from .fallback_mechanisms import FallbackManager, FallbackType

logger = logging.getLogger(__name__)


class GracefulDegradationCoordinator:
    """Shim — delegates to ChatRuntimeControlPlane."""

    def __init__(self, *args, **kwargs):
        logger.debug("[Shim] GracefulDegradationCoordinator instantiated")

    async def handle_degradation(self, service_name: str) -> Dict[str, Any]:
        return {"status": "delegated_to_control_plane"}


_coordinator: Optional[GracefulDegradationCoordinator] = None


def get_graceful_degradation_coordinator() -> GracefulDegradationCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = GracefulDegradationCoordinator()
    return _coordinator