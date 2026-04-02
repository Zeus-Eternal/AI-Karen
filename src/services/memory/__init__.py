import importlib
import logging
import sys
from typing import Any

__all__ = [
    "UnifiedMemoryService",
    "NeuroVaultIntegrationService",
    "MemoryPolicy",
    "MemoryWritebackSystem",
    "get_database_health_checker",
    "OverallHealthStatus",
]


def __getattr__(name: str) -> Any:
    """Lazily expose public memory services to avoid import cycles."""
    if name == "UnifiedMemoryService":
        from .unified_memory_service import UnifiedMemoryService

        return UnifiedMemoryService
    if name == "NeuroVaultIntegrationService":
        from .neurovault_integration_service import NeuroVaultIntegrationService

        return NeuroVaultIntegrationService
    if name == "MemoryPolicy":
        from .internal.memory_policy import MemoryPolicy

        return MemoryPolicy
    if name == "MemoryWritebackSystem":
        from .internal.memory_writeback import MemoryWritebackSystem

        return MemoryWritebackSystem
    
    # Static imports for IDE support
    if name == "get_database_health_checker":
        from .internal.database_health_checker import get_database_health_checker
        return get_database_health_checker
    
    if name == "OverallHealthStatus":
        from .internal.database_health_checker import OverallHealthStatus
        return OverallHealthStatus
        
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
