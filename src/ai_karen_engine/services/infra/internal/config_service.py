"""
Config Service Helper

This module provides helper functionality for configuration management in the KAREN AI system.
It handles configuration loading, validation, updates, and other configuration-related operations.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigServiceHelper:
    """
    Helper service for configuration management.
    
    This service provides methods for managing system configuration,
    including loading, validating, updating, and persisting configuration data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the config service helper.
        
        Args:
            config: Configuration dictionary for the config service
        """
        self.config = config
        self.config_path = config.get("config_path", "./config")
        self.config_file = config.get("config_file", "config.json")
        self.backup_enabled = config.get("backup_enabled", True)
        self.backup_path = config.get("backup_path", "./config/backups")
        self.backup_count = config.get("backup_count", 5)
        self.validation_enabled = config.get("validation_enabled", True)
        self._is_connected = False
        self._config_data = {}
        
    async def initialize(self) -> bool:
        """
        Initialize the config service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing config service")
            
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_path):
                os.makedirs(self.config_path)
                
            # Create backup directory if enabled and doesn't exist
            if self.backup_enabled and not os.path.exists(self.backup_path):
                os.makedirs(self.backup_path)
                
            # Load configuration
            await self._load_configuration()
            
            self._is_connected = True
            logger.info("Config service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing config service: {str(e)}")
            return False
    
    async def _load_configuration(self) -> None:
        """Load configuration from file."""
        config_file_path = os.path.join(self.config_path, self.config_file)
        
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as f:
                self._config_data = json.load(f)
            logger.info(f"Loaded configuration from: {config_file_path}")
        else:
            logger.info(f"Configuration file not found, using default configuration: {config_file_path}")
            self._config_data = {}
            
    async def start(self) -> bool:
        """
        Start the config service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting config service")
            
            # Validate configuration if enabled
            if self.validation_enabled:
                await self._validate_configuration()
                
            logger.info("Config service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting config service: {str(e)}")
            return False
    
    async def _validate_configuration(self) -> None:
        """Validate configuration."""
        # In a real implementation, this would validate the configuration
        logger.info("Validating configuration")
        
    async def stop(self) -> bool:
        """
        Stop the config service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping config service")
            
            # Save configuration
            await self._save_configuration()
            
            self._is_connected = False
            logger.info("Config service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping config service: {str(e)}")
            return False
    
    async def _save_configuration(self) -> None:
        """Save configuration to file."""
        config_file_path = os.path.join(self.config_path, self.config_file)
        
        # Create backup if enabled
        if self.backup_enabled:
            await self._create_backup()
            
        with open(config_file_path, 'w') as f:
            json.dump(self._config_data, f, indent=2)
        logger.info(f"Saved configuration to: {config_file_path}")
        
    async def _create_backup(self) -> None:
        """Create a backup of the configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"config_{timestamp}.json"
        backup_file_path = os.path.join(self.backup_path, backup_file)
        
        # Copy current configuration to backup
        with open(backup_file_path, 'w') as f:
            json.dump(self._config_data, f, indent=2)
        logger.info(f"Created configuration backup: {backup_file_path}")
        
        # Clean up old backups if needed
        await self._cleanup_old_backups()
        
    async def _cleanup_old_backups(self) -> None:
        """Clean up old backup files."""
        # In a real implementation, this would clean up old backup files
        logger.info("Cleaning up old backup files")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the config service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_connected:
                return {"status": "unhealthy", "message": "Config service is not connected"}
                
            # Check if configuration file exists and is readable
            config_file_path = os.path.join(self.config_path, self.config_file)
            config_file_exists = os.path.exists(config_file_path)
            config_file_readable = os.access(config_file_path, os.R_OK) if config_file_exists else False
            
            # Check if backup directory exists and is writable if backups are enabled
            backup_dir_exists = False
            backup_dir_writable = False
            if self.backup_enabled:
                backup_dir_exists = os.path.exists(self.backup_path)
                backup_dir_writable = os.access(self.backup_path, os.W_OK) if backup_dir_exists else False
                
            # Determine overall health
            if config_file_exists and config_file_readable:
                if not self.backup_enabled or (backup_dir_exists and backup_dir_writable):
                    overall_status = "healthy"
                else:
                    overall_status = "degraded"
            else:
                overall_status = "unhealthy"
                
            return {
                "status": overall_status,
                "message": f"Config service is {overall_status}",
                "config_file_exists": config_file_exists,
                "config_file_readable": config_file_readable,
                "backup_enabled": self.backup_enabled,
                "backup_dir_exists": backup_dir_exists,
                "backup_dir_writable": backup_dir_writable
            }
            
        except Exception as e:
            logger.error(f"Error checking config service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
        
    async def connect(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Connect to the config service.
        
        Args:
            data: Optional data for the connection
            context: Optional context for the connection
            
        Returns:
            Dictionary containing connection status information
        """
        try:
            logger.info("Connecting to config service")
            
            # Reload configuration
            await self._load_configuration()
            
            self._is_connected = True
            return {"status": "success", "message": "Connected to config service"}
            
        except Exception as e:
            logger.error(f"Error connecting to config service: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def disconnect(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Disconnect from the config service.
        
        Args:
            data: Optional data for the disconnection
            context: Optional context for the disconnection
            
        Returns:
            Dictionary containing disconnection status information
        """
        try:
            logger.info("Disconnecting from config service")
            
            # Save configuration
            await self._save_configuration()
            
            self._is_connected = False
            return {"status": "success", "message": "Disconnected from config service"}
            
        except Exception as e:
            logger.error(f"Error disconnecting from config service: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def get(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a configuration value.
        
        Args:
            data: Dictionary containing key and other parameters
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            if not data:
                return {"status": "error", "message": "Configuration data is required"}
                
            key = data.get("key")
            default_value = data.get("default_value", None)
            
            if not key:
                return {"status": "error", "message": "Key is required"}
                
            # Get configuration value
            keys = key.split('.')
            value = self._config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    value = default_value
                    break
                    
            return {
                "status": "success",
                "message": f"Retrieved configuration value for key: {key}",
                "key": key,
                "value": value
            }
            
        except Exception as e:
            logger.error(f"Error getting configuration value: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def set(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Set a configuration value.
        
        Args:
            data: Dictionary containing key, value, and other parameters
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            if not data:
                return {"status": "error", "message": "Configuration data is required"}
                
            key = data.get("key")
            value = data.get("value")
            create_missing = data.get("create_missing", True)
            
            if key is None or value is None:
                return {"status": "error", "message": "Key and value are required"}
                
            # Set configuration value
            keys = key.split('.')
            config = self._config_data
            
            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    if create_missing:
                        config[k] = {}
                    else:
                        return {"status": "error", "message": f"Key not found: {'.'.join(keys[:i+1])}"}
                        
                if not isinstance(config[k], dict):
                    return {"status": "error", "message": f"Key is not a dictionary: {'.'.join(keys[:i+1])}"}
                    
                config = config[k]
                
            # Set the final value
            config[keys[-1]] = value
            
            return {
                "status": "success",
                "message": f"Set configuration value for key: {key}",
                "key": key,
                "value": value
            }
            
        except Exception as e:
            logger.error(f"Error setting configuration value: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def delete(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delete a configuration value.
        
        Args:
            data: Dictionary containing key and other parameters
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            if not data:
                return {"status": "error", "message": "Configuration data is required"}
                
            key = data.get("key")
            
            if not key:
                return {"status": "error", "message": "Key is required"}
                
            # Delete configuration value
            keys = key.split('.')
            config = self._config_data
            
            for i, k in enumerate(keys[:-1]):
                if k not in config or not isinstance(config[k], dict):
                    return {"status": "error", "message": f"Key not found: {'.'.join(keys[:i+1])}"}
                    
                config = config[k]
                
            # Delete the final value
            if keys[-1] in config:
                del config[keys[-1]]
                return {
                    "status": "success",
                    "message": f"Deleted configuration value for key: {key}",
                    "key": key
                }
            else:
                return {"status": "error", "message": f"Key not found: {key}"}
                
        except Exception as e:
            logger.error(f"Error deleting configuration value: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def get_all(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            return {
                "status": "success",
                "message": "Retrieved all configuration values",
                "config": self._config_data
            }
            
        except Exception as e:
            logger.error(f"Error getting all configuration values: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    async def set_all(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Set all configuration values.
        
        Args:
            data: Dictionary containing config and other parameters
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            if not data or "config" not in data:
                return {"status": "error", "message": "Configuration data is required"}
                
            new_config = data.get("config")
            
            if not isinstance(new_config, dict):
                return {"status": "error", "message": "Configuration must be a dictionary"}
                
            # Validate configuration if enabled
            if self.validation_enabled:
                validation_result = await self._validate_new_config(new_config)
                if validation_result.get("status") != "success":
                    return validation_result
                    
            # Replace configuration
            self._config_data = new_config
            
            return {
                "status": "success",
                "message": "Set all configuration values",
                "config": self._config_data
            }
            
        except Exception as e:
            logger.error(f"Error setting all configuration values: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _validate_new_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate new configuration."""
        # In a real implementation, this would validate the new configuration
        return {"status": "success", "message": "Configuration is valid"}
        
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get configuration statistics.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing configuration statistics
        """
        try:
            if not self._is_connected:
                return {"status": "error", "message": "Config service is not connected"}
                
            # Count configuration keys
            def count_keys(config, prefix=""):
                count = 0
                for key, value in config.items():
                    if isinstance(value, dict):
                        count += count_keys(value, f"{prefix}{key}.")
                    else:
                        count += 1
                return count
                
            key_count = count_keys(self._config_data)
            
            # Get configuration file size
            config_file_path = os.path.join(self.config_path, self.config_file)
            file_size = os.path.getsize(config_file_path) if os.path.exists(config_file_path) else 0
            
            # Count backup files
            backup_count = 0
            if self.backup_enabled and os.path.exists(self.backup_path):
                backup_files = [f for f in os.listdir(self.backup_path) if f.startswith("config_") and f.endswith(".json")]
                backup_count = len(backup_files)
                
            return {
                "status": "success",
                "stats": {
                    "key_count": key_count,
                    "file_size": file_size,
                    "backup_enabled": self.backup_enabled,
                    "backup_count": backup_count,
                    "validation_enabled": self.validation_enabled,
                    "config_path": self.config_path,
                    "config_file": self.config_file
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting configuration statistics: {str(e)}")
            return {"status": "error", "message": str(e)}