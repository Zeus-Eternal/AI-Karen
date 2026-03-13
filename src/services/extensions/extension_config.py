"""
Extension Config Service

This service manages the configuration of extensions in the AI Karen system,
providing validation, storage, and retrieval of extension configurations.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionConfig(BaseService):
    """
    Extension Config service for managing extension configurations.
    
    This service provides capabilities for validating, storing, and retrieving
    extension configurations in the AI Karen system.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_config"))
        self._initialized = False
        self._extension_configs: Dict[str, Dict[str, Any]] = {}
        self._config_schemas: Dict[str, Dict[str, Any]] = {}
        self._config_defaults: Dict[str, Dict[str, Any]] = {}
        self._config_validators: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Config service."""
        try:
            self.logger.info("Initializing Extension Config service")
            
            # Load configuration files
            await self._load_config_files()
            
            # Load configuration schemas
            await self._load_config_schemas()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Config service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Config service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Config service."""
        try:
            self.logger.info("Shutting down Extension Config service")
            
            # Save all configurations
            await self._save_all_configs()
            
            async with self._lock:
                self._extension_configs.clear()
                self._config_schemas.clear()
                self._config_defaults.clear()
                self._config_validators.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Config service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Config service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Config service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def get_extension_config(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension configuration or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_configs:
                return self._extension_configs[extension_id].copy()
            elif extension_id in self._config_defaults:
                return self._config_defaults[extension_id].copy()
            else:
                return None
    
    async def set_extension_config(
        self,
        extension_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """
        Set the configuration for an extension.
        
        Args:
            extension_id: The ID of the extension
            config: The configuration to set
            
        Returns:
            True if the configuration was set successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        # Validate the configuration
        if not await self._validate_config(extension_id, config):
            self.logger.error(f"Invalid configuration for extension {extension_id}")
            return False
        
        async with self._lock:
            self._extension_configs[extension_id] = config.copy()
        
        # Save the configuration to file
        await self._save_config(extension_id, config)
        
        self.logger.info(f"Configuration set for extension {extension_id}")
        return True
    
    async def update_extension_config(
        self,
        extension_id: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """
        Update the configuration for an extension.
        
        Args:
            extension_id: The ID of the extension
            config_updates: The configuration updates to apply
            
        Returns:
            True if the configuration was updated successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            # Get the current configuration or default
            if extension_id in self._extension_configs:
                current_config = self._extension_configs[extension_id].copy()
            elif extension_id in self._config_defaults:
                current_config = self._config_defaults[extension_id].copy()
            else:
                self.logger.error(f"No configuration found for extension {extension_id}")
                return False
            
            # Apply the updates
            current_config.update(config_updates)
            
            # Validate the updated configuration
            if not await self._validate_config(extension_id, current_config):
                self.logger.error(f"Invalid configuration update for extension {extension_id}")
                return False
            
            # Set the updated configuration
            self._extension_configs[extension_id] = current_config
        
        # Save the configuration to file
        await self._save_config(extension_id, current_config)
        
        self.logger.info(f"Configuration updated for extension {extension_id}")
        return True
    
    async def delete_extension_config(self, extension_id: str) -> bool:
        """
        Delete the configuration for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the configuration was deleted successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_configs:
                del self._extension_configs[extension_id]
                
                # Delete the configuration file
                config_file = os.path.join("config", "extensions", f"{extension_id}.json")
                if os.path.exists(config_file):
                    os.remove(config_file)
                
                self.logger.info(f"Configuration deleted for extension {extension_id}")
                return True
            else:
                self.logger.warning(f"No configuration found for extension {extension_id}")
                return False
    
    async def get_config_schema(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration schema for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The configuration schema or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            return self._config_schemas.get(extension_id)
    
    async def get_config_defaults(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the default configuration for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The default configuration or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            return self._config_defaults.get(extension_id)
    
    async def get_all_extension_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all extension configurations.
        
        Returns:
            Dictionary mapping extension IDs to extension configurations
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            result = {}
            for ext_id, config in self._extension_configs.items():
                result[ext_id] = config.copy()
            return result
    
    async def register_extension_config(
        self,
        extension_id: str,
        schema: Dict[str, Any],
        defaults: Dict[str, Any]
    ) -> bool:
        """
        Register a configuration schema and defaults for an extension.
        
        Args:
            extension_id: The ID of the extension
            schema: The configuration schema
            defaults: The default configuration
            
        Returns:
            True if the configuration was registered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            self._config_schemas[extension_id] = schema
            self._config_defaults[extension_id] = defaults
            
            # If no configuration exists for this extension, use the defaults
            if extension_id not in self._extension_configs:
                self._extension_configs[extension_id] = defaults.copy()
        
        self.logger.info(f"Configuration registered for extension {extension_id}")
        return True
    
    async def unregister_extension_config(self, extension_id: str) -> bool:
        """
        Unregister a configuration schema and defaults for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the configuration was unregistered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Config service is not initialized")
        
        async with self._lock:
            if extension_id in self._config_schemas:
                del self._config_schemas[extension_id]
            
            if extension_id in self._config_defaults:
                del self._config_defaults[extension_id]
            
            if extension_id in self._extension_configs:
                del self._extension_configs[extension_id]
        
        self.logger.info(f"Configuration unregistered for extension {extension_id}")
        return True
    
    async def _load_config_files(self) -> None:
        """Load configuration files from the config/extensions directory."""
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
    
    async def _load_config_schemas(self) -> None:
        """Load configuration schemas from the config/schemas directory."""
        schema_dir = os.path.join("config", "schemas")
        if os.path.exists(schema_dir):
            for filename in os.listdir(schema_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(schema_dir, filename)
                    try:
                        with open(filepath, "r") as f:
                            schema = json.load(f)
                            extension_id = schema.get("extension_id", filename[:-5])
                            self._config_schemas[extension_id] = schema
                            
                            # Load defaults if present
                            if "defaults" in schema:
                                self._config_defaults[extension_id] = schema["defaults"]
                            
                            self.logger.info(f"Loaded configuration schema for extension {extension_id} from {filename}")
                    except Exception as e:
                        self.logger.error(f"Failed to load configuration schema from {filename}: {e}")
    
    async def _validate_config(self, extension_id: str, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration against its schema.
        
        Args:
            extension_id: The ID of the extension
            config: The configuration to validate
            
        Returns:
            True if the configuration is valid, False otherwise
        """
        if extension_id not in self._config_schemas:
            # No schema to validate against, assume valid
            return True
        
        # This is a placeholder for configuration validation
        # In a real implementation, this would use a proper JSON schema validator
        schema = self._config_schemas[extension_id]
        
        # Basic validation - check that all required fields are present
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                self.logger.error(f"Missing required field '{field}' in configuration for extension {extension_id}")
                return False
        
        return True
    
    async def _save_config(self, extension_id: str, config: Dict[str, Any]) -> None:
        """
        Save a configuration to a file.
        
        Args:
            extension_id: The ID of the extension
            config: The configuration to save
        """
        config_dir = os.path.join("config", "extensions")
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f"{extension_id}.json")
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            self.logger.info(f"Saved configuration for extension {extension_id} to {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration for extension {extension_id}: {e}")
    
    async def _save_all_configs(self) -> None:
        """Save all configurations to files."""
        async with self._lock:
            for extension_id, config in self._extension_configs.items():
                await self._save_config(extension_id, config)