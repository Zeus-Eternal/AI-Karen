"""
Extension Registry Service

This service manages the registration, discovery, and lifecycle of extensions
in the AI Karen system.
"""

import asyncio
import logging
import os
import json
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionRegistry(BaseService):
    """
    Extension Registry service for managing extensions.
    
    This service provides capabilities for registering, discovering, and managing
    the lifecycle of extensions in the AI Karen system.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_registry"))
        self._initialized = False
        self._extensions: Dict[str, Dict[str, Any]] = {}
        self._extension_configs: Dict[str, Dict[str, Any]] = {}
        self._extension_dependencies: Dict[str, List[str]] = {}
        self._extension_states: Dict[str, str] = {}  # extension_id -> state
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Registry service."""
        try:
            self.logger.info("Initializing Extension Registry service")
            
            # Load extension configurations
            await self._load_extension_configs()
            
            # Register built-in extensions
            await self._register_builtin_extensions()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Registry service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Registry service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Registry service."""
        try:
            self.logger.info("Shutting down Extension Registry service")
            
            # Shutdown all extensions
            async with self._lock:
                for extension_id in self._extensions:
                    await self._shutdown_extension(extension_id)
                
                self._extensions.clear()
                self._extension_configs.clear()
                self._extension_dependencies.clear()
                self._extension_states.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Registry service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Registry service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Registry service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def register_extension(
        self,
        extension_id: str,
        extension_type: str,
        extension_config: Dict[str, Any],
        dependencies: Optional[List[str]] = None
    ) -> bool:
        """
        Register an extension.
        
        Args:
            extension_id: The ID of the extension
            extension_type: The type of the extension
            extension_config: The configuration of the extension
            dependencies: Optional list of extension IDs that this extension depends on
            
        Returns:
            True if the extension was registered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id in self._extensions:
                self.logger.warning(f"Extension {extension_id} is already registered")
                return False
            
            # Check if dependencies exist
            if dependencies:
                for dep_id in dependencies:
                    if dep_id not in self._extensions:
                        self.logger.error(f"Dependency {dep_id} not found for extension {extension_id}")
                        return False
            
            # Register the extension
            self._extensions[extension_id] = {
                "type": extension_type,
                "config": extension_config,
                "dependencies": dependencies or [],
                "registered_at": asyncio.get_event_loop().time()
            }
            
            self._extension_configs[extension_id] = extension_config
            self._extension_dependencies[extension_id] = dependencies or []
            self._extension_states[extension_id] = "registered"
        
        self.logger.info(f"Extension {extension_id} registered successfully")
        return True
    
    async def unregister_extension(self, extension_id: str) -> bool:
        """
        Unregister an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was unregistered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extensions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            # Check if other extensions depend on this one
            for ext_id, deps in self._extension_dependencies.items():
                if extension_id in deps:
                    self.logger.error(f"Cannot unregister extension {extension_id}: extension {ext_id} depends on it")
                    return False
            
            # Shutdown the extension if it's running
            if self._extension_states[extension_id] == "running":
                await self._shutdown_extension(extension_id)
            
            # Unregister the extension
            del self._extensions[extension_id]
            del self._extension_configs[extension_id]
            del self._extension_dependencies[extension_id]
            del self._extension_states[extension_id]
        
        self.logger.info(f"Extension {extension_id} unregistered successfully")
        return True
    
    async def get_extension(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension information or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id in self._extensions:
                extension_info = self._extensions[extension_id].copy()
                extension_info["state"] = self._extension_states[extension_id]
                return extension_info
            else:
                return None
    
    async def get_all_extensions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all extensions.
        
        Returns:
            Dictionary mapping extension IDs to extension information
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            result = {}
            for ext_id, ext_info in self._extensions.items():
                ext_copy = ext_info.copy()
                ext_copy["state"] = self._extension_states[ext_id]
                result[ext_id] = ext_copy
            return result
    
    async def start_extension(self, extension_id: str) -> bool:
        """
        Start an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was started successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extensions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if self._extension_states[extension_id] == "running":
                self.logger.warning(f"Extension {extension_id} is already running")
                return True
            
            # Start dependencies first
            for dep_id in self._extension_dependencies[extension_id]:
                if self._extension_states[dep_id] != "running":
                    if not await self.start_extension(dep_id):
                        self.logger.error(f"Failed to start dependency {dep_id} for extension {extension_id}")
                        return False
            
            # Start the extension
            if await self._start_extension(extension_id):
                self._extension_states[extension_id] = "running"
                self.logger.info(f"Extension {extension_id} started successfully")
                return True
            else:
                self.logger.error(f"Failed to start extension {extension_id}")
                return False
    
    async def stop_extension(self, extension_id: str) -> bool:
        """
        Stop an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was stopped successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extensions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            if self._extension_states[extension_id] != "running":
                self.logger.warning(f"Extension {extension_id} is not running")
                return True
            
            # Stop extensions that depend on this one
            for ext_id, deps in self._extension_dependencies.items():
                if extension_id in deps and self._extension_states[ext_id] == "running":
                    if not await self.stop_extension(ext_id):
                        self.logger.error(f"Failed to stop dependent extension {ext_id}")
                        return False
            
            # Stop the extension
            if await self._stop_extension(extension_id):
                self._extension_states[extension_id] = "stopped"
                self.logger.info(f"Extension {extension_id} stopped successfully")
                return True
            else:
                self.logger.error(f"Failed to stop extension {extension_id}")
                return False
    
    async def get_extension_config(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension configuration or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            return self._extension_configs.get(extension_id)
    
    async def update_extension_config(self, extension_id: str, config: Dict[str, Any]) -> bool:
        """
        Update the configuration of an extension.
        
        Args:
            extension_id: The ID of the extension
            config: The new configuration
            
        Returns:
            True if the configuration was updated successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Registry service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extensions:
                self.logger.warning(f"Extension {extension_id} is not registered")
                return False
            
            # If the extension is running, stop it first
            was_running = self._extension_states[extension_id] == "running"
            if was_running:
                if not await self.stop_extension(extension_id):
                    return False
            
            # Update the configuration
            self._extension_configs[extension_id] = config
            self._extensions[extension_id]["config"] = config
            
            # Restart the extension if it was running
            if was_running:
                if not await self.start_extension(extension_id):
                    return False
            
            self.logger.info(f"Configuration for extension {extension_id} updated successfully")
            return True
    
    async def _load_extension_configs(self) -> None:
        """Load extension configurations from files."""
        # Look for extension configuration files in the config/extensions directory
        config_dir = os.path.join("config", "extensions")
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(config_dir, filename)
                    try:
                        with open(filepath, "r") as f:
                            config = json.load(f)
                            extension_id = config.get("id", filename[:-5])
                            self._extension_configs[extension_id] = config
                            self.logger.info(f"Loaded configuration for extension {extension_id} from {filename}")
                    except Exception as e:
                        self.logger.error(f"Failed to load configuration from {filename}: {e}")
    
    async def _register_builtin_extensions(self) -> None:
        """Register built-in extensions."""
        # Built-in extensions can be registered here
        pass
    
    async def _start_extension(self, extension_id: str) -> bool:
        """Start an extension."""
        # This is a placeholder for extension startup logic
        # In a real implementation, this would load and initialize the extension
        self.logger.info(f"Starting extension {extension_id}")
        return True
    
    async def _stop_extension(self, extension_id: str) -> bool:
        """Stop an extension."""
        # This is a placeholder for extension shutdown logic
        # In a real implementation, this would properly shutdown the extension
        self.logger.info(f"Stopping extension {extension_id}")
        return True
    
    async def _shutdown_extension(self, extension_id: str) -> bool:
        """Shutdown an extension."""
        # This is a placeholder for extension shutdown logic
        # In a real implementation, this would properly shutdown the extension
        self.logger.info(f"Shutting down extension {extension_id}")
        return True