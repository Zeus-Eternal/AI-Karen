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
from ai_karen_engine.extensions.models import ExtensionManifest


class ExtensionMCPServer:
    """
    MCP server for an extension, exposing its tools and capabilities.
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
        
        # Server state
        self.running = False
        self.endpoint: Optional[str] = None
    
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
    MCP client for extensions to consume external MCP services.
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