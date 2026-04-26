"""
API Routes for Automation Statistics.

Aggregates statistics from tasks, jobs, and cron schedules for the Automation Hub dashboard.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from ai_karen_engine.auth.session import get_current_user
from ai_karen_engine.services.job_service import get_job_service, JobService
from ai_karen_engine.agents import get_agent_integration_service, AgentStatus
from ai_karen_engine.api_routes.automation.tasks import get_tasks_summary
from ai_karen_engine.api_routes.automation.cron import get_cron_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/automation/stats", tags=["automation-stats"])


@router.get("/")
async def get_automation_stats(
    user: Dict[str, Any] = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service)
):
    """Get aggregated automation statistics."""
    try:
        # Get tasks summary
        tasks_summary = get_tasks_summary()
        
        # Get cron summary
        cron_summary = get_cron_summary()
        
        # Get jobs (sequences) count
        jobs = await job_service.list_jobs()
        active_sequences = len(jobs)
        
        # Get agent integration service for agent count
        integration_service = get_agent_integration_service()
        await integration_service.initialize()
        agents = await integration_service.get_all_agents()
        
        # Consider IDLE, PROCESSING, and STREAMING as "active" for the dashboard
        active_statuses = [AgentStatus.IDLE, AgentStatus.PROCESSING, AgentStatus.STREAMING]
        active_count = len([a for a in agents if a.status in active_statuses])
        total_agents = len(agents)
        
        return {
            "activeAgents": f"{active_count} / {total_agents}",
            "tasksToday": str(tasks_summary["tasks_run_today"]),
            "activeSequences": str(active_sequences),
            "nextJob": cron_summary["next_job"] or "None Scheduled",
            "nextJobTime": cron_summary["next_job_time"] or "N/A",
            "details": {
                "tasks": tasks_summary,
                "cron": cron_summary,
                "total_sequences": active_sequences
            }
        }
    except Exception as e:
        logger.error(f"Error getting automation stats: {e}")
        return {
            "activeAgents": "0 / 0",
            "tasksToday": "0",
            "activeSequences": "0",
            "nextJob": "Error",
            "nextJobTime": str(e)
        }
