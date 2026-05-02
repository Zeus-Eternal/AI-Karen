"""Compatibility shim for legacy integrations fallback manager.

Deprecated: canonical fallback ownership lives in:
- `ai_karen_engine.services.models.routing.llm_router_service`
- `ai_karen_engine.core.runtime.resilience`
- `ai_karen_engine.core.runtime.degraded_mode`
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ai_karen_engine.core.runtime.resilience.fallback_manager import (
    get_fallback_manager as get_resilience_fallback_manager,
)
from ai_karen_engine.core.runtime.degraded_mode import (
    DegradedModeReason,
    get_degraded_mode_manager,
)

logger = logging.getLogger("kari.fallback_manager")


class FallbackReason(Enum):
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    UNKNOWN_ERROR = "unknown_error"


class FallbackStrategy(Enum):
    RUNTIME_SWITCH = "runtime_switch"
    EMERGENCY_DEGRADED = "emergency_degraded"


@dataclass
class FallbackAttempt:
    provider: str
    runtime: str
    model: str
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class FallbackResult:
    success: bool
    used_provider: Optional[str]
    used_runtime: Optional[str]
    used_model: Optional[str]
    attempts: List[FallbackAttempt]
    final_error: Optional[str]
    degraded_mode_activated: bool
    total_time: float
    strategy_used: Optional[FallbackStrategy] = None
    recovery_suggestions: List[str] = field(default_factory=list)


class FallbackManager:
    """Legacy facade that intentionally defers fallback ownership to canonical runtime/router."""

    def __init__(self, registry=None, router=None):
        self.registry = registry
        self.router = router
        self._resilience = get_resilience_fallback_manager()

    def construct_fallback_chain(self, request: Any, failed_providers: List[str]) -> List[str]:
        logger.info("Legacy integrations fallback chain disabled; using router-owned fallback chain")
        return []

    def execute_fallback(self, request: Any, fallback_chain: List[str]) -> FallbackResult:
        logger.warning("Legacy integrations fallback execution is disabled; rely on router/runtime fallback")
        return FallbackResult(
            success=False,
            used_provider=None,
            used_runtime=None,
            used_model=None,
            attempts=[],
            final_error="legacy_fallback_manager_disabled",
            degraded_mode_activated=False,
            total_time=0.0,
            strategy_used=FallbackStrategy.EMERGENCY_DEGRADED,
            recovery_suggestions=["Use canonical router/runtime fallback path"],
        )

    def start_recovery_monitoring(self) -> None:
        logger.info("Legacy recovery monitoring disabled; canonical monitoring is runtime-owned")

    def stop_recovery_monitoring(self) -> None:
        logger.info("Legacy recovery monitoring disabled; canonical monitoring is runtime-owned")

    def activate_degraded_mode(self, request: Any) -> Optional[Dict[str, Any]]:
        manager = get_degraded_mode_manager()
        if not manager:
            return None
        status = manager.activate_degraded_mode(
            reason=DegradedModeReason.ALL_PROVIDERS_FAILED,
            context={"source": "legacy_fallback_manager_shim"},
        )
        if not getattr(status, "is_active", False):
            return None
        return {
            "provider": "degraded_mode",
            "runtime": "degraded_mode",
            "model_id": "degraded_mode",
            "confidence": 0.1,
        }


def get_fallback_manager(registry=None, router=None) -> FallbackManager:
    return FallbackManager(registry=registry, router=router)


__all__ = [
    "FallbackReason",
    "FallbackStrategy",
    "FallbackAttempt",
    "FallbackResult",
    "FallbackManager",
    "get_fallback_manager",
]
