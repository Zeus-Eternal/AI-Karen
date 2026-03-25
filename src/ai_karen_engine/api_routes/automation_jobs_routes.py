"""
API Routes for Automation Jobs (formerly Sequences)

This module provides REST API endpoints for defining, viewing, and executing
multi-step job sequences.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import uuid

from ai_karen_engine.auth.session import get_current_user

logger = logging.getLogger(__name__)

# Note: frontend expects /api/automation/jobs
router = APIRouter(prefix="/automation/jobs", tags=["automation-jobs"])


class JobTask(BaseModel):
    name: str = Field(..., description="Name of the task")
    agent: str = Field(..., description="Agent assigned to the task")
    instructions: Optional[str] = Field(None, description="Specific instructions for this step")


class JobDefinitionRequest(BaseModel):
    name: str = Field(..., description="Job name")
    description: str = Field(..., description="Description of the job")
    tasks: List[JobTask] = Field(default_factory=list, description="Chain of tasks")
    trigger: str = Field("Manual Run", description="How this job is triggered")


class JobDefinitionResponse(JobDefinitionRequest):
    id: str = Field(..., description="Unique job identifier")
    created_at: datetime = Field(..., description="Creation timestamp")


# In-memory storage for demo purposes
_jobs_db: Dict[str, Dict[str, Any]] = {
    "job_demo_1": {
        "id": "job_demo_1",
        "name": "Weekly Blog Post Workflow",
        "description": "Researches a topic, writes a draft, creates an image, and stages it for review.",
        "tasks": [
            {"name": "Web Research", "agent": "Research Agent"},
            {"name": "Write Article Draft", "agent": "Writing Agent"},
            {"name": "Generate Header Image", "agent": "Image Agent"},
            {"name": "Save as Draft in CMS", "agent": "CMS Agent"}
        ],
        "trigger": "Cron: Every Monday at 9 AM",
        "created_at": datetime.utcnow()
    },
    "job_demo_2": {
        "id": "job_demo_2",
        "name": "Social Media Engagement",
        "description": "Fetches recent mentions and drafts replies for approval.",
        "tasks": [
            {"name": "Fetch Facebook Mentions", "agent": "Social Media Agent"},
            {"name": "Analyze Sentiment", "agent": "Data Analyst Agent"},
            {"name": "Draft Replies", "agent": "Social Media Agent"}
        ],
        "trigger": "Manual Run",
        "created_at": datetime.utcnow()
    }
}


@router.post("/", response_model=JobDefinitionResponse)
async def create_job(
    request: JobDefinitionRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new job sequence definition."""
    try:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        
        job_record = {
            "id": job_id,
            "name": request.name,
            "description": request.description,
            "tasks": [t.dict() for t in request.tasks],
            "trigger": request.trigger,
            "created_at": datetime.utcnow()
        }
        
        _jobs_db[job_id] = job_record
        return JobDefinitionResponse(**job_record)
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/", response_model=List[JobDefinitionResponse])
async def list_jobs(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List all configured jobs."""
    try:
        jobs = list(_jobs_db.values())
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return [JobDefinitionResponse(**j) for j in jobs]
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a job."""
    try:
        if job_id not in _jobs_db:
            raise HTTPException(status_code=404, detail="Job not found")
            
        del _jobs_db[job_id]
        return {"message": f"Job {job_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Trigger the execution of a job."""
    try:
        if job_id not in _jobs_db:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return {
            "message": f"Job {job_id} queued for execution",
            "job_id": job_id,
            "status": "Running"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute job: {str(e)}")
