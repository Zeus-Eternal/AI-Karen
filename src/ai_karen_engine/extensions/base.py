"""
Base classes for the legacy extension system.

This module provides backward compatibility with the old extension system
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.extension_host.base import ExtensionBase as ExtensionHostBase
from ai_karen_engine.extension_host.base import ExtensionManifest as ExtensionHostManifest


class BaseExtension(ExtensionHostBase):
    """
    Base class for all extensions in the legacy system.
    
    This class extends the new ExtensionBase to maintain backward compatibility.
    """

    def __init__(
        self,
        manifest: Union[ExtensionManifest, ExtensionHostManifest, Dict[str, Any]],
        context: ExtensionContext
    ):
        """
        Initialize the extension.
        
        Args:
            manifest: Extension manifest
            context: Extension context
        """
        # Convert legacy manifest to new format if needed
        if isinstance(manifest, dict):
            # Create a new manifest from dict
            self._manifest = ExtensionHostManifest(**manifest)
        elif isinstance(manifest, ExtensionManifest):
            # Convert legacy manifest to new format
            self._manifest = ExtensionHostManifest(
                id=manifest.id,
                name=manifest.name,
                version=manifest.version,
                entrypoint=manifest.entrypoint,
                description=manifest.description,
                hook_points=manifest.hook_points,
                prompt_files=manifest.prompt_files,
                config_schema=manifest.config_schema,
                permissions=manifest.permissions,
                rbac=manifest.rbac
            )
        else:
            # Already in new format
            self._manifest = manifest
            
        # Store context
        self._context = context
        
        # Initialize parent class
        super().__init__(self._manifest)
        
        # Legacy attributes
        self.logger = logging.getLogger(f"extension.{self._manifest.id}")
        self.enabled = True

    @property
    def manifest(self) -> ExtensionHostManifest:
        """Get the extension manifest."""
        return self._manifest

    @property
    def context(self) -> ExtensionContext:
        """Get the extension context."""
        return self._context

    async def initialize(self) -> None:
        """
        Initialize the extension.
        
        This method is called when the extension is loaded.
        """
        pass

    async def shutdown(self) -> None:
        """
        Shutdown the extension.
        
        This method is called when the extension is unloaded.
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the extension.
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self._manifest.name,
            "version": self._manifest.version,
            "enabled": self.enabled,
            "status": "active" if self.enabled else "inactive"
        }

    def get_hook_stats(self) -> Dict[str, Any]:
        """
        Get hook execution statistics.
        
        Returns:
            Dictionary with hook statistics
        """
        return {
            "hooks_enabled": hasattr(self, "handle_hook"),
            "hooks_executed": 0,
            "hooks_failed": 0
        }

    async def handle_hook(self, hook_type: str, data: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle a hook execution.
        
        Args:
            hook_type: Type of hook to execute
            data: Hook data
            user_context: Optional user context
            
        Returns:
            Hook execution result
        """
        return {"success": True, "message": "Hook not implemented"}


class ExtensionManifest:
    """
    Legacy extension manifest class.
    
    This class provides backward compatibility with the old manifest format.
    """

    def __init__(
        self,
        id: str,
        name: str,
        version: str,
        entrypoint: str,
        description: str = "",
        hook_points: Optional[List[str]] = None,
        prompt_files: Optional[Dict[str, str]] = None,
        config_schema: Optional[Dict[str, Any]] = None,
        permissions: Optional[Dict[str, Any]] = None,
        rbac: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.id = id
        self.name = name
        self.version = version
        self.entrypoint = entrypoint
        self.description = description
        self.hook_points = hook_points or []
        self.prompt_files = prompt_files or {}
        self.config_schema = config_schema or {}
        self.permissions = permissions or {}
        self.rbac = rbac or {}
        
        # Additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_file(cls, file_path: str) -> ExtensionManifest:
        """
        Load manifest from a JSON file.
        
        Args:
            file_path: Path to the manifest file
            
        Returns:
            ExtensionManifest instance
        """
        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def dict(self) -> Dict[str, Any]:
        """
        Convert manifest to dictionary.
        
        Returns:
            Dictionary representation of the manifest
        """
        result = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "description": self.description,
            "hook_points": self.hook_points,
            "prompt_files": self.prompt_files,
            "config_schema": self.config_schema,
            "permissions": self.permissions,
            "rbac": self.rbac
        }
        
        # Add additional attributes
        for key, value in self.__dict__.items():
            if key not in result:
                result[key] = value
                
        return result


class ExtensionContext:
    """
    Legacy extension context class.
    
    This class provides backward compatibility with the old context format.
    """

    def __init__(
        self,
        plugin_router: Optional[Any] = None,
        db_session: Optional[Any] = None,
        app_instance: Optional[Any] = None,
        **kwargs
    ):
        self.plugin_router = plugin_router
        self.db_session = db_session
        self.app_instance = app_instance
        
        # Additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a context value.
        
        Args:
            key: Key to get
            default: Default value if key not found
            
        Returns:
            Context value or default
        """
        return getattr(self, key, default)


class ExtensionStatus:
    """
    Extension status enumeration.
    """
    
    INACTIVE = "inactive"
    LOADING = "loading"
    ACTIVE = "active"
    UNLOADING = "unloading"
    ERROR = "error"