from __future__ import annotations

from functools import lru_cache
from typing import Any

from ai_karen_engine.services.database.database_connection_manager import (
    DatabaseConfig,
    DatabaseConnectionManager,
)


@lru_cache()
def get_database_manager(config: Any | None = None) -> DatabaseConnectionManager:
    if config is None:
        config = {}
    if hasattr(config, "model_dump"):
        config = config.model_dump()
    elif hasattr(config, "__dict__") and not isinstance(config, dict):
        config = dict(config.__dict__)
    return DatabaseConnectionManager(config)


__all__ = ["DatabaseConfig", "DatabaseConnectionManager", "get_database_manager"]
