"""
KAREN Integration Module for Llama.cpp Server

This module provides seamless integration with KAREN, including:
- Auto-configuration
- API compatibility
- Model sharing
- Authentication synchronization
- Settings synchronization
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import shutil

from .config_manager import ConfigManager
from .security_manager import SecurityManager, User, UserRole, Permission

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class KARENIntegration:
    """
    KAREN Integration class that handles seamless integration with KAREN
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize KAREN integration with configuration"""
        self.config_manager = ConfigManager(config_path)
        self.security_manager = SecurityManager(config_path)
        
        # KAREN paths
        self.karen_config_path = self._find_karen_config()
        self.karen_models_path = self._find_karen_models()
        
        # Integration status
        self.is_enabled = self.config_manager.get("karen.enabled", False)
        self.is_configured = self.karen_config_path is not None
        
        logger.info(f"KAREN integration initialized (enabled: {self.is_enabled}, configured: {self.is_configured})")
    
    def _find_karen_config(self) -> Optional[Path]:
        """Find KAREN configuration file"""
        # Common KAREN config paths
        possible_paths = [
            Path.home() / ".karen" / "config.json",
            Path.home() / ".config" / "karen" / "config.json",
            Path.cwd() / "config" / "karen.json",
            Path.cwd() / "karen_config.json"
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found KAREN config at {path}")
                return path
        
        return None
    
    def _find_karen_models(self) -> Optional[Path]:
        """Find KAREN models directory"""
        # Common KAREN models paths
        possible_paths = [
            Path.home() / ".karen" / "models",
            Path.home() / ".local" / "share" / "karen" / "models",
            Path.cwd() / "models" / "karen",
            Path.cwd() / "karen_models"
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                logger.info(f"Found KAREN models at {path}")
                return path
        
        return None
    
    def enable_integration(self) -> bool:
        """
        Enable KAREN integration
        
        Returns:
            True if integration was enabled successfully, False otherwise
        """
        if not self.is_configured:
            logger.error("Cannot enable KAREN integration: KAREN not found")
            return False
        
        self.is_enabled = True
        self.config_manager.set("karen.enabled", True)
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        logger.info("KAREN integration enabled")
        return True
    
    def disable_integration(self) -> bool:
        """
        Disable KAREN integration
        
        Returns:
            True if integration was disabled successfully, False otherwise
        """
        self.is_enabled = False
        self.config_manager.set("karen.enabled", False)
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        logger.info("KAREN integration disabled")
        return True
    
    def get_karen_config(self) -> Optional[Dict[str, Any]]:
        """
        Get KAREN configuration
        
        Returns:
            KAREN configuration as a dictionary, or None if not found
        """
        if not self.karen_config_path:
            return None
        
        try:
            with open(self.karen_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load KAREN config: {e}")
            return None
    
    def sync_config_from_karen(self) -> bool:
        """
        Sync configuration from KAREN to Llama.cpp Server
        
        Returns:
            True if sync was successful, False otherwise
        """
        if not self.is_enabled or not self.is_configured:
            return False
        
        karen_config = self.get_karen_config()
        if not karen_config:
            return False
        
        # Map KAREN config keys to Llama.cpp Server config keys
        config_mapping = {
            # Model settings
            "model_path": "model.path",
            "model_directory": "models.directory",
            "context_length": "server.n_ctx",
            "threads": "server.threads",
            "low_vram": "server.low_vram",
            
            # Server settings
            "host": "server.host",
            "port": "server.port",
            
            # Security settings
            "enable_auth": "security.enable_jwt",
            "api_key_required": "security.enable_api_keys",
            "enable_rate_limiting": "security.enable_rate_limiting",
            "max_login_attempts": "security.max_login_attempts",
            "lockout_duration": "security.login_lockout_duration",
            
            # Performance settings
            "performance_mode": "system.performance_mode",
            "optimize_on_startup": "system.optimize_on_startup"
        }
        
        # Sync configuration
        for karen_key, server_key in config_mapping.items():
            if karen_key in karen_config:
                self.config_manager.set(server_key, karen_config[karen_key])
        
        # Save configuration
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        logger.info("Configuration synced from KAREN")
        return True
    
    def sync_config_to_karen(self) -> bool:
        """
        Sync configuration from Llama.cpp Server to KAREN
        
        Returns:
            True if sync was successful, False otherwise
        """
        if not self.is_enabled or not self.is_configured:
            return False
        
        # Load current KAREN config
        karen_config = self.get_karen_config() or {}
        
        # Map Llama.cpp Server config keys to KAREN config keys
        config_mapping = {
            # Model settings
            "model.path": "model_path",
            "models.directory": "model_directory",
            "server.n_ctx": "context_length",
            "server.threads": "threads",
            "server.low_vram": "low_vram",
            
            # Server settings
            "server.host": "host",
            "server.port": "port",
            
            # Security settings
            "security.enable_jwt": "enable_auth",
            "security.enable_api_keys": "api_key_required",
            "security.enable_rate_limiting": "enable_rate_limiting",
            "security.max_login_attempts": "max_login_attempts",
            "security.login_lockout_duration": "lockout_duration",
            
            # Performance settings
            "system.performance_mode": "performance_mode",
            "system.optimize_on_startup": "optimize_on_startup"
        }
        
        # Sync configuration
        for server_key, karen_key in config_mapping.items():
            value = self.config_manager.get(server_key)
            if value is not None:
                karen_config[karen_key] = value
        
        # Save KAREN configuration
        try:
            if self.karen_config_path:
                with open(str(self.karen_config_path), 'w') as f:
                    json.dump(karen_config, f, indent=2)
            
            logger.info("Configuration synced to KAREN")
            return True
        except Exception as e:
            logger.error(f"Failed to save KAREN config: {e}")
            return False
    
    def sync_users_from_karen(self) -> bool:
        """
        Sync users from KAREN to Llama.cpp Server
        
        Returns:
            True if sync was successful, False otherwise
        """
        if not self.is_enabled or not self.is_configured:
            return False
        
        karen_config = self.get_karen_config()
        if not karen_config:
            return False
        
        # Get users from KAREN config
        karen_users = karen_config.get("users", [])
        
        # Sync users
        for karen_user in karen_users:
            username = karen_user.get("username")
            if not username:
                continue
            
            # Check if user already exists
            if username in self.security_manager.users:
                # Update existing user
                user = self.security_manager.users[username]
                
                # Update role
                if "role" in karen_user:
                    try:
                        user.role = UserRole(karen_user["role"])
                    except ValueError:
                        logger.warning(f"Invalid role for user {username}: {karen_user['role']}")
                
                # Update permissions
                if "permissions" in karen_user:
                    try:
                        user.permissions = [Permission(p) for p in karen_user["permissions"]]
                    except ValueError:
                        logger.warning(f"Invalid permissions for user {username}: {karen_user['permissions']}")
                
                # Update active status
                if "active" in karen_user:
                    user.active = karen_user["active"]
            else:
                # Create new user
                try:
                    role = UserRole(karen_user.get("role", "user"))
                    permissions = []
                    
                    if "permissions" in karen_user:
                        try:
                            permissions = [Permission(p) for p in karen_user["permissions"]]
                        except ValueError:
                            logger.warning(f"Invalid permissions for user {username}: {karen_user['permissions']}")
                    
                    # Generate a temporary password
                    temp_password = f"temp_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    self.security_manager.create_user(
                        username,
                        temp_password,
                        role,
                        permissions
                    )
                    
                    # Mark user as requiring password change
                    user = self.security_manager.users[username]
                    user.active = karen_user.get("active", True)
                    
                    logger.info(f"Created user {username} from KAREN config")
                except ValueError as e:
                    logger.warning(f"Failed to create user {username}: {e}")
        
        # Save security data
        self.security_manager._save_security_data()
        
        logger.info("Users synced from KAREN")
        return True
    
    def sync_models(self) -> bool:
        """
        Sync models between KAREN and Llama.cpp Server
        
        Returns:
            True if sync was successful, False otherwise
        """
        if not self.is_enabled or not self.is_configured:
            return False
        
        if not self.karen_models_path:
            logger.warning("KAREN models directory not found")
            return False
        
        # Get models directory from config
        models_dir = Path(self.config_manager.get("models.directory", "models"))
        
        # Create models directory if it doesn't exist
        if not models_dir.exists():
            models_dir.mkdir(parents=True, exist_ok=True)
        
        # Sync models from KAREN to Llama.cpp Server
        synced_count = 0
        for model_file in self.karen_models_path.glob("*.gguf"):
            target_path = models_dir / model_file.name
            
            # Skip if model already exists and is up to date
            if target_path.exists() and target_path.stat().st_mtime >= model_file.stat().st_mtime:
                continue
            
            try:
                # Copy model file
                shutil.copy2(model_file, target_path)
                synced_count += 1
                logger.info(f"Synced model {model_file.name}")
            except Exception as e:
                logger.error(f"Failed to sync model {model_file.name}: {e}")
        
        logger.info(f"Synced {synced_count} models from KAREN")
        return synced_count > 0
    
    def auto_configure(self) -> bool:
        """
        Auto-configure Llama.cpp Server based on KAREN configuration
        
        Returns:
            True if auto-configuration was successful, False otherwise
        """
        if not self.is_configured:
            logger.warning("KAREN not found, skipping auto-configuration")
            return False
        
        # Enable integration
        self.enable_integration()
        
        # Sync configuration
        self.sync_config_from_karen()
        
        # Sync users
        self.sync_users_from_karen()
        
        # Sync models
        self.sync_models()
        
        logger.info("Auto-configuration completed")
        return True
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get the current integration status
        
        Returns:
            Dictionary with integration status information
        """
        return {
            "enabled": self.is_enabled,
            "configured": self.is_configured,
            "karen_config_path": str(self.karen_config_path) if self.karen_config_path else None,
            "karen_models_path": str(self.karen_models_path) if self.karen_models_path else None,
            "last_sync": self.config_manager.get("karen.last_sync"),
            "auto_sync_enabled": self.config_manager.get("karen.auto_sync", True)
        }
    
    def enable_auto_sync(self) -> bool:
        """
        Enable automatic synchronization with KAREN
        
        Returns:
            True if auto-sync was enabled successfully, False otherwise
        """
        self.config_manager.set("karen.auto_sync", True)
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        logger.info("Auto-sync with KAREN enabled")
        return True
    
    def disable_auto_sync(self) -> bool:
        """
        Disable automatic synchronization with KAREN
        
        Returns:
            True if auto-sync was disabled successfully, False otherwise
        """
        self.config_manager.set("karen.auto_sync", False)
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        logger.info("Auto-sync with KAREN disabled")
        return True
    
    def perform_sync(self) -> bool:
        """
        Perform a full synchronization with KAREN
        
        Returns:
            True if sync was successful, False otherwise
        """
        if not self.is_enabled or not self.is_configured:
            return False
        
        logger.info("Starting full sync with KAREN")
        
        # Sync configuration
        config_synced = self.sync_config_from_karen()
        
        # Sync users
        users_synced = self.sync_users_from_karen()
        
        # Sync models
        models_synced = self.sync_models()
        
        # Update last sync time
        self.config_manager.set("karen.last_sync", datetime.now().isoformat())
        if hasattr(self.config_manager, 'save'):
            self.config_manager.save()
        
        success = config_synced or users_synced or models_synced
        
        if success:
            logger.info("Full sync with KAREN completed")
        else:
            logger.warning("Full sync with KAREN completed with no changes")
        
        return success
    
    def export_config_to_karen(self) -> Dict[str, Any]:
        """
        Export Llama.cpp Server configuration to KAREN format
        
        Returns:
            KAREN-compatible configuration dictionary
        """
        # Get current configuration
        config = {
            "llamacpp_server": {
                "version": "1.0.0",
                "enabled": True
            }
        }
        
        # Add model settings
        config["model"] = {
            "path": self.config_manager.get("model.path"),
            "directory": self.config_manager.get("models.directory"),
            "context_length": self.config_manager.get("server.n_ctx"),
            "threads": self.config_manager.get("server.threads"),
            "low_vram": self.config_manager.get("server.low_vram")
        }
        
        # Add server settings
        config["server"] = {
            "host": self.config_manager.get("server.host"),
            "port": self.config_manager.get("server.port")
        }
        
        # Add security settings
        config["security"] = {
            "enable_auth": self.config_manager.get("security.enable_jwt"),
            "api_key_required": self.config_manager.get("security.enable_api_keys"),
            "enable_rate_limiting": self.config_manager.get("security.enable_rate_limiting"),
            "max_login_attempts": self.config_manager.get("security.max_login_attempts"),
            "lockout_duration": self.config_manager.get("security.login_lockout_duration")
        }
        
        # Add performance settings
        config["performance"] = {
            "mode": self.config_manager.get("system.performance_mode"),
            "optimize_on_startup": self.config_manager.get("system.optimize_on_startup")
        }
        
        return config
    
    def create_karen_integration_script(self) -> str:
        """
        Create a script for KAREN to integrate with Llama.cpp Server
        
        Returns:
            Path to the created script
        """
        script_content = f'''#!/usr/bin/env python3
"""
KAREN Integration Script for Llama.cpp Server

This script configures KAREN to work with Llama.cpp Server
"""

import json
import os
from pathlib import Path

# Llama.cpp Server configuration
LLAMACPP_CONFIG = {{
    "host": "{self.config_manager.get('server.host', 'localhost')}",
    "port": {self.config_manager.get('server.port', 8000)},
    "api_path": "/api/v1",
    "auth_required": {str(self.config_manager.get('security.enable_jwt', True)).lower()},
    "api_key_required": {str(self.config_manager.get('security.enable_api_keys', True)).lower()}
}}

# KAREN configuration path
KAREN_CONFIG_PATH = Path.home() / ".karen" / "config.json"

def main():
    """Main function"""
    print("Configuring KAREN to work with Llama.cpp Server...")
    
    # Load existing KAREN config
    karen_config = {{}}
    if KAREN_CONFIG_PATH.exists():
        try:
            with open(KAREN_CONFIG_PATH, 'r') as f:
                karen_config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load KAREN config: {{e}}")
    
    # Update KAREN config with Llama.cpp Server settings
    karen_config["llamacpp_server"] = LLAMACPP_CONFIG
    
    # Create KAREN config directory if it doesn't exist
    KAREN_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save KAREN config
    try:
        with open(KAREN_CONFIG_PATH, 'w') as f:
            json.dump(karen_config, f, indent=2)
        
        print(f"KAREN configuration updated at: {{KAREN_CONFIG_PATH}}")
        print("Please restart KAREN for changes to take effect.")
    except Exception as e:
        print(f"Error: Failed to save KAREN config: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
        
        # Write script to file
        script_path = Path("karen_integration.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"Created KAREN integration script at {script_path}")
        return str(script_path)