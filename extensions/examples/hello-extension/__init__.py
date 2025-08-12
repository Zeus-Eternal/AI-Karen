"""
Hello Extension - A simple example extension with MCP integration.

This extension demonstrates the basic structure and capabilities
of the Kari extension system, including MCP tool exposure and consumption.
"""

from ai_karen_engine.extensions.base import BaseExtension

try:
    from fastapi import APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object


class HelloExtension(BaseExtension):
    """
    A simple example extension that demonstrates basic functionality.
    """
    
    async def _initialize(self) -> None:
        """Initialize the Hello Extension with MCP capabilities."""
        self.logger.info("Hello Extension initializing...")
        
        # Extension-specific initialization logic goes here
        self.greeting_count = 0
        
        # Initialize MCP server and register tools
        await self._setup_mcp_tools()
        
        self.logger.info("Hello Extension initialized successfully")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for this extension."""
        # Create MCP server to expose our tools
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register a simple greeting tool
            await self.register_mcp_tool(
                name="generate_greeting",
                handler=self._generate_greeting_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name to greet"},
                        "style": {"type": "string", "enum": ["formal", "casual", "enthusiastic"], "default": "casual"}
                    },
                    "required": ["name"]
                },
                description="Generate a personalized greeting message"
            )
            
            # Register a counter tool
            await self.register_mcp_tool(
                name="get_greeting_stats",
                handler=self._get_greeting_stats_tool,
                schema={
                    "type": "object",
                    "properties": {}
                },
                description="Get statistics about greetings generated"
            )
            
            self.logger.info("MCP tools registered successfully")
    
    async def _generate_greeting_tool(self, name: str, style: str = "casual") -> dict:
        """MCP tool to generate personalized greetings."""
        self.greeting_count += 1
        
        greetings = {
            "formal": f"Good day, {name}. It is a pleasure to make your acquaintance.",
            "casual": f"Hey {name}! Nice to meet you!",
            "enthusiastic": f"WOW! Hi there {name}! This is AMAZING! 🎉"
        }
        
        greeting = greetings.get(style, greetings["casual"])
        
        return {
            "greeting": greeting,
            "style": style,
            "recipient": name,
            "count": self.greeting_count,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use real timestamp
        }
    
    async def _get_greeting_stats_tool(self) -> dict:
        """MCP tool to get greeting statistics."""
        return {
            "total_greetings": self.greeting_count,
            "extension_name": self.manifest.name,
            "extension_version": self.manifest.version,
            "status": "active"
        }
    
    async def _shutdown(self) -> None:
        """Cleanup the Hello Extension."""
        self.logger.info("Hello Extension shutting down...")
        
        # Extension-specific cleanup logic goes here
        
        self.logger.info("Hello Extension shut down successfully")
    
    def create_api_router(self):
        """Create API routes for the Hello Extension."""
        if not FASTAPI_AVAILABLE:
            return None
        
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.get("/hello")
        async def get_hello():
            """Simple hello endpoint."""
            self.greeting_count += 1
            
            # Demonstrate plugin orchestration
            try:
                # Use the hello_world plugin through orchestration
                result = await self.plugin_orchestrator.execute_plugin(
                    intent="hello_world",
                    params={"message": "Hello from extension!"},
                    user_context={"roles": ["user"]}
                )
                
                return {
                    "message": "Hello from Hello Extension!",
                    "greeting_count": self.greeting_count,
                    "plugin_result": result,
                    "extension_info": {
                        "name": self.manifest.name,
                        "version": self.manifest.version
                    }
                }
            except Exception as e:
                self.logger.error(f"Plugin orchestration failed: {e}")
                return {
                    "message": "Hello from Hello Extension!",
                    "greeting_count": self.greeting_count,
                    "plugin_error": str(e),
                    "extension_info": {
                        "name": self.manifest.name,
                        "version": self.manifest.version
                    }
                }
        
        @router.get("/status")
        async def get_status():
            """Get extension status."""
            return self.get_status()
        
        return router
    
    def create_ui_components(self):
        """Create UI components for the Hello Extension."""
        components = super().create_ui_components()
        
        # Add custom UI components
        components["custom_dashboard"] = {
            "title": "Hello Extension Dashboard",
            "description": "A simple dashboard showing extension status",
            "data": {
                "greeting_count": getattr(self, 'greeting_count', 0),
                "status": "active"
            }
        }
        
        return components
    
    def get_status(self):
        """Get detailed status information."""
        status = super().get_status()
        status.update({
            "greeting_count": getattr(self, 'greeting_count', 0),
            "custom_status": "Hello Extension is running!"
        })
        return status


# Export the extension class
__all__ = ["HelloExtension"]
