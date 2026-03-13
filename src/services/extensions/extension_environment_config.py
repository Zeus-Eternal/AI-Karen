"""
Extension Environment Configuration service for managing extension environment configurations.

This service provides capabilities for managing environment configurations for extensions,
including environment variables, runtime settings, and deployment configurations.
"""

from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import time
import os
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionEnvironmentConfig(BaseService):
    """
    Extension Environment Configuration service for managing extension environment configurations.
    
    This service provides capabilities for managing environment configurations for extensions,
    including environment variables, runtime settings, and deployment configurations.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_environment_config"))
        self._initialized = False
        self._extension_environments: Dict[str, Dict[str, Any]] = {}  # extension_id -> environment_config
        self._environment_templates: Dict[str, Dict[str, Any]] = {}  # template_name -> template_config
        self._environment_secrets: Dict[str, Dict[str, str]] = {}  # extension_id -> secret_name -> secret_value
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Environment Configuration service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Environment Configuration service")
            
            # Initialize environment configurations
            self._extension_environments = {}
            self._environment_templates = {}
            self._environment_secrets = {}
            
            # Create default environment templates
            self._environment_templates["default"] = {
                "PYTHONPATH": "/app/src:/app/extensions",
                "PYTHONUNBUFFERED": "1",
                "TZ": "UTC",
                "LOG_LEVEL": "INFO",
                "MAX_WORKERS": "4",
                "TIMEOUT": "30"
            }
            
            self._environment_templates["production"] = {
                "PYTHONPATH": "/app/src:/app/extensions",
                "PYTHONUNBUFFERED": "1",
                "TZ": "UTC",
                "LOG_LEVEL": "WARNING",
                "MAX_WORKERS": "8",
                "TIMEOUT": "60",
                "DEBUG": "false"
            }
            
            self._environment_templates["development"] = {
                "PYTHONPATH": "/app/src:/app/extensions",
                "PYTHONUNBUFFERED": "1",
                "TZ": "UTC",
                "LOG_LEVEL": "DEBUG",
                "MAX_WORKERS": "2",
                "TIMEOUT": "120",
                "DEBUG": "true",
                "DEV_MODE": "true"
            }
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Environment Configuration service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Environment Configuration service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def create_environment(self, extension_id: str, template_name: str = "default", overrides: Optional[Dict[str, Any]] = None) -> None:
        """Create an environment configuration for an extension."""
        async with self._lock:
            # Get template
            if template_name not in self._environment_templates:
                raise ValueError(f"Environment template '{template_name}' not found")
                
            template = self._environment_templates[template_name].copy()
            
            # Apply overrides
            if overrides:
                template.update(overrides)
                
            # Create environment configuration
            self._extension_environments[extension_id] = {
                "template": template_name,
                "variables": template,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Initialize secrets for the extension
            self._environment_secrets[extension_id] = {}
            
        self.logger.info(f"Created environment configuration for extension {extension_id} using template {template_name}")
        
    async def update_environment(self, extension_id: str, updates: Dict[str, Any]) -> None:
        """Update an environment configuration for an extension."""
        async with self._lock:
            if extension_id not in self._extension_environments:
                raise ValueError(f"Environment configuration for extension '{extension_id}' not found")
                
            # Update variables
            if "variables" in updates:
                self._extension_environments[extension_id]["variables"].update(updates["variables"])
                
            # Update template
            if "template" in updates:
                template_name = updates["template"]
                if template_name not in self._environment_templates:
                    raise ValueError(f"Environment template '{template_name}' not found")
                    
                # Get new template and merge with existing variables
                template = self._environment_templates[template_name].copy()
                existing_vars = self._extension_environments[extension_id]["variables"]
                template.update(existing_vars)
                
                self._extension_environments[extension_id]["template"] = template_name
                self._extension_environments[extension_id]["variables"] = template
                
            # Update timestamp
            self._extension_environments[extension_id]["updated_at"] = datetime.now().isoformat()
            
        self.logger.info(f"Updated environment configuration for extension {extension_id}")
        
    async def get_environment(self, extension_id: str) -> Dict[str, Any]:
        """Get the environment configuration for an extension."""
        async with self._lock:
            if extension_id not in self._extension_environments:
                raise ValueError(f"Environment configuration for extension '{extension_id}' not found")
                
            return self._extension_environments[extension_id].copy()
            
    async def get_environment_variables(self, extension_id: str) -> Dict[str, str]:
        """Get the environment variables for an extension."""
        async with self._lock:
            if extension_id not in self._extension_environments:
                raise ValueError(f"Environment configuration for extension '{extension_id}' not found")
                
            variables = self._extension_environments[extension_id]["variables"].copy()
            
            # Add secrets if any
            if extension_id in self._environment_secrets:
                variables.update(self._environment_secrets[extension_id])
                
            return variables
            
    async def delete_environment(self, extension_id: str) -> None:
        """Delete the environment configuration for an extension."""
        async with self._lock:
            if extension_id in self._extension_environments:
                del self._extension_environments[extension_id]
                
            if extension_id in self._environment_secrets:
                del self._environment_secrets[extension_id]
                
        self.logger.info(f"Deleted environment configuration for extension {extension_id}")
        
    async def create_template(self, template_name: str, variables: Dict[str, Any]) -> None:
        """Create an environment template."""
        async with self._lock:
            self._environment_templates[template_name] = variables.copy()
            
        self.logger.info(f"Created environment template {template_name}")
        
    async def update_template(self, template_name: str, updates: Dict[str, Any]) -> None:
        """Update an environment template."""
        async with self._lock:
            if template_name not in self._environment_templates:
                raise ValueError(f"Environment template '{template_name}' not found")
                
            self._environment_templates[template_name].update(updates)
            
        self.logger.info(f"Updated environment template {template_name}")
        
    async def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get an environment template."""
        async with self._lock:
            if template_name not in self._environment_templates:
                raise ValueError(f"Environment template '{template_name}' not found")
                
            return self._environment_templates[template_name].copy()
            
    async def list_templates(self) -> List[str]:
        """List all environment template names."""
        async with self._lock:
            return list(self._environment_templates.keys())
            
    async def delete_template(self, template_name: str) -> None:
        """Delete an environment template."""
        async with self._lock:
            if template_name in self._environment_templates:
                del self._environment_templates[template_name]
                
        self.logger.info(f"Deleted environment template {template_name}")
        
    async def set_secret(self, extension_id: str, secret_name: str, secret_value: str) -> None:
        """Set a secret for an extension."""
        async with self._lock:
            if extension_id not in self._environment_secrets:
                self._environment_secrets[extension_id] = {}
                
            self._environment_secrets[extension_id][secret_name] = secret_value
            
        self.logger.info(f"Set secret '{secret_name}' for extension {extension_id}")
        
    async def get_secret(self, extension_id: str, secret_name: str) -> str:
        """Get a secret for an extension."""
        async with self._lock:
            if extension_id not in self._environment_secrets or secret_name not in self._environment_secrets[extension_id]:
                raise ValueError(f"Secret '{secret_name}' for extension '{extension_id}' not found")
                
            return self._environment_secrets[extension_id][secret_name]
            
    async def delete_secret(self, extension_id: str, secret_name: str) -> None:
        """Delete a secret for an extension."""
        async with self._lock:
            if extension_id in self._environment_secrets and secret_name in self._environment_secrets[extension_id]:
                del self._environment_secrets[extension_id][secret_name]
                
        self.logger.info(f"Deleted secret '{secret_name}' for extension {extension_id}")
        
    async def export_environment(self, extension_id: str, format: str = "env") -> str:
        """Export an environment configuration to a specific format."""
        environment = await self.get_environment(extension_id)
        variables = environment["variables"]
        
        if format.lower() == "env":
            # Export as .env file format
            lines = []
            for key, value in variables.items():
                lines.append(f"{key}={value}")
            return "\n".join(lines)
        elif format.lower() == "json":
            # Export as JSON
            import json
            return json.dumps(variables, indent=2)
        elif format.lower() == "yaml":
            # Export as YAML
            import yaml
            return yaml.dump(variables, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    async def import_environment(self, extension_id: str, content: str, format: str = "env", template_name: str = "default") -> None:
        """Import an environment configuration from a specific format."""
        variables = {}
        
        if format.lower() == "env":
            # Parse .env file format
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        variables[key.strip()] = value.strip()
        elif format.lower() == "json":
            # Parse JSON
            import json
            variables = json.loads(content)
        elif format.lower() == "yaml":
            # Parse YAML
            import yaml
            variables = yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported import format: {format}")
            
        # Create environment with imported variables
        await self.create_environment(extension_id, template_name, variables)
        
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "extension_environments": len(self._extension_environments),
                "environment_templates": len(self._environment_templates),
                "extension_secrets": len(self._environment_secrets)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Environment Configuration service")
        
        self._extension_environments.clear()
        self._environment_templates.clear()
        self._environment_secrets.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Environment Configuration service shutdown complete")