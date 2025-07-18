"""
Advanced Plugin Orchestration Interface for Extensions.

This module provides sophisticated workflow orchestration capabilities
including conditional execution, loops, error handling, and state management.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

from ai_karen_engine.plugins.router import PluginRouter
from .workflow_engine import WorkflowEngine, WorkflowDefinition, WorkflowStep as AdvancedWorkflowStep, StepType as AdvancedStepType


class StepType(Enum):
    """Types of workflow steps (legacy)."""
    PLUGIN = "plugin"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    WEBHOOK = "webhook"


class ConditionOperator(Enum):
    """Condition operators for conditional steps."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    CONTAINS = "contains"
    EXISTS = "exists"


@dataclass
class Condition:
    """Represents a condition for conditional execution."""
    left_operand: str  # Can be a reference like "${step1.result}"
    operator: ConditionOperator
    right_operand: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate the condition against the current context."""
        # Resolve left operand
        left_value = self._resolve_value(self.left_operand, context)
        right_value = self.right_operand
        
        # Evaluate based on operator
        if self.operator == ConditionOperator.EQUALS:
            return left_value == right_value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return left_value != right_value
        elif self.operator == ConditionOperator.GREATER_THAN:
            return left_value > right_value
        elif self.operator == ConditionOperator.LESS_THAN:
            return left_value < right_value
        elif self.operator == ConditionOperator.CONTAINS:
            return right_value in str(left_value)
        elif self.operator == ConditionOperator.EXISTS:
            return left_value is not None
        
        return False
    
    def _resolve_value(self, value: str, context: Dict[str, Any]) -> Any:
        """Resolve a value that might be a reference."""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            ref_path = value[2:-1]
            if "." in ref_path:
                step_key, field_key = ref_path.split(".", 1)
                if step_key in context:
                    step_result = context[step_key]
                    if isinstance(step_result, dict) and field_key in step_result:
                        return step_result[field_key]
            else:
                return context.get(ref_path)
        return value


@dataclass
class WorkflowStep:
    """Enhanced workflow step with support for different step types."""
    step_id: str
    step_type: StepType
    name: Optional[str] = None
    
    # Plugin execution
    intent: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Conditional execution
    condition: Optional[Condition] = None
    if_steps: List['WorkflowStep'] = field(default_factory=list)
    else_steps: List['WorkflowStep'] = field(default_factory=list)
    
    # Loop execution
    loop_condition: Optional[Condition] = None
    loop_steps: List['WorkflowStep'] = field(default_factory=list)
    max_iterations: int = 10
    
    # Parallel execution
    parallel_steps: List['WorkflowStep'] = field(default_factory=list)
    
    # Delay
    delay_seconds: float = 0
    
    # Webhook
    webhook_url: Optional[str] = None
    webhook_method: str = "POST"
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    # Output configuration
    output_key: Optional[str] = None
    
    # Error handling
    retry_count: int = 0
    retry_delay: float = 1.0
    continue_on_error: bool = False


@dataclass
class PluginStep:
    """Legacy plugin step for backward compatibility."""
    intent: str
    params: Dict[str, Any]
    output_key: Optional[str] = None


@dataclass
class PluginCall:
    """Represents a plugin call for parallel execution."""
    intent: str
    params: Dict[str, Any]
    call_id: str


@dataclass
class WorkflowExecution:
    """Tracks the execution of a workflow."""
    execution_id: str
    workflow_id: Optional[str]
    status: str  # "running", "completed", "failed", "cancelled"
    start_time: float
    end_time: Optional[float] = None
    current_step: Optional[str] = None
    step_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    results: List[Any]
    errors: List[str]
    execution_time: float
    step_results: Dict[str, Any]
    execution: WorkflowExecution


class PluginOrchestrator:
    """
    Orchestrates plugin execution within extensions.
    
    This class provides methods for extensions to compose and execute
    multiple plugins in various patterns (sequential, parallel, conditional).
    It integrates with the advanced workflow engine for complex orchestration.
    """
    
    def __init__(self, plugin_router: PluginRouter):
        """
        Initialize the orchestrator.
        
        Args:
            plugin_router: The plugin router instance for executing plugins
        """
        self.plugin_router = plugin_router
        self.execution_context: Dict[str, Any] = {}
        self.logger = logging.getLogger("extension.orchestrator")
        
        # Initialize advanced workflow engine
        self.workflow_engine = WorkflowEngine(self)
        
        # Register built-in transformation functions
        self._register_builtin_functions()
    
    def _register_builtin_functions(self) -> None:
        """Register built-in transformation functions."""
        # String manipulation functions
        self.workflow_engine.register_function("upper", lambda x: str(x).upper())
        self.workflow_engine.register_function("lower", lambda x: str(x).lower())
        self.workflow_engine.register_function("strip", lambda x: str(x).strip())
        
        # Math functions
        self.workflow_engine.register_function("add", lambda x, y: x + y)
        self.workflow_engine.register_function("subtract", lambda x, y: x - y)
        self.workflow_engine.register_function("multiply", lambda x, y: x * y)
        self.workflow_engine.register_function("divide", lambda x, y: x / y if y != 0 else 0)
        
        # List functions
        self.workflow_engine.register_function("length", lambda x: len(x) if hasattr(x, '__len__') else 0)
        self.workflow_engine.register_function("first", lambda x: x[0] if x and hasattr(x, '__getitem__') else None)
        self.workflow_engine.register_function("last", lambda x: x[-1] if x and hasattr(x, '__getitem__') else None)
        
        # JSON functions
        self.workflow_engine.register_function("json_parse", lambda x: json.loads(x) if isinstance(x, str) else x)
        self.workflow_engine.register_function("json_stringify", lambda x: json.dumps(x))
        
        # Utility functions
        self.workflow_engine.register_function("now", lambda: time.time())
        self.workflow_engine.register_function("uuid", lambda: str(uuid.uuid4()))
    
    async def execute_advanced_workflow(
        self,
        workflow_definition: WorkflowDefinition,
        inputs: Dict[str, Any] = None,
        user_context: Dict[str, Any] = None
    ) -> Any:
        """
        Execute an advanced workflow using the workflow engine.
        
        Args:
            workflow_definition: Advanced workflow definition
            inputs: Input variables for the workflow
            user_context: User context for plugin execution
            
        Returns:
            Workflow execution result
        """
        # Register the workflow
        workflow_id = self.workflow_engine.register_workflow(workflow_definition)
        
        # Execute the workflow
        execution = await self.workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            inputs=inputs,
            user_context=user_context
        )
        
        return execution
    
    def create_workflow_from_prompt(self, prompt: str, context: Dict[str, Any] = None) -> WorkflowDefinition:
        """
        Create a workflow definition from a natural language prompt.
        
        This is a simplified implementation that demonstrates the concept.
        In a real implementation, this would use an LLM to parse the prompt.
        
        Args:
            prompt: Natural language description of the workflow
            context: Additional context for workflow creation
            
        Returns:
            WorkflowDefinition created from the prompt
        """
        workflow_id = f"workflow_{int(time.time())}"
        
        # Simple prompt parsing (in reality, this would use an LLM)
        steps = {}
        
        if "github" in prompt.lower() and "slack" in prompt.lower():
            # GitHub to Slack workflow
            steps["check_github"] = AdvancedWorkflowStep(
                id="check_github",
                type=AdvancedStepType.PLUGIN,
                config={
                    "intent": "github_check_pr",
                    "params": {"repo": "${repo_name}"},
                    "output_key": "github_result"
                },
                next_steps=["notify_slack"]
            )
            
            steps["notify_slack"] = AdvancedWorkflowStep(
                id="notify_slack",
                type=AdvancedStepType.PLUGIN,
                config={
                    "intent": "slack_notify",
                    "params": {
                        "channel": "#ci-cd",
                        "message": "GitHub check result: ${github_result}"
                    }
                }
            )
            
        elif "schedule" in prompt.lower() or "daily" in prompt.lower():
            # Scheduled workflow
            steps["fetch_data"] = AdvancedWorkflowStep(
                id="fetch_data",
                type=AdvancedStepType.PLUGIN,
                config={
                    "intent": "fetch_data",
                    "params": {"source": "api"},
                    "output_key": "data"
                },
                next_steps=["process_data"]
            )
            
            steps["process_data"] = AdvancedWorkflowStep(
                id="process_data",
                type=AdvancedStepType.TRANSFORM,
                config={
                    "transform_type": "function",
                    "function_name": "json_stringify",
                    "args": ["${data}"],
                    "output_key": "processed_data"
                },
                next_steps=["send_notification"]
            )
            
            steps["send_notification"] = AdvancedWorkflowStep(
                id="send_notification",
                type=AdvancedStepType.PLUGIN,
                config={
                    "intent": "send_email",
                    "params": {
                        "to": "${email}",
                        "subject": "Daily Report",
                        "body": "${processed_data}"
                    }
                }
            )
            
        else:
            # Default simple workflow
            steps["hello"] = AdvancedWorkflowStep(
                id="hello",
                type=AdvancedStepType.PLUGIN,
                config={
                    "intent": "hello_world",
                    "params": {"message": "Hello from workflow!"}
                }
            )
        
        return WorkflowDefinition(
            id=workflow_id,
            name=f"Workflow from prompt: {prompt[:50]}...",
            description=prompt,
            steps=steps,
            start_step=next(iter(steps.keys())) if steps else None,
            variables=context or {}
        )
    
    async def execute_conditional_workflow(
        self,
        condition: Condition,
        if_steps: List[PluginStep],
        else_steps: List[PluginStep] = None,
        user_context: Dict[str, Any] = None
    ) -> WorkflowResult:
        """
        Execute a conditional workflow.
        
        Args:
            condition: Condition to evaluate
            if_steps: Steps to execute if condition is true
            else_steps: Steps to execute if condition is false
            user_context: User context for plugin execution
            
        Returns:
            WorkflowResult with execution details
        """
        # Evaluate condition
        condition_result = condition.evaluate(self.execution_context)
        
        # Choose steps to execute
        steps_to_execute = if_steps if condition_result else (else_steps or [])
        
        self.logger.info(f"Conditional workflow: condition={condition_result}, executing {len(steps_to_execute)} steps")
        
        # Execute chosen steps
        return await self.execute_workflow(steps_to_execute, user_context or {})
    
    async def execute_loop_workflow(
        self,
        loop_condition: Condition,
        loop_steps: List[PluginStep],
        max_iterations: int = 10,
        user_context: Dict[str, Any] = None
    ) -> List[WorkflowResult]:
        """
        Execute a loop workflow.
        
        Args:
            loop_condition: Condition to check for each iteration
            loop_steps: Steps to execute in each iteration
            max_iterations: Maximum number of iterations
            user_context: User context for plugin execution
            
        Returns:
            List of WorkflowResult for each iteration
        """
        results = []
        iteration = 0
        
        self.logger.info(f"Starting loop workflow with max {max_iterations} iterations")
        
        while iteration < max_iterations and loop_condition.evaluate(self.execution_context):
            self.logger.debug(f"Loop iteration {iteration + 1}")
            
            # Set iteration context
            self.set_context("iteration", iteration)
            
            # Execute loop steps
            result = await self.execute_workflow(loop_steps, user_context or {})
            results.append(result)
            
            iteration += 1
        
        self.logger.info(f"Loop workflow completed after {iteration} iterations")
        return results
    
    def register_mcp_tool(self, service_name: str, tool_name: str, tool_info: Dict[str, Any]) -> None:
        """
        Register an MCP tool for use in workflows.
        
        Args:
            service_name: MCP service name
            tool_name: Tool name
            tool_info: Tool information including schema and handler
        """
        self.workflow_engine.register_mcp_tool(service_name, tool_name, tool_info)
        self.logger.info(f"Registered MCP tool: {service_name}.{tool_name}")
    
    def register_transform_function(self, name: str, func: Callable) -> None:
        """
        Register a custom transformation function.
        
        Args:
            name: Function name
            func: Function implementation
        """
        self.workflow_engine.register_function(name, func)
        self.logger.info(f"Registered transform function: {name}")
    
    def get_workflow_execution(self, execution_id: str) -> Optional[Any]:
        """
        Get workflow execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Workflow execution or None if not found
        """
        return self.workflow_engine.workflow_executions.get(execution_id)
    
    def list_workflow_executions(self) -> List[str]:
        """
        List all workflow execution IDs.
        
        Returns:
            List of execution IDs
        """
        return list(self.workflow_engine.workflow_executions.keys())
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """
        Cancel a running workflow execution.
        
        Args:
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        execution = self.workflow_engine.workflow_executions.get(execution_id)
        if execution and execution.status == "running":
            execution.status = "cancelled"
            execution.end_time = time.time()
            self.logger.info(f"Cancelled workflow execution: {execution_id}")
            return True
        return False
    
    async def execute_plugin(
        self, 
        intent: str, 
        params: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Any:
        """
        Execute a single plugin.
        
        Args:
            intent: The plugin intent to execute
            params: Parameters to pass to the plugin
            user_context: User context for authentication and tenant isolation
            
        Returns:
            Plugin execution result
            
        Raises:
            RuntimeError: If plugin execution fails
        """
        try:
            self.logger.debug(f"Executing plugin {intent} with params: {params}")
            
            # Extract roles from user context for RBAC
            roles = user_context.get("roles", [])
            
            # Execute the plugin through the router
            result = await self.plugin_router.dispatch(intent, params, roles)
            
            self.logger.debug(f"Plugin {intent} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Plugin {intent} execution failed: {e}")
            raise RuntimeError(f"Plugin execution failed: {e}") from e
    
    async def execute_workflow(
        self, 
        workflow: List[PluginStep],
        user_context: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute a sequence of plugin calls.
        
        Args:
            workflow: List of plugin steps to execute in sequence
            user_context: User context for authentication and tenant isolation
            
        Returns:
            WorkflowResult with execution details
        """
        import time
        start_time = time.time()
        
        results = []
        errors = []
        step_results = {}
        
        self.logger.info(f"Starting workflow execution with {len(workflow)} steps")
        
        try:
            for i, step in enumerate(workflow):
                try:
                    # Merge execution context into step parameters
                    merged_params = {**step.params}
                    
                    # Replace parameter placeholders with previous step results
                    merged_params = self._resolve_parameter_references(
                        merged_params, step_results
                    )
                    
                    # Execute the plugin
                    result = await self.execute_plugin(
                        step.intent, 
                        merged_params, 
                        user_context
                    )
                    
                    results.append(result)
                    
                    # Store result with key if specified
                    if step.output_key:
                        step_results[step.output_key] = result
                    else:
                        step_results[f"step_{i}"] = result
                    
                    self.logger.debug(f"Workflow step {i} ({step.intent}) completed")
                    
                except Exception as e:
                    error_msg = f"Step {i} ({step.intent}) failed: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    
                    # For now, we'll continue execution even if a step fails
                    # In the future, we might want to make this configurable
                    results.append(None)
        
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            errors.append(error_msg)
            self.logger.error(error_msg)
        
        execution_time = time.time() - start_time
        success = len(errors) == 0
        
        self.logger.info(
            f"Workflow execution completed in {execution_time:.2f}s. "
            f"Success: {success}, Errors: {len(errors)}"
        )
        
        # Create a mock execution for compatibility
        execution = WorkflowExecution(
            execution_id=f"exec_{int(time.time())}",
            workflow_id="legacy_workflow",
            status="completed" if success else "failed",
            start_time=start_time,
            end_time=time.time(),
            step_results=step_results,
            errors=errors
        )
        
        return WorkflowResult(
            success=success,
            results=results,
            errors=errors,
            execution_time=execution_time,
            step_results=step_results,
            execution=execution
        )
    
    async def execute_parallel(
        self,
        plugin_calls: List[PluginCall],
        user_context: Dict[str, Any]
    ) -> List[Any]:
        """
        Execute multiple plugins in parallel.
        
        Args:
            plugin_calls: List of plugin calls to execute in parallel
            user_context: User context for authentication and tenant isolation
            
        Returns:
            List of results in the same order as input calls
        """
        self.logger.info(f"Starting parallel execution of {len(plugin_calls)} plugins")
        
        # Create coroutines for all plugin calls
        coroutines = [
            self.execute_plugin(call.intent, call.params, user_context)
            for call in plugin_calls
        ]
        
        try:
            # Execute all plugins concurrently
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Parallel plugin {plugin_calls[i].intent} failed: {result}"
                    )
            
            self.logger.info("Parallel execution completed")
            return results
            
        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            raise
    
    def _resolve_parameter_references(
        self, 
        params: Dict[str, Any], 
        step_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve parameter references to previous step results.
        
        This method looks for parameter values that reference previous step
        results using a simple syntax like "${step_name.field}".
        
        Args:
            params: Parameters that may contain references
            step_results: Results from previous steps
            
        Returns:
            Parameters with references resolved
        """
        resolved_params = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference path
                ref_path = value[2:-1]  # Remove ${ and }
                
                try:
                    # Simple dot notation resolution
                    if "." in ref_path:
                        step_key, field_key = ref_path.split(".", 1)
                        if step_key in step_results:
                            step_result = step_results[step_key]
                            if isinstance(step_result, dict) and field_key in step_result:
                                resolved_params[key] = step_result[field_key]
                            else:
                                resolved_params[key] = value  # Keep original if can't resolve
                        else:
                            resolved_params[key] = value  # Keep original if can't resolve
                    else:
                        # Direct step reference
                        if ref_path in step_results:
                            resolved_params[key] = step_results[ref_path]
                        else:
                            resolved_params[key] = value  # Keep original if can't resolve
                            
                except Exception as e:
                    self.logger.warning(f"Failed to resolve parameter reference {value}: {e}")
                    resolved_params[key] = value  # Keep original on error
            else:
                resolved_params[key] = value
        
        return resolved_params
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a value in the execution context."""
        self.execution_context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from the execution context."""
        return self.execution_context.get(key, default)
    
    def clear_context(self) -> None:
        """Clear the execution context."""
        self.execution_context.clear()


__all__ = [
    "PluginOrchestrator",
    "PluginStep", 
    "PluginCall",
    "WorkflowResult",
]