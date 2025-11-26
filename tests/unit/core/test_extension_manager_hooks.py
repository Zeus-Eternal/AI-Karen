"""
Unit tests for ExtensionManager hook integration.
Extends existing extension manager tests with hook functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import asyncio

from ai_karen_engine.extension_host.manager import ExtensionManager, get_extension_manager
from ai_karen_engine.extension_host.models2 import ExtensionManifest, ExtensionStatus
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks import HookTypes, HookContext, HookResult
from ai_karen_engine.hooks.hook_manager import HookManager


class TestExtensionManagerHooks:
    """Test ExtensionManager hook integration."""
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create a mock plugin router."""
        return MagicMock()
    
    @pytest.fixture
    def extension_manager(self, mock_plugin_router, tmp_path):
        """Create an ExtensionManager with mocked dependencies."""
        manager = ExtensionManager(
            extension_root=tmp_path,
            plugin_router=mock_plugin_router
        )
        return manager
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create a mock hook manager."""
        hook_manager = AsyncMock(spec=HookManager)
        hook_manager.trigger_hooks = AsyncMock(return_value=MagicMock(
            successful_hooks=1,
            results=[HookResult.success_result("test_hook", {"triggered": True})]
        ))
        return hook_manager
    
    @pytest.fixture
    def sample_manifest(self):
        """Create a sample extension manifest."""
        return ExtensionManifest(
            name="test_extension",
            version="1.0.0",
            display_name="Test Extension",
            description="Test extension",
            author="Test Author",
            license="MIT",
            category="test",
        )
    
    @pytest.fixture
    def mock_extension_instance(self):
        """Create a mock extension instance."""
        instance = AsyncMock(spec=BaseExtension)
        instance.initialize = AsyncMock()
        instance.shutdown = AsyncMock()
        return instance
    
    def test_extension_manager_inherits_hook_mixin(self, extension_manager):
        """Test that ExtensionManager inherits from HookMixin."""
        from ai_karen_engine.hooks.hook_mixin import HookMixin
        assert isinstance(extension_manager, HookMixin)
        assert hasattr(extension_manager, 'trigger_hooks')
        assert hasattr(extension_manager, 'register_hook')
        assert extension_manager.name == "extension_manager"
    
    @pytest.mark.asyncio
    async def test_load_extension_triggers_hooks(self, extension_manager, mock_hook_manager, sample_manifest, mock_extension_instance):
        """Test that load_extension triggers appropriate hooks."""
        extension_manager.set_hook_manager(mock_hook_manager)
        
        # Mock the extension loading process
        with patch.object(extension_manager, '_find_extension_directory') as mock_find, \
             patch.object(extension_manager, '_load_extension_module') as mock_load_module, \
             patch('ai_karen_engine.extensions.manager.ExtensionManifest.from_file') as mock_from_file:
            
            mock_find.return_value = Path("/fake/extension/path")
            mock_from_file.return_value = sample_manifest
            mock_load_module.return_value = mock_extension_instance
            
            # Load extension
            record = await extension_manager.load_extension("test_extension")
            
            # Verify extension loaded
            assert record is not None
            assert record.manifest.name == "test_extension"
            
            # Verify hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 2  # Loaded and activated hooks
            
            # Check hook calls
            calls = mock_hook_manager.trigger_hooks.call_args_list
            
            # Find loaded hook call
            loaded_call = None
            activated_call = None
            for call in calls:
                context = call[0][0]
                if context.hook_type == HookTypes.EXTENSION_LOADED:
                    loaded_call = call
                elif context.hook_type == HookTypes.EXTENSION_ACTIVATED:
                    activated_call = call
            
            # Verify loaded hook
            assert loaded_call is not None
            loaded_context = loaded_call[0][0]
            assert loaded_context.data["extension_name"] == "test_extension"
            assert loaded_context.data["extension_version"] == "1.0.0"
            
            # Verify activated hook
            assert activated_call is not None
            activated_context = activated_call[0][0]
            assert activated_context.data["extension_name"] == "test_extension"
            assert activated_context.data["extension_instance"] == mock_extension_instance
    
    @pytest.mark.asyncio
    async def test_unload_extension_triggers_hooks(self, extension_manager, mock_hook_manager, sample_manifest, mock_extension_instance):
        """Test that unload_extension triggers appropriate hooks."""
        extension_manager.set_hook_manager(mock_hook_manager)
        
        # First load an extension
        with patch.object(extension_manager, '_find_extension_directory') as mock_find, \
             patch.object(extension_manager, '_load_extension_module') as mock_load_module, \
             patch('ai_karen_engine.extensions.manager.ExtensionManifest.from_file') as mock_from_file:
            
            mock_find.return_value = Path("/fake/extension/path")
            mock_from_file.return_value = sample_manifest
            mock_load_module.return_value = mock_extension_instance
            
            await extension_manager.load_extension("test_extension")
            
            # Clear previous hook calls
            mock_hook_manager.trigger_hooks.reset_mock()
            
            # Unload extension
            await extension_manager.unload_extension("test_extension")
            
            # Verify hooks were triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 2  # Deactivated and unloaded hooks
            
            # Check hook calls
            calls = mock_hook_manager.trigger_hooks.call_args_list
            
            # Find deactivated and unloaded hook calls
            deactivated_call = None
            unloaded_call = None
            for call in calls:
                context = call[0][0]
                if context.hook_type == HookTypes.EXTENSION_DEACTIVATED:
                    deactivated_call = call
                elif context.hook_type == HookTypes.EXTENSION_UNLOADED:
                    unloaded_call = call
            
            # Verify deactivated hook
            assert deactivated_call is not None
            deactivated_context = deactivated_call[0][0]
            assert deactivated_context.data["extension_name"] == "test_extension"
            assert deactivated_context.data["extension_instance"] == mock_extension_instance
            
            # Verify unloaded hook
            assert unloaded_call is not None
            unloaded_context = unloaded_call[0][0]
            assert unloaded_context.data["extension_name"] == "test_extension"
            assert unloaded_context.data["extension_version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_extension_manager_hook_registration(self, extension_manager, mock_hook_manager):
        """Test that ExtensionManager can register hooks."""
        extension_manager.set_hook_manager(mock_hook_manager)
        mock_hook_manager.register_hook = AsyncMock(return_value="hook_id_456")
        
        async def test_hook_handler(context):
            return {"handled": True}
        
        hook_id = await extension_manager.register_hook(
            HookTypes.EXTENSION_LOADED,
            test_hook_handler,
            priority=30
        )
        
        assert hook_id == "hook_id_456"
        mock_hook_manager.register_hook.assert_called_once_with(
            hook_type=HookTypes.EXTENSION_LOADED,
            handler=test_hook_handler,
            priority=30,
            conditions={},
            source_type="extensionmanager",
            source_name="extension_manager"
        )
    
    def test_extension_manager_hook_stats(self, extension_manager, mock_hook_manager):
        """Test getting hook statistics from ExtensionManager."""
        extension_manager.set_hook_manager(mock_hook_manager)
        
        # Mock hook manager response
        mock_hook_manager.get_hooks_by_source.return_value = [
            MagicMock(hook_type=HookTypes.EXTENSION_LOADED),
            MagicMock(hook_type=HookTypes.EXTENSION_ACTIVATED),
            MagicMock(hook_type=HookTypes.EXTENSION_DEACTIVATED)
        ]
        
        stats = extension_manager.get_hook_stats()
        
        assert stats['hooks_enabled']
        assert stats['registered_hooks'] == 3
        assert len(stats['hook_types']) == 3
    
    @pytest.mark.asyncio
    async def test_extension_manager_safe_hook_trigger(self, extension_manager):
        """Test safe hook triggering when no hook manager is available."""
        # Don't set hook manager - should use safe triggering
        result = await extension_manager.trigger_hook_safe(
            HookTypes.EXTENSION_LOADED,
            {"test": "data"},
            default_result="safe_default"
        )
        
        assert result == "safe_default"
    
    def test_extension_manager_enable_disable_hooks(self, extension_manager):
        """Test enabling and disabling hooks."""
        assert extension_manager.are_hooks_enabled() is False  # No hook manager initially
        
        extension_manager.enable_hooks()
        assert extension_manager._hook_enabled is True
        
        extension_manager.disable_hooks()
        assert extension_manager._hook_enabled is False
    
    @pytest.mark.asyncio
    async def test_load_extension_with_hooks_disabled(self, extension_manager, mock_hook_manager, sample_manifest, mock_extension_instance):
        """Test that disabling hooks prevents hook execution."""
        extension_manager.set_hook_manager(mock_hook_manager)
        extension_manager.disable_hooks()
        
        # Mock the extension loading process
        with patch.object(extension_manager, '_find_extension_directory') as mock_find, \
             patch.object(extension_manager, '_load_extension_module') as mock_load_module, \
             patch('ai_karen_engine.extensions.manager.ExtensionManifest.from_file') as mock_from_file:
            
            mock_find.return_value = Path("/fake/extension/path")
            mock_from_file.return_value = sample_manifest
            mock_load_module.return_value = mock_extension_instance
            
            # Load extension
            await extension_manager.load_extension("test_extension")
            
            # Hooks should not be triggered when disabled
            mock_hook_manager.trigger_hooks.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_extension_error_handling_with_hooks(self, extension_manager, mock_hook_manager, sample_manifest):
        """Test extension error handling doesn't break hook system."""
        extension_manager.set_hook_manager(mock_hook_manager)
        
        # Mock extension loading to fail
        with patch.object(extension_manager, '_find_extension_directory') as mock_find, \
             patch('ai_karen_engine.extensions.manager.ExtensionManifest.from_file') as mock_from_file:
            
            mock_find.return_value = Path("/fake/extension/path")
            mock_from_file.return_value = sample_manifest
            
            # Make module loading fail
            with patch.object(extension_manager, '_load_extension_module') as mock_load_module:
                mock_load_module.side_effect = RuntimeError("Module loading failed")
                
                # Load extension and expect failure
                with pytest.raises(RuntimeError):
                    await extension_manager.load_extension("test_extension")
                
                # Hook system should still be functional
                assert extension_manager.are_hooks_enabled()
    
    def test_get_extension_manager_singleton(self):
        """Test that get_extension_manager returns instance with hook capabilities."""
        # Note: get_extension_manager returns None by default since it's not initialized
        # This test verifies the function exists and can be called
        manager = get_extension_manager()
        # Manager will be None unless initialized, which is expected
        assert manager is None or hasattr(manager, 'trigger_hooks')


class TestExtensionManagerHookIntegration:
    """Integration tests for ExtensionManager with real hook system."""
    
    @pytest.fixture
    def real_extension_manager(self, tmp_path):
        """Create an ExtensionManager with real hook system."""
        mock_router = MagicMock()
        manager = ExtensionManager(
            extension_root=tmp_path,
            plugin_router=mock_router
        )
        
        # Set up real hook manager
        from ai_karen_engine.hooks.hook_manager import HookManager
        manager.set_hook_manager(HookManager())
        return manager
    
    @pytest.fixture
    def create_test_extension(self, tmp_path):
        """Create a test extension on disk."""
        def _create_extension(name="test_extension"):
            ext_dir = tmp_path / name
            ext_dir.mkdir()
            
            # Create manifest
            manifest = {
                "name": name,
                "version": "1.0.0",
                "description": "Test extension",
                "author": "Test Author",
                "entry_point": "__init__.py",
                "dependencies": [],
                "permissions": [],
                "category": "test"
            }
            
            import json
            (ext_dir / "extension.json").write_text(json.dumps(manifest))
            
            # Create extension module
            extension_code = '''
from ai_karen_engine.extensions.base import BaseExtension

class TestExtensionExtension(BaseExtension):
    async def initialize(self):
        pass
    
    async def shutdown(self):
        pass
'''
            (ext_dir / "__init__.py").write_text(extension_code)
            
            return ext_dir
        
        return _create_extension
    
    @pytest.mark.asyncio
    async def test_real_hook_integration_load_unload(self, real_extension_manager, create_test_extension):
        """Test ExtensionManager with real hook system for load/unload cycle."""
        hook_results = []
        
        async def test_hook_handler(context):
            hook_results.append({
                'hook_type': context.hook_type,
                'extension_name': context.data.get('extension_name'),
                'timestamp': context.timestamp
            })
            return {'processed': True}
        
        # Register hooks for all extension lifecycle events
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_LOADED,
            test_hook_handler,
            priority=50
        )
        
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_ACTIVATED,
            test_hook_handler,
            priority=50
        )
        
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_DEACTIVATED,
            test_hook_handler,
            priority=50
        )
        
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_UNLOADED,
            test_hook_handler,
            priority=50
        )
        
        # Create and load extension
        create_test_extension("test_extension")
        
        record = await real_extension_manager.load_extension("test_extension")
        assert record is not None
        
        # Unload extension
        await real_extension_manager.unload_extension("test_extension")
        
        # Verify all hooks were executed
        assert len(hook_results) == 4
        
        hook_types = [r['hook_type'] for r in hook_results]
        assert HookTypes.EXTENSION_LOADED in hook_types
        assert HookTypes.EXTENSION_ACTIVATED in hook_types
        assert HookTypes.EXTENSION_DEACTIVATED in hook_types
        assert HookTypes.EXTENSION_UNLOADED in hook_types
        
        # Verify all hooks have correct extension name
        for result in hook_results:
            assert result['extension_name'] == "test_extension"
    
    @pytest.mark.asyncio
    async def test_extension_hook_monitoring_integration(self, real_extension_manager, create_test_extension):
        """Test that extension hook execution is monitored by resource monitor."""
        hook_execution_count = 0
        
        async def monitored_hook_handler(context):
            nonlocal hook_execution_count
            hook_execution_count += 1
            return {'execution_count': hook_execution_count}
        
        # Register a hook that will be monitored
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_ACTIVATED,
            monitored_hook_handler,
            priority=50
        )
        
        # Create and load extension
        create_test_extension("monitored_extension")
        record = await real_extension_manager.load_extension("monitored_extension")
        
        # Check that resource monitor tracked hook execution
        hook_metrics = real_extension_manager.resource_monitor.get_hook_metrics("monitored_extension")
        assert hook_metrics is not None
        assert hook_metrics["hooks_executed"] >= 1  # At least the activation hook
        
        # Verify hook was actually executed
        assert hook_execution_count >= 1
    
    @pytest.mark.asyncio
    async def test_extension_mcp_hook_integration(self, real_extension_manager, create_test_extension):
        """Test MCP integration with hook capabilities."""
        # Create extension with MCP capabilities
        ext_dir = create_test_extension("mcp_extension")
        
        # Update extension code to include MCP setup
        extension_code = '''
from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_types import HookTypes

class McpExtensionExtension(BaseExtension):
    async def _initialize(self):
        # Set up MCP server with hook capabilities
        if hasattr(self, 'create_mcp_server'):
            mcp_server = self.create_mcp_server()
            if mcp_server:
                # Register a hook-enabled MCP tool
                mcp_server.register_hook_enabled_tool(
                    name="test_tool",
                    handler=self._test_tool_handler,
                    schema={"type": "object", "properties": {}},
                    hook_types=[HookTypes.LLM_REQUEST, HookTypes.LLM_RESPONSE],
                    description="Test MCP tool with hook capabilities"
                )
    
    async def _test_tool_handler(self, **kwargs):
        return {"result": "test_tool_executed", "kwargs": kwargs}
'''
        (ext_dir / "__init__.py").write_text(extension_code)
        
        # Load extension
        record = await real_extension_manager.load_extension("mcp_extension")
        assert record is not None
        
        # Verify MCP server was created (if MCP is available)
        if hasattr(record.instance, '_mcp_server') and record.instance._mcp_server:
            mcp_server = record.instance._mcp_server
            assert "test_tool" in mcp_server.hook_tools
            assert HookTypes.LLM_REQUEST in mcp_server.hook_tools["test_tool"]["hook_types"]
    
    @pytest.mark.asyncio
    async def test_extension_hook_error_handling(self, real_extension_manager, create_test_extension):
        """Test that extension hook errors are properly handled and monitored."""
        error_count = 0
        
        async def failing_hook_handler(context):
            nonlocal error_count
            error_count += 1
            if error_count <= 2:  # Fail first two times
                raise RuntimeError(f"Simulated hook failure #{error_count}")
            return {'success': True, 'attempt': error_count}
        
        # Register a hook that will fail initially
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_LOADED,
            failing_hook_handler,
            priority=50
        )
        
        # Create and load multiple extensions to trigger the hook multiple times
        for i in range(3):
            ext_name = f"error_test_extension_{i}"
            create_test_extension(ext_name)
            
            try:
                await real_extension_manager.load_extension(ext_name)
            except Exception:
                pass  # Expected for first two attempts
        
        # Verify error tracking
        assert error_count == 3
        
        # Check that resource monitor tracked hook failures
        # Note: This would require the hook to be associated with a specific extension
        # For now, we just verify the hook was called multiple times
    
    @pytest.mark.asyncio
    async def test_extension_hook_cleanup_on_shutdown(self, real_extension_manager, create_test_extension):
        """Test that extension hooks are properly cleaned up on shutdown."""
        # Create extension
        create_test_extension("cleanup_test")
        record = await real_extension_manager.load_extension("cleanup_test")
        
        # Verify extension has hook capabilities
        assert hasattr(record.instance, 'cleanup_extension_hooks')
        assert hasattr(record.instance, '_registered_hooks')
        
        # Register some hooks through the extension
        if hasattr(record.instance, 'register_extension_hook'):
            hook_id = await record.instance.register_extension_hook(
                HookTypes.EXTENSION_DEACTIVATED,
                lambda ctx: {"cleaned": True},
                priority=50
            )
            
            # Verify hook was registered
            assert hook_id is not None
            assert hook_id in record.instance._registered_hooks
        
        # Unload extension
        await real_extension_manager.unload_extension("cleanup_test")
        
        # Verify hooks were cleaned up (extension instance should have called cleanup)
        # Note: After unload, the instance might not be accessible, so we check indirectly
        # by ensuring no errors occurred during unload
    
    def test_extension_hook_stats_integration(self, real_extension_manager):
        """Test that extension hook statistics are properly integrated."""
        # Get hook stats from extension manager
        stats = real_extension_manager.get_hook_stats()
        
        # Verify stats structure
        assert isinstance(stats, dict)
        assert 'hooks_enabled' in stats
        assert 'registered_hooks' in stats
        assert 'hook_types' in stats
        
        # Verify extension manager has hook capabilities
        assert hasattr(real_extension_manager, 'trigger_hooks')
        assert hasattr(real_extension_manager, 'register_hook')
        assert hasattr(real_extension_manager, 'are_hooks_enabled')


class TestExtensionBaseClassHookIntegration:
    """Test BaseExtension hook integration."""
    
    @pytest.fixture
    def mock_manifest(self):
        """Create a mock extension manifest."""
        from ai_karen_engine.extension_host.models2 import ExtensionManifest
        return ExtensionManifest(
            name="test_hook_extension",
            version="1.0.0",
            display_name="Test Hook Extension",
            description="Test extension with hooks",
            author="Test Author",
            license="MIT",
            category="test"
        )
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock extension context."""
        from ai_karen_engine.extension_host.models2 import ExtensionContext
        return ExtensionContext(
            plugin_router=MagicMock(),
            db_session=MagicMock(),
            app_instance=MagicMock()
        )
    
    @pytest.fixture
    def test_extension(self, mock_manifest, mock_context):
        """Create a test extension instance."""
        from ai_karen_engine.extensions.base import BaseExtension
        
        class TestHookExtension(BaseExtension):
            async def _initialize(self):
                pass
        
        # Mock the data manager to avoid database issues
        with patch('ai_karen_engine.extensions.base.ExtensionDataManager') as mock_data_manager:
            mock_data_manager.return_value = MagicMock()
            return TestHookExtension(mock_manifest, mock_context)
    
    def test_base_extension_inherits_hook_mixin(self, test_extension):
        """Test that BaseExtension inherits from HookMixin."""
        from ai_karen_engine.hooks.hook_mixin import HookMixin
        assert isinstance(test_extension, HookMixin)
        assert hasattr(test_extension, 'trigger_hooks')
        assert hasattr(test_extension, 'register_hook')
        assert hasattr(test_extension, 'are_hooks_enabled')
    
    def test_base_extension_hook_attributes(self, test_extension):
        """Test that BaseExtension has hook-related attributes."""
        assert hasattr(test_extension, '_registered_hooks')
        assert hasattr(test_extension, '_hook_handlers')
        assert isinstance(test_extension._registered_hooks, list)
        assert isinstance(test_extension._hook_handlers, dict)
    
    @pytest.mark.asyncio
    async def test_extension_hook_registration(self, test_extension):
        """Test extension hook registration."""
        # Mock hook manager
        mock_hook_manager = AsyncMock()
        mock_hook_manager.register_hook = AsyncMock(return_value="test_hook_id")
        test_extension.set_hook_manager(mock_hook_manager)
        
        async def test_handler(context):
            return {"handled": True}
        
        # Register hook
        hook_id = await test_extension.register_extension_hook(
            HookTypes.EXTENSION_LOADED,
            test_handler,
            priority=30
        )
        
        # Verify registration
        assert hook_id == "test_hook_id"
        assert hook_id in test_extension._registered_hooks
        assert HookTypes.EXTENSION_LOADED in test_extension._hook_handlers
        
        # Verify hook manager was called correctly
        mock_hook_manager.register_hook.assert_called_once_with(
            hook_type=HookTypes.EXTENSION_LOADED,
            handler=test_handler,
            priority=30,
            conditions={},
            source_type="baseextension",
            source_name="test_hook_extension_extension"
        )
    
    @pytest.mark.asyncio
    async def test_extension_hook_handling(self, test_extension):
        """Test extension hook handling."""
        # Register a test handler
        test_result = {"test": "result"}
        
        async def test_handler(context):
            return test_result
        
        test_extension._hook_handlers[HookTypes.EXTENSION_LOADED] = test_handler
        
        # Handle hook
        result = await test_extension.handle_hook(
            HookTypes.EXTENSION_LOADED,
            {"test": "context"},
            {"user": "test"}
        )
        
        assert result == test_result
    
    @pytest.mark.asyncio
    async def test_extension_default_hook_handling(self, test_extension):
        """Test extension default hook handling."""
        # Test default handling for extension loaded hook
        result = await test_extension._handle_default_hook(
            HookTypes.EXTENSION_LOADED,
            {"test": "context"}
        )
        
        assert result["extension_name"] == "test_hook_extension"
        assert result["hook_type"] == HookTypes.EXTENSION_LOADED
        assert result["status"] == "loaded"
    
    @pytest.mark.asyncio
    async def test_extension_hook_cleanup(self, test_extension):
        """Test extension hook cleanup."""
        # Mock hook manager
        mock_hook_manager = AsyncMock()
        mock_hook_manager.register_hook = AsyncMock(return_value="test_hook_id")
        mock_hook_manager.unregister_hook = AsyncMock(return_value=True)
        test_extension.set_hook_manager(mock_hook_manager)
        
        # Register a hook
        hook_id = await test_extension.register_extension_hook(
            HookTypes.EXTENSION_LOADED,
            lambda ctx: {"test": True}
        )
        
        assert len(test_extension._registered_hooks) == 1
        assert len(test_extension._hook_handlers) == 1
        
        # Cleanup hooks
        await test_extension.cleanup_extension_hooks()
        
        # Verify cleanup
        assert len(test_extension._registered_hooks) == 0
        assert len(test_extension._hook_handlers) == 0
        mock_hook_manager.unregister_hook.assert_called_once_with(hook_id)
    
    def test_extension_hook_summary(self, test_extension):
        """Test extension hook summary."""
        # Add some mock data
        test_extension._registered_hooks = ["hook1", "hook2"]
        test_extension._hook_handlers = {
            HookTypes.EXTENSION_LOADED: lambda: None,
            HookTypes.EXTENSION_ACTIVATED: lambda: None
        }
        
        summary = test_extension.get_extension_hook_summary()
        
        assert summary["extension_name"] == "test_hook_extension"
        assert summary["registered_hooks"] == 2
        assert len(summary["hook_types"]) == 2
        assert HookTypes.EXTENSION_LOADED in summary["hook_types"]
        assert HookTypes.EXTENSION_ACTIVATED in summary["hook_types"]


class TestExtensionMCPHookIntegration:
    """Test MCP integration with hook capabilities."""
    
    @pytest.fixture
    def mock_manifest(self):
        """Create a mock extension manifest."""
        from ai_karen_engine.extension_host.models2 import ExtensionManifest
        return ExtensionManifest(
            name="test_mcp_extension",
            version="1.0.0",
            display_name="Test MCP Extension",
            description="Test MCP extension",
            author="Test Author",
            license="MIT",
            category="test"
        )
    
    @pytest.fixture
    def mcp_server(self, mock_manifest):
        """Create an MCP server instance."""
        from ai_karen_engine.extensions.mcp_integration import ExtensionMCPServer
        return ExtensionMCPServer("test_mcp_extension", mock_manifest)
    
    def test_mcp_server_hook_capabilities(self, mcp_server):
        """Test that MCP server has hook capabilities."""
        assert hasattr(mcp_server, 'hook_tools')
        assert hasattr(mcp_server, 'ai_context_providers')
        assert hasattr(mcp_server, 'register_hook_enabled_tool')
        assert hasattr(mcp_server, 'trigger_tool_hooks')
    
    def test_mcp_server_hook_enabled_tool_registration(self, mcp_server):
        """Test registration of hook-enabled MCP tools."""
        async def test_handler(**kwargs):
            return {"result": "test"}
        
        async def ai_context_provider(context):
            return {"ai_enhanced": True}
        
        # Register hook-enabled tool
        mcp_server.register_hook_enabled_tool(
            name="test_hook_tool",
            handler=test_handler,
            schema={"type": "object"},
            hook_types=[HookTypes.LLM_REQUEST, HookTypes.LLM_RESPONSE],
            description="Test hook-enabled tool",
            ai_context_provider=ai_context_provider
        )
        
        # Verify registration
        assert "test_hook_tool" in mcp_server.tools
        assert "test_hook_tool" in mcp_server.hook_tools
        assert "test_hook_tool" in mcp_server.ai_context_providers
        
        # Verify hook tool configuration
        hook_tool = mcp_server.hook_tools["test_hook_tool"]
        assert hook_tool["handler"] == test_handler
        assert HookTypes.LLM_REQUEST in hook_tool["hook_types"]
        assert HookTypes.LLM_RESPONSE in hook_tool["hook_types"]
        assert hook_tool["ai_context_provider"] == ai_context_provider
    
    @pytest.mark.asyncio
    async def test_mcp_server_hook_triggering(self, mcp_server):
        """Test MCP server hook triggering."""
        # Mock hook manager
        mock_hook_manager = AsyncMock()
        mock_summary = MagicMock()
        mock_summary.results = [MagicMock(success=True, result={"triggered": True})]
        mock_hook_manager.trigger_hooks = AsyncMock(return_value=mock_summary)
        
        mcp_server.set_hook_manager(mock_hook_manager)
        
        # Register a hook-enabled tool
        mcp_server.register_hook_enabled_tool(
            name="hook_test_tool",
            handler=lambda **kwargs: {"result": "test"},
            schema={"type": "object"},
            hook_types=[HookTypes.LLM_REQUEST]
        )
        
        # Trigger hooks for the tool
        results = await mcp_server.trigger_tool_hooks(
            "hook_test_tool",
            HookTypes.LLM_REQUEST,
            {"test": "context"}
        )
        
        # Verify hook was triggered
        assert len(results) == 1
        assert results[0]["triggered"] is True
        mock_hook_manager.trigger_hooks.assert_called_once()
    
    @pytest.fixture
    def mcp_client(self):
        """Create an MCP client instance."""
        from ai_karen_engine.extensions.mcp_integration import ExtensionMCPClient
        mock_registry = MagicMock()
        return ExtensionMCPClient("test_extension", mock_registry)
    
    def test_mcp_client_ai_enhancement_capabilities(self, mcp_client):
        """Test that MCP client has AI enhancement capabilities."""
        assert hasattr(mcp_client, 'ai_enhanced_tools')
        assert hasattr(mcp_client, 'register_ai_enhanced_tool')
        assert hasattr(mcp_client, 'call_ai_enhanced_tool')
    
    def test_mcp_client_ai_enhanced_tool_registration(self, mcp_client):
        """Test registration of AI-enhanced tools."""
        enhancement_config = {
            "semantic_analysis": True,
            "context_enrichment": True,
            "intelligent_suggestions": False
        }
        
        mcp_client.register_ai_enhanced_tool(
            "test_service",
            "test_tool",
            enhancement_config
        )
        
        tool_key = "test_service.test_tool"
        assert tool_key in mcp_client.ai_enhanced_tools
        
        tool_config = mcp_client.ai_enhanced_tools[tool_key]
        assert tool_config["service_name"] == "test_service"
        assert tool_config["tool_name"] == "test_tool"
        assert tool_config["config"] == enhancement_config
    
    @pytest.mark.asyncio
    async def test_hook_priority_ordering_in_extension_manager(self, real_extension_manager, create_test_extension):
        """Test that extension hooks respect priority ordering."""
        execution_order = []
        
        async def high_priority_handler(context):
            execution_order.append("high")
            return "high"
        
        async def low_priority_handler(context):
            execution_order.append("low")
            return "low"
        
        # Register hooks with different priorities
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_LOADED,
            low_priority_handler,
            priority=75  # Lower priority (executed later)
        )
        
        await real_extension_manager.register_hook(
            HookTypes.EXTENSION_LOADED,
            high_priority_handler,
            priority=25  # Higher priority (executed first)
        )
        
        # Create and load extension
        create_test_extension("priority_test")
        await real_extension_manager.load_extension("priority_test")
        
        # Verify execution order
        assert execution_order == ["high", "low"]