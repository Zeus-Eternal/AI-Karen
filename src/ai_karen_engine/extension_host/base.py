"""
Base classes and interfaces for the KARI extension system.

This module defines the core abstractions that all extensions must implement,
as well as the data structures used throughout the extension system.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from pydantic import BaseModel, Field, validator


class HookPoint(str, Enum):
    """Standard hook points for KARI extensions."""
    
    PRE_INTENT_DETECTION = "pre_intent_detection"
    PRE_MEMORY_RETRIEVAL = "pre_memory_retrieval"
    POST_MEMORY_RETRIEVAL = "post_memory_retrieval"
    PRE_LLM_PROMPT = "pre_llm_prompt"
    POST_LLM_RESULT = "post_llm_result"
    POST_RESPONSE = "post_response"


class Permission(str, Enum):
    """Standard permissions for extensions."""
    
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    TOOL_ACCESS = "tool_access"
    USER_DATA_READ = "user_data_read"
    USER_DATA_WRITE = "user_data_write"
    SYSTEM_CONFIG_READ = "system_config_read"
    SYSTEM_CONFIG_WRITE = "system_config_write"


class ExtensionRole(str, Enum):
    """Standard roles for extension RBAC."""
    
    SYSTEM = "system"
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    GUEST = "guest"


@dataclass
class ExtensionContext:
    """Context object passed to extensions during initialization and execution."""
    
    plugin_router: Any
    db_session: Any
    app_instance: Any
    user_context: Optional[Dict[str, Any]] = None
    extension_dir: Optional[Path] = None
    config: Optional[Dict[str, Any]] = None
    
    def get_service(self, service_name: str) -> Any:
        """Get a service from the application context."""
        if hasattr(self.app_instance, 'state') and hasattr(self.app_instance.state, 'services'):
            return self.app_instance.state.services.get(service_name)
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        if self.config and key in self.config:
            return self.config[key]
        return default


class ExtensionConfigSchema(BaseModel):
    """Schema for extension configuration."""
    
    type: str = "object"
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    additional_properties: bool = True


class ExtensionPermissions(BaseModel):
    """Permissions configuration for an extension."""
    
    memory_read: bool = False
    memory_write: bool = False
    tools: List[str] = field(default_factory=list)
    user_data_read: bool = False
    user_data_write: bool = False
    system_config_read: bool = False
    system_config_write: bool = False


class ExtensionRBAC(BaseModel):
    """Role-based access control configuration for an extension."""
    
    allowed_roles: List[ExtensionRole] = field(default_factory=list)
    default_enabled: bool = True


class ExtensionPromptFiles(BaseModel):
    """Prompt file configuration for an extension."""
    
    system: Optional[str] = None
    user: Optional[str] = None
    templates: Dict[str, str] = field(default_factory=dict)


class ExtensionManifest(BaseModel):
    """Manifest schema for KARI extensions."""
    
    id: str
    name: str
    version: str
    entrypoint: str
    description: str
    hook_points: List[HookPoint] = field(default_factory=list)
    prompt_files: ExtensionPromptFiles = field(default_factory=ExtensionPromptFiles)
    config_schema: Optional[ExtensionConfigSchema] = None
    permissions: ExtensionPermissions = field(default_factory=ExtensionPermissions)
    rbac: ExtensionRBAC = field(default_factory=ExtensionRBAC)
    dependencies: List[str] = field(default_factory=list)
    
    @validator('entrypoint')
    def validate_entrypoint(cls, v):
        """Validate that entrypoint is in format 'module:ClassName'."""
        if ':' not in v:
            raise ValueError("Entrypoint must be in format 'module:ClassName'")
        return v
    
    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'ExtensionManifest':
        """Load manifest from a JSON file."""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)


class ExtensionError(Exception):
    """Base exception for extension-related errors."""
    pass


class ExtensionLoadError(ExtensionError):
    """Exception raised when an extension fails to load."""
    pass


class ExtensionValidationError(ExtensionError):
    """Exception raised when an extension fails validation."""
    pass


class ExtensionExecutionError(ExtensionError):
    """Exception raised when an extension fails during execution."""
    pass


class ExtensionTimeoutError(ExtensionError):
    """Exception raised when an extension execution times out."""
    pass


class HookContext:
    """Context object passed to hook handlers."""
    
    def __init__(self, hook_point: HookPoint, data: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None):
        self.hook_point = hook_point
        self.data = data
        self.user_context = user_context or {}
        self.timestamp = time.time()
        self.results: Dict[str, Any] = {}
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the context."""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data in the context."""
        self.data[key] = value
    
    def get_user_context(self, key: str, default: Any = None) -> Any:
        """Get user context data."""
        return self.user_context.get(key, default)
    
    def set_result(self, extension_id: str, result: Any) -> None:
        """Set result from an extension."""
        self.results[extension_id] = result


class ExtensionBase(ABC):
    """Base class that all KARI extensions must inherit from."""
    
    def __init__(self, manifest: ExtensionManifest, context: ExtensionContext):
        """Initialize the extension with its manifest and context."""
        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        self._is_initialized = False
        self._is_shutdown = False
        self.enabled = manifest.rbac.default_enabled
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the extension.
        
        This method is called when the extension is loaded.
        It should set up any resources needed by the extension.
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shutdown the extension.
        
        This method is called when the extension is unloaded.
        It should clean up any resources created by the extension.
        """
        pass
    
    @abstractmethod
    async def execute_hook(self, hook_point: HookPoint, context: HookContext) -> Dict[str, Any]:
        """
        Execute a hook point.
        
        Args:
            hook_point: The hook point being executed
            context: The hook context containing data and user context
            
        Returns:
            A dictionary containing the result of the hook execution
        """
        pass
    
    async def _initialize(self) -> None:
        """Internal initialization method that sets up the extension."""
        try:
            await self.initialize()
            self._is_initialized = True
            self.logger.info(f"Extension {self.manifest.name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize extension {self.manifest.name}: {e}")
            raise ExtensionLoadError(f"Failed to initialize extension: {e}") from e
    
    async def _shutdown(self) -> None:
        """Internal shutdown method that cleans up the extension."""
        try:
            await self.shutdown()
            self._is_shutdown = True
            self.logger.info(f"Extension {self.manifest.name} shut down successfully")
        except Exception as e:
            self.logger.error(f"Failed to shutdown extension {self.manifest.name}: {e}")
            raise ExtensionError(f"Failed to shutdown extension: {e}") from e
    
    def is_initialized(self) -> bool:
        """Check if the extension has been initialized."""
        return self._is_initialized
    
    def is_shutdown(self) -> bool:
        """Check if the extension has been shut down."""
        return self._is_shutdown
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the extension."""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "initialized": self._is_initialized,
            "shutdown": self._is_shutdown,
            "hook_points": [hp.value for hp in self.manifest.hook_points],
        }
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if the extension has a specific permission."""
        if permission == Permission.MEMORY_READ:
            return self.manifest.permissions.memory_read
        elif permission == Permission.MEMORY_WRITE:
            return self.manifest.permissions.memory_write
        elif permission == Permission.TOOL_ACCESS:
            return len(self.manifest.permissions.tools) > 0
        elif permission == Permission.USER_DATA_READ:
            return self.manifest.permissions.user_data_read
        elif permission == Permission.USER_DATA_WRITE:
            return self.manifest.permissions.user_data_write
        elif permission == Permission.SYSTEM_CONFIG_READ:
            return self.manifest.permissions.system_config_read
        elif permission == Permission.SYSTEM_CONFIG_WRITE:
            return self.manifest.permissions.system_config_write
        return False
    
    def can_access_tool(self, tool_name: str) -> bool:
        """Check if the extension can access a specific tool."""
        return tool_name in self.manifest.permissions.tools
    
    def is_role_allowed(self, role: ExtensionRole) -> bool:
        """Check if the extension allows a specific role."""
        return role in self.manifest.rbac.allowed_roles
    
    def is_enabled_by_default(self) -> bool:
        """Check if the extension is enabled by default."""
        return self.manifest.rbac.default_enabled
    
    def supports_hook_point(self, hook_point: HookPoint) -> bool:
        """Check if the extension supports a specific hook point."""
        return hook_point in self.manifest.hook_points


# Type aliases for hooks
HookHandler = Callable[..., Awaitable[Any]]
MaybeAsyncFn = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


class BackgroundTask:
    """Represents a background task that can be scheduled."""

    def __init__(self, name: str, schedule: str, function: Union[str, MaybeAsyncFn]):
        self.name = name
        self.schedule = schedule
        self.function = function  # string reference or callable


# Optional FastAPI router
try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except Exception:  # pragma: no cover
    FASTAPI_AVAILABLE = False

    class APIRouter:  # minimal stub
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


# Optional MCP integration
try:
    from ai_karen_engine.extensions.mcp_integration import (
        ExtensionMCPServer,
        ExtensionMCPClient,
    )
    MCP_AVAILABLE = True
except Exception:  # pragma: no cover
    MCP_AVAILABLE = False
    ExtensionMCPServer = None  # type: ignore[assignment]
    ExtensionMCPClient = None  # type: ignore[assignment]


# Optional hook mixin
try:
    from ai_karen_engine.hooks.hook_mixin import HookMixin
    HOOK_MIXIN_AVAILABLE = True
except Exception:  # pragma: no cover
    HOOK_MIXIN_AVAILABLE = False
    
    class HookMixin:  # minimal stub
        def __init__(self) -> None:
            pass
        
        def are_hooks_enabled(self) -> bool:
            return False
        
        def get_hook_stats(self) -> Dict[str, Any]:
            return {}
        
        async def register_hook(
            self,
            hook_type: str,
            handler: HookHandler,
            priority: int = 50,
            conditions: Optional[Dict[str, Any]] = None,
            source_name: Optional[str] = None,
        ) -> Optional[str]:
            return None
        
        async def unregister_hook(self, hook_id: str) -> bool:
            return False


# Optional hook types
try:
    from ai_karen_engine.hooks.hook_types import HookTypes
    HOOK_TYPES_AVAILABLE = True
except Exception:  # pragma: no cover
    HOOK_TYPES_AVAILABLE = False
    
    class HookTypes:
        EXTENSION_LOADED = "extension_loaded"
        EXTENSION_ACTIVATED = "extension_activated"
        EXTENSION_DEACTIVATED = "extension_deactivated"
        EXTENSION_UNLOADED = "extension_unloaded"


# Optional plugin orchestrator
try:
    from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
    PLUGIN_ORCHESTRATOR_AVAILABLE = True
except Exception:  # pragma: no cover
    PLUGIN_ORCHESTRATOR_AVAILABLE = False
    
    class PluginOrchestrator:
        def __init__(self, plugin_router: Any) -> None:
            pass


# Optional data manager
try:
    from ai_karen_engine.extensions.data_manager import ExtensionDataManager
    DATA_MANAGER_AVAILABLE = True
except Exception:  # pragma: no cover
    DATA_MANAGER_AVAILABLE = False
    
    class ExtensionDataManager:
        def __init__(self, db_session: Any, extension_name: str) -> None:
            pass


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
        super().__init__()  # HookMixin init

        self.manifest = manifest
        self.context = context
        self.logger = logging.getLogger(f"extension.{manifest.name}")
        self.name = manifest.name  # required by HookMixin

        # Core services
        self.plugin_orchestrator = PluginOrchestrator(context.plugin_router)
        self.data_manager = ExtensionDataManager(context.db_session, manifest.name)

        # Extension state
        self._initialized: bool = False
        self._api_router: Optional[APIRouter] = None
        self._background_tasks: List[BackgroundTask] = []
        self._ui_components: Dict[str, Any] = {}

        # MCP integration (optional)
        self._mcp_server: Optional[ExtensionMCPServer] = None  # type: ignore[assignment]
        self._mcp_client: Optional[ExtensionMCPClient] = None  # type: ignore[assignment]

        # Hook-related state
        self._registered_hooks: List[str] = []
        self._hook_handlers: Dict[str, HookHandler] = {}

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    async def initialize(self) -> None:
        """
        Initialize extension resources.
        Called when the extension is loaded.
        """
        self.logger.info(
            "Initializing extension %s v%s", self.manifest.name, self.manifest.version
        )

        # Register base hooks first so extension code can rely on them
        await self.setup_extension_hooks()

        # Extension-specific initialization
        await self._initialize()

        # Optional capabilities from manifest
        caps = getattr(self.manifest, "capabilities", None)

        if caps and getattr(caps, "provides_api", False):
            self._api_router = self.create_api_router()

        if caps and getattr(caps, "provides_background_tasks", False):
            self._background_tasks = self.create_background_tasks()

        if caps and getattr(caps, "provides_ui", False):
            self._ui_components = self.create_ui_components()

        self._initialized = True
        self.logger.info("Extension %s initialized successfully", self.manifest.name)

    async def shutdown(self) -> None:
        """
        Cleanup extension resources.
        Called when the extension is unloaded.
        """
        self.logger.info("Shutting down extension %s", self.manifest.name)

        # Extension-specific cleanup
        await self._shutdown()

        # Unregister hooks registered by this instance
        await self.cleanup_extension_hooks()

        self._initialized = False
        self.logger.info("Extension %s shut down successfully", self.manifest.name)

    @abstractmethod
    async def _initialize(self) -> None:
        """Extension-specific initialization logic."""
        raise NotImplementedError

    async def _shutdown(self) -> None:
        """Extension-specific cleanup logic. Override if needed."""
        return None

    # -------------------------------------------------------------------------
    # Capabilities: API / UI / Tasks
    # -------------------------------------------------------------------------
    def get_api_router(self) -> Optional[APIRouter]:
        """Return FastAPI router for this extension (if any)."""
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
        Override to define endpoints.
        """
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI not available, cannot create API router")
            return None
        return APIRouter(prefix=f"/api/extensions/{self.manifest.name}")

    def create_background_tasks(self) -> List[BackgroundTask]:
        """
        Create background tasks for this extension.
        Override to define scheduled tasks.
        """
        tasks: List[BackgroundTask] = []
        bg_cfg = getattr(self.manifest, "background_tasks", []) or []
        for task_config in bg_cfg:
            try:
                # Store the function path string; actual resolution can happen in scheduler
                func_ref = getattr(task_config, "function", "")
                tasks.append(
                    BackgroundTask(
                        name=getattr(task_config, "name", "task"),
                        schedule=getattr(task_config, "schedule", "* * * * *"),
                        function=func_ref or "",  # resolve later
                    )
                )
            except Exception as e:
                self.logger.error(
                    "Failed to create background task %s: %s",
                    getattr(task_config, "name", "<unnamed>"),
                    e,
                )
        return tasks

    def create_ui_components(self) -> Dict[str, Any]:
        """
        Create UI components for this extension.
        Override to define Control Room integrations.
        """
        components: Dict[str, Any] = {}
        ui = getattr(self.manifest, "ui", None)
        if ui and getattr(ui, "control_room_pages", None):
            components["control_room_pages"] = ui.control_room_pages
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

    # -------------------------------------------------------------------------
    # MCP Integration (optional)
    # -------------------------------------------------------------------------
    def get_mcp_server(self) -> Optional[ExtensionMCPServer]:  # type: ignore[valid-type]
        return self._mcp_server

    def get_mcp_client(self) -> Optional[ExtensionMCPClient]:  # type: ignore[valid-type]
        return self._mcp_client

    def create_mcp_server(self) -> Optional[ExtensionMCPServer]:  # type: ignore[valid-type]
        """Create an MCP server for this extension (if MCP is available)."""
        if not MCP_AVAILABLE:
            self.logger.warning("MCP not available, cannot create MCP server")
            return None
        if self._mcp_server is None:
            self._mcp_server = ExtensionMCPServer(self.manifest.name, self.manifest)  # type: ignore[call-arg]
            self.logger.info("Created MCP server for extension %s", self.manifest.name)
        return self._mcp_server

    def create_mcp_client(self, service_registry: Any) -> Optional[ExtensionMCPClient]:  # type: ignore[valid-type]
        """Create an MCP client for this extension (if MCP is available)."""
        if not MCP_AVAILABLE:
            self.logger.warning("MCP not available, cannot create MCP client")
            return None
        if self._mcp_client is None:
            self._mcp_client = ExtensionMCPClient(self.manifest.name, service_registry)  # type: ignore[call-arg]
            self.logger.info("Created MCP client for extension %s", self.manifest.name)
        return self._mcp_client

    async def register_mcp_tool(
        self,
        name: str,
        handler: HookHandler,
        schema: Dict[str, Any],
        description: Optional[str] = None,
    ) -> bool:
        """Register an MCP tool on the extension's MCP server."""
        if not self._mcp_server:
            self.create_mcp_server()
        if self._mcp_server:
            self._mcp_server.register_tool(name, handler, schema, description)  # type: ignore[attr-defined]
            self.logger.info("Registered MCP tool: %s", name)
            return True
        return False

    async def discover_mcp_tools(
        self, service_pattern: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Discover available MCP tools via the MCP client."""
        if not self._mcp_client:
            self.logger.warning("MCP client not available for tool discovery")
            return {}
        return await self._mcp_client.discover_tools(service_pattern)  # type: ignore[func-returns-value]

    async def call_mcp_tool(
        self, service_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Call an MCP tool from another service."""
        if not self._mcp_client:
            raise RuntimeError("MCP client not available")
        return await self._mcp_client.call_tool(service_name, tool_name, arguments)  # type: ignore[func-returns-value]

    # -------------------------------------------------------------------------
    # Hook registration & handling
    # -------------------------------------------------------------------------
    async def register_extension_hook(
        self,
        hook_type: str,
        handler: HookHandler,
        priority: int = 50,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Register a hook handler for this extension.
        Returns the hook_id on success.
        """
        hook_id = await self.register_hook(
            hook_type=hook_type,
            handler=handler,
            priority=priority,
            conditions=conditions,
            source_name=f"{self.manifest.name}_extension",
        )
        if hook_id:
            self._registered_hooks.append(hook_id)
            self._hook_handlers[hook_type] = handler
            self.logger.info("Registered extension hook %s with ID %s", hook_type, hook_id)
        return hook_id

    async def unregister_extension_hook(self, hook_id: str) -> bool:
        """Unregister a hook handler by id."""
        success = await self.unregister_hook(hook_id)
        if success and hook_id in self._registered_hooks:
            self._registered_hooks.remove(hook_id)
            self.logger.info("Unregistered extension hook %s", hook_id)
        return success

    async def handle_hook(
        self,
        hook_type: str,
        context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Handle a hook call for this extension.
        If a custom handler is registered for `hook_type`, it is invoked.
        Otherwise, fall back to default lifecycle handlers.
        """
        handler = self._hook_handlers.get(hook_type)
        if handler:
            try:
                # Call with or without user_context depending on signature
                if handler.__code__.co_argcount >= 2:  # type: ignore[attr-defined]
                    return await handler(context, user_context)  # type: ignore[misc]
                return await handler(context)  # type: ignore[misc]
            except Exception as e:
                self.logger.error("Hook handler %s failed: %s", hook_type, e, exc_info=True)
                raise

        # Default handling for standard lifecycle hooks
        return await self._handle_default_hook(hook_type, context, user_context)

    async def _handle_default_hook(
        self,
        hook_type: str,
        context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Default responses for lifecycle hooks."""
        result: Dict[str, Any] = {
            "extension_name": self.manifest.name,
            "extension_version": self.manifest.version,
            "hook_type": hook_type,
            "handled_by": "default_handler",
        }

        if hook_type == HookTypes.EXTENSION_LOADED:
            result.update(
                {
                    "status": "loaded",
                    "capabilities": getattr(self.manifest, "capabilities", None),
                    "has_mcp": self._mcp_server is not None,
                }
            )
        elif hook_type == HookTypes.EXTENSION_ACTIVATED:
            result.update(
                {
                    "status": "activated",
                    "initialized": self._initialized,
                    "api_available": self._api_router is not None,
                    "background_tasks": len(self._background_tasks),
                }
            )
        elif hook_type == HookTypes.EXTENSION_DEACTIVATED:
            result.update({"status": "deactivated", "cleanup_performed": True})
        elif hook_type == HookTypes.EXTENSION_UNLOADED:
            result.update(
                {"status": "unloaded", "hooks_unregistered": len(self._registered_hooks)}
            )
        return result

    async def setup_extension_hooks(self) -> None:
        """
        Set up standard extension hooks (lifecycle).
        Extensions may override to register more hooks before/after.
        """
        await self.register_extension_hook(
            HookTypes.EXTENSION_LOADED, self._on_extension_loaded, priority=50
        )
        await self.register_extension_hook(
            HookTypes.EXTENSION_ACTIVATED, self._on_extension_activated, priority=50
        )
        await self.register_extension_hook(
            HookTypes.EXTENSION_DEACTIVATED, self._on_extension_deactivated, priority=50
        )
        await self.register_extension_hook(
            HookTypes.EXTENSION_UNLOADED, self._on_extension_unloaded, priority=50
        )

    async def cleanup_extension_hooks(self) -> None:
        """Unregister all hooks registered by this extension."""
        for hook_id in self._registered_hooks.copy():
            await self.unregister_extension_hook(hook_id)
        self._hook_handlers.clear()
        self.logger.info("Cleaned up all hooks for extension %s", self.manifest.name)

    # Default lifecycle hook handlers
    async def _on_extension_loaded(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "extension_name": self.manifest.name,
            "loaded_successfully": True,
            "timestamp": context.get("timestamp"),
        }

    async def _on_extension_activated(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "extension_name": self.manifest.name,
            "activated_successfully": True,
            "initialization_complete": self._initialized,
        }

    async def _on_extension_deactivated(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "extension_name": self.manifest.name,
            "deactivated_successfully": True,
            "cleanup_reason": context.get("deactivation_reason", "unknown"),
        }

    async def _on_extension_unloaded(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "extension_name": self.manifest.name,
            "unloaded_successfully": True,
            "hooks_cleaned": len(self._registered_hooks) == 0,
        }

    def get_extension_hook_summary(self) -> Dict[str, Any]:
        """Return a summary of hook-related information for this extension."""
        return {
            "extension_name": self.manifest.name,
            "hooks_enabled": self.are_hooks_enabled(),
            "registered_hooks": len(self._registered_hooks),
            "hook_types": list(self._hook_handlers.keys()),
            "hook_stats": self.get_hook_stats(),
        }

    # -------------------------------------------------------------------------
    # AI-powered hooks (optional convenience wrapper)
    # -------------------------------------------------------------------------
    async def register_ai_powered_hook(
        self,
        hook_type: str,
        handler: HookHandler,
        ai_context_provider: Optional[MaybeAsyncFn] = None,
        priority: int = 50,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Register an AI-powered hook with optional AI context provider.
        The provider runs before the handler; its result is merged into context.
        """

        async def enhanced_handler(
            context: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None
        ) -> Any:
            enhanced_context = dict(context)
            if ai_context_provider:
                try:
                    if asyncio.iscoroutinefunction(ai_context_provider):
                        ai_ctx = await ai_context_provider(context, user_context)
                    else:
                        ai_ctx = ai_context_provider(context, user_context)  # type: ignore[misc]
                    enhanced_context.update({"ai_context": ai_ctx, "ai_enhanced": True})
                except Exception as e:
                    self.logger.warning(
                        "AI context provider failed for hook %s: %s", hook_type, e
                    )
            # Call the original handler with the enriched context
            return await handler(enhanced_context, user_context)

        return await self.register_extension_hook(
            hook_type=hook_type,
            handler=enhanced_handler,
            priority=priority,
            conditions=conditions,
        )


__all__ = [
    "ExtensionBase", 
    "BaseExtension", 
    "BackgroundTask",
    "HookPoint",
    "Permission",
    "ExtensionRole",
    "ExtensionContext",
    "ExtensionConfigSchema",
    "ExtensionPermissions",
    "ExtensionRBAC",
    "ExtensionPromptFiles",
    "ExtensionManifest",
    "ExtensionError",
    "ExtensionLoadError",
    "ExtensionValidationError",
    "ExtensionExecutionError",
    "ExtensionTimeoutError",
    "HookContext",
    "HookHandler",
    "MaybeAsyncFn"
]
