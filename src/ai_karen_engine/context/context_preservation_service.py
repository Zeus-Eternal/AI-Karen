"""
Context Preservation Service for CoPilot Architecture.

This service provides functionality to preserve and restore context when switching
between different agents in the CoPilot system.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, validator

from .context_manager import (
    ContextManager, ContextData, ContextError, ContextErrorType,
    ContextRequest, ContextType, MemoryAccessLevel, ContextUpdateRequest
)
from .file_upload_service import FileUploadService, FileUploadRequest, FileUploadResponse

logger = logging.getLogger(__name__)


class PreservationStrategy(str, Enum):
    """Context preservation strategy enumeration."""
    COMPLETE = "complete"  # Preserve entire context
    SELECTIVE = "selective"  # Preserve only selected context elements
    MINIMAL = "minimal"  # Preserve only essential context elements
    NONE = "none"  # Do not preserve context


class ContextElement(str, Enum):
    """Context element enumeration."""
    CONVERSATION_HISTORY = "conversation_history"
    USER_PREFERENCES = "user_preferences"
    SESSION_STATE = "session_state"
    UPLOADED_FILES = "uploaded_files"
    AGENT_MEMORY = "agent_memory"
    WORKING_DATA = "working_data"
    METADATA = "metadata"


@dataclass
class ContextSnapshot:
    """Context snapshot data model."""
    snapshot_id: str
    source_agent_id: str
    target_agent_id: str
    context_id: str
    session_id: str
    user_id: str
    tenant_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    strategy: PreservationStrategy = PreservationStrategy.COMPLETE
    elements: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_restored: bool = False
    restored_at: Optional[datetime] = None


class ContextPreservationRequest(BaseModel):
    """Context preservation request model."""
    
    context_id: str = Field(..., description="Context ID")
    source_agent_id: str = Field(..., description="Source agent ID")
    target_agent_id: str = Field(..., description="Target agent ID")
    strategy: PreservationStrategy = Field(PreservationStrategy.COMPLETE, description="Preservation strategy")
    elements: List[ContextElement] = Field(default_factory=list, description="Elements to preserve")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('elements')
    def validate_elements(cls, v, values):
        strategy = values.get('strategy', PreservationStrategy.COMPLETE)
        
        if strategy == PreservationStrategy.COMPLETE:
            # For complete strategy, include all elements
            return [e for e in ContextElement]
        elif strategy == PreservationStrategy.MINIMAL:
            # For minimal strategy, include only essential elements
            return [ContextElement.CONVERSATION_HISTORY, ContextElement.SESSION_STATE]
        elif strategy == PreservationStrategy.SELECTIVE:
            # For selective strategy, validate that elements are provided
            if not v:
                raise ValueError("Elements must be specified for selective strategy")
            return v
        elif strategy == PreservationStrategy.NONE:
            # For none strategy, return empty list
            return []
        
        return v


class ContextPreservationResponse(BaseModel):
    """Context preservation response model."""
    
    success: bool = Field(..., description="Preservation success status")
    snapshot_id: Optional[str] = Field(None, description="Snapshot ID if preservation was successful")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class ContextRestorationRequest(BaseModel):
    """Context restoration request model."""
    
    snapshot_id: str = Field(..., description="Snapshot ID")
    target_agent_id: str = Field(..., description="Target agent ID")
    merge_strategy: str = Field("replace", description="Merge strategy (replace, merge, append)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ContextRestorationResponse(BaseModel):
    """Context restoration response model."""
    
    success: bool = Field(..., description="Restoration success status")
    context_id: Optional[str] = Field(None, description="Context ID if restoration was successful")
    error_message: Optional[str] = Field(None, description="Error message if any")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class ContextPreservationService:
    """Context Preservation Service for CoPilot Architecture."""
    
    def __init__(
        self,
        context_manager: ContextManager,
        file_upload_service: Optional[FileUploadService] = None
    ):
        """
        Initialize Context Preservation Service.
        
        Args:
            context_manager: Context Manager instance
            file_upload_service: File Upload Service instance (optional)
        """
        self.context_manager = context_manager
        self.file_upload_service = file_upload_service
        
        # In-memory snapshot storage (in production, this would be a database)
        self._snapshots: Dict[str, ContextSnapshot] = {}
        
        # Metrics
        self._metrics = {
            "preservations_created": 0,
            "restorations_completed": 0,
            "preservation_errors": 0,
            "restoration_errors": 0,
            "errors": 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize Context Preservation Service.
        
        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Initializing Context Preservation Service")
            
            # Initialize context manager if not already initialized
            if not self.context_manager:
                raise ValueError("Context Manager is required")
            
            logger.info("Context Preservation Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Context Preservation Service: {e}")
            self._metrics["errors"] += 1
            raise ContextError(
                message=f"Initialization failed: {str(e)}",
                error_type=ContextErrorType.INTEGRATION_ERROR,
                details={"exception": str(e)}
            )
    
    async def preserve_context(
        self,
        request: ContextPreservationRequest,
        correlation_id: Optional[str] = None
    ) -> ContextPreservationResponse:
        """
        Preserve context for agent switch.
        
        Args:
            request: Context preservation request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context preservation response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Validate request
            await self._validate_preservation_request(request)
            
            # Get context
            context_response = await self.context_manager.get_context(request.context_id)
            if not context_response.success or not context_response.data:
                raise ContextError(
                    message=f"Context {request.context_id} not found",
                    error_type=ContextErrorType.NOT_FOUND,
                    context_id=request.context_id
                )
            
            context_data = context_response.data
            
            # Create snapshot
            snapshot_id = str(uuid.uuid4())
            snapshot = ContextSnapshot(
                snapshot_id=snapshot_id,
                source_agent_id=request.source_agent_id,
                target_agent_id=request.target_agent_id,
                context_id=request.context_id,
                session_id=context_data.session_id,
                user_id=context_data.user_id,
                tenant_id=context_data.tenant_id,
                strategy=request.strategy,
                elements={},
                metadata=request.metadata
            )
            
            # Extract context elements based on strategy
            for element in request.elements:
                if element == ContextElement.CONVERSATION_HISTORY:
                    snapshot.elements[element.value] = await self._extract_conversation_history(context_data)
                elif element == ContextElement.USER_PREFERENCES:
                    snapshot.elements[element.value] = await self._extract_user_preferences(context_data)
                elif element == ContextElement.SESSION_STATE:
                    snapshot.elements[element.value] = await self._extract_session_state(context_data)
                elif element == ContextElement.UPLOADED_FILES:
                    snapshot.elements[element.value] = await self._extract_uploaded_files(context_data)
                elif element == ContextElement.AGENT_MEMORY:
                    snapshot.elements[element.value] = await self._extract_agent_memory(context_data)
                elif element == ContextElement.WORKING_DATA:
                    snapshot.elements[element.value] = await self._extract_working_data(context_data)
                elif element == ContextElement.METADATA:
                    snapshot.elements[element.value] = await self._extract_metadata(context_data)
            
            # Store snapshot
            self._snapshots[snapshot_id] = snapshot
            
            # Update metrics
            self._metrics["preservations_created"] += 1
            
            logger.info(
                f"Created context snapshot {snapshot_id} for agent switch from {request.source_agent_id} to {request.target_agent_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextPreservationResponse(
                success=True,
                snapshot_id=snapshot_id,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["preservation_errors"] += 1
            error_msg = f"Failed to preserve context: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextPreservationResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def restore_context(
        self,
        request: ContextRestorationRequest,
        correlation_id: Optional[str] = None
    ) -> ContextRestorationResponse:
        """
        Restore context from snapshot.
        
        Args:
            request: Context restoration request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Context restoration response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Validate request
            await self._validate_restoration_request(request)
            
            # Get snapshot
            snapshot = self._snapshots.get(request.snapshot_id)
            if not snapshot:
                raise ContextError(
                    message=f"Snapshot {request.snapshot_id} not found",
                    error_type=ContextErrorType.NOT_FOUND
                )
            
            # Create new context for target agent
            new_context_request = ContextRequest(
                session_id=snapshot.session_id,
                user_id=snapshot.user_id,
                tenant_id=snapshot.tenant_id,
                context_type=ContextType.CONVERSATION,
                title=f"Restored Context from Agent {snapshot.source_agent_id}",
                description=f"Context restored from snapshot {snapshot.snapshot_id}",
                content={},
                tags=["restored", f"from_agent_{snapshot.source_agent_id}"],
                access_level=MemoryAccessLevel.PRIVATE,
                agent_id=request.target_agent_id
            )
            
            # Create new context
            new_context_response = await self.context_manager.create_context(new_context_request)
            if not new_context_response.success or not new_context_response.data:
                raise ContextError(
                    message=f"Failed to create new context: {new_context_response.error_message}",
                    error_type=ContextErrorType.VALIDATION_ERROR
                )
            
            new_context_id = new_context_response.context_id
            new_context_data = new_context_response.data
            
            # Restore context elements
            for element_name, element_data in snapshot.elements.items():
                if element_name == ContextElement.CONVERSATION_HISTORY.value:
                    await self._restore_conversation_history(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.USER_PREFERENCES.value:
                    await self._restore_user_preferences(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.SESSION_STATE.value:
                    await self._restore_session_state(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.UPLOADED_FILES.value:
                    await self._restore_uploaded_files(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.AGENT_MEMORY.value:
                    await self._restore_agent_memory(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.WORKING_DATA.value:
                    await self._restore_working_data(new_context_data, element_data, request.merge_strategy)
                elif element_name == ContextElement.METADATA.value:
                    await self._restore_metadata(new_context_data, element_data, request.merge_strategy)
            
            # Update new context
            update_request = ContextUpdateRequest(
                content=new_context_data.content,
                files=new_context_data.files,
                metadata=new_context_data.metadata
            )
            await self.context_manager.update_context(
                context_id=new_context_id,
                request=update_request
            )
            
            # Update snapshot
            snapshot.is_restored = True
            snapshot.restored_at = datetime.utcnow()
            
            # Update metrics
            self._metrics["restorations_completed"] += 1
            
            logger.info(
                f"Restored context {new_context_id} from snapshot {request.snapshot_id} for agent {request.target_agent_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return ContextRestorationResponse(
                success=True,
                context_id=new_context_id,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["restoration_errors"] += 1
            error_msg = f"Failed to restore context: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return ContextRestorationResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def get_snapshot(
        self,
        snapshot_id: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a context snapshot.
        
        Args:
            snapshot_id: Snapshot identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Snapshot data
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            snapshot = self._snapshots.get(snapshot_id)
            if not snapshot:
                raise ContextError(
                    message=f"Snapshot {snapshot_id} not found",
                    error_type=ContextErrorType.NOT_FOUND
                )
            
            # Convert snapshot to dict for serialization
            snapshot_dict = {
                "snapshot_id": snapshot.snapshot_id,
                "source_agent_id": snapshot.source_agent_id,
                "target_agent_id": snapshot.target_agent_id,
                "context_id": snapshot.context_id,
                "session_id": snapshot.session_id,
                "user_id": snapshot.user_id,
                "tenant_id": snapshot.tenant_id,
                "timestamp": snapshot.timestamp.isoformat(),
                "strategy": snapshot.strategy.value,
                "elements": snapshot.elements,
                "metadata": snapshot.metadata,
                "is_restored": snapshot.is_restored,
                "restored_at": snapshot.restored_at.isoformat() if snapshot.restored_at else None
            }
            
            logger.debug(
                f"Retrieved snapshot {snapshot_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return snapshot_dict
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to get snapshot {snapshot_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            raise ContextError(
                message=error_msg,
                error_type=ContextErrorType.VALIDATION_ERROR
            )
    
    async def list_snapshots(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        correlation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List context snapshots.
        
        Args:
            user_id: Filter by user ID
            session_id: Filter by session ID
            limit: Maximum number of snapshots to return
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of snapshots
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Filter snapshots
            snapshots = list(self._snapshots.values())
            
            if user_id:
                snapshots = [s for s in snapshots if s.user_id == user_id]
            
            if session_id:
                snapshots = [s for s in snapshots if s.session_id == session_id]
            
            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda s: s.timestamp, reverse=True)
            
            # Apply limit
            snapshots = snapshots[:limit]
            
            # Convert snapshots to dicts for serialization
            result = []
            for snapshot in snapshots:
                snapshot_dict = {
                    "snapshot_id": snapshot.snapshot_id,
                    "source_agent_id": snapshot.source_agent_id,
                    "target_agent_id": snapshot.target_agent_id,
                    "context_id": snapshot.context_id,
                    "session_id": snapshot.session_id,
                    "user_id": snapshot.user_id,
                    "tenant_id": snapshot.tenant_id,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "strategy": snapshot.strategy.value,
                    "is_restored": snapshot.is_restored,
                    "restored_at": snapshot.restored_at.isoformat() if snapshot.restored_at else None
                }
                result.append(snapshot_dict)
            
            logger.debug(
                f"Listed {len(result)} snapshots",
                extra={"correlation_id": correlation_id}
            )
            
            return result
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to list snapshots: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            raise ContextError(
                message=error_msg,
                error_type=ContextErrorType.VALIDATION_ERROR
            )
    
    async def delete_snapshot(
        self,
        snapshot_id: str,
        correlation_id: Optional[str] = None
    ) -> bool:
        """
        Delete a context snapshot.
        
        Args:
            snapshot_id: Snapshot identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            True if deletion was successful
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            if snapshot_id not in self._snapshots:
                raise ContextError(
                    message=f"Snapshot {snapshot_id} not found",
                    error_type=ContextErrorType.NOT_FOUND
                )
            
            # Delete snapshot
            del self._snapshots[snapshot_id]
            
            logger.info(
                f"Deleted snapshot {snapshot_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return True
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to delete snapshot {snapshot_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            raise ContextError(
                message=error_msg,
                error_type=ContextErrorType.VALIDATION_ERROR
            )
    
    async def _validate_preservation_request(self, request: ContextPreservationRequest) -> None:
        """
        Validate a context preservation request.
        
        Args:
            request: Context preservation request to validate
            
        Raises:
            ContextError: If validation fails
        """
        if not request.context_id:
            raise ContextError(
                message="Context ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
        
        if not request.source_agent_id:
            raise ContextError(
                message="Source agent ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
        
        if not request.target_agent_id:
            raise ContextError(
                message="Target agent ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
        
        if request.source_agent_id == request.target_agent_id:
            raise ContextError(
                message="Source and target agent IDs must be different",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
    
    async def _validate_restoration_request(self, request: ContextRestorationRequest) -> None:
        """
        Validate a context restoration request.
        
        Args:
            request: Context restoration request to validate
            
        Raises:
            ContextError: If validation fails
        """
        if not request.snapshot_id:
            raise ContextError(
                message="Snapshot ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
        
        if not request.target_agent_id:
            raise ContextError(
                message="Target agent ID is required",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
        
        if request.merge_strategy not in ["replace", "merge", "append"]:
            raise ContextError(
                message=f"Invalid merge strategy: {request.merge_strategy}",
                error_type=ContextErrorType.VALIDATION_ERROR
            )
    
    async def _extract_conversation_history(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract conversation history from context."""
        return {
            "messages": getattr(context_data.content, "messages", []),
            "current_message": getattr(context_data.content, "current_message", ""),
            "conversation_summary": getattr(context_data.content, "conversation_summary", "")
        }
    
    async def _extract_user_preferences(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract user preferences from context."""
        return {
            "language": getattr(context_data.content, "language", "en"),
            "theme": getattr(context_data.content, "theme", "default"),
            "response_format": getattr(context_data.content, "response_format", "text"),
            "custom_preferences": getattr(context_data.content, "custom_preferences", {})
        }
    
    async def _extract_session_state(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract session state from context."""
        return {
            "session_variables": getattr(context_data.content, "session_variables", {}),
            "workflow_state": getattr(context_data.content, "workflow_state", {}),
            "active_tools": getattr(context_data.content, "active_tools", []),
            "active_plugins": getattr(context_data.content, "active_plugins", [])
        }
    
    async def _extract_uploaded_files(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract uploaded files from context."""
        files_data = []
        for file_obj in context_data.files:
            files_data.append({
                "file_id": file_obj.file_id,
                "filename": file_obj.filename,
                "file_type": file_obj.file_type,
                "file_size": file_obj.file_size,
                "mime_type": file_obj.mime_type,
                "content_hash": file_obj.content_hash,
                "metadata": file_obj.metadata
            })
        
        return {
            "files": files_data,
            "total_files": len(files_data)
        }
    
    async def _extract_agent_memory(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract agent memory from context."""
        return {
            "short_term_memory": getattr(context_data.content, "short_term_memory", []),
            "long_term_memory": getattr(context_data.content, "long_term_memory", []),
            "working_memory": getattr(context_data.content, "working_memory", {}),
            "memory_summary": getattr(context_data.content, "memory_summary", "")
        }
    
    async def _extract_working_data(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract working data from context."""
        return {
            "variables": getattr(context_data.content, "variables", {}),
            "intermediate_results": getattr(context_data.content, "intermediate_results", []),
            "calculations": getattr(context_data.content, "calculations", {}),
            "scratchpad": getattr(context_data.content, "scratchpad", "")
        }
    
    async def _extract_metadata(self, context_data: ContextData) -> Dict[str, Any]:
        """Extract metadata from context."""
        return {
            "created_at": context_data.created_at.isoformat(),
            "updated_at": context_data.updated_at.isoformat(),
            "tags": context_data.tags,
            "access_level": context_data.access_level.value,
            "expires_at": context_data.expires_at.isoformat() if context_data.expires_at else None,
            "custom_metadata": context_data.metadata
        }
    
    async def _restore_conversation_history(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore conversation history to context."""
        if merge_strategy == "replace":
            # Replace existing conversation history
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            context_data.content["messages"] = element_data.get("messages", [])
            context_data.content["current_message"] = element_data.get("current_message", "")
            context_data.content["conversation_summary"] = element_data.get("conversation_summary", "")
        elif merge_strategy == "merge":
            # Merge with existing conversation history
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            existing_messages = getattr(context_data.content, "messages", [])
            new_messages = element_data.get("messages", [])
            
            # Merge messages, avoiding duplicates
            existing_ids = {msg.get("id") for msg in existing_messages if isinstance(msg, dict) and "id" in msg}
            merged_messages = existing_messages + [msg for msg in new_messages if isinstance(msg, dict) and msg.get("id") not in existing_ids]
            
            context_data.content["messages"] = merged_messages
            context_data.content["current_message"] = element_data.get("current_message", getattr(context_data.content, "current_message", ""))
            context_data.content["conversation_summary"] = element_data.get("conversation_summary", getattr(context_data.content, "conversation_summary", ""))
        elif merge_strategy == "append":
            # Append to existing conversation history
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            existing_messages = getattr(context_data.content, "messages", [])
            new_messages = element_data.get("messages", [])
            
            context_data.content["messages"] = existing_messages + new_messages
            context_data.content["current_message"] = element_data.get("current_message", getattr(context_data.content, "current_message", ""))
            context_data.content["conversation_summary"] = element_data.get("conversation_summary", getattr(context_data.content, "conversation_summary", ""))
    
    async def _restore_user_preferences(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore user preferences to context."""
        if merge_strategy == "replace":
            # Replace existing user preferences
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            context_data.content["language"] = element_data.get("language", "en")
            context_data.content["theme"] = element_data.get("theme", "default")
            context_data.content["response_format"] = element_data.get("response_format", "text")
            context_data.content["custom_preferences"] = element_data.get("custom_preferences", {})
        elif merge_strategy in ["merge", "append"]:
            # Merge with existing user preferences
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            
            context_data.content["language"] = element_data.get("language", getattr(context_data.content, "language", "en"))
            context_data.content["theme"] = element_data.get("theme", getattr(context_data.content, "theme", "default"))
            context_data.content["response_format"] = element_data.get("response_format", getattr(context_data.content, "response_format", "text"))
            
            existing_prefs = getattr(context_data.content, "custom_preferences", {})
            new_prefs = element_data.get("custom_preferences", {})
            
            # Merge preferences
            if merge_strategy == "merge":
                merged_prefs = {**existing_prefs, **new_prefs}
            else:  # append
                merged_prefs = {**new_prefs, **existing_prefs}  # New preferences take precedence
            
            context_data.content["custom_preferences"] = merged_prefs
    
    async def _restore_session_state(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore session state to context."""
        if merge_strategy == "replace":
            # Replace existing session state
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            context_data.content["session_variables"] = element_data.get("session_variables", {})
            context_data.content["workflow_state"] = element_data.get("workflow_state", {})
            context_data.content["active_tools"] = element_data.get("active_tools", [])
            context_data.content["active_plugins"] = element_data.get("active_plugins", [])
        elif merge_strategy in ["merge", "append"]:
            # Merge with existing session state
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            
            existing_vars = getattr(context_data.content, "session_variables", {})
            new_vars = element_data.get("session_variables", {})
            
            existing_workflow = getattr(context_data.content, "workflow_state", {})
            new_workflow = element_data.get("workflow_state", {})
            
            existing_tools = getattr(context_data.content, "active_tools", [])
            new_tools = element_data.get("active_tools", [])
            
            existing_plugins = getattr(context_data.content, "active_plugins", [])
            new_plugins = element_data.get("active_plugins", [])
            
            # Merge session variables
            if merge_strategy == "merge":
                merged_vars = {**existing_vars, **new_vars}
                merged_workflow = {**existing_workflow, **new_workflow}
            else:  # append
                merged_vars = {**new_vars, **existing_vars}  # New variables take precedence
                merged_workflow = {**new_workflow, **existing_workflow}  # New workflow state takes precedence
            
            # Merge tools and plugins (avoid duplicates)
            merged_tools = existing_tools + [tool for tool in new_tools if tool not in existing_tools]
            merged_plugins = existing_plugins + [plugin for plugin in new_plugins if plugin not in existing_plugins]
            
            context_data.content["session_variables"] = merged_vars
            context_data.content["workflow_state"] = merged_workflow
            context_data.content["active_tools"] = merged_tools
            context_data.content["active_plugins"] = merged_plugins
    
    async def _restore_uploaded_files(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore uploaded files to context."""
        # For files, we always append to avoid duplicates
        existing_files = context_data.files
        new_files_data = element_data.get("files", [])
        
        # Get existing file IDs
        existing_file_ids = {f.file_id for f in existing_files}
        
        # Add new files (avoiding duplicates)
        for file_data in new_files_data:
            if file_data.get("file_id") not in existing_file_ids:
                from .context_manager import ContextFile, FileUploadStatus
                context_file = ContextFile(
                    file_id=file_data.get("file_id"),
                    filename=file_data.get("filename"),
                    file_type=file_data.get("file_type"),
                    file_size=file_data.get("file_size"),
                    mime_type=file_data.get("mime_type"),
                    content_hash=file_data.get("content_hash"),
                    upload_status=FileUploadStatus.COMPLETED,
                    upload_timestamp=datetime.utcnow(),
                    metadata=file_data.get("metadata", {}),
                    storage_path=None  # Files are not actually copied, just referenced
                )
                existing_files.append(context_file)
    
    async def _restore_agent_memory(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore agent memory to context."""
        if merge_strategy == "replace":
            # Replace existing agent memory
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            context_data.content["short_term_memory"] = element_data.get("short_term_memory", [])
            context_data.content["long_term_memory"] = element_data.get("long_term_memory", [])
            context_data.content["working_memory"] = element_data.get("working_memory", {})
            context_data.content["memory_summary"] = element_data.get("memory_summary", "")
        elif merge_strategy in ["merge", "append"]:
            # Merge with existing agent memory
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            
            existing_short_term = getattr(context_data.content, "short_term_memory", [])
            new_short_term = element_data.get("short_term_memory", [])
            
            existing_long_term = getattr(context_data.content, "long_term_memory", [])
            new_long_term = element_data.get("long_term_memory", [])
            
            existing_working = getattr(context_data.content, "working_memory", {})
            new_working = element_data.get("working_memory", {})
            
            # Merge memories
            if merge_strategy == "merge":
                merged_short_term = existing_short_term + [item for item in new_short_term if item not in existing_short_term]
                merged_long_term = existing_long_term + [item for item in new_long_term if item not in existing_long_term]
                merged_working = {**existing_working, **new_working}
            else:  # append
                merged_short_term = new_short_term + [item for item in existing_short_term if item not in new_short_term]
                merged_long_term = new_long_term + [item for item in existing_long_term if item not in new_long_term]
                merged_working = {**new_working, **existing_working}  # New working memory takes precedence
            
            context_data.content["short_term_memory"] = merged_short_term
            context_data.content["long_term_memory"] = merged_long_term
            context_data.content["working_memory"] = merged_working
            context_data.content["memory_summary"] = element_data.get("memory_summary", getattr(context_data.content, "memory_summary", ""))
    
    async def _restore_working_data(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore working data to context."""
        if merge_strategy == "replace":
            # Replace existing working data
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            context_data.content["variables"] = element_data.get("variables", {})
            context_data.content["intermediate_results"] = element_data.get("intermediate_results", [])
            context_data.content["calculations"] = element_data.get("calculations", {})
            context_data.content["scratchpad"] = element_data.get("scratchpad", "")
        elif merge_strategy in ["merge", "append"]:
            # Merge with existing working data
            if not hasattr(context_data.content, "__dict__"):
                context_data.content = {}
            
            existing_vars = getattr(context_data.content, "variables", {})
            new_vars = element_data.get("variables", {})
            
            existing_results = getattr(context_data.content, "intermediate_results", [])
            new_results = element_data.get("intermediate_results", [])
            
            existing_calcs = getattr(context_data.content, "calculations", {})
            new_calcs = element_data.get("calculations", {})
            
            # Merge working data
            if merge_strategy == "merge":
                merged_vars = {**existing_vars, **new_vars}
                merged_results = existing_results + [result for result in new_results if result not in existing_results]
                merged_calcs = {**existing_calcs, **new_calcs}
            else:  # append
                merged_vars = {**new_vars, **existing_vars}  # New variables take precedence
                merged_results = new_results + [result for result in existing_results if result not in new_results]
                merged_calcs = {**new_calcs, **existing_calcs}  # New calculations take precedence
            
            context_data.content["variables"] = merged_vars
            context_data.content["intermediate_results"] = merged_results
            context_data.content["calculations"] = merged_calcs
            context_data.content["scratchpad"] = element_data.get("scratchpad", getattr(context_data.content, "scratchpad", ""))
    
    async def _restore_metadata(
        self,
        context_data: ContextData,
        element_data: Dict[str, Any],
        merge_strategy: str
    ) -> None:
        """Restore metadata to context."""
        # For metadata, we always merge
        existing_tags = set(context_data.tags)
        new_tags = set(element_data.get("tags", []))
        
        existing_metadata = context_data.metadata
        new_metadata = element_data.get("custom_metadata", {})
        
        # Merge tags
        merged_tags = list(existing_tags.union(new_tags))
        
        # Merge metadata
        merged_metadata = {**existing_metadata, **new_metadata}
        
        context_data.tags = merged_tags
        context_data.metadata = merged_metadata
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.
        
        Returns:
            Service metrics
        """
        return {
            **self._metrics,
            "total_snapshots": len(self._snapshots),
            "restored_snapshots": len([s for s in self._snapshots.values() if s.is_restored])
        }
    
    async def cleanup_old_snapshots(self, days: int = 30, correlation_id: Optional[str] = None) -> int:
        """
        Clean up old snapshots.
        
        Args:
            days: Number of days after which snapshots are considered old
            correlation_id: Correlation ID for tracking
            
        Returns:
            Number of snapshots cleaned up
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            old_snapshots = [
                s for s in self._snapshots.values() 
                if s.timestamp < cutoff_date and not s.is_restored
            ]
            
            cleanup_count = len(old_snapshots)
            
            # Delete old snapshots
            for snapshot in old_snapshots:
                del self._snapshots[snapshot.snapshot_id]
            
            logger.info(
                f"Cleaned up {cleanup_count} old snapshots",
                extra={"correlation_id": correlation_id}
            )
            
            return cleanup_count
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to cleanup old snapshots: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            return 0
    
    async def shutdown(self) -> None:
        """Shutdown Context Preservation Service."""
        try:
            logger.info("Shutting down Context Preservation Service")
            
            # Clear snapshots
            self._snapshots.clear()
            
            logger.info("Context Preservation Service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during Context Preservation Service shutdown: {e}")