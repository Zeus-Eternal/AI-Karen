"""
Plugin Orchestrator with Hook-Based Workflows

Extends existing plugin orchestration in plugin_marketplace/ to support hook-based workflows
that integrate with the unified hook system for enhanced plugin coordination and monitoring.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field

from ai_karen_engine.plugin_manager import get_plugin_manager
from ai_karen_engine.plugin_router import get_plugin_router
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.hooks.models import HookContext

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Represents a single step in a plugin workflow."""
    plugin_intent: str
    params: Dict[str, Any]
    conditions: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: float = 30.0
    depends_on: List[str] = field(default_factory=list)
    parallel: bool = False


@dataclass
class WorkflowDefinition:
    """Defines a complete plugin workflow."""
    name: str
    description: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = field(default_factory=dict)
    hooks: Dict[str, List[str]] = field(default_factory=dict)  # Hook type -> handler names
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowExecution:
    """Tracks the execution of a workflow."""
    workflow_name: str
    execution_id: str
    status: str = "pending"  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    step_results: Dict[str, Any] = field(default_factory=dict)


class PluginOrchestrator(HookMixin):
    """
    Enhanced plugin orchestrator with hook-based workflow support.
    
    Extends existing plugin orchestration capabilities with:
    - Hook-based workflow coordination
    - Advanced error handling and recovery
    - Workflow monitoring and metrics
    - Conditional execution logic
    - Parallel and sequential execution patterns
    """
    
    def __init__(self):
        super().__init__()
        self.name = "plugin_orchestrator"
        self.plugin_manager = get_plugin_manager()
        self.plugin_router = get_plugin_router()
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self._setup_workflow_hooks()
    
    def _setup_workflow_hooks(self):
        """Set up built-in workflow hooks."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._register_workflow_hooks())
        except RuntimeError:
            # No event loop running, skip hook registration for now
            pass
    
    async def _register_workflow_hooks(self):
        """Register standard workflow hooks."""
        try:
            # Workflow lifecycle hooks
            await self.register_hook(
                "workflow_started",
                self._on_workflow_started,
                priority=10,
                source_name="orchestrator_lifecycle"
            )
            
            await self.register_hook(
                "workflow_completed",
                self._on_workflow_completed,
                priority=10,
                source_name="orchestrator_lifecycle"
            )
            
            await self.register_hook(
                "workflow_failed",
                self._on_workflow_failed,
                priority=10,
                source_name="orchestrator_lifecycle"
            )
            
            # Step execution hooks
            await self.register_hook(
                "workflow_step_started",
                self._on_step_started,
                priority=20,
                source_name="orchestrator_steps"
            )
            
            await self.register_hook(
                "workflow_step_completed",
                self._on_step_completed,
                priority=20,
                source_name="orchestrator_steps"
            )
            
            logger.info("Workflow hooks registered successfully")
            
        except Exception as e:
            logger.warning(f"Failed to register workflow hooks: {e}")
    
    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """
        Register a new workflow definition.
        
        Args:
            workflow: Workflow definition to register
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate workflow
            if not self._validate_workflow(workflow):
                logger.error(f"Invalid workflow definition: {workflow.name}")
                return False
            
            self.workflows[workflow.name] = workflow
            
            # Trigger workflow registration hook
            await self.trigger_hook_safe(
                "workflow_registered",
                {
                    "workflow_name": workflow.name,
                    "workflow_definition": workflow,
                    "step_count": len(workflow.steps),
                    "has_parallel_steps": any(step.parallel for step in workflow.steps)
                }
            )
            
            logger.info(f"Workflow '{workflow.name}' registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register workflow '{workflow.name}': {e}")
            return False
    
    def _validate_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Validate workflow definition."""
        if not workflow.name or not workflow.steps:
            return False
        
        # Check for circular dependencies
        step_names = {i: step.plugin_intent for i, step in enumerate(workflow.steps)}
        
        for i, step in enumerate(workflow.steps):
            for dep in step.depends_on:
                if dep not in step_names.values():
                    logger.warning(f"Step '{step.plugin_intent}' depends on unknown step '{dep}'")
                    return False
        
        return True
    
    async def execute_workflow(
        self,
        workflow_name: str,
        context: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        Execute a registered workflow.
        
        Args:
            workflow_name: Name of workflow to execute
            context: Execution context and parameters
            user_context: User context for plugin execution
            
        Returns:
            WorkflowExecution tracking the execution
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")
        
        workflow = self.workflows[workflow_name]
        execution_id = f"exec_{workflow_name}_{datetime.utcnow().timestamp()}"
        
        execution = WorkflowExecution(
            workflow_name=workflow_name,
            execution_id=execution_id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Trigger workflow start hooks
            await self.trigger_hook_safe(
                "workflow_started",
                {
                    "workflow_name": workflow_name,
                    "execution_id": execution_id,
                    "context": context,
                    "user_context": user_context,
                    "step_count": len(workflow.steps)
                },
                user_context
            )
            
            # Execute workflow steps
            results = await self._execute_workflow_steps(
                workflow, execution, context, user_context
            )
            
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.results = results
            
            # Trigger completion hooks
            await self.trigger_hook_safe(
                "workflow_completed",
                {
                    "workflow_name": workflow_name,
                    "execution_id": execution_id,
                    "results": results,
                    "execution_time_ms": (
                        execution.completed_at - execution.started_at
                    ).total_seconds() * 1000
                },
                user_context
            )
            
            logger.info(f"Workflow '{workflow_name}' completed successfully")
            
        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.errors.append(str(e))
            
            # Trigger failure hooks
            await self.trigger_hook_safe(
                "workflow_failed",
                {
                    "workflow_name": workflow_name,
                    "execution_id": execution_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "partial_results": execution.step_results
                },
                user_context
            )
            
            logger.error(f"Workflow '{workflow_name}' failed: {e}")
            raise
        
        return execution
    
    async def _execute_workflow_steps(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        context: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute all steps in a workflow."""
        results = {}
        completed_steps = set()
        
        # Group steps by dependencies
        step_groups = self._group_steps_by_dependencies(workflow.steps)
        
        for group in step_groups:
            if any(step.parallel for step in group):
                # Execute parallel steps
                group_results = await self._execute_parallel_steps(
                    group, execution, context, user_context, results
                )
            else:
                # Execute sequential steps
                group_results = await self._execute_sequential_steps(
                    group, execution, context, user_context, results
                )
            
            results.update(group_results)
            completed_steps.update(step.plugin_intent for step in group)
        
        return results
    
    def _group_steps_by_dependencies(self, steps: List[WorkflowStep]) -> List[List[WorkflowStep]]:
        """Group workflow steps by their dependencies."""
        groups = []
        remaining_steps = steps.copy()
        completed_steps = set()
        
        while remaining_steps:
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = []
            for step in remaining_steps:
                if all(dep in completed_steps for dep in step.depends_on):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Circular dependency or missing dependency
                raise ValueError("Circular dependency detected in workflow steps")
            
            groups.append(ready_steps)
            completed_steps.update(step.plugin_intent for step in ready_steps)
            
            # Remove ready steps from remaining
            for step in ready_steps:
                remaining_steps.remove(step)
        
        return groups
    
    async def _execute_parallel_steps(
        self,
        steps: List[WorkflowStep],
        execution: WorkflowExecution,
        context: Dict[str, Any],
        user_context: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute steps in parallel."""
        tasks = []
        
        for step in steps:
            task = asyncio.create_task(
                self._execute_single_step(step, execution, context, user_context, previous_results)
            )
            tasks.append((step.plugin_intent, task))
        
        results = {}
        for step_name, task in tasks:
            try:
                result = await task
                results[step_name] = result
            except Exception as e:
                logger.error(f"Parallel step '{step_name}' failed: {e}")
                results[step_name] = {"error": str(e), "success": False}
        
        return results
    
    async def _execute_sequential_steps(
        self,
        steps: List[WorkflowStep],
        execution: WorkflowExecution,
        context: Dict[str, Any],
        user_context: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute steps sequentially."""
        results = {}
        
        for step in steps:
            try:
                result = await self._execute_single_step(
                    step, execution, context, user_context, {**previous_results, **results}
                )
                results[step.plugin_intent] = result
            except Exception as e:
                logger.error(f"Sequential step '{step.plugin_intent}' failed: {e}")
                results[step.plugin_intent] = {"error": str(e), "success": False}
                # Stop execution on failure in sequential mode
                break
        
        return results
    
    async def _execute_single_step(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution,
        context: Dict[str, Any],
        user_context: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Any:
        """Execute a single workflow step with retry logic."""
        step_context = {
            "step": step,
            "execution_id": execution.execution_id,
            "workflow_name": execution.workflow_name,
            "previous_results": previous_results
        }
        
        # Trigger step start hook
        await self.trigger_hook_safe(
            "workflow_step_started",
            step_context,
            user_context
        )
        
        last_error = None
        
        for attempt in range(step.max_retries + 1):
            try:
                # Check step conditions
                if not self._check_step_conditions(step, context, previous_results):
                    logger.info(f"Step '{step.plugin_intent}' conditions not met, skipping")
                    return {"skipped": True, "reason": "conditions_not_met"}
                
                # Prepare step parameters
                step_params = self._prepare_step_params(step, context, previous_results)
                
                # Execute plugin
                result = await asyncio.wait_for(
                    self.plugin_manager.run_plugin(
                        step.plugin_intent,
                        step_params,
                        user_context
                    ),
                    timeout=step.timeout_seconds
                )
                
                # Store step result
                execution.step_results[step.plugin_intent] = result
                
                # Trigger step completion hook
                await self.trigger_hook_safe(
                    "workflow_step_completed",
                    {
                        **step_context,
                        "result": result,
                        "attempt": attempt + 1,
                        "success": True
                    },
                    user_context
                )
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Step '{step.plugin_intent}' attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < step.max_retries:
                    # Wait before retry
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # Final failure
                    await self.trigger_hook_safe(
                        "workflow_step_failed",
                        {
                            **step_context,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "attempts": attempt + 1
                        },
                        user_context
                    )
        
        raise last_error
    
    def _check_step_conditions(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> bool:
        """Check if step conditions are satisfied."""
        if not step.conditions:
            return True
        
        # Simple condition evaluation
        for key, expected_value in step.conditions.items():
            if key in context:
                actual_value = context[key]
            elif key in previous_results:
                actual_value = previous_results[key]
            else:
                return False
            
            if actual_value != expected_value:
                return False
        
        return True
    
    def _prepare_step_params(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare parameters for step execution."""
        params = step.params.copy()
        
        # Substitute context variables
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${"):
                var_name = value[2:-1]  # Remove ${ and }
                if var_name in context:
                    params[key] = context[var_name]
                elif var_name in previous_results:
                    params[key] = previous_results[var_name]
        
        return params
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the status of a workflow execution."""
        return self.executions.get(execution_id)
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow."""
        execution = self.executions.get(execution_id)
        if not execution or execution.status != "running":
            return False
        
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        
        await self.trigger_hook_safe(
            "workflow_cancelled",
            {
                "execution_id": execution_id,
                "workflow_name": execution.workflow_name,
                "partial_results": execution.step_results
            }
        )
        
        return True
    
    def list_workflows(self) -> List[str]:
        """List all registered workflows."""
        return list(self.workflows.keys())
    
    def get_workflow_definition(self, workflow_name: str) -> Optional[WorkflowDefinition]:
        """Get workflow definition by name."""
        return self.workflows.get(workflow_name)
    
    # Hook handlers
    async def _on_workflow_started(self, context: HookContext) -> Dict[str, Any]:
        """Handle workflow started event."""
        return {
            "event": "workflow_started",
            "workflow_name": context.data.get("workflow_name"),
            "execution_id": context.data.get("execution_id"),
            "timestamp": context.timestamp.isoformat()
        }
    
    async def _on_workflow_completed(self, context: HookContext) -> Dict[str, Any]:
        """Handle workflow completed event."""
        return {
            "event": "workflow_completed",
            "workflow_name": context.data.get("workflow_name"),
            "execution_id": context.data.get("execution_id"),
            "execution_time_ms": context.data.get("execution_time_ms"),
            "timestamp": context.timestamp.isoformat()
        }
    
    async def _on_workflow_failed(self, context: HookContext) -> Dict[str, Any]:
        """Handle workflow failed event."""
        return {
            "event": "workflow_failed",
            "workflow_name": context.data.get("workflow_name"),
            "execution_id": context.data.get("execution_id"),
            "error": context.data.get("error"),
            "timestamp": context.timestamp.isoformat()
        }
    
    async def _on_step_started(self, context: HookContext) -> Dict[str, Any]:
        """Handle workflow step started event."""
        step = context.data.get("step")
        return {
            "event": "step_started",
            "step_name": step.plugin_intent if step else "unknown",
            "execution_id": context.data.get("execution_id"),
            "timestamp": context.timestamp.isoformat()
        }
    
    async def _on_step_completed(self, context: HookContext) -> Dict[str, Any]:
        """Handle workflow step completed event."""
        step = context.data.get("step")
        return {
            "event": "step_completed",
            "step_name": step.plugin_intent if step else "unknown",
            "execution_id": context.data.get("execution_id"),
            "success": context.data.get("success", False),
            "timestamp": context.timestamp.isoformat()
        }


# Singleton accessor
_plugin_orchestrator: Optional[PluginOrchestrator] = None

def get_plugin_orchestrator() -> PluginOrchestrator:
    """Get the singleton plugin orchestrator instance."""
    global _plugin_orchestrator
    if _plugin_orchestrator is None:
        _plugin_orchestrator = PluginOrchestrator()
    return _plugin_orchestrator


__all__ = [
    "PluginOrchestrator",
    "WorkflowStep",
    "WorkflowDefinition", 
    "WorkflowExecution",
    "get_plugin_orchestrator"
]