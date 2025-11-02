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

# Import from core framework
from .core import (
    ExtensionManager,
    BaseExtension,
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
    ExtensionContext,
    ExtensionCapabilities,
    ExtensionDependencies,
    ExtensionPermissions,
    ExtensionResources,
    ExtensionRegistry,
    ExtensionAPIIntegration,
    BackgroundTaskManager,
    ExtensionSecurityManager,
    require_permission,
    audit_log,
    security_monitor
)

# Backward compatibility - maintain old import paths
# These imports allow existing code to continue working
from .core.manager import ExtensionManager as _ExtensionManager
from .core.base import BaseExtension as _BaseExtension
from .core.models import ExtensionManifest as _ExtensionManifest
from .core.models import ExtensionRecord as _ExtensionRecord
from .core.models import ExtensionStatus as _ExtensionStatus
from .core.api_integration import ExtensionAPIIntegration as _ExtensionAPIIntegration
from .core.registry import ExtensionRegistry as _ExtensionRegistry

__all__ = [
    "ExtensionManager",
    "BaseExtension", 
    "ExtensionManifest",
    "ExtensionRecord",
    "ExtensionStatus",
    "ExtensionContext",
    "ExtensionCapabilities",
    "ExtensionDependencies",
    "ExtensionPermissions",
    "ExtensionResources",
    "ExtensionAPIIntegration",
    "ExtensionRegistry",
    "BackgroundTaskManager",
    "ExtensionSecurityManager",
    "require_permission",
    "audit_log",
    "security_monitor"
]
