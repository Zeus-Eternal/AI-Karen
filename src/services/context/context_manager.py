"""
Context Manager Service for CoPilot Architecture.

This service provides comprehensive context management capabilities including:
1. Conversation context persistence
2. File/context upload functionality
3. Context preservation across agent switches
4. Context validation
5. Integration with session state and agent memory
"""

import asyncio
import json
import logging
import uuid
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
import base64
import hashlib
import mimetypes
import os

try:
    from pydantic import BaseModel, Field, ConfigDict, validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, ConfigDict, validator

from ..session_state.session_state_manager import SessionStateManager
from ..session_state.session_state_models import SessionState, SessionStateStatus
from ..agents.agent_memory import EnhancedAgentMemory, MemoryAccessLevel
from ..memory.unified_memory_service import UnifiedMemoryService

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """Context type enumeration."""
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    CUSTOM = "custom"


class ContextStatus(str, Enum):
    """Context status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"
    ERROR = "error"


class ContextErrorType(str, Enum):
    """Context error type enumeration."""
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    PERSISTENCE_ERROR = "persistence_error"
    UPLOAD_ERROR = "upload_error"
    PROCESSING_ERROR = "processing_error"
    INTEGRATION_ERROR = "integration_error"
    PERMISSION_ERROR = "permission_error"


class FileUploadStatus(str, Enum):
    """File upload status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ContextFile:
    """Context file data model."""
    file_id: str
    filename: str
    file_type: str
    file_size: int
    mime_type: str
    content_hash: str
    upload_status: FileUploadStatus
    upload_timestamp: datetime
    processing_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    storage_path: Optional[str] = None
    download_url: Optional[str] = None


class ContextData(BaseModel):
    """Context data model."""
    
    context_id: str = Field(..., description="Unique context identifier")
    session_id: str = Field(..., description="Associated session ID")
    user_id: str = Field(..., description="User identifier")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    
    # Context information
    context_type: ContextType = Field(..., description="Type of context")
    title: str = Field(..., description="Context title")
    description: Optional[str] = Field(None, description="Context description")
    
    # Content
    content: Dict[str, Any] = Field(default_factory=dict, description="Context content")
    files: List[ContextFile] = Field(default_factory=list, description="Associated files")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Context tags")
    status: ContextStatus = Field(ContextStatus.ACTIVE, description="Context status")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    # Access control
    access_level: MemoryAccessLevel = Field(MemoryAccessLevel.PRIVATE, description="Access level")
    shared_with: List[str] = Field(default_factory=list, description="List of user IDs this context is shared with")
    
    # Agent integration
    agent_id: Optional[str] = Field(None, description="Associated agent ID")
    memory_ids: List[str] = Field(default_factory=list, description="Associated memory IDs")
    
    @validator('context_id')
    def validate_context_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Context ID must be a non-empty string")
        return v
    
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


class ContextRequest(BaseModel):
    """Context request model."""
    
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    
    # Context information
    context_type: ContextType = Field(..., description="Type of context")
    title: str = Field(..., description="Context title")
    description: Optional[str] = Field(None, description="Context description")
    
    # Content
    content: Dict[str, Any] = Field(default_factory=dict, description="Initial content")
    
    # Configuration
    tags: List[str] = Field(default_factory=list, description="Context tags")
    access_level: MemoryAccessLevel = Field(MemoryAccessLevel.PRIVATE, description="Access level")
    expires_in_seconds: Optional[int] = Field(None, description="Context expiration in seconds")
    
    # Agent integration
    agent_id: Optional[str] = Field(None, description="Associated agent ID")
    
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


class ContextUpdateRequest(BaseModel):
    """Context update request model."""
    
    content: Optional[Dict[str, Any]] = Field(None, description="Content to update")
    title: Optional[str] = Field(None, description="Title to update")
    description: Optional[str] = Field(None, description="Description to update")
    tags: Optional[List[str]] = Field(None, description="Tags to update")
    status: Optional[ContextStatus] = Field(None, description="Status to update")
    access_level: Optional[MemoryAccessLevel] = Field(None, description="Access level to update")
    expires_at: Optional[datetime] = Field(None, description="New expiration time")
    shared_with: Optional[List[str]] = Field(None, description="Shared users list to update")


class FileUploadRequest(BaseModel):
    """File upload request model."""
    
    context_id: str = Field(..., description="Context ID")
    filename: str = Field(..., description="File name")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    content_hash: str = Field(..., description="Content hash for verification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")


class ContextResponse(BaseModel):
    """Context response model."""
    
    success: bool = Field(..., description="Request success status")
    context_data: Optional[ContextData] = Field(None, description="Context data")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class ContextListResponse(BaseModel):
    """Context list response model."""
    
    success: bool = Field(..., description="Request success status")
    contexts: List[ContextData] = Field(default_factory=list, description="List of contexts")
    total_count: int = Field(0, description="Total count of contexts")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class ContextError(Exception):
    """Context error exception."""
    
    def __init__(
        self,
        message: str,
        error_type: ContextErrorType = ContextErrorType.INTEGRATION_ERROR,
        context_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.context_id = context_id
        self.session_id = session_id
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "context_id": self.context_id,
            "session_id": self.session_id,
            "details": self.details
        }


class ContextManager:
    """Context Manager service for CoPilot Architecture."""
    
    def __init__(
        self,
        session_state_manager: Optional[SessionStateManager] = None,
        agent_memory: Optional[EnhancedAgentMemory] = None,
        unified_memory_service: Optional[UnifiedMemoryService] = None,
        storage_path: str = "./context_storage",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        allowed_file_types: Optional[Set[str]] = None,
        default_context_ttl_seconds: int = 3600
    ):
        """
        Initialize Context Manager.
        
        Args:
            session_state_manager: Session State Manager instance
            agent_memory: Enhanced Agent Memory instance
            unified_memory_service: Unified Memory Service instance
            storage_path: Path for storing uploaded files
            max_file_size: Maximum file size in bytes
            allowed_file_types: Set of allowed file types
            default_context_ttl_seconds: Default context TTL in seconds
        """
        self.session_state_manager = session_state_manager
        self.agent_memory = agent_memory
        self.unified_memory_service = unified_memory_service
        self.storage_path = storage_path
        self.max_file_size = max_file_size
        self.allowed_file_types = allowed_file_types or {
            ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
            ".mp3", ".wav", ".ogg", ".flac",
            ".mp4", ".avi", ".mov", ".wmv", ".flv",
            ".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml"
        }
        self.default_context_ttl_seconds = default_context_ttl_seconds
        
        # In-memory context storage (in production, this would be a database)
        self._contexts: Dict[str, ContextData] = {}
        self._context_files: Dict[str, ContextFile] = {}
        
        # Metrics
        self._metrics = {
            "contexts_created": 0,
            "contexts_updated": 0,
            "contexts_deleted": 0,
            "files_uploaded": 0,
            "validation_errors": 0,
            "errors": 0
        }
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def initialize(self) -> bool:
        """
        Initialize the Context Manager.
        
        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Initializing Context Manager")
            
            # Initialize session state manager if not provided
            if not self.session_state_manager:
                self.session_state_manager = SessionStateManager()
                await self.session_state_manager.initialize()
            
            # Initialize agent memory if not provided
            if not self.agent_memory:
                self.agent_memory = EnhancedAgentMemory()
                await self.agent_memory.initialize()
            
            # Initialize unified memory service if not provided
            if not self.unified_memory_service:
                # This would typically be initialized with proper configuration
                # For now, we'll set it to None
                self.unified_memory_service = None
            
            logger.info("Context Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Context Manager: {e}")
            self._metrics["errors"] += 1
            raise ContextError(
                message=f"Initialization failed: {str(e)}",
                error_type=ContextErrorType.INTEGRATION_ERROR,
                details={"exception": str(e)}
            )
    
    async def create_context(
        self,
        request: ContextRequest,
        correlation_id: Optional[str] = None
    ) -> ContextResponse:
        """
        Create a new context.
        
        Args:
            request: Context creation request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context creation response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Validate request
            await self._validate_context_request(request)
            
            # Generate context ID if not provided
            context_id = str(uuid.uuid4())
            
            # Calculate expiration time
            expires_at = None
            if request.expires_in_seconds:
                expires_at = datetime.utcnow() + timedelta(seconds=request.expires_in_seconds)
            
            # Create context data
            context_data = ContextData(
                context_id=context_id,
                session_id=request.session_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                context_type=request.context_type,
                title=request.title,
                description=request.description,
                content=request.content,
                tags=request.tags,
                access_level=request.access_level,
                expires_at=expires_at,
                agent_id=request.agent_id
            )
            
            # Validate context data
            await self._validate_context_data(context_data)
            
            # Store context
            self._contexts[context_id] = context_data
            
            # Create memory in agent memory if available
            if self.agent_memory:
                memory_id = await self.agent_memory.store_memory(
                    agent_id=request.agent_id or "system",
                    memory_type="context",
                    content={
                        "context_id": context_id,
                        "title": request.title,
                        "description": request.description,
                        "content": request.content
                    },
                    tags=request.tags,
                    importance=0.7,
                    access_level=request.access_level
                )
                
                # Add memory ID to context
                context_data.memory_ids.append(memory_id)
            
            # Update session state if available
            if self.session_state_manager:
                session_response = await self.session_state_manager.get_session(request.session_id)
                if session_response.success and session_response.session_state:
                    # Add context ID to session state
                    session_state = session_response.session_state
                    if "context_ids" not in session_state.context_data:
                        session_state.context_data["context_ids"] = []
                    session_state.context_data["context_ids"].append(context_id)
                    
                    # Update session state
                    from ..session_state.session_state_models import SessionStateUpdateRequest
                    update_request = SessionStateUpdateRequest(
                        context_data=session_state.context_data
                    )
                    await self.session_state_manager.update_session(
                        session_id=request.session_id,
                        request=update_request
                    )
            
            # Update metrics
            self._metrics["contexts_created"] += 1
            
            logger.info(
                f"Created context {context_id} for session {request.session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=True,
                context_data=context_data,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to create context: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def get_context(
        self,
        context_id: str,
        correlation_id: Optional[str] = None
    ) -> ContextResponse:
        """
        Get a context by ID.
        
        Args:
            context_id: Context identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            context_data = self._contexts.get(context_id)
            if not context_data:
                error_msg = f"Context {context_id} not found"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return ContextResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Check if context has expired
            if context_data.expires_at and datetime.utcnow() > context_data.expires_at:
                context_data.status = ContextStatus.EXPIRED
                logger.info(
                    f"Context {context_id} has expired",
                    extra={"correlation_id": correlation_id}
                )
            
            logger.debug(
                f"Retrieved context {context_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=True,
                context_data=context_data,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to get context {context_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def update_context(
        self,
        context_id: str,
        request: ContextUpdateRequest,
        correlation_id: Optional[str] = None
    ) -> ContextResponse:
        """
        Update a context.
        
        Args:
            context_id: Context identifier
            request: Context update request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context update response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            context_data = self._contexts.get(context_id)
            if not context_data:
                error_msg = f"Context {context_id} not found for update"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return ContextResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Update context data
            if request.content is not None:
                context_data.content.update(request.content)
            
            if request.title is not None:
                context_data.title = request.title
            
            if request.description is not None:
                context_data.description = request.description
            
            if request.tags is not None:
                context_data.tags = request.tags
            
            if request.status is not None:
                context_data.status = request.status
            
            if request.access_level is not None:
                context_data.access_level = request.access_level
            
            if request.expires_at is not None:
                context_data.expires_at = request.expires_at
            
            if request.shared_with is not None:
                context_data.shared_with = request.shared_with
            
            context_data.updated_at = datetime.utcnow()
            
            # Validate updated context data
            await self._validate_context_data(context_data)
            
            # Update memory in agent memory if available
            if self.agent_memory and context_data.memory_ids:
                for memory_id in context_data.memory_ids:
                    await self.agent_memory.update_memory(
                        memory_id=memory_id,
                        updates={
                            "content": {
                                "title": context_data.title,
                                "description": context_data.description,
                                "content": context_data.content
                            },
                            "tags": context_data.tags
                        }
                    )
            
            # Update metrics
            self._metrics["contexts_updated"] += 1
            
            logger.info(
                f"Updated context {context_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=True,
                context_data=context_data,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to update context {context_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def delete_context(
        self,
        context_id: str,
        correlation_id: Optional[str] = None
    ) -> ContextResponse:
        """
        Delete a context.
        
        Args:
            context_id: Context identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context deletion response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            context_data = self._contexts.get(context_id)
            if not context_data:
                error_msg = f"Context {context_id} not found for deletion"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return ContextResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Delete associated files
            for context_file in context_data.files:
                await self._delete_context_file(context_file.file_id)
            
            # Delete memories in agent memory if available
            if self.agent_memory and context_data.memory_ids:
                for memory_id in context_data.memory_ids:
                    await self.agent_memory.delete_memory(memory_id=memory_id)
            
            # Delete context
            del self._contexts[context_id]
            
            # Update session state if available
            if self.session_state_manager:
                session_response = await self.session_state_manager.get_session(context_data.session_id)
                if session_response.success and session_response.session_state:
                    # Remove context ID from session state
                    session_state = session_response.session_state
                    if "context_ids" in session_state.context_data:
                        session_state.context_data["context_ids"] = [
                            cid for cid in session_state.context_data["context_ids"]
                            if cid != context_id
                        ]
                        
                        # Update session state
                        from ..session_state.session_state_models import SessionStateUpdateRequest
                        update_request = SessionStateUpdateRequest(
                            context_data=session_state.context_data
                        )
                        await self.session_state_manager.update_session(
                            session_id=context_data.session_id,
                            request=update_request
                        )
            
            # Update metrics
            self._metrics["contexts_deleted"] += 1
            
            logger.info(
                f"Deleted context {context_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=True,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to delete context {context_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def list_contexts(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_type: Optional[ContextType] = None,
        status: Optional[ContextStatus] = None,
        limit: int = 50,
        offset: int = 0,
        correlation_id: Optional[str] = None
    ) -> ContextListResponse:
        """
        List contexts with filtering.
        
        Args:
            session_id: Filter by session ID (optional)
            user_id: Filter by user ID (optional)
            context_type: Filter by context type (optional)
            status: Filter by status (optional)
            limit: Maximum number of contexts to return
            offset: Offset for pagination
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context list response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            contexts = list(self._contexts.values())
            
            # Apply filters
            if session_id:
                contexts = [c for c in contexts if c.session_id == session_id]
            
            if user_id:
                contexts = [c for c in contexts if c.user_id == user_id]
            
            if context_type:
                contexts = [c for c in contexts if c.context_type == context_type]
            
            if status:
                contexts = [c for c in contexts if c.status == status]
            
            # Apply pagination
            total_count = len(contexts)
            contexts = contexts[offset:offset + limit]
            
            logger.debug(
                f"Listed {len(contexts)} contexts (total: {total_count})",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextListResponse(
                success=True,
                contexts=contexts,
                total_count=total_count,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to list contexts: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextListResponse(
                success=False,
                contexts=[],
                total_count=0,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def _validate_context_request(self, request: ContextRequest) -> None:
        """
        Validate a context request.
        
        Args:
            request: Context request to validate
            
        Raises:
            ContextError: If validation fails
        """
        # Validate session exists if session state manager is available
        if self.session_state_manager:
            session_response = await self.session_state_manager.get_session(request.session_id)
            if not session_response.success:
                raise ContextError(
                    message=f"Session {request.session_id} not found",
                    error_type=ContextErrorType.VALIDATION_ERROR,
                    session_id=request.session_id
                )
        
        # Validate agent exists if agent ID is provided
        if request.agent_id and self.agent_memory:
            # This would typically check if the agent exists
            # For now, we'll skip this validation
            pass
    
    async def _validate_context_data(self, context_data: ContextData) -> None:
        """
        Validate context data.
        
        Args:
            context_data: Context data to validate
            
        Raises:
            ContextError: If validation fails
        """
        # Validate required fields
        if not context_data.context_id:
            raise ContextError(
                message="Context ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR,
                context_id=context_data.context_id
            )
        
        if not context_data.session_id:
            raise ContextError(
                message="Session ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR,
                context_id=context_data.context_id,
                session_id=context_data.session_id
            )
        
        if not context_data.user_id:
            raise ContextError(
                message="User ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR,
                context_id=context_data.context_id,
                session_id=context_data.session_id
            )
        
        # Validate expiration time
        if context_data.expires_at and context_data.expires_at <= context_data.created_at:
            raise ContextError(
                message="Expiration time must be after creation time",
                error_type=ContextErrorType.VALIDATION_ERROR,
                context_id=context_data.context_id,
                session_id=context_data.session_id
            )
        
        # Validate file sizes
        for context_file in context_data.files:
            if context_file.file_size > self.max_file_size:
                raise ContextError(
                    message=f"File {context_file.filename} exceeds maximum size of {self.max_file_size} bytes",
                    error_type=ContextErrorType.VALIDATION_ERROR,
                    context_id=context_data.context_id,
                    session_id=context_data.session_id
                )
            
            # Validate file type
            file_ext = os.path.splitext(context_file.filename)[1].lower()
            if file_ext not in self.allowed_file_types:
                raise ContextError(
                    message=f"File type {file_ext} is not allowed",
                    error_type=ContextErrorType.VALIDATION_ERROR,
                    context_id=context_data.context_id,
                    session_id=context_data.session_id
                )
    
    async def _delete_context_file(self, file_id: str) -> bool:
        """
        Delete a context file.
        
        Args:
            file_id: File identifier
            
        Returns:
            True if deletion was successful
        """
        try:
            context_file = self._context_files.get(file_id)
            if not context_file:
                logger.warning(f"File {file_id} not found for deletion")
                return False
            
            # Delete file from storage
            if context_file.storage_path and os.path.exists(context_file.storage_path):
                os.remove(context_file.storage_path)
            
            # Remove from registry
            del self._context_files[file_id]
            
            logger.debug(f"Deleted context file {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete context file {file_id}: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.
        
        Returns:
            Service metrics
        """
        return {
            **self._metrics,
            "active_contexts": len(self._contexts),
            "total_files": len(self._context_files),
            "storage_path": self.storage_path,
            "max_file_size": self.max_file_size,
            "allowed_file_types": list(self.allowed_file_types)
        }
    
    async def cleanup_expired_contexts(self, correlation_id: Optional[str] = None) -> int:
        """
        Clean up expired contexts.
        
        Args:
            correlation_id: Correlation ID for tracking
            
        Returns:
            Number of contexts cleaned up
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            now = datetime.utcnow()
            expired_contexts = [
                context_id for context_id, context in self._contexts.items()
                if context.expires_at and now > context.expires_at
            ]
            
            cleanup_count = 0
            for context_id in expired_contexts:
                response = await self.delete_context(context_id, correlation_id)
                if response.success:
                    cleanup_count += 1
            
            logger.info(
                f"Cleaned up {cleanup_count} expired contexts",
                extra={"correlation_id": correlation_id}
            )
            
            return cleanup_count
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to cleanup expired contexts: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            return 0
    
    async def shutdown(self) -> None:
        """Shutdown the Context Manager."""
        try:
            logger.info("Shutting down Context Manager")
            
            # Clear in-memory storage
            self._contexts.clear()
            self._context_files.clear()
            
            logger.info("Context Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during Context Manager shutdown: {e}")