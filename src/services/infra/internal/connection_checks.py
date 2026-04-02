"""
Shared connection validation helpers for infra connection managers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional


class ConnectionValidator:
    """Basic async validator for database-style connections."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    async def validate(self, connection: Any) -> bool:
        if connection is None:
            return False

        health_check = getattr(connection, "health_check", None)
        if callable(health_check):
            try:
                result = health_check()
                if hasattr(result, "__await__"):
                    result = await result
                if isinstance(result, dict):
                    return bool(result.get("healthy", result.get("status") in ("healthy", "ok")))
                return bool(result)
            except Exception as exc:
                self.logger.warning("Connection validation failed: %s", exc)
                return False

        closed = getattr(connection, "closed", None)
        if isinstance(closed, bool):
            return not closed

        return True


class ModelConnectionValidator(ConnectionValidator):
    """Validator specialized for model-provider connections."""

    async def validate(self, connection: Any) -> bool:
        if not await super().validate(connection):
            return False

        if connection is None:
            return False

        ready = getattr(connection, "is_ready", None)
        if callable(ready):
            try:
                result = ready()
                if hasattr(result, "__await__"):
                    result = await result
                return bool(result)
            except Exception as exc:
                self.logger.warning("Model connection readiness check failed: %s", exc)
                return False

        return True
