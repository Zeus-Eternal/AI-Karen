"""
Extension Lifecycle Management API Routes
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .manager import ExtensionLifecycleManager
from .models import (
    ExtensionHealth,
    ExtensionBackup,
    ExtensionMigration,
    LifecycleEvent,
    RecoveryAction
)


# Request/Response models
class BackupRequest(BaseModel):
    extension_name: str
    backup_type: str = "full"
    description: Optional[str] = None
    include_data: bool = True
    include_config: bool = True
    include_code: bool = True


class RestoreRequest(BaseModel):
    backup_id: str
    target_extension_name: Optional[str] = None
    restore_data: bool = True
    restore_config: bool = True
    restore_code: bool = False


class MigrationRequest(BaseModel):
    extension_name: str
    target_version: str
    create_backup: bool = True
    auto_rollback_on_failure: bool = True


class RecoveryRequest(BaseModel):
    extension_name: str
    strategy: str = "auto"
    force_recovery: bool = False


class HealthConfigRequest(BaseModel):
    extension_name: str
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    failure_threshold: int = 3
    success_threshold: int = 1
    enabled_checks: List[str] = []
    thresholds: Dict[str, float] = {}
    custom_checks: List[Dict[str, Any]] = []


# Create router
router = APIRouter(prefix="/api/extensions/lifecycle", tags=["Extension Lifecycle"])


# Dependency to get lifecycle manager
async def get_lifecycle_manager() -> ExtensionLifecycleManager:
    # This would typically be injected from the main application
    # For now, this is a placeholder
    raise HTTPException(status_code=500, detail="Lifecycle manager not available")


# Health Management Endpoints
@router.get("/health", response_model=Dict[str, ExtensionHealth])
async def get_all_health_status(
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get health status of all extensions."""
    return await lifecycle_manager.get_all_health_status()


@router.get("/health/{extension_name}", response_model=ExtensionHealth)
async def get_extension_health(
    extension_name: str,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get health status of a specific extension."""
    health = await lifecycle_manager.get_extension_health(extension_name)
    if not health:
        raise HTTPException(status_code=404, detail="Extension health not found")
    return health


@router.post("/health/{extension_name}/config")
async def configure_health_monitoring(
    extension_name: str,
    config: HealthConfigRequest,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Configure health monitoring for an extension."""
    await lifecycle_manager.configure_health_monitoring(
        extension_name, config.dict()
    )
    return {"message": "Health monitoring configured successfully"}


# Backup Management Endpoints
@router.post("/backup", response_model=ExtensionBackup)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Create a backup of an extension."""
    backup = await lifecycle_manager.create_backup(
        request.extension_name,
        request.backup_type,
        request.description
    )
    return backup


@router.post("/backup/restore")
async def restore_backup(
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Restore an extension from backup."""
    success = await lifecycle_manager.restore_backup(
        request.backup_id,
        request.target_extension_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Backup restore failed")
    
    return {"message": "Backup restored successfully"}


@router.get("/backup", response_model=List[ExtensionBackup])
async def list_backups(
    extension_name: Optional[str] = None,
    limit: int = 50,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """List available backups."""
    backups = await lifecycle_manager.list_backups(extension_name)
    return backups[:limit]


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Delete a backup."""
    success = await lifecycle_manager.delete_backup(backup_id)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return {"message": "Backup deleted successfully"}


# Migration Management Endpoints
@router.post("/migration", response_model=ExtensionMigration)
async def migrate_extension(
    request: MigrationRequest,
    background_tasks: BackgroundTasks,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Migrate an extension to a target version."""
    migration = await lifecycle_manager.migrate_extension(
        request.extension_name,
        request.target_version,
        request.create_backup
    )
    return migration


@router.post("/migration/{migration_id}/rollback")
async def rollback_migration(
    migration_id: str,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Rollback a migration."""
    success = await lifecycle_manager.rollback_migration(migration_id)
    if not success:
        raise HTTPException(status_code=400, detail="Migration rollback failed")
    
    return {"message": "Migration rolled back successfully"}


@router.get("/migration/{extension_name}", response_model=ExtensionMigration)
async def get_migration_status(
    extension_name: str,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get migration status for an extension."""
    migration = await lifecycle_manager.get_migration_status(extension_name)
    if not migration:
        raise HTTPException(status_code=404, detail="No active migration found")
    return migration


@router.get("/migration", response_model=List[ExtensionMigration])
async def list_migrations(
    extension_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """List migrations."""
    migrations = await lifecycle_manager.list_migrations(extension_name)
    
    if status:
        migrations = [m for m in migrations if m.status == status]
    
    return migrations[:limit]


# Recovery Management Endpoints
@router.post("/recovery")
async def recover_extension(
    request: RecoveryRequest,
    background_tasks: BackgroundTasks,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Recover a failed extension."""
    success = await lifecycle_manager.recover_extension(
        request.extension_name,
        request.strategy
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Extension recovery failed")
    
    return {"message": "Extension recovery initiated successfully"}


@router.get("/recovery/{extension_name}")
async def get_recovery_history(
    extension_name: str,
    limit: int = 50,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get recovery history for an extension."""
    history = await lifecycle_manager.get_recovery_history(extension_name)
    return history[:limit]


# Lifecycle Events Endpoints
@router.get("/events", response_model=List[LifecycleEvent])
async def get_lifecycle_events(
    extension_name: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get lifecycle events."""
    events = await lifecycle_manager.get_lifecycle_events(
        extension_name, event_type, limit
    )
    return events


# Overview Endpoints
@router.get("/overview/{extension_name}")
async def get_extension_overview(
    extension_name: str,
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get comprehensive overview of an extension's lifecycle status."""
    overview = await lifecycle_manager.get_extension_overview(extension_name)
    return overview


@router.get("/overview")
async def get_system_overview(
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Get system-wide lifecycle overview."""
    overview = await lifecycle_manager.get_system_overview()
    return overview


# Utility Endpoints
@router.post("/start")
async def start_lifecycle_management(
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Start lifecycle management services."""
    await lifecycle_manager.start()
    return {"message": "Lifecycle management started"}


@router.post("/stop")
async def stop_lifecycle_management(
    lifecycle_manager: ExtensionLifecycleManager = Depends(get_lifecycle_manager)
):
    """Stop lifecycle management services."""
    await lifecycle_manager.stop()
    return {"message": "Lifecycle management stopped"}