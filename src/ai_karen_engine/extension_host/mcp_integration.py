"""
MCP (Model Context Protocol) integration for extensions.

This module provides MCP server and client capabilities for extensions,
enabling them to expose tools and consume external MCP services.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable

from ai_karen_engine.mcp.registry import ServiceRegistry
from ai_karen_engine.extension_host.models2 import ExtensionManifest
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.hooks.models import HookContext


class ExtensionMCPServer:
    """
    MCP server for an extension, exposing its tools and capabilities with AI-powered hook support.
    """
    
    def __init__(self, extension_name: str, manifest: ExtensionManifest):
        """
        Initialize MCP server for an extension.
        
        Args:
            extension_name: Name of the extension
            manifest: Extension manifest
        """
        self.extension_name = extension_name
        self.manifest = manifest
        self.logger = logging.getLogger(f"extension.mcp.{extension_name}")
        
        # Tool registry
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Hook-enabled tools registry
        self.hook_tools: Dict[str, Dict[str, Any]] = {}
        
        # Server state
        self.running = False
        self.endpoint: Optional[str] = None
        
        # AI-powered capabilities
        self.ai_context_providers: Dict[str, Callable] = {}
        self.hook_manager: Optional[Any] = None
    
    def register_tool(
        self, 
        name: str, 
        handler: Callable,
        schema: Dict[str, Any],
        description: Optional[str] = None
    ) -> None:
        """
        Register a tool that can be called via MCP.
        
        Args:
            name: Tool name
            handler: Function to handle tool calls
            schema: JSON schema for tool parameters
            description: Tool description
        """
        self.tools[name] = handler
        self.tool_schemas[name] = {
            "name": name,
            "description": description or f"Tool from {self.extension_name} extension",
            "inputSchema": schema
        }
        
        self.logger.info(f"Registered MCP tool: {name}")
    
    def register_hook_enabled_tool(
        self,
        name: str,
        handler: Callable,
        schema: Dict[str, Any],
        hook_types: List[str],
        description: Optional[str] = None,
        ai_context_provider: Optional[Callable] = None
    ) -> None:
        """
        Register a hook-enabled MCP tool with AI-powered capabilities.
        
        Args:
            name: Tool name
            handler: Function to handle tool calls
            schema: JSON schema for tool parameters
            hook_types: List of hook types this tool responds to
            description: Tool description
            ai_context_provider: Function to provide AI context
        """
        # Register as regular tool
        self.register_tool(name, handler, schema, description)
        
        # Register hook capabilities
        self.hook_tools[name] = {
            "handler": handler,
            "hook_types": hook_types,
            "ai_context_provider": ai_context_provider,
            "schema": schema
        }
        
        # Register AI context provider if provided
        if ai_context_provider:
            self.ai_context_providers[name] = ai_context_provider
        
        self.logger.info(f"Registered hook-enabled MCP tool: {name} with hooks: {hook_types}")
    
    def set_hook_manager(self, hook_manager: Any) -> None:
        """Set the hook manager for AI-powered capabilities."""
        self.hook_manager = hook_manager
        self.logger.info(f"Hook manager set for MCP server {self.extension_name}")
    
    async def trigger_tool_hooks(
        self,
        tool_name: str,
        hook_type: str,
        context_data: Dict[str, Any]
    ) -> List[Any]:
        """
        Trigger hooks for a specific tool.
        
        Args:
            tool_name: Name of the tool
            hook_type: Type of hook to trigger
            context_data: Context data for the hook
            
        Returns:
            List of hook results
        """
        if tool_name not in self.hook_tools:
            return []
        
        tool_info = self.hook_tools[tool_name]
        if hook_type not in tool_info["hook_types"]:
            return []
        
        if not self.hook_manager:
            self.logger.warning(f"No hook manager available for tool {tool_name}")
            return []
        
        try:
            # Enhance context with AI-provided data if available
            if tool_name in self.ai_context_providers:
                ai_context = await self._get_ai_context(tool_name, context_data)
                context_data.update(ai_context)
            
            # Create hook context
            hook_context = HookContext(
                hook_type=hook_type,
                data={
                    **context_data,
                    "tool_name": tool_name,
                    "extension_name": self.extension_name,
                    "mcp_server": True
                },
                metadata={
                    "source": "mcp_tool",
                    "tool_schema": tool_info["schema"]
                }
            )
            
            # Trigger hooks
            summary = await self.hook_manager.trigger_hooks(hook_context)
            return [result.result for result in summary.results if result.success]
            
        except Exception as e:
            self.logger.error(f"Failed to trigger hooks for tool {tool_name}: {e}")
            return []
    
    async def _get_ai_context(self, tool_name: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI-enhanced context for a tool.
        
        Args:
            tool_name: Name of the tool
            base_context: Base context data
            
        Returns:
            AI-enhanced context
        """
        try:
            provider = self.ai_context_providers[tool_name]
            if asyncio.iscoroutinefunction(provider):
                return await provider(base_context)
            else:
                return provider(base_context)
        except Exception as e:
            self.logger.error(f"Failed to get AI context for tool {tool_name}: {e}")
            return {}
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a registered tool.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If tool not found
        """
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in extension {self.extension_name}")
        
        try:
            handler = self.tools[name]
            
            # Call handler (may be sync or async)
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)
            
            self.logger.info(f"MCP tool {name} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"MCP tool {name} execution failed: {e}")
            raise
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.
        
        Returns:
            List of tool schemas
        """
        return list(self.tool_schemas.values())
    
    async def start_server(self, port: Optional[int] = None) -> str:
        """
        Start the MCP server.
        
        Args:
            port: Port to listen on (auto-assigned if None)
            
        Returns:
            Server endpoint URL
        """
        # This is a simplified implementation
        # In production, you'd start an actual MCP server (JSON-RPC or gRPC)
        
        if port is None:
            port = 8000 + hash(self.extension_name) % 1000  # Simple port assignment
        
        self.endpoint = f"http://localhost:{port}/mcp"
        self.running = True
        
        self.logger.info(f"MCP server started for {self.extension_name} at {self.endpoint}")
        return self.endpoint
    
    async def stop_server(self) -> None:
        """Stop the MCP server."""
        self.running = False
        self.endpoint = None
        self.logger.info(f"MCP server stopped for {self.extension_name}")


class ExtensionMCPClient:
    """
    MCP client for extensions to consume external MCP services with AI-powered hook support.
    """
    
    def __init__(self, extension_name: str, service_registry: ServiceRegistry):
        """
        Initialize MCP client for an extension.
        
        Args:
            extension_name: Name of the extension
            service_registry: MCP service registry
        """
        self.extension_name = extension_name
        self.service_registry = service_registry
        self.logger = logging.getLogger(f"extension.mcp_client.{extension_name}")
        
        # Connected services
        self.connected_services: Dict[str, Any] = {}
        
        # AI-powered capabilities
        self.hook_manager: Optional[Any] = None
        self.ai_enhanced_tools: Dict[str, Dict[str, Any]] = {}
    
    def set_hook_manager(self, hook_manager: Any) -> None:
        """Set the hook manager for AI-powered capabilities."""
        self.hook_manager = hook_manager
        self.logger.info(f"Hook manager set for MCP client {self.extension_name}")
    
    def register_ai_enhanced_tool(
        self,
        service_name: str,
        tool_name: str,
        enhancement_config: Dict[str, Any]
    ) -> None:
        """
        Register an AI-enhanced tool configuration.
        
        Args:
            service_name: Name of the MCP service
            tool_name: Name of the tool
            enhancement_config: AI enhancement configuration
        """
        tool_key = f"{service_name}.{tool_name}"
        self.ai_enhanced_tools[tool_key] = {
            "service_name": service_name,
            "tool_name": tool_name,
            "config": enhancement_config
        }
        
        self.logger.info(f"Registered AI-enhanced tool: {tool_key}")
    
    async def call_ai_enhanced_tool(
        self,
        service_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        ai_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Call an AI-enhanced MCP tool with hook integration.
        
        Args:
            service_name: Name of the MCP service
            tool_name: Name of the tool to call
            arguments: Tool arguments
            ai_context: Additional AI context
            
        Returns:
            Enhanced tool result
        """
        tool_key = f"{service_name}.{tool_name}"
        
        # Trigger pre-call hooks if available
        if self.hook_manager:
            await self._trigger_tool_hooks(
                HookTypes.LLM_REQUEST,  # Using LLM_REQUEST as proxy for MCP tool calls
                {
                    "service_name": service_name,
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "ai_context": ai_context or {},
                    "phase": "pre_call"
                }
            )
        
        try:
            # Call the regular tool
            result = await self.call_tool(service_name, tool_name, arguments)
            
            # Apply AI enhancements if configured
            if tool_key in self.ai_enhanced_tools:
                result = await self._apply_ai_enhancements(tool_key, result, ai_context)
            
            # Trigger post-call hooks if available
            if self.hook_manager:
                await self._trigger_tool_hooks(
                    HookTypes.LLM_RESPONSE,  # Using LLM_RESPONSE as proxy for MCP tool responses
                    {
                        "service_name": service_name,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result,
                        "phase": "post_call"
                    }
                )
            
            return result
            
        except Exception as e:
            # Trigger error hooks if available
            if self.hook_manager:
                await self._trigger_tool_hooks(
                    HookTypes.LLM_ERROR,  # Using LLM_ERROR as proxy for MCP tool errors
                    {
                        "service_name": service_name,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "error": str(e),
                        "phase": "error"
                    }
                )
            raise
    
    async def _trigger_tool_hooks(self, hook_type: str, context_data: Dict[str, Any]) -> List[Any]:
        """
        Trigger hooks for MCP tool operations.
        
        Args:
            hook_type: Type of hook to trigger
            context_data: Context data for the hook
            
        Returns:
            List of hook results
        """
        if not self.hook_manager:
            return []
        
        try:
            hook_context = HookContext(
                hook_type=hook_type,
                data={
                    **context_data,
                    "extension_name": self.extension_name,
                    "mcp_client": True
                },
                metadata={
                    "source": "mcp_client",
                    "client_name": self.extension_name
                }
            )
            
            summary = await self.hook_manager.trigger_hooks(hook_context)
            return [result.result for result in summary.results if result.success]
            
        except Exception as e:
            self.logger.error(f"Failed to trigger MCP client hooks: {e}")
            return []
    
    async def _apply_ai_enhancements(
        self,
        tool_key: str,
        base_result: Any,
        ai_context: Optional[Dict[str, Any]]
    ) -> Any:
        """
        Apply AI enhancements to tool results.
        
        Args:
            tool_key: Tool key (service.tool)
            base_result: Base tool result
            ai_context: AI context data
            
        Returns:
            Enhanced result
        """
        try:
            enhancement_config = self.ai_enhanced_tools[tool_key]["config"]
            
            # Apply configured enhancements
            enhanced_result = {
                "original_result": base_result,
                "ai_enhancements": {},
                "metadata": {
                    "enhanced_by": self.extension_name,
                    "enhancement_config": enhancement_config
                }
            }
            
            # Add semantic analysis if configured
            if enhancement_config.get("semantic_analysis", False):
                enhanced_result["ai_enhancements"]["semantic_analysis"] = await self._analyze_semantics(
                    base_result, ai_context
                )
            
            # Add context enrichment if configured
            if enhancement_config.get("context_enrichment", False):
                enhanced_result["ai_enhancements"]["enriched_context"] = await self._enrich_context(
                    base_result, ai_context
                )
            
            # Add intelligent suggestions if configured
            if enhancement_config.get("intelligent_suggestions", False):
                enhanced_result["ai_enhancements"]["suggestions"] = await self._generate_suggestions(
                    base_result, ai_context
                )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Failed to apply AI enhancements for {tool_key}: {e}")
            return base_result
    
    async def _analyze_semantics(self, result: Any, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze semantic content of tool results."""
        # Placeholder for semantic analysis
        return {
            "sentiment": "neutral",
            "key_concepts": [],
            "confidence": 0.5
        }
    
    async def _enrich_context(self, result: Any, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Enrich context with additional AI-powered insights."""
        # Placeholder for context enrichment
        return {
            "related_concepts": [],
            "contextual_relevance": 0.5,
            "enrichment_source": "ai_analysis"
        }
    
    async def _generate_suggestions(self, result: Any, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate intelligent suggestions based on tool results."""
        # Placeholder for suggestion generation
        return [
            {
                "type": "next_action",
                "suggestion": "Consider analyzing the result further",
                "confidence": 0.7
            }
        ]
    
    async def discover_tools(self, service_pattern: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover available MCP tools from registered services.
        
        Args:
            service_pattern: Optional pattern to filter services
            
        Returns:
            Dictionary mapping service names to their available tools
        """
        discovered_tools = {}
        
        try:
            # Get all registered services
            services = self.service_registry.list()
            
            for service_name, service_info in services.items():
                if service_pattern and service_pattern not in service_name:
                    continue
                
                try:
                    # Connect to service and get tools
                    tools = await self._get_service_tools(service_name, service_info)
                    if tools:
                        discovered_tools[service_name] = tools
                        
                except Exception as e:
                    self.logger.warning(f"Failed to discover tools from {service_name}: {e}")
            
            self.logger.info(f"Discovered {len(discovered_tools)} MCP services with tools")
            return discovered_tools
            
        except Exception as e:
            self.logger.error(f"Tool discovery failed: {e}")
            return {}
    
    async def _get_service_tools(self, service_name: str, service_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get tools from a specific MCP service.
        
        Args:
            service_name: Service name
            service_info: Service information from registry
            
        Returns:
            List of available tools
        """
        # This is a simplified implementation
        # In production, you'd make actual MCP calls to list tools
        
        endpoint = service_info.get("endpoint")
        if not endpoint:
            return []
        
        # Mock tool discovery for now
        # In reality, you'd call the MCP service's list_tools method
        return [
            {
                "name": f"{service_name}_tool",
                "description": f"Tool from {service_name} service",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
    
    async def call_tool(
        self, 
        service_name: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool from an MCP service.
        
        Args:
            service_name: Name of the MCP service
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
            
        Raises:
            ValueError: If service or tool not found
        """
        try:
            # Look up service
            service_info = self.service_registry.lookup(service_name)
            if not service_info:
                raise ValueError(f"MCP service {service_name} not found")
            
            # This is a simplified implementation
            # In production, you'd make actual MCP calls
            
            self.logger.info(f"Calling MCP tool {tool_name} from {service_name}")
            
            # Mock tool call for now
            result = {
                "service": service_name,
                "tool": tool_name,
                "arguments": arguments,
                "result": "Mock MCP tool result"
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {e}")
            raise


class MCPIntegrationManager:
    """
    Manages MCP integration for the extension system.
    """
    
    def __init__(self, service_registry: ServiceRegistry):
        """
        Initialize MCP integration manager.
        
        Args:
            service_registry: MCP service registry
        """
        self.service_registry = service_registry
        self.logger = logging.getLogger("extension.mcp_manager")
        
        # Extension MCP servers and clients
        self.extension_servers: Dict[str, ExtensionMCPServer] = {}
        self.extension_clients: Dict[str, ExtensionMCPClient] = {}
    
    def create_extension_server(
        self, 
        extension_name: str, 
        manifest: ExtensionManifest
    ) -> ExtensionMCPServer:
        """
        Create an MCP server for an extension.
        
        Args:
            extension_name: Extension name
            manifest: Extension manifest
            
        Returns:
            ExtensionMCPServer instance
        """
        server = ExtensionMCPServer(extension_name, manifest)
        self.extension_servers[extension_name] = server
        
        self.logger.info(f"Created MCP server for extension {extension_name}")
        return server
    
    def create_extension_client(self, extension_name: str) -> ExtensionMCPClient:
        """
        Create an MCP client for an extension.
        
        Args:
            extension_name: Extension name
            
        Returns:
            ExtensionMCPClient instance
        """
        client = ExtensionMCPClient(extension_name, self.service_registry)
        self.extension_clients[extension_name] = client
        
        self.logger.info(f"Created MCP client for extension {extension_name}")
        return client
    
    async def register_extension_server(
        self, 
        extension_name: str, 
        endpoint: str
    ) -> None:
        """
        Register an extension's MCP server in the service registry.
        
        Args:
            extension_name: Extension name
            endpoint: Server endpoint
        """
        try:
            self.service_registry.register(
                name=f"extension_{extension_name}",
                endpoint=endpoint,
                kind="extension",
                roles=["user", "admin"]  # Default roles
            )
            
            self.logger.info(f"Registered MCP server for extension {extension_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to register MCP server for {extension_name}: {e}")
    
    async def discover_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover all available MCP tools across all services.
        
        Returns:
            Dictionary mapping service names to their tools
        """
        all_tools = {}
        
        # Discover tools from all extension clients
        for extension_name, client in self.extension_clients.items():
            try:
                tools = await client.discover_tools()
                if tools:
                    all_tools.update(tools)
            except Exception as e:
                self.logger.error(f"Tool discovery failed for {extension_name}: {e}")
        
        return all_tools
    
    def get_extension_server(self, extension_name: str) -> Optional[ExtensionMCPServer]:
        """Get MCP server for an extension."""
        return self.extension_servers.get(extension_name)
    
    def get_extension_client(self, extension_name: str) -> Optional[ExtensionMCPClient]:
        """Get MCP client for an extension."""
        return self.extension_clients.get(extension_name)


__all__ = [
    "ExtensionMCPServer",
    "ExtensionMCPClient", 
    "MCPIntegrationManager"
]