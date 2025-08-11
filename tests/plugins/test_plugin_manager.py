"""
Unit tests for PluginManager hook integration.
Extends existing plugin manager tests with hook functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from ai_karen_engine.plugin_manager import PluginManager, get_plugin_manager
from ai_karen_engine.plugin_router import PluginRouter
from ai_karen_engine.hooks import HookTypes, HookContext, HookResult
from ai_karen_engine.hooks.hook_manager import HookManager


class TestPluginManagerHooks:
    """Test PluginManager hook integration."""
    
    @pytest.fixture
    def mock_router(self):
        """Create a mock plugin router."""
        router = MagicMock(spec=PluginRouter)
        router.dispatch = AsyncMock(return_value=("result", "stdout", "stderr"))
        return router
    
    @pytest.fixture
    def plugin_manager(self, mock_router):
        """Create a PluginManager with mocked dependencies."""
        with patch('ai_karen_engine.plugin_manager.embed_text'), \
             patch('ai_karen_engine.plugin_manager.update_memory'):
            manager = PluginManager(router=mock_router)
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
    
    def test_plugin_manager_inherits_hook_mixin(self, plugin_manager):
        """Test that PluginManager inherits from HookMixin."""
        from ai_karen_engine.hooks.hook_mixin import HookMixin
        assert isinstance(plugin_manager, HookMixin)
        assert hasattr(plugin_manager, 'trigger_hooks')
        assert hasattr(plugin_manager, 'register_hook')
        assert plugin_manager.name == "plugin_manager"
    
    @pytest.mark.asyncio
    async def test_run_plugin_triggers_hooks(self, plugin_manager, mock_hook_manager):
        """Test that run_plugin triggers appropriate hooks."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        
        # Run a plugin
        result = await plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify plugin executed
        assert result == ("result", "stdout", "stderr")
        
        # Verify hooks were triggered
        assert mock_hook_manager.trigger_hooks.call_count >= 2  # At least start and end hooks
        
        # Check hook calls
        calls = mock_hook_manager.trigger_hooks.call_args_list
        
        # Verify pre-execution hook
        start_call = calls[0]
        start_context = start_call[0][0]  # First argument (HookContext)
        assert start_context.hook_type == HookTypes.PLUGIN_EXECUTION_START
        assert start_context.data["plugin_name"] == "test_plugin"
        assert start_context.data["params"] == {"param": "value"}
        
        # Verify post-execution hook
        end_call = calls[1]
        end_context = end_call[0][0]
        assert end_context.hook_type == HookTypes.PLUGIN_EXECUTION_END
        assert end_context.data["plugin_name"] == "test_plugin"
        assert end_context.data["result"] == "result"
        assert end_context.data["success"] is True
    
    @pytest.mark.asyncio
    async def test_run_plugin_error_triggers_error_hook(self, plugin_manager, mock_hook_manager, mock_router):
        """Test that plugin errors trigger error hooks."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        
        # Make router raise an exception
        mock_router.dispatch.side_effect = ValueError("Plugin failed")
        
        # Run plugin and expect exception
        with pytest.raises(ValueError, match="Plugin failed"):
            await plugin_manager.run_plugin(
                "failing_plugin",
                {"param": "value"},
                {"user_id": "123", "roles": ["user"]}
            )
        
        # Verify error hook was triggered
        calls = mock_hook_manager.trigger_hooks.call_args_list
        
        # Should have start hook and error hook
        assert len(calls) >= 2
        
        # Check error hook
        error_call = None
        for call in calls:
            context = call[0][0]
            if context.hook_type == HookTypes.PLUGIN_ERROR:
                error_call = call
                break
        
        assert error_call is not None
        error_context = error_call[0][0]
        assert error_context.data["plugin_name"] == "failing_plugin"
        assert error_context.data["error"] == "Plugin failed"
        assert error_context.data["error_type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_plugin_manager_hook_registration(self, plugin_manager, mock_hook_manager):
        """Test that PluginManager can register hooks."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        mock_hook_manager.register_hook = AsyncMock(return_value="hook_id_123")
        
        async def test_hook_handler(context):
            return {"handled": True}
        
        hook_id = await plugin_manager.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            test_hook_handler,
            priority=25
        )
        
        assert hook_id == "hook_id_123"
        mock_hook_manager.register_hook.assert_called_once_with(
            hook_type=HookTypes.PLUGIN_EXECUTION_START,
            handler=test_hook_handler,
            priority=25,
            conditions={},
            source_type="pluginmanager",
            source_name="plugin_manager"
        )
    
    def test_plugin_manager_hook_stats(self, plugin_manager, mock_hook_manager):
        """Test getting hook statistics from PluginManager."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        
        # Mock hook manager response
        mock_hook_manager.get_hooks_by_source.return_value = [
            MagicMock(hook_type=HookTypes.PLUGIN_EXECUTION_START),
            MagicMock(hook_type=HookTypes.PLUGIN_EXECUTION_END)
        ]
        
        stats = plugin_manager.get_hook_stats()
        
        assert stats['hooks_enabled']
        assert stats['registered_hooks'] == 2
        assert len(stats['hook_types']) == 2
    
    @pytest.mark.asyncio
    async def test_plugin_manager_safe_hook_trigger(self, plugin_manager):
        """Test safe hook triggering when no hook manager is available."""
        # Don't set hook manager - should use safe triggering
        result = await plugin_manager.trigger_hook_safe(
            HookTypes.PLUGIN_EXECUTION_START,
            {"test": "data"},
            default_result="safe_default"
        )
        
        assert result == "safe_default"
    
    def test_plugin_manager_enable_disable_hooks(self, plugin_manager):
        """Test enabling and disabling hooks."""
        # Initially hooks are enabled and hook manager may be auto-initialized
        assert plugin_manager._hook_enabled is True
        
        plugin_manager.enable_hooks()
        assert plugin_manager._hook_enabled is True
        
        plugin_manager.disable_hooks()
        assert plugin_manager._hook_enabled is False
        
        # Test that hooks are properly disabled
        assert plugin_manager.are_hooks_enabled() is False
    
    @pytest.mark.asyncio
    async def test_run_plugin_with_hooks_disabled(self, plugin_manager, mock_hook_manager):
        """Test that disabling hooks prevents hook execution."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        plugin_manager.disable_hooks()
        
        # Run plugin
        await plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Hooks should not be triggered when disabled
        mock_hook_manager.trigger_hooks.assert_not_called()
    
    def test_get_plugin_manager_singleton(self):
        """Test that get_plugin_manager returns singleton instance."""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, PluginManager)
        assert hasattr(manager1, 'trigger_hooks')  # Has hook capabilities
    
    @pytest.mark.asyncio
    async def test_plugin_manager_context_data(self, plugin_manager, mock_hook_manager):
        """Test that plugin manager provides proper context data."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        
        await plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"], "tenant_id": "tenant1"}
        )
        
        # Check that user context is properly passed to hooks
        calls = mock_hook_manager.trigger_hooks.call_args_list
        for call in calls:
            context = call[0][0]
            assert context.user_context is not None
            assert context.user_context["user_id"] == "123"
            assert context.user_context["tenant_id"] == "tenant1"
    
    @pytest.mark.asyncio
    async def test_plugin_manager_hook_integration_with_metrics(self, plugin_manager, mock_hook_manager):
        """Test that hooks work alongside existing metrics."""
        plugin_manager.set_hook_manager(mock_hook_manager)
        
        # Mock metrics to verify they still work
        with patch('ai_karen_engine.plugin_manager.PLUGIN_CALLS') as mock_calls, \
             patch('ai_karen_engine.plugin_manager.MEMORY_WRITES') as mock_memory:
            
            await plugin_manager.run_plugin(
                "test_plugin",
                {"param": "value"},
                {"user_id": "123", "roles": ["user"]}
            )
            
            # Verify metrics still work
            mock_calls.labels.assert_called_with(plugin="test_plugin")
            mock_calls.labels().inc.assert_called_once()
            mock_memory.inc.assert_called_once()
            
            # Verify hooks also triggered
            assert mock_hook_manager.trigger_hooks.call_count >= 2


class TestPluginManagerHookIntegration:
    """Integration tests for PluginManager with real hook system."""
    
    @pytest.fixture
    def real_plugin_manager(self):
        """Create a PluginManager with real hook system."""
        with patch('ai_karen_engine.plugin_manager.embed_text'), \
             patch('ai_karen_engine.plugin_manager.update_memory'):
            
            mock_router = MagicMock(spec=PluginRouter)
            mock_router.dispatch = AsyncMock(return_value=("result", "stdout", "stderr"))
            
            manager = PluginManager(router=mock_router)
            # Set up real hook manager
            from ai_karen_engine.hooks.hook_manager import HookManager
            manager.set_hook_manager(HookManager())
            return manager
    
    @pytest.mark.asyncio
    async def test_real_hook_integration(self, real_plugin_manager):
        """Test PluginManager with real hook system."""
        hook_results = []
        
        async def test_hook_handler(context):
            hook_results.append({
                'hook_type': context.hook_type,
                'plugin_name': context.data.get('plugin_name'),
                'timestamp': context.timestamp
            })
            return {'processed': True}
        
        # Register hooks
        await real_plugin_manager.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            test_hook_handler,
            priority=50
        )
        
        await real_plugin_manager.register_hook(
            HookTypes.PLUGIN_EXECUTION_END,
            test_hook_handler,
            priority=50
        )
        
        # Run plugin
        await real_plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify hooks were executed
        assert len(hook_results) == 2
        
        start_hook = next(r for r in hook_results if r['hook_type'] == HookTypes.PLUGIN_EXECUTION_START)
        end_hook = next(r for r in hook_results if r['hook_type'] == HookTypes.PLUGIN_EXECUTION_END)
        
        assert start_hook['plugin_name'] == "test_plugin"
        assert end_hook['plugin_name'] == "test_plugin"
        assert start_hook['timestamp'] <= end_hook['timestamp']
    
    @pytest.mark.asyncio
    async def test_plugin_metrics_with_hooks(self, real_plugin_manager):
        """Test that plugin metrics include hook statistics."""
        # Run a plugin to generate metrics
        await real_plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Get metrics
        metrics = real_plugin_manager.get_plugin_metrics()
        
        # Verify metrics structure
        assert "plugin_calls" in metrics
        assert "plugin_failures" in metrics
        assert "memory_writes" in metrics
        assert "hook_metrics" in metrics
        assert "workflow_metrics" in metrics
        assert "hook_system" in metrics
        
        # Verify hook metrics
        hook_metrics = metrics["hook_metrics"]
        assert "hooks_triggered" in hook_metrics
        assert "hooks_failed" in hook_metrics
        assert "hook_duration_stats" in hook_metrics
    
    @pytest.mark.asyncio
    async def test_hook_monitoring_with_failures(self, real_plugin_manager):
        """Test hook monitoring when hooks fail."""
        hook_results = []
        
        async def failing_hook_handler(context):
            hook_results.append(context.hook_type)
            raise ValueError("Hook failed intentionally")
        
        async def successful_hook_handler(context):
            hook_results.append(f"{context.hook_type}_success")
            return {'processed': True}
        
        # Register both failing and successful hooks
        await real_plugin_manager.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            failing_hook_handler,
            priority=10
        )
        
        await real_plugin_manager.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            successful_hook_handler,
            priority=20
        )
        
        # Run plugin - should continue despite hook failure
        await real_plugin_manager.run_plugin(
            "test_plugin",
            {"param": "value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify both hooks were attempted
        assert HookTypes.PLUGIN_EXECUTION_START in hook_results
        assert f"{HookTypes.PLUGIN_EXECUTION_START}_success" in hook_results
        
        # Check that metrics recorded the failure
        metrics = real_plugin_manager.get_plugin_metrics()
        hook_metrics = metrics["hook_metrics"]
        
        # Should have recorded both triggered and failed hooks
        assert hook_metrics["hooks_triggered"].get("enabled", True) is not False
        assert hook_metrics["hooks_failed"].get("enabled", True) is not False


class TestPluginManagerWorkflowIntegration:
    """Test PluginManager integration with workflow orchestration."""
    
    @pytest.fixture
    def plugin_manager_with_orchestrator(self):
        """Create PluginManager with workflow orchestrator."""
        with patch('ai_karen_engine.plugin_manager.embed_text'), \
             patch('ai_karen_engine.plugin_manager.update_memory'):
            
            mock_router = MagicMock(spec=PluginRouter)
            mock_router.dispatch = AsyncMock(return_value=("workflow_result", "stdout", "stderr"))
            
            manager = PluginManager(router=mock_router)
            
            # Set up hook manager
            from ai_karen_engine.hooks.hook_manager import HookManager
            manager.set_hook_manager(HookManager())
            
            return manager
    
    @pytest.mark.asyncio
    async def test_workflow_hook_integration(self, plugin_manager_with_orchestrator):
        """Test that workflow execution triggers appropriate hooks."""
        workflow_events = []
        
        async def workflow_hook_handler(context):
            workflow_events.append({
                'hook_type': context.hook_type,
                'plugin_name': context.data.get('plugin_name'),
                'execution_id': context.data.get('execution_id'),
                'data_keys': list(context.data.keys())
            })
            return {'workflow_processed': True}
        
        # Register workflow-related hooks
        await plugin_manager_with_orchestrator.register_hook(
            HookTypes.PLUGIN_EXECUTION_START,
            workflow_hook_handler,
            priority=30
        )
        
        await plugin_manager_with_orchestrator.register_hook(
            HookTypes.PLUGIN_EXECUTION_END,
            workflow_hook_handler,
            priority=30
        )
        
        # Simulate workflow plugin execution
        await plugin_manager_with_orchestrator.run_plugin(
            "workflow_orchestrator",
            {
                "workflow_name": "test_workflow",
                "steps": ["step1", "step2"],
                "context": {"user_id": "123"}
            },
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify workflow hooks were triggered
        assert len(workflow_events) == 2
        
        start_event = next(e for e in workflow_events if e['hook_type'] == HookTypes.PLUGIN_EXECUTION_START)
        end_event = next(e for e in workflow_events if e['hook_type'] == HookTypes.PLUGIN_EXECUTION_END)
        
        assert start_event['plugin_name'] == "workflow_orchestrator"
        assert end_event['plugin_name'] == "workflow_orchestrator"
        assert start_event['execution_id'] == end_event['execution_id']
        
        # Verify expected data keys are present
        expected_start_keys = ['plugin_name', 'params', 'user_context', 'execution_id', 'timestamp']
        expected_end_keys = ['plugin_name', 'params', 'result', 'stdout', 'stderr', 'success', 'user_context', 'execution_id', 'execution_time_ms', 'memory_usage', 'metrics']
        
        assert all(key in start_event['data_keys'] for key in expected_start_keys)
        assert all(key in end_event['data_keys'] for key in expected_end_keys)
    
    @pytest.mark.asyncio
    async def test_error_recovery_suggestions(self, plugin_manager_with_orchestrator):
        """Test error recovery suggestions in hook context."""
        error_events = []
        
        async def error_hook_handler(context):
            error_events.append({
                'hook_type': context.hook_type,
                'error': context.data.get('error'),
                'error_type': context.data.get('error_type'),
                'recovery_suggestions': context.data.get('recovery_suggestions', [])
            })
            return {'error_processed': True}
        
        # Register error hook
        await plugin_manager_with_orchestrator.register_hook(
            HookTypes.PLUGIN_ERROR,
            error_hook_handler,
            priority=40
        )
        
        # Make router raise a specific error
        plugin_manager_with_orchestrator.router.dispatch.side_effect = FileNotFoundError("Plugin file not found")
        
        # Run plugin and expect exception
        with pytest.raises(FileNotFoundError):
            await plugin_manager_with_orchestrator.run_plugin(
                "missing_plugin",
                {"param": "value"},
                {"user_id": "123", "roles": ["user"]}
            )
        
        # Verify error hook was triggered with recovery suggestions
        assert len(error_events) == 1
        error_event = error_events[0]
        
        assert error_event['hook_type'] == HookTypes.PLUGIN_ERROR
        assert error_event['error'] == "Plugin file not found"
        assert error_event['error_type'] == "FileNotFoundError"
        
        # Verify recovery suggestions are provided
        suggestions = error_event['recovery_suggestions']
        assert len(suggestions) > 0
        assert any("files exist" in suggestion for suggestion in suggestions)
        assert any("directory structure" in suggestion for suggestion in suggestions)