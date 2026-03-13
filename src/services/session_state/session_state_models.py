"""
Session State Manager Models

This module defines the data models used by the Session State Manager service.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, validator


class SessionStateStatus(str, Enum):
    """Session state status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    ERROR = "error"


class SessionStateErrorType(str, Enum):
    """Session state error type enumeration"""
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    INVALID_STATE = "invalid_state"
    PERSISTENCE_ERROR = "persistence_error"
    CHECKPOINT_ERROR = "checkpoint_error"
    INTEGRATION_ERROR = "integration_error"


class SessionState(BaseModel):
    """Session state data model"""
    
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    thread_id: Optional[str] = Field(None, description="Thread identifier")
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread identifier")
    status: SessionStateStatus = Field(SessionStateStatus.ACTIVE, description="Session status")
    
    # Session metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    # Session data
    state_data: Dict[str, Any] = Field(default_factory=dict, description="Session state data")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Session context data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Checkpoint information
    last_checkpoint_id: Optional[str] = Field(None, description="Last checkpoint ID")
    checkpoint_count: int = Field(0, description="Number of checkpoints created")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Session ID must be a non-empty string")
        return v
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("User ID must be a non-empty string")
        return v
    
    @validator('expires_at')
    def validate_expires_at(cls, v, values):
        if v is not None:
            created_at = values.get('created_at')
            if created_at and v <= created_at:
                raise ValueError("Expiration time must be after creation time")
        return v


class SessionCheckpoint(BaseModel):
    """Session checkpoint data model"""
    
    checkpoint_id: str = Field(..., description="Unique checkpoint identifier")
    session_id: str = Field(..., description="Associated session ID")
    sequence_number: int = Field(..., description="Checkpoint sequence number")
    
    # Checkpoint metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    checkpoint_type: str = Field("manual", description="Checkpoint type (manual, auto, etc.)")
    
    # Checkpoint data
    state_data: Dict[str, Any] = Field(..., description="Checkpoint state data")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Checkpoint context data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # LangGraph integration
    langgraph_config: Optional[Dict[str, Any]] = Field(None, description="LangGraph configuration")
    
    @validator('checkpoint_id')
    def validate_checkpoint_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Checkpoint ID must be a non-empty string")
        return v
    
    @validator('sequence_number')
    def validate_sequence_number(cls, v):
        if v < 0:
            raise ValueError("Sequence number must be non-negative")
        return v


class SessionStateRequest(BaseModel):
    """Session state request model"""
    
    session_id: Optional[str] = Field(None, description="Session ID (will generate if not provided)")
    user_id: str = Field(..., description="User identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    thread_id: Optional[str] = Field(None, description="Thread identifier")
    langgraph_thread_id: Optional[str] = Field(None, description="LangGraph thread identifier")
    
    # Session configuration
    expires_in_seconds: Optional[int] = Field(3600, description="Session expiration in seconds")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="Initial state data")
    initial_context: Dict[str, Any] = Field(default_factory=dict, description="Initial context data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # LangGraph configuration
    langgraph_config: Optional[Dict[str, Any]] = Field(None, description="LangGraph configuration")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("User ID must be a non-empty string")
        return v


class SessionStateResponse(BaseModel):
    """Session state response model"""
    
    success: bool = Field(..., description="Request success status")
    session_state: Optional[SessionState] = Field(None, description="Session state data")
    checkpoint: Optional[SessionCheckpoint] = Field(None, description="Checkpoint data if created")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class SessionStateError(Exception):
    """Session state error exception"""
    
    def __init__(
        self,
        message: str,
        error_type: SessionStateErrorType = SessionStateErrorType.INTEGRATION_ERROR,
        session_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.session_id = session_id
        self.checkpoint_id = checkpoint_id
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "session_id": self.session_id,
            "checkpoint_id": self.checkpoint_id,
            "details": self.details
        }


class SessionStateListResponse(BaseModel):
    """Session state list response model"""
    
    success: bool = Field(..., description="Request success status")
    sessions: List[SessionState] = Field(default_factory=list, description="List of session states")
    total_count: int = Field(0, description="Total count of sessions")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class SessionStateUpdateRequest(BaseModel):
    """Session state update request model"""
    
    state_data: Optional[Dict[str, Any]] = Field(None, description="State data to update")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Context data to update")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata to update")
    status: Optional[SessionStateStatus] = Field(None, description="Status to update")
    expires_at: Optional[datetime] = Field(None, description="New expiration time")
    
    # Checkpoint options
    create_checkpoint: bool = Field(False, description="Whether to create a checkpoint")
    checkpoint_type: str = Field("manual", description="Checkpoint type if created")
    checkpoint_metadata: Dict[str, Any] = Field(default_factory=dict, description="Checkpoint metadata")


class CheckpointListResponse(BaseModel):
    """Checkpoint list response model"""
    
    success: bool = Field(..., description="Request success status")
    checkpoints: List[SessionCheckpoint] = Field(default_factory=list, description="List of checkpoints")
    total_count: int = Field(0, description="Total count of checkpoints")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")