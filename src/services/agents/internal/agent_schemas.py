"""
Agent Schemas module for the agent system.

This module defines all the data models, schemas, and type definitions for the agent system,
including agent definitions, tasks, messages, memory, tools, responses, sessions, and permissions.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from enum import Enum
from datetime import datetime
try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, ConfigDict


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    BUSY = "busy"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class MessageStatus(str, Enum):
    """Message status enumeration."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    PROCESSED = "processed"
    FAILED = "failed"


class PermissionLevel(str, Enum):
    """Permission level enumeration."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class AgentCapability(BaseModel):
    """Agent capability schema."""
    name: str = Field(..., description="Name of the capability")
    description: Optional[str] = Field(None, description="Description of the capability")
    version: str = Field("1.0.0", description="Version of the capability")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the capability")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies of the capability")
    
    model_config = ConfigDict(extra="allow")


class AgentDefinition(BaseModel):
    """Agent definition schema."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Human-readable name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    agent_type: str = Field(..., description="Type/category of the agent")
    version: str = Field("1.0.0", description="Version of the agent")
    capabilities: List[AgentCapability] = Field(default_factory=list, description="Capabilities of the agent")
    endpoint: Optional[str] = Field(None, description="Endpoint URL for the agent")
    status: AgentStatus = Field(AgentStatus.INITIALIZING, description="Current status of the agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the agent")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for the agent")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    model_config = ConfigDict(extra="allow")


class AgentTask(BaseModel):
    """Agent task schema."""
    task_id: str = Field(..., description="Unique identifier for the task")
    agent_id: str = Field(..., description="ID of the agent to execute the task")
    task_type: str = Field(..., description="Type of the task")
    description: Optional[str] = Field(None, description="Description of the task")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the task")
    expected_output: Optional[Dict[str, Any]] = Field(None, description="Expected output format")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current status of the task")
    priority: int = Field(0, description="Priority of the task (higher = more important)")
    progress: float = Field(0.0, description="Progress of the task (0.0 to 1.0)")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of the task")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    timeout_seconds: Optional[int] = Field(None, description="Timeout in seconds")
    retry_count: int = Field(0, description="Number of retries")
    max_retries: int = Field(3, description="Maximum number of retries")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the task")
    
    model_config = ConfigDict(extra="allow")


class AgentMessage(BaseModel):
    """Agent message schema."""
    message_id: str = Field(..., description="Unique identifier for the message")
    sender_id: str = Field(..., description="ID of the sender agent")
    recipient_id: str = Field(..., description="ID of the recipient agent")
    message_type: str = Field(..., description="Type of the message")
    content: Dict[str, Any] = Field(..., description="Content of the message")
    status: MessageStatus = Field(MessageStatus.SENT, description="Current status of the message")
    priority: int = Field(0, description="Priority of the message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    reply_to: Optional[str] = Field(None, description="ID of the message this is a reply to")
    thread_id: Optional[str] = Field(None, description="ID of the conversation thread")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the message")
    
    model_config = ConfigDict(extra="allow")


class AgentMemory(BaseModel):
    """Agent memory schema."""
    memory_id: str = Field(..., description="Unique identifier for the memory")
    agent_id: str = Field(..., description="ID of the agent the memory belongs to")
    content: Dict[str, Any] = Field(..., description="Content of the memory")
    tags: List[str] = Field(default_factory=list, description="Tags for the memory")
    importance: float = Field(0.5, description="Importance score (0.0 to 1.0)")
    access_count: int = Field(0, description="Number of times the memory has been accessed")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the memory")
    
    model_config = ConfigDict(extra="allow")


class AgentTool(BaseModel):
    """Agent tool schema."""
    tool_id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Name of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    version: str = Field("1.0.0", description="Version of the tool")
    endpoint: Optional[str] = Field(None, description="Endpoint URL for the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    return_type: str = Field("any", description="Return type of the tool")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions to use the tool")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies of the tool")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the tool")
    
    model_config = ConfigDict(extra="allow")


class AgentResponse(BaseModel):
    """Agent response schema."""
    response_id: str = Field(..., description="Unique identifier for the response")
    task_id: Optional[str] = Field(None, description="ID of the task this response is for")
    agent_id: str = Field(..., description="ID of the agent generating the response")
    success: bool = Field(..., description="Whether the response indicates success")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    execution_time: float = Field(0.0, description="Execution time in seconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the response")
    
    model_config = ConfigDict(extra="allow")


class AgentSession(BaseModel):
    """Agent session schema."""
    session_id: str = Field(..., description="Unique identifier for the session")
    agent_id: str = Field(..., description="ID of the agent")
    user_id: Optional[str] = Field(None, description="ID of the user")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    status: str = Field("active", description="Status of the session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the session")
    
    model_config = ConfigDict(extra="allow")


class AgentPermission(BaseModel):
    """Agent permission schema."""
    permission_id: str = Field(..., description="Unique identifier for the permission")
    agent_id: str = Field(..., description="ID of the agent")
    resource: str = Field(..., description="Resource the permission applies to")
    level: PermissionLevel = Field(..., description="Permission level")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditions for the permission")
    granted_at: datetime = Field(default_factory=datetime.utcnow, description="Grant timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    granted_by: Optional[str] = Field(None, description="ID of who granted the permission")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the permission")
    
    model_config = ConfigDict(extra="allow")


class AgentSchemas:
    """
    Container class for all agent schemas.
    
    This class provides a centralized location for all schema definitions
    used throughout the agent system.
    """
    
    # Enums
    AgentStatus = AgentStatus
    TaskStatus = TaskStatus
    MessageStatus = MessageStatus
    PermissionLevel = PermissionLevel
    
    # Models
    AgentCapability = AgentCapability
    AgentDefinition = AgentDefinition
    AgentTask = AgentTask
    AgentMessage = AgentMessage
    AgentMemory = AgentMemory
    AgentTool = AgentTool
    AgentResponse = AgentResponse
    AgentSession = AgentSession
    AgentPermission = AgentPermission