"""
Job Service for AI Karen Engine.

Manages persistent multi-step job sequences and their execution.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_karen_engine.agents import get_agent_integration_service, AgentExecutionMode
from ai_karen_engine.agents.internal.agent_schemas import AgentTask

logger = logging.getLogger(__name__)

class JobService:
    """Service for managing multi-step job sequences."""

    def __init__(self, storage_path: str = "data/automation_jobs.json"):
        self.storage_path = storage_path
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._load_jobs()

    def _load_jobs(self):
        """Load jobs from persistent storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, "r") as f:
                    self._jobs = json.load(f)
                logger.info(f"Loaded {len(self._jobs)} jobs from {self.storage_path}")
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                self._jobs = {}
                self._save_jobs()
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            self._jobs = {}

    def _save_jobs(self):
        """Save jobs to persistent storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self._jobs, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")

    async def list_jobs(self) -> List[Dict[str, Any]]:
        """List all defined jobs."""
        jobs = list(self._jobs.values())
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific job definition."""
        return self._jobs.get(job_id)

    async def create_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job sequence definition."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        job_record = {
            "id": job_id,
            "name": job_data["name"],
            "description": job_data["description"],
            "tasks": job_data.get("tasks", []),
            "trigger": job_data.get("trigger", "Manual Run"),
            "created_at": now,
            "updated_at": now,
            "status": "Pending",
        }
        
        self._jobs[job_id] = job_record
        self._save_jobs()
        return job_record

    async def delete_job(self, job_id: str) -> bool:
        """Delete a job definition."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save_jobs()
            return True
        return False

    async def execute_job(self, job_id: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger the execution of a multi-step job."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self._jobs[job_id]
        job["status"] = "Running"
        job["updated_at"] = datetime.utcnow().isoformat()
        self._save_jobs()
        
        # Start execution in the background
        asyncio.create_task(self._run_job_sequence(job_id, user_context))
        
        return {
            "message": f"Job {job_id} queued for execution",
            "job_id": job_id,
            "status": "Running"
        }

    async def _run_job_sequence(self, job_id: str, user_context: Optional[Dict[str, Any]] = None):
        """Execute the task sequence for a job."""
        try:
            job = self._jobs[job_id]
            tasks = job.get("tasks", [])
            
            integration_service = get_agent_integration_service()
            await integration_service.initialize()
            
            job_results = []
            job_success = True
            
            for i, task_def in enumerate(tasks):
                logger.info(f"Executing step {i+1}/{len(tasks)} for job {job_id}: {task_def.get('name')}")
                
                runtime_task = AgentTask(
                    task_id=f"job_{job_id}_step_{i}_{uuid.uuid4().hex[:4]}",
                    agent_id=str(task_def.get("agent") or "default_agent"),
                    task_type="automation_step",
                    description=str(task_def.get("name") or f"Step {i+1}"),
                    input_data={
                        "instructions": task_def.get("instructions"),
                        "job_id": job_id,
                        "step_index": i,
                        "previous_results": job_results
                    },
                    metadata={
                        "source": "job_service",
                        "job_id": job_id,
                        "user_id": user_context.get("user_id") if user_context else "system"
                    }
                )
                
                try:
                    execution_response = await integration_service.execute_task(
                        runtime_task, execution_mode=AgentExecutionMode.LANGGRAPH
                    )
                    
                    job_results.append({
                        "step": task_def.get("name"),
                        "success": execution_response.success,
                        "data": execution_response.data,
                        "error": execution_response.error
                    })
                    
                    if not execution_response.success:
                        logger.error(f"Step {i+1} failed for job {job_id}: {execution_response.error}")
                        job_success = False
                        break
                        
                except Exception as step_err:
                    logger.error(f"Exception in job {job_id} step {i+1}: {step_err}")
                    job_results.append({
                        "step": task_def.get("name"),
                        "success": False,
                        "error": str(step_err)
                    })
                    job_success = False
                    break
            
            # Update final job status
            job["status"] = "Success" if job_success else "Failed"
            job["last_results"] = job_results
            job["last_run"] = datetime.utcnow().isoformat()
            job["updated_at"] = datetime.utcnow().isoformat()
            self._save_jobs()
            
            logger.info(f"Job {job_id} execution finished with status: {job['status']}")
            
        except Exception as e:
            logger.error(f"Critical error in job sequence {job_id}: {e}")
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "Failed"
                self._jobs[job_id]["error"] = str(e)
                self._save_jobs()

# Factory function
_job_service = None

def get_job_service() -> JobService:
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
