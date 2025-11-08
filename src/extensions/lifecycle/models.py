"""
Extension Lifecycle Models

Data models for extension lifecycle management.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExtensionHealthStatus(str, Enum):
    """Extension health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class LifecycleEventType(str, Enum):
    """Lifecycle event types."""
    STARTED = "started"
    STOPPED = "stopped"
    RESTARTED = "restarted"
    UPDATED = "updated"
    ROLLED_BACK = "rolled_back"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    MIGRATION_STARTED = "migration_started"
    MIGRATION_COMPLETED = "migration_completed"
    MIGRATION_FAILED = "migration_failed"
    HEALTH_CHECK_PASSED = "health_check_passed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    RECOVERY_INITIATED = "recovery_initiated"
    RECOVERY_COMPLETED = "recovery_completed"


class RecoveryActionType(str, Enum):
    """Recovery action types."""
    RESTART = "restart"
    ROLLBACK = "rollback"
    RESTORE_BACKUP = "restore_backup"
    DISABLE = "disable"
    NOTIFY_ADMIN = "notify_admin"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"


class ExtensionHealth(BaseModel):
    """Extension health information."""
    extension_name: str
    status: ExtensionHealthStatus
    last_check: datetime
    cpu_usage: float = Field(ge=0, le=100)
    memory_usage: float = Field(ge=0)
    disk_usage: float = Field(ge=0)
    error_rate: float = Field(ge=0, le=100)
    response_time: float = Field(ge=0)
    uptime: float = Field(ge=0)
    restart_count: int = Field(ge=0)
    last_error: Optional[str] = None
    health_score: float = Field(ge=0, le=100)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ExtensionBackup(BaseModel):
    """Extension backup information."""
    backup_id: str
    extension_name: str
    version: str
    created_at: datetime
    backup_type: str  # "full", "incremental", "config_only"
    size_bytes: int
    file_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checksum: str
    is_valid: bool = True
    description: Optional[str] = None


class ExtensionMigration(BaseModel):
    """Extension migration information."""
    migration_id: str
    extension_name: str
    from_version: str
    to_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # "pending", "running", "completed", "failed", "rolled_back"
    migration_steps: List[Dict[str, Any]] = Field(default_factory=list)
    rollback_plan: List[Dict[str, Any]] = Field(default_factory=list)
    error_message: Optional[str] = None
    backup_id: Optional[str] = None


class LifecycleEvent(BaseModel):
    """Lifecycle event record."""
    event_id: str
    extension_name: str
    event_type: LifecycleEventType
    timestamp: datetime
    details: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class RecoveryAction(BaseModel):
    """Recovery action definition."""
    action_id: str
    extension_name: str
    action_type: RecoveryActionType
    trigger_condition: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = 3
    cooldown_seconds: int = 300
    is_enabled: bool = True
    priority: int = 1  # Lower numbers = higher priority


class ExtensionSnapshot(BaseModel):
    """Extension state snapshot."""
    snapshot_id: str
    extension_name: str
    version: str
    created_at: datetime
    state: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    data_checksum: str
    is_restorable: bool = True


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    extension_name: str
    check_interval_seconds: int = 60
    timeout_seconds: int = 30
    failure_threshold: int = 3
    success_threshold: int = 1
    enabled_checks: List[str] = Field(default_factory=lambda: [
        "cpu_usage", "memory_usage", "response_time", "error_rate"
    ])
    thresholds: Dict[str, float] = Field(default_factory=dict)
    custom_checks: List[Dict[str, Any]] = Field(default_factory=list)