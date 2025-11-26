"""
Agent Orchestrator Service

This service is the top-level brain for multi-agent workflows in the Kari system.
It coordinates task distribution, execution, and result aggregation across multiple agents.
"""

from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent."""
    id: str
    type: str
    input_data: Dict[str, Any]
    priority: int = 0
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentExecutionResult:
    """Represents the result of an agent execution."""
    task_id: str
    agent_id: str
    success: bool
    output_data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentOrchestrator:
    """
    Top-level orchestrator for multi-agent workflows.
    
    This class is responsible for:
    - Coordinating task distribution across multiple agents
    - Managing agent execution pipelines
    - Aggregating results from multiple agents
    - Handling agent failures and fallbacks
    """
    
    def __init__(self):
        self._agents = {}
        self._task_queue = []
        self._running_tasks = {}
        self._completed_tasks = {}
        self._failed_tasks = {}
        
    def register_agent(self, agent_id: str, agent_instance: Any) -> None:
        """Register an agent with the orchestrator."""
        self._agents[agent_id] = agent_instance
        logger.info(f"Registered agent: {agent_id}")
        
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
        else:
            logger.warning(f"Attempted to unregister non-existent agent: {agent_id}")
    
    def submit_task(self, task: AgentTask) -> str:
        """Submit a task for execution by an appropriate agent."""
        self._task_queue.append(task)
        logger.info(f"Submitted task: {task.id} of type {task.type}")
        return task.id
    
    def execute_task(self, task: AgentTask, agent_id: Optional[str] = None) -> AgentExecutionResult:
        """
        Execute a task using a specific agent or automatically select one.
        
        Args:
            task: The task to execute
            agent_id: Optional specific agent to use. If None, agent will be selected automatically.
            
        Returns:
            The result of the execution
        """
        import time
        start_time = time.time()
        
        # Select agent if not specified
        if agent_id is None:
            agent_id = self._select_agent_for_task(task)
            if agent_id is None:
                return AgentExecutionResult(
                    task_id=task.id,
                    agent_id="none",
                    success=False,
                    output_data={},
                    error_message="No suitable agent found for task"
                )
        
        # Get agent instance
        agent = self._agents.get(agent_id)
        if agent is None:
            return AgentExecutionResult(
                task_id=task.id,
                agent_id=agent_id,
                success=False,
                output_data={},
                error_message=f"Agent {agent_id} not found"
            )
        
        # Track running task
        self._running_tasks[task.id] = (agent_id, start_time)
        
        try:
            # Execute task
            result_data = self._execute_with_agent(agent, task)
            
            execution_time = time.time() - start_time
            
            # Create result
            result = AgentExecutionResult(
                task_id=task.id,
                agent_id=agent_id,
                success=True,
                output_data=result_data,
                execution_time=execution_time
            )
            
            # Store completed task
            self._completed_tasks[task.id] = result
            
            logger.info(f"Task {task.id} completed successfully by agent {agent_id}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Create failed result
            result = AgentExecutionResult(
                task_id=task.id,
                agent_id=agent_id,
                success=False,
                output_data={},
                error_message=str(e),
                execution_time=execution_time
            )
            
            # Store failed task
            self._failed_tasks[task.id] = result
            
            logger.error(f"Task {task.id} failed with agent {agent_id}: {str(e)}")
            return result
            
        finally:
            # Remove from running tasks
            if task.id in self._running_tasks:
                del self._running_tasks[task.id]
    
    def execute_workflow(self, tasks: List[AgentTask]) -> Dict[str, AgentExecutionResult]:
        """
        Execute a workflow of multiple tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Dictionary mapping task IDs to execution results
        """
        results = {}
        
        # Execute each task
        for task in tasks:
            result = self.execute_task(task)
            results[task.id] = result
            
        return results
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task (queued, running, completed, failed, not_found)."""
        if task_id in [t.id for t in self._task_queue]:
            return "queued"
        elif task_id in self._running_tasks:
            return "running"
        elif task_id in self._completed_tasks:
            return "completed"
        elif task_id in self._failed_tasks:
            return "failed"
        else:
            return "not_found"
    
    def get_task_result(self, task_id: str) -> Optional[AgentExecutionResult]:
        """Get the result of a completed or failed task."""
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        elif task_id in self._failed_tasks:
            return self._failed_tasks[task_id]
        else:
            return None
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status information for an agent."""
        if agent_id not in self._agents:
            return {"status": "not_found"}
        
        # Count tasks by status for this agent
        queued_count = sum(1 for task in self._task_queue if self._select_agent_for_task(task) == agent_id)
        running_count = sum(1 for task_id, (aid, _) in self._running_tasks.items() if aid == agent_id)
        completed_count = sum(1 for task_id, result in self._completed_tasks.items() if result.agent_id == agent_id)
        failed_count = sum(1 for task_id, result in self._failed_tasks.items() if result.agent_id == agent_id)
        
        return {
            "status": "active",
            "queued_tasks": queued_count,
            "running_tasks": running_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count
        }
    
    def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all agents."""
        return {agent_id: self.get_agent_status(agent_id) for agent_id in self._agents}
    
    def _select_agent_for_task(self, task: AgentTask) -> Optional[str]:
        """
        Select the most appropriate agent for a task.
        
        This is a simple implementation that could be enhanced with more sophisticated
        agent selection logic based on capabilities, load, etc.
        """
        # Simple strategy: find first agent that can handle the task type
        for agent_id, agent in self._agents.items():
            if hasattr(agent, 'can_handle_task') and agent.can_handle_task(task.type):
                return agent_id
        
        # If no agent explicitly can handle the task, use the first available agent
        if self._agents:
            return next(iter(self._agents.keys()))
        
        return None
    
    def _execute_with_agent(self, agent: Any, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task with a specific agent.
        
        This method handles the actual execution of the task by the agent,
        including initialization, execution, and finalization if needed.
        """
        # Initialize agent if needed
        if hasattr(agent, 'initialize'):
            agent.initialize(task.metadata or {})
        
        # Execute the task
        if hasattr(agent, 'execute'):
            result = agent.execute({
                "id": task.id,
                "type": task.type,
                "input_data": task.input_data,
                "priority": task.priority,
                "timeout": task.timeout,
                "metadata": task.metadata
            })
        else:
            raise ValueError(f"Agent does not have execute method")
        
        # Finalize agent if needed
        if hasattr(agent, 'finalize'):
            agent.finalize(result)
        
        return result