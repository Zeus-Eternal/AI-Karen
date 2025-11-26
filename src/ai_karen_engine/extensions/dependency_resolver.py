"""
Dependency resolver for the legacy extension system.

This module provides backward compatibility with the old dependency resolver
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .base import ExtensionManifest


class DependencyResolver:
    """
    Resolver for extension dependencies in the legacy system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("extension.dependency_resolver")
    
    def resolve_loading_order(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> List[str]:
        """
        Resolve loading order for extensions based on dependencies.
        
        Args:
            manifests: Dictionary of extension manifests
            
        Returns:
            List of extension names in loading order
        """
        # For now, return a simple alphabetical order
        # This can be enhanced later to actually resolve dependencies
        return sorted(manifests.keys())
        
    def check_version_compatibility(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> List[str]:
        """
        Check version compatibility between extensions.
        
        Args:
            manifests: Dictionary of extension manifests
            
        Returns:
            List of compatibility warnings
        """
        # For now, return an empty list
        # This can be enhanced later to actually check version compatibility
        return []
        
    def get_dependency_tree(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> Dict[str, Any]:
        """
        Get the dependency tree for all discovered extensions.
        NOTE: Intended for admin/diagnostic usage.
        
        Args:
            manifests: Dictionary of extension manifests
            
        Returns:
            Dictionary with dependency tree
        """
        # For now, return a simple tree structure
        # This can be enhanced later to actually build a dependency tree
        tree = {
            "extensions": {},
            "dependencies": {}
        }
        
        for name, manifest in manifests.items():
            tree["extensions"][name] = {
                "name": manifest.name,
                "version": manifest.version,
                "dependencies": getattr(manifest, "dependencies", {})
            }
            
        return tree


class DependencyError(Exception):
    """
    Exception raised when there's an error with extension dependencies.
    """
    pass