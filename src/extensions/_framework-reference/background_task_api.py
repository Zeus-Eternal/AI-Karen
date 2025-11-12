"""
Background Task API endpoints for the AI Karen Extensions System.

This module provides REST API endpoints for managing extension background tasks,
including task execution, monitoring, and event management.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from datetime import datetime

from .background_tasks import TaskStatus, TaskTriggerType, TaskExecution, TaskDefinition


logger = logging.getLogger(__name__)


# Request/Response Models
class TaskExecutionRequest(BaseModel):
    """Request model for manual task execution."""
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TaskExecutionResponse(BaseModel):
    """Response model for task execution."""
    execution_id: str
    task_name: str
    extension_name: str
    status: TaskStatus
    trigger_type: TaskTriggerType
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    resource_usage: Dict[str, Any] = Field(default_factory=dict)


class TaskDefinitionResponse(BaseModel):
    """Response model for task definition."""
    name: str
    extension_name: str
    function_path: str
    description: Optional[str] = None
    schedule: Optional[str] = None
    trigger_type: TaskTriggerType
    enabled: bool
    max_retries: int
    timeout_seconds: int


class EventEmissionRequest(BaseModel):
    """Request model for event emission."""
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)


class EventTriggerRequest(BaseModel):
    """Request model for event trigger registration."""
    event_type: str
    extension_name: str
    task_name: str
    filter_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BackgroundTaskStats(BaseModel):
    """Background task system statistics."""
    running: bool
    registered_tasks: int
    scheduled_tasks: int
    active_executions: int
    total_executions: int
    event_triggers: int


def create_background_task_router(extension_manager) -> APIRouter:
    """Create FastAPI router for background task management with authentication."""
    from server.security import require_background_tasks, require_extension_read, require_extension_admin
    
    router = APIRouter(prefix="/background-tasks", tags=["Background Tasks"])
    
    @router.get("/", response_model=List[TaskDefinitionResponse])
    async def list_tasks(
        extension_name: Optional[str] = Query(None, description="Filter by extension name"),
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """List all registered background tasks."""
        try:
            user_id = user_context.get('user_id', 'unknown') if isinstance(user_context, dict) else 'unknown'
            logger.info(f"User {user_id} listing background tasks")
            tasks = extension_manager.get_extension_tasks(extension_name)
            
            return [
                TaskDefinitionResponse(
                    name=task.name,
                    extension_name=task.extension_name,
                    function_path=task.function_path,
                    description=task.description,
                    schedule=task.schedule,
                    trigger_type=task.trigger_type,
                    enabled=task.enabled,
                    max_retries=task.max_retries,
                    timeout_seconds=task.timeout_seconds
                )
                for task in tasks
            ]
            
        except Exception as e:
            user_id = user_context.get('user_id', 'unknown') if isinstance(user_context, dict) else 'unknown'
            logger.error(f"Error listing background tasks for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/{extension_name}/{task_name}", response_model=TaskDefinitionResponse)
    async def get_task(
        extension_name: str, 
        task_name: str,
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """Get a specific background task definition."""
        try:
            task_def = extension_manager.background_task_manager.get_task_definition(
                extension_name, task_name
            )
            
            if not task_def:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Task not found: {extension_name}.{task_name}"
                )
            
            return TaskDefinitionResponse(
                name=task_def.name,
                extension_name=task_def.extension_name,
                function_path=task_def.function_path,
                description=task_def.description,
                schedule=task_def.schedule,
                trigger_type=task_def.trigger_type,
                enabled=task_def.enabled,
                max_retries=task_def.max_retries,
                timeout_seconds=task_def.timeout_seconds
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting task {extension_name}.{task_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/{extension_name}/{task_name}/execute", response_model=TaskExecutionResponse)
    async def execute_task(
        extension_name: str, 
        task_name: str, 
        request: TaskExecutionRequest,
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """Execute a background task manually."""
        try:
            execution = await extension_manager.execute_extension_task(
                extension_name, task_name, request.parameters
            )
            
            return TaskExecutionResponse(
                execution_id=execution.id,
                task_name=execution.task_name,
                extension_name=execution.extension_name,
                status=execution.status,
                trigger_type=execution.trigger_type,
                scheduled_at=execution.scheduled_at,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                duration_seconds=execution.duration_seconds,
                result=execution.result,
                error=execution.error,
                resource_usage=execution.resource_usage
            )
            
        except Exception as e:
            logger.error(f"Error executing task {extension_name}.{task_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/executions", response_model=List[TaskExecutionResponse])
    async def list_executions(
        extension_name: Optional[str] = Query(None, description="Filter by extension name"),
        task_name: Optional[str] = Query(None, description="Filter by task name"),
        limit: int = Query(100, description="Maximum number of executions to return"),
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """List task execution history."""
        try:
            executions = extension_manager.get_task_execution_history(
                extension_name, task_name, limit
            )
            
            return [
                TaskExecutionResponse(
                    execution_id=execution.id,
                    task_name=execution.task_name,
                    extension_name=execution.extension_name,
                    status=execution.status,
                    trigger_type=execution.trigger_type,
                    scheduled_at=execution.scheduled_at,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration_seconds=execution.duration_seconds,
                    result=execution.result,
                    error=execution.error,
                    resource_usage=execution.resource_usage
                )
                for execution in executions
            ]
            
        except Exception as e:
            logger.error(f"Error listing task executions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/executions/active", response_model=List[str])
    async def list_active_executions(
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """List currently running task executions."""
        try:
            return extension_manager.get_active_task_executions()
            
        except Exception as e:
            logger.error(f"Error listing active executions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/executions/{execution_id}/cancel")
    async def cancel_execution(
        execution_id: str,
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """Cancel a running task execution."""
        try:
            success = await extension_manager.cancel_task_execution(execution_id)
            
            if not success:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Execution not found or not running: {execution_id}"
                )
            
            return {"message": f"Execution {execution_id} cancelled successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling execution {execution_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/events/emit")
    async def emit_event(
        request: EventEmissionRequest,
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """Emit an event that may trigger background tasks."""
        try:
            triggered_tasks = await extension_manager.emit_event(
                request.event_type, request.event_data
            )
            
            return {
                "event_type": request.event_type,
                "triggered_tasks": triggered_tasks,
                "message": f"Event emitted, triggered {len(triggered_tasks)} tasks"
            }
            
        except Exception as e:
            logger.error(f"Error emitting event {request.event_type}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/events/triggers")
    async def register_event_trigger(
        request: EventTriggerRequest,
        user_context: Dict[str, Any] = Depends(require_extension_admin)
    ):
        """Register an event trigger for a task."""
        try:
            extension_manager.register_event_trigger(
                request.event_type,
                request.extension_name,
                request.task_name,
                request.filter_conditions
            )
            
            return {
                "message": f"Event trigger registered: {request.event_type} -> "
                          f"{request.extension_name}.{request.task_name}"
            }
            
        except Exception as e:
            logger.error(f"Error registering event trigger: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/events/triggers")
    async def list_event_triggers(
        user_context: Dict[str, Any] = Depends(require_background_tasks)
    ):
        """List all registered event triggers."""
        try:
            triggers = extension_manager.background_task_manager.event_manager.get_event_triggers()
            
            result = []
            for event_type, trigger_list in triggers.items():
                for trigger in trigger_list:
                    result.append({
                        "event_type": event_type,
                        "extension_name": trigger.extension_name,
                        "task_name": trigger.task_name,
                        "filter_conditions": trigger.filter_conditions,
                        "enabled": trigger.enabled
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing event triggers: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/stats", response_model=BackgroundTaskStats)
    async def get_stats(
        user_context: Dict[str, Any] = Depends(require_extension_read)
    ):
        """Get background task system statistics."""
        try:
            stats = extension_manager.background_task_manager.get_manager_stats()
            
            return BackgroundTaskStats(
                running=stats['running'],
                registered_tasks=stats['registered_tasks'],
                scheduled_tasks=stats['scheduled_tasks'],
                active_executions=stats['active_executions'],
                total_executions=stats['total_executions'],
                event_triggers=stats['event_triggers']
            )
            
        except Exception as e:
            logger.error(f"Error getting background task stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/health")
    async def health_check(
        user_context: Dict[str, Any] = Depends(require_extension_read)
    ):
        """Background task system health check."""
        try:
            health = await extension_manager.background_task_manager.health_check()
            return health
            
        except Exception as e:
            logger.error(f"Background task health check error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router