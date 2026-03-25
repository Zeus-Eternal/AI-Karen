"""
API Routes for Agent Task Management

This module provides REST API endpoints for defining, viewing, and executing
standalone tasks assigned to specific primary agents and sub-agents.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import uuid

from ai_karen_engine.auth.session import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class SubAgentConfig(BaseModel):
    name: str = Field(..., description="Name of the sub-agent assigned")
    instructions: str = Field(..., description="Specific instructions for this sub-agent")


class TaskDefinitionRequest(BaseModel):
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Detailed description of what the task does")
    primaryAgent: str = Field(..., description="Primary agent responsible for the outcome")
    primaryAgentInstructions: str = Field("", description="Instructions for the primary agent")
    subAgents: List[SubAgentConfig] = Field(default_factory=list, description="Delegated sub-agents and instructions")


class TaskDefinitionResponse(TaskDefinitionRequest):
    id: str = Field(..., description="Unique task identifier")
    lastRun: Optional[str] = Field(None, description="When the task was last executed")
    status: str = Field("Pending", description="Status of the task (e.g., Success, Failed, Pending, Running)")
    created_at: datetime = Field(..., description="Task creation timestamp")


# In-memory storage for demo purposes
# In a full system, this would be tied to a Postgres DB or similar.
_tasks_db: Dict[str, Dict[str, Any]] = {
    "task_demo_1": {
        "id": "task_demo_1",
        "name": "Generate Weekly Sales Report",
        "description": "Queries the sales database, analyzes the data, and formats it into a PDF report.",
        "primaryAgent": "Data Analyst Agent",
        "primaryAgentInstructions": "{'sales_period': 'last_7_days', 'output_format': 'summary_table'}",
        "subAgents": [
            {"name": "PDF Generation Agent", "instructions": "{'template': 'weekly_sales_report', 'filename': 'Weekly_Sales.pdf'}"}
        ],
        "lastRun": "2024-07-26 17:00 UTC",
        "status": "Failed",
        "created_at": datetime.utcnow()
    },
    "task_demo_2": {
        "id": "task_demo_2",
        "name": "Check Urgent Emails",
        "description": "Scans Gmail for unread emails from 'boss@example.com' or with 'URGENT' in the subject.",
        "primaryAgent": "Email Agent",
        "primaryAgentInstructions": "Only check for emails within the last 24 hours.",
        "subAgents": [],
        "lastRun": "2024-07-29 11:00 UTC",
        "status": "Success",
        "created_at": datetime.utcnow()
    }
}


@router.post("/", response_model=TaskDefinitionResponse)
async def create_task(
    request: TaskDefinitionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new task definition."""
    try:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task_record = {
            "id": task_id,
            "name": request.name,
            "description": request.description,
            "primaryAgent": request.primaryAgent,
            "primaryAgentInstructions": request.primaryAgentInstructions,
            "subAgents": [sa.dict() for sa in request.subAgents],
            "lastRun": None,
            "status": "Pending",
            "created_at": datetime.utcnow()
        }
        
        _tasks_db[task_id] = task_record
        return TaskDefinitionResponse(**task_record)
        
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
        
        return [TaskDefinitionResponse(**t) for t in tasks]
        
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
        
        return TaskDefinitionResponse(**_tasks_db[task_id])
        
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
        
        # In a real implementation, this would dispatch to Celery or the Orchestrator
        # For now, we simulate execution
        task["status"] = "Running"
        task["lastRun"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        
        return {
            "message": f"Task {task_id} queued for execution",
            "task_id": task_id,
            "status": "Running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute task: {str(e)}")
