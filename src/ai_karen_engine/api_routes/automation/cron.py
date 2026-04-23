"""
API Routes for Cron Jobs

Provides REST API endpoints for tracking and managing Cron-based task orchestrations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import uuid
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False

from ai_karen_engine.auth.session import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation/cron", tags=["automation-cron"])


class CronJobRequest(BaseModel):
    taskName: str = Field(..., description="Task or Sequence Name")
    schedule: str = Field(..., description="Cron expression")
    type: str = Field(..., description="'Task' or 'Sequence'")
    targetId: str = Field(..., description="The ID of the Task or Sequence to trigger")
    enabled: bool = Field(True, description="Whether this cron job is active")


class CronJobResponse(CronJobRequest):
    id: str = Field(..., description="Unique cron job identifier")
    nextRun: str = Field(..., description="Next calculated run time")
    created_at: datetime = Field(..., description="Task creation timestamp")


# In-memory storage for demo and runtime
_cron_db: Dict[str, Dict[str, Any]] = {}
_cron_executor_task: Optional[asyncio.Task] = None


def _get_next_run(schedule: str) -> str:
    if not CRONITER_AVAILABLE:
        return "Unknown (croniter unavailable)"
    try:
        if not croniter.is_valid(schedule):
            return "Invalid Schedule"
        cron = croniter(schedule, datetime.utcnow())
        next_dt = cron.get_next(datetime)
        return next_dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return "Unknown"


@router.post("/", response_model=CronJobResponse)
async def create_cron_job(
    request: CronJobRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Create a new cron job definition."""
    try:
        cron_id = f"cron_{uuid.uuid4().hex[:8]}"
        
        if CRONITER_AVAILABLE and not croniter.is_valid(request.schedule):
            raise HTTPException(status_code=400, detail="Invalid cron expression")

        cron_record = {
            "id": cron_id,
            "taskName": request.taskName,
            "schedule": request.schedule,
            "type": request.type,
            "targetId": request.targetId,
            "enabled": request.enabled,
            "nextRun": _get_next_run(request.schedule),
            "created_at": datetime.utcnow()
        }

        _cron_db[cron_id] = cron_record
        return CronJobResponse(**cron_record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating cron job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create cron job: {str(e)}")


@router.get("/", response_model=List[CronJobResponse])
async def list_cron_jobs(
    user: Dict[str, Any] = Depends(get_current_user),
):
    """List all configured cron jobs."""
    try:
        jobs = list(_cron_db.values())
        
        # Update next runs dynamically
        for job in jobs:
            if job.get("enabled"):
                job["nextRun"] = _get_next_run(job["schedule"])
            else:
                job["nextRun"] = "Disabled"

        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        return [CronJobResponse(**j) for j in jobs]
        
    except Exception as e:
        logger.error(f"Error listing cron jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list cron jobs: {str(e)}")


@router.delete("/{cron_id}")
async def delete_cron_job(
    cron_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Delete a cron job."""
    try:
        if cron_id not in _cron_db:
            raise HTTPException(status_code=404, detail="Cron job not found")
            
        del _cron_db[cron_id]
        return {"message": f"Cron job {cron_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cron job {cron_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete cron job: {str(e)}")


@router.put("/{cron_id}/toggle", response_model=CronJobResponse)
async def toggle_cron_job(
    cron_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Toggle a cron job enablement."""
    try:
        if cron_id not in _cron_db:
            raise HTTPException(status_code=404, detail="Cron job not found")
            
        record = _cron_db[cron_id]
        record["enabled"] = not record["enabled"]
        record["nextRun"] = _get_next_run(record["schedule"]) if record["enabled"] else "Disabled"
        
        return CronJobResponse(**record)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling cron job {cron_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle cron job: {str(e)}")

# Background executor task (started optionally or runs automatically)
async def _cron_executor_loop():
    while True:
        try:
            if not CRONITER_AVAILABLE:
                await asyncio.sleep(60)
                continue
                
            now = datetime.utcnow()
            for cron_id, job in list(_cron_db.items()):
                if not job.get("enabled"):
                    continue
                    
                last_eval = job.get("last_eval", now)
                cron = croniter(job["schedule"], last_eval)
                next_calc = cron.get_next(datetime)
                
                # If we've passed the trigger time
                if now >= next_calc:
                    logger.info(f"Triggering cron job: {cron_id} -> {job.get('taskName')}")
                    job["last_eval"] = now
                    
                    # Dispatch to relevant execution logic (Task / Sequence)
                    # We just print internally for mock live functionality.
                    # Since execute_task requires FastAPI context historically, 
                    # backend logic can be queued to an orchestrator background worker here.
            
            await asyncio.sleep(10) # 10s precision
        except Exception as e:
            logger.error(f"Cron executor error: {e}")
            await asyncio.sleep(10)


@router.on_event("startup")
async def _start_cron_executor() -> None:
    """Start the background cron executor once the application event loop is running."""
    global _cron_executor_task

    if _cron_executor_task and not _cron_executor_task.done():
        return

    _cron_executor_task = asyncio.create_task(_cron_executor_loop())
    logger.info("Cron executor background task started")


@router.on_event("shutdown")
async def _stop_cron_executor() -> None:
    """Stop the background cron executor during application shutdown."""
    global _cron_executor_task

    if not _cron_executor_task:
        return

    _cron_executor_task.cancel()
    try:
        await _cron_executor_task
    except asyncio.CancelledError:
        pass
    finally:
        _cron_executor_task = None
