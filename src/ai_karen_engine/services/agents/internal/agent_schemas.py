"""
Internal schemas for the agents domain.

This module defines the data structures and schemas used internally by agent services.
These are not part of the public API and should not be imported from outside the agents domain.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, validator


class AgentType(str, Enum):
    """Enumeration of agent types."""
    WORKER = "worker"
    SPECIALIZED = "specialized"
    SYSTEM = "system"
    META = "meta"


class AgentStatus(str, Enum):
    """Enumeration of agent statuses."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class TaskStatus(str, Enum):
    """Enumeration of task statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(BaseModel):
    """Schema for agent capability."""
    name: str
    description: str
    version: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentSchema(BaseModel):
    """Base schema for agent data."""
    id: UUID
    name: str
    type: AgentType
    version: str
    description: str
    status: AgentStatus
    capabilities: List[AgentCapability] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('capabilities')
    def validate_capabilities(cls, v):
        """Validate agent capabilities."""
        capability_names = [cap.name for cap in v]
        if len(capability_names) != len(set(capability_names)):
            raise ValueError("Duplicate capability names found")
        return v


class AgentManifestSchema(BaseModel):
    """Schema for agent manifest."""
    name: str
    type: AgentType
    version: str
    description: str
    entry_point: str
    requirements: List[str] = Field(default_factory=list)
    capabilities: List[AgentCapability] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    resources: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('version')
    def validate_version(cls, v):
        """Validate version format."""
        if not v:
            raise ValueError("Version cannot be empty")
        return v
    
    @validator('entry_point')
    def validate_entry_point(cls, v):
        """Validate entry point format."""
        if not v.endswith('.py'):
            raise ValueError("Entry point must be a Python file")
        return v


class TaskSchema(BaseModel):
    """Schema for agent task."""
    id: UUID
    agent_id: UUID
    name: str
    description: str
    status: TaskStatus
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionSchema(BaseModel):
    """Schema for agent execution."""
    task_id: UUID
    agent_id: UUID
    status: TaskStatus
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResultSchema(BaseModel):
    """Schema for agent execution result."""
    task_id: UUID
    agent_id: UUID
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMemorySchema(BaseModel):
    """Schema for agent memory."""
    agent_id: UUID
    memory_type: str
    content: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentToolSchema(BaseModel):
    """Schema for agent tool."""
    name: str
    description: str
    version: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    entry_point: str
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate tool name."""
        if not v:
            raise ValueError("Tool name cannot be empty")
        return v
    
    @validator('entry_point')
    def validate_entry_point(cls, v):
        """Validate entry point format."""
        if not v.endswith('.py'):
            raise ValueError("Entry point must be a Python file")
        return v