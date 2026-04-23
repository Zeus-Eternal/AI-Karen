"""
API Routes for Agent Task Management.

This module provides REST API endpoints for defining, viewing, and executing
task definitions backed by live agent runtime execution.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ai_karen_engine.auth.session import get_current_user
from ai_karen_engine.agents import AgentExecutionMode, get_agent_integration_service
from ai_karen_engine.agents.internal.agent_schemas import AgentTask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class SubAgentConfig(BaseModel):
    name: str = Field(..., description="Name of the sub-agent assigned")
    instructions: str = Field(..., description="Specific instructions for this sub-agent")
    agentId: Optional[str] = Field(
        None, description="Optional live agent identifier for the sub-agent"
    )


class TaskDefinitionRequest(BaseModel):
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Detailed description of what the task does")
    primaryAgent: str = Field(..., description="Primary agent responsible for the outcome")
    primaryAgentInstructions: str = Field("", description="Instructions for the primary agent")
    taskType: Optional[str] = Field(
        None, description="Optional runtime task type used for execution routing"
    )
    subAgents: List[SubAgentConfig] = Field(default_factory=list, description="Delegated sub-agents and instructions")


class TaskDefinitionResponse(TaskDefinitionRequest):
    id: str = Field(..., description="Unique task identifier")
    lastRun: Optional[str] = Field(None, description="When the task was last executed")
    status: str = Field("Pending", description="Status of the task (e.g., Success, Failed, Pending, Running)")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task update timestamp")
    lastError: Optional[str] = Field(None, description="Last execution error, if any")
    runCount: int = Field(0, description="Number of executions for this task")
    runtimeTaskId: Optional[str] = Field(None, description="Last live runtime task identifier")


# Live task registry for the running backend process.
# Tasks are created from the UI and executed against the real agent runtime.
_tasks_db: Dict[str, Dict[str, Any]] = {}


def _slugify_task_type(name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "general_task"


def _normalize_task_record(task_record: Dict[str, Any]) -> TaskDefinitionResponse:
    record = dict(task_record)
    record.setdefault("updated_at", record.get("created_at", datetime.utcnow()))
    record.setdefault("lastError", None)
    record.setdefault("runCount", 0)
    record.setdefault("runtimeTaskId", None)
    record.setdefault("taskType", record.get("taskType") or _slugify_task_type(record["name"]))
    return TaskDefinitionResponse(**record)


@router.post("/", response_model=TaskDefinitionResponse)
async def create_task(
    request: TaskDefinitionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new task definition."""
    try:
        integration_service = get_agent_integration_service()
        await integration_service.initialize()

        primary_agent = await integration_service.get_agent_info(request.primaryAgent)
        if not primary_agent:
            raise HTTPException(
                status_code=404,
                detail=f"Primary agent {request.primaryAgent} not found",
            )

        for sub_agent in request.subAgents:
            if sub_agent.agentId:
                sub_agent_info = await integration_service.get_agent_info(
                    sub_agent.agentId
                )
                if not sub_agent_info:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Sub-agent {sub_agent.agentId} not found",
                    )

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        task_type = request.taskType or _slugify_task_type(request.name)
        
        task_record = {
            "id": task_id,
            "name": request.name,
            "description": request.description,
            "primaryAgent": request.primaryAgent,
            "primaryAgentInstructions": request.primaryAgentInstructions,
            "taskType": task_type,
            "subAgents": [sa.dict() for sa in request.subAgents],
            "lastRun": None,
            "status": "Pending",
            "created_at": now,
            "updated_at": now,
            "lastError": None,
            "runCount": 0,
            "runtimeTaskId": None,
            "created_by": user.get("user_id") or user.get("id"),
        }
        
        _tasks_db[task_id] = task_record
        return _normalize_task_record(task_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/", response_model=List[TaskDefinitionResponse])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    agent_name: Optional[str] = Query(None, description="Filter by primary agent name"),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List all configured tasks."""
    try:
        tasks = list(_tasks_db.values())
        
        if status:
            tasks = [t for t in tasks if t["status"] == status]
            
        if agent_name:
            tasks = [t for t in tasks if t["primaryAgent"] == agent_name]
            
        # Sort by creation date (newest first)
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        
        return [_normalize_task_record(t) for t in tasks]
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/{task_id}", response_model=TaskDefinitionResponse)
async def get_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific task definition."""
    try:
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return _normalize_task_record(_tasks_db[task_id])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a task."""
    try:
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
            
        del _tasks_db[task_id]
        return {"message": f"Task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Trigger the execution of a task."""
    try:
        if task_id not in _tasks_db:
            raise HTTPException(status_code=404, detail="Task not found")
            
        task = _tasks_db[task_id]
        task["status"] = "Running"
        task["lastRun"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        task["updated_at"] = datetime.utcnow()
        task["lastError"] = None
        task["runCount"] = int(task.get("runCount", 0)) + 1

        integration_service = get_agent_integration_service()
        await integration_service.initialize()

        runtime_task = AgentTask(
            task_id=f"runtime_{task_id}_{uuid.uuid4().hex[:8]}",
            agent_id=str(task.get("primaryAgent") or ""),
            task_type=str(task.get("taskType") or _slugify_task_type(task.get("name", "task"))),
            description=str(task.get("description") or ""),
            input_data={
                "task_id": task_id,
                "task_name": task.get("name"),
                "task_description": task.get("description"),
                "primary_agent_instructions": task.get("primaryAgentInstructions"),
                "sub_agents": task.get("subAgents", []),
            },
            metadata={
                "source": "api_tasks",
                "created_by": user.get("user_id") or user.get("id"),
                "task_definition_id": task_id,
            },
        )

        execution_response = await integration_service.execute_task(
            runtime_task, execution_mode=AgentExecutionMode.LANGGRAPH
        )

        task["runtimeTaskId"] = runtime_task.task_id
        task["updated_at"] = datetime.utcnow()
        task["status"] = "Success" if execution_response.success else "Failed"
        task["lastError"] = execution_response.error

        if not execution_response.success:
            raise HTTPException(
                status_code=500,
                detail=execution_response.error or "Task execution failed",
            )

        return {
            "message": f"Task {task_id} executed successfully",
            "task_id": task_id,
            "runtime_task_id": runtime_task.task_id,
            "status": task["status"],
            "agent_id": task.get("primaryAgent"),
            "response": execution_response.data,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")
