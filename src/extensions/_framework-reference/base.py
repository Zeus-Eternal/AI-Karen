"""
Base extension class for the AI Karen Extensions System.

This module provides the BaseExtension class that all extensions must inherit from,
providing common functionality for API creation, plugin orchestration, and lifecycle management.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from fastapi import APIRouter
import asyncio

from .models import ExtensionManifest, ExtensionContext, ExtensionStatus
from .security_decorators import (
    require_permission, 
    audit_log, 
    security_monitor,
    get_extension_permissions,
    get_resource_usage,
    is_within_resource_limits
)


class BaseExtension(ABC):
    """
    Base class for all AI Karen extensions.
    
    Extensions must inherit from this class and implement the required abstract methods.
    This class provides common functionality for API creation, plugin orchestration,
    data management, and lifecycle management.
    """
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        """
        Initialize the base extension.
        
        Args:
            manifest: Extension manifest with configuration
            context: Extension execution context
        """
        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        
        # Extension state
        self._status = ExtensionStatus.NOT_LOADED
        self._initialized = False
        self._error = None
        
        # Extension services (will be injected by extension manager)
        self.plugin_orchestrator = None
        self.data_manager = None
        self.mcp_server = None
        self.security_manager = None
        
        self.logger.info(f"Extension {manifest.name} v{manifest.version} created")
    
    async def initialize(self) -> None:
        """
        Initialize the extension.
        
        This method handles the common initialization logic and calls the
        extension-specific _initialize method.
        """
        try:
            self.logger.info(f"Initializing extension {self.manifest.name}")
            self._status = ExtensionStatus.LOADING
            
            # Call extension-specific initialization
            await self._initialize()
            
            self._status = ExtensionStatus.ACTIVE
            self._initialized = True
            self._error = None
            
            self.logger.info(f"Extension {self.manifest.name} initialized successfully")
            
        except Exception as e:
            self._status = ExtensionStatus.ERROR
            self._error = str(e)
            self.logger.error(f"Failed to initialize extension {self.manifest.name}: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Shutdown the extension.
        
        This method handles the common shutdown logic and calls the
        extension-specific _shutdown method.
        """
        try:
            self.logger.info(f"Shutting down extension {self.manifest.name}")
            self._status = ExtensionStatus.UNLOADING
            
            # Call extension-specific shutdown
            await self._shutdown()
            
            self._status = ExtensionStatus.NOT_LOADED
            self._initialized = False
            
            self.logger.info(f"Extension {self.manifest.name} shut down successfully")
            
        except Exception as e:
            self._status = ExtensionStatus.ERROR
            self._error = str(e)
            self.logger.error(f"Failed to shutdown extension {self.manifest.name}: {e}")
            raise
    
    @abstractmethod
    async def _initialize(self) -> None:
        """
        Extension-specific initialization logic.
        
        Extensions must implement this method to perform their specific
        initialization tasks.
        """
        pass
    
    @abstractmethod
    async def _shutdown(self) -> None:
        """
        Extension-specific shutdown logic.
        
        Extensions must implement this method to perform their specific
        cleanup tasks.
        """
        pass
    
    def create_api_router(self) -> Optional[APIRouter]:
        """
        Create FastAPI router for the extension.
        
        Extensions that provide API endpoints should override this method
        to return a configured APIRouter.
        
        Returns:
            Optional[APIRouter]: The API router or None if no API provided
        """
        if not self.manifest.capabilities.provides_api:
            return None
        
        # Default implementation - extensions should override
        router = APIRouter()
        
        # Add a default health endpoint
        @router.get("/health")
        async def extension_health():
            """Extension health check endpoint."""
            return {
                "extension": self.manifest.name,
                "version": self.manifest.version,
                "status": self._status.value,
                "healthy": self._status == ExtensionStatus.ACTIVE
            }
        
        return router
    
    def create_background_tasks(self) -> List[Dict[str, Any]]:
        """
        Create background tasks for the extension.
        
        Extensions that provide background tasks should override this method
        to return a list of task configurations.
        
        Returns:
            List[Dict[str, Any]]: List of background task configurations
        """
        if not self.manifest.capabilities.provides_background_tasks:
            return []
        
        # Convert manifest background tasks to runtime format
        tasks = []
        for task_config in self.manifest.background_tasks:
            if task_config.enabled:
                tasks.append({
                    'name': task_config.name,
                    'schedule': task_config.schedule,
                    'function': task_config.function,
                    'description': task_config.description,
                    'extension': self.manifest.name
                })
        
        return tasks
    
    def create_ui_components(self) -> Dict[str, Any]:
        """
        Create UI components for the extension.
        
        Extensions that provide UI should override this method to return
        UI component configurations.
        
        Returns:
            Dict[str, Any]: UI component configurations
        """
        if not self.manifest.capabilities.provides_ui:
            return {}
        
        components = {
            'control_room_pages': [],
            'metadata': {
                'extension': self.manifest.name,
                'display_name': self.manifest.display_name,
                'description': self.manifest.description,
                'version': self.manifest.version
            }
        }

        # Add control room pages
        for page in self.manifest.ui.control_room_pages:
            components['control_room_pages'].append({
                'name': page.name,
                'path': page.path,
                'icon': page.icon,
                'permissions': page.permissions,
                'extension': self.manifest.name
            })
        
        return components
    
    def create_mcp_server(self) -> Optional[Any]:
        """
        Create MCP server for the extension.
        
        Extensions that want to expose MCP tools should override this method.
        
        Returns:
            Optional[Any]: MCP server instance or None
        """
        # MCP integration will be implemented in a future task
        return None
    
    async def register_mcp_tool(
        self, 
        name: str, 
        handler: Callable, 
        schema: Dict[str, Any], 
        description: str
    ) -> bool:
        """
        Register an MCP tool for AI integration.
        
        Args:
            name: Tool name
            handler: Tool handler function
            schema: Tool parameter schema
            description: Tool description
            
        Returns:
            bool: True if registration successful
        """
        # MCP integration will be implemented in a future task
        self.logger.debug(f"MCP tool registration not yet implemented: {name}")
        return False
    
    async def discover_mcp_tools(self, service_pattern: str) -> Dict[str, List[Dict]]:
        """
        Discover available MCP tools.
        
        Args:
            service_pattern: Pattern to match service names
            
        Returns:
            Dict[str, List[Dict]]: Available tools by service
        """
        # MCP integration will be implemented in a future task
        self.logger.debug(f"MCP tool discovery not yet implemented: {service_pattern}")
        return {}
    
    async def call_mcp_tool(
        self, 
        service_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool from another service.
        
        Args:
            service_name: Name of the service providing the tool
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Any: Tool result
        """
        # MCP integration will be implemented in a future task
        self.logger.debug(f"MCP tool calling not yet implemented: {service_name}.{tool_name}")
        return None
    
    # Plugin orchestration methods (will be implemented when plugin orchestrator is available)
    async def execute_plugin(
        self, 
        intent: str, 
        params: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> Any:
        """
        Execute a single plugin.
        
        Args:
            intent: Plugin intent to execute
            params: Plugin parameters
            user_context: User context for execution
            
        Returns:
            Any: Plugin execution result
        """
        if self.plugin_orchestrator:
            return await self.plugin_orchestrator.execute_plugin(intent, params, user_context)
        else:
            self.logger.warning("Plugin orchestrator not available")
            return None
    
    async def execute_workflow(
        self, 
        workflow: List[Dict[str, Any]], 
        user_context: Dict[str, Any]
    ) -> Any:
        """
        Execute a workflow of plugins.
        
        Args:
            workflow: List of plugin steps
            user_context: User context for execution
            
        Returns:
            Any: Workflow execution result
        """
        if self.plugin_orchestrator:
            return await self.plugin_orchestrator.execute_workflow(workflow, user_context)
        else:
            self.logger.warning("Plugin orchestrator not available")
            return None
    
    # Data management methods (will be implemented when data manager is available)
    async def store_data(self, key: str, data: Any) -> bool:
        """
        Store extension data.
        
        Args:
            key: Data key
            data: Data to store
            
        Returns:
            bool: True if storage successful
        """
        if self.data_manager:
            return await self.data_manager.store(key, data)
        else:
            self.logger.warning("Data manager not available")
            return False
    
    async def retrieve_data(self, key: str) -> Any:
        """
        Retrieve extension data.
        
        Args:
            key: Data key
            
        Returns:
            Any: Retrieved data or None
        """
        if self.data_manager:
            return await self.data_manager.retrieve(key)
        else:
            self.logger.warning("Data manager not available")
            return None
    
    async def query_data(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query extension data.
        
        Args:
            table: Table name
            filters: Query filters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        if self.data_manager:
            return await self.data_manager.query(table, filters)
        else:
            self.logger.warning("Data manager not available")
            return []
    
    # Status and health methods
    def get_status(self) -> Dict[str, Any]:
        """
        Get extension status information.
        
        Returns:
            Dict[str, Any]: Status information
        """
        return {
            'name': self.manifest.name,
            'version': self.manifest.version,
            'status': self._status.value,
            'initialized': self._initialized,
            'error': self._error,
            'capabilities': {
                'provides_ui': self.manifest.capabilities.provides_ui,
                'provides_api': self.manifest.capabilities.provides_api,
                'provides_background_tasks': self.manifest.capabilities.provides_background_tasks,
                'provides_webhooks': self.manifest.capabilities.provides_webhooks
            }
        }
    
    def is_initialized(self) -> bool:
        """
        Check if extension is initialized.
        
        Returns:
            bool: True if initialized
        """
        return self._initialized
    
    def is_healthy(self) -> bool:
        """
        Check if extension is healthy.
        
        Returns:
            bool: True if healthy
        """
        return self._status == ExtensionStatus.ACTIVE and self._error is None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform extension health check.
        
        Extensions can override this method to provide custom health checks.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        return {
            'extension': self.manifest.name,
            'version': self.manifest.version,
            'status': self._status.value,
            'healthy': self.is_healthy(),
            'initialized': self._initialized,
            'error': self._error,
            'uptime': 'unknown'  # Will be calculated by extension manager
        }
    
    # Security methods
    def check_permission(self, permission: str) -> bool:
        """
        Check if extension has a specific permission.
        
        Args:
            permission: Permission to check (e.g., 'data:read', 'system:files')
            
        Returns:
            bool: True if extension has permission
        """
        if self.security_manager:
            return self.security_manager.check_permission(self.manifest.name, permission, self.context)
        return False
    
    def get_permissions(self) -> List[str]:
        """
        Get all permissions for this extension.
        
        Returns:
            List[str]: List of permissions
        """
        return get_extension_permissions(self.manifest.name)
    
    def get_resource_usage(self) -> Optional[Dict[str, Any]]:
        """
        Get current resource usage for this extension.
        
        Returns:
            Optional[Dict[str, Any]]: Resource usage information
        """
        return get_resource_usage(self.manifest.name)
    
    def is_within_limits(self) -> bool:
        """
        Check if extension is within resource limits.
        
        Returns:
            bool: True if within limits
        """
        return is_within_resource_limits(self.manifest.name)
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get comprehensive security status for this extension.
        
        Returns:
            Dict[str, Any]: Security status information
        """
        if self.security_manager:
            return self.security_manager.get_security_status(self.manifest.name)
        return {'error': 'Security manager not available'}
    
    @require_permission('system:files')
    @audit_log('file_access')
    def secure_file_access(self, file_path: str, mode: str = 'r') -> Any:
        """
        Secure file access with permission checking and auditing.
        
        Args:
            file_path: Path to the file
            mode: File access mode
            
        Returns:
            File handle or raises PermissionError
        """
        # Additional security checks could be added here
        return open(file_path, mode)
    
    @require_permission('network:external')
    @audit_log('network_access')
    @security_monitor
    async def secure_http_request(self, url: str, **kwargs) -> Any:
        """
        Secure HTTP request with permission checking and monitoring.
        
        Args:
            url: URL to request
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response or raises PermissionError
        """
        import aiohttp
        
        # Additional network security checks could be added here
        async with aiohttp.ClientSession() as session:
            async with session.get(url, **kwargs) as response:
                return await response.json()
    
    # Utility methods
    def get_extension_path(self) -> Path:
        """
        Get the extension directory path.
        
        Returns:
            Path: Extension directory path
        """
        # This will be set by the extension manager
        return Path(f"extensions/{self.manifest.category}/{self.manifest.name}")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value for the extension.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        # Configuration management will be implemented in a future task
        return default
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """
        Set configuration value for the extension.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            bool: True if setting successful
        """
        # Configuration management will be implemented in a future task
        return False