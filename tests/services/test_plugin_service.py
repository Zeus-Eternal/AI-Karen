"""
Unit tests for Plugin Service components.
"""

import asyncio
import json
import pytest
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.ai_karen_engine.services.plugin_registry import (
    PluginRegistry, PluginMetadata, PluginManifest, PluginStatus, PluginType
)
from src.ai_karen_engine.services.plugin_execution import (
    PluginExecutionEngine, ExecutionRequest, ExecutionResult, ExecutionMode, ExecutionStatus
)
from src.ai_karen_engine.services.plugin_service import (
    PluginService, get_plugin_service, initialize_plugin_service
)


class TestPluginRegistry:
    """Test cases for PluginRegistry."""
    
    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary plugin directory with test plugins."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test plugin
            plugin_dir = temp_path / "test_plugin"
            plugin_dir.mkdir()
            
            # Create manifest
            manifest = {
                "name": "test_plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "author": "Test Author",
                "plugin_type": "example",
                "module": "test_plugin.handler",
                "category": "test"
            }
            
            with open(plugin_dir / "plugin_manifest.json", "w") as f:
                json.dump(manifest, f)
            
            # Create handler
            handler_code = '''
async def run(params):
    """Test plugin handler."""
    return {"message": "Hello from test plugin", "params": params}
'''
            with open(plugin_dir / "handler.py", "w") as f:
                f.write(handler_code)
            
            # Create __init__.py
            with open(plugin_dir / "__init__.py", "w") as f:
                f.write("")
            
            yield temp_path
    
    @pytest.fixture
    def plugin_registry(self, temp_plugin_dir):
        """Create plugin registry with test plugins."""
        return PluginRegistry(marketplace_path=temp_plugin_dir)
    
    @pytest.mark.asyncio
    async def test_discover_plugins(self, plugin_registry):
        """Test plugin discovery."""
        # Discover plugins
        discovered = await plugin_registry.discover_plugins()
        
        # Verify discovery
        assert len(discovered) == 1
        assert "test_plugin" in discovered
        
        plugin_metadata = discovered["test_plugin"]
        assert plugin_metadata.manifest.name == "test_plugin"
        assert plugin_metadata.manifest.version == "1.0.0"
        assert plugin_metadata.status == PluginStatus.DISCOVERED
    
    @pytest.mark.asyncio
    async def test_validate_plugin(self, plugin_registry):
        """Test plugin validation."""
        # First discover plugins
        await plugin_registry.discover_plugins()
        
        # Validate plugin
        result = await plugin_registry.validate_plugin("test_plugin")
        
        # Verify validation
        assert result is True
        
        plugin_metadata = plugin_registry.get_plugin("test_plugin")
        assert plugin_metadata.status == PluginStatus.VALIDATED
        assert plugin_metadata.dependencies_resolved is True
        assert plugin_metadata.compatibility_checked is True
    
    @pytest.mark.asyncio
    async def test_register_plugin(self, plugin_registry):
        """Test plugin registration."""
        # Discover and validate first
        await plugin_registry.discover_plugins()
        await plugin_registry.validate_plugin("test_plugin")
        
        # Register plugin
        result = await plugin_registry.register_plugin("test_plugin")
        
        # Verify registration
        assert result is True
        
        plugin_metadata = plugin_registry.get_plugin("test_plugin")
        assert plugin_metadata.status == PluginStatus.REGISTERED
    
    def test_get_plugins_by_category(self, plugin_registry):
        """Test getting plugins by category."""
        # Add a test plugin manually
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category="test",
            module="test.handler"
        )
        
        metadata = PluginMetadata(
            manifest=manifest,
            path=Path("/fake/path"),
            status=PluginStatus.REGISTERED
        )
        
        plugin_registry.plugins["test_plugin"] = metadata
        plugin_registry._update_indices()
        
        # Get plugins by category
        test_plugins = plugin_registry.get_plugins_by_category("test")
        
        assert len(test_plugins) == 1
        assert test_plugins[0].manifest.name == "test_plugin"
    
    def test_get_registry_stats(self, plugin_registry):
        """Test getting registry statistics."""
        # Add test plugins manually
        for i in range(3):
            manifest = PluginManifest(
                name=f"plugin_{i}",
                version="1.0.0",
                description=f"Test plugin {i}",
                author="Test Author",
                category="test",
                plugin_type=PluginType.EXAMPLE,
                module=f"plugin_{i}.handler"
            )
            
            metadata = PluginMetadata(
                manifest=manifest,
                path=Path(f"/fake/path/{i}"),
                status=PluginStatus.REGISTERED if i < 2 else PluginStatus.DISCOVERED
            )
            
            plugin_registry.plugins[f"plugin_{i}"] = metadata
        
        plugin_registry._update_indices()
        
        # Get stats
        stats = plugin_registry.get_registry_stats()
        
        assert stats["total_plugins"] == 3
        assert stats["by_status"]["registered"] == 2
        assert stats["by_status"]["discovered"] == 1
        assert stats["by_type"]["example"] == 3
        assert stats["by_category"]["test"] == 3


class TestPluginExecutionEngine:
    """Test cases for PluginExecutionEngine."""
    
    @pytest.fixture
    def mock_registry(self):
        """Create mock plugin registry."""
        registry = Mock()
        
        # Create mock plugin metadata
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            module="test_plugin.handler"
        )
        
        metadata = PluginMetadata(
            manifest=manifest,
            path=Path("/fake/path"),
            status=PluginStatus.REGISTERED
        )
        
        registry.get_plugin.return_value = metadata
        return registry
    
    @pytest.fixture
    def execution_engine(self, mock_registry):
        """Create plugin execution engine."""
        return PluginExecutionEngine(mock_registry)
    
    @pytest.mark.asyncio
    async def test_execute_plugin_request_creation(self, execution_engine):
        """Test execution request creation."""
        request = ExecutionRequest(
            plugin_name="test_plugin",
            parameters={"key": "value"},
            execution_mode=ExecutionMode.DIRECT,
            timeout_seconds=30
        )
        
        assert request.plugin_name == "test_plugin"
        assert request.parameters == {"key": "value"}
        assert request.execution_mode == ExecutionMode.DIRECT
        assert request.timeout_seconds == 30
        assert request.request_id is not None
    
    @pytest.mark.asyncio
    async def test_validate_and_sanitize_input(self, execution_engine, mock_registry):
        """Test input validation and sanitization."""
        # Test valid input
        valid_params = {"key": "value", "number": 42}
        result = await execution_engine._validate_and_sanitize_input(
            valid_params, mock_registry.get_plugin.return_value
        )
        assert result == valid_params
        
        # Test invalid input (not a dict)
        with pytest.raises(ValueError, match="must be a dictionary"):
            await execution_engine._validate_and_sanitize_input(
                "not a dict", mock_registry.get_plugin.return_value
            )
    
    @pytest.mark.asyncio
    async def test_validate_and_sanitize_output(self, execution_engine, mock_registry):
        """Test output validation and sanitization."""
        from src.ai_karen_engine.services.plugin_execution import ResourceLimits
        
        resource_limits = ResourceLimits(max_output_size_kb=1)
        
        # Test valid output
        valid_output = {"result": "success"}
        result = await execution_engine._validate_and_sanitize_output(
            valid_output, mock_registry.get_plugin.return_value, resource_limits
        )
        assert result == valid_output
        
        # Test oversized output
        large_output = {"data": "x" * 2000}  # Larger than 1KB limit
        with pytest.raises(ValueError, match="too large"):
            await execution_engine._validate_and_sanitize_output(
                large_output, mock_registry.get_plugin.return_value, resource_limits
            )
    
    def test_execution_metrics(self, execution_engine):
        """Test execution metrics tracking."""
        metrics = execution_engine.get_execution_metrics()
        
        assert "executions_total" in metrics
        assert "executions_successful" in metrics
        assert "executions_failed" in metrics
        assert "executions_timeout" in metrics
        assert "average_execution_time" in metrics
        assert "total_execution_time" in metrics
    
    def test_active_executions_tracking(self, execution_engine):
        """Test active executions tracking."""
        # Initially no active executions
        active = execution_engine.get_active_executions()
        assert len(active) == 0
        
        # Add mock active execution
        result = ExecutionResult(
            request_id="test-123",
            plugin_name="test_plugin",
            status=ExecutionStatus.RUNNING
        )
        execution_engine.active_executions["test-123"] = result
        
        # Check active executions
        active = execution_engine.get_active_executions()
        assert len(active) == 1
        assert active[0].request_id == "test-123"
    
    def test_execution_history(self, execution_engine):
        """Test execution history management."""
        # Initially no history
        history = execution_engine.get_execution_history()
        assert len(history) == 0
        
        # Add mock execution to history
        result = ExecutionResult(
            request_id="test-123",
            plugin_name="test_plugin",
            status=ExecutionStatus.COMPLETED
        )
        execution_engine._add_to_history(result)
        
        # Check history
        history = execution_engine.get_execution_history()
        assert len(history) == 1
        assert history[0].request_id == "test-123"


class TestPluginService:
    """Test cases for PluginService."""
    
    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary plugin directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple test plugin
            plugin_dir = temp_path / "simple_plugin"
            plugin_dir.mkdir()
            
            manifest = {
                "name": "simple_plugin",
                "version": "1.0.0",
                "description": "Simple test plugin",
                "author": "Test Author",
                "module": "simple_plugin.handler"
            }
            
            with open(plugin_dir / "plugin_manifest.json", "w") as f:
                json.dump(manifest, f)
            
            handler_code = '''
def run(params):
    """Simple synchronous handler."""
    return {"status": "success", "input": params}
'''
            with open(plugin_dir / "handler.py", "w") as f:
                f.write(handler_code)
            
            with open(plugin_dir / "__init__.py", "w") as f:
                f.write("")
            
            yield temp_path
    
    @pytest.fixture
    def plugin_service(self, temp_plugin_dir):
        """Create plugin service with test plugins."""
        return PluginService(marketplace_path=temp_plugin_dir)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, plugin_service):
        """Test plugin service initialization."""
        assert not plugin_service.initialized
        
        await plugin_service.initialize()
        
        assert plugin_service.initialized
        assert plugin_service.registry is not None
        assert plugin_service.execution_engine is not None
    
    @pytest.mark.asyncio
    async def test_discover_and_register_workflow(self, plugin_service):
        """Test complete discover and register workflow."""
        await plugin_service.initialize()
        
        # Discover plugins
        discovered = await plugin_service.discover_plugins()
        assert len(discovered) == 1
        assert "simple_plugin" in discovered
        
        # Validate and register
        result = await plugin_service.validate_and_register_plugin("simple_plugin")
        assert result is True
        
        # Check plugin is available
        plugin = plugin_service.get_plugin("simple_plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.REGISTERED
    
    @pytest.mark.asyncio
    async def test_validate_and_register_all_discovered(self, plugin_service):
        """Test bulk validation and registration."""
        await plugin_service.initialize()
        await plugin_service.discover_plugins()
        
        results = await plugin_service.validate_and_register_all_discovered()
        
        assert len(results) == 1
        assert results["simple_plugin"] is True
    
    @pytest.mark.asyncio
    async def test_get_plugins_by_various_criteria(self, plugin_service):
        """Test getting plugins by different criteria."""
        await plugin_service.initialize()
        await plugin_service.discover_plugins()
        await plugin_service.validate_and_register_plugin("simple_plugin")
        
        # By status
        registered = plugin_service.get_plugins_by_status(PluginStatus.REGISTERED)
        assert len(registered) == 1
        
        # Available plugins
        available = plugin_service.get_available_plugins()
        assert len(available) == 1
        assert available[0].manifest.name == "simple_plugin"
    
    @pytest.mark.asyncio
    async def test_service_stats(self, plugin_service):
        """Test service statistics."""
        await plugin_service.initialize()
        await plugin_service.discover_plugins()
        
        stats = plugin_service.get_service_stats()
        
        assert "initialized" in stats
        assert "registry_stats" in stats
        assert "execution_metrics" in stats
        assert "active_executions" in stats
        assert "timestamp" in stats
        
        assert stats["initialized"] is True
        assert stats["registry_stats"]["total_plugins"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check(self, plugin_service):
        """Test service health check."""
        # Health check before initialization
        health = await plugin_service.health_check()
        assert health["status"] == "unhealthy"
        
        # Health check after initialization
        await plugin_service.initialize()
        health = await plugin_service.health_check()
        
        assert health["status"] in ["healthy", "degraded"]
        assert "components" in health
        assert "registry" in health["components"]
        assert "execution_engine" in health["components"]
    
    @pytest.mark.asyncio
    async def test_cleanup(self, plugin_service):
        """Test service cleanup."""
        await plugin_service.initialize()
        assert plugin_service.initialized is True
        
        await plugin_service.cleanup()
        assert plugin_service.initialized is False


class TestPluginServiceIntegration:
    """Integration tests for plugin service components."""
    
    @pytest.fixture
    def temp_marketplace(self):
        """Create temporary marketplace with multiple plugins."""
        with tempfile.TemporaryDirectory() as temp_dir:
            marketplace = Path(temp_dir)
            
            # Create example category
            examples_dir = marketplace / "examples"
            examples_dir.mkdir()
            
            # Create hello world plugin
            hello_dir = examples_dir / "hello-world"
            hello_dir.mkdir()
            
            hello_manifest = {
                "name": "hello-world",
                "version": "1.0.0",
                "description": "Hello world example plugin",
                "author": "AI Karen Team",
                "category": "examples",
                "plugin_type": "example",
                "module": "hello_world.handler",
                "tags": ["example", "greeting"]
            }
            
            with open(hello_dir / "plugin_manifest.json", "w") as f:
                json.dump(hello_manifest, f)
            
            hello_handler = '''
async def run(params):
    """Hello world plugin."""
    name = params.get("name", "World")
    return {"message": f"Hello, {name}!"}
'''
            with open(hello_dir / "handler.py", "w") as f:
                f.write(hello_handler)
            
            with open(hello_dir / "__init__.py", "w") as f:
                f.write("")
            
            # Create math plugin
            math_dir = examples_dir / "math-calculator"
            math_dir.mkdir()
            
            math_manifest = {
                "name": "math-calculator",
                "version": "1.0.0",
                "description": "Simple math calculator",
                "author": "AI Karen Team",
                "category": "examples",
                "plugin_type": "example",
                "module": "math_calculator.handler",
                "tags": ["math", "calculator"]
            }
            
            with open(math_dir / "plugin_manifest.json", "w") as f:
                json.dump(math_manifest, f)
            
            math_handler = '''
def run(params):
    """Math calculator plugin."""
    operation = params.get("operation", "add")
    a = params.get("a", 0)
    b = params.get("b", 0)
    
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "Division by zero"}
        result = a / b
    else:
        return {"error": f"Unknown operation: {operation}"}
    
    return {"result": result, "operation": operation, "a": a, "b": b}
'''
            with open(math_dir / "handler.py", "w") as f:
                f.write(math_handler)
            
            with open(math_dir / "__init__.py", "w") as f:
                f.write("")
            
            yield marketplace
    
    @pytest.mark.asyncio
    async def test_full_plugin_lifecycle(self, temp_marketplace):
        """Test complete plugin lifecycle from discovery to execution."""
        # Initialize service
        service = PluginService(marketplace_path=temp_marketplace)
        await service.initialize()
        
        # Discover plugins
        discovered = await service.discover_plugins()
        assert len(discovered) == 2
        assert "hello-world" in discovered
        assert "math-calculator" in discovered
        
        # Validate and register all
        results = await service.validate_and_register_all_discovered()
        assert all(results.values())
        
        # Execute hello-world plugin
        hello_result = await service.execute_plugin(
            plugin_name="hello-world",
            parameters={"name": "AI Karen"},
            execution_mode=ExecutionMode.DIRECT
        )
        
        assert hello_result.status == ExecutionStatus.COMPLETED
        assert hello_result.result["message"] == "Hello, AI Karen!"
        
        # Execute math plugin
        math_result = await service.execute_plugin(
            plugin_name="math-calculator",
            parameters={"operation": "multiply", "a": 6, "b": 7},
            execution_mode=ExecutionMode.DIRECT
        )
        
        assert math_result.status == ExecutionStatus.COMPLETED
        assert math_result.result["result"] == 42
        
        # Check execution history
        history = service.get_execution_history()
        assert len(history) == 2
        
        # Check service stats
        stats = service.get_service_stats()
        assert stats["execution_metrics"]["executions_total"] == 2
        assert stats["execution_metrics"]["executions_successful"] == 2
        
        # Cleanup
        await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_plugin_categorization_and_filtering(self, temp_marketplace):
        """Test plugin categorization and filtering capabilities."""
        service = PluginService(marketplace_path=temp_marketplace)
        await service.initialize()
        
        # Discover and register plugins
        await service.discover_plugins()
        await service.validate_and_register_all_discovered()
        
        # Test category filtering
        examples = service.get_plugins_by_category("examples")
        assert len(examples) == 2
        
        # Test type filtering
        example_plugins = service.get_plugins_by_type(PluginType.EXAMPLE)
        assert len(example_plugins) == 2
        
        # Test status filtering
        registered = service.get_plugins_by_status(PluginStatus.REGISTERED)
        assert len(registered) == 2
        
        # Test available plugins
        available = service.get_available_plugins()
        assert len(available) == 2
        
        plugin_names = [p.manifest.name for p in available]
        assert "hello-world" in plugin_names
        assert "math-calculator" in plugin_names
        
        await service.cleanup()


# Test global service functions
class TestGlobalServiceFunctions:
    """Test global service functions."""
    
    @pytest.mark.asyncio
    async def test_get_plugin_service(self):
        """Test getting global plugin service."""
        service1 = get_plugin_service()
        service2 = get_plugin_service()
        
        # Should return same instance
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_initialize_plugin_service(self):
        """Test initializing global plugin service."""
        service = await initialize_plugin_service(auto_discover=False)
        
        assert service.initialized is True
        assert service.registry is not None
        assert service.execution_engine is not None
        
        await service.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])