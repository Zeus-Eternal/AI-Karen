"""
Unit tests for PluginOrchestrator hook integration.
Tests the workflow orchestration system with hook capabilities.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
from datetime import datetime

from ai_karen_engine.plugin_orchestrator import (
    PluginOrchestrator, WorkflowStep, WorkflowDefinition, WorkflowExecution,
    get_plugin_orchestrator
)
from ai_karen_engine.hooks import HookTypes, HookContext, HookResult
from ai_karen_engine.hooks.hook_manager import HookManager


class TestPluginOrchestratorHooks:
    """Test PluginOrchestrator hook integration."""
    
    @pytest.fixture
    def mock_plugin_manager(self):
        """Create a mock plugin manager."""
        manager = AsyncMock()
        manager.run_plugin = AsyncMock(return_value=("plugin_result", "stdout", "stderr"))
        return manager
    
    @pytest.fixture
    def orchestrator(self, mock_plugin_manager):
        """Create a PluginOrchestrator with mocked dependencies."""
        with patch('ai_karen_engine.plugin_orchestrator.get_plugin_manager', return_value=mock_plugin_manager), \
             patch('ai_karen_engine.plugin_orchestrator.get_plugin_router'):
            orchestrator = PluginOrchestrator()
            return orchestrator
    
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
    def sample_workflow(self):
        """Create a sample workflow definition."""
        steps = [
            WorkflowStep(
                plugin_intent="step1_plugin",
                params={"param1": "value1"},
                max_retries=2
            ),
            WorkflowStep(
                plugin_intent="step2_plugin",
                params={"param2": "value2"},
                depends_on=["step1_plugin"]
            )
        ]
        
        return WorkflowDefinition(
            name="test_workflow",
            description="Test workflow for hook integration",
            steps=steps
        )
    
    def test_orchestrator_inherits_hook_mixin(self, orchestrator):
        """Test that PluginOrchestrator inherits from HookMixin."""
        from ai_karen_engine.hooks.hook_mixin import HookMixin
        assert isinstance(orchestrator, HookMixin)
        assert hasattr(orchestrator, 'trigger_hooks')
        assert hasattr(orchestrator, 'register_hook')
        assert orchestrator.name == "plugin_orchestrator"
    
    @pytest.mark.asyncio
    async def test_workflow_registration_triggers_hooks(self, orchestrator, mock_hook_manager, sample_workflow):
        """Test that workflow registration triggers appropriate hooks."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Register workflow
        success = await orchestrator.register_workflow(sample_workflow)
        
        assert success is True
        assert sample_workflow.name in orchestrator.workflows
        
        # Verify hook was triggered
        mock_hook_manager.trigger_hooks.assert_called()
        
        # Check the hook call
        call_args = mock_hook_manager.trigger_hooks.call_args_list[-1]
        context = call_args[0][0]
        
        assert context.hook_type == "workflow_registered"
        assert context.data["workflow_name"] == "test_workflow"
        assert context.data["step_count"] == 2
        assert context.data["has_parallel_steps"] is False
    
    @pytest.mark.asyncio
    async def test_workflow_execution_lifecycle_hooks(self, orchestrator, mock_hook_manager, sample_workflow):
        """Test that workflow execution triggers lifecycle hooks."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Register workflow first
        await orchestrator.register_workflow(sample_workflow)
        
        # Execute workflow
        execution = await orchestrator.execute_workflow(
            "test_workflow",
            {"context_param": "context_value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        assert execution.status == "completed"
        
        # Verify lifecycle hooks were triggered
        hook_calls = mock_hook_manager.trigger_hooks.call_args_list
        
        # Find workflow lifecycle hooks
        workflow_started = None
        workflow_completed = None
        
        for call in hook_calls:
            context = call[0][0]
            if context.hook_type == "workflow_started":
                workflow_started = context
            elif context.hook_type == "workflow_completed":
                workflow_completed = context
        
        # Verify workflow started hook
        assert workflow_started is not None
        assert workflow_started.data["workflow_name"] == "test_workflow"
        assert workflow_started.data["step_count"] == 2
        
        # Verify workflow completed hook
        assert workflow_completed is not None
        assert workflow_completed.data["workflow_name"] == "test_workflow"
        assert "execution_time_ms" in workflow_completed.data
    
    @pytest.mark.asyncio
    async def test_workflow_step_hooks(self, orchestrator, mock_hook_manager, sample_workflow):
        """Test that individual workflow steps trigger hooks."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Register workflow
        await orchestrator.register_workflow(sample_workflow)
        
        # Execute workflow
        await orchestrator.execute_workflow(
            "test_workflow",
            {"context_param": "context_value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify step hooks were triggered
        hook_calls = mock_hook_manager.trigger_hooks.call_args_list
        
        step_started_calls = []
        step_completed_calls = []
        
        for call in hook_calls:
            context = call[0][0]
            if context.hook_type == "workflow_step_started":
                step_started_calls.append(context)
            elif context.hook_type == "workflow_step_completed":
                step_completed_calls.append(context)
        
        # Should have step hooks for each step
        assert len(step_started_calls) >= 2  # At least 2 steps
        assert len(step_completed_calls) >= 2
        
        # Verify step data
        for step_context in step_started_calls:
            assert "execution_id" in step_context.data
            assert "workflow_name" in step_context.data
            assert step_context.data["workflow_name"] == "test_workflow"
    
    @pytest.mark.asyncio
    async def test_workflow_failure_hooks(self, orchestrator, mock_hook_manager, sample_workflow):
        """Test that workflow failures trigger error hooks."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Make plugin manager fail
        orchestrator.plugin_manager.run_plugin.side_effect = ValueError("Plugin execution failed")
        
        # Register workflow
        await orchestrator.register_workflow(sample_workflow)
        
        # Execute workflow and expect failure
        with pytest.raises(ValueError):
            await orchestrator.execute_workflow(
                "test_workflow",
                {"context_param": "context_value"},
                {"user_id": "123", "roles": ["user"]}
            )
        
        # Verify failure hook was triggered
        hook_calls = mock_hook_manager.trigger_hooks.call_args_list
        
        workflow_failed = None
        for call in hook_calls:
            context = call[0][0]
            if context.hook_type == "workflow_failed":
                workflow_failed = context
                break
        
        assert workflow_failed is not None
        assert workflow_failed.data["workflow_name"] == "test_workflow"
        assert workflow_failed.data["error"] == "Plugin execution failed"
        assert workflow_failed.data["error_type"] == "ValueError"
    
    @pytest.mark.asyncio
    async def test_parallel_workflow_hooks(self, orchestrator, mock_hook_manager):
        """Test hooks for parallel workflow execution."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Create workflow with parallel steps
        parallel_steps = [
            WorkflowStep(
                plugin_intent="parallel_step1",
                params={"param1": "value1"},
                parallel=True
            ),
            WorkflowStep(
                plugin_intent="parallel_step2",
                params={"param2": "value2"},
                parallel=True
            )
        ]
        
        parallel_workflow = WorkflowDefinition(
            name="parallel_workflow",
            description="Parallel workflow test",
            steps=parallel_steps
        )
        
        # Register and execute workflow
        await orchestrator.register_workflow(parallel_workflow)
        await orchestrator.execute_workflow(
            "parallel_workflow",
            {"context_param": "context_value"},
            {"user_id": "123", "roles": ["user"]}
        )
        
        # Verify registration hook indicated parallel steps
        registration_calls = [
            call for call in mock_hook_manager.trigger_hooks.call_args_list
            if call[0][0].hook_type == "workflow_registered"
        ]
        
        assert len(registration_calls) > 0
        registration_context = registration_calls[-1][0][0]
        assert registration_context.data["has_parallel_steps"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation_hooks(self, orchestrator, mock_hook_manager, sample_workflow):
        """Test hooks for workflow cancellation."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        # Register workflow
        await orchestrator.register_workflow(sample_workflow)
        
        # Start workflow execution (simulate by creating execution record)
        execution = WorkflowExecution(
            workflow_name="test_workflow",
            execution_id="test_exec_123",
            status="running"
        )
        orchestrator.executions["test_exec_123"] = execution
        
        # Cancel workflow
        success = await orchestrator.cancel_workflow("test_exec_123")
        
        assert success is True
        assert execution.status == "cancelled"
        
        # Verify cancellation hook was triggered
        hook_calls = mock_hook_manager.trigger_hooks.call_args_list
        
        cancellation_hook = None
        for call in hook_calls:
            context = call[0][0]
            if context.hook_type == "workflow_cancelled":
                cancellation_hook = context
                break
        
        assert cancellation_hook is not None
        assert cancellation_hook.data["execution_id"] == "test_exec_123"
        assert cancellation_hook.data["workflow_name"] == "test_workflow"
    
    @pytest.mark.asyncio
    async def test_custom_workflow_hooks(self, orchestrator, mock_hook_manager):
        """Test registration and execution of custom workflow hooks."""
        orchestrator.set_hook_manager(mock_hook_manager)
        
        custom_hook_results = []
        
        async def custom_workflow_hook(context):
            custom_hook_results.append({
                'hook_type': context.hook_type,
                'workflow_name': context.data.get('workflow_name'),
                'custom_data': context.data.get('custom_data')
            })
            return {'custom_processed': True}
        
        # Register custom hook
        await orchestrator.register_hook(
            "custom_workflow_event",
            custom_workflow_hook,
            priority=25
        )
        
        # Trigger custom hook
        await orchestrator.trigger_hook_safe(
            "custom_workflow_event",
            {
                "workflow_name": "custom_workflow",
                "custom_data": "test_data"
            }
        )
        
        # Verify custom hook was executed
        assert len(custom_hook_results) == 1
        result = custom_hook_results[0]
        assert result['hook_type'] == "custom_workflow_event"
        assert result['workflow_name'] == "custom_workflow"
        assert result['custom_data'] == "test_data"
    
    def test_get_orchestrator_singleton(self):
        """Test that get_plugin_orchestrator returns singleton instance."""
        orchestrator1 = get_plugin_orchestrator()
        orchestrator2 = get_plugin_orchestrator()
        
        assert orchestrator1 is orchestrator2
        assert isinstance(orchestrator1, PluginOrchestrator)
        assert hasattr(orchestrator1, 'trigger_hooks')  # Has hook capabilities


class TestPluginOrchestratorWorkflowIntegration:
    """Integration tests for PluginOrchestrator with real hook system."""
    
    @pytest.fixture
    def real_orchestrator(self):
        """Create a PluginOrchestrator with real hook system."""
        with patch('ai_karen_engine.plugin_orchestrator.get_plugin_manager') as mock_pm, \
             patch('ai_karen_engine.plugin_orchestrator.get_plugin_router'):
            
            # Mock plugin manager
            mock_plugin_manager = AsyncMock()
            mock_plugin_manager.run_plugin = AsyncMock(return_value=("result", "stdout", "stderr"))
            mock_pm.return_value = mock_plugin_manager
            
            orchestrator = PluginOrchestrator()
            
            # Set up real hook manager
            orchestrator.set_hook_manager(HookManager())
            
            return orchestrator
    
    @pytest.mark.asyncio
    async def test_real_workflow_execution_with_hooks(self, real_orchestrator):
        """Test complete workflow execution with real hook system."""
        workflow_events = []
        
        async def workflow_event_handler(context):
            workflow_events.append({
                'event': context.hook_type,
                'workflow_name': context.data.get('workflow_name'),
                'execution_id': context.data.get('execution_id'),
                'timestamp': context.timestamp
            })
            return {'event_processed': True}
        
        # Register hooks for all workflow events
        hook_types = [
            "workflow_started",
            "workflow_completed", 
            "workflow_step_started",
            "workflow_step_completed"
        ]
        
        for hook_type in hook_types:
            await real_orchestrator.register_hook(
                hook_type,
                workflow_event_handler,
                priority=50
            )
        
        # Create and register workflow
        steps = [
            WorkflowStep(
                plugin_intent="test_plugin1",
                params={"param": "value1"}
            ),
            WorkflowStep(
                plugin_intent="test_plugin2", 
                params={"param": "value2"},
                depends_on=["test_plugin1"]
            )
        ]
        
        workflow = WorkflowDefinition(
            name="integration_test_workflow",
            description="Integration test workflow",
            steps=steps
        )
        
        await real_orchestrator.register_workflow(workflow)
        
        # Execute workflow
        execution = await real_orchestrator.execute_workflow(
            "integration_test_workflow",
            {"test_context": "integration"},
            {"user_id": "integration_user", "roles": ["user"]}
        )
        
        assert execution.status == "completed"
        
        # Verify all expected events were captured
        event_types = [event['event'] for event in workflow_events]
        
        assert "workflow_started" in event_types
        assert "workflow_completed" in event_types
        assert "workflow_step_started" in event_types
        assert "workflow_step_completed" in event_types
        
        # Verify event ordering (started before completed)
        started_event = next(e for e in workflow_events if e['event'] == 'workflow_started')
        completed_event = next(e for e in workflow_events if e['event'] == 'workflow_completed')
        
        assert started_event['timestamp'] <= completed_event['timestamp']
        assert started_event['execution_id'] == completed_event['execution_id']
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling_with_hooks(self, real_orchestrator):
        """Test workflow error handling with real hook system."""
        error_events = []
        
        async def error_handler(context):
            error_events.append({
                'event': context.hook_type,
                'error': context.data.get('error'),
                'workflow_name': context.data.get('workflow_name')
            })
            return {'error_handled': True}
        
        # Register error hooks
        await real_orchestrator.register_hook(
            "workflow_failed",
            error_handler,
            priority=60
        )
        
        await real_orchestrator.register_hook(
            "workflow_step_failed",
            error_handler,
            priority=60
        )
        
        # Make plugin manager fail
        real_orchestrator.plugin_manager.run_plugin.side_effect = RuntimeError("Simulated plugin failure")
        
        # Create failing workflow
        failing_workflow = WorkflowDefinition(
            name="failing_workflow",
            description="Workflow that will fail",
            steps=[
                WorkflowStep(
                    plugin_intent="failing_plugin",
                    params={"will": "fail"}
                )
            ]
        )
        
        await real_orchestrator.register_workflow(failing_workflow)
        
        # Execute workflow and expect failure
        with pytest.raises(RuntimeError):
            await real_orchestrator.execute_workflow(
                "failing_workflow",
                {"test": "context"},
                {"user_id": "test_user", "roles": ["user"]}
            )
        
        # Verify error events were captured
        assert len(error_events) > 0
        
        # Check for workflow failure event
        workflow_failures = [e for e in error_events if e['event'] == 'workflow_failed']
        assert len(workflow_failures) > 0
        
        failure_event = workflow_failures[0]
        assert failure_event['workflow_name'] == "failing_workflow"
        assert "Simulated plugin failure" in failure_event['error']
    
    @pytest.mark.asyncio
    async def test_workflow_metrics_integration(self, real_orchestrator):
        """Test that workflow execution integrates with metrics system."""
        # Create simple workflow
        workflow = WorkflowDefinition(
            name="metrics_test_workflow",
            description="Test workflow for metrics",
            steps=[
                WorkflowStep(
                    plugin_intent="metrics_plugin",
                    params={"test": "metrics"}
                )
            ]
        )
        
        await real_orchestrator.register_workflow(workflow)
        
        # Execute workflow
        execution = await real_orchestrator.execute_workflow(
            "metrics_test_workflow",
            {"metrics": "test"},
            {"user_id": "metrics_user", "roles": ["user"]}
        )
        
        assert execution.status == "completed"
        
        # Verify workflow was tracked
        assert execution.workflow_name == "metrics_test_workflow"
        assert execution.started_at is not None
        assert execution.completed_at is not None
        assert execution.completed_at >= execution.started_at
        
        # Verify execution is stored
        stored_execution = await real_orchestrator.get_workflow_status(execution.execution_id)
        assert stored_execution is not None
        assert stored_execution.status == "completed"