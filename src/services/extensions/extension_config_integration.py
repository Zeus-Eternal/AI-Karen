"""
Extension Configuration Integration service for integrating extension configurations with other systems.

This service provides capabilities for integrating extension configurations with other
systems, including configuration synchronization and cross-system compatibility.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import asyncio
import logging
import json
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionConfigIntegration(BaseService):
    """
    Extension Configuration Integration service for integrating extension configurations with other systems.
    
    This service provides capabilities for integrating extension configurations with other
    systems, including configuration synchronization and cross-system compatibility.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_config_integration"))
        self._initialized = False
        self._integration_targets: Dict[str, Dict[str, Any]] = {}  # target_name -> target_config
        self._integration_mappings: Dict[str, Dict[str, str]] = {}  # target_name -> field_mappings
        self._sync_status: Dict[str, Dict[str, Any]] = {}  # target_name -> sync_status
        self._integration_history: List[Dict[str, Any]] = []  # list of integration_events
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Configuration Integration service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Configuration Integration service")
            
            # Initialize integration targets
            self._integration_targets = {}
            self._integration_mappings = {}
            self._sync_status = {}
            self._integration_history = []
            
            # Create default integration targets
            self._integration_targets["kubernetes"] = {
                "type": "kubernetes",
                "enabled": False,
                "config": {
                    "namespace": "default",
                    "config_map_prefix": "ext-",
                    "secret_prefix": "ext-secret-"
                }
            }
            
            self._integration_targets["docker"] = {
                "type": "docker",
                "enabled": False,
                "config": {
                    "registry": "",
                    "image_prefix": "ext-",
                    "network": "bridge"
                }
            }
            
            self._integration_targets["database"] = {
                "type": "database",
                "enabled": False,
                "config": {
                    "table_prefix": "ext_",
                    "connection_string": ""
                }
            }
            
            # Create default integration mappings
            self._integration_mappings["kubernetes"] = {
                "name": "metadata.name",
                "version": "metadata.annotations.version",
                "description": "metadata.annotations.description",
                "resources.cpu": "spec.resources.requests.cpu",
                "resources.memory": "spec.resources.requests.memory",
                "resources.storage": "spec.volumes[0].persistentVolumeClaim.resources.requests.storage"
            }
            
            self._integration_mappings["docker"] = {
                "name": "Image",
                "version": "Tag",
                "description": "Label.description",
                "resources.cpu": "HostConfig.Resources.CPUShares",
                "resources.memory": "HostConfig.Resources.Memory",
                "entrypoint": "Entrypoint"
            }
            
            self._integration_mappings["database"] = {
                "name": "name",
                "version": "version",
                "description": "description",
                "created_at": "created_at",
                "updated_at": "updated_at"
            }
            
            # Initialize sync status
            for target_name in self._integration_targets:
                self._sync_status[target_name] = {
                    "last_sync": None,
                    "sync_count": 0,
                    "error_count": 0,
                    "status": "not_configured"
                }
                
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Configuration Integration service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Configuration Integration service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def register_integration_target(self, target_name: str, target_config: Dict[str, Any], 
                                      mappings: Optional[Dict[str, str]] = None) -> None:
        """Register an integration target."""
        async with self._lock:
            self._integration_targets[target_name] = target_config
            
            if mappings:
                self._integration_mappings[target_name] = mappings
                
            # Initialize sync status if not exists
            if target_name not in self._sync_status:
                self._sync_status[target_name] = {
                    "last_sync": None,
                    "sync_count": 0,
                    "error_count": 0,
                    "status": "configured"
                }
                
        self.logger.info(f"Registered integration target: {target_name}")
        
    async def update_integration_target(self, target_name: str, config_updates: Dict[str, Any]) -> None:
        """Update an integration target configuration."""
        async with self._lock:
            if target_name not in self._integration_targets:
                raise ValueError(f"Integration target '{target_name}' not found")
                
            # Update configuration
            if "config" in self._integration_targets[target_name]:
                self._integration_targets[target_name]["config"].update(config_updates)
            else:
                self._integration_targets[target_name]["config"] = config_updates
                
        self.logger.info(f"Updated integration target: {target_name}")
        
    async def get_integration_target(self, target_name: str) -> Dict[str, Any]:
        """Get an integration target configuration."""
        async with self._lock:
            if target_name not in self._integration_targets:
                raise ValueError(f"Integration target '{target_name}' not found")
                
            return self._integration_targets[target_name].copy()
            
    async def list_integration_targets(self) -> List[str]:
        """List all integration target names."""
        async with self._lock:
            return list(self._integration_targets.keys())
            
    async def enable_integration_target(self, target_name: str) -> None:
        """Enable an integration target."""
        async with self._lock:
            if target_name not in self._integration_targets:
                raise ValueError(f"Integration target '{target_name}' not found")
                
            self._integration_targets[target_name]["enabled"] = True
            
            # Update sync status
            if target_name in self._sync_status:
                self._sync_status[target_name]["status"] = "enabled"
                
        self.logger.info(f"Enabled integration target: {target_name}")
        
    async def disable_integration_target(self, target_name: str) -> None:
        """Disable an integration target."""
        async with self._lock:
            if target_name not in self._integration_targets:
                raise ValueError(f"Integration target '{target_name}' not found")
                
            self._integration_targets[target_name]["enabled"] = False
            
            # Update sync status
            if target_name in self._sync_status:
                self._sync_status[target_name]["status"] = "disabled"
                
        self.logger.info(f"Disabled integration target: {target_name}")
        
    async def update_mappings(self, target_name: str, mappings: Dict[str, str]) -> None:
        """Update field mappings for an integration target."""
        async with self._lock:
            if target_name not in self._integration_targets:
                raise ValueError(f"Integration target '{target_name}' not found")
                
            self._integration_mappings[target_name] = mappings
            
        self.logger.info(f"Updated mappings for integration target: {target_name}")
        
    async def get_mappings(self, target_name: str) -> Dict[str, str]:
        """Get field mappings for an integration target."""
        async with self._lock:
            if target_name not in self._integration_mappings:
                raise ValueError(f"Mappings for integration target '{target_name}' not found")
                
            return self._integration_mappings[target_name].copy()
            
    async def sync_configuration(self, extension_id: str, config: Dict[str, Any], 
                               target_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sync extension configuration to integration targets."""
        if target_names is None:
            # Sync to all enabled targets
            target_names = []
            async with self._lock:
                for name, target in self._integration_targets.items():
                    if target.get("enabled", False):
                        target_names.append(name)
                        
        results = {}
        
        for target_name in target_names:
            try:
                # Get target configuration and mappings
                target_config = await self.get_integration_target(target_name)
                mappings = await self.get_mappings(target_name)
                
                # Transform configuration
                transformed_config = self._transform_config(config, mappings)
                
                # Apply to target
                result = await self._apply_to_target(target_name, extension_id, transformed_config, target_config)
                
                # Update sync status
                async with self._lock:
                    if target_name in self._sync_status:
                        self._sync_status[target_name]["last_sync"] = datetime.now().isoformat()
                        self._sync_status[target_name]["sync_count"] += 1
                        self._sync_status[target_name]["status"] = "synced"
                        
                # Record integration event
                integration_event = {
                    "extension_id": extension_id,
                    "target_name": target_name,
                    "timestamp": datetime.now().isoformat(),
                    "success": True
                }
                
                async with self._lock:
                    self._integration_history.append(integration_event)
                    
                results[target_name] = result
                
                self.logger.info(f"Synced configuration for extension {extension_id} to target {target_name}")
                
            except Exception as e:
                # Update sync status
                async with self._lock:
                    if target_name in self._sync_status:
                        self._sync_status[target_name]["error_count"] += 1
                        self._sync_status[target_name]["status"] = "error"
                        
                # Record failed integration event
                integration_event = {
                    "extension_id": extension_id,
                    "target_name": target_name,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                }
                
                async with self._lock:
                    self._integration_history.append(integration_event)
                    
                results[target_name] = {
                    "success": False,
                    "error": str(e)
                }
                
                self.logger.error(f"Failed to sync configuration for extension {extension_id} to target {target_name}: {str(e)}")
                
        return results
        
    async def get_sync_status(self, target_name: Optional[str] = None) -> Dict[str, Any]:
        """Get sync status for integration targets."""
        async with self._lock:
            if target_name:
                if target_name not in self._sync_status:
                    raise ValueError(f"Sync status for integration target '{target_name}' not found")
                return self._sync_status[target_name].copy()
            else:
                return self._sync_status.copy()
                
    async def get_integration_history(self, extension_id: Optional[str] = None,
                                     target_name: Optional[str] = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Get integration history."""
        async with self._lock:
            history = self._integration_history.copy()
            
            # Filter by extension_id if provided
            if extension_id:
                history = [event for event in history if event.get("extension_id") == extension_id]
                
            # Filter by target_name if provided
            if target_name:
                history = [event for event in history if event.get("target_name") == target_name]
                
            # Sort by timestamp (newest first)
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Limit results
            return history[:limit]
            
    def _transform_config(self, config: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Transform configuration using field mappings."""
        transformed = {}
        
        for source_field, target_field in mappings.items():
            # Handle nested fields
            if "." in target_field:
                # Create nested structure
                parts = target_field.split(".")
                current = transformed
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
                # Set value
                if source_field in config:
                    current[parts[-1]] = config[source_field]
            else:
                # Simple field mapping
                if source_field in config:
                    transformed[target_field] = config[source_field]
                    
        return transformed
        
    async def _apply_to_target(self, target_name: str, extension_id: str, 
                              config: Dict[str, Any], target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration to an integration target."""
        target_type = target_config.get("type")
        
        if target_type == "kubernetes":
            return await self._apply_to_kubernetes(extension_id, config, target_config)
        elif target_type == "docker":
            return await self._apply_to_docker(extension_id, config, target_config)
        elif target_type == "database":
            return await self._apply_to_database(extension_id, config, target_config)
        else:
            raise ValueError(f"Unsupported integration target type: {target_type}")
            
    async def _apply_to_kubernetes(self, extension_id: str, config: Dict[str, Any], 
                                 target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration to Kubernetes."""
        # This is a placeholder implementation
        # In a real implementation, this would use the Kubernetes API to create/update resources
        
        namespace = target_config.get("config", {}).get("namespace", "default")
        config_map_prefix = target_config.get("config", {}).get("config_map_prefix", "ext-")
        
        return {
            "success": True,
            "resource_type": "ConfigMap",
            "resource_name": f"{config_map_prefix}{extension_id}",
            "namespace": namespace
        }
        
    async def _apply_to_docker(self, extension_id: str, config: Dict[str, Any], 
                              target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration to Docker."""
        # This is a placeholder implementation
        # In a real implementation, this would use the Docker API to create/update resources
        
        image_prefix = target_config.get("config", {}).get("image_prefix", "ext-")
        
        return {
            "success": True,
            "resource_type": "Image",
            "resource_name": f"{image_prefix}{extension_id}",
            "registry": target_config.get("config", {}).get("registry", "")
        }
        
    async def _apply_to_database(self, extension_id: str, config: Dict[str, Any], 
                                target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configuration to database."""
        # This is a placeholder implementation
        # In a real implementation, this would use a database connection to create/update records
        
        table_prefix = target_config.get("config", {}).get("table_prefix", "ext_")
        
        return {
            "success": True,
            "resource_type": "Table",
            "resource_name": f"{table_prefix}{extension_id}",
            "connection": target_config.get("config", {}).get("connection_string", "")
        }
        
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        # Check if any sync operations have failed
        for target_name, sync_info in self._sync_status.items():
            if sync_info.get("status") == "error":
                status = ServiceStatus.ERROR
                break
                
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "integration_targets": len(self._integration_targets),
                "enabled_targets": sum(1 for t in self._integration_targets.values() if t.get("enabled", False)),
                "sync_errors": sum(s.get("error_count", 0) for s in self._sync_status.values()),
                "integration_history": len(self._integration_history)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Configuration Integration service")
        
        self._integration_targets.clear()
        self._integration_mappings.clear()
        self._sync_status.clear()
        self._integration_history.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Configuration Integration service shutdown complete")