"""
Kari AI Extensions System

The Extensions system provides a higher-level architecture above Kari's plugin system,
enabling developers to build substantial, feature-rich modules that can compose multiple
plugins, provide rich UIs, manage their own data, and be distributed through a marketplace.
"""

from ai_karen_engine.extensions.manager import ExtensionManager, get_extension_manager, initialize_extension_manager
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionRecord, ExtensionStatus
from ai_karen_engine.extensions.registry import ExtensionRegistry
from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
from ai_karen_engine.extensions.data_manager import ExtensionDataManager
from ai_karen_engine.extensions.validator import ExtensionValidator, validate_extension_manifest
from ai_karen_engine.extensions.dependency_resolver import DependencyResolver
from ai_karen_engine.extensions.resource_monitor import ResourceMonitor, ExtensionHealthChecker

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
