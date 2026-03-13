"""
Agent UI Service for CoPilot integration.

This service acts as the bridge between CoPilot UI and the agent architecture,
translating UI interactions to AgentTask objects and handling execution modes.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union

from ai_karen_engine.copilotkit.models import (
    AgentTask,
    SendMessageRequest,
    SendMessageResponse,
    CreateDeepTaskRequest,
    CreateDeepTaskResponse,
    GetTaskProgressRequest,
    GetTaskProgressResponse,
    CancelTaskRequest,
    CancelTaskResponse,
    ExecutionMode,
    TaskType,
    TaskStatus,
    TaskStep,
    AgentUIServiceError
)

logger = logging.getLogger(__name__)


class AgentUIService:
    """
    Bridge between CoPilot UI and Agent Architecture.
    
    Responsibilities:
    - Translate UI interactions to AgentTask objects
    - Maintain session state
    - Route requests to appropriate agent components
    - Format responses for UI consumption
    - Handle different execution modes (Native, LangGraph, DeepAgents)
    """
    
    def __init__(self, agent_orchestrator=None, thread_manager=None, session_manager=None):
        """Initialize Agent UI Service with dependencies."""
        self.agent_orchestrator = agent_orchestrator
        self.thread_manager = thread_manager
        self.session_manager = session_manager
        
        # In-memory storage for tasks (in production, this would be persistent)
        self._tasks: Dict[str, AgentTask] = {}
        self._task_progress: Dict[str, GetTaskProgressResponse] = {}
        
        # Task execution tracking
        self._running_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info("Agent UI Service initialized")
    
    async def send_message(self, request: SendMessageRequest) -> SendMessageResponse:
        """
        Send a message to an agent.
        
        Args:
            request: Message send request with session info and content
            
        Returns:
            SendMessageResponse with agent response and execution metadata
        """
        try:
            logger.info(f"Processing message for session {request.session_id}")
            
            # Create AgentTask from request
            agent_task = self._create_agent_task_from_message(request)
            
            # Store task
            self._tasks[agent_task.task_id] = agent_task
            
            # Route to appropriate execution mode
            execution_mode = await self._determine_execution_mode(agent_task)
            agent_task.execution_mode = execution_mode
            
            logger.info(f"Executing task {agent_task.task_id} in {execution_mode} mode")
            
            # Execute task based on mode
            result = await self._execute_task(agent_task)
            
            # Create response
            response = SendMessageResponse(
                success=True,
                task_id=agent_task.task_id,
                content=result.get("content", "Task completed successfully"),
                execution_mode=execution_mode,
                execution_metadata=result.get("metadata", {}),
                thread_id=agent_task.thread_id
            )
            
            logger.info(f"Message processed successfully for task {agent_task.task_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return SendMessageResponse(
                success=False,
                content=f"Error processing message: {str(e)}",
                execution_mode=ExecutionMode.NATIVE,
                execution_metadata={"error": str(e)}
            )
    
    async def create_deep_task(self, request: CreateDeepTaskRequest) -> CreateDeepTaskResponse:
        """
        Create a deep task that uses DeepAgents.
        
        Args:
            request: Deep task creation request
            
        Returns:
            CreateDeepTaskResponse with task ID and status
        """
        try:
            logger.info(f"Creating deep task for session {request.session_id}")
            
            # Create AgentTask with DeepAgents execution mode
            agent_task = AgentTask(
                task_id=str(uuid.uuid4()),
                session_id=request.session_id,
                task_type=request.task_type,
                content=request.content,
                context=request.context,
                execution_mode=ExecutionMode.DEEPAGENT,
                priority=request.priority,
                timeout_seconds=request.timeout_seconds,
                user_id=request.user_id,
                tenant_id=request.tenant_id
            )
            
            # Store task
            self._tasks[agent_task.task_id] = agent_task
            
            # Initialize task progress
            progress_response = GetTaskProgressResponse(
                task_id=agent_task.task_id,
                status=TaskStatus.PENDING,
                progress_percentage=0.0,
                started_at=datetime.utcnow(),
                steps=[],
                thread_id=agent_task.thread_id
            )
            self._task_progress[agent_task.task_id] = progress_response
            
            # Start task execution in background
            task_coroutine = self._execute_deep_task(agent_task)
            background_task = asyncio.create_task(task_coroutine)
            self._running_tasks[agent_task.task_id] = background_task
            
            # Estimate duration based on task type and content
            estimated_duration = self._estimate_task_duration(agent_task)
            
            response = CreateDeepTaskResponse(
                success=True,
                task_id=agent_task.task_id,
                status=TaskStatus.PENDING,
                execution_metadata={"mode": "deepagent", "started": True},
                thread_id=agent_task.thread_id,
                estimated_duration=estimated_duration
            )
            
            logger.info(f"Deep task created successfully: {agent_task.task_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating deep task: {e}", exc_info=True)
            return CreateDeepTaskResponse(
                success=False,
                task_id="",
                status=TaskStatus.FAILED,
                execution_metadata={"error": str(e)}
            )
    
    async def get_task_progress(self, request: GetTaskProgressRequest) -> GetTaskProgressResponse:
        """
        Get progress of a running task, especially for DeepAgents tasks.
        
        Args:
            request: Task progress request
            
        Returns:
            GetTaskProgressResponse with current task status and progress
        """
        try:
            logger.info(f"Getting progress for task {request.task_id}")
            
            # Check if task exists
            if request.task_id not in self._tasks:
                raise ValueError(f"Task {request.task_id} not found")
            
            # Get stored progress
            progress = self._task_progress.get(request.task_id)
            if not progress:
                # Create default progress response
                task = self._tasks[request.task_id]
                progress = GetTaskProgressResponse(
                    task_id=request.task_id,
                    status=task.status if hasattr(task, 'status') else TaskStatus.PENDING,
                    progress_percentage=0.0,
                    steps=[] if not request.include_steps else None
                )
                self._task_progress[request.task_id] = progress
            
            # Update progress if task is still running
            if (progress.status == TaskStatus.RUNNING and 
                request.task_id in self._running_tasks and
                not self._running_tasks[request.task_id].done()):
                
                # Update progress based on task execution
                await self._update_task_progress(request.task_id)
            
            logger.info(f"Retrieved progress for task {request.task_id}: {progress.status}")
            return progress
            
        except Exception as e:
            logger.error(f"Error getting task progress: {e}", exc_info=True)
            return GetTaskProgressResponse(
                task_id=request.task_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_metadata={"error": str(e)}
            )
    
    async def cancel_task(self, request: CancelTaskRequest) -> CancelTaskResponse:
        """
        Cancel a running task.
        
        Args:
            request: Task cancellation request
            
        Returns:
            CancelTaskResponse with cancellation status
        """
        try:
            logger.info(f"Cancelling task {request.task_id}")
            
            # Check if task exists
            if request.task_id not in self._tasks:
                raise ValueError(f"Task {request.task_id} not found")
            
            # Cancel running task if exists
            if request.task_id in self._running_tasks:
                background_task = self._running_tasks[request.task_id]
                if not background_task.done():
                    background_task.cancel()
                    del self._running_tasks[request.task_id]
            
            # Update task status
            task = self._tasks[request.task_id]
            task.status = TaskStatus.CANCELLED
            task.updated_at = datetime.utcnow()
            
            # Update progress
            if request.task_id in self._task_progress:
                progress = self._task_progress[request.task_id]
                progress.status = TaskStatus.CANCELLED
                progress.updated_at = datetime.utcnow()
                progress.error_message = request.reason
            
            response = CancelTaskResponse(
                success=True,
                task_id=request.task_id,
                message=f"Task {request.task_id} cancelled successfully"
            )
            
            logger.info(f"Task cancelled successfully: {request.task_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error cancelling task: {e}", exc_info=True)
            return CancelTaskResponse(
                success=False,
                task_id=request.task_id,
                message=f"Error cancelling task: {str(e)}"
            )
    
    def _create_agent_task_from_message(self, request: SendMessageRequest) -> AgentTask:
        """Create AgentTask from SendMessageRequest."""
        return AgentTask(
            task_id=str(uuid.uuid4()),
            session_id=request.session_id,
            task_type=request.task_type,
            content=request.content,
            context=request.context,
            execution_mode=request.execution_mode or ExecutionMode.AUTO,
            user_id=request.user_id,
            tenant_id=request.tenant_id
        )
    
    async def _determine_execution_mode(self, task: AgentTask) -> ExecutionMode:
        """
        Determine the best execution mode for a task.
        
        Args:
            task: AgentTask to analyze
            
        Returns:
            ExecutionMode to use for the task
        """
        # If explicitly set, use it
        if task.execution_mode != ExecutionMode.AUTO:
            return task.execution_mode
        
        # Auto-determine based on task type and content
        if task.task_type in [TaskType.CONVERSATION, TaskType.TEXT_TRANSFORM]:
            return ExecutionMode.NATIVE
        elif task.task_type in [TaskType.CODE_GENERATION, TaskType.DEBUGGING]:
            # Check complexity based on content length and context
            if len(task.content) > 1000 or len(task.context) > 5:
                return ExecutionMode.LANGGRAPH
            else:
                return ExecutionMode.NATIVE
        elif task.task_type in [TaskType.CODE_REFACTOR, TaskType.CODE_AUDIT, TaskType.RESEARCH]:
            return ExecutionMode.DEEPAGENT
        else:
            # Default to native for unknown types
            return ExecutionMode.NATIVE
    
    async def _execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task based on its execution mode.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            Dictionary with execution result and metadata
        """
        if task.execution_mode == ExecutionMode.NATIVE:
            return await self._execute_native_task(task)
        elif task.execution_mode == ExecutionMode.LANGGRAPH:
            return await self._execute_langgraph_task(task)
        elif task.execution_mode == ExecutionMode.DEEPAGENT:
            return await self._execute_deepagent_task(task)
        else:
            raise ValueError(f"Unknown execution mode: {task.execution_mode}")
    
    async def _execute_native_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task in native mode."""
        logger.info(f"Executing native task: {task.task_id}")
        
        # Simulate native execution (in real implementation, this would call AI Orchestrator)
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "content": f"Native execution completed for: {task.content[:100]}...",
            "metadata": {
                "mode": "native",
                "execution_time": 0.1,
                "task_type": task.task_type
            }
        }
    
    async def _execute_langgraph_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task in LangGraph mode."""
        logger.info(f"Executing LangGraph task: {task.task_id}")
        
        # Simulate LangGraph execution (in real implementation, this would use LangGraph)
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "content": f"LangGraph workflow completed for: {task.content[:100]}...",
            "metadata": {
                "mode": "langgraph",
                "execution_time": 0.5,
                "task_type": task.task_type,
                "workflow_steps": ["analyze", "process", "respond"]
            }
        }
    
    async def _execute_deepagent_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task in DeepAgents mode."""
        logger.info(f"Executing DeepAgents task: {task.task_id}")
        
        # Simulate DeepAgents execution (in real implementation, this would use DeepAgents)
        await asyncio.sleep(1.0)  # Simulate processing time
        
        return {
            "content": f"DeepAgents analysis completed for: {task.content[:100]}...",
            "metadata": {
                "mode": "deepagent",
                "execution_time": 1.0,
                "task_type": task.task_type,
                "subagents": ["analyzer", "planner", "executor"],
                "complexity_score": 0.8
            }
        }
    
    async def _execute_deep_task(self, task: AgentTask) -> None:
        """
        Execute a deep task in background with progress updates.
        
        Args:
            task: AgentTask to execute
        """
        try:
            # Update task status to running
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.utcnow()
            
            progress = self._task_progress[task.task_id]
            progress.status = TaskStatus.RUNNING
            progress.started_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()
            
            # Simulate task execution with progress updates
            steps = [
                TaskStep(
                    step_id="step_1",
                    name="Analysis",
                    description="Analyzing task requirements",
                    status=TaskStatus.RUNNING,
                    start_time=datetime.utcnow()
                ),
                TaskStep(
                    step_id="step_2", 
                    name="Planning",
                    description="Creating execution plan",
                    status=TaskStatus.PENDING
                ),
                TaskStep(
                    step_id="step_3",
                    name="Execution",
                    description="Executing task plan",
                    status=TaskStatus.PENDING
                ),
                TaskStep(
                    step_id="step_4",
                    name="Finalization",
                    description="Finalizing results",
                    status=TaskStatus.PENDING
                )
            ]
            
            progress.steps = steps
            progress.progress_percentage = 10.0
            
            # Execute steps with delays to simulate progress
            for i, step in enumerate(steps):
                # Update current step
                step.status = TaskStatus.RUNNING
                step.start_time = datetime.utcnow()
                progress.progress_percentage = 10.0 + (i * 20.0)
                progress.updated_at = datetime.utcnow()
                
                # Simulate step execution time
                await asyncio.sleep(0.5)
                
                # Complete step
                step.status = TaskStatus.COMPLETED
                step.end_time = datetime.utcnow()
                step.duration_seconds = 0.5
                step.progress_percentage = 100.0
            
            # Complete task
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.utcnow()
            
            progress.status = TaskStatus.COMPLETED
            progress.progress_percentage = 100.0
            progress.updated_at = datetime.utcnow()
            progress.result = {
                "summary": f"Deep task {task.task_id} completed successfully",
                "details": f"Processed: {task.content[:50]}..."
            }
            
            # Clean up running task
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
            
            logger.info(f"Deep task completed: {task.task_id}")
            
        except asyncio.CancelledError:
            logger.info(f"Deep task cancelled: {task.task_id}")
            task.status = TaskStatus.CANCELLED
            progress.status = TaskStatus.CANCELLED
            progress.error_message = "Task was cancelled"
            
        except Exception as e:
            logger.error(f"Error executing deep task {task.task_id}: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            progress.status = TaskStatus.FAILED
            progress.error_message = str(e)
    
    async def _update_task_progress(self, task_id: str) -> None:
        """Update progress for a running task."""
        # This would be implemented based on actual task execution progress
        # For now, we'll just update the timestamp
        if task_id in self._task_progress:
            progress = self._task_progress[task_id]
            progress.updated_at = datetime.utcnow()
    
    def _estimate_task_duration(self, task: AgentTask) -> int:
        """
        Estimate task duration in seconds based on task type and content.
        
        Args:
            task: AgentTask to analyze
            
        Returns:
            Estimated duration in seconds
        """
        base_durations = {
            TaskType.CODE_REFACTOR: 300,  # 5 minutes
            TaskType.CODE_AUDIT: 240,      # 4 minutes
            TaskType.RESEARCH: 180,          # 3 minutes
            TaskType.ANALYSIS: 120,         # 2 minutes
            TaskType.DOCUMENTATION: 150,     # 2.5 minutes
            TaskType.CODE_GENERATION: 90,    # 1.5 minutes
            TaskType.DEBUGGING: 60,          # 1 minute
        }
        
        base_duration = base_durations.get(task.task_type, 60)
        
        # Adjust based on content length
        content_factor = min(2.0, max(0.5, len(task.content) / 1000))
        
        # Adjust based on context complexity
        context_factor = min(1.5, max(0.8, len(task.context) / 10))
        
        estimated_duration = int(base_duration * content_factor * context_factor)
        
        logger.debug(f"Estimated duration for task {task.task_id}: {estimated_duration}s")
        return estimated_duration
    
    def get_active_tasks(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of active tasks.
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of active task information
        """
        active_tasks = []
        
        for task_id, task in self._tasks.items():
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                if session_id is None or task.session_id == session_id:
                    progress = self._task_progress.get(task_id)
                    active_tasks.append({
                        "task_id": task_id,
                        "task_type": task.task_type,
                        "status": task.status,
                        "progress": progress.model_dump() if progress else None,
                        "created_at": task.created_at
                    })
        
        return active_tasks
    
    def get_task_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get task history.
        
        Args:
            session_id: Optional session ID to filter by
            limit: Maximum number of tasks to return
            
        Returns:
            List of task history
        """
        history = []
        
        # Sort tasks by creation time (newest first)
        sorted_tasks = sorted(
            self._tasks.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        
        for task_id, task in sorted_tasks[:limit]:
            if session_id is None or task.session_id == session_id:
                progress = self._task_progress.get(task_id)
                history.append({
                    "task_id": task_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "content": task.content[:200] + "..." if len(task.content) > 200 else task.content,
                    "execution_mode": task.execution_mode,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "progress": progress.model_dump() if progress else None
                })
        
        return history