"""
Thread Manager for CoPilot Architecture

This service provides comprehensive thread management capabilities for the CoPilot Architecture,
including session-to-thread mapping, thread lifecycle management, and thread persistence.
"""

import asyncio
import logging
import time
import uuid
import json
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from .thread_manager_models import (
    # Enums
    ThreadStatus,
    ThreadType,
    
    # Request/Response Models
    CreateThreadRequest,
    CreateThreadResponse,
    GetThreadRequest,
    GetThreadResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
    DeleteThreadRequest,
    DeleteThreadResponse,
    ListThreadsRequest,
    ListThreadsResponse,
    GetSessionThreadsRequest,
    GetSessionThreadsResponse,
    SetPrimaryThreadRequest,
    SetPrimaryThreadResponse,
    
    # Data Models
    Thread,
    SessionThreadMapping,
    ThreadManagerConfig,
    ThreadManagerStatus,
    ThreadManagerMetrics,
    ThreadManagerError
)

# Try to import LangGraph integration
try:
    from src.services.langgraph.langgraph_integration import LangGraphIntegration
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    LangGraphIntegration = None

# Try to import persistence services
try:
    from src.services.persistence.persistence_service import PersistenceService
    HAS_PERSISTENCE = True
except ImportError:
    HAS_PERSISTENCE = False
    PersistenceService = None

# Try to import Session State Manager
try:
    from src.services.session_state.session_state_manager import SessionStateManager
    from src.services.session_state.session_state_models import SessionState
    HAS_SESSION_STATE = True
except ImportError:
    HAS_SESSION_STATE = False
    SessionStateManager = None
    SessionState = None

logger = logging.getLogger(__name__)


class ThreadManagerInterface:
    """
    Interface for the Thread Manager.
    
    This interface defines the contract for the Thread Manager,
    ensuring consistency across different implementations.
    """
    
    async def create_thread(self, request: CreateThreadRequest) -> CreateThreadResponse:
        """
        Create a new thread.
        
        Args:
            request: The create thread request
            
        Returns:
            The create thread response
        """
        raise NotImplementedError("create_thread not implemented")
    
    async def get_thread(self, request: GetThreadRequest) -> GetThreadResponse:
        """
        Get a thread by ID.
        
        Args:
            request: The get thread request
            
        Returns:
            The get thread response
        """
        raise NotImplementedError("get_thread not implemented")
    
    async def update_thread(self, request: UpdateThreadRequest) -> UpdateThreadResponse:
        """
        Update a thread.
        
        Args:
            request: The update thread request
            
        Returns:
            The update thread response
        """
        raise NotImplementedError("update_thread not implemented")
    
    async def delete_thread(self, request: DeleteThreadRequest) -> DeleteThreadResponse:
        """
        Delete a thread.
        
        Args:
            request: The delete thread request
            
        Returns:
            The delete thread response
        """
        raise NotImplementedError("delete_thread not implemented")
    
    async def list_threads(self, request: ListThreadsRequest) -> ListThreadsResponse:
        """
        List threads based on filters.
        
        Args:
            request: The list threads request
            
        Returns:
            The list threads response
        """
        raise NotImplementedError("list_threads not implemented")
    
    async def get_session_threads(self, request: GetSessionThreadsRequest) -> GetSessionThreadsResponse:
        """
        Get all threads for a session.
        
        Args:
            request: The get session threads request
            
        Returns:
            The get session threads response
        """
        raise NotImplementedError("get_session_threads not implemented")
    
    async def set_primary_thread(self, request: SetPrimaryThreadRequest) -> SetPrimaryThreadResponse:
        """
        Set the primary thread for a session.
        
        Args:
            request: The set primary thread request
            
        Returns:
            The set primary thread response
        """
        raise NotImplementedError("set_primary_thread not implemented")
    
    async def get_langgraph_thread(self, session_id: str) -> Optional[str]:
        """
        Get the LangGraph thread ID for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            LangGraph thread ID if available, None otherwise
        """
        raise NotImplementedError("get_langgraph_thread not implemented")
    
    async def get_service_status(self) -> ThreadManagerStatus:
        """
        Get the status of the Thread Manager.
        
        Returns:
            The service status
        """
        raise NotImplementedError("get_service_status not implemented")
    
    async def get_service_metrics(self) -> ThreadManagerMetrics:
        """
        Get the metrics of the Thread Manager.
        
        Returns:
            The service metrics
        """
        raise NotImplementedError("get_service_metrics not implemented")


class ThreadManager(BaseService, ThreadManagerInterface):
    """
    Thread Manager implementation for the CoPilot Architecture.
    
    This service provides comprehensive thread management capabilities, including
    session-to-thread mapping, thread lifecycle management, and thread persistence.
    
    Features:
    - Session-to-thread mapping with primary thread support
    - Thread lifecycle management (create, update, delete, archive, restore)
    - Thread persistence with configurable storage backends
    - Integration with LangGraph for thread management
    - Thread expiration and archival policies
    - Comprehensive error handling and logging
    - Metrics collection and monitoring
    
    Example:
        ```python
        # Initialize the thread manager
        thread_manager = ThreadManager()
        await thread_manager.initialize()
        
        # Create a thread for a session
        create_request = CreateThreadRequest(
            session_id="session123",
            thread_type=ThreadType.CONVERSATION,
            title="Customer Support Chat",
            description="Conversation with customer about account issues"
        )
        create_response = await thread_manager.create_thread(create_request)
        
        # Get the thread
        get_request = GetThreadRequest(thread_id=create_response.thread_id)
        get_response = await thread_manager.get_thread(get_request)
        
        # List all threads for a session
        list_request = ListThreadsRequest(session_id="session123")
        list_response = await thread_manager.list_threads(list_request)
        
        # Set primary thread for a session
        set_primary_request = SetPrimaryThreadRequest(
            session_id="session123",
            thread_id=create_response.thread_id
        )
        set_primary_response = await thread_manager.set_primary_thread(set_primary_request)
        
        # Get LangGraph thread ID
        langgraph_thread_id = await thread_manager.get_langgraph_thread("session123")
        print(f"LangGraph thread ID: {langgraph_thread_id}")
        ```
    
    Error Handling:
        The service implements comprehensive error handling with proper logging and graceful
        degradation when dependencies are unavailable. All methods log errors with context
        and provide meaningful error messages.
        
    Performance Considerations:
        - Async/await pattern for non-blocking operations
        - Configurable batch sizes for bulk operations
        - Memory usage monitoring and cleanup
        - Operation metrics collection
    """
    
    def __init__(self, config: Optional[ThreadManagerConfig] = None):
        """
        Initialize the Thread Manager.
        
        Args:
            config: Configuration for the service
        """
        service_config = ServiceConfig(
            name=config.service_name if config else "thread_manager"
        )
        super().__init__(service_config)
        
        self._config = config or ThreadManagerConfig()
        self._initialized = False
        self._start_time = datetime.utcnow()
        
        # Thread storage
        self._threads: Dict[str, Thread] = {}
        self._session_mappings: Dict[str, SessionThreadMapping] = {}
        self._primary_threads: Dict[str, str] = {}  # session_id -> thread_id
        
        # Dependencies
        self._langgraph_integration = None
        self._persistence_service = None
        self._session_state_manager = None
        
        # Metrics
        self._metrics = ThreadManagerMetrics()
        
        # Lock for thread operations
        self._lock = asyncio.Lock()
        
        # Background tasks
        self._persistence_task = None
        self._cleanup_task = None
        
        # Set up logging
        self.logger = logging.getLogger(self._config.service_name)
        if self._config.enable_logging:
            self.logger.setLevel(getattr(logging, self._config.log_level))
    
    async def initialize(self) -> bool:
        """
        Initialize the Thread Manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            self.logger.info("Initializing Thread Manager")
            
            # Initialize LangGraph integration if enabled
            if HAS_LANGGRAPH and LangGraphIntegration:
                try:
                    self._langgraph_integration = LangGraphIntegration()
                    await self._langgraph_integration.initialize()
                    self.logger.debug("LangGraph integration initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize LangGraph integration: {e}")
                    self._langgraph_integration = None
            
            # Initialize persistence service if enabled
            if HAS_PERSISTENCE and PersistenceService and self._config.enable_thread_persistence:
                try:
                    self._persistence_service = PersistenceService()
                    await self._persistence_service.initialize()
                    self.logger.debug("Persistence service initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize persistence service: {e}")
                    self._persistence_service = None
            
            # Initialize Session State Manager if available
            if HAS_SESSION_STATE and SessionStateManager:
                try:
                    self._session_state_manager = SessionStateManager()
                    await self._session_state_manager.initialize()
                    self.logger.debug("Session State Manager initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize Session State Manager: {e}")
                    self._session_state_manager = None
            
            # Load persisted data if available
            await self._load_persisted_data()
            
            # Start background tasks
            self._persistence_task = asyncio.create_task(self._persistence_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self._initialized = True
            self.logger.info("Thread Manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Thread Manager: {e}")
            self.logger.debug(f"Initialization error traceback: {traceback.format_exc()}")
            return False
    
    async def _load_persisted_data(self) -> None:
        """Load persisted data from storage."""
        try:
            if self._persistence_service:
                # Load threads
                persisted_threads = await self._persistence_service.load("threads")
                if persisted_threads:
                    for thread_data in persisted_threads:
                        thread = Thread(**thread_data)
                        self._threads[thread.thread_id] = thread
                
                # Load session mappings
                persisted_mappings = await self._persistence_service.load("session_mappings")
                if persisted_mappings:
                    for mapping_data in persisted_mappings:
                        mapping = SessionThreadMapping(**mapping_data)
                        self._session_mappings[mapping.session_id] = mapping
                        
                        # Update primary threads
                        if mapping.primary_thread_id:
                            self._primary_threads[mapping.session_id] = mapping.primary_thread_id
                
                self.logger.info(f"Loaded {len(persisted_threads)} threads and {len(persisted_mappings)} session mappings")
        except Exception as e:
            self.logger.error(f"Failed to load persisted data: {e}")
    
    async def shutdown(self) -> bool:
        """
        Shutdown the Thread Manager.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        try:
            self.logger.info("Shutting down Thread Manager")
            
            # Cancel background tasks
            if self._persistence_task:
                self._persistence_task.cancel()
                try:
                    await self._persistence_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Persist data if enabled
            if self._persistence_service:
                await self._persist_data()
                
                # Shutdown persistence service
                await self._persistence_service.shutdown()
            
            # Shutdown LangGraph integration
            if self._langgraph_integration:
                await self._langgraph_integration.shutdown()
            
            # Shutdown Session State Manager
            if self._session_state_manager:
                await self._session_state_manager.shutdown()
            
            # Clear service state
            async with self._lock:
                self._threads.clear()
                self._session_mappings.clear()
                self._primary_threads.clear()
            
            self._initialized = False
            self.logger.info("Thread Manager shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Thread Manager: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check the health of the Thread Manager.
        
        Returns:
            True if the service is healthy, False otherwise
        """
        return self._initialized
    
    async def _persistence_loop(self) -> None:
        """Background task for periodic persistence."""
        while self._initialized:
            try:
                # Persist data
                await self._persist_data()
                
                # Wait for next persistence interval
                await asyncio.sleep(self._config.persistence_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in persistence loop: {e}")
                # Wait before retrying
                await asyncio.sleep(10)
    
    async def _persist_data(self) -> None:
        """Persist data to storage."""
        if not self._persistence_service:
            return
        
        try:
            # Prepare threads data
            threads_data = [thread.model_dump() for thread in self._threads.values()]
            
            # Prepare session mappings data
            mappings_data = [mapping.model_dump() for mapping in self._session_mappings.values()]
            
            # Persist data
            await self._persistence_service.save("threads", threads_data)
            await self._persistence_service.save("session_mappings", mappings_data)
            
            # Update metrics
            self._metrics.persistence_operations += 1
            
            self.logger.debug(f"Persisted {len(threads_data)} threads and {len(mappings_data)} session mappings")
        except Exception as e:
            self.logger.error(f"Failed to persist data: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for periodic cleanup."""
        while self._initialized:
            try:
                # Perform cleanup
                await self._perform_cleanup()
                
                # Wait for next cleanup interval (1 hour)
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                # Wait before retrying
                await asyncio.sleep(60)
    
    async def _perform_cleanup(self) -> None:
        """Perform cleanup operations."""
        try:
            now = datetime.utcnow()
            cleanup_count = 0
            
            async with self._lock:
                # Archive inactive threads if enabled
                if self._config.enable_thread_archiving:
                    inactive_threshold = now - timedelta(days=self._config.archive_inactive_threads_days)
                    
                    for thread in self._threads.values():
                        if (thread.status == ThreadStatus.ACTIVE and 
                            thread.updated_at < inactive_threshold):
                            # Archive thread
                            thread.status = ThreadStatus.ARCHIVED
                            thread.archived_at = now
                            cleanup_count += 1
                
                # Delete expired threads if enabled
                if self._config.enable_thread_expiration:
                    for thread_id, thread in list(self._threads.items()):
                        if thread.expires_at and thread.expires_at < now:
                            # Delete expired thread
                            await self._delete_thread_internal(thread_id, hard_delete=True)
                            cleanup_count += 1
            
            if cleanup_count > 0:
                self.logger.info(f"Cleaned up {cleanup_count} threads")
        except Exception as e:
            self.logger.error(f"Failed to perform cleanup: {e}")
    
    async def create_thread(self, request: CreateThreadRequest) -> CreateThreadResponse:
        """
        Create a new thread.
        
        Args:
            request: The create thread request
            
        Returns:
            The create thread response
        """
        if not self._initialized:
            return CreateThreadResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            # Update metrics
            self._metrics.threads_created += 1
            
            # Generate thread ID
            thread_id = str(uuid.uuid4())
            
            # Create thread
            thread = Thread(
                thread_id=thread_id,
                session_id=request.session_id,
                thread_type=request.thread_type,
                title=request.title,
                description=request.description,
                langgraph_thread_id=request.langgraph_thread_id,
                parent_thread_id=request.parent_thread_id,
                tags=request.tags,
                data=request.data,
                metadata=request.metadata,
                expires_at=request.expires_at
            )
            
            # Get or create session mapping
            async with self._lock:
                # Store thread
                self._threads[thread_id] = thread
                
                # Update session mapping
                if request.session_id not in self._session_mappings:
                    # Create new session mapping
                    session_mapping = SessionThreadMapping(
                        session_id=request.session_id,
                        thread_ids=[thread_id]
                    )
                    self._session_mappings[request.session_id] = session_mapping
                    self._metrics.session_mappings_created += 1
                else:
                    # Add thread to existing session mapping
                    session_mapping = self._session_mappings[request.session_id]
                    if thread_id not in session_mapping.thread_ids:
                        session_mapping.thread_ids.append(thread_id)
                
                # Set as primary thread if it's the first thread for the session
                if request.session_id not in self._primary_threads:
                    self._primary_threads[request.session_id] = thread_id
                    session_mapping.primary_thread_id = thread_id
                
                # Update parent thread if specified
                if request.parent_thread_id and request.parent_thread_id in self._threads:
                    parent_thread = self._threads[request.parent_thread_id]
                    if thread_id not in parent_thread.child_thread_ids:
                        parent_thread.child_thread_ids.append(thread_id)
            
            # Create LangGraph thread if requested
            if request.langgraph_thread_id is None and self._langgraph_integration:
                try:
                    langgraph_thread_id = await self._langgraph_integration.create_thread(
                        session_id=request.session_id,
                        thread_type=request.thread_type.value,
                        title=request.title or f"Thread {thread_id[:8]}"
                    )
                    
                    # Update thread with LangGraph thread ID
                    thread.langgraph_thread_id = langgraph_thread_id
                    self._metrics.langgraph_threads_created += 1
                except Exception as e:
                    self.logger.error(f"Failed to create LangGraph thread: {e}")
            
            # Create session state if Session State Manager is available
            if self._session_state_manager and SessionState:
                try:
                    from src.services.session_state.session_state_models import CreateSessionStateRequest
                    session_state_request = CreateSessionStateRequest(
                        session_id=request.session_id,
                        user_id=request.metadata.get("user_id", "") if request.metadata else "",
                        thread_id=thread_id,
                        langgraph_thread_id=thread.langgraph_thread_id,
                        metadata=request.metadata or {}
                    )
                    session_state_response = await self._session_state_manager.create_session_state(session_state_request)
                    if session_state_response.success:
                        self.logger.debug(f"Created session state for session {request.session_id}")
                    else:
                        self.logger.error(f"Failed to create session state: {session_state_response.error}")
                except Exception as e:
                    self.logger.error(f"Error creating session state: {e}")
            
            # Persist data if enabled
            if self._persistence_service:
                await self._persist_data()
            
            return CreateThreadResponse(
                success=True,
                thread_id=thread_id,
                thread=thread,
                message="Thread created successfully"
            )
        except Exception as e:
            # Update metrics
            self._metrics.errors_encountered += 1
            
            self.logger.error(f"Error creating thread: {e}")
            
            return CreateThreadResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def get_thread(self, request: GetThreadRequest) -> GetThreadResponse:
        """
        Get a thread by ID.
        
        Args:
            request: The get thread request
            
        Returns:
            The get thread response
        """
        if not self._initialized:
            return GetThreadResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            async with self._lock:
                thread = self._threads.get(request.thread_id)
                
                if not thread:
                    return GetThreadResponse(
                        success=False,
                        message=f"Thread {request.thread_id} not found",
                        error="Thread not found"
                    )
                
                # Return a copy of the thread
                thread_copy = thread.model_copy(deep=True)
                
                # Exclude data and metadata if requested
                if not request.include_data:
                    thread_copy.data = {}
                
                if not request.include_metadata:
                    thread_copy.metadata = {}
                
                # Get session state if Session State Manager is available
                if self._session_state_manager:
                    try:
                        from src.services.session_state.session_state_models import GetSessionStateRequest
                        session_state_request = GetSessionStateRequest(
                            session_id=thread.session_id,
                            thread_id=request.thread_id
                        )
                        session_state_response = await self._session_state_manager.get_session_state(session_state_request)
                        if session_state_response.success and session_state_response.session_state:
                            # Add session state data to thread
                            thread_copy.session_state = session_state_response.session_state
                    except Exception as e:
                        self.logger.error(f"Error getting session state: {e}")
                
                return GetThreadResponse(
                    success=True,
                    thread=thread_copy,
                    message="Thread retrieved successfully"
                )
        except Exception as e:
            self.logger.error(f"Error getting thread: {e}")
            
            return GetThreadResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def update_thread(self, request: UpdateThreadRequest) -> UpdateThreadResponse:
        """
        Update a thread.
        
        Args:
            request: The update thread request
            
        Returns:
            The update thread response
        """
        if not self._initialized:
            return UpdateThreadResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            # Update metrics
            self._metrics.threads_updated += 1
            
            async with self._lock:
                thread = self._threads.get(request.thread_id)
                
                if not thread:
                    return UpdateThreadResponse(
                        success=False,
                        message=f"Thread {request.thread_id} not found",
                        error="Thread not found"
                    )
                
                # Update thread fields
                if request.title is not None:
                    thread.title = request.title
                
                if request.description is not None:
                    thread.description = request.description
                
                if request.status is not None:
                    thread.status = request.status
                
                if request.tags is not None:
                    thread.tags = request.tags
                
                if request.data is not None:
                    thread.data.update(request.data)
                
                if request.metadata is not None:
                    thread.metadata.update(request.metadata)
                
                if request.expires_at is not None:
                    thread.expires_at = request.expires_at
                
                # Update timestamp
                thread.updated_at = datetime.utcnow()
                
                # Update LangGraph thread if applicable
                if thread.langgraph_thread_id and self._langgraph_integration:
                    try:
                        await self._langgraph_integration.update_thread(
                            thread_id=thread.langgraph_thread_id,
                            title=thread.title,
                            status=thread.status.value
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to update LangGraph thread: {e}")
                
                # Update session state if Session State Manager is available
                if self._session_state_manager:
                    try:
                        from src.services.session_state.session_state_models import UpdateSessionStateRequest
                        session_state_request = UpdateSessionStateRequest(
                            session_id=thread.session_id,
                            thread_id=request.thread_id,
                            metadata=thread.metadata
                        )
                        session_state_response = await self._session_state_manager.update_session_state(session_state_request)
                        if not session_state_response.success:
                            self.logger.error(f"Failed to update session state: {session_state_response.error}")
                    except Exception as e:
                        self.logger.error(f"Error updating session state: {e}")
                
                # Persist data if enabled
                if self._persistence_service:
                    await self._persist_data()
                
                return UpdateThreadResponse(
                    success=True,
                    thread_id=request.thread_id,
                    thread=thread,
                    message="Thread updated successfully"
                )
        except Exception as e:
            self.logger.error(f"Error updating thread: {e}")
            
            return UpdateThreadResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def delete_thread(self, request: DeleteThreadRequest) -> DeleteThreadResponse:
        """
        Delete a thread.
        
        Args:
            request: The delete thread request
            
        Returns:
            The delete thread response
        """
        if not self._initialized:
            return DeleteThreadResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            # Update metrics
            self._metrics.threads_deleted += 1
            
            # Perform internal delete
            result = await self._delete_thread_internal(request.thread_id, request.hard_delete)
            
            if result:
                # Persist data if enabled
                if self._persistence_service:
                    await self._persist_data()
                
                return DeleteThreadResponse(
                    success=True,
                    thread_id=request.thread_id,
                    message="Thread deleted successfully"
                )
            else:
                return DeleteThreadResponse(
                    success=False,
                    message=f"Thread {request.thread_id} not found",
                    error="Thread not found"
                )
        except Exception as e:
            self.logger.error(f"Error deleting thread: {e}")
            
            return DeleteThreadResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def _delete_thread_internal(self, thread_id: str, hard_delete: bool = False) -> bool:
        """
        Internal method to delete a thread.
        
        Args:
            thread_id: ID of the thread to delete
            hard_delete: Whether to permanently delete the thread
            
        Returns:
            True if deletion was successful, False otherwise
        """
        async with self._lock:
            thread = self._threads.get(thread_id)
            if not thread:
                return False
            
            if hard_delete:
                # Remove from threads storage
                del self._threads[thread_id]
                
                # Remove from session mappings
                session_mapping = self._session_mappings.get(thread.session_id)
                if session_mapping and thread_id in session_mapping.thread_ids:
                    session_mapping.thread_ids.remove(thread_id)
                    
                    # Update primary thread if needed
                    if session_mapping.primary_thread_id == thread_id:
                        if session_mapping.thread_ids:
                            # Set first remaining thread as primary
                            session_mapping.primary_thread_id = session_mapping.thread_ids[0]
                            self._primary_threads[thread.session_id] = session_mapping.thread_ids[0]
                        else:
                            # No threads left for session
                            session_mapping.primary_thread_id = None
                            if thread.session_id in self._primary_threads:
                                del self._primary_threads[thread.session_id]
                
                # Remove from parent's child threads
                if thread.parent_thread_id and thread.parent_thread_id in self._threads:
                    parent_thread = self._threads[thread.parent_thread_id]
                    if thread_id in parent_thread.child_thread_ids:
                        parent_thread.child_thread_ids.remove(thread_id)
                
                # Delete LangGraph thread if applicable
                if thread.langgraph_thread_id and self._langgraph_integration:
                    try:
                        await self._langgraph_integration.delete_thread(thread.langgraph_thread_id)
                    except Exception as e:
                        self.logger.error(f"Failed to delete LangGraph thread: {e}")
                
                # Delete session state if Session State Manager is available
                if self._session_state_manager:
                    try:
                        from src.services.session_state.session_state_models import DeleteSessionStateRequest
                        session_state_request = DeleteSessionStateRequest(
                            session_id=thread.session_id,
                            thread_id=thread_id
                        )
                        session_state_response = await self._session_state_manager.delete_session_state(session_state_request)
                        if not session_state_response.success:
                            self.logger.error(f"Failed to delete session state: {session_state_response.error}")
                    except Exception as e:
                        self.logger.error(f"Error deleting session state: {e}")
            else:
                # Soft delete - just mark as deleted
                thread.status = ThreadStatus.DELETED
            
            return True
    
    async def list_threads(self, request: ListThreadsRequest) -> ListThreadsResponse:
        """
        List threads based on filters.
        
        Args:
            request: The list threads request
            
        Returns:
            The list threads response
        """
        if not self._initialized:
            return ListThreadsResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            async with self._lock:
                # Filter threads
                filtered_threads = []
                
                for thread in self._threads.values():
                    # Apply filters
                    if request.session_id and thread.session_id != request.session_id:
                        continue
                    
                    if request.thread_type and thread.thread_type != request.thread_type:
                        continue
                    
                    if request.status and thread.status != request.status:
                        continue
                    
                    if request.parent_thread_id and thread.parent_thread_id != request.parent_thread_id:
                        continue
                    
                    if request.tags and not any(tag in thread.tags for tag in request.tags):
                        continue
                    
                    if not request.include_archived and thread.status == ThreadStatus.ARCHIVED:
                        continue
                    
                    if not request.include_deleted and thread.status == ThreadStatus.DELETED:
                        continue
                    
                    filtered_threads.append(thread)
                
                # Sort by creation time (newest first)
                filtered_threads.sort(key=lambda t: t.created_at, reverse=True)
                
                # Apply pagination
                total_count = len(filtered_threads)
                start_idx = request.offset
                end_idx = start_idx + request.limit
                paginated_threads = filtered_threads[start_idx:end_idx]
                
                return ListThreadsResponse(
                    success=True,
                    threads=paginated_threads,
                    total_count=total_count,
                    message=f"Listed {len(paginated_threads)} of {total_count} threads"
                )
        except Exception as e:
            self.logger.error(f"Error listing threads: {e}")
            
            return ListThreadsResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def get_session_threads(self, request: GetSessionThreadsRequest) -> GetSessionThreadsResponse:
        """
        Get all threads for a session.
        
        Args:
            request: The get session threads request
            
        Returns:
            The get session threads response
        """
        if not self._initialized:
            return GetSessionThreadsResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            async with self._lock:
                # Get session mapping
                session_mapping = self._session_mappings.get(request.session_id)
                
                if not session_mapping:
                    return GetSessionThreadsResponse(
                        success=True,
                        session_id=request.session_id,
                        primary_thread_id=None,
                        threads=[],
                        message="No threads found for session"
                    )
                
                # Get threads for session
                threads = []
                for thread_id in session_mapping.thread_ids:
                    thread = self._threads.get(thread_id)
                    if thread:
                        # Apply filters
                        if not request.include_archived and thread.status == ThreadStatus.ARCHIVED:
                            continue
                        
                        if not request.include_deleted and thread.status == ThreadStatus.DELETED:
                            continue
                        
                        threads.append(thread)
                
                # Sort by creation time (newest first)
                threads.sort(key=lambda t: t.created_at, reverse=True)
                
                return GetSessionThreadsResponse(
                    success=True,
                    session_id=request.session_id,
                    primary_thread_id=session_mapping.primary_thread_id,
                    threads=threads,
                    message=f"Retrieved {len(threads)} threads for session"
                )
        except Exception as e:
            self.logger.error(f"Error getting session threads: {e}")
            
            return GetSessionThreadsResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def set_primary_thread(self, request: SetPrimaryThreadRequest) -> SetPrimaryThreadResponse:
        """
        Set the primary thread for a session.
        
        Args:
            request: The set primary thread request
            
        Returns:
            The set primary thread response
        """
        if not self._initialized:
            return SetPrimaryThreadResponse(
                success=False,
                message="Thread Manager is not initialized",
                error="Service not initialized"
            )
        
        try:
            # Update metrics
            self._metrics.primary_threads_set += 1
            
            async with self._lock:
                # Check if thread exists
                thread = self._threads.get(request.thread_id)
                if not thread:
                    return SetPrimaryThreadResponse(
                        success=False,
                        message=f"Thread {request.thread_id} not found",
                        error="Thread not found"
                    )
                
                # Check if thread belongs to session
                if thread.session_id != request.session_id:
                    return SetPrimaryThreadResponse(
                        success=False,
                        message=f"Thread {request.thread_id} does not belong to session {request.session_id}",
                        error="Thread does not belong to session"
                    )
                
                # Get or create session mapping
                session_mapping = self._session_mappings.get(request.session_id)
                if not session_mapping:
                    # Create new session mapping
                    session_mapping = SessionThreadMapping(
                        session_id=request.session_id,
                        thread_ids=[request.thread_id]
                    )
                    self._session_mappings[request.session_id] = session_mapping
                    self._metrics.session_mappings_created += 1
                elif request.thread_id not in session_mapping.thread_ids:
                    # Add thread to session mapping
                    session_mapping.thread_ids.append(request.thread_id)
                
                # Set primary thread
                session_mapping.primary_thread_id = request.thread_id
                self._primary_threads[request.session_id] = request.thread_id
                
                # Persist data if enabled
                if self._persistence_service:
                    await self._persist_data()
                
                return SetPrimaryThreadResponse(
                    success=True,
                    session_id=request.session_id,
                    thread_id=request.thread_id,
                    message="Primary thread set successfully"
                )
        except Exception as e:
            self.logger.error(f"Error setting primary thread: {e}")
            
            return SetPrimaryThreadResponse(
                success=False,
                message=None,
                error=str(e)
            )
    
    async def get_langgraph_thread(self, session_id: str) -> Optional[str]:
        """
        Get the LangGraph thread ID for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            LangGraph thread ID if available, None otherwise
        """
        if not self._initialized:
            return None
        
        try:
            # Get primary thread for session
            primary_thread_id = self._primary_threads.get(session_id)
            if not primary_thread_id:
                return None
            
            # Get thread
            async with self._lock:
                thread = self._threads.get(primary_thread_id)
                if not thread:
                    return None
                
                return thread.langgraph_thread_id
        except Exception as e:
            self.logger.error(f"Error getting LangGraph thread: {e}")
            return None
    
    async def get_session_state(self, session_id: str, thread_id: Optional[str] = None):
        """
        Get the session state for a session.
        
        Args:
            session_id: ID of the session
            thread_id: Optional ID of the thread
            
        Returns:
            Session state if available, None otherwise
        """
        if not self._initialized or not self._session_state_manager:
            return None
        
        try:
            from src.services.session_state.session_state_models import GetSessionStateRequest
            session_state_request = GetSessionStateRequest(
                session_id=session_id,
                thread_id=thread_id
            )
            session_state_response = await self._session_state_manager.get_session_state(session_state_request)
            if session_state_response.success and session_state_response.session_state:
                return session_state_response.session_state
            return None
        except Exception as e:
            self.logger.error(f"Error getting session state: {e}")
            return None
    
    async def create_checkpoint(self, session_id: str, thread_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """
        Create a checkpoint for a session.
        
        Args:
            session_id: ID of the session
            thread_id: ID of the thread
            checkpoint_data: Data to checkpoint
            
        Returns:
            True if checkpoint was created successfully, False otherwise
        """
        if not self._initialized or not self._session_state_manager:
            return False
        
        try:
            from src.services.session_state.session_state_models import CreateCheckpointRequest
            checkpoint_request = CreateCheckpointRequest(
                session_id=session_id,
                thread_id=thread_id,
                checkpoint_data=checkpoint_data
            )
            checkpoint_response = await self._session_state_manager.create_checkpoint(checkpoint_request)
            return checkpoint_response.success
        except Exception as e:
            self.logger.error(f"Error creating checkpoint: {e}")
            return False
    
    async def restore_from_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """
        Restore session state from a checkpoint.
        
        Args:
            session_id: ID of the session
            checkpoint_id: ID of the checkpoint
            
        Returns:
            True if restoration was successful, False otherwise
        """
        if not self._initialized or not self._session_state_manager:
            return False
        
        try:
            from src.services.session_state.session_state_models import RestoreFromCheckpointRequest
            restore_request = RestoreFromCheckpointRequest(
                session_id=session_id,
                checkpoint_id=checkpoint_id
            )
            restore_response = await self._session_state_manager.restore_from_checkpoint(restore_request)
            return restore_response.success
        except Exception as e:
            self.logger.error(f"Error restoring from checkpoint: {e}")
            return False
    
    async def get_service_status(self) -> ThreadManagerStatus:
        """
        Get the status of the Thread Manager.
        
        Returns:
            The service status
        """
        uptime = (datetime.utcnow() - (self._start_time or datetime.utcnow())).total_seconds()
        
        async with self._lock:
            # Count threads by status
            active_threads = sum(1 for t in self._threads.values() if t.status == ThreadStatus.ACTIVE)
            archived_threads = sum(1 for t in self._threads.values() if t.status == ThreadStatus.ARCHIVED)
            
            # Get last activity timestamp
            last_activity = None
            if self._threads:
                last_activity = max(t.updated_at for t in self._threads.values())
            
            return ThreadManagerStatus(
                service_name=self._config.service_name,
                status="running" if self._initialized else "stopped",
                is_healthy=await self.health_check(),
                uptime_seconds=uptime,
                total_threads=len(self._threads),
                active_threads=active_threads,
                archived_threads=archived_threads,
                last_activity=last_activity,
                version="1.0.0"
            )
    
    async def get_service_metrics(self) -> ThreadManagerMetrics:
        """
        Get the metrics of the Thread Manager.
        
        Returns:
            The service metrics
        """
        # Calculate cache hit rate
        total_requests = self._metrics.cache_hits + self._metrics.cache_misses
        cache_hit_rate = self._metrics.cache_hits / total_requests if total_requests > 0 else 0.0
        
        # Update metrics
        self._metrics.metadata["cache_hit_rate"] = cache_hit_rate
        
        return self._metrics
    
    async def start(self) -> bool:
        """
        Start the service.
        
        Returns:
            True if the service was started successfully, False otherwise
        """
        return await self.initialize()
    
    async def stop(self) -> bool:
        """
        Stop the service.
        
        Returns:
            True if the service was stopped successfully, False otherwise
        """
        return await self.shutdown()