"""
Plan and Diff API Routes

API endpoints for execution plan management and file diff operations
supporting the enhanced code screen center panel.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
try:
    from pydantic import BaseModel, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict
from datetime import datetime
import logging
import uuid

from ai_karen_engine.auth.session import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plans", tags=["plans"])


class PlanStepRequest(BaseModel):
    """Request model for plan steps."""
    title: str
    description: str
    risk_level: str  # low, medium, high, critical
    estimated_duration: int  # seconds
    dependencies: List[str] = []
    affected_files: List[str] = []
    commands: Optional[List[str]] = None
    rollback_commands: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ExecutionPlanRequest(BaseModel):
    """Request model for execution plans."""
    title: str
    description: str
    steps: List[PlanStepRequest]
    tags: List[str] = []


class PlanStepResponse(BaseModel):
    """Response model for plan steps."""
    id: str
    title: str
    description: str
    risk_level: str
    status: str  # pending, running, completed, failed, skipped
    estimated_duration: int
    actual_duration: Optional[int] = None
    dependencies: List[str]
    affected_files: List[str]
    commands: Optional[List[str]] = None
    rollback_commands: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ExecutionPlanResponse(BaseModel):
    """Response model for execution plans."""
    id: str
    title: str
    description: str
    status: str  # draft, review, approved, rejected
    steps: List[PlanStepResponse]
    total_estimated_duration: int
    progress: float  # 0-100
    created_at: datetime
    modified_at: datetime
    author: str
    reviewers: Optional[List[str]] = None
    tags: List[str]


class DiffLineResponse(BaseModel):
    """Response model for diff lines."""
    line_number: int
    content: str
    type: str  # added, removed, modified, unchanged
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None


class FileDiffResponse(BaseModel):
    """Response model for file diffs."""
    id: str
    file_path: str
    old_file_path: Optional[str] = None
    change_type: str  # added, removed, modified, renamed, unchanged
    additions: int
    deletions: int
    old_content: str
    new_content: str
    lines: List[DiffLineResponse]
    binary: bool
    selected: bool
    applied: bool
    metadata: Optional[Dict[str, Any]] = None


class PlanExecutionRequest(BaseModel):
    """Request model for plan execution."""
    execution_mode: str = "manual"  # manual, auto
    dry_run: bool = False


class StepExecutionRequest(BaseModel):
    """Request model for step execution."""
    dry_run: bool = False


class FileSelectionRequest(BaseModel):
    """Request model for file selection."""
    file_ids: List[str]
    selected: bool


# In-memory storage for demo purposes (replace with database in production)
_plans: Dict[str, Dict] = {}
_diffs: Dict[str, Dict] = {}


@router.post("/", response_model=ExecutionPlanResponse)
async def create_plan(
    request: ExecutionPlanRequest,
    user = Depends(get_current_user)
):
    """Create a new execution plan."""
    try:
        plan_id = str(uuid.uuid4())
        
        # Convert steps to response format
        steps = []
        total_duration = 0
        
        for step_req in request.steps:
            step_id = str(uuid.uuid4())
            step = {
                "id": step_id,
                "title": step_req.title,
                "description": step_req.description,
                "risk_level": step_req.risk_level,
                "status": "pending",
                "estimated_duration": step_req.estimated_duration,
                "actual_duration": None,
                "dependencies": step_req.dependencies,
                "affected_files": step_req.affected_files,
                "commands": step_req.commands,
                "rollback_commands": step_req.rollback_commands,
                "metadata": step_req.metadata or {}
            }
            steps.append(step)
            total_duration += step_req.estimated_duration
        
        # Create plan
        plan = {
            "id": plan_id,
            "title": request.title,
            "description": request.description,
            "status": "draft",
            "steps": steps,
            "total_estimated_duration": total_duration,
            "progress": 0.0,
            "created_at": datetime.utcnow(),
            "modified_at": datetime.utcnow(),
            "author": user.get("username", "unknown"),
            "reviewers": None,
            "tags": request.tags
        }
        
        _plans[plan_id] = plan
        
        return ExecutionPlanResponse(**plan)
    
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {str(e)}")


@router.get("/", response_model=List[ExecutionPlanResponse])
async def list_plans(
    status: Optional[str] = Query(None, description="Filter by status"),
    author: Optional[str] = Query(None, description="Filter by author"),
    limit: int = Query(50, description="Maximum number of plans to return"),
    user = Depends(get_current_user)
):
    """List execution plans with optional filtering."""
    try:
        plans = list(_plans.values())
        
        # Apply filters
        if status:
            plans = [p for p in plans if p["status"] == status]
        
        if author:
            plans = [p for p in plans if p["author"] == author]
        
        # Sort by modified date (newest first)
        plans.sort(key=lambda x: x["modified_at"], reverse=True)
        
        # Apply limit
        plans = plans[:limit]
        
        return [ExecutionPlanResponse(**plan) for plan in plans]
    
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list plans: {str(e)}")


@router.get("/{plan_id}", response_model=ExecutionPlanResponse)
async def get_plan(
    plan_id: str,
    user = Depends(get_current_user)
):
    """Get a specific execution plan."""
    try:
        if plan_id not in _plans:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan = _plans[plan_id]
        return ExecutionPlanResponse(**plan)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plan: {str(e)}")


@router.put("/{plan_id}/status")
async def update_plan_status(
    plan_id: str,
    status: str,
    reason: Optional[str] = None,
    user = Depends(get_current_user)
):
    """Update plan status (approve, reject, etc.)."""
    try:
        if plan_id not in _plans:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        valid_statuses = ["draft", "review", "approved", "rejected"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        plan = _plans[plan_id]
        plan["status"] = status
        plan["modified_at"] = datetime.utcnow()
        
        if reason:
            if "metadata" not in plan:
                plan["metadata"] = {}
            plan["metadata"]["status_reason"] = reason
        
        return {"message": f"Plan status updated to {status}", "plan_id": plan_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plan status {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update plan status: {str(e)}")


@router.post("/{plan_id}/execute")
async def execute_plan(
    plan_id: str,
    request: PlanExecutionRequest,
    user = Depends(get_current_user)
):
    """Execute an entire plan."""
    try:
        if plan_id not in _plans:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan = _plans[plan_id]
        
        if plan["status"] != "approved":
            raise HTTPException(status_code=400, detail="Plan must be approved before execution")
        
        # Simulate execution
        if request.dry_run:
            return {
                "message": "Dry run completed successfully",
                "plan_id": plan_id,
                "estimated_duration": plan["total_estimated_duration"],
                "steps_to_execute": len([s for s in plan["steps"] if s["status"] == "pending"])
            }
        
        # Mark all pending steps as completed (simulation)
        completed_count = 0
        for step in plan["steps"]:
            if step["status"] == "pending":
                step["status"] = "completed"
                step["actual_duration"] = step["estimated_duration"]  # Simulate
                completed_count += 1
        
        # Update progress
        total_steps = len(plan["steps"])
        completed_steps = len([s for s in plan["steps"] if s["status"] == "completed"])
        plan["progress"] = (completed_steps / total_steps) * 100 if total_steps > 0 else 100
        plan["modified_at"] = datetime.utcnow()
        
        return {
            "message": "Plan executed successfully",
            "plan_id": plan_id,
            "steps_executed": completed_count,
            "progress": plan["progress"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute plan: {str(e)}")


@router.post("/{plan_id}/steps/{step_id}/execute")
async def execute_step(
    plan_id: str,
    step_id: str,
    request: StepExecutionRequest,
    user = Depends(get_current_user)
):
    """Execute a specific step."""
    try:
        if plan_id not in _plans:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan = _plans[plan_id]
        step = next((s for s in plan["steps"] if s["id"] == step_id), None)
        
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        if step["status"] != "pending":
            raise HTTPException(status_code=400, detail="Step is not in pending status")
        
        # Check dependencies
        for dep_id in step["dependencies"]:
            dep_step = next((s for s in plan["steps"] if s["id"] == dep_id), None)
            if not dep_step or dep_step["status"] != "completed":
                raise HTTPException(status_code=400, detail=f"Dependency {dep_id} not completed")
        
        if request.dry_run:
            return {
                "message": "Step dry run completed successfully",
                "step_id": step_id,
                "estimated_duration": step["estimated_duration"],
                "affected_files": step["affected_files"]
            }
        
        # Simulate step execution
        step["status"] = "completed"
        step["actual_duration"] = step["estimated_duration"]  # Simulate
        
        # Update plan progress
        total_steps = len(plan["steps"])
        completed_steps = len([s for s in plan["steps"] if s["status"] == "completed"])
        plan["progress"] = (completed_steps / total_steps) * 100 if total_steps > 0 else 100
        plan["modified_at"] = datetime.utcnow()
        
        return {
            "message": "Step executed successfully",
            "step_id": step_id,
            "plan_progress": plan["progress"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing step {step_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute step: {str(e)}")


@router.get("/{plan_id}/diffs", response_model=List[FileDiffResponse])
async def get_plan_diffs(
    plan_id: str,
    user = Depends(get_current_user)
):
    """Get file diffs associated with a plan."""
    try:
        if plan_id not in _plans:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Return demo diffs for now
        demo_diffs = [
            {
                "id": str(uuid.uuid4()),
                "file_path": "src/components/example.tsx",
                "old_file_path": None,
                "change_type": "modified",
                "additions": 15,
                "deletions": 8,
                "old_content": "// Old content here",
                "new_content": "// New content here",
                "lines": [
                    {
                        "line_number": 1,
                        "content": "import React from 'react';",
                        "type": "unchanged",
                        "old_line_number": 1,
                        "new_line_number": 1
                    },
                    {
                        "line_number": 2,
                        "content": "// Added new import",
                        "type": "added",
                        "old_line_number": None,
                        "new_line_number": 2
                    }
                ],
                "binary": False,
                "selected": False,
                "applied": False,
                "metadata": {
                    "size": 1024,
                    "last_modified": datetime.utcnow().isoformat()
                }
            }
        ]
        
        return [FileDiffResponse(**diff) for diff in demo_diffs]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diffs for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get diffs: {str(e)}")


@router.post("/diffs/select")
async def select_files(
    request: FileSelectionRequest,
    user = Depends(get_current_user)
):
    """Select/deselect files for batch operations."""
    try:
        # Update selection status for specified files
        updated_count = 0
        for file_id in request.file_ids:
            if file_id in _diffs:
                _diffs[file_id]["selected"] = request.selected
                updated_count += 1
        
        return {
            "message": f"Updated selection for {updated_count} files",
            "selected": request.selected,
            "file_count": len(request.file_ids)
        }
    
    except Exception as e:
        logger.error(f"Error selecting files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to select files: {str(e)}")


@router.post("/diffs/{file_id}/apply")
async def apply_file_diff(
    file_id: str,
    user = Depends(get_current_user)
):
    """Apply changes for a specific file."""
    try:
        # Simulate applying file changes
        return {
            "message": "File changes applied successfully",
            "file_id": file_id,
            "applied_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error applying file diff {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply file diff: {str(e)}")


@router.post("/diffs/{file_id}/revert")
async def revert_file_diff(
    file_id: str,
    user = Depends(get_current_user)
):
    """Revert changes for a specific file."""
    try:
        # Simulate reverting file changes
        return {
            "message": "File changes reverted successfully",
            "file_id": file_id,
            "reverted_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error reverting file diff {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to revert file diff: {str(e)}")


@router.get("/health")
async def plan_health_check(user = Depends(get_current_user)):
    """Health check for plan services."""
    try:
        return {
            "status": "healthy",
            "plans_count": len(_plans),
            "diffs_count": len(_diffs),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Plan health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }