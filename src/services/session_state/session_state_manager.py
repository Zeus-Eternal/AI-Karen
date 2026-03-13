"""
Session State Manager Service

This module provides session state management for the CoPilot Architecture,
including LangGraph checkpoint functionality and integration with the Unified Memory Service.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..memory.unified_memory_service import UnifiedMemoryService
from .langgraph_integration import LangGraphIntegration
from .session_state_models import (
    SessionState,
    SessionCheckpoint,
    SessionStateRequest,
    SessionStateResponse,
    SessionStateUpdateRequest,
    SessionStateListResponse,
    CheckpointListResponse,
    SessionStateError,
    SessionStateErrorType,
    SessionStateStatus
)

logger = logging.getLogger(__name__)


class SessionStateManager:
    """Session State Manager service"""
    
    def __init__(
        self,
        unified_memory_service: Optional[UnifiedMemoryService] = None,
        langgraph_integration: Optional[LangGraphIntegration] = None,
        checkpoint_enabled: bool = True,
        default_session_ttl_seconds: int = 3600
    ):
        """
        Initialize Session State Manager
        
        Args:
            unified_memory_service: Unified Memory Service instance
            langgraph_integration: LangGraph integration instance
            checkpoint_enabled: Whether checkpointing is enabled
            default_session_ttl_seconds: Default session TTL in seconds
        """
        self.unified_memory_service = unified_memory_service
        self.langgraph_integration = langgraph_integration or LangGraphIntegration(
            checkpoint_enabled=checkpoint_enabled
        )
        self.checkpoint_enabled = checkpoint_enabled
        self.default_session_ttl_seconds = default_session_ttl_seconds
        
        # In-memory session storage (in production, this would be a database)
        self._sessions: Dict[str, SessionState] = {}
        self._checkpoints: Dict[str, SessionCheckpoint] = {}
        
        # Metrics
        self._metrics = {
            "sessions_created": 0,
            "sessions_updated": 0,
            "sessions_deleted": 0,
            "checkpoints_created": 0,
            "errors": 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the Session State Manager
        
        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Initializing Session State Manager")
            
            # Initialize LangGraph integration
            if self.langgraph_integration:
                await self.langgraph_integration.initialize()
            
            logger.info("Session State Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Session State Manager: {e}")
            self._metrics["errors"] += 1
            raise SessionStateError(
                message=f"Initialization failed: {str(e)}",
                error_type=SessionStateErrorType.INTEGRATION_ERROR,
                details={"exception": str(e)}
            )
    
    async def create_session(
        self,
        request: SessionStateRequest,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Create a new session
        
        Args:
            request: Session creation request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session creation response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            # Calculate expiration time
            expires_at = None
            if request.expires_in_seconds:
                expires_at = datetime.utcnow() + timedelta(seconds=request.expires_in_seconds)
            
            # Create LangGraph thread if needed
            langgraph_thread_id = request.langgraph_thread_id
            if not langgraph_thread_id and self.langgraph_integration:
                langgraph_thread_id = await self.langgraph_integration.create_thread(
                    session_id=session_id,
                    user_id=request.user_id,
                    tenant_id=request.tenant_id,
                    config=request.langgraph_config
                )
            
            # Create session state
            session_state = SessionState(
                session_id=session_id,
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                langgraph_thread_id=langgraph_thread_id,
                status=SessionStateStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=expires_at,
                state_data=request.initial_state,
                context_data=request.initial_context,
                metadata=request.metadata
            )
            
            # Store session
            self._sessions[session_id] = session_state
            
            # Create initial checkpoint if enabled
            checkpoint = None
            if self.checkpoint_enabled and self.langgraph_integration:
                checkpoint = await self.langgraph_integration.create_checkpoint(
                    session_state=session_state,
                    state_data=request.initial_state,
                    config=request.langgraph_config,
                    checkpoint_type="initial"
                )
                self._checkpoints[checkpoint.checkpoint_id] = checkpoint
                session_state.last_checkpoint_id = checkpoint.checkpoint_id
                session_state.checkpoint_count = 1
            
            # Update metrics
            self._metrics["sessions_created"] += 1
            if checkpoint:
                self._metrics["checkpoints_created"] += 1
            
            logger.info(
                f"Created session {session_id} for user {request.user_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=True,
                session_state=session_state,
                checkpoint=checkpoint,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to create session: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def get_session(
        self,
        session_id: str,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Get a session by ID
        
        Args:
            session_id: Session identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            session_state = self._sessions.get(session_id)
            if not session_state:
                error_msg = f"Session {session_id} not found"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Check if session has expired
            if session_state.expires_at and datetime.utcnow() > session_state.expires_at:
                session_state.status = SessionStateStatus.EXPIRED
                logger.info(
                    f"Session {session_id} has expired",
                    extra={"correlation_id": correlation_id}
                )
            
            logger.debug(
                f"Retrieved session {session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=True,
                session_state=session_state,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to get session {session_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def update_session(
        self,
        session_id: str,
        request: SessionStateUpdateRequest,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Update a session
        
        Args:
            session_id: Session identifier
            request: Session update request
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session update response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            session_state = self._sessions.get(session_id)
            if not session_state:
                error_msg = f"Session {session_id} not found for update"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Update session data
            if request.state_data is not None:
                session_state.state_data.update(request.state_data)
            
            if request.context_data is not None:
                session_state.context_data.update(request.context_data)
            
            if request.metadata is not None:
                session_state.metadata.update(request.metadata)
            
            if request.status is not None:
                session_state.status = request.status
            
            if request.expires_at is not None:
                session_state.expires_at = request.expires_at
            
            session_state.updated_at = datetime.utcnow()
            
            # Create checkpoint if requested
            checkpoint = None
            if request.create_checkpoint and self.langgraph_integration:
                checkpoint = await self.langgraph_integration.create_checkpoint(
                    session_state=session_state,
                    state_data=session_state.state_data,
                    checkpoint_type=request.checkpoint_type
                )
                self._checkpoints[checkpoint.checkpoint_id] = checkpoint
                session_state.last_checkpoint_id = checkpoint.checkpoint_id
                session_state.checkpoint_count += 1
                self._metrics["checkpoints_created"] += 1
            
            # Update metrics
            self._metrics["sessions_updated"] += 1
            
            logger.info(
                f"Updated session {session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=True,
                session_state=session_state,
                checkpoint=checkpoint,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to update session {session_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def delete_session(
        self,
        session_id: str,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session deletion response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            session_state = self._sessions.get(session_id)
            if not session_state:
                error_msg = f"Session {session_id} not found for deletion"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Delete LangGraph thread if exists
            if session_state.langgraph_thread_id and self.langgraph_integration:
                await self.langgraph_integration.delete_thread(session_state.langgraph_thread_id)
            
            # Delete session
            del self._sessions[session_id]
            
            # Update metrics
            self._metrics["sessions_deleted"] += 1
            
            logger.info(
                f"Deleted session {session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=True,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to delete session {session_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        status: Optional[SessionStateStatus] = None,
        limit: int = 50,
        offset: int = 0,
        correlation_id: Optional[str] = None
    ) -> SessionStateListResponse:
        """
        List sessions with filtering
        
        Args:
            user_id: Filter by user ID (optional)
            tenant_id: Filter by tenant ID (optional)
            status: Filter by status (optional)
            limit: Maximum number of sessions to return
            offset: Offset for pagination
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session list response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            sessions = list(self._sessions.values())
            
            # Apply filters
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
            
            if tenant_id:
                sessions = [s for s in sessions if s.tenant_id == tenant_id]
            
            if status:
                sessions = [s for s in sessions if s.status == status]
            
            # Apply pagination
            total_count = len(sessions)
            sessions = sessions[offset:offset + limit]
            
            logger.debug(
                f"Listed {len(sessions)} sessions (total: {total_count})",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateListResponse(
                success=True,
                sessions=sessions,
                total_count=total_count,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to list sessions: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateListResponse(
                success=False,
                sessions=[],
                total_count=0,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def create_checkpoint(
        self,
        session_id: str,
        checkpoint_type: str = "manual",
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Create a checkpoint for a session
        
        Args:
            session_id: Session identifier
            checkpoint_type: Type of checkpoint
            metadata: Additional metadata
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session response with checkpoint
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            session_state = self._sessions.get(session_id)
            if not session_state:
                error_msg = f"Session {session_id} not found for checkpoint creation"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            if not self.langgraph_integration:
                error_msg = "LangGraph integration not available for checkpoint creation"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Create checkpoint
            checkpoint = await self.langgraph_integration.create_checkpoint(
                session_state=session_state,
                state_data=session_state.state_data,
                checkpoint_type=checkpoint_type
            )
            
            # Update checkpoint metadata
            if metadata:
                checkpoint.metadata.update(metadata)
            
            # Store checkpoint
            self._checkpoints[checkpoint.checkpoint_id] = checkpoint
            
            # Update session
            session_state.last_checkpoint_id = checkpoint.checkpoint_id
            session_state.checkpoint_count += 1
            session_state.updated_at = datetime.utcnow()
            
            # Update metrics
            self._metrics["checkpoints_created"] += 1
            
            logger.info(
                f"Created checkpoint {checkpoint.checkpoint_id} for session {session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=True,
                session_state=session_state,
                checkpoint=checkpoint,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to create checkpoint for session {session_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def get_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
        correlation_id: Optional[str] = None
    ) -> CheckpointListResponse:
        """
        Get a checkpoint by ID
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Checkpoint response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if not checkpoint:
                error_msg = f"Checkpoint {checkpoint_id} not found"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return CheckpointListResponse(
                    success=False,
                    checkpoints=[],
                    total_count=0,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Verify checkpoint belongs to session
            if checkpoint.session_id != session_id:
                error_msg = f"Checkpoint {checkpoint_id} does not belong to session {session_id}"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return CheckpointListResponse(
                    success=False,
                    checkpoints=[],
                    total_count=0,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            logger.debug(
                f"Retrieved checkpoint {checkpoint_id} for session {session_id}",
                extra={"correlation_id": correlation_id}
            )
            
            return CheckpointListResponse(
                success=True,
                checkpoints=[checkpoint],
                total_count=1,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to get checkpoint {checkpoint_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return CheckpointListResponse(
                success=False,
                checkpoints=[],
                total_count=0,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def list_checkpoints(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        correlation_id: Optional[str] = None
    ) -> CheckpointListResponse:
        """
        List checkpoints for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of checkpoints to return
            offset: Offset for pagination
            correlation_id: Correlation ID for tracking
            
        Returns:
            Checkpoint list response
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Get all checkpoints for the session
            checkpoints = [
                cp for cp in self._checkpoints.values()
                if cp.session_id == session_id
            ]
            
            # Sort by creation time (newest first)
            checkpoints.sort(key=lambda cp: cp.created_at, reverse=True)
            
            # Apply pagination
            total_count = len(checkpoints)
            checkpoints = checkpoints[offset:offset + limit]
            
            logger.debug(
                f"Listed {len(checkpoints)} checkpoints for session {session_id} (total: {total_count})",
                extra={"correlation_id": correlation_id}
            )
            
            return CheckpointListResponse(
                success=True,
                checkpoints=checkpoints,
                total_count=total_count,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to list checkpoints for session {session_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return CheckpointListResponse(
                success=False,
                checkpoints=[],
                total_count=0,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def restore_from_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str,
        correlation_id: Optional[str] = None
    ) -> SessionStateResponse:
        """
        Restore session state from a checkpoint
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
            correlation_id: Correlation ID for tracking
            
        Returns:
            Session response with restored state
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            session_state = self._sessions.get(session_id)
            if not session_state:
                error_msg = f"Session {session_id} not found for restore"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            checkpoint = self._checkpoints.get(checkpoint_id)
            if not checkpoint:
                error_msg = f"Checkpoint {checkpoint_id} not found"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Verify checkpoint belongs to session
            if checkpoint.session_id != session_id:
                error_msg = f"Checkpoint {checkpoint_id} does not belong to session {session_id}"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
            # Restore state using LangGraph integration
            if self.langgraph_integration:
                restored_state = await self.langgraph_integration.restore_from_checkpoint(
                    session_state=session_state,
                    checkpoint_id=checkpoint_id
                )
                
                # Update session state
                session_state.state_data = restored_state
                session_state.context_data = checkpoint.context_data
                session_state.metadata = checkpoint.metadata
                session_state.updated_at = datetime.utcnow()
                
                logger.info(
                    f"Restored session {session_id} from checkpoint {checkpoint_id}",
                    extra={"correlation_id": correlation_id}
                )
                
                return SessionStateResponse(
                    success=True,
                    session_state=session_state,
                    checkpoint=checkpoint,
                    correlation_id=correlation_id
                )
            else:
                error_msg = "LangGraph integration not available for restore"
                logger.warning(
                    error_msg,
                    extra={"correlation_id": correlation_id}
                )
                return SessionStateResponse(
                    success=False,
                    error_message=error_msg,
                    correlation_id=correlation_id
                )
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to restore session {session_id} from checkpoint {checkpoint_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            return SessionStateResponse(
                success=False,
                error_message=error_msg,
                correlation_id=correlation_id
            )
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics
        
        Returns:
            Service metrics
        """
        return {
            **self._metrics,
            "active_sessions": len(self._sessions),
            "total_checkpoints": len(self._checkpoints),
            "checkpoint_enabled": self.checkpoint_enabled
        }
    
    async def cleanup_expired_sessions(self, correlation_id: Optional[str] = None) -> int:
        """
        Clean up expired sessions
        
        Args:
            correlation_id: Correlation ID for tracking
            
        Returns:
            Number of sessions cleaned up
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            now = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, session in self._sessions.items()
                if session.expires_at and now > session.expires_at
            ]
            
            cleanup_count = 0
            for session_id in expired_sessions:
                response = await self.delete_session(session_id, correlation_id)
                if response.success:
                    cleanup_count += 1
            
            logger.info(
                f"Cleaned up {cleanup_count} expired sessions",
                extra={"correlation_id": correlation_id}
            )
            
            return cleanup_count
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Failed to cleanup expired sessions: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            return 0
    
    async def shutdown(self) -> None:
        """Shutdown the Session State Manager"""
        try:
            logger.info("Shutting down Session State Manager")
            
            # Shutdown LangGraph integration
            if self.langgraph_integration:
                await self.langgraph_integration.shutdown()
            
            # Clear in-memory storage
            self._sessions.clear()
            self._checkpoints.clear()
            
            logger.info("Session State Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during Session State Manager shutdown: {e}")