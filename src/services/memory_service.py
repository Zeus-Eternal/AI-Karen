"""Compatibility shim for web UI memory services."""

from services.memory.memory_service import (
    MemoryType,
    UISource,
    WebUIMemoryEntry,
    WebUIMemoryQuery,
    WebUIMemoryService,
)

__all__ = [
    "MemoryType",
    "UISource",
    "WebUIMemoryEntry",
    "WebUIMemoryQuery",
    "WebUIMemoryService",
]
