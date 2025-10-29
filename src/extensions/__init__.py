"""
AI Karen Extensions System - Core Infrastructure

This module provides the foundation for the modular extensions system,
enabling developers to build feature-rich extensions that integrate
seamlessly with the core AI Karen platform.
"""

from .manager import ExtensionManager
from .base import BaseExtension
from .models import ExtensionManifest, ExtensionRecord, ExtensionStatus
from .api_integration import ExtensionAPIIntegration
from .registry import ExtensionRegistry

__all__ = [
    "ExtensionManager",
    "BaseExtension", 
    "ExtensionManifest",
    "ExtensionRecord",
    "ExtensionStatus",
    "ExtensionAPIIntegration",
    "ExtensionRegistry"
]