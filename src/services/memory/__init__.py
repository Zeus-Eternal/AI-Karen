"""
Memory & Cognitive Services

This package contains memory and cognitive services for the Kari platform.
"""

from typing import Any

__all__ = [
    "UnifiedMemoryService",
    "NeuroVaultIntegrationService",
    "MemoryPolicy",
    "MemoryWritebackSystem",
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
