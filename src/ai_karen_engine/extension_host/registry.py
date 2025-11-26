"""
Extension Registry - Manages registration and lookup of extensions.

This module handles the registration of extensions by hook point and provides
methods for discovering and retrieving extensions that implement specific hooks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import ExtensionBase, ExtensionManifest, HookPoint
from .errors import ExtensionRegistryError, ExtensionNotFoundError

logger = logging.getLogger(__name__)


class ExtensionRegistry:
    """
    Registry for managing extensions and their hook implementations.
    
    Handles:
    - Registration of extensions by hook point
    - Discovery of extensions for specific hooks
    - Dependency resolution between extensions
    - Extension lifecycle management
    """
    
    def __init__(self, 
                 plugin_registry: Optional[Any] = None,
                 service_registry: Optional[Any] = None):
        """
        Initialize the extension registry.
        
        Args:
            plugin_registry: Optional pre-configured plugin registry instance.
            service_registry: Optional pre-configured service registry instance.
        """
        self.extensions: Dict[str, Any] = {}
        self.logger = logging.getLogger("extension.registry")
        self._plugin_registry = plugin_registry
        self._service_registry = service_registry
        
        # Registry storage
        self._hook_registry: Dict[HookPoint, List[str]] = {
            hook_point: [] for hook_point in HookPoint
        }
        self._extension_dependencies: Dict[str, Any] = {}
    
    def register_extension(
        self, 
        manifest: ExtensionManifest,
        instance: Any,
        directory: str
    ) -> Any:
        """
        Register a new extension in the registry.
        
        Args:
            manifest: Extension manifest
            instance: Extension instance
            directory: Extension directory path
            
        Returns:
            ExtensionRecord for the registered extension
        """
        # Create a simple record for the extension
        record = {
            "manifest": manifest,
            "instance": instance,
            "status": "loading",
            "directory": Path(directory),
            "loaded_at": datetime.now(timezone.utc),
        }
        
        # Store the extension
        self.extensions[manifest.name] = record
        
        # Register by hook points
        for hook_point in manifest.hook_points:
            try:
                hook_point_enum = HookPoint(hook_point)
                if manifest.name not in self._hook_registry[hook_point_enum]:
                    self._hook_registry[hook_point_enum].append(manifest.name)
            except ValueError:
                logger.warning(f"Extension {manifest.name} has unknown hook point: {hook_point}")
        
        # Register dependencies
        dependencies = set(manifest.dependencies or [])
        self._extension_dependencies[manifest.name] = dependencies
        
        self.logger.info(f"Registered extension {manifest.name} v{manifest.version}")
        
        return record
    
    def unregister_extension(self, name: str) -> bool:
        """
        Unregister an extension from the registry.
        
        Args:
            name: Extension name
            
        Returns:
            True if extension was unregistered, False if not found
        """
        if name not in self.extensions:
            logger.warning(f"Cannot unregister extension {name}: not found in registry")
            return False
        
        # Remove from hook registry
        for hook_point, extensions in self._hook_registry.items():
            if name in extensions:
                extensions.remove(name)
        
        # Remove from dependencies
        if name in self._extension_dependencies:
            del self._extension_dependencies[name]
        
        # Remove from other extensions' dependencies
        for ext_name, dependencies in self._extension_dependencies.items():
            if name in dependencies:
                dependencies.remove(name)
        
        # Remove the extension
        del self.extensions[name]
        
        self.logger.info(f"Unregistered extension {name}")
        return True
    
    def get_extension(self, name: str) -> Optional[Any]:
        """
        Get extension record by name.
        
        Args:
            name: Extension name
            
        Returns:
            ExtensionRecord if found, None otherwise
        """
        return self.extensions.get(name)
    
    def get_extensions_for_hook(self, hook_point: HookPoint) -> List[Any]:
        """
        Get all extensions that implement a specific hook point.
        
        Args:
            hook_point: The hook point to get extensions for
            
        Returns:
            List of extension instances that implement the hook
        """
        if hook_point not in self._hook_registry:
            return []
        
        extension_names = self._hook_registry[hook_point]
        extensions = []
        
        for name in extension_names:
            try:
                record = self.get_extension(name)
                if record:
                    extensions.append(record["instance"])
            except Exception:
                logger.warning(f"Extension {name} registered for hook {hook_point} but not found in registry")
                # Remove from registry
                self._hook_registry[hook_point].remove(name)
        
        return extensions
    
    def list_extensions(self, status_filter: Optional[str] = None) -> List[Any]:
        """
        List all registered extensions.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of ExtensionRecord instances
        """
        extensions = list(self.extensions.values())
        
        if status_filter:
            extensions = [ext for ext in extensions if ext.get("status") == status_filter]
        
        return extensions
    
    def get_all_extensions(self) -> Dict[str, Any]:
        """
        Get all registered extensions.
        
        Returns:
            Dictionary mapping extension names to extension records
        """
        return self.extensions.copy()
    
    def is_extension_registered(self, extension_name: str) -> bool:
        """
        Check if an extension is registered.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            True if registered, False otherwise
        """
        return extension_name in self.extensions
    
    def update_status(self, name: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update extension status.
        
        Args:
            name: Extension name
            status: New status
            error_message: Optional error message
            
        Returns:
            True if status was updated, False if extension not found
        """
        if name in self.extensions:
            self.extensions[name]["status"] = status
            if error_message:
                self.extensions[name]["error_message"] = error_message
            self.logger.info(f"Updated extension {name} status to {status}")
            return True
        return False
    
    def get_active_extensions(self) -> List[Any]:
        """Get all active extensions."""
        return self.list_extensions("active")
    
    def get_extension_count(self) -> int:
        """Get total number of registered extensions."""
        return len(self.extensions)
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of extension statuses.
        
        Returns:
            Dictionary with status counts
        """
        summary = {}
        for extension in self.extensions.values():
            status = extension.get("status", "unknown")
            summary[status] = summary.get(status, 0) + 1
        
        return summary
    
    def enable_extension(self, extension_name: str) -> bool:
        """
        Enable an extension.
        
        Args:
            extension_name: Name of the extension to enable
            
        Returns:
            True if successfully enabled, False otherwise
        """
        try:
            record = self.get_extension(extension_name)
            if record and "instance" in record:
                record["instance"].enabled = True
                self.update_status(extension_name, "active")
                self.logger.info(f"Enabled extension {extension_name}")
                return True
        except Exception:
            pass
        
        self.logger.warning(f"Cannot enable extension {extension_name}: not found in registry")
        return False
    
    def disable_extension(self, extension_name: str) -> bool:
        """
        Disable an extension.
        
        Args:
            extension_name: Name of the extension to disable
            
        Returns:
            True if successfully disabled, False otherwise
        """
        try:
            record = self.get_extension(extension_name)
            if record and "instance" in record:
                record["instance"].enabled = False
                self.update_status(extension_name, "inactive")
                self.logger.info(f"Disabled extension {extension_name}")
                return True
        except Exception:
            pass
        
        self.logger.warning(f"Cannot disable extension {extension_name}: not found in registry")
        return False
    
    def is_extension_enabled(self, extension_name: str) -> bool:
        """
        Check if an extension is enabled.
        
        Args:
            extension_name: Name of the extension to check
            
        Returns:
            True if enabled, False otherwise
        """
        try:
            record = self.get_extension(extension_name)
            if record and "instance" in record:
                return record["instance"].enabled
        except Exception:
            pass
        return False
    
    def get_hook_points(self) -> List[HookPoint]:
        """
        Get all available hook points.
        
        Returns:
            List of all hook points
        """
        return list(HookPoint)
    
    def get_extensions_by_hook_point(self) -> Dict[HookPoint, List[str]]:
        """
        Get a mapping of hook points to extension names.
        
        Returns:
            Dictionary mapping hook points to lists of extension names
        """
        result = {}
        
        for hook_point, extension_names in self._hook_registry.items():
            result[hook_point] = extension_names.copy()
        
        return result
    
    def check_dependencies(self, manifest: ExtensionManifest) -> Dict[str, bool]:
        """
        Check if extension dependencies are satisfied.
        
        Args:
            manifest: Extension manifest to check
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        dependency_status: Dict[str, bool] = {}

        # Check extension dependencies
        for dep in manifest.dependencies:
            dep_name = dep
            if "@" in dep:
                dep_name, _ = dep.split("@", 1)
            
            is_available = dep_name in self.extensions
            dependency_status[f"extension:{dep}"] = is_available

        return dependency_status
    
    def get_dependent_extensions(self, extension_name: str) -> List[str]:
        """
        Get extensions that depend on the specified extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            List of extension names that depend on the specified extension
        """
        dependents = []
        
        for ext_name, dependencies in self._extension_dependencies.items():
            if extension_name in dependencies:
                dependents.append(ext_name)
        
        return dependents
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert registry to dictionary for serialization.
        
        Returns:
            Dictionary representation of the registry
        """
        return {
            "extensions": {
                name: {
                    "name": record["manifest"].name,
                    "version": record["manifest"].version,
                    "status": record.get("status", "unknown"),
                    "directory": str(record.get("directory", "")),
                    "loaded_at": record.get("loaded_at", "").isoformat() if record.get("loaded_at") else None,
                } 
                for name, record in self.extensions.items()
            },
            "summary": self.get_status_summary(),
            "total_count": self.get_extension_count()
        }


__all__ = ["ExtensionRegistry"]