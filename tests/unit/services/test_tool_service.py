"""
Tests for the Tool Service implementation.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock

from src.ai_karen_engine.services.tool_service import (
    ToolService,
    ToolRegistry,
    BaseTool,
    ToolMetadata,
    ToolInput,
    ToolOutput,
    ToolCategory,
    ToolStatus,
    ToolParameter,
    get_tool_service,
    initialize_tool_service
)

from src.ai_karen_engine.services.tools.core_tools import (
    DateTool,
    TimeTool,
    WeatherTool
)

from src.ai_karen_engine.services.tools.registry import (
    register_core_tools,
    get_core_tool_names,
    initialize_core_tools
)


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def _create_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mock_tool",
            description="A mock tool for testing",
            category=ToolCategory.CUSTOM,
            parameters=[
                ToolParameter(
                    name="test_param",
                    type=str,
                    description="Test parameter",
                    required=True
                )
            ],
            return_type=str
        )
    
    async def _execute(self, parameters, context=None):
        return f"Mock result: {parameters.get('test_param', 'none')}"


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_registry_initialization(self):
        """Test registry initializes correctly."""
        registry = ToolRegistry()
        assert len(registry.tools) == 0
        assert len(registry.tools_by_category) == 0
        assert len(registry.tool_aliases) == 0
    
    def test_tool_registration(self):
        """Test tool registration."""
        registry = ToolRegistry()
        tool = MockTool()
        
        # Register tool
        success = registry.register_tool(tool, aliases=["mock", "test"])
        assert success is True
        
        # Check tool is registered
        assert "mock_tool" in registry.tools
        assert registry.get_tool("mock_tool") is tool
        assert registry.get_tool("mock") is tool
        assert registry.get_tool("test") is tool
        
        # Check category indexing
        assert ToolCategory.CUSTOM in registry.tools_by_category
        assert "mock_tool" in registry.tools_by_category[ToolCategory.CUSTOM]
    
    def test_tool_unregistration(self):
        """Test tool unregistration."""
        registry = ToolRegistry()
        tool = MockTool()
        
        # Register and then unregister
        registry.register_tool(tool, aliases=["mock"])
        success = registry.unregister_tool("mock_tool")
        assert success is True
        
        # Check tool is removed
        assert "mock_tool" not in registry.tools
        assert registry.get_tool("mock_tool") is None
        assert registry.get_tool("mock") is None
    
    def test_tool_listing(self):
        """Test tool listing functionality."""
        registry = ToolRegistry()
        tool1 = MockTool()
        tool2 = DateTool()
        
        registry.register_tool(tool1)
        registry.register_tool(tool2)
        
        # List all tools
        all_tools = registry.list_tools()
        assert "mock_tool" in all_tools
        assert "get_current_date" in all_tools
        
        # List by category
        custom_tools = registry.list_tools(category=ToolCategory.CUSTOM)
        assert "mock_tool" in custom_tools
        assert "get_current_date" not in custom_tools
        
        time_tools = registry.list_tools(category=ToolCategory.TIME)
        assert "get_current_date" in time_tools
        assert "mock_tool" not in time_tools
    
    def test_tool_search(self):
        """Test tool search functionality."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register_tool(tool)
        
        # Search by name
        results = registry.search_tools("mock")
        assert "mock_tool" in results
        
        # Search by description
        results = registry.search_tools("testing")
        assert "mock_tool" in results


class TestBaseTool:
    """Test base tool functionality."""
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution."""
        tool = MockTool()
        
        tool_input = ToolInput(
            tool_name="mock_tool",
            parameters={"test_param": "hello"}
        )
        
        result = await tool.execute(tool_input)
        
        assert result.success is True
        assert result.result == "Mock result: hello"
        assert result.error is None
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_tool_validation_error(self):
        """Test tool validation error handling."""
        tool = MockTool()
        
        # Missing required parameter
        tool_input = ToolInput(
            tool_name="mock_tool",
            parameters={}
        )
        
        result = await tool.execute(tool_input)
        
        assert result.success is False
        assert result.error is not None
        assert "Required parameter 'test_param' is missing" in result.error
    
    def test_tool_schema_generation(self):
        """Test tool schema generation."""
        tool = MockTool()
        schema = tool.get_schema()
        
        assert schema["type"] == "object"
        assert "test_param" in schema["properties"]
        assert "test_param" in schema["required"]
        assert schema["properties"]["test_param"]["type"] == "string"


class TestToolService:
    """Test tool service functionality."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        service = ToolService()
        assert service.registry is not None
        assert len(service.execution_cache) == 0
    
    @pytest.mark.asyncio
    async def test_tool_execution_via_service(self):
        """Test tool execution through service."""
        service = ToolService()
        tool = MockTool()
        service.register_tool(tool)
        
        tool_input = ToolInput(
            tool_name="mock_tool",
            parameters={"test_param": "service_test"}
        )
        
        result = await service.execute_tool(tool_input)
        
        assert result.success is True
        assert result.result == "Mock result: service_test"
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test handling of non-existent tool."""
        service = ToolService()
        
        tool_input = ToolInput(
            tool_name="nonexistent_tool",
            parameters={}
        )
        
        result = await service.execute_tool(tool_input)
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self):
        """Test result caching."""
        service = ToolService()
        service.enable_caching = True
        tool = MockTool()
        service.register_tool(tool)
        
        tool_input = ToolInput(
            tool_name="mock_tool",
            parameters={"test_param": "cache_test"}
        )
        
        # First execution
        result1 = await service.execute_tool(tool_input)
        assert result1.success is True
        
        # Second execution should be cached
        result2 = await service.execute_tool(tool_input)
        assert result2.success is True
        assert result2.metadata.get("cached") is True
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        service = ToolService()
        health = await service.health_check()
        
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in health
        assert "timestamp" in health


class TestCoreTools:
    """Test core tool implementations."""
    
    @pytest.mark.asyncio
    async def test_date_tool(self):
        """Test date tool."""
        tool = DateTool()
        
        tool_input = ToolInput(
            tool_name="get_current_date",
            parameters={}
        )
        
        result = await tool.execute(tool_input)
        
        assert result.success is True
        assert isinstance(result.result, str)
        assert len(result.result) > 0
    
    @pytest.mark.asyncio
    async def test_time_tool_no_location(self):
        """Test time tool without location."""
        tool = TimeTool()
        
        tool_input = ToolInput(
            tool_name="get_current_time",
            parameters={}
        )
        
        result = await tool.execute(tool_input)
        
        assert result.success is True
        assert "current time" in result.result.lower()
    
    @pytest.mark.asyncio
    async def test_weather_tool_validation(self):
        """Test weather tool parameter validation."""
        tool = WeatherTool()
        
        # Test with missing location
        tool_input = ToolInput(
            tool_name="get_weather",
            parameters={}
        )
        
        result = await tool.execute(tool_input)
        
        assert result.success is False
        assert "required parameter" in result.error.lower()


class TestCoreToolsRegistry:
    """Test core tools registry functionality."""
    
    def test_get_core_tool_names(self):
        """Test getting core tool names."""
        names = get_core_tool_names()
        
        assert isinstance(names, list)
        assert len(names) > 0
        assert "get_current_date" in names
        assert "get_current_time" in names
        assert "get_weather" in names
    
    @pytest.mark.asyncio
    async def test_register_core_tools(self):
        """Test registering core tools."""
        service = ToolService()
        success = register_core_tools(service)
        
        assert success is True
        
        # Check some tools are registered
        assert service.get_tool_metadata("get_current_date") is not None
        assert service.get_tool_metadata("get_current_time") is not None
        assert service.get_tool_metadata("get_weather") is not None
        
        # Check aliases work
        assert service.registry.get_tool("date") is not None
        assert service.registry.get_tool("time") is not None
        assert service.registry.get_tool("weather") is not None
    
    @pytest.mark.asyncio
    async def test_initialize_core_tools(self):
        """Test core tools initialization."""
        service = await initialize_core_tools()
        
        assert isinstance(service, ToolService)
        
        # Check tools are available
        tools = service.list_tools()
        assert len(tools) > 0
        
        # Test a tool execution
        tool_input = ToolInput(
            tool_name="get_current_date",
            parameters={}
        )
        
        result = await service.execute_tool(tool_input)
        assert result.success is True


class TestGlobalService:
    """Test global service functionality."""
    
    def test_get_tool_service(self):
        """Test getting global tool service."""
        service1 = get_tool_service()
        service2 = get_tool_service()
        
        # Should return same instance
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_initialize_tool_service(self):
        """Test initializing global tool service."""
        service = await initialize_tool_service()
        
        assert isinstance(service, ToolService)
        
        # Should be same as global instance
        global_service = get_tool_service()
        assert service is global_service


if __name__ == "__main__":
    pytest.main([__file__])