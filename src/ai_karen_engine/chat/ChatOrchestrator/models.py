from __future__ import annotations
import uuid
import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from dataclasses import dataclass, field

class ProcessingStatus(str, Enum):
    """Refined status tracking for long-running chat operations."""
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    EXTRACTING_CONTEXT = "extracting_context"
    GENERATING_RESPONSE = "generating_response"
    STREAMING = "streaming"
    EXECUTING_TOOLS = "executing_tools"
    RECORDING_MEMORY = "recording_memory"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    DEGRADED = "degraded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class ErrorType(str, Enum):
    """Categorized processing failures for structured reporting."""
    NLP_PARSING_ERROR = "nlp_parsing_error"
    CONTEXT_RETRIEVAL_ERROR = "context_retrieval_error"
    AI_MODEL_ERROR = "ai_model_error"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    MEMORY_STORAGE_ERROR = "memory_storage_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "auth_error"
    EMBEDDING_ERROR = "embedding_error"
    REQUEST_CANCELLED = "request_cancelled"
    UNKNOWN_ERROR = "unknown_error"

class ChatRequest(BaseModel):
    """Input payload for a chat orchestration request."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Stable request identifier")
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Cross-service correlation identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier when available")
    message: str = Field(..., description="The user's message content")
    user_id: str = Field(..., description="Unique user identifier")
    org_id: Optional[str] = Field(None, description="Organization or Tenant ID")
    conversation_id: str = Field(..., description="Active conversation context ID")
    session_id: Optional[str] = Field(None, description="Optional session tracking ID")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Stable user message identifier")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Associated file or media links")
    include_context: bool = Field(True, description="Whether to perform RAG recall")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional request-specific metadata")
    streaming: bool = Field(False, description="Whether to return a stream generator")
    stream: bool = Field(False, description="Alias for streaming")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation timestamp")

class ChatResponse(BaseModel):
    """Structured output from the orchestrator."""
    model_config = ConfigDict(protected_namespaces=())

    request_id: Optional[str] = Field(None, description="Source request identifier")
    response: str = Field(..., description="The final generated response")
    correlation_id: str = Field(..., description="Request tracking identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    assistant_message_id: Optional[str] = Field(None, description="Persisted assistant message identifier")
    processing_time: float = Field(..., description="Total execution time in seconds")
    status: ProcessingStatus = Field(..., description="Terminal processing state")
    used_fallback: bool = Field(False, description="Whether a fallback model was used")
    context_used: bool = Field(False, description="Whether RAG context was utilized")
    execution_path: Optional[str] = Field(None, description="Execution path selected by the orchestrator")
    structured_content: Dict[str, Any] = Field(default_factory=dict, description="Rich JSON output or application state")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested or triggered automation actions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Detailed execution and model metadata")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Telemetry payload for frontend/runtime inspection")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[ErrorType] = Field(None, description="Error classification")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Response creation timestamp")

class ChatStreamChunk(BaseModel):
    """Granular output chunk for streaming responses."""
    model_config = ConfigDict(protected_namespaces=())
    
    type: str = Field(..., description="Chunk type: 'content', 'status', 'error', 'complete'")
    content: str = Field("", description="The text fragment or status update")
    correlation_id: str = Field(..., description="Request tracking identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional chunk metadata")

class ProcessingContext:
    """Internal state bag for a single chat operation."""
    def __init__(
        self, 
        request: Optional[ChatRequest] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.correlation_id = str(uuid.uuid4())
        self.request_timestamp = datetime.utcnow()
        self.start_time = datetime.utcnow()
        self.processing_start: Optional[datetime] = None
        self.processing_end: Optional[datetime] = None
        
        self.request = request
        if request:
            self.conversation_id = request.conversation_id
            self.user_id = request.user_id
            self.session_id = request.session_id
            self.metadata = request.metadata.copy()
        else:
            self.conversation_id = conversation_id or ""
            self.user_id = user_id or ""
            self.session_id = session_id
            self.metadata = (metadata or {}).copy()
            
        self.status = ProcessingStatus.INITIALIZING
        self.retry_count = 0
        self.cancel_event = asyncio.Event()
        self.cancelled = False

@dataclass
class ProcessingResult:
    """Internal summary of an LLM generation attempt or tool run."""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    llm_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    used_fallback: bool = False
    structured_content: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    parsed_message: Any = None
    embeddings: Optional[List[float]] = None
    correlation_id: Optional[str] = None

@dataclass
class RetryConfig:
    """Strategy for handling transient processing failures."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    exponential_backoff: bool = True
    max_delay: float = 10.0

@dataclass
class FallbackContext:
    """Tracking context for navigating the model fallback chain."""
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    attempt_count: int = 0
    fallback_level: str = "primary" # primary -> secondary -> local -> degraded
    providers_attempted: List[str] = field(default_factory=list)
    decision_history: List[str] = field(default_factory=list)

@dataclass
class FallbackDecision:
    """Final determination of which model provider to attempt next."""
    provider: str
    model_id: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class LLMResponseVerificationError(Exception):
    """Exception raised when an LLM response fails validation or is empty."""
    def __init__(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.metadata = metadata or {}
