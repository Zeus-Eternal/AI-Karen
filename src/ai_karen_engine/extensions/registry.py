"""
Extension registry for tracking installed extensions.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionRecord, ExtensionStatus


class ExtensionRegistry:
    """
    Registry for tracking installed and loaded extensions.
    
    This class maintains the state of all extensions in the system,
    including their manifests, status, and runtime information.
    """
    
    def __init__(self):
        """Initialize the extension registry."""
        self.extensions: Dict[str, ExtensionRecord] = {}
        self.logger = logging.getLogger("extension.registry")
    
    def register_extension(
        self, 
        manifest: ExtensionManifest,
        instance: Any,
        directory: str
    ) -> ExtensionRecord:
        """
        Register a new extension in the registry.
        
        Args:
            manifest: Extension manifest
            instance: Extension instance
            directory: Extension directory path
            
        Returns:
            ExtensionRecord for the registered extension
        """
        from pathlib import Path
        
        record = ExtensionRecord(
            manifest=manifest,
            instance=instance,
            status=ExtensionStatus.LOADING,
            directory=Path(directory),
            loaded_at=time.time()
        )
        
        self.extensions[manifest.name] = record
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
        if name in self.extensions:
            del self.extensions[name]
            self.logger.info(f"Unregistered extension {name}")
            return True
        return False
    
    def get_extension(self, name: str) -> Optional[ExtensionRecord]:
        """
        Get extension record by name.
        
        Args:
            name: Extension name
            
        Returns:
            ExtensionRecord if found, None otherwise
        """
        return self.extensions.get(name)
    
    def list_extensions(
        self, 
        status_filter: Optional[ExtensionStatus] = None
    ) -> List[ExtensionRecord]:
        """
        List all registered extensions.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of ExtensionRecord instances
        """
        extensions = list(self.extensions.values())
        
        if status_filter:
            extensions = [ext for ext in extensions if ext.status == status_filter]
        
        return extensions
    
    def update_status(self, name: str, status: ExtensionStatus, error_message: Optional[str] = None) -> bool:
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
            self.extensions[name].status = status
            self.extensions[name].error_message = error_message
            self.logger.info(
                f"Updated extension {name} status to {status.value}"
            )
            return True
        return False
    
    def get_active_extensions(self) -> List[ExtensionRecord]:
        """Get all active extensions."""
        return self.list_extensions(ExtensionStatus.ACTIVE)
    
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
        for status in ExtensionStatus:
            summary[status.value] = 0
        
        for extension in self.extensions.values():
            summary[extension.status.value] += 1
        
        return summary
    
    def find_extensions_by_category(self, category: str) -> List[ExtensionRecord]:
        """
        Find extensions by category.
        
        Args:
            category: Extension category
            
        Returns:
            List of matching ExtensionRecord instances
        """
        return [
            ext for ext in self.extensions.values()
            if ext.manifest.category == category
        ]
    
    def find_extensions_by_tag(self, tag: str) -> List[ExtensionRecord]:
        """
        Find extensions by tag.
        
        Args:
            tag: Extension tag
            
        Returns:
            List of matching ExtensionRecord instances
        """
        return [
            ext for ext in self.extensions.values()
            if tag in ext.manifest.tags
        ]
    
    def check_dependencies(self, manifest: ExtensionManifest) -> Dict[str, bool]:
        """
        Check if extension dependencies are satisfied.
        
        Args:
            manifest: Extension manifest to check
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        dependency_status = {}
        
        # Check extension dependencies
        for dep in manifest.dependencies.extensions:
            # Parse version requirement if present (e.g., "extension@^1.0.0")
            if "@" in dep:
                dep_name = dep.split("@", 1)[0]
            else:
                dep_name = dep
            
            # Check if dependency is available
            dep_extension = self.get_extension(dep_name)
            if dep_extension and dep_extension.status == ExtensionStatus.ACTIVE:
                # TODO: Add version compatibility checking
                dependency_status[dep] = True
            else:
                dependency_status[dep] = False
        
        # TODO: Check plugin dependencies
        # TODO: Check system service dependencies
        
        return dependency_status
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert registry to dictionary for serialization.
        
        Returns:
            Dictionary representation of the registry
        """
        return {
            "extensions": {
                name: record.to_dict() 
                for name, record in self.extensions.items()
            },
            "summary": self.get_status_summary(),
            "total_count": self.get_extension_count()
        }


__all__ = ["ExtensionRegistry"]