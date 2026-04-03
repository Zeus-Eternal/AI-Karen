"""
Tests for the Prompt-Driven Automation Extension.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from extensions.automation.prompt_driven import PromptDrivenAutomationExtension, WorkflowStatus, Workflow, WorkflowStep


class TestPromptDrivenAutomationExtension:
    """Test suite for the Prompt-Driven Automation Extension."""
    
    @pytest.fixture
    async def extension(self):
        """Create a test extension instance."""
        # Mock the required dependencies
        mock_manifest = Mock()
        mock_manifest.name = "prompt-driven-automation"
        
        mock_context = Mock()
        mock_context.plugin_router = Mock()
        mock_context.db_session = Mock()
        mock_context.config = {}
        
        extension = PromptDrivenAutomationExtension(mock_manifest, mock_context)
        await extension._initialize()
        return extension
    
    @pytest.mark.asyncio
    async def test_extension_initialization(self, extension):
        """Test that the extension initializes correctly."""
        assert extension.workflows == {}
        assert extension.execution_history == []
        assert len(extension.plugin_capabilities) > 0
        assert len(extension.workflow_templates) > 0
    
    @pytest.mark.asyncio
    async def test_create_workflow_from_prompt(self, extension):
        """Test creating a workflow from a natural language prompt."""
        prompt = "Monitor GitHub repo and notify Slack when tests fail"
        
        # Mock the plugin orchestrator
        extension.plugin_orchestrator.execute_plugin = AsyncMock(return_value={
            "intent": "workflow_intent",
            "entities": ["github", "slack", "tests"]
        })
        
        result = await extension._create_workflow_from_prompt_tool(prompt, "Test Workflow")
        
        assert result["success"] is True
        assert "workflow" in result
        assert result["workflow"]["name"] == "Test Workflow"
        assert result["workflow"]["prompt"] == prompt
        assert len(result["workflow"]["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_discover_plugins_for_task(self, extension):
        """Test plugin discovery for a specific task."""
        task_description = "Send notifications to Slack"
        
        # Mock the plugin orchestrator
        extension.plugin_orchestrator.execute_plugin = AsyncMock(return_value={
            "capabilities": ["send_message", "notify"]
        })
        
        result = await extension._discover_plugins_for_task_tool(task_description)
        
        assert result["success"] is True
        assert "suitable_plugins" in result
        assert len(result["suitable_plugins"]) > 0
        
        # Check that slack_notifier is recommended
        plugin_names = [p["plugin"] for p in result["suitable_plugins"]]
        assert "slack_notifier" in plugin_names
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, extension):
        """Test workflow execution."""
        # Create a test workflow
        workflow = Workflow(
            id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
            prompt="Test prompt",
            steps=[
                WorkflowStep(
                    id="step1",
                    plugin="time_query",
                    params={"action": "get_time"}
                )
            ],
            triggers=[{"type": "manual"}],
            status=WorkflowStatus.ACTIVE,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        extension.workflows["test_workflow"] = workflow
        
        # Mock plugin execution
        extension.plugin_orchestrator.execute_plugin = AsyncMock(return_value={
            "timestamp": "2024-01-01T12:00:00Z"
        })
        
        result = await extension.execute_workflow("test_workflow")
        
        assert result["success"] is True
        assert result["workflow_id"] == "test_workflow"
        assert result["steps_executed"] == 1
        assert "execution_id" in result
        assert "duration" in result
    
    @pytest.mark.asyncio
    async def test_workflow_execution_with_failure(self, extension):
        """Test workflow execution with step failure."""
        # Create a test workflow
        workflow = Workflow(
            id="test_workflow_fail",
            name="Test Workflow Fail",
            description="A test workflow that fails",
            prompt="Test prompt",
            steps=[
                WorkflowStep(
                    id="step1",
                    plugin="nonexistent_plugin",
                    params={"action": "fail"}
                )
            ],
            triggers=[{"type": "manual"}],
            status=WorkflowStatus.ACTIVE,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        extension.workflows["test_workflow_fail"] = workflow
        
        # Mock plugin execution failure
        extension.plugin_orchestrator.execute_plugin = AsyncMock(side_effect=Exception("Plugin failed"))
        
        result = await extension.execute_workflow("test_workflow_fail")
        
        assert result["success"] is False
        assert "error" in result
        assert result["workflow_id"] == "test_workflow_fail"
    
    @pytest.mark.asyncio
    async def test_workflow_optimization(self, extension):
        """Test workflow optimization based on execution history."""
        # Create a test workflow with some execution history
        workflow = Workflow(
            id="test_workflow_opt",
            name="Test Workflow Optimization",
            description="A test workflow for optimization",
            prompt="Test prompt",
            steps=[
                WorkflowStep(
                    id="step1",
                    plugin="time_query",
                    params={"action": "get_time"}
                )
            ],
            triggers=[{"type": "manual"}],
            status=WorkflowStatus.ACTIVE,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            execution_count=10,
            success_rate=0.7
        )
        
        extension.workflows["test_workflow_opt"] = workflow
        
        # Add some execution history
        extension.execution_history = [
            {
                "workflow_id": "test_workflow_opt",
                "success": False,
                "failed_step": "step1",
                "duration": 30,
                "start_time": datetime.utcnow().isoformat()
            }
        ] * 3  # 3 failures
        
        result = await extension._optimize_workflow_tool("test_workflow_opt", "reliability")
        
        assert result["success"] is True
        assert "optimizations" in result
        assert len(result["optimizations"]) > 0
    
    def test_template_matching(self, extension):
        """Test workflow template matching."""
        prompt = "monitor github and notify slack"
        
        matching_template = extension._find_matching_template(prompt, "monitoring")
        
        assert matching_template is not None
        assert "github_slack_monitoring" in str(matching_template)
    
    def test_plugin_discovery_capabilities(self, extension):
        """Test that plugin capabilities are properly loaded."""
        assert "github_integration" in extension.plugin_capabilities
        assert "slack_notifier" in extension.plugin_capabilities
        assert "email_sender" in extension.plugin_capabilities
        
        github_plugin = extension.plugin_capabilities["github_integration"]
        assert "monitor_repo" in github_plugin["capabilities"]
        assert "repo_url" in github_plugin["inputs"]
    
    def test_workflow_templates_loaded(self, extension):
        """Test that workflow templates are properly loaded."""
        assert len(extension.workflow_templates) > 0
        assert "github_slack_monitoring" in extension.workflow_templates
        assert "file_processing_pipeline" in extension.workflow_templates
        
        github_template = extension.workflow_templates["github_slack_monitoring"]
        assert github_template["name"] == "GitHub to Slack Monitoring"
        assert "github_integration" in github_template["plugins"]
        assert "slack_notifier" in github_template["plugins"]
    
    @pytest.mark.asyncio
    async def test_parameter_resolution(self, extension):
        """Test parameter resolution with execution context."""
        params = {
            "message": "{{previous.event_data}}",
            "channel": "#alerts",
            "user": "{{input.user_id}}"
        }
        
        execution_context = {
            "steps_executed": [
                {
                    "output": {"event_data": "Test event occurred"}
                }
            ],
            "input_data": {"user_id": "user123"}
        }
        
        resolved = extension._resolve_step_parameters(params, execution_context)
        
        assert resolved["message"] == "Test event occurred"
        assert resolved["channel"] == "#alerts"
        assert resolved["user"] == "user123"
    
    def test_condition_evaluation(self, extension):
        """Test step condition evaluation."""
        # Test success condition
        conditions = {"if": "{{previous.success}}"}
        execution_context = {
            "steps_executed": [{"success": True}]
        }
        
        result = extension._evaluate_conditions(conditions, execution_context)
        assert result is True
        
        # Test failure condition
        execution_context = {
            "steps_executed": [{"success": False}]
        }
        
        result = extension._evaluate_conditions(conditions, execution_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_api_router_creation(self, extension):
        """Test that API router is created with all endpoints."""
        router = extension.create_api_router()
        
        # Check that router has the expected prefix
        assert router.prefix == "/api/extensions/prompt-driven-automation"
        
        # Check that routes are registered (this is a basic check)
        route_paths = [route.path for route in router.routes]
        
        expected_paths = [
            "/workflows",
            "/workflows/{workflow_id}",
            "/workflows/{workflow_id}/execute",
            "/discover",
            "/templates",
            "/plugins",
            "/metrics"
        ]
        
        for expected_path in expected_paths:
            # Check if any route contains the expected path pattern
            assert any(expected_path in path for path in route_paths), f"Missing route: {expected_path}"


if __name__ == "__main__":
    pytest.main([__file__])