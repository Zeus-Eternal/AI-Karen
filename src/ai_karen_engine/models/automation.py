from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class AutomationTriggerType(str, Enum):
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    CONDITIONAL = "conditional"


class AutomationTrigger(BaseModel):
    type: AutomationTriggerType
    schedule: Optional[str] = None  # cron or RRULE
    event_name: Optional[str] = None
    condition: Optional[str] = None
    timezone: str = "UTC"
    next_run_at: Optional[datetime] = None


class AutomationExecutionConfig(BaseModel):
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    timeout_seconds: int = 120
    max_retries: int = 2
    retry_delay_seconds: int = 30


class AutomationMemoryPolicy(BaseModel):
    can_read: bool = True
    can_write: bool = True
    write_mode: Literal["full", "summary_only", "none"] = "summary_only"
    store_raw_tool_outputs: bool = False
    tenant_scope: str = "current_user"


class AutomationApprovalPolicy(BaseModel):
    required_to_create: bool = False
    required_before_execution: bool = False
    required_for_actions: List[str] = Field(default_factory=list)


class AutomationNotificationPolicy(BaseModel):
    channels: List[str] = Field(default_factory=list)  # chat, email, dashboard
    only_on_failure: bool = False


class AutomationDraft(BaseModel):
    draft_id: str
    name: str
    goal: str
    trigger: AutomationTrigger
    execution: AutomationExecutionConfig
    memory: AutomationMemoryPolicy
    approval: AutomationApprovalPolicy
    notification: AutomationNotificationPolicy
    risk_level: Literal["low", "medium", "high"] = "low"
    confirmation_required: bool = True
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentAutomation(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: Literal["active", "paused", "disabled", "failed", "completed", "pending_approval"] = "active"
    trigger: AutomationTrigger
    execution: AutomationExecutionConfig
    memory: AutomationMemoryPolicy
    approval: AutomationApprovalPolicy
    notification: AutomationNotificationPolicy
    risk_level: str = "low"
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_from_message_id: Optional[str] = None
    created_by_user_id: Optional[str] = None
    tenant_id: Optional[str] = None


class AgentRun(BaseModel):
    id: str
    automation_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    correlation_id: str
    status: ExecutionStatus
    trigger_source: Literal["chat", "schedule", "manual", "webhook", "system"]
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_name: Optional[str] = None
    tools_used: List[Dict[str, Any]] = Field(default_factory=list)
    memory_recall_count: int = 0
    memory_persistence_status: str = "none"
    started_at: datetime
    completed_at: Optional[datetime] = None
    latency_ms: Optional[float] = None
    summary: Optional[str] = None
    error: Optional[str] = None
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
