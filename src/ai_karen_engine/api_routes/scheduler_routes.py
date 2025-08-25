"""
API routes for the autonomous training scheduler.

This module provides REST API endpoints for managing cron-based autonomous training
schedules, including creation, configuration, monitoring, and notification management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator

from ai_karen_engine.core.response.scheduler_manager import (
    SchedulerManager, AutonomousConfig, NotificationConfig, SafetyControls,
    ScheduleStatus, NotificationType, SafetyLevel
)
from ai_karen_engine.core.response.factory import get_global_scheduler_manager
from ai_karen_engine.auth.rbac_middleware import (
    get_current_user, check_scheduler_access, check_admin_access
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.training_audit_logger import get_training_audit_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# Initialize audit logger
training_audit_logger = get_training_audit_logger()


def get_scheduler_manager() -> SchedulerManager:
    """Get the global scheduler manager instance."""
    try:
        return get_global_scheduler_manager()
    except Exception as e:
        logger.error(f"Failed to get scheduler manager: {e}")
        raise HTTPException(status_code=503, detail="Scheduler manager not available")


async def require_admin_user(current_user: UserData = Depends(get_current_user)) -> UserData:
    """Require admin user for scheduler operations."""
    if not check_admin_access(current_user, "write"):
        training_audit_logger.log_permission_denied(
            user=current_user,
            resource_type="scheduler",
            resource_id="admin",
            permission_required="admin:write"
        )
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


# Pydantic models for API

class NotificationConfigModel(BaseModel):
    """Notification configuration model."""
    enabled: bool = True
    types: List[NotificationType] = [NotificationType.LOG]
    
    # Email configuration
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_recipients: List[str] = []
    email_use_tls: bool = True
    
    # Webhook configuration
    webhook_url: Optional[str] = None
    webhook_headers: Dict[str, str] = {}
    webhook_timeout: int = 30
    
    # Memory storage configuration
    memory_tenant_id: Optional[str] = None
    memory_importance_score: int = 8


class SafetyControlsModel(BaseModel):
    """Safety controls model."""
    level: SafetyLevel = SafetyLevel.MODERATE
    
    # Data quality controls
    min_data_threshold: int = Field(100, ge=1, le=100000)
    max_data_threshold: int = Field(10000, ge=100, le=1000000)
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0)
    
    # Training controls
    max_training_time_minutes: int = Field(60, ge=1, le=1440)
    validation_threshold: float = Field(0.85, ge=0.0, le=1.0)
    rollback_on_degradation: bool = True
    
    # Resource controls
    max_memory_usage_mb: int = Field(2048, ge=512, le=32768)
    max_cpu_usage_percent: float = Field(80.0, ge=10.0, le=100.0)
    
    # Failure controls
    max_consecutive_failures: int = Field(3, ge=1, le=10)
    failure_cooldown_hours: int = Field(24, ge=1, le=168)
    
    # Backup controls
    backup_before_training: bool = True
    max_backup_retention_days: int = Field(30, ge=1, le=365)


class AutonomousConfigModel(BaseModel):
    """Autonomous configuration model."""
    enabled: bool = False
    training_schedule: str = "0 2 * * *"
    timezone: str = "UTC"


# RBAC-protected endpoints

@router.get("/schedules")
async def list_schedules(
    current_user: UserData = Depends(get_current_user)
) -> Dict[str, Any]:
    """List all training schedules (requires SCHEDULER_READ permission)."""
    # Check permissions
    if not check_scheduler_access(current_user, "read"):
        training_audit_logger.log_permission_denied(
            user=current_user,
            resource_type="scheduler",
            resource_id="list",
            permission_required="scheduler:read"
        )
        raise HTTPException(status_code=403, detail="SCHEDULER_READ permission required")
    
    try:
        manager = get_scheduler_manager()
        schedules = await manager.list_schedules(user_id=current_user.user_id)
        
        return {
            "schedules": [schedule.to_dict() for schedule in schedules],
            "total": len(schedules)
        }
        
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules")
async def create_schedule(
    config: AutonomousConfigModel,
    current_user: UserData = Depends(require_admin_user)
) -> Dict[str, Any]:
    """Create a new training schedule (requires admin privileges)."""
    try:
        manager = get_scheduler_manager()
        
        # Convert to internal config format
        autonomous_config = AutonomousConfig(
            enabled=config.enabled,
            training_schedule=config.training_schedule,
            timezone=config.timezone
        )
        
        schedule_id = await manager.create_schedule(
            config=autonomous_config,
            created_by=current_user.user_id
        )
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="training_schedule",
            config_changes={
                "schedule_id": schedule_id,
                "enabled": config.enabled,
                "training_schedule": config.training_schedule,
                "timezone": config.timezone
            }
        )
        
        return {
            "schedule_id": schedule_id,
            "message": "Training schedule created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    config: AutonomousConfigModel,
    current_user: UserData = Depends(require_admin_user)
) -> Dict[str, str]:
    """Update a training schedule (requires admin privileges)."""
    try:
        manager = get_scheduler_manager()
        
        # Convert to internal config format
        autonomous_config = AutonomousConfig(
            enabled=config.enabled,
            training_schedule=config.training_schedule,
            timezone=config.timezone
        )
        
        success = await manager.update_schedule(
            schedule_id=schedule_id,
            config=autonomous_config,
            updated_by=current_user.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="training_schedule",
            config_changes={
                "schedule_id": schedule_id,
                "enabled": config.enabled,
                "training_schedule": config.training_schedule,
                "timezone": config.timezone
            }
        )
        
        return {"message": f"Schedule {schedule_id} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: UserData = Depends(require_admin_user)
) -> Dict[str, str]:
    """Delete a training schedule (requires admin privileges)."""
    try:
        manager = get_scheduler_manager()
        success = await manager.delete_schedule(
            schedule_id=schedule_id,
            deleted_by=current_user.user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Audit log
        training_audit_logger.log_config_updated(
            user=current_user,
            config_type="training_schedule",
            config_changes={
                "schedule_id": schedule_id,
                "action": "deleted"
            }
        )
        
        return {"message": f"Schedule {schedule_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{schedule_id}/execute")
async def execute_schedule(
    schedule_id: str,
    current_user: UserData = Depends(require_admin_user)
) -> Dict[str, str]:
    """Manually execute a training schedule (requires admin privileges)."""
    try:
        manager = get_scheduler_manager()
        execution_id = await manager.execute_schedule(
            schedule_id=schedule_id,
            executed_by=current_user.user_id
        )
        
        # Audit log
        training_audit_logger.log_training_started(
            user=current_user,
            training_job_id=execution_id,
            correlation_id=schedule_id
        )
        
        return {
            "execution_id": execution_id,
            "message": f"Schedule {schedule_id} execution started"
        }
        
    except Exception as e:
        logger.error(f"Failed to execute schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Quality thresholds
    min_data_threshold: int = Field(100, ge=1, le=100000)
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0)
    validation_threshold: float = Field(0.85, ge=0.0, le=1.0)
    
    # Safety controls
    safety_controls: SafetyControlsModel = SafetyControlsModel()
    
    # Notification settings
    notifications: NotificationConfigModel = NotificationConfigModel()
    
    # Advanced settings
    max_training_time: int = Field(3600, ge=60, le=86400)
    backup_models: bool = True
    auto_rollback: bool = True
    
    @validator('training_schedule')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError("Invalid cron expression")
        except ImportError:
            # If croniter not available, do basic validation
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts")
        return v


class CreateScheduleRequest(BaseModel):
    """Request model for creating a schedule."""
    tenant_id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    cron_expression: str
    config: AutonomousConfigModel
    
    @validator('cron_expression')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError("Invalid cron expression")
        except ImportError:
            # If croniter not available, do basic validation
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts")
        return v


class UpdateScheduleRequest(BaseModel):
    """Request model for updating a schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    cron_expression: Optional[str] = None
    config: Optional[AutonomousConfigModel] = None
    
    @validator('cron_expression')
    def validate_cron_expression(cls, v):
        """Validate cron expression format."""
        if v is None:
            return v
        try:
            from croniter import croniter
            if not croniter.is_valid(v):
                raise ValueError("Invalid cron expression")
        except ImportError:
            # If croniter not available, do basic validation
            parts = v.split()
            if len(parts) != 5:
                raise ValueError("Cron expression must have 5 parts")
        return v


class ScheduleResponse(BaseModel):
    """Response model for schedule information."""
    schedule_id: str
    name: str
    status: str
    cron_expression: str
    next_run: Optional[str]
    last_run: Optional[str]
    total_runs: int
    successful_runs: int
    failed_runs: int
    consecutive_failures: int
    is_running: bool
    last_result: Optional[Dict[str, Any]] = None


# API Routes

@router.post("/schedules", response_model=Dict[str, str])
async def create_schedule(
    request: CreateScheduleRequest,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Create a new autonomous training schedule."""
    try:
        # Convert Pydantic models to dataclasses
        config = AutonomousConfig(
            enabled=request.config.enabled,
            training_schedule=request.config.training_schedule,
            timezone=request.config.timezone,
            min_data_threshold=request.config.min_data_threshold,
            quality_threshold=request.config.quality_threshold,
            validation_threshold=request.config.validation_threshold,
            safety_controls=SafetyControls(**request.config.safety_controls.dict()),
            notifications=NotificationConfig(**request.config.notifications.dict()),
            max_training_time=request.config.max_training_time,
            backup_models=request.config.backup_models,
            auto_rollback=request.config.auto_rollback
        )
        
        schedule_id = scheduler.create_training_schedule(
            tenant_id=request.tenant_id,
            name=request.name,
            cron_expression=request.cron_expression,
            config=config,
            description=request.description
        )
        
        return {"schedule_id": schedule_id, "message": "Schedule created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")


@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    tenant_id: Optional[str] = None,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """List all training schedules."""
    try:
        schedules = scheduler.list_schedules(tenant_id)
        return [ScheduleResponse(**schedule) for schedule in schedules]
        
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail="Failed to list schedules")


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Get details of a specific schedule."""
    try:
        schedule = scheduler.get_schedule_status(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return ScheduleResponse(**schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get schedule")


@router.put("/schedules/{schedule_id}", response_model=Dict[str, str])
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Update an existing schedule."""
    try:
        updates = {}
        
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.cron_expression is not None:
            updates["cron_expression"] = request.cron_expression
        if request.config is not None:
            config = AutonomousConfig(
                enabled=request.config.enabled,
                training_schedule=request.config.training_schedule,
                timezone=request.config.timezone,
                min_data_threshold=request.config.min_data_threshold,
                quality_threshold=request.config.quality_threshold,
                validation_threshold=request.config.validation_threshold,
                safety_controls=SafetyControls(**request.config.safety_controls.dict()),
                notifications=NotificationConfig(**request.config.notifications.dict()),
                max_training_time=request.config.max_training_time,
                backup_models=request.config.backup_models,
                auto_rollback=request.config.auto_rollback
            )
            updates["autonomous_config"] = config
        
        success = scheduler.update_schedule(schedule_id, **updates)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found or update failed")
        
        return {"message": "Schedule updated successfully"}
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")


@router.post("/schedules/{schedule_id}/pause", response_model=Dict[str, str])
async def pause_schedule(
    schedule_id: str,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Pause a schedule."""
    try:
        success = scheduler.pause_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found or pause failed")
        
        return {"message": "Schedule paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause schedule")


@router.post("/schedules/{schedule_id}/resume", response_model=Dict[str, str])
async def resume_schedule(
    schedule_id: str,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Resume a paused schedule."""
    try:
        success = scheduler.resume_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found or resume failed")
        
        return {"message": "Schedule resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume schedule")


@router.delete("/schedules/{schedule_id}", response_model=Dict[str, str])
async def delete_schedule(
    schedule_id: str,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Delete a schedule."""
    try:
        success = scheduler.delete_schedule(schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found or delete failed")
        
        return {"message": "Schedule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete schedule {schedule_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete schedule")


@router.post("/start", response_model=Dict[str, str])
async def start_scheduler(
    background_tasks: BackgroundTasks,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Start the scheduler background task."""
    try:
        background_tasks.add_task(scheduler.start_scheduler)
        return {"message": "Scheduler start initiated"}
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scheduler")


@router.post("/stop", response_model=Dict[str, str])
async def stop_scheduler(
    background_tasks: BackgroundTasks,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Stop the scheduler background task."""
    try:
        background_tasks.add_task(scheduler.stop_scheduler)
        return {"message": "Scheduler stop initiated"}
        
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop scheduler")


@router.get("/status", response_model=Dict[str, Any])
async def get_scheduler_status(
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Get overall scheduler status."""
    try:
        total_schedules = len(scheduler.schedules)
        active_schedules = sum(1 for s in scheduler.schedules.values() 
                              if s.status == ScheduleStatus.ACTIVE)
        running_tasks = len(scheduler.running_tasks)
        
        return {
            "scheduler_running": scheduler.running,
            "total_schedules": total_schedules,
            "active_schedules": active_schedules,
            "running_tasks": running_tasks,
            "schedules": scheduler.list_schedules()
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scheduler status")


@router.post("/test-notification", response_model=Dict[str, str])
async def test_notification(
    config: NotificationConfigModel,
    scheduler: SchedulerManager = Depends(get_scheduler_manager),
    _: None = Depends(require_admin_user)
):
    """Test notification configuration."""
    try:
        notification_config = NotificationConfig(**config.dict())
        
        await scheduler.notification_manager.send_notification(
            notification_config,
            "test",
            "Test Notification",
            "This is a test notification from the Karen AI scheduler system.",
            {"test": True, "timestamp": datetime.utcnow().isoformat()}
        )
        
        return {"message": "Test notification sent successfully"}
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")


@router.get("/cron-help", response_model=Dict[str, Any])
async def get_cron_help():
    """Get help information for cron expressions."""
    return {
        "format": "minute hour day_of_month month day_of_week",
        "examples": {
            "0 2 * * *": "Daily at 2:00 AM",
            "0 */6 * * *": "Every 6 hours",
            "0 9 * * 1": "Every Monday at 9:00 AM",
            "30 14 1 * *": "First day of every month at 2:30 PM",
            "0 0 * * 0": "Every Sunday at midnight"
        },
        "special_values": {
            "*": "Any value",
            "*/n": "Every n units",
            "a-b": "Range from a to b",
            "a,b,c": "Specific values a, b, and c"
        },
        "fields": {
            "minute": "0-59",
            "hour": "0-23",
            "day_of_month": "1-31",
            "month": "1-12",
            "day_of_week": "0-7 (0 and 7 are Sunday)"
        }
    }