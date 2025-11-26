"""
Extensions module for the AI Karen Engine.

This module contains the legacy extension system components that are being
migrated to the new two-tier extension architecture.
"""

from .base import BaseExtension
from .models import (
    ExtensionContext,
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
)
from .registry import ExtensionRegistry

# Lazy imports to avoid circular dependency
def get_extension_manager():
    """Lazy import to avoid circular dependency."""
    from ai_karen_engine.extension_host import get_extension_manager as _get_extension_manager
    return _get_extension_manager()

def initialize_extension_manager(*args, **kwargs):
    """Lazy import to avoid circular dependency."""
    from ai_karen_engine.extension_host import initialize_extension_manager as _initialize_extension_manager
    return _initialize_extension_manager(*args, **kwargs)

__all__ = [
    "BaseExtension",
    "ExtensionContext",
    "ExtensionManifest",
    "ExtensionRecord",
    "ExtensionStatus",
    "ExtensionRegistry",
    "get_extension_manager",
    "initialize_extension_manager",
]
