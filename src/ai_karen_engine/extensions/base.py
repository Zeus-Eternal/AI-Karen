"""
Base extension class that all extensions inherit from.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .models import ExtensionManifest, ExtensionContext
from .orchestrator import PluginOrchestrator
from .data_manager import ExtensionDataManager

# MCP integration (optional)
try:
    from .mcp_integration import ExtensionMCPServer, ExtensionMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ExtensionMCPServer = ExtensionMCPClient = None

try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object


class BackgroundTask:
    """Represents a background task that can be scheduled."""
    
    def __init__(self, name: str, schedule: str, function: callable):
        self.name = name
        self.schedule = schedule
        self.function = function


class BaseExtension(ABC):
    """
    Base class for all Kari extensions.
    
    Extensions inherit from this class and implement the required methods
    to provide their functionality. The base class provides common services
    like plugin orchestration, data management, and logging.
    """
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        """
        Initialize the extension.
        
        Args:
            manifest: Extension manifest with metadata and configuration
            context: Runtime context with access to core services
        """
        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        
        # Initialize core services
        self.plugin_orchestrator = PluginOrchestrator(context.plugin_router)
        self.data_manager = ExtensionDataManager(context.db_session, manifest.name)
        
        # Extension state
        self._initialized = False
        self._api_router: Optional[APIRouter] = None
        self._background_tasks: List[BackgroundTask] = []
        self._ui_components: Dict[str, Any] = {}
        
        # MCP integration (optional)
        self._mcp_server: Optional[ExtensionMCPServer] = None
        self._mcp_client: Optional[ExtensionMCPClient] = None
    
    async def initialize(self) -> None:
        """
        Initialize extension resources.
        
        This method is called when the extension is loaded. Extensions should
        override this method to set up their resources, register API routes,
        create database tables, etc.
        """
        self.logger.info(f"Initializing extension {self.manifest.name} v{self.manifest.version}")
        
        # Call extension-specific initialization
        await self._initialize()
        
        # Set up API router if extension provides API
        if self.manifest.capabilities.provides_api:
            self._api_router = self.create_api_router()
        
        # Set up background tasks if extension provides them
        if self.manifest.capabilities.provides_background_tasks:
            self._background_tasks = self.create_background_tasks()
        
        # Set up UI components if extension provides UI
        if self.manifest.capabilities.provides_ui:
            self._ui_components = self.create_ui_components()
        
        self._initialized = True
        self.logger.info(f"Extension {self.manifest.name} initialized successfully")
    
    async def shutdown(self) -> None:
        """
        Cleanup extension resources.
        
        This method is called when the extension is unloaded. Extensions should
        override this method to clean up resources, close connections, etc.
        """
        self.logger.info(f"Shutting down extension {self.manifest.name}")
        
        # Call extension-specific cleanup
        await self._shutdown()
        
        self._initialized = False
        self.logger.info(f"Extension {self.manifest.name} shut down successfully")
    
    @abstractmethod
    async def _initialize(self) -> None:
        """Extension-specific initialization logic."""
        pass
    
    async def _shutdown(self) -> None:
        """Extension-specific cleanup logic. Override if needed."""
        pass
    
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension."""
        return self._api_router
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components for integration."""
        return self._ui_components
    
    def get_background_tasks(self) -> List[BackgroundTask]:
        """Return background tasks to be scheduled."""
        return self._background_tasks
    
    def create_api_router(self) -> Optional[APIRouter]:
        """
        Create and configure the FastAPI router for this extension.
        
        Extensions that provide APIs should override this method to define
        their endpoints.
        
        Returns:
            APIRouter instance or None if no API is provided
        """
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI not available, cannot create API router")
            return None
        
        router = APIRouter(prefix=f"/extensions/{self.manifest.name}")
        return router
    
    def create_background_tasks(self) -> List[BackgroundTask]:
        """
        Create background tasks for this extension.
        
        Extensions that provide background tasks should override this method
        to define their scheduled tasks.
        
        Returns:
            List of BackgroundTask instances
        """
        tasks = []
        for task_config in self.manifest.background_tasks:
            # Convert string function reference to actual callable
            # This is a simplified implementation - in production you'd want
            # more sophisticated function resolution
            try:
                module_path, func_name = task_config.function.rsplit('.', 1)
                # For now, we'll store the function reference as a string
                # and resolve it when the task is actually executed
                task = BackgroundTask(
                    name=task_config.name,
                    schedule=task_config.schedule,
                    function=task_config.function  # Store as string for now
                )
                tasks.append(task)
            except Exception as e:
                self.logger.error(f"Failed to create background task {task_config.name}: {e}")
        
        return tasks
    
    def create_ui_components(self) -> Dict[str, Any]:
        """
        Create UI components for this extension.
        
        Extensions that provide UI should override this method to define
        their UI components for integration with the Control Room and
        Streamlit interfaces.
        
        Returns:
            Dictionary of UI components
        """
        components = {}
        
        # Control Room pages
        if self.manifest.ui.control_room_pages:
            components["control_room_pages"] = self.manifest.ui.control_room_pages
        
        # Streamlit pages
        if self.manifest.ui.streamlit_pages:
            components["streamlit_pages"] = self.manifest.ui.streamlit_pages
        
        return components
    
    def is_initialized(self) -> bool:
        """Check if extension is initialized."""
        return self._initialized
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status information."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "initialized": self._initialized,
            "has_api": self._api_router is not None,
            "background_tasks": len(self._background_tasks),
            "ui_components": len(self._ui_components),
            "has_mcp_server": self._mcp_server is not None,
            "has_mcp_client": self._mcp_client is not None,
        }
    
    # MCP Integration Methods
    
    def get_mcp_server(self) -> Optional[ExtensionMCPServer]:
        """Get the MCP server for this extension."""
        return self._mcp_server
    
    def get_mcp_client(self) -> Optional[ExtensionMCPClient]:
        """Get the MCP client for this extension."""
        return self._mcp_client
    
    def create_mcp_server(self) -> Optional[ExtensionMCPServer]:
        """
        Create an MCP server for this extension.
        
        Extensions that want to expose MCP tools should override this method
        to register their tools.
        
        Returns:
            ExtensionMCPServer instance or None if MCP not available
        """
        if not MCP_AVAILABLE:
            self.logger.warning("MCP not available, cannot create MCP server")
            return None
        
        if self._mcp_server is None:
            self._mcp_server = ExtensionMCPServer(self.manifest.name, self.manifest)
            self.logger.info(f"Created MCP server for extension {self.manifest.name}")
        
        return self._mcp_server
    
    def create_mcp_client(self, service_registry) -> Optional[ExtensionMCPClient]:
        """
        Create an MCP client for this extension.
        
        Extensions that want to consume MCP tools should call this method
        to get access to external MCP services.
        
        Args:
            service_registry: MCP service registry
            
        Returns:
            ExtensionMCPClient instance or None if MCP not available
        """
        if not MCP_AVAILABLE:
            self.logger.warning("MCP not available, cannot create MCP client")
            return None
        
        if self._mcp_client is None:
            self._mcp_client = ExtensionMCPClient(self.manifest.name, service_registry)
            self.logger.info(f"Created MCP client for extension {self.manifest.name}")
        
        return self._mcp_client
    
    async def register_mcp_tool(
        self, 
        name: str, 
        handler: callable,
        schema: Dict[str, Any],
        description: Optional[str] = None
    ) -> bool:
        """
        Register an MCP tool for this extension.
        
        Args:
            name: Tool name
            handler: Function to handle tool calls
            schema: JSON schema for tool parameters
            description: Tool description
            
        Returns:
            True if tool was registered successfully
        """
        if not self._mcp_server:
            self.create_mcp_server()
        
        if self._mcp_server:
            self._mcp_server.register_tool(name, handler, schema, description)
            self.logger.info(f"Registered MCP tool: {name}")
            return True
        
        return False
    
    async def discover_mcp_tools(self, service_pattern: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover available MCP tools from other services.
        
        Args:
            service_pattern: Optional pattern to filter services
            
        Returns:
            Dictionary mapping service names to their available tools
        """
        if not self._mcp_client:
            self.logger.warning("MCP client not available for tool discovery")
            return {}
        
        return await self._mcp_client.discover_tools(service_pattern)
    
    async def call_mcp_tool(
        self, 
        service_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool from another service.
        
        Args:
            service_name: Name of the MCP service
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        
        return await self._mcp_client.call_tool(service_name, tool_name, arguments)


__all__ = ["BaseExtension", "BackgroundTask"]