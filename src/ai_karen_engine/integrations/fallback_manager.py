"""Legacy fallback manager - REMOVED.

Canonical fallback ownership lives in:
- `ai_karen_engine.services.models.routing.llm_router_service`
- `ai_karen_engine.core.runtime.resilience`
- `ai_karen_engine.core.runtime.degraded_mode`

This module exists only to raise clear errors for code attempting to use the removed legacy system.
"""

from __future__ import annotations


class FallbackManagerRemovedError(Exception):
    """Raised when code attempts to use the removed legacy fallback manager.

    The legacy integrations fallback manager has been removed in favor of:
    1. ExpressionGateway for expression generation
    2. LLMRouter for provider routing
    3. Runtime resilience fallback_manager for runtime-level fallbacks

    Code should use ExpressionGateway for all expression generation tasks.
    """

    pass


def get_fallback_manager():
    """Factory function that raises error to prevent legacy fallback manager usage.

    Raises:
        FallbackManagerRemovedError: Always, as this module is removed.
    """
    raise FallbackManagerRemovedError(
        "Legacy FallbackManager has been removed. "
        "Use ExpressionGateway for expression generation. "
        "See ai_karen_engine.core.expression.gateway.ExpressionGateway"
    )


# All other classes/functions removed to prevent accidental usage
__all__ = ["FallbackManagerRemovedError", "get_fallback_manager"]
