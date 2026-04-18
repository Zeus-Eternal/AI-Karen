"""
Extension Loader Service

This service handles the dynamic loading and unloading of extensions
in the AI Karen system.
"""

import asyncio
import importlib
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionLoader(BaseService):
    """
    Extension Loader service for handling dynamic loading of extensions.
    
    This service provides capabilities for dynamically loading and unloading
    extensions in the AI Karen system.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_loader"))
        self._initialized = False
        self._loaded_extensions: Dict[str, Dict[str, Any]] = {}
        self._extension_paths: Dict[str, str] = {}
        self._extension_modules: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Loader service."""
        try:
            self.logger.info("Initializing Extension Loader service")
            
            # Initialize extension paths
            await self._initialize_extension_paths()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Loader service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Loader service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Loader service."""
        try:
            self.logger.info("Shutting down Extension Loader service")
            
            # Unload all extensions
            async with self._lock:
                for extension_id in list(self._loaded_extensions.keys()):
                    await self.unload_extension(extension_id)
                
                self._loaded_extensions.clear()
                self._extension_paths.clear()
                self._extension_modules.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Loader service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Loader service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Loader service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def load_extension(self, extension_id: str, extension_path: str) -> bool:
        """
        Load an extension.
        
        Args:
            extension_id: The ID of the extension
            extension_path: The path to the extension module
            
        Returns:
            True if the extension was loaded successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            if extension_id in self._loaded_extensions:
                self.logger.warning(f"Extension {extension_id} is already loaded")
                return True
            
            try:
                # Add the extension path to sys.path if not already there
                if extension_path not in sys.path:
                    sys.path.insert(0, extension_path)
                
                # Import the extension module
                module_name = f"extension_{extension_id}"
                module = importlib.import_module(module_name)
                
                # Store the extension information
                self._loaded_extensions[extension_id] = {
                    "path": extension_path,
                    "module_name": module_name,
                    "loaded_at": asyncio.get_event_loop().time()
                }
                
                self._extension_paths[extension_id] = extension_path
                self._extension_modules[extension_id] = module
                
                self.logger.info(f"Extension {extension_id} loaded successfully from {extension_path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to load extension {extension_id} from {extension_path}: {e}")
                # Remove the path from sys.path if we added it
                if extension_path in sys.path:
                    sys.path.remove(extension_path)
                return False
    
    async def unload_extension(self, extension_id: str) -> bool:
        """
        Unload an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was unloaded successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            if extension_id not in self._loaded_extensions:
                self.logger.warning(f"Extension {extension_id} is not loaded")
                return True
            
            try:
                # Get the extension information
                extension_info = self._loaded_extensions[extension_id]
                module_name = extension_info["module_name"]
                extension_path = extension_info["path"]
                
                # Remove the module from sys.modules
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                # Remove the extension information
                del self._loaded_extensions[extension_id]
                del self._extension_paths[extension_id]
                if extension_id in self._extension_modules:
                    del self._extension_modules[extension_id]
                
                # Remove the path from sys.path if it's there
                if extension_path in sys.path:
                    sys.path.remove(extension_path)
                
                self.logger.info(f"Extension {extension_id} unloaded successfully")
                return True
            except Exception as e:
                self.logger.error(f"Failed to unload extension {extension_id}: {e}")
                return False
    
    async def reload_extension(self, extension_id: str) -> bool:
        """
        Reload an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was reloaded successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            if extension_id not in self._loaded_extensions:
                self.logger.warning(f"Extension {extension_id} is not loaded")
                return False
            
            # Get the extension path
            extension_path = self._loaded_extensions[extension_id]["path"]
            
            # Unload the extension
            if not await self.unload_extension(extension_id):
                return False
            
            # Load the extension again
            return await self.load_extension(extension_id, extension_path)
    
    async def get_loaded_extensions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all loaded extensions.
        
        Returns:
            Dictionary mapping extension IDs to extension information
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            return self._loaded_extensions.copy()
    
    async def is_extension_loaded(self, extension_id: str) -> bool:
        """
        Check if an extension is loaded.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension is loaded, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            return extension_id in self._loaded_extensions
    
    async def get_extension_module(self, extension_id: str) -> Optional[Any]:
        """
        Get the module of a loaded extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension module or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            return self._extension_modules.get(extension_id)
    
    async def get_extension_path(self, extension_id: str) -> Optional[str]:
        """
        Get the path of a loaded extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension path or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Loader service is not initialized")
        
        async with self._lock:
            return self._extension_paths.get(extension_id)
    
    async def _initialize_extension_paths(self) -> None:
        """Initialize extension paths."""
        # Add common extension paths to sys.path
        extension_paths = [
            "extensions",
            "src/extensions",
            "src/ai_karen_engine/extensions"
        ]
        
        for path in extension_paths:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
                self.logger.info(f"Added extension path: {path}")