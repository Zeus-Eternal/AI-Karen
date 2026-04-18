"""
Thread Manager Data Models

This module defines all the data models, schemas, and type definitions for the Thread Manager,
including thread models, session-thread mapping models, and request/response models.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, ConfigDict


class ThreadStatus(str, Enum):
    """Thread status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"
    ERROR = "error"


class ThreadType(str, Enum):
    """Thread type enumeration."""
    CONVERSATION = "conversation"
    TASK = "task"
    WORKFLOW = "workflow"
    SESSION = "session"


class ThreadMetadata(BaseModel):
    """Thread metadata schema."""
    thread_id: str = Field(..., description="Unique identifier for the thread")
    session_id: str = Field(..., description="ID of the session this thread belongs to")
    thread_type: ThreadType = Field(..., description="Type of the thread")
    status: ThreadStatus = Field(ThreadStatus.ACTIVE, description="Status of the thread")
    title: Optional[str] = Field(None, description="Title of the thread")
    description: Optional[str] = Field(None, description="Description of the thread")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archival timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread ID if applicable")
    parent_thread_id: Optional[str] = Field(None, description="Parent thread ID if this is a sub-thread")
    child_thread_ids: List[str] = Field(default_factory=list, description="IDs of child threads")
    tags: List[str] = Field(default_factory=list, description="Tags for the thread")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(extra="allow")


class Thread(BaseModel):
    """Thread schema."""
    thread_id: str = Field(..., description="Unique identifier for the thread")
    session_id: str = Field(..., description="ID of the session this thread belongs to")
    thread_type: ThreadType = Field(..., description="Type of the thread")
    status: ThreadStatus = Field(ThreadStatus.ACTIVE, description="Status of the thread")
    title: Optional[str] = Field(None, description="Title of the thread")
    description: Optional[str] = Field(None, description="Description of the thread")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archival timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread ID if applicable")
    parent_thread_id: Optional[str] = Field(None, description="Parent thread ID if this is a sub-thread")
    child_thread_ids: List[str] = Field(default_factory=list, description="IDs of child threads")
    tags: List[str] = Field(default_factory=list, description="Tags for the thread")
    data: Dict[str, Any] = Field(default_factory=dict, description="Thread data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(extra="allow")


class SessionThreadMapping(BaseModel):
    """Session-thread mapping schema."""
    session_id: str = Field(..., description="ID of the session")
    primary_thread_id: Optional[str] = Field(None, description="Primary thread ID for the session")
    thread_ids: List[str] = Field(default_factory=list, description="All thread IDs associated with the session")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(extra="allow")


class CreateThreadRequest(BaseModel):
    """Create thread request schema."""
    session_id: str = Field(..., description="ID of the session")
    thread_type: ThreadType = Field(ThreadType.CONVERSATION, description="Type of the thread")
    title: Optional[str] = Field(None, description="Title of the thread")
    description: Optional[str] = Field(None, description="Description of the thread")
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread ID if applicable")
    parent_thread_id: Optional[str] = Field(None, description="Parent thread ID if this is a sub-thread")
    tags: List[str] = Field(default_factory=list, description="Tags for the thread")
    data: Dict[str, Any] = Field(default_factory=dict, description="Initial thread data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    model_config = ConfigDict(extra="allow")


class CreateThreadResponse(BaseModel):
    """Create thread response schema."""
    success: bool = Field(..., description="Whether the thread was created successfully")
    thread_id: Optional[str] = Field(None, description="ID of the created thread")
    thread: Optional[Thread] = Field(None, description="Created thread data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class GetThreadRequest(BaseModel):
    """Get thread request schema."""
    thread_id: str = Field(..., description="ID of the thread")
    include_data: bool = Field(True, description="Whether to include thread data")
    include_metadata: bool = Field(True, description="Whether to include metadata")
    
    model_config = ConfigDict(extra="allow")


class GetThreadResponse(BaseModel):
    """Get thread response schema."""
    success: bool = Field(..., description="Whether the request was successful")
    thread: Optional[Thread] = Field(None, description="Thread data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class UpdateThreadRequest(BaseModel):
    """Update thread request schema."""
    thread_id: str = Field(..., description="ID of the thread")
    title: Optional[str] = Field(None, description="Title of the thread")
    description: Optional[str] = Field(None, description="Description of the thread")
    status: Optional[ThreadStatus] = Field(None, description="Status of the thread")
    tags: Optional[List[str]] = Field(None, description="Tags for the thread")
    data: Optional[Dict[str, Any]] = Field(None, description="Thread data to update")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata to update")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    model_config = ConfigDict(extra="allow")


class UpdateThreadResponse(BaseModel):
    """Update thread response schema."""
    success: bool = Field(..., description="Whether the thread was updated successfully")
    thread_id: Optional[str] = Field(None, description="ID of the updated thread")
    thread: Optional[Thread] = Field(None, description="Updated thread data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class DeleteThreadRequest(BaseModel):
    """Delete thread request schema."""
    thread_id: str = Field(..., description="ID of the thread")
    hard_delete: bool = Field(False, description="Whether to permanently delete the thread")
    
    model_config = ConfigDict(extra="allow")


class DeleteThreadResponse(BaseModel):
    """Delete thread response schema."""
    success: bool = Field(..., description="Whether the thread was deleted successfully")
    thread_id: Optional[str] = Field(None, description="ID of the deleted thread")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class ListThreadsRequest(BaseModel):
    """List threads request schema."""
    session_id: Optional[str] = Field(None, description="ID of the session to filter by")
    thread_type: Optional[ThreadType] = Field(None, description="Thread type to filter by")
    status: Optional[ThreadStatus] = Field(None, description="Thread status to filter by")
    parent_thread_id: Optional[str] = Field(None, description="Parent thread ID to filter by")
    tags: Optional[List[str]] = Field(None, description="Tags to filter by")
    include_archived: bool = Field(False, description="Whether to include archived threads")
    include_deleted: bool = Field(False, description="Whether to include deleted threads")
    limit: int = Field(50, description="Maximum number of threads to return")
    offset: int = Field(0, description="Offset for pagination")
    
    model_config = ConfigDict(extra="allow")


class ListThreadsResponse(BaseModel):
    """List threads response schema."""
    success: bool = Field(..., description="Whether the request was successful")
    threads: List[Thread] = Field(default_factory=list, description="List of threads")
    total_count: int = Field(0, description="Total number of threads matching the criteria")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class GetSessionThreadsRequest(BaseModel):
    """Get session threads request schema."""
    session_id: str = Field(..., description="ID of the session")
    include_archived: bool = Field(False, description="Whether to include archived threads")
    include_deleted: bool = Field(False, description="Whether to include deleted threads")
    
    model_config = ConfigDict(extra="allow")


class GetSessionThreadsResponse(BaseModel):
    """Get session threads response schema."""
    success: bool = Field(..., description="Whether the request was successful")
    session_id: str = Field(..., description="ID of the session")
    primary_thread_id: Optional[str] = Field(None, description="Primary thread ID for the session")
    threads: List[Thread] = Field(default_factory=list, description="List of threads for the session")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class SetPrimaryThreadRequest(BaseModel):
    """Set primary thread request schema."""
    session_id: str = Field(..., description="ID of the session")
    thread_id: str = Field(..., description="ID of the thread to set as primary")
    
    model_config = ConfigDict(extra="allow")


class SetPrimaryThreadResponse(BaseModel):
    """Set primary thread response schema."""
    success: bool = Field(..., description="Whether the primary thread was set successfully")
    session_id: str = Field(..., description="ID of the session")
    thread_id: Optional[str] = Field(None, description="ID of the primary thread")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(extra="allow")


class ThreadManagerConfig(BaseModel):
    """Thread Manager configuration schema."""
    service_name: str = Field("thread_manager", description="Name of the service")
    default_thread_type: ThreadType = Field(ThreadType.CONVERSATION, description="Default thread type")
    default_thread_status: ThreadStatus = Field(ThreadStatus.ACTIVE, description="Default thread status")
    max_threads_per_session: int = Field(10, description="Maximum number of threads per session")
    enable_thread_persistence: bool = Field(True, description="Whether to enable thread persistence")
    enable_thread_archiving: bool = Field(True, description="Whether to enable thread archiving")
    enable_thread_expiration: bool = Field(True, description="Whether to enable thread expiration")
    default_thread_lifetime_days: int = Field(30, description="Default thread lifetime in days")
    archive_inactive_threads_days: int = Field(7, description="Days after which inactive threads are archived")
    persistence_interval_seconds: int = Field(60, description="Interval for persistence operations in seconds")
    enable_error_handling: bool = Field(True, description="Whether to enable error handling")
    enable_logging: bool = Field(True, description="Whether to enable logging")
    log_level: str = Field("INFO", description="Log level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    model_config = ConfigDict(extra="allow")


class ThreadManagerStatus(BaseModel):
    """Thread Manager status schema."""
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Status of the service")
    is_healthy: bool = Field(..., description="Whether the service is healthy")
    uptime_seconds: float = Field(0.0, description="Uptime in seconds")
    total_threads: int = Field(0, description="Total number of threads")
    active_threads: int = Field(0, description="Number of active threads")
    archived_threads: int = Field(0, description="Number of archived threads")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    version: str = Field("1.0.0", description="Version of the service")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional status information")
    
    model_config = ConfigDict(extra="allow")


class ThreadManagerMetrics(BaseModel):
    """Thread Manager metrics schema."""
    threads_created: int = Field(0, description="Number of threads created")
    threads_updated: int = Field(0, description="Number of threads updated")
    threads_deleted: int = Field(0, description="Number of threads deleted")
    threads_archived: int = Field(0, description="Number of threads archived")
    threads_restored: int = Field(0, description="Number of threads restored")
    session_mappings_created: int = Field(0, description="Number of session-thread mappings created")
    primary_threads_set: int = Field(0, description="Number of primary threads set")
    langgraph_threads_created: int = Field(0, description="Number of LangGraph threads created")
    persistence_operations: int = Field(0, description="Number of persistence operations")
    cache_hits: int = Field(0, description="Number of cache hits")
    cache_misses: int = Field(0, description="Number of cache misses")
    errors_encountered: int = Field(0, description="Number of errors encountered")
    average_operation_time_ms: float = Field(0.0, description="Average operation time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metrics")
    
    model_config = ConfigDict(extra="allow")


class ThreadManagerError(BaseModel):
    """Thread Manager error schema."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_details: Optional[str] = Field(None, description="Detailed error information")
    error_type: str = Field(..., description="Type of the error")
    severity: str = Field(..., description="Severity of the error")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the error")
    thread_id: Optional[str] = Field(None, description="ID of the thread if applicable")
    session_id: Optional[str] = Field(None, description="ID of the session if applicable")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(extra="allow")