"""
API Routes for Automation Jobs (formerly Sequences)

This module provides REST API endpoints for defining, viewing, and executing
multi-step job sequences, backed by the persistent JobService.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ai_karen_engine.auth.session import get_current_user
from ai_karen_engine.services.job_service import get_job_service, JobService

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
    status: str = Field("Pending", description="Current status of the job")


@router.post("/", response_model=JobDefinitionResponse)
async def create_job(
    request: JobDefinitionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """Create a new job sequence definition."""
    try:
        job_record = await job_service.create_job(request.dict())
        return JobDefinitionResponse(**job_record)
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/", response_model=List[JobDefinitionResponse])
async def list_jobs(
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """List all configured jobs."""
    try:
        jobs = await job_service.list_jobs()
        return [JobDefinitionResponse(**j) for j in jobs]
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobDefinitionResponse)
async def get_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """Get a specific job definition."""
    try:
        job = await job_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobDefinitionResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """Delete a job."""
    try:
        success = await job_service.delete_job(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"message": f"Job {job_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """Trigger the execution of a job."""
    try:
        result = await job_service.execute_job(job_id, user_context=user)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute job: {str(e)}")
