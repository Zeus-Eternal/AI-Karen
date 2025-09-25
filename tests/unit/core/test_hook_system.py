"""
Unit tests for the unified hook system.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ai_karen_engine.hooks import (
    HookManager, get_hook_manager, HookMixin, HookTypes,
    HookRegistration, HookContext, HookResult, HookExecutionSummary
)
from ai_karen_engine.hooks.models import HookPriority


class TestHookManager:
    """Test the HookManager class."""
    
    @pytest.fixture
    def hook_manager(self):
        """Create a fresh HookManager instance for each test."""
        return HookManager()
    
    @pytest.fixture
    def sample_handler(self):
        """Create a sample hook handler."""
        async def handler(context: HookContext):
            return {"processed": True, "data": context.data}
        return handler
    
    def test_hook_manager_initialization(self, hook_manager):
        """Test HookManager initializes correctly."""
        assert hook_manager.is_enabled()
        assert len(hook_manager.get_all_hooks()) == 0
        assert len(hook_manager.get_hook_types()) == 0
    
    @pytest.mark.asyncio
    async def test_register_hook(self, hook_manager, sample_handler):
        """Test hook registration."""
        hook_id = await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            sample_handler,
            priority=HookPriority.HIGH.value,
            source_type="test"
        )
        
        assert hook_id is not None
        assert hook_id.startswith("test_pre_message_")
        
        # Verify hook is registered
        hooks = hook_manager.get_hooks_by_type(HookTypes.PRE_MESSAGE)
        assert len(hooks) == 1
        assert hooks[0].id == hook_id
        assert hooks[0].handler == sample_handler
        assert hooks[0].priority == HookPriority.HIGH.value
    
    @pytest.mark.asyncio
    async def test_unregister_hook(self, hook_manager, sample_handler):
        """Test hook unregistration."""
        hook_id = await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            sample_handler,
            source_type="test"
        )
        
        # Verify hook exists
        assert hook_manager.get_hook_by_id(hook_id) is not None
        
        # Unregister hook
        success = await hook_manager.unregister_hook(hook_id)
        assert success
        
        # Verify hook is removed
        assert hook_manager.get_hook_by_id(hook_id) is None
        assert len(hook_manager.get_hooks_by_type(HookTypes.PRE_MESSAGE)) == 0
    
    @pytest.mark.asyncio
    async def test_trigger_hooks(self, hook_manager, sample_handler):
        """Test hook triggering."""
        # Register a hook
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            sample_handler,
            source_type="test"
        )
        
        # Trigger hooks
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={"message": "test message"},
            user_context={"user_id": "123"}
        )
        
        summary = await hook_manager.trigger_hooks(context)
        
        assert summary.hook_type == HookTypes.PRE_MESSAGE
        assert summary.total_hooks == 1
        assert summary.successful_hooks == 1
        assert summary.failed_hooks == 0
        assert len(summary.results) == 1
        assert summary.results[0].success
        assert summary.results[0].result["processed"]
    
    @pytest.mark.asyncio
    async def test_hook_priority_ordering(self, hook_manager):
        """Test that hooks are executed in priority order."""
        execution_order = []
        
        async def high_priority_handler(context):
            execution_order.append("high")
            return "high"
        
        async def low_priority_handler(context):
            execution_order.append("low")
            return "low"
        
        # Register hooks in reverse priority order
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            low_priority_handler,
            priority=HookPriority.LOW.value,
            source_type="test"
        )
        
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            high_priority_handler,
            priority=HookPriority.HIGH.value,
            source_type="test"
        )
        
        # Trigger hooks
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={}
        )
        
        await hook_manager.trigger_hooks(context)
        
        # Verify execution order (high priority first)
        assert execution_order == ["high", "low"]
    
    @pytest.mark.asyncio
    async def test_hook_conditions(self, hook_manager):
        """Test hook condition filtering."""
        async def conditional_handler(context):
            return "executed"
        
        # Register hook with user role condition
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            conditional_handler,
            conditions={"user_roles": ["admin"]},
            source_type="test"
        )
        
        # Test with matching role
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={},
            user_context={"roles": ["admin", "user"]}
        )
        
        summary = await hook_manager.trigger_hooks(context)
        assert summary.successful_hooks == 1
        
        # Test with non-matching role
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={},
            user_context={"roles": ["user"]}
        )
        
        summary = await hook_manager.trigger_hooks(context)
        assert summary.successful_hooks == 0
    
    @pytest.mark.asyncio
    async def test_hook_error_handling(self, hook_manager):
        """Test hook error handling."""
        async def failing_handler(context):
            raise ValueError("Test error")
        
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            failing_handler,
            source_type="test"
        )
        
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={}
        )
        
        summary = await hook_manager.trigger_hooks(context)
        
        assert summary.total_hooks == 1
        assert summary.successful_hooks == 0
        assert summary.failed_hooks == 1
        assert not summary.results[0].success
        assert "Test error" in summary.results[0].error
    
    @pytest.mark.asyncio
    async def test_hook_timeout(self, hook_manager):
        """Test hook timeout handling."""
        async def slow_handler(context):
            await asyncio.sleep(2)  # Longer than timeout
            return "completed"
        
        await hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            slow_handler,
            source_type="test"
        )
        
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={}
        )
        
        summary = await hook_manager.trigger_hooks(context, timeout_seconds=0.1)
        
        assert summary.failed_hooks == 1
        assert "timed out" in summary.results[0].error
    
    def test_get_hooks_by_source(self, hook_manager, sample_handler):
        """Test filtering hooks by source."""
        asyncio.run(hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            sample_handler,
            source_type="plugin",
            source_name="test_plugin"
        ))
        
        asyncio.run(hook_manager.register_hook(
            HookTypes.POST_MESSAGE,
            sample_handler,
            source_type="extension",
            source_name="test_extension"
        ))
        
        plugin_hooks = hook_manager.get_hooks_by_source("plugin")
        assert len(plugin_hooks) == 1
        assert plugin_hooks[0].source_type == "plugin"
        
        extension_hooks = hook_manager.get_hooks_by_source("extension", "test_extension")
        assert len(extension_hooks) == 1
        assert extension_hooks[0].source_name == "test_extension"
    
    def test_hook_manager_disable_enable(self, hook_manager, sample_handler):
        """Test disabling and enabling hook manager."""
        asyncio.run(hook_manager.register_hook(
            HookTypes.PRE_MESSAGE,
            sample_handler,
            source_type="test"
        ))
        
        # Disable hook manager
        hook_manager.disable()
        assert not hook_manager.is_enabled()
        
        context = HookContext(hook_type=HookTypes.PRE_MESSAGE, data={})
        summary = asyncio.run(hook_manager.trigger_hooks(context))
        
        assert summary.total_hooks == 0  # No hooks executed when disabled
        
        # Re-enable hook manager
        hook_manager.enable()
        assert hook_manager.is_enabled()
        
        summary = asyncio.run(hook_manager.trigger_hooks(context))
        assert summary.successful_hooks == 1  # Hook executed when enabled


class TestHookMixin:
    """Test the HookMixin class."""
    
    class TestComponent(HookMixin):
        """Test component that uses HookMixin."""
        def __init__(self, name="test_component"):
            super().__init__()
            self.name = name
    
    @pytest.fixture
    def component(self):
        """Create a test component."""
        return self.TestComponent()
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create a mock hook manager."""
        mock_manager = AsyncMock()
        mock_manager.register_hook = AsyncMock(return_value="test_hook_id")
        mock_manager.unregister_hook = AsyncMock(return_value=True)
        mock_manager.trigger_hooks = AsyncMock(return_value=HookExecutionSummary(
            hook_type="test",
            total_hooks=1,
            successful_hooks=1,
            failed_hooks=0,
            total_execution_time_ms=10.0,
            results=[HookResult.success_result("test_hook", {"result": "success"})]
        ))
        return mock_manager
    
    def test_hook_mixin_initialization(self, component):
        """Test HookMixin initializes correctly."""
        assert component.are_hooks_enabled() is False  # No hook manager initially
        assert component._hook_enabled is True
    
    def test_enable_disable_hooks(self, component):
        """Test enabling and disabling hooks."""
        component.enable_hooks()
        assert component._hook_enabled is True
        
        component.disable_hooks()
        assert component._hook_enabled is False
    
    @pytest.mark.asyncio
    async def test_register_hook(self, component, mock_hook_manager):
        """Test hook registration through mixin."""
        component.set_hook_manager(mock_hook_manager)
        
        async def test_handler(context):
            return "test"
        
        hook_id = await component.register_hook(
            HookTypes.PRE_MESSAGE,
            test_handler,
            priority=50
        )
        
        assert hook_id == "test_hook_id"
        mock_hook_manager.register_hook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_hooks(self, component, mock_hook_manager):
        """Test hook triggering through mixin."""
        component.set_hook_manager(mock_hook_manager)
        
        summary = await component.trigger_hooks(
            HookTypes.PRE_MESSAGE,
            {"test": "data"}
        )
        
        assert summary.successful_hooks == 1
        mock_hook_manager.trigger_hooks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_hook_safe(self, component, mock_hook_manager):
        """Test safe hook triggering."""
        component.set_hook_manager(mock_hook_manager)
        
        result = await component.trigger_hook_safe(
            HookTypes.PRE_MESSAGE,
            {"test": "data"},
            default_result="default"
        )
        
        assert result == [{"result": "success"}]
    
    @pytest.mark.asyncio
    async def test_trigger_hook_safe_with_failure(self, component):
        """Test safe hook triggering with failure."""
        # No hook manager set, should return default
        result = await component.trigger_hook_safe(
            HookTypes.PRE_MESSAGE,
            {"test": "data"},
            default_result="default"
        )
        
        assert result == "default"
    
    def test_get_hook_stats(self, component, mock_hook_manager):
        """Test getting hook statistics."""
        # Without hook manager
        stats = component.get_hook_stats()
        assert not stats['hooks_enabled']
        assert stats['registered_hooks'] == 0
        
        # With hook manager
        component.set_hook_manager(mock_hook_manager)
        mock_hook_manager.get_hooks_by_source.return_value = [
            MagicMock(hook_type=HookTypes.PRE_MESSAGE),
            MagicMock(hook_type=HookTypes.POST_MESSAGE)
        ]
        
        stats = component.get_hook_stats()
        assert stats['hooks_enabled']
        assert stats['registered_hooks'] == 2
        assert len(stats['hook_types']) == 2


class TestHookTypes:
    """Test the HookTypes class."""
    
    def test_get_all_types(self):
        """Test getting all hook types."""
        all_types = HookTypes.get_all_types()
        assert isinstance(all_types, list)
        assert len(all_types) > 0
        assert HookTypes.PRE_MESSAGE in all_types
        assert HookTypes.POST_MESSAGE in all_types
    
    def test_is_valid_type(self):
        """Test hook type validation."""
        assert HookTypes.is_valid_type(HookTypes.PRE_MESSAGE)
        assert HookTypes.is_valid_type(HookTypes.PLUGIN_LOADED)
        assert not HookTypes.is_valid_type("invalid_hook_type")
    
    def test_get_lifecycle_hooks(self):
        """Test getting lifecycle hooks."""
        lifecycle_hooks = HookTypes.get_lifecycle_hooks()
        assert HookTypes.PLUGIN_LOADED in lifecycle_hooks
        assert HookTypes.EXTENSION_ACTIVATED in lifecycle_hooks
        assert HookTypes.SYSTEM_STARTUP in lifecycle_hooks
    
    def test_get_error_hooks(self):
        """Test getting error hooks."""
        error_hooks = HookTypes.get_error_hooks()
        assert HookTypes.PLUGIN_ERROR in error_hooks
        assert HookTypes.EXTENSION_ERROR in error_hooks
        assert HookTypes.SYSTEM_ERROR in error_hooks


class TestHookModels:
    """Test hook data models."""
    
    def test_hook_registration_creation(self):
        """Test HookRegistration creation."""
        def test_handler():
            pass
        
        registration = HookRegistration(
            id="test_id",
            hook_type=HookTypes.PRE_MESSAGE,
            handler=test_handler,
            priority=50,
            conditions={},
            source_type="test"
        )
        
        assert registration.id == "test_id"
        assert registration.hook_type == HookTypes.PRE_MESSAGE
        assert registration.handler == test_handler
        assert registration.enabled
    
    def test_hook_registration_validation(self):
        """Test HookRegistration validation."""
        with pytest.raises(ValueError, match="Handler must be callable"):
            HookRegistration(
                id="test",
                hook_type=HookTypes.PRE_MESSAGE,
                handler="not_callable",
                priority=50,
                conditions={},
                source_type="test"
            )
        
        with pytest.raises(ValueError, match="Priority must be a non-negative integer"):
            HookRegistration(
                id="test",
                hook_type=HookTypes.PRE_MESSAGE,
                handler=lambda: None,
                priority=-1,
                conditions={},
                source_type="test"
            )
    
    def test_hook_context_creation(self):
        """Test HookContext creation."""
        context = HookContext(
            hook_type=HookTypes.PRE_MESSAGE,
            data={"key": "value"},
            user_context={"user_id": "123"}
        )
        
        assert context.hook_type == HookTypes.PRE_MESSAGE
        assert context.get("key") == "value"
        assert context.get("missing", "default") == "default"
        
        context.set("new_key", "new_value")
        assert context.get("new_key") == "new_value"
    
    def test_hook_result_creation(self):
        """Test HookResult creation."""
        success_result = HookResult.success_result("hook_id", {"data": "result"}, 15.5)
        assert success_result.success
        assert success_result.hook_id == "hook_id"
        assert success_result.result == {"data": "result"}
        assert success_result.execution_time_ms == 15.5
        
        error_result = HookResult.error_result("hook_id", "Error message", 10.0)
        assert not error_result.success
        assert error_result.error == "Error message"
        assert error_result.execution_time_ms == 10.0
    
    def test_hook_execution_summary(self):
        """Test HookExecutionSummary."""
        results = [
            HookResult.success_result("hook1", "result1"),
            HookResult.success_result("hook2", "result2"),
            HookResult.error_result("hook3", "error")
        ]
        
        summary = HookExecutionSummary(
            hook_type=HookTypes.PRE_MESSAGE,
            total_hooks=3,
            successful_hooks=2,
            failed_hooks=1,
            total_execution_time_ms=25.0,
            results=results
        )
        
        assert summary.success_rate == 66.66666666666666  # 2/3 * 100
        assert summary.total_hooks == 3
        assert len(summary.results) == 3


def test_get_hook_manager_singleton():
    """Test the global hook manager singleton."""
    manager1 = get_hook_manager()
    manager2 = get_hook_manager()
    
    assert manager1 is manager2  # Same instance
    assert isinstance(manager1, HookManager)