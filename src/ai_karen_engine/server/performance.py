from __future__ import annotations

import logging
from typing import Any

from ai_karen_engine.config.performance_config import PerformanceConfig

logger = logging.getLogger(__name__)


def load_performance_settings(settings: Any) -> PerformanceConfig:
    """Load performance settings and optionally mirror them onto server settings."""
    config = PerformanceConfig.from_environment()

    if settings is not None:
        for key, value in config.to_dict().items():
            if hasattr(settings, key):
                try:
                    setattr(settings, key, value)
                except Exception:
                    logger.debug("Unable to set %s on settings", key, exc_info=True)

    return config


__all__ = ["load_performance_settings"]
