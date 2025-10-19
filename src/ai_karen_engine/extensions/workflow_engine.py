"""
Advanced workflow execution engine for extensions.

This module provides a powerful workflow execution engine that can
run complex workflows with conditional logic, error handling, and
parallel execution.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from ai_karen_engine.core.predictors import predictor_registry, run_predictor

# Import will be done at runtime to avoid circular imports


class StepType(Enum):
    """Types of workflow steps."""

    PLUGIN = "plugin"  # Execute a plugin
    CONDITION = "condition"  # Conditional branching
    PARALLEL = "parallel"  # Parallel execution
    LOOP = "loop"  # Loop execution
    WAIT = "wait"  # Wait for a condition
    TRANSFORM = "transform"  # Transform data
    MCP_TOOL = "mcp_tool"  # Execute an MCP tool
    ROUTING = "routing"  # Execute a CORTEX routing action


class StepStatus(Enum):
    """Status of a workflow step execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """Status of a workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""

    id: str
    type: StepType
    config: Dict[str, Any]
    next_steps: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # Condition expression for branching
    error_handler: Optional[str] = None  # Step to execute on error
    retry_config: Optional[Dict[str, Any]] = None  # Retry configuration
    timeout_seconds: Optional[int] = None  # Step timeout


@dataclass
class WorkflowStepExecution:
    """Execution state of a workflow step."""

    step_id: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    inputs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Definition of a workflow."""

    id: str
    name: str
    description: Optional[str] = None
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    start_step: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None
    max_retries: int = 0
    retry_delay_seconds: int = 5


@dataclass
class WorkflowExecution:
    """Execution state of a workflow."""

    workflow_id: str
    execution_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    step_executions: Dict[str, WorkflowStepExecution] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    current_step_id: Optional[str] = None


class WorkflowEngine:
    """
    Advanced workflow execution engine.

    This engine can execute complex workflows with conditional logic,
    error handling, parallel execution, and more.
    """

    def __init__(self, plugin_orchestrator: Any):
        """
        Initialize the workflow engine.

        Args:
            plugin_orchestrator: Plugin orchestrator for executing plugins
        """
        self.plugin_orchestrator = plugin_orchestrator
        self.logger = logging.getLogger("extension.workflow_engine")

        # Workflow storage
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.workflow_executions: Dict[str, WorkflowExecution] = {}

        # Function registry for evaluating conditions and transformations
        self.function_registry: Dict[str, Callable] = {}

        # MCP tool registry
        self.mcp_tool_registry: Dict[str, Dict[str, Any]] = {}

    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """
        Register a workflow definition.

        Args:
            workflow: Workflow definition

        Returns:
            Workflow ID
        """
        self.workflow_definitions[workflow.id] = workflow
        self.logger.info(f"Registered workflow: {workflow.id} - {workflow.name}")
        return workflow.id

    def register_function(self, name: str, func: Callable) -> None:
        """
        Register a function for use in conditions and transformations.

        Args:
            name: Function name
            func: Function implementation
        """
        self.function_registry[name] = func
        self.logger.debug(f"Registered function: {name}")

    def register_mcp_tool(
        self, service_name: str, tool_name: str, tool_info: Dict[str, Any]
    ) -> None:
        """
        Register an MCP tool for use in workflows.

        Args:
            service_name: MCP service name
            tool_name: Tool name
            tool_info: Tool information
        """
        if service_name not in self.mcp_tool_registry:
            self.mcp_tool_registry[service_name] = {}

        self.mcp_tool_registry[service_name][tool_name] = tool_info
        self.logger.debug(f"Registered MCP tool: {service_name}.{tool_name}")

    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any] = None,
        execution_id: Optional[str] = None,
        user_context: Dict[str, Any] = None,
    ) -> WorkflowExecution:
        """
        Execute a workflow.

        Args:
            workflow_id: Workflow ID
            inputs: Input variables
            execution_id: Optional execution ID
            user_context: User context for plugin execution

        Returns:
            Workflow execution state

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"Workflow not found: {workflow_id}")

        workflow = self.workflow_definitions[workflow_id]

        # Create execution ID if not provided
        if not execution_id:
            execution_id = f"exec_{int(time.time())}_{workflow_id}"

        # Initialize execution state
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            execution_id=execution_id,
            status=WorkflowStatus.PENDING,
            variables=inputs or {},
        )

        # Store execution state
        self.workflow_executions[execution_id] = execution

        # Start execution in background
        asyncio.create_task(
            self._execute_workflow_async(workflow, execution, user_context or {})
        )

        return execution

    async def _execute_workflow_async(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        user_context: Dict[str, Any],
    ) -> None:
        """
        Execute a workflow asynchronously.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            user_context: User context for plugin execution
        """
        try:
            # Update execution state
            execution.status = WorkflowStatus.RUNNING
            execution.start_time = time.time()

            # Determine start step
            start_step_id = workflow.start_step
            if not start_step_id and workflow.steps:
                # Use first step if start step not specified
                start_step_id = next(iter(workflow.steps.keys()))

            if not start_step_id:
                raise ValueError("No start step defined for workflow")

            # Execute workflow starting from the start step
            await self._execute_step(workflow, execution, start_step_id, user_context)

            # Check if workflow completed successfully
            if execution.status != WorkflowStatus.FAILED:
                execution.status = WorkflowStatus.COMPLETED

            execution.end_time = time.time()

            self.logger.info(
                f"Workflow {workflow.id} execution {execution.execution_id} "
                f"completed with status: {execution.status.value}"
            )

        except Exception as e:
            # Handle workflow-level error
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.end_time = time.time()

            self.logger.error(
                f"Workflow {workflow.id} execution {execution.execution_id} failed: {e}"
            )

    async def _execute_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step_id: str,
        user_context: Dict[str, Any],
    ) -> Any:
        """
        Execute a single workflow step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step_id: Step ID to execute
            user_context: User context for plugin execution

        Returns:
            Step result

        Raises:
            ValueError: If step not found
        """
        if step_id not in workflow.steps:
            raise ValueError(f"Step not found: {step_id}")

        step = workflow.steps[step_id]

        # Initialize step execution if not exists
        if step_id not in execution.step_executions:
            execution.step_executions[step_id] = WorkflowStepExecution(step_id=step_id)

        step_execution = execution.step_executions[step_id]

        # Update execution state
        execution.current_step_id = step_id
        step_execution.status = StepStatus.RUNNING
        step_execution.start_time = time.time()

        self.logger.debug(f"Executing step {step_id} of type {step.type.value}")

        try:
            # Execute step based on type
            if step.type == StepType.PLUGIN:
                result = await self._execute_plugin_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.CONDITION:
                result = await self._execute_condition_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.PARALLEL:
                result = await self._execute_parallel_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.LOOP:
                result = await self._execute_loop_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.WAIT:
                result = await self._execute_wait_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.TRANSFORM:
                result = await self._execute_transform_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.MCP_TOOL:
                result = await self._execute_mcp_tool_step(
                    workflow, execution, step, step_execution, user_context
                )
            elif step.type == StepType.ROUTING:
                result = await self._execute_routing_step(
                    workflow, execution, step, step_execution, user_context
                )
            else:
                raise ValueError(f"Unsupported step type: {step.type}")

            # Update step execution state
            step_execution.status = StepStatus.COMPLETED
            step_execution.result = result
            step_execution.end_time = time.time()

            # Execute next steps
            for next_step_id in step.next_steps:
                await self._execute_step(
                    workflow, execution, next_step_id, user_context
                )

            return result

        except Exception as e:
            # Handle step-level error
            step_execution.status = StepStatus.FAILED
            step_execution.error = str(e)
            step_execution.end_time = time.time()

            self.logger.error(f"Step {step_id} execution failed: {e}")

            # Check if retry is configured
            if (
                step.retry_config
                and step_execution.retry_count < step.retry_config.get("max_retries", 0)
            ):
                # Retry step after delay
                retry_delay = step.retry_config.get("delay_seconds", 1)
                step_execution.retry_count += 1

                self.logger.info(
                    f"Retrying step {step_id} (attempt {step_execution.retry_count}) "
                    f"after {retry_delay}s delay"
                )

                await asyncio.sleep(retry_delay)
                return await self._execute_step(
                    workflow, execution, step_id, user_context
                )

            # Check if error handler is configured
            if step.error_handler:
                self.logger.info(
                    f"Executing error handler {step.error_handler} for step {step_id}"
                )
                return await self._execute_step(
                    workflow, execution, step.error_handler, user_context
                )

            # No error handler, propagate error
            execution.status = WorkflowStatus.FAILED
            execution.error = f"Step {step_id} failed: {e}"
            raise

    async def _execute_plugin_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> Any:
        """
        Execute a plugin step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            Plugin result
        """
        # Extract plugin configuration
        intent = step.config.get("intent")
        if not intent:
            raise ValueError(f"Plugin step {step.id} missing intent")

        # Get parameters and resolve variables
        params = step.config.get("params", {})
        resolved_params = self._resolve_variables(params, execution.variables)

        # Store inputs for debugging
        step_execution.inputs = {
            "intent": intent,
            "params": resolved_params,
        }

        # Execute plugin
        result = await self.plugin_orchestrator.execute_plugin(
            intent=intent, params=resolved_params, user_context=user_context
        )

        # Store result in variables if output_key is specified
        output_key = step.config.get("output_key")
        if output_key:
            execution.variables[output_key] = result

        return result

    async def _execute_routing_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> Any:
        """Execute a routing step via CORTEX predictor registry."""

        action = step.config.get("action")
        if not action:
            raise ValueError(f"Routing step {step.id} missing action")

        handler = predictor_registry.get(action)
        if handler is None:
            raise ValueError(f"Routing action '{action}' is not registered")

        query_value = step.config.get("query", "")
        resolved_query = self._resolve_variables(query_value, execution.variables)
        context_value = step.config.get("context", {})
        resolved_context = self._resolve_variables(context_value, execution.variables)

        step_execution.inputs = {
            "action": action,
            "query": resolved_query,
            "context": resolved_context,
        }

        result = await run_predictor(
            handler,
            user_context,
            resolved_query,
            resolved_context if isinstance(resolved_context, dict) else {},
        )

        output_key = step.config.get("output_key")
        if output_key:
            execution.variables[output_key] = result

        return result

    async def _execute_condition_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> bool:
        """
        Execute a condition step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            Condition result (True/False)
        """
        # Extract condition expression
        condition = step.config.get("condition")
        if not condition:
            raise ValueError(f"Condition step {step.id} missing condition")

        # Store inputs for debugging
        step_execution.inputs = {
            "condition": condition,
            "variables": execution.variables,
        }

        # Evaluate condition
        result = self._evaluate_condition(condition, execution.variables)

        # Determine next step based on condition result
        if result:
            next_step = step.config.get("true_step")
            if next_step:
                step.next_steps = [next_step]
        else:
            next_step = step.config.get("false_step")
            if next_step:
                step.next_steps = [next_step]

        return result

    async def _execute_parallel_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> List[Any]:
        """
        Execute multiple steps in parallel.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            List of step results
        """
        # Extract parallel steps
        parallel_steps = step.config.get("steps", [])
        if not parallel_steps:
            raise ValueError(f"Parallel step {step.id} has no steps defined")

        # Store inputs for debugging
        step_execution.inputs = {"steps": parallel_steps}

        # Execute steps in parallel
        tasks = []
        for parallel_step_id in parallel_steps:
            # Create a copy of the execution for each parallel branch
            branch_execution = WorkflowExecution(
                workflow_id=execution.workflow_id,
                execution_id=f"{execution.execution_id}_parallel_{parallel_step_id}",
                status=WorkflowStatus.RUNNING,
                variables=execution.variables.copy(),
                step_executions={},
            )

            # Execute step
            task = asyncio.create_task(
                self._execute_step(
                    workflow, branch_execution, parallel_step_id, user_context
                )
            )
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Parallel step {parallel_steps[i]} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)

        # Store results in variables if output_key is specified
        output_key = step.config.get("output_key")
        if output_key:
            execution.variables[output_key] = processed_results

        return processed_results

    async def _execute_loop_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> List[Any]:
        """
        Execute a loop step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            List of iteration results
        """
        # Extract loop configuration
        loop_type = step.config.get("loop_type", "items")
        target_step = step.config.get("target_step")

        if not target_step:
            raise ValueError(f"Loop step {step.id} missing target_step")

        # Store inputs for debugging
        step_execution.inputs = {"loop_type": loop_type, "target_step": target_step}

        results = []

        if loop_type == "items":
            # Loop over items in a collection
            items = step.config.get("items", [])
            items_var = step.config.get("items_var")

            if items_var:
                # Get items from variable
                items = execution.variables.get(items_var, [])

            step_execution.inputs["items"] = items

            # Execute target step for each item
            for i, item in enumerate(items):
                # Add item to variables
                item_var = step.config.get("item_var", "item")
                index_var = step.config.get("index_var", "index")

                execution.variables[item_var] = item
                execution.variables[index_var] = i

                # Execute target step
                result = await self._execute_step(
                    workflow, execution, target_step, user_context
                )
                results.append(result)

                # Check for break condition
                break_condition = step.config.get("break_condition")
                if break_condition and self._evaluate_condition(
                    break_condition, execution.variables
                ):
                    self.logger.debug(
                        f"Loop step {step.id} break condition met after {i+1} iterations"
                    )
                    break

        elif loop_type == "count":
            # Loop a fixed number of times
            count = step.config.get("count", 1)
            step_execution.inputs["count"] = count

            # Execute target step count times
            for i in range(count):
                # Add index to variables
                index_var = step.config.get("index_var", "index")
                execution.variables[index_var] = i

                # Execute target step
                result = await self._execute_step(
                    workflow, execution, target_step, user_context
                )
                results.append(result)

                # Check for break condition
                break_condition = step.config.get("break_condition")
                if break_condition and self._evaluate_condition(
                    break_condition, execution.variables
                ):
                    self.logger.debug(
                        f"Loop step {step.id} break condition met after {i+1} iterations"
                    )
                    break

        elif loop_type == "while":
            # Loop while condition is true
            condition = step.config.get("condition")
            if not condition:
                raise ValueError(f"While loop step {step.id} missing condition")

            step_execution.inputs["condition"] = condition

            # Execute target step while condition is true
            iteration = 0
            max_iterations = step.config.get("max_iterations", 100)  # Safety limit

            while self._evaluate_condition(condition, execution.variables):
                # Add iteration to variables
                index_var = step.config.get("index_var", "index")
                execution.variables[index_var] = iteration

                # Execute target step
                result = await self._execute_step(
                    workflow, execution, target_step, user_context
                )
                results.append(result)

                iteration += 1
                if iteration >= max_iterations:
                    self.logger.warning(
                        f"While loop step {step.id} reached max iterations ({max_iterations})"
                    )
                    break

        else:
            raise ValueError(f"Unsupported loop type: {loop_type}")

        # Store results in variables if output_key is specified
        output_key = step.config.get("output_key")
        if output_key:
            execution.variables[output_key] = results

        return results

    async def _execute_wait_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a wait step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            Wait result
        """
        wait_type = step.config.get("wait_type", "delay")

        if wait_type == "delay":
            # Simple delay
            delay_seconds = step.config.get("delay_seconds", 1)
            step_execution.inputs = {"delay_seconds": delay_seconds}

            await asyncio.sleep(delay_seconds)
            return {"waited_seconds": delay_seconds}

        elif wait_type == "condition":
            # Wait for condition to be true
            condition = step.config.get("condition")
            if not condition:
                raise ValueError(f"Wait step {step.id} missing condition")

            check_interval = step.config.get("check_interval_seconds", 1)
            max_wait_seconds = step.config.get("max_wait_seconds", 60)

            step_execution.inputs = {
                "condition": condition,
                "check_interval_seconds": check_interval,
                "max_wait_seconds": max_wait_seconds,
            }

            start_time = time.time()
            while time.time() - start_time < max_wait_seconds:
                if self._evaluate_condition(condition, execution.variables):
                    waited_seconds = time.time() - start_time
                    return {"condition_met": True, "waited_seconds": waited_seconds}

                await asyncio.sleep(check_interval)

            # Timeout
            return {"condition_met": False, "waited_seconds": max_wait_seconds}

        else:
            raise ValueError(f"Unsupported wait type: {wait_type}")

    async def _execute_transform_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> Any:
        """
        Execute a transform step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            Transform result
        """
        transform_type = step.config.get("transform_type", "function")

        if transform_type == "function":
            # Execute a registered function
            function_name = step.config.get("function_name")
            if not function_name or function_name not in self.function_registry:
                raise ValueError(
                    f"Transform step {step.id} missing or unknown function: {function_name}"
                )

            # Get function arguments
            args = step.config.get("args", [])
            kwargs = step.config.get("kwargs", {})

            # Resolve variables in arguments
            resolved_args = [
                self._resolve_variables(arg, execution.variables) for arg in args
            ]
            resolved_kwargs = {
                k: self._resolve_variables(v, execution.variables)
                for k, v in kwargs.items()
            }

            step_execution.inputs = {
                "function_name": function_name,
                "args": resolved_args,
                "kwargs": resolved_kwargs,
            }

            # Execute function
            func = self.function_registry[function_name]
            result = func(*resolved_args, **resolved_kwargs)

            # Store result in variables if output_key is specified
            output_key = step.config.get("output_key")
            if output_key:
                execution.variables[output_key] = result

            return result

        else:
            raise ValueError(f"Unsupported transform type: {transform_type}")

    async def _execute_mcp_tool_step(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        step: WorkflowStep,
        step_execution: WorkflowStepExecution,
        user_context: Dict[str, Any],
    ) -> Any:
        """
        Execute an MCP tool step.

        Args:
            workflow: Workflow definition
            execution: Workflow execution state
            step: Step definition
            step_execution: Step execution state
            user_context: User context for plugin execution

        Returns:
            MCP tool result
        """
        service_name = step.config.get("service_name")
        tool_name = step.config.get("tool_name")

        if not service_name or not tool_name:
            raise ValueError(
                f"MCP tool step {step.id} missing service_name or tool_name"
            )

        # Check if tool is registered
        if (
            service_name not in self.mcp_tool_registry
            or tool_name not in self.mcp_tool_registry[service_name]
        ):
            raise ValueError(f"MCP tool {service_name}.{tool_name} not registered")

        # Get tool arguments
        args = step.config.get("args", {})
        resolved_args = self._resolve_variables(args, execution.variables)

        step_execution.inputs = {
            "service_name": service_name,
            "tool_name": tool_name,
            "args": resolved_args,
        }

        # For now, we'll simulate MCP tool execution
        # In a real implementation, this would call the actual MCP tool
        result = {
            "service": service_name,
            "tool": tool_name,
            "args": resolved_args,
            "result": "MCP tool executed successfully (simulated)",
        }

        # Store result in variables if output_key is specified
        output_key = step.config.get("output_key")
        if output_key:
            execution.variables[output_key] = result

        return result

    def _resolve_variables(self, value: Any, variables: Dict[str, Any]) -> Any:
        """
        Resolve variables in a value.

        Args:
            value: Value that may contain variable references
            variables: Available variables

        Returns:
            Value with variables resolved
        """
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            return variables.get(var_name, value)
        elif isinstance(value, dict):
            return {k: self._resolve_variables(v, variables) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_variables(item, variables) for item in value]
        else:
            return value

    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Safely evaluate a condition expression.

        The method substitutes variables of the form ``${var}`` with their
        ``repr`` values and then parses the expression using ``ast``. Only a
        subset of Python expressions is supported (boolean operators,
        comparisons, arithmetic and unary operations). If evaluation fails the
        method returns ``False``.

        Args:
            condition: Condition expression
            variables: Available variables

        Returns:
            ``True`` or ``False`` based on the evaluated expression.
        """

        import ast
        import operator
        import re

        def replace_var(match: re.Match[str]) -> str:
            name = match.group(1)
            if name in variables:
                return repr(variables[name])
            return "None"

        resolved_condition = re.sub(r"\$\{(\w+)\}", replace_var, condition)

        operators: Dict[type, Any] = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
        }

        def eval_node(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return eval_node(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.UnaryOp):
                if isinstance(node.op, ast.Not):
                    return not eval_node(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +eval_node(node.operand)
                if isinstance(node.op, ast.USub):
                    return -eval_node(node.operand)
                raise ValueError("unsupported unary operator")
            if isinstance(node, ast.BoolOp):
                if isinstance(node.op, ast.And):
                    return all(eval_node(value) for value in node.values)
                if isinstance(node.op, ast.Or):
                    return any(eval_node(value) for value in node.values)
                raise ValueError("unsupported boolean operator")
            if isinstance(node, ast.BinOp):
                op_func = operators.get(type(node.op))
                if op_func is None:
                    raise ValueError("unsupported binary operator")
                return op_func(eval_node(node.left), eval_node(node.right))
            if isinstance(node, ast.Compare):
                left = eval_node(node.left)
                for op, comparator in zip(node.ops, node.comparators):
                    right = eval_node(comparator)
                    if isinstance(op, ast.Eq) and not left == right:
                        return False
                    if isinstance(op, ast.NotEq) and not left != right:
                        return False
                    if isinstance(op, ast.Lt) and not left < right:
                        return False
                    if isinstance(op, ast.Gt) and not left > right:
                        return False
                    if isinstance(op, ast.LtE) and not left <= right:
                        return False
                    if isinstance(op, ast.GtE) and not left >= right:
                        return False
                    left = right
                return True
            raise ValueError("unsupported expression")

        try:
            # Handle simple comparisons
            if " == " in resolved_condition:
                left, right = resolved_condition.split(" == ", 1)
                return left.strip().strip('"\'') == right.strip().strip('"\'')
            elif " != " in resolved_condition:
                left, right = resolved_condition.split(" != ", 1)
                return left.strip().strip('"\'') != right.strip().strip('"\'')
            elif " > " in resolved_condition:
                left, right = resolved_condition.split(" > ", 1)
                return float(left.strip()) > float(right.strip())
            elif " < " in resolved_condition:
                left, right = resolved_condition.split(" < ", 1)
                return float(left.strip()) < float(right.strip())
            else:
                # Try to evaluate as boolean
                return bool(eval(resolved_condition))
        except Exception:
            # Default to False if evaluation fails
            return False


# Export the workflow engine
__all__ = [
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowStep",
    "WorkflowExecution",
    "StepType",
    "StepStatus",
    "WorkflowStatus",
]
