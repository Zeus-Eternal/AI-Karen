"""
Kari AI Extensions System

The Extensions system provides a higher-level architecture above Kari's plugin system,
enabling developers to build substantial, feature-rich modules that can compose multiple
plugins, provide rich UIs, manage their own data, and be distributed through a marketplace.
"""

from .manager import ExtensionManager, get_extension_manager, initialize_extension_manager
from .base import BaseExtension
from .models import ExtensionManifest, ExtensionRecord, ExtensionStatus
from .registry import ExtensionRegistry
from .orchestrator import PluginOrchestrator
from .data_manager import ExtensionDataManager
from .validator import ExtensionValidator, validate_extension_manifest
from .dependency_resolver import DependencyResolver
from .resource_monitor import ResourceMonitor, ExtensionHealthChecker

__all__ = [
    "ExtensionManager",
    "get_extension_manager",
    "initialize_extension_manager",
    "BaseExtension",
    "ExtensionManifest",
    "ExtensionRecord", 
    "ExtensionStatus",
    "ExtensionRegistry",
    "PluginOrchestrator",
    "ExtensionDataManager",
    "ExtensionValidator",
    "validate_extension_manifest",
    "DependencyResolver",
    "ResourceMonitor",
    "ExtensionHealthChecker",
]