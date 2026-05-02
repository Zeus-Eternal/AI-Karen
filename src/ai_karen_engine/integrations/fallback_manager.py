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
        raise FallbackManagerDeprecatedError(
            "Legacy integrations fallback manager is disabled. Use core.expression.ExpressionGateway + builtin provider engine."
        )

    def execute_fallback(self, request: Any, fallback_chain: List[str]) -> FallbackResult:
        raise FallbackManagerDeprecatedError(
            "Legacy integrations fallback execution is disabled. Use core.expression.ExpressionGateway."
        )

    def start_recovery_monitoring(self) -> None:
        raise FallbackManagerDeprecatedError("Legacy recovery monitoring is disabled.")

    def stop_recovery_monitoring(self) -> None:
        raise FallbackManagerDeprecatedError("Legacy recovery monitoring is disabled.")

    def activate_degraded_mode(self, request: Any) -> Optional[Dict[str, Any]]:
        raise FallbackManagerDeprecatedError("Legacy degraded-mode activation is disabled.")


class FallbackManagerDeprecatedError(RuntimeError):
    """Raised whenever deprecated integrations fallback manager is invoked."""


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
