"""
Unit tests for BaseExtension class.
Tests extension lifecycle, hook management, and capability registration.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extensions.base import BaseExtension, BackgroundTask
from ai_karen_engine.extension_host.models2 import ExtensionManifest, ExtensionContext
from ai_karen_engine.extensions.orchestrator import PluginOrchestrator
from ai_karen_engine.extensions.data_manager import ExtensionDataManager
from ai_karen_engine.hooks.hook_types import HookTypes


class TestExtension(BaseExtension):
    """Test extension implementation."""
    
    def __init__(self, manifest, context):
        super().__init__(manifest, context)
        self.test_initialized = False
        self.test_shutdown = False
    
    async def _initialize(self):
        self.test_initialized = True
    
    async def _shutdown(self):
        self.test_shutdown = True


class TestBaseExtension:
    """Test BaseExtension functionality."""
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router."""
        router = Mock()
        router.dispatch = AsyncMock(return_value="plugin_result")
        return router
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def sample_manifest(self):
        """Create sample extension manifest."""
        return ExtensionManifest(
            name="test-extension",
            version="1.0.0",
            display_name="Test Extension",
            description="A test extension",
            author="Test Author",
            license="MIT",
            api_version="1.0",
            kari_min_version="0.4.0"
        )
    
    @pytest.fixture
    def extension_context(self, mock_plugin_router, mock_db_session):
        """Create extension context."""
        return ExtensionContext(
            plugin_router=mock_plugin_router,
            db_session=mock_db_session,
            app_instance=None
        )
    
    @pytest.fixture
    def test_extension(self, sample_manifest, extension_context):
        """Create test extension instance."""
        return TestExtension(sample_manifest, extension_context)
    
    # Test Initialization
    def test_extension_creation(self, test_extension, sample_manifest):
        """Test extension creation and basic properties."""
        assert test_extension.manifest == sample_manifest
        assert test_extension.name == "test-extension"
        assert test_extension.logger is not None
        assert test_extension.plugin_orchestrator is not None
        assert test_extension.data_manager is not None
        assert not test_extension._initialized
    
    @pytest.mark.asyncio
    async def test_extension_initialization(self, test_extension):
        """Test extension initialization process."""
        assert not test_extension.test_initialized
        assert not test_extension._initialized
        
        await test_extension.initialize()
        
        assert test_extension.test_initialized
        assert test_extension._initialized
    
    @pytest.mark.asyncio
    async def test_extension_shutdown(self, test_extension):
        """Test extension shutdown process."""
        # Initialize first
        await test_extension.initialize()
        assert test_extension._initialized
        
        # Shutdown
        await test_extension.shutdown()
        assert test_extension.test_shutdown
        assert not test_extension._initialized
    
    @pytest.mark.asyncio
    async def test_extension_initialization_with_capabilities(self, sample_manifest, extension_context):
        """Test extension initialization with capabilities."""
        # Add capabilities to manifest
        sample_manifest.capabilities = Mock()
        sample_manifest.capabilities.provides_api = True
        sample_manifest.capabilities.provides_background_tasks = True
        sample_manifest.capabilities.provides_ui = True
        
        extension = TestExtension(sample_manifest, extension_context)
        
        with patch.object(extension, 'create_api_router', return_value=Mock()) as mock_api, \
             patch.object(extension, 'create_background_tasks', return_value=[]) as mock_tasks, \
             patch.object(extension, 'create_ui_components', return_value={}) as mock_ui:
            
            await extension.initialize()
            
            mock_api.assert_called_once()
            mock_tasks.assert_called_once()
            mock_ui.assert_called_once()
            assert extension._api_router is not None
    
    # Test Status and Properties
    def test_is_initialized(self, test_extension):
        """Test is_initialized property."""
        assert not test_extension.is_initialized()
        
        async def test():
            await test_extension.initialize()
            assert test_extension.is_initialized()
        
        asyncio.run(test())
    
    def test_get_status(self, test_extension):
        """Test get_status method."""
        status = test_extension.get_status()
        
        assert status["name"] == "test-extension"
        assert status["version"] == "1.0.0"
        assert status["initialized"] is False
        assert status["has_api"] is False
        assert status["background_tasks"] == 0
        assert status["ui_components"] == 0
        assert status["has_mcp_server"] is False
        assert status["has_mcp_client"] is False
    
    def test_get_status_after_initialization(self, test_extension):
        """Test get_status after initialization."""
        async def test():
            await test_extension.initialize()
            status = test_extension.get_status()
            assert status["initialized"] is True
        
        asyncio.run(test())
    
    # Test Capability Creation
    def test_create_api_router_no_fastapi(self, test_extension):
        """Test API router creation when FastAPI is not available."""
        with patch('ai_karen_engine.extensions.base.FASTAPI_AVAILABLE', False):
            router = test_extension.create_api_router()
            assert router is None
    
    def test_create_api_router_with_fastapi(self, test_extension):
        """Test API router creation when FastAPI is available."""
        with patch('ai_karen_engine.extensions.base.FASTAPI_AVAILABLE', True):
            router = test_extension.create_api_router()
            assert router is not None
    
    def test_create_background_tasks_empty(self, test_extension):
        """Test background task creation with no tasks."""
        tasks = test_extension.create_background_tasks()
        assert tasks == []
    
    def test_create_background_tasks_with_manifest_tasks(self, sample_manifest, extension_context):
        """Test background task creation with manifest tasks."""
        # Add background tasks to manifest
        task_config = Mock()
        task_config.name = "test_task"
        task_config.schedule = "0 * * * *"
        task_config.function = "test_function"
        
        sample_manifest.background_tasks = [task_config]
        
        extension = TestExtension(sample_manifest, extension_context)
        tasks = extension.create_background_tasks()
        
        assert len(tasks) == 1
        assert tasks[0].name == "test_task"
        assert tasks[0].schedule == "0 * * * *"
        assert tasks[0].function == "test_function"
    
    def test_create_ui_components_empty(self, test_extension):
        """Test UI component creation with no components."""
        components = test_extension.create_ui_components()
        assert components == {}
    
    def test_create_ui_components_with_manifest_ui(self, sample_manifest, extension_context):
        """Test UI component creation with manifest UI config."""
        # Add UI config to manifest
        ui_config = Mock()
        ui_config.control_room_pages = ["page1", "page2"]
        
        sample_manifest.ui = ui_config
        
        extension = TestExtension(sample_manifest, extension_context)
        components = extension.create_ui_components()
        
        assert components == {"control_room_pages": ["page1", "page2"]}
    
    # Test Getters
    def test_get_api_router(self, test_extension):
        """Test get_api_router method."""
        assert test_extension.get_api_router() is None
        
        # Set router and test again
        mock_router = Mock()
        test_extension._api_router = mock_router
        assert test_extension.get_api_router() == mock_router
    
    def test_get_ui_components(self, test_extension):
        """Test get_ui_components method."""
        assert test_extension.get_ui_components() == {}
        
        # Set components and test again
        components = {"test": "component"}
        test_extension._ui_components = components
        assert test_extension.get_ui_components() == components
    
    def test_get_background_tasks(self, test_extension):
        """Test get_background_tasks method."""
        assert test_extension.get_background_tasks() == []
        
        # Set tasks and test again
        tasks = [BackgroundTask("test", "* * * * *", "func")]
        test_extension._background_tasks = tasks
        assert test_extension.get_background_tasks() == tasks
    
    # Test MCP Integration
    def test_get_mcp_server_none(self, test_extension):
        """Test get_mcp_server when none exists."""
        assert test_extension.get_mcp_server() is None
    
    def test_get_mcp_client_none(self, test_extension):
        """Test get_mcp_client when none exists."""
        assert test_extension.get_mcp_client() is None
    
    def test_create_mcp_server_not_available(self, test_extension):
        """Test MCP server creation when MCP is not available."""
        with patch('ai_karen_engine.extensions.base.MCP_AVAILABLE', False):
            server = test_extension.create_mcp_server()
            assert server is None
    
    def test_create_mcp_client_not_available(self, test_extension):
        """Test MCP client creation when MCP is not available."""
        with patch('ai_karen_engine.extensions.base.MCP_AVAILABLE', False):
            client = test_extension.create_mcp_client(Mock())
            assert client is None
    
    @pytest.mark.asyncio
    async def test_register_mcp_tool_no_server(self, test_extension):
        """Test MCP tool registration without server."""
        result = await test_extension.register_mcp_tool(
            "test_tool", AsyncMock(), {}, "Test tool"
        )
        assert result is False
    
    @pytest.mark.asyncio
    async def test_discover_mcp_tools_no_client(self, test_extension):
        """Test MCP tool discovery without client."""
        tools = await test_extension.discover_mcp_tools()
        assert tools == {}
    
    @pytest.mark.asyncio
    async def test_call_mcp_tool_no_client(self, test_extension):
        """Test MCP tool calling without client."""
        with pytest.raises(RuntimeError, match="MCP client not available"):
            await test_extension.call_mcp_tool("service", "tool", {})
    
    # Test Hook Management
    @pytest.mark.asyncio
    async def test_register_extension_hook(self, test_extension):
        """Test registering extension hook."""
        handler = AsyncMock()
        
        with patch.object(test_extension, 'register_hook', return_value="hook_id") as mock_register:
            hook_id = await test_extension.register_extension_hook(
                "test_hook", handler, priority=60
            )
            
            assert hook_id == "hook_id"
            assert "hook_id" in test_extension._registered_hooks
            assert "test_hook" in test_extension._hook_handlers
            
            mock_register.assert_called_once_with(
                hook_type="test_hook",
                handler=handler,
                priority=60,
                conditions=None,
                source_name="test-extension_extension"
            )
    
    @pytest.mark.asyncio
    async def test_unregister_extension_hook(self, test_extension):
        """Test unregistering extension hook."""
        # First register a hook
        test_extension._registered_hooks.append("hook_id")
        
        with patch.object(test_extension, 'unregister_hook', return_value=True) as mock_unregister:
            success = await test_extension.unregister_extension_hook("hook_id")
            
            assert success is True
            assert "hook_id" not in test_extension._registered_hooks
            mock_unregister.assert_called_once_with("hook_id")
    
    @pytest.mark.asyncio
    async def test_handle_hook_custom_handler(self, test_extension):
        """Test handling hook with custom handler."""
        handler = AsyncMock(return_value="custom_result")
        test_extension._hook_handlers["test_hook"] = handler
        
        result = await test_extension.handle_hook("test_hook", {"data": "test"})
        
        assert result == "custom_result"
        handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_hook_default_handler(self, test_extension):
        """Test handling hook with default handler."""
        result = await test_extension.handle_hook(
            HookTypes.EXTENSION_LOADED, {"timestamp": "2023-01-01"}
        )
        
        assert result["extension_name"] == "test-extension"
        assert result["hook_type"] == HookTypes.EXTENSION_LOADED
        assert result["handled_by"] == "default_handler"
        assert result["status"] == "loaded"
    
    @pytest.mark.asyncio
    async def test_handle_hook_handler_error(self, test_extension):
        """Test handling hook when handler raises error."""
        handler = AsyncMock(side_effect=RuntimeError("Handler error"))
        test_extension._hook_handlers["test_hook"] = handler
        
        with pytest.raises(RuntimeError, match="Handler error"):
            await test_extension.handle_hook("test_hook", {})
    
    @pytest.mark.asyncio
    async def test_setup_extension_hooks(self, test_extension):
        """Test setting up standard extension hooks."""
        with patch.object(test_extension, 'register_extension_hook') as mock_register:
            await test_extension.setup_extension_hooks()
            
            # Should register 4 lifecycle hooks
            assert mock_register.call_count == 4
            
            # Check hook types
            hook_types = [call[0][0] for call in mock_register.call_args_list]
            expected_hooks = [
                HookTypes.EXTENSION_LOADED,
                HookTypes.EXTENSION_ACTIVATED,
                HookTypes.EXTENSION_DEACTIVATED,
                HookTypes.EXTENSION_UNLOADED
            ]
            for expected_hook in expected_hooks:
                assert expected_hook in hook_types
    
    @pytest.mark.asyncio
    async def test_cleanup_extension_hooks(self, test_extension):
        """Test cleaning up extension hooks."""
        # Add some hooks
        test_extension._registered_hooks = ["hook1", "hook2"]
        test_extension._hook_handlers = {"type1": Mock(), "type2": Mock()}
        
        with patch.object(test_extension, 'unregister_extension_hook') as mock_unregister:
            await test_extension.cleanup_extension_hooks()
            
            assert mock_unregister.call_count == 2
            assert len(test_extension._registered_hooks) == 0
            assert len(test_extension._hook_handlers) == 0
    
    # Test Default Lifecycle Handlers
    @pytest.mark.asyncio
    async def test_on_extension_loaded(self, test_extension):
        """Test default extension loaded handler."""
        result = await test_extension._on_extension_loaded({"timestamp": "2023-01-01"})
        
        assert result["extension_name"] == "test-extension"
        assert result["loaded_successfully"] is True
        assert result["timestamp"] == "2023-01-01"
    
    @pytest.mark.asyncio
    async def test_on_extension_activated(self, test_extension):
        """Test default extension activated handler."""
        result = await test_extension._on_extension_activated({})
        
        assert result["extension_name"] == "test-extension"
        assert result["activated_successfully"] is True
        assert result["initialization_complete"] is False  # Not initialized yet
    
    @pytest.mark.asyncio
    async def test_on_extension_deactivated(self, test_extension):
        """Test default extension deactivated handler."""
        result = await test_extension._on_extension_deactivated({"deactivation_reason": "test"})
        
        assert result["extension_name"] == "test-extension"
        assert result["deactivated_successfully"] is True
        assert result["cleanup_reason"] == "test"
    
    @pytest.mark.asyncio
    async def test_on_extension_unloaded(self, test_extension):
        """Test default extension unloaded handler."""
        result = await test_extension._on_extension_unloaded({})
        
        assert result["extension_name"] == "test-extension"
        assert result["unloaded_successfully"] is True
        assert result["hooks_cleaned"] is True  # No hooks registered
    
    def test_get_extension_hook_summary(self, test_extension):
        """Test getting extension hook summary."""
        # Add some test data
        test_extension._registered_hooks = ["hook1", "hook2"]
        test_extension._hook_handlers = {"type1": Mock(), "type2": Mock()}
        
        with patch.object(test_extension, 'are_hooks_enabled', return_value=True), \
             patch.object(test_extension, 'get_hook_stats', return_value={"calls": 5}):
            
            summary = test_extension.get_extension_hook_summary()
            
            assert summary["extension_name"] == "test-extension"
            assert summary["hooks_enabled"] is True
            assert summary["registered_hooks"] == 2
            assert summary["hook_types"] == ["type1", "type2"]
            assert summary["hook_stats"] == {"calls": 5}
    
    # Test AI-Powered Hooks
    @pytest.mark.asyncio
    async def test_register_ai_powered_hook_without_provider(self, test_extension):
        """Test registering AI-powered hook without context provider."""
        handler = AsyncMock(return_value="result")
        
        with patch.object(test_extension, 'register_extension_hook', return_value="hook_id") as mock_register:
            hook_id = await test_extension.register_ai_powered_hook("test_hook", handler)
            
            assert hook_id == "hook_id"
            mock_register.assert_called_once()
            
            # Test the enhanced handler
            enhanced_handler = mock_register.call_args[1]["handler"]
            result = await enhanced_handler({"test": "context"})
            assert result == "result"
    
    @pytest.mark.asyncio
    async def test_register_ai_powered_hook_with_provider(self, test_extension):
        """Test registering AI-powered hook with context provider."""
        handler = AsyncMock(return_value="result")
        ai_provider = AsyncMock(return_value={"ai_data": "enhanced"})
        
        with patch.object(test_extension, 'register_extension_hook', return_value="hook_id") as mock_register:
            hook_id = await test_extension.register_ai_powered_hook(
                "test_hook", handler, ai_provider
            )
            
            assert hook_id == "hook_id"
            
            # Test the enhanced handler
            enhanced_handler = mock_register.call_args[1]["handler"]
            result = await enhanced_handler({"test": "context"})
            
            # AI provider should have been called
            ai_provider.assert_called_once()
            # Handler should have been called with enhanced context
            handler.assert_called_once()
            call_args = handler.call_args[0][0]  # First positional argument (context)
            assert "ai_context" in call_args
            assert call_args["ai_enhanced"] is True
    
    @pytest.mark.asyncio
    async def test_register_ai_powered_hook_provider_error(self, test_extension):
        """Test AI-powered hook when context provider fails."""
        handler = AsyncMock(return_value="result")
        ai_provider = AsyncMock(side_effect=RuntimeError("AI provider error"))
        
        with patch.object(test_extension, 'register_extension_hook', return_value="hook_id") as mock_register:
            await test_extension.register_ai_powered_hook("test_hook", handler, ai_provider)
            
            # Test the enhanced handler - should continue despite AI provider error
            enhanced_handler = mock_register.call_args[1]["handler"]
            result = await enhanced_handler({"test": "context"})
            
            assert result == "result"
            handler.assert_called_once()
            # Context should not have AI enhancement due to error
            call_args = handler.call_args[0][0]
            assert "ai_enhanced" not in call_args


class TestBackgroundTask:
    """Test BackgroundTask class."""
    
    def test_background_task_creation(self):
        """Test BackgroundTask creation."""
        task = BackgroundTask("test_task", "0 * * * *", "test_function")
        
        assert task.name == "test_task"
        assert task.schedule == "0 * * * *"
        assert task.function == "test_function"
    
    def test_background_task_with_callable(self):
        """Test BackgroundTask with callable function."""
        def test_func():
            return "test"
        
        task = BackgroundTask("test_task", "0 * * * *", test_func)
        
        assert task.name == "test_task"
        assert task.schedule == "0 * * * *"
        assert task.function == test_func
        assert callable(task.function)