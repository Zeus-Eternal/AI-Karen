"""
Basic tests for the plugin orchestration interface.

This module tests the core plugin orchestration capabilities
without complex workflow dependencies.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.extensions.orchestrator import (
    PluginOrchestrator, PluginStep, PluginCall, WorkflowResult,
    Condition, ConditionOperator
)


class TestBasicPluginOrchestrator:
    """Test the basic PluginOrchestrator functionality."""
    
    @pytest.fixture
    def mock_plugin_router(self):
        """Create a mock plugin router."""
        router = Mock()
        router.dispatch = AsyncMock()
        return router
    
    @pytest.fixture
    def orchestrator(self, mock_plugin_router):
        """Create a PluginOrchestrator instance."""
        return PluginOrchestrator(mock_plugin_router)
    
    @pytest.mark.asyncio
    async def test_execute_single_plugin(self, orchestrator, mock_plugin_router):
        """Test executing a single plugin."""
        # Setup
        mock_plugin_router.dispatch.return_value = {"result": "success"}
        user_context = {"user_id": "test_user", "roles": ["user"]}
        
        # Execute
        result = await orchestrator.execute_plugin(
            intent="test_plugin",
            params={"param1": "value1"},
            user_context=user_context
        )
        
        # Verify
        assert result == {"result": "success"}
        mock_plugin_router.dispatch.assert_called_once_with(
            "test_plugin", 
            {"param1": "value1"}, 
            ["user"]
        )
    
    @pytest.mark.asyncio
    async def test_execute_workflow_sequence(self, orchestrator, mock_plugin_router):
        """Test executing a sequence of plugins."""
        # Setup
        mock_plugin_router.dispatch.side_effect = [
            {"step1_result": "data1"},
            {"step2_result": "data2"}
        ]
        
        workflow = [
            PluginStep(intent="plugin1", params={"input": "test"}, output_key="step1"),
            PluginStep(intent="plugin2", params={"input": "${step1.step1_result}"}, output_key="step2")
        ]
        
        user_context = {"user_id": "test_user", "roles": ["user"]}
        
        # Execute
        result = await orchestrator.execute_workflow(workflow, user_context)
        
        # Verify
        assert result.success is True
        assert len(result.results) == 2
        assert result.step_results["step1"] == {"step1_result": "data1"}
        assert result.step_results["step2"] == {"step2_result": "data2"}
        
        # Verify parameter resolution worked
        assert mock_plugin_router.dispatch.call_count == 2
        calls = mock_plugin_router.dispatch.call_args_list
        assert calls[1][0][1]["input"] == "data1"  # Parameter was resolved
    
    @pytest.mark.asyncio
    async def test_execute_parallel_plugins(self, orchestrator, mock_plugin_router):
        """Test executing plugins in parallel."""
        # Setup
        mock_plugin_router.dispatch.side_effect = [
            {"plugin1_result": "result1"},
            {"plugin2_result": "result2"},
            {"plugin3_result": "result3"}
        ]
        
        plugin_calls = [
            PluginCall(intent="plugin1", params={"input": "test1"}, call_id="call1"),
            PluginCall(intent="plugin2", params={"input": "test2"}, call_id="call2"),
            PluginCall(intent="plugin3", params={"input": "test3"}, call_id="call3")
        ]
        
        user_context = {"user_id": "test_user", "roles": ["user"]}
        
        # Execute
        results = await orchestrator.execute_parallel(plugin_calls, user_context)
        
        # Verify
        assert len(results) == 3
        assert results[0] == {"plugin1_result": "result1"}
        assert results[1] == {"plugin2_result": "result2"}
        assert results[2] == {"plugin3_result": "result3"}
        assert mock_plugin_router.dispatch.call_count == 3
    
    def test_condition_evaluation(self):
        """Test condition evaluation."""
        context = {"value1": 10, "value2": 5, "text": "hello world"}
        
        # Test equality
        condition = Condition("${value1}", ConditionOperator.EQUALS, 10)
        assert condition.evaluate(context) is True
        
        condition = Condition("${value1}", ConditionOperator.EQUALS, 5)
        assert condition.evaluate(context) is False
        
        # Test greater than
        condition = Condition("${value1}", ConditionOperator.GREATER_THAN, 5)
        assert condition.evaluate(context) is True
        
        # Test contains
        condition = Condition("${text}", ConditionOperator.CONTAINS, "world")
        assert condition.evaluate(context) is True
        
        # Test exists
        condition = Condition("${value1}", ConditionOperator.EXISTS, None)
        assert condition.evaluate(context) is True
        
        condition = Condition("${nonexistent}", ConditionOperator.EXISTS, None)
        assert condition.evaluate(context) is False
    
    @pytest.mark.asyncio
    async def test_conditional_workflow(self, orchestrator, mock_plugin_router):
        """Test conditional workflow execution."""
        # Setup
        mock_plugin_router.dispatch.return_value = {"result": "success"}
        
        condition = Condition("${should_execute}", ConditionOperator.EQUALS, True)
        if_steps = [PluginStep(intent="plugin_if", params={"action": "execute"})]
        else_steps = [PluginStep(intent="plugin_else", params={"action": "skip"})]
        
        user_context = {"user_id": "test_user", "roles": ["user"]}
        
        # Test true condition
        orchestrator.set_context("should_execute", True)
        result = await orchestrator.execute_conditional_workflow(
            condition, if_steps, else_steps, user_context
        )
        
        assert result.success is True
        mock_plugin_router.dispatch.assert_called_with("plugin_if", {"action": "execute"}, ["user"])
        
        # Test false condition
        orchestrator.set_context("should_execute", False)
        result = await orchestrator.execute_conditional_workflow(
            condition, if_steps, else_steps, user_context
        )
        
        assert result.success is True
        mock_plugin_router.dispatch.assert_called_with("plugin_else", {"action": "skip"}, ["user"])
    
    def test_context_management(self, orchestrator):
        """Test execution context management."""
        # Test setting and getting context
        orchestrator.set_context("key1", "value1")
        orchestrator.set_context("key2", {"nested": "value"})
        
        assert orchestrator.get_context("key1") == "value1"
        assert orchestrator.get_context("key2") == {"nested": "value"}
        assert orchestrator.get_context("nonexistent", "default") == "default"
        
        # Test clearing context
        orchestrator.clear_context()
        assert orchestrator.get_context("key1") is None
    
    def test_parameter_resolution(self, orchestrator):
        """Test parameter reference resolution."""
        step_results = {
            "step1": {"output": "result1", "count": 5},
            "step2": "simple_result"
        }
        
        params = {
            "static_param": "static_value",
            "reference_param": "${step1.output}",
            "nested_reference": "${step1.count}",
            "direct_reference": "${step2}",
            "invalid_reference": "${nonexistent.field}"
        }
        
        resolved = orchestrator._resolve_parameter_references(params, step_results)
        
        assert resolved["static_param"] == "static_value"
        assert resolved["reference_param"] == "result1"
        assert resolved["nested_reference"] == 5
        assert resolved["direct_reference"] == "simple_result"
        assert resolved["invalid_reference"] == "${nonexistent.field}"  # Unchanged
    
    def test_workflow_from_prompt(self, orchestrator):
        """Test creating workflow from natural language prompt."""
        # Test GitHub to Slack workflow
        prompt = "Monitor GitHub repo and notify Slack when tests fail"
        workflow = orchestrator.create_workflow_from_prompt(prompt)
        
        assert workflow.name.startswith("Workflow from prompt:")
        assert workflow.description == prompt
        assert len(workflow.steps) == 2
        assert "check_github" in workflow.steps
        assert "notify_slack" in workflow.steps
        
        # Test scheduled workflow
        prompt = "Send daily report via email"
        workflow = orchestrator.create_workflow_from_prompt(prompt)
        
        assert len(workflow.steps) == 3
        assert "fetch_data" in workflow.steps
        assert "process_data" in workflow.steps
        assert "send_notification" in workflow.steps
    
    def test_builtin_functions_registration(self, orchestrator):
        """Test that built-in transformation functions are registered."""
        # Test string functions
        upper_func = orchestrator.workflow_engine.function_registry.get("upper")
        assert upper_func is not None
        assert upper_func("hello") == "HELLO"
        
        # Test math functions
        add_func = orchestrator.workflow_engine.function_registry.get("add")
        assert add_func is not None
        assert add_func(5, 3) == 8
        
        # Test utility functions
        uuid_func = orchestrator.workflow_engine.function_registry.get("uuid")
        assert uuid_func is not None
        uuid_result = uuid_func()
        assert isinstance(uuid_result, str)
        assert len(uuid_result) == 36  # Standard UUID length
    
    def test_mcp_tool_registration(self, orchestrator):
        """Test MCP tool registration."""
        tool_info = {
            "name": "test_tool",
            "description": "A test tool",
            "schema": {"type": "object", "properties": {}}
        }
        
        orchestrator.register_mcp_tool("test_service", "test_tool", tool_info)
        
        # Verify tool was registered in workflow engine
        assert "test_service" in orchestrator.workflow_engine.mcp_tool_registry
        assert "test_tool" in orchestrator.workflow_engine.mcp_tool_registry["test_service"]
        assert orchestrator.workflow_engine.mcp_tool_registry["test_service"]["test_tool"] == tool_info
    
    def test_custom_transform_function(self, orchestrator):
        """Test registering custom transformation functions."""
        def custom_transform(x, y):
            return f"{x}_{y}"
        
        orchestrator.register_transform_function("custom_concat", custom_transform)
        
        # Verify function was registered
        assert "custom_concat" in orchestrator.workflow_engine.function_registry
        func = orchestrator.workflow_engine.function_registry["custom_concat"]
        assert func("hello", "world") == "hello_world"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])