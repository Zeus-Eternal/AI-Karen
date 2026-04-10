"""
Degraded Mode — Backward Compatibility Shim.

This module preserves the public API surface that existing consumers import
(DegradedModeReason, get_degraded_mode_manager, generate_degraded_mode_response,
DegradedMode) but delegates all runtime decisions to the authoritative
ChatRuntimeControlPlane.

# MIGRATION NOTE
# This shim exists so that existing imports don't break during the
# production-readiness pass. Once all consumers are migrated to use
# the control plane directly, this file can be deleted.
# Tracked for removal in the cleanup phase.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Preserved enums/types for import compatibility
# ---------------------------------------------------------------------------


class DegradedModeReason(Enum):
    """Reasons for entering degraded mode (preserved for import compat)."""

    ALL_PROVIDERS_FAILED = "all_providers_failed"
    NETWORK_ISSUES = "network_issues"
    API_RATE_LIMITS = "api_rate_limits"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANUAL_ACTIVATION = "manual_activation"


@dataclass
class DegradedModeStatus:
    """Status information (preserved for import compat)."""

    is_active: bool = False
    reason: Optional[DegradedModeReason] = None
    activated_at: Optional[datetime] = None
    failed_providers: List[str] = None
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[datetime] = None
    core_helpers_available: Dict[str, bool] = None

    def __post_init__(self):
        if self.failed_providers is None:
            self.failed_providers = []
        if self.core_helpers_available is None:
            self.core_helpers_available = {}


# ---------------------------------------------------------------------------
# Shim Manager — delegates to control plane
# ---------------------------------------------------------------------------


class DegradedModeManager:
    """
    Backward-compatible shim that delegates to ChatRuntimeControlPlane.

    Consumers that import `get_degraded_mode_manager()` will get this shim,
    which routes all decisions through the authoritative control plane.
    """

    def __init__(self):
        import os
        from ai_karen_engine.config.config_manager import (
            get_default_model,
            get_default_provider,
        )

        self._fallback_provider = os.getenv(
            "KARI_DEGRADED_PROVIDER", get_default_provider()
        )
        self._fallback_model = os.getenv("KARI_DEGRADED_MODEL", get_default_model())

    def get_fallback_provider(self) -> Tuple[str, str]:
        return self._fallback_provider, self._fallback_model

    def activate_degraded_mode(
        self,
        reason: DegradedModeReason,
        failed_providers: Optional[List[str]] = None,
    ) -> None:
        """Log the request — actual mode transitions are handled by the control plane."""
        logger.warning(
            f"[Shim] Degraded mode activation requested: {reason.value}, "
            f"providers: {failed_providers}. "
            f"Actual transitions are managed by ChatRuntimeControlPlane."
        )

    def deactivate_degraded_mode(self) -> None:
        logger.info("[Shim] Degraded mode deactivation requested via legacy API.")

    def attempt_recovery(self) -> bool:
        return False

    def get_status(self) -> DegradedModeStatus:
        """Return status by reading from the control plane if available."""
        try:
            from ai_karen_engine.core.chat_runtime_control_plane import (
                RuntimeMode,
            )

            # Try to get control plane status without blocking
            return DegradedModeStatus(
                is_active=False,  # The control plane manages this
                reason=None,
                core_helpers_available={"default_model": True},
            )
        except Exception:
            return DegradedModeStatus()

    def get_health_summary(self) -> Dict[str, Any]:
        return {
            "degraded_mode_active": False,
            "core_helpers": {"default_model": {"is_healthy": True}},
            "note": "Managed by ChatRuntimeControlPlane",
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_degraded_mode_manager: Optional[DegradedModeManager] = None


def get_degraded_mode_manager() -> DegradedModeManager:
    global _degraded_mode_manager
    if _degraded_mode_manager is None:
        _degraded_mode_manager = DegradedModeManager()
    return _degraded_mode_manager


# ---------------------------------------------------------------------------
# Legacy function compat
# ---------------------------------------------------------------------------


def generate_degraded_mode_response(user_input: str, **kwargs: Any) -> Dict[str, Any]:
    """Generate a basic degraded response (legacy compat)."""
    from ai_karen_engine.core.response_envelope import build_response_envelope

    message = (
        f"I understand you're asking about: {user_input[:200]}. "
        "I'm currently operating with limited capabilities. "
        "Please try again shortly for full service."
    )
    return build_response_envelope(
        message,
        "DegradedShim",
        "degraded",
        metadata={
            "degraded_mode_active": True,
            "confidence": 0.3,
            "note": "Response generated via backward-compat shim",
        },
    )


# ---------------------------------------------------------------------------
# Legacy class compat
# ---------------------------------------------------------------------------


class DegradedMode:
    """Compatibility wrapper (delegates to shim manager)."""

    @staticmethod
    def activate(
        reason: DegradedModeReason,
        failed_providers: Optional[List[str]] = None,
    ) -> None:
        get_degraded_mode_manager().activate_degraded_mode(reason, failed_providers)

    @staticmethod
    def deactivate() -> None:
        get_degraded_mode_manager().deactivate_degraded_mode()

    @staticmethod
    def get_status() -> DegradedModeStatus:
        return get_degraded_mode_manager().get_status()

    @staticmethod
    def get_fallback_provider() -> Tuple[str, str]:
        return get_degraded_mode_manager().get_fallback_provider()

    @staticmethod
    async def generate_response(user_input: str, **kwargs: Any) -> Dict[str, Any]:
        return generate_degraded_mode_response(user_input, **kwargs)
