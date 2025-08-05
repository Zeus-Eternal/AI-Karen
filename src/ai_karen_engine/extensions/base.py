"""
Base extension class that all extensions inherit from.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionContext
from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
from ai_karen_engine.extensions.data_manager import ExtensionDataManager
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes

# MCP integration (optional)
try:
    from ai_karen_engine.extensions.mcp_integration import ExtensionMCPServer, ExtensionMCPClient
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


class BaseExtension(ABC, HookMixin):
    """
    Base class for all Kari extensions.
    
    Extensions inherit from this class and implement the required methods
    to provide their functionality. The base class provides common services
    like plugin orchestration, data management, logging, and hook capabilities.
    """
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        """
        Initialize the extension.
        
        Args:
            manifest: Extension manifest with metadata and configuration
            context: Runtime context with access to core services
        """
        # Initialize HookMixin first
        super().__init__()
        
        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        self.name = manifest.name  # Required for HookMixin
        
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
        
        # Hook-related state
        self._registered_hooks: List[str] = []
        self._hook_handlers: Dict[str, callable] = {}
    
    async def initialize(self) -> None:
        """
        Initialize extension resources.
        
        This method is called when the extension is loaded. Extensions should
        override this method to set up their resources, register API routes,
        create database tables, etc.
        """
        self.logger.info(f"Initializing extension {self.manifest.name} v{self.manifest.version}")
        
        # Set up extension hooks first
        await self.setup_extension_hooks()
        
        # Call extension-specific initialization
        await self._initialize()
        
        # Set up API router if extension provides API
        if hasattr(self.manifest, 'capabilities') and self.manifest.capabilities.provides_api:
            self._api_router = self.create_api_router()
        
        # Set up background tasks if extension provides them
        if hasattr(self.manifest, 'capabilities') and self.manifest.capabilities.provides_background_tasks:
            self._background_tasks = self.create_background_tasks()
        
        # Set up UI components if extension provides UI
        if hasattr(self.manifest, 'capabilities') and self.manifest.capabilities.provides_ui:
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
        
        # Clean up extension hooks
        await self.cleanup_extension_hooks()
        
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
    
    # Hook Handler Methods
    
    async def register_extension_hook(
        self,
        hook_type: str,
        handler: callable,
        priority: int = 50,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Register a hook handler for this extension.
        
        Args:
            hook_type: Type of hook to register
            handler: Hook handler function
            priority: Hook priority (lower = higher priority)
            conditions: Conditions for hook execution
            
        Returns:
            Hook ID if successful, None otherwise
        """
        hook_id = await self.register_hook(
            hook_type=hook_type,
            handler=handler,
            priority=priority,
            conditions=conditions,
            source_name=f"{self.manifest.name}_extension"
        )
        
        if hook_id:
            self._registered_hooks.append(hook_id)
            self._hook_handlers[hook_type] = handler
            self.logger.info(f"Registered extension hook {hook_type} with ID {hook_id}")
        
        return hook_id
    
    async def unregister_extension_hook(self, hook_id: str) -> bool:
        """
        Unregister a hook handler for this extension.
        
        Args:
            hook_id: ID of hook to unregister
            
        Returns:
            True if successful, False otherwise
        """
        success = await self.unregister_hook(hook_id)
        
        if success and hook_id in self._registered_hooks:
            self._registered_hooks.remove(hook_id)
            self.logger.info(f"Unregistered extension hook {hook_id}")
        
        return success
    
    async def handle_hook(
        self,
        hook_type: str,
        context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Handle a hook call for this extension.
        
        This method is called by the hook system when a hook is triggered.
        Extensions can override this method to provide custom hook handling.
        
        Args:
            hook_type: Type of hook being triggered
            context: Hook context data
            user_context: User context information
            
        Returns:
            Hook result
        """
        if hook_type in self._hook_handlers:
            handler = self._hook_handlers[hook_type]
            
            try:
                # Call the handler with appropriate parameters
                if hasattr(handler, '__code__') and handler.__code__.co_argcount > 2:
                    # Handler expects (self, context, user_context)
                    return await handler(context, user_context)
                else:
                    # Handler expects (self, context)
                    return await handler(context)
            except Exception as e:
                self.logger.error(f"Hook handler {hook_type} failed: {e}")
                raise
        
        # Default hook handling for standard extension lifecycle hooks
        return await self._handle_default_hook(hook_type, context, user_context)
    
    async def _handle_default_hook(
        self,
        hook_type: str,
        context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle default extension lifecycle hooks.
        
        Args:
            hook_type: Type of hook being triggered
            context: Hook context data
            user_context: User context information
            
        Returns:
            Default hook result
        """
        result = {
            "extension_name": self.manifest.name,
            "extension_version": self.manifest.version,
            "hook_type": hook_type,
            "handled_by": "default_handler"
        }
        
        if hook_type == HookTypes.EXTENSION_LOADED:
            result.update({
                "status": "loaded",
                "capabilities": self.manifest.capabilities.dict() if hasattr(self.manifest, 'capabilities') else {},
                "has_mcp": self._mcp_server is not None
            })
        
        elif hook_type == HookTypes.EXTENSION_ACTIVATED:
            result.update({
                "status": "activated",
                "initialized": self._initialized,
                "api_available": self._api_router is not None,
                "background_tasks": len(self._background_tasks)
            })
        
        elif hook_type == HookTypes.EXTENSION_DEACTIVATED:
            result.update({
                "status": "deactivated",
                "cleanup_performed": True
            })
        
        elif hook_type == HookTypes.EXTENSION_UNLOADED:
            result.update({
                "status": "unloaded",
                "hooks_unregistered": len(self._registered_hooks)
            })
        
        return result
    
    async def setup_extension_hooks(self) -> None:
        """
        Set up standard extension hooks.
        
        Extensions can override this method to register their own hooks
        during initialization. This method is called automatically during
        extension initialization.
        """
        # Register standard lifecycle hooks
        await self.register_extension_hook(
            HookTypes.EXTENSION_LOADED,
            self._on_extension_loaded,
            priority=50
        )
        
        await self.register_extension_hook(
            HookTypes.EXTENSION_ACTIVATED,
            self._on_extension_activated,
            priority=50
        )
        
        await self.register_extension_hook(
            HookTypes.EXTENSION_DEACTIVATED,
            self._on_extension_deactivated,
            priority=50
        )
        
        await self.register_extension_hook(
            HookTypes.EXTENSION_UNLOADED,
            self._on_extension_unloaded,
            priority=50
        )
    
    async def cleanup_extension_hooks(self) -> None:
        """
        Clean up all registered hooks for this extension.
        
        This method is called automatically during extension shutdown.
        """
        for hook_id in self._registered_hooks.copy():
            await self.unregister_extension_hook(hook_id)
        
        self._hook_handlers.clear()
        self.logger.info(f"Cleaned up all hooks for extension {self.manifest.name}")
    
    # Default lifecycle hook handlers
    
    async def _on_extension_loaded(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for extension loaded hook."""
        return {
            "extension_name": self.manifest.name,
            "loaded_successfully": True,
            "timestamp": context.get("timestamp")
        }
    
    async def _on_extension_activated(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for extension activated hook."""
        return {
            "extension_name": self.manifest.name,
            "activated_successfully": True,
            "initialization_complete": self._initialized
        }
    
    async def _on_extension_deactivated(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for extension deactivated hook."""
        return {
            "extension_name": self.manifest.name,
            "deactivated_successfully": True,
            "cleanup_reason": context.get("deactivation_reason", "unknown")
        }
    
    async def _on_extension_unloaded(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for extension unloaded hook."""
        return {
            "extension_name": self.manifest.name,
            "unloaded_successfully": True,
            "hooks_cleaned": len(self._registered_hooks) == 0
        }
    
    def get_extension_hook_summary(self) -> Dict[str, Any]:
        """
        Get summary of hook-related information for this extension.
        
        Returns:
            Hook summary dictionary
        """
        return {
            "extension_name": self.manifest.name,
            "hooks_enabled": self.are_hooks_enabled(),
            "registered_hooks": len(self._registered_hooks),
            "hook_types": list(self._hook_handlers.keys()),
            "hook_stats": self.get_hook_stats()
        }
    
    async def register_ai_powered_hook(
        self,
        hook_type: str,
        handler: callable,
        ai_context_provider: Optional[callable] = None,
        priority: int = 50,
        conditions: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Register an AI-powered hook with enhanced context capabilities.
        
        Args:
            hook_type: Type of hook to register
            handler: Hook handler function
            ai_context_provider: Function to provide AI-enhanced context
            priority: Hook priority
            conditions: Hook execution conditions
            
        Returns:
            Hook ID if successful, None otherwise
        """
        # Create enhanced handler that includes AI context
        async def enhanced_handler(context: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Any:
            # Get AI-enhanced context if provider is available
            if ai_context_provider:
                try:
                    if asyncio.iscoroutinefunction(ai_context_provider):
                        ai_context = await ai_context_provider(context, user_context)
                    else:
                        ai_context = ai_context_provider(context, user_context)
                    
                    # Merge AI context with original context
                    enhanced_context = {
                        **context,
                        "ai_context": ai_context,
                        "ai_enhanced": True
                    }
                except Exception as e:
                    self.logger.warning(f"AI context provider 


__all__ = ["BaseExtension", "BackgroundTask"]