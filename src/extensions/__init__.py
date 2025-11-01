"""
AI Karen Extensions System - Core Infrastructure

This module provides the foundation for the modular extensions system,
enabling developers to build feature-rich extensions that integrate
seamlessly with the core AI Karen platform.

The extension system is organized as follows:
- core/: Extension framework code (managers, base classes, utilities)
- docs/: Comprehensive documentation for extension development
- Extension implementations are located in /extensions/ directory

This module maintains backward compatibility by re-exporting core components.
"""

# Import from core framework (will be available after task 2 is completed)
from .manager import ExtensionManager
from .base import BaseExtension
from .models import ExtensionManifest, ExtensionRecord, ExtensionStatus
from .api_integration import ExtensionAPIIntegration
from .registry import ExtensionRegistry

# Future imports from core/ (will be activated in task 2)
# from .core import (
#     ExtensionManager,
#     BaseExtension,
#     ExtensionManifest,
#     ExtensionRecord,
#     ExtensionStatus,
#     ExtensionRegistry
# )

__all__ = [
    "ExtensionManager",
    "BaseExtension", 
    "ExtensionManifest",
    "ExtensionRecord",
    "ExtensionStatus",
    "ExtensionAPIIntegration",
    "ExtensionRegistry"
]
