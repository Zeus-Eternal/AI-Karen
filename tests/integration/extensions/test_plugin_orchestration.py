"""
Integration tests for plugin orchestration within extensions.
Tests workflow execution, plugin composition, and data flow.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ai_karen_engine.extensions.orchestrator import (
    PluginOrchestrator,
    PluginStep,
    PluginCall,
    WorkflowResult,
    Condition,
    ConditionOperator,
    StepType,
    WorkflowStep
)
from ai_karen_engine.plugins.router import PluginRouter


class TestPluginOrchestration:
    """Test plugin orchestration functionality."""
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create mock plugin router with test plugins."""
        router = Mock(spec=PluginRouter)
        
        # Mock different plugin responses
        async def mock_dispatch(intent, params, roles):
            if intent == "hello_world":
                return {"message": f"Hello {params.get('name', 'World')}!"}
            elif intent == "time_query":
                return {"time": "2023-01-01 12:00:00"}
            elif intent == "math_add":
                return {"result": params.get("a", 0) + params.get("b", 0)}
            elif intent == "failing_plugin":
                raise RuntimeError("Plugin failed")
            elif intent == "slow_plugin":
                await asyncio.sleep(0.1)
                return {"status": "completed"}
            else:
                return {"status": "unknown_plugin"}
        
        router.dispatch = AsyncMock(side_effect=mock_dispatch)
        return router
    
    @pytest.fixture
    def orchestrator(self, mock_plugin_router):
        """Create plugin orchestrator instance."""
        return PluginOrchestrator(mock_plugin_router)
    
    @pytest.fixture
    def user_context(self):
        """Create user context for testing."""
        return {
            "user_id": "test_user",
            "tenant_id": "test_tenant",
            "roles": ["user"]
        }
    
    # Test Single Plugin Execution
    @pytest.mark.asyncio
    async def test_execute_plugin_success(self, orchestrator, user_context):
        """Test successful single plugin execution."""
        result = await orchestrator.execute_plugin(
            intent="hello_world",
            params={"name": "Alice"},
            user_context=user_context
        )
        
        assert result == {"message": "Hello Alice!"}
    
    @pytest.mark.asyncio
    async def test_execute_plugin_failure(self, orchestrator, user_context):
        """Test plugin execution failure."""
        with pytest.raises(RuntimeError, match="Plugin execution failed"):
            await orchestrator.execute_plugin(
                intent="failing_plugin",
                params={},
                user_context=user_context
            )
    
    @pytest.mark.asyncio
    async def test_execute_plugin_with_roles(self, orchestrator, user_context):
        """Test plugin execution with role-based access."""
        # Verify roles are passed to plugin router
        await orchestrator.execute_plugin(
            intent="hello_world",
            params={},
            user_context=user_context
        )
        
        orchestrator.plugin_router.dispatch.assert_called_with(
            "hello_world", {}, ["user"]
        )
    
    # Test Sequential Workflow Execution
    @pytest.mark.asyncio
    async def test_execute_workflow_simple(self, orchestrator, user_context):
        """Test simple sequential workflow execution."""
        workflow = [
            PluginStep(intent="hello_world", params={"name": "Alice"}),
            PluginStep(intent="time_query", params={})
        ]
        
        result = await orchestrator.execute_workflow(workflow, user_context)
        
        assert result.success is True
        assert len(result.results) == 2
        assert result.results[0] == {"message": "Hello Alice!"}
        assert result.results[1] == {"time": "2023-01-01 12:00:00"}
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_output_keys(self, orchestrator, user_context):
        """Test workflow execution with output keys."""
        workflow = [
            PluginStep(intent="hello_world", params={"name": "Alice"}, output_key="greeting"),
            PluginStep(intent="time_query", params={}, output_key="current_time")
        ]
        
        result = await orchestrator.execute_workflow(workflow, user_context)
        
        assert result.success is True
        assert "greeting" in result.step_results
        assert "current_time" in result.step_results
        assert result.step_results["greeting"] == {"message": "Hello Alice!"}
        assert result.step_results["current_time"] == {"time": "2023-01-01 12:00:00"}
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_parameter_references(self, orchestrator, user_context):
        """Test workflow execution with parameter references between steps."""
        workflow = [
            PluginStep(intent="math_add", params={"a": 5, "b": 3}, output_key="sum"),
            PluginStep(intent="hello_world", params={"name": "${sum.result}"})
        ]
        
        result = await orchestrator.execute_workflow(workflow, user_context)
        
        assert result.success is True
        assert result.results[1] == {"message": "Hello 8!"}
    
    @pytest.mark.asyncio
    async def test_execute_workflow_with_step_failure(self, orchestrator, user_context):
        """Test workflow execution when a step fails."""
        workflow = [
            PluginStep(intent="hello_world", params={"name": "Alice"}),
            PluginStep(intent="failing_plugin", params={}),
            PluginStep(intent="time_query", params={})
        ]
        
        result = await orchestrator.execute_workflow(workflow, user_context)
        
        assert result.success is False
        assert len(result.results) == 3
        assert result.results[0] == {"message": "Hello Alice!"}
        assert result.results[1] is None  # Failed step
        assert result.results[2] == {"time": "2023-01-01 12:00:00"}  # Continues despite failure
        assert len(result.errors) == 1
        assert "failing_plugin" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_execute_workflow_empty(self, orchestrator, user_context):
        """Test execution of empty workflow."""
        result = await orchestrator.execute_workflow([], user_context)
        
        assert result.success is True
        assert result.results == []
        assert result.errors == []
        assert result.step_results == {}
    
    # Test Parallel Execution
    @pytest.mark.asyncio
    async def test_execute_parallel_success(self, orchestrator, user_context):
        """Test successful parallel plugin execution."""
        plugin_calls = [
            PluginCall(intent="hello_world", params={"name": "Alice"}, call_id="call1"),
            PluginCall(intent="time_query", params={}, call_id="call2"),
            PluginCall(intent="math_add", params={"a": 2, "b": 3}, call_id="call3")
        ]
        
        results = await orchestrator.execute_parallel(plugin_calls, user_context)
        
        assert len(results) == 3
        assert results[0] == {"message": "Hello Alice!"}
        assert results[1] == {"time": "2023-01-01 12:00:00"}
        assert results[2] == {"result": 5}
    
    @pytest.mark.asyncio
    async def test_execute_parallel_with_failures(self, orchestrator, user_context):
        """Test parallel execution with some failures."""
        plugin_calls = [
            PluginCall(intent="hello_world", params={"name": "Alice"}, call_id="call1"),
            PluginCall(intent="failing_plugin", params={}, call_id="call2"),
            PluginCall(intent="time_query", params={}, call_id="call3")
        ]
        
        results = await orchestrator.execute_parallel(plugin_calls, user_context)
        
        assert len(results) == 3
        assert results[0] == {"message": "Hello Alice!"}
        assert isinstance(results[1], RuntimeError)  # Exception returned
        assert results[2] == {"time": "2023-01-01 12:00:00"}
    
    @pytest.mark.asyncio
    async def test_execute_parallel_empty(self, orchestrator, user_context):
        """Test parallel execution with empty list."""
        results = await orchestrator.execute_parallel([], user_context)
        assert results == []
    
    # Test Conditional Execution
    @pytest.mark.asyncio
    async def test_execute_conditional_workflow_true(self, orchestrator, user_context):
        """Test conditional workflow when condition is true."""
        # Set up context for condition
        orchestrator.set_context("test_value", 10)
        
        condition = Condition("${test_value}", ConditionOperator.GREATER_THAN, 5)
        if_steps = [PluginStep(intent="hello_world", params={"name": "True"})]
        else_steps = [PluginStep(intent="hello_world", params={"name": "False"})]
        
        result = await orchestrator.execute_conditional_workflow(
            condition, if_steps, else_steps, user_context
        )
        
        assert result.success is True
        assert result.results[0] == {"message": "Hello True!"}
    
    @pytest.mark.asyncio
    async def test_execute_conditional_workflow_false(self, orchestrator, user_context):
        """Test conditional workflow when condition is false."""
        # Set up context for condition
        orchestrator.set_context("test_value", 3)
        
        condition = Condition("${test_value}", ConditionOperator.GREATER_THAN, 5)
        if_steps = [PluginStep(intent="hello_world", params={"name": "True"})]
        else_steps = [PluginStep(intent="hello_world", params={"name": "False"})]
        
        result = await orchestrator.execute_conditional_workflow(
            condition, if_steps, else_steps, user_context
        )
        
        assert result.success is True
        assert result.results[0] == {"message": "Hello False!"}
    
    @pytest.mark.asyncio
    async def test_execute_conditional_workflow_no_else(self, orchestrator, user_context):
        """Test conditional workflow without else steps."""
        orchestrator.set_context("test_value", 3)
        
        condition = Condition("${test_value}", ConditionOperator.GREATER_THAN, 5)
        if_steps = [PluginStep(intent="hello_world", params={"name": "True"})]
        
        result = await orchestrator.execute_conditional_workflow(
            condition, if_steps, None, user_context
        )
        
        assert result.success is True
        assert result.results == []  # No steps executed
    
    # Test Loop Execution
    @pytest.mark.asyncio
    async def test_execute_loop_workflow(self, orchestrator, user_context):
        """Test loop workflow execution."""
        # Set up loop condition that will be true for 3 iterations
        orchestrator.set_context("counter", 0)
        
        # Create a condition that checks counter < 3
        loop_condition = Condition("${counter}", ConditionOperator.LESS_THAN, 3)
        loop_steps = [
            PluginStep(intent="math_add", params={"a": "${counter}", "b": 1}, output_key="new_counter")
        ]
        
        # Mock the condition evaluation to simulate counter increment
        original_evaluate = loop_condition.evaluate
        counter = [0]  # Use list to allow modification in nested function
        
        def mock_evaluate(context):
            result = counter[0] < 3
            counter[0] += 1
            orchestrator.set_context("counter", counter[0])
            return result
        
        loop_condition.evaluate = mock_evaluate
        
        results = await orchestrator.execute_loop_workflow(
            loop_condition, loop_steps, max_iterations=5, user_context=user_context
        )
        
        assert len(results) == 3  # Should execute 3 times
        assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_execute_loop_workflow_max_iterations(self, orchestrator, user_context):
        """Test loop workflow with max iterations limit."""
        # Condition that's always true
        loop_condition = Condition("true", ConditionOperator.EQUALS, "true")
        loop_steps = [PluginStep(intent="hello_world", params={"name": "Loop"})]
        
        results = await orchestrator.execute_loop_workflow(
            loop_condition, loop_steps, max_iterations=2, user_context=user_context
        )
        
        assert len(results) == 2  # Limited by max_iterations
    
    # Test Context Management
    def test_set_and_get_context(self, orchestrator):
        """Test context management."""
        orchestrator.set_context("test_key", "test_value")
        assert orchestrator.get_context("test_key") == "test_value"
        assert orchestrator.get_context("missing_key", "default") == "default"
    
    def test_clear_context(self, orchestrator):
        """Test context clearing."""
        orchestrator.set_context("test_key", "test_value")
        orchestrator.clear_context()
        assert orchestrator.get_context("test_key") is None
    
    # Test Parameter Reference Resolution
    def test_resolve_parameter_references_simple(self, orchestrator):
        """Test simple parameter reference resolution."""
        step_results = {"step1": {"value": "hello"}}
        params = {"message": "${step1.value}"}
        
        resolved = orchestrator._resolve_parameter_references(params, step_results)
        assert resolved["message"] == "hello"
    
    def test_resolve_parameter_references_direct(self, orchestrator):
        """Test direct step reference resolution."""
        step_results = {"step1": "direct_value"}
        params = {"message": "${step1}"}
        
        resolved = orchestrator._resolve_parameter_references(params, step_results)
        assert resolved["message"] == "direct_value"
    
    def test_resolve_parameter_references_missing(self, orchestrator):
        """Test parameter reference resolution with missing reference."""
        step_results = {"step1": {"value": "hello"}}
        params = {"message": "${missing.value}"}
        
        resolved = orchestrator._resolve_parameter_references(params, step_results)
        assert resolved["message"] == "${missing.value}"  # Unchanged
    
    def test_resolve_parameter_references_non_string(self, orchestrator):
        """Test parameter reference resolution with non-string values."""
        step_results = {"step1": {"value": "hello"}}
        params = {"number": 42, "message": "${step1.value}"}
        
        resolved = orchestrator._resolve_parameter_references(params, step_results)
        assert resolved["number"] == 42
        assert resolved["message"] == "hello"
    
    # Test Advanced Workflow Features
    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt_github_slack(self, orchestrator):
        """Test workflow creation from GitHub-Slack prompt."""
        prompt = "Monitor GitHub repo and notify Slack when tests fail"
        workflow_def = orchestrator.create_workflow_from_prompt(prompt)
        
        assert workflow_def.name.startswith("Workflow from prompt")
        assert workflow_def.description == prompt
        assert "check_github" in workflow_def.steps
        assert "notify_slack" in workflow_def.steps
    
    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt_scheduled(self, orchestrator):
        """Test workflow creation from scheduled task prompt."""
        prompt = "Generate daily reports and send via email"
        workflow_def = orchestrator.create_workflow_from_prompt(prompt)
        
        assert "fetch_data" in workflow_def.steps
        assert "process_data" in workflow_def.steps
        assert "send_notification" in workflow_def.steps
    
    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt_default(self, orchestrator):
        """Test workflow creation from generic prompt."""
        prompt = "Do something generic"
        workflow_def = orchestrator.create_workflow_from_prompt(prompt)
        
        assert "hello" in workflow_def.steps
        assert workflow_def.start_step == "hello"
    
    def test_register_transform_function(self, orchestrator):
        """Test registering custom transform function."""
        def custom_func(x):
            return x * 2
        
        orchestrator.register_transform_function("double", custom_func)
        
        # Verify function is registered in workflow engine
        assert "double" in orchestrator.workflow_engine.functions
        assert orchestrator.workflow_engine.functions["double"](5) == 10
    
    def test_register_mcp_tool(self, orchestrator):
        """Test registering MCP tool."""
        tool_info = {"schema": {}, "handler": Mock()}
        
        orchestrator.register_mcp_tool("test_service", "test_tool", tool_info)
        
        # Verify tool is registered in workflow engine
        assert "test_service.test_tool" in orchestrator.workflow_engine.mcp_tools
    
    def test_get_workflow_execution_not_found(self, orchestrator):
        """Test getting non-existent workflow execution."""
        execution = orchestrator.get_workflow_execution("non_existent")
        assert execution is None
    
    def test_list_workflow_executions_empty(self, orchestrator):
        """Test listing workflow executions when none exist."""
        executions = orchestrator.list_workflow_executions()
        assert executions == []
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_execution_not_found(self, orchestrator):
        """Test cancelling non-existent workflow execution."""
        success = await orchestrator.cancel_workflow_execution("non_existent")
        assert success is False


class TestCondition:
    """Test Condition class functionality."""
    
    def test_condition_equals(self):
        """Test equals condition."""
        condition = Condition("test_value", ConditionOperator.EQUALS, "expected")
        context = {"test_value": "expected"}
        
        assert condition.evaluate(context) is True
        
        context["test_value"] = "different"
        assert condition.evaluate(context) is False
    
    def test_condition_not_equals(self):
        """Test not equals condition."""
        condition = Condition("test_value", ConditionOperator.NOT_EQUALS, "expected")
        context = {"test_value": "different"}
        
        assert condition.evaluate(context) is True
        
        context["test_value"] = "expected"
        assert condition.evaluate(context) is False
    
    def test_condition_greater_than(self):
        """Test greater than condition."""
        condition = Condition("test_value", ConditionOperator.GREATER_THAN, 5)
        context = {"test_value": 10}
        
        assert condition.evaluate(context) is True
        
        context["test_value"] = 3
        assert condition.evaluate(context) is False
    
    def test_condition_less_than(self):
        """Test less than condition."""
        condition = Condition("test_value", ConditionOperator.LESS_THAN, 10)
        context = {"test_value": 5}
        
        assert condition.evaluate(context) is True
        
        context["test_value"] = 15
        assert condition.evaluate(context) is False
    
    def test_condition_contains(self):
        """Test contains condition."""
        condition = Condition("test_value", ConditionOperator.CONTAINS, "hello")
        context = {"test_value": "hello world"}
        
        assert condition.evaluate(context) is True
        
        context["test_value"] = "goodbye world"
        assert condition.evaluate(context) is False
    
    def test_condition_exists(self):
        """Test exists condition."""
        condition = Condition("test_value", ConditionOperator.EXISTS, None)
        context = {"test_value": "anything"}
        
        assert condition.evaluate(context) is True
        
        context = {}
        assert condition.evaluate(context) is False
    
    def test_condition_with_reference(self):
        """Test condition with parameter reference."""
        condition = Condition("${step1.result}", ConditionOperator.EQUALS, "success")
        context = {"step1": {"result": "success"}}
        
        assert condition.evaluate(context) is True
        
        context["step1"]["result"] = "failure"
        assert condition.evaluate(context) is False
    
    def test_condition_resolve_value_missing_reference(self):
        """Test resolving missing reference."""
        condition = Condition("${missing.value}", ConditionOperator.EQUALS, "test")
        context = {}
        
        # Should return None for missing reference
        assert condition.evaluate(context) is False  # None != "test"


class TestWorkflowDataStructures:
    """Test workflow data structures."""
    
    def test_plugin_step_creation(self):
        """Test PluginStep creation."""
        step = PluginStep(
            intent="test_intent",
            params={"param1": "value1"},
            output_key="test_output"
        )
        
        assert step.intent == "test_intent"
        assert step.params == {"param1": "value1"}
        assert step.output_key == "test_output"
    
    def test_plugin_call_creation(self):
        """Test PluginCall creation."""
        call = PluginCall(
            intent="test_intent",
            params={"param1": "value1"},
            call_id="call_123"
        )
        
        assert call.intent == "test_intent"
        assert call.params == {"param1": "value1"}
        assert call.call_id == "call_123"
    
    def test_workflow_step_creation(self):
        """Test WorkflowStep creation."""
        step = WorkflowStep(
            step_id="step_1",
            step_type=StepType.PLUGIN,
            intent="test_intent",
            params={"param1": "value1"}
        )
        
        assert step.step_id == "step_1"
        assert step.step_type == StepType.PLUGIN
        assert step.intent == "test_intent"
        assert step.params == {"param1": "value1"}
    
    def test_workflow_result_creation(self):
        """Test WorkflowResult creation."""
        from ai_karen_engine.extensions.orchestrator import WorkflowExecution
        
        execution = WorkflowExecution(
            execution_id="exec_123",
            workflow_id="workflow_456",
            status="completed",
            start_time=1234567890.0
        )
        
        result = WorkflowResult(
            success=True,
            results=["result1", "result2"],
            errors=[],
            execution_time=1.5,
            step_results={"step1": "result1"},
            execution=execution
        )
        
        assert result.success is True
        assert result.results == ["result1", "result2"]
        assert result.errors == []
        assert result.execution_time == 1.5
        assert result.step_results == {"step1": "result1"}
        assert result.execution == execution