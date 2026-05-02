# mypy: ignore-errors
"""
Logging configuration for Kari FastAPI Server.
Handles logging setup, filters, and uvicorn integration.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict

from .config import settings

_LOGGING_CONFIGURED = False


class _DedupFilter(logging.Filter):
    """Filter that drops immediate duplicate log records within a short window."""

    def __init__(self, window_seconds: float = 0.75):
        super().__init__(name="")
        self.window = window_seconds
        self._last_key: tuple | None = None
        self._last_ts: float = 0.0

    def filter(self, record: logging.LogRecord) -> bool:  # True = keep
        try:
            import time as _time

            key = (record.name, record.levelno, record.getMessage())
            now = _time.time()
            if self._last_key == key and (now - self._last_ts) <= self.window:
                return False
            self._last_key = key
            self._last_ts = now
        except Exception:
            return True
        return True


def configure_logging() -> None:
    """Configure production-grade logging using the centralized system."""
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    from ai_karen_engine.core.logging import configure_runtime_logging
    configure_runtime_logging()

    _LOGGING_CONFIGURED = True


def apply_uvicorn_filters() -> None:
    """Apply uvicorn-specific logging filters to reduce noise"""
    # Ensure auth audit/monitoring loggers are INFO, non-propagating, and not duplicated
    try:
        logging.getLogger("ai_karen_engine.auth.security.audit").setLevel(logging.INFO)
        logging.getLogger("ai_karen_engine.auth.security.audit").propagate = False
        logging.getLogger("ai_karen_engine.auth.monitoring.AuthMonitor").setLevel(
            logging.INFO
        )
        logging.getLogger(
            "ai_karen_engine.auth.monitoring.AuthMonitor"
        ).propagate = False
    except Exception:
        pass


# Initialize logging and create logger instance
configure_logging()
logger = logging.getLogger("kari")
