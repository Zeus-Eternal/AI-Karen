"""
Extension Marketplace Service

This service manages a marketplace for extensions in the AI Karen system,
providing discovery, installation, and management of extensions from various sources.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionMarketplace(BaseService):
    """
    Extension Marketplace service for managing extension marketplace.
    
    This service provides capabilities for discovering, installing, and managing
    extensions from various sources in the AI Karen system.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_marketplace"))
        self._initialized = False
        self._extension_sources: Dict[str, Dict[str, Any]] = {}  # source_name -> source_info
        self._available_extensions: Dict[str, Dict[str, Any]] = {}  # extension_id -> extension_info
        self._installed_extensions: Dict[str, Dict[str, Any]] = {}  # extension_id -> installation_info
        self._extension_dependencies: Dict[str, List[str]] = {}  # extension_id -> dependencies
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Marketplace service."""
        try:
            self.logger.info("Initializing Extension Marketplace service")
            
            # Load extension sources
            await self._load_extension_sources()
            
            # Load available extensions
            await self._load_available_extensions()
            
            # Load installed extensions
            await self._load_installed_extensions()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Marketplace service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Marketplace service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Marketplace service."""
        try:
            self.logger.info("Shutting down Extension Marketplace service")
            
            async with self._lock:
                self._extension_sources.clear()
                self._available_extensions.clear()
                self._installed_extensions.clear()
                self._extension_dependencies.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Marketplace service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Marketplace service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Marketplace service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def add_extension_source(
        self,
        name: str,
        url: str,
        source_type: str = "registry",
        auth_token: Optional[str] = None
    ) -> bool:
        """
        Add an extension source.
        
        Args:
            name: The name of the source
            url: The URL of the source
            source_type: The type of the source (registry, git, etc.)
            auth_token: Optional authentication token for the source
            
        Returns:
            True if the source was added successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if name in self._extension_sources:
                self.logger.warning(f"Extension source {name} already exists")
                return False
            
            # Add the source
            self._extension_sources[name] = {
                "url": url,
                "type": source_type,
                "auth_token": auth_token,
                "enabled": True,
                "last_updated": None
            }
            
            # Load extensions from the source
            await self._load_extensions_from_source(name)
        
        self.logger.info(f"Extension source {name} added successfully")
        return True
    
    async def remove_extension_source(self, name: str) -> bool:
        """
        Remove an extension source.
        
        Args:
            name: The name of the source
            
        Returns:
            True if the source was removed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if name not in self._extension_sources:
                self.logger.warning(f"Extension source {name} does not exist")
                return False
            
            # Remove extensions from this source
            extensions_to_remove = []
            for ext_id, ext_info in self._available_extensions.items():
                if ext_info.get("source") == name:
                    extensions_to_remove.append(ext_id)
            
            for ext_id in extensions_to_remove:
                del self._available_extensions[ext_id]
            
            # Remove the source
            del self._extension_sources[name]
        
        self.logger.info(f"Extension source {name} removed successfully")
        return True
    
    async def get_extension_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all extension sources.
        
        Returns:
            Dictionary mapping source names to source information
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            return self._extension_sources.copy()
    
    async def get_available_extensions(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get available extensions.
        
        Args:
            source: Optional source to filter by
            category: Optional category to filter by
            search: Optional search term to filter by
            
        Returns:
            Dictionary mapping extension IDs to extension information
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            result = {}
            
            for ext_id, ext_info in self._available_extensions.items():
                # Filter by source
                if source and ext_info.get("source") != source:
                    continue
                
                # Filter by category
                if category and ext_info.get("category") != category:
                    continue
                
                # Filter by search term
                if search:
                    search_term = search.lower()
                    name = ext_info.get("name", "").lower()
                    description = ext_info.get("description", "").lower()
                    if search_term not in name and search_term not in description:
                        continue
                
                result[ext_id] = ext_info.copy()
            
            return result
    
    async def get_extension_details(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension details or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if extension_id in self._available_extensions:
                return self._available_extensions[extension_id].copy()
            else:
                return None
    
    async def install_extension(
        self,
        extension_id: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Install an extension.
        
        Args:
            extension_id: The ID of the extension
            version: Optional version to install
            
        Returns:
            True if the extension was installed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if extension_id not in self._available_extensions:
                self.logger.error(f"Extension {extension_id} is not available")
                return False
            
            if extension_id in self._installed_extensions:
                self.logger.warning(f"Extension {extension_id} is already installed")
                return True
            
            # Get extension details
            ext_info = self._available_extensions[extension_id]
            
            # Check dependencies
            dependencies = ext_info.get("dependencies", [])
            for dep_id in dependencies:
                if dep_id not in self._installed_extensions:
                    self.logger.error(f"Dependency {dep_id} is not installed for extension {extension_id}")
                    return False
            
            # Install the extension
            if await self._install_extension_files(extension_id, ext_info, version):
                # Record the installation
                self._installed_extensions[extension_id] = {
                    "source": ext_info.get("source"),
                    "version": version or ext_info.get("latest_version"),
                    "installed_at": asyncio.get_event_loop().time()
                }
                
                self.logger.info(f"Extension {extension_id} installed successfully")
                return True
            else:
                self.logger.error(f"Failed to install extension {extension_id}")
                return False
    
    async def uninstall_extension(self, extension_id: str) -> bool:
        """
        Uninstall an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was uninstalled successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if extension_id not in self._installed_extensions:
                self.logger.warning(f"Extension {extension_id} is not installed")
                return False
            
            # Check if other extensions depend on this one
            for ext_id, deps in self._extension_dependencies.items():
                if extension_id in deps and ext_id in self._installed_extensions:
                    self.logger.error(f"Cannot uninstall extension {extension_id}: extension {ext_id} depends on it")
                    return False
            
            # Uninstall the extension
            if await self._uninstall_extension_files(extension_id):
                # Remove from installed extensions
                del self._installed_extensions[extension_id]
                
                self.logger.info(f"Extension {extension_id} uninstalled successfully")
                return True
            else:
                self.logger.error(f"Failed to uninstall extension {extension_id}")
                return False
    
    async def update_extension(
        self,
        extension_id: str,
        version: Optional[str] = None
    ) -> bool:
        """
        Update an extension.
        
        Args:
            extension_id: The ID of the extension
            version: Optional version to update to
            
        Returns:
            True if the extension was updated successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            if extension_id not in self._installed_extensions:
                self.logger.warning(f"Extension {extension_id} is not installed")
                return False
            
            # Get extension details
            ext_info = self._available_extensions.get(extension_id)
            if not ext_info:
                self.logger.error(f"Extension {extension_id} is not available")
                return False
            
            # Uninstall the current version
            if not await self.uninstall_extension(extension_id):
                return False
            
            # Install the new version
            return await self.install_extension(extension_id, version)
    
    async def get_installed_extensions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all installed extensions.
        
        Returns:
            Dictionary mapping extension IDs to installation information
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            return self._installed_extensions.copy()
    
    async def is_extension_installed(self, extension_id: str) -> bool:
        """
        Check if an extension is installed.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension is installed, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            return extension_id in self._installed_extensions
    
    async def refresh_extension_sources(self) -> bool:
        """
        Refresh all extension sources.
        
        Returns:
            True if all sources were refreshed successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Marketplace service is not initialized")
        
        async with self._lock:
            success = True
            for source_name in self._extension_sources:
                if not await self._load_extensions_from_source(source_name):
                    success = False
            
            return success
    
    async def _load_extension_sources(self) -> None:
        """Load extension sources from configuration."""
        # This is a placeholder for loading extension sources from configuration
        # In a real implementation, this would load from a configuration file
        
        # Add default sources
        await self.add_extension_source(
            "official",
            "https://extensions.ai-karen.com/api/v1",
            "registry"
        )
    
    async def _load_available_extensions(self) -> None:
        """Load available extensions from all sources."""
        # This is a placeholder for loading available extensions
        # In a real implementation, this would fetch from the extension sources
        
        # Add some sample extensions
        sample_extensions = [
            {
                "id": "sample_extension_1",
                "name": "Sample Extension 1",
                "description": "A sample extension for demonstration purposes",
                "version": "1.0.0",
                "category": "utility",
                "source": "official",
                "dependencies": [],
                "author": "AI Karen Team",
                "license": "MIT"
            },
            {
                "id": "sample_extension_2",
                "name": "Sample Extension 2",
                "description": "Another sample extension for demonstration purposes",
                "version": "1.0.0",
                "category": "utility",
                "source": "official",
                "dependencies": ["sample_extension_1"],
                "author": "AI Karen Team",
                "license": "MIT"
            }
        ]
        
        for ext_info in sample_extensions:
            self._available_extensions[ext_info["id"]] = ext_info
            self._extension_dependencies[ext_info["id"]] = ext_info.get("dependencies", [])
    
    async def _load_installed_extensions(self) -> None:
        """Load installed extensions from the filesystem."""
        # This is a placeholder for loading installed extensions
        # In a real implementation, this would check the filesystem for installed extensions
        pass
    
    async def _load_extensions_from_source(self, source_name: str) -> bool:
        """
        Load extensions from a source.
        
        Args:
            source_name: The name of the source
            
        Returns:
            True if the extensions were loaded successfully, False otherwise
        """
        # This is a placeholder for loading extensions from a source
        # In a real implementation, this would fetch from the source API
        
        if source_name not in self._extension_sources:
            return False
        
        # Update last_updated timestamp
        self._extension_sources[source_name]["last_updated"] = asyncio.get_event_loop().time()
        
        return True
    
    async def _install_extension_files(
        self,
        extension_id: str,
        ext_info: Dict[str, Any],
        version: Optional[str] = None
    ) -> bool:
        """
        Install the files for an extension.
        
        Args:
            extension_id: The ID of the extension
            ext_info: The extension information
            version: Optional version to install
            
        Returns:
            True if the files were installed successfully, False otherwise
        """
        # This is a placeholder for installing extension files
        # In a real implementation, this would download and install the extension files
        
        return True
    
    async def _uninstall_extension_files(self, extension_id: str) -> bool:
        """
        Uninstall the files for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the files were uninstalled successfully, False otherwise
        """
        # This is a placeholder for uninstalling extension files
        # In a real implementation, this would remove the extension files
        
        return True