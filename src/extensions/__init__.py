"""
AI Karen Extensions System - Core Infrastructure

This module provides the foundation for the modular extensions system,
enabling developers to build feature-rich extensions that integrate
seamlessly with the core AI Karen platform. Runtime primitives live in
`ai_karen_engine.extensions`; this package orchestrates them for CLI and
FastAPI integrations.
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
