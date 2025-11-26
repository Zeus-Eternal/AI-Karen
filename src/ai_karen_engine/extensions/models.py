"""
Models for the legacy extension system.

This module provides backward compatibility with the old extension models
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .base import ExtensionContext, ExtensionManifest, ExtensionStatus
# Compatibility export to allow api_routes to import ExtensionStatusAPI from legacy path
try:
    from ai_karen_engine.extension_host.models import ExtensionStatusAPI  # type: ignore
except Exception:  # pragma: no cover
    ExtensionStatusAPI = None  # type: ignore


@dataclass
class ExtensionRecord:
    """
    Record for a loaded extension in the legacy system.
    """
    manifest: ExtensionManifest
    instance: Any
    directory: str
    status: ExtensionStatus = ExtensionStatus.INACTIVE
    loaded_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.loaded_at is None:
            self.loaded_at = datetime.datetime.utcnow()


@dataclass
class ExtensionValidator:
    """
    Validator for extension manifests in the legacy system.
    """
    
    def validate_manifest_enhanced(
        self, 
        manifest: ExtensionManifest
    ) -> tuple[bool, List[str], List[str], List[Any]]:
        """
        Validate an extension manifest with enhanced checks.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings, field_errors)
        """
        errors = []
        warnings = []
        field_errors = []
        
        # Check required fields
        if not manifest.id:
            errors.append("Extension ID is required")
            
        if not manifest.name:
            errors.append("Extension name is required")
            
        if not manifest.version:
            errors.append("Extension version is required")
            
        if not manifest.entrypoint:
            errors.append("Extension entrypoint is required")
            
        # Check hook points
        if not isinstance(manifest.hook_points, list):
            field_errors.append("hook_points must be a list")
        else:
            valid_hook_points = [
                "pre_intent_detection",
                "pre_memory_retrieval",
                "post_memory_retrieval",
                "pre_llm_prompt",
                "post_llm_result",
                "post_response"
            ]
            for hook_point in manifest.hook_points:
                if hook_point not in valid_hook_points:
                    warnings.append(f"Unknown hook point: {hook_point}")
                    
        # Check prompt files
        if not isinstance(manifest.prompt_files, dict):
            field_errors.append("prompt_files must be a dictionary")
            
        # Check config schema
        if not isinstance(manifest.config_schema, dict):
            field_errors.append("config_schema must be a dictionary")
            
        # Check permissions
        if not isinstance(manifest.permissions, dict):
            field_errors.append("permissions must be a dictionary")
            
        # Check RBAC
        if not isinstance(manifest.rbac, dict):
            field_errors.append("rbac must be a dictionary")
            
        return (len(errors) == 0, errors, warnings, field_errors)
    
    def get_validation_report(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """
        Get a comprehensive validation report for an extension manifest.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Dictionary with validation report
        """
        is_valid, errors, warnings, field_errors = self.validate_manifest_enhanced(manifest)
        
        report = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "field_errors": field_errors,
            "recommendations": []
        }
        
        # Add recommendations based on validation results
        if not is_valid:
            report["recommendations"].append("Fix all errors before loading the extension")
            
        if warnings:
            report["recommendations"].append("Consider addressing warnings for better compatibility")
            
        if field_errors:
            report["recommendations"].append("Fix field errors to ensure proper functionality")
            
        return report


@dataclass
class ExtensionRegistry:
    """
    Registry for extensions in the legacy system.
    """
    extensions: Dict[str, ExtensionRecord] = field(default_factory=dict)
    
    def register_extension(
        self, 
        manifest: ExtensionManifest, 
        instance: Any, 
        directory: str
    ) -> ExtensionRecord:
        """
        Register an extension.
        
        Args:
            manifest: Extension manifest
            instance: Extension instance
            directory: Extension directory
            
        Returns:
            Extension record
        """
        record = ExtensionRecord(
            manifest=manifest,
            instance=instance,
            directory=directory,
            status=ExtensionStatus.LOADING
        )
        self.extensions[manifest.name] = record
        return record
        
    def unregister_extension(self, name: str) -> bool:
        """
        Unregister an extension.
        
        Args:
            name: Extension name
            
        Returns:
            True if extension was unregistered, False if not found
        """
        if name in self.extensions:
            del self.extensions[name]
            return True
        return False
        
    def get_extension(self, name: str) -> Optional[ExtensionRecord]:
        """
        Get an extension by name.
        
        Args:
            name: Extension name
            
        Returns:
            Extension record or None if not found
        """
        return self.extensions.get(name)
        
    def get_active_extensions(self) -> List[ExtensionRecord]:
        """
        Get all active extensions.
        
        Returns:
            List of active extension records
        """
        return [
            record for record in self.extensions.values()
            if record.status == ExtensionStatus.ACTIVE and record.enabled
        ]
        
    def update_status(
        self, 
        name: str, 
        status: ExtensionStatus, 
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status of an extension.
        
        Args:
            name: Extension name
            status: New status
            error_message: Optional error message
            
        Returns:
            True if status was updated, False if extension not found
        """
        record = self.get_extension(name)
        if record:
            record.status = status
            if error_message:
                record.error_message = error_message
            return True
        return False
        
    def check_dependencies(self, manifest: ExtensionManifest) -> Dict[str, bool]:
        """
        Check if an extension's dependencies are satisfied.
        
        Args:
            manifest: Extension manifest
            
        Returns:
            Dictionary mapping dependency names to satisfaction status
        """
        # For now, return all dependencies as satisfied
        # This can be enhanced later to actually check dependencies
        dependencies = getattr(manifest, "dependencies", {})
        return {dep: True for dep in dependencies}


@dataclass
class DependencyResolver:
    """
    Resolver for extension dependencies in the legacy system.
    """
    
    def resolve_loading_order(
        self, 
        manifests: Dict[str, ExtensionManifest]
    ) -> List[str]:
        """
        Resolve the loading order for extensions based on dependencies.
        
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
        Get the dependency tree for extensions.
        
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


__all__ = [
    "ExtensionContext",
    "ExtensionManifest",
    "ExtensionStatus",
    "ExtensionRecord",
    "ExtensionValidator",
    "ExtensionRegistry",
    "DependencyResolver",
    "DependencyError",
    "ExtensionStatusAPI",
]
