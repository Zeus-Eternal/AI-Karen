"""
Fallback Mechanisms — Backward Compatibility Shim.

Fallback logic is now centralized in ChatRuntimeControlPlane.
This module preserves the public API surface for any remaining consumers.

# MIGRATION NOTE: Tracked for removal in cleanup phase.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackType(Enum):
    LOCAL_MODEL = "local_model"
    CACHED_RESPONSE = "cached_response"
    TEMPLATE_RESPONSE = "template_response"
    ERROR_MESSAGE = "error_message"


class FallbackManager:
    """Shim — delegates to ChatRuntimeControlPlane."""

    def __init__(self, *args, **kwargs):
        logger.debug("[Shim] FallbackManager instantiated (delegating to control plane)")

    async def get_fallback_response(self, request: Any) -> Dict[str, Any]:
        return {
            "response": "Service is temporarily operating with limited capabilities.",
            "fallback_type": FallbackType.TEMPLATE_RESPONSE.value,
        }


_fallback_manager: Optional[FallbackManager] = None


def get_fallback_manager() -> FallbackManager:
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackManager()
    return _fallback_manager
