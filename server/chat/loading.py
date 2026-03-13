"""
Loading State Management for AI-Karen Production Chat System
Provides comprehensive loading state tracking for long-running operations.
"""

import logging
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LoadingState(Enum):
    """Loading state types."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    LOADING = "loading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LoadingPriority(Enum):
    """Loading operation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LoadingOperation:
    """Individual loading operation information."""
    id: str
    name: str
    state: LoadingState
    priority: LoadingPriority
    progress: float = 0.0  # 0-100 percentage
    message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    timeout: Optional[int] = None  # milliseconds
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation_type: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    cancel_callback: Optional[Callable] = None


@dataclass
class LoadingStats:
    """Loading statistics for monitoring."""
    total_operations: int = 0
    active_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    cancelled_operations: int = 0
    average_duration: float = 0.0
    longest_operation: Optional[str] = None
    longest_duration: float = 0.0
    operations_by_type: Dict[str, int] = field(default_factory=dict)
    operations_by_priority: Dict[str, int] = field(default_factory=dict)


class LoadingManager:
    """
    Loading state manager for tracking long-running operations.
    
    Features:
    - Real-time progress tracking
    - Operation timeout handling
    - Priority-based execution
    - Resource usage monitoring
    - Cancellation support
    - Statistics collection
    """
    
    def __init__(self, max_concurrent_operations: int = 50):
        self.max_concurrent_operations = max_concurrent_operations
        self.operations: Dict[str, LoadingOperation] = {}
        self.active_operations: Set[str] = set()
        self.operation_handlers: Dict[str, List[Callable]] = {}
        self.stats = LoadingStats()
        self.lock = asyncio.Lock()
        
        # Background tasks
        self._cleanup_task = None
        self._monitoring_task = None
        
        logger.info(f"Loading manager initialized with max {max_concurrent_operations} concurrent operations")
    
    async def start_operation(
        self,
        name: str,
        operation_type: str = "general",
        priority: LoadingPriority = LoadingPriority.MEDIUM,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cancel_callback: Optional[Callable] = None
    ) -> str:
        """
        Start a new loading operation.
        
        Args:
            name: Operation name
            operation_type: Type of operation (upload, processing, etc.)
            priority: Operation priority
            timeout: Timeout in milliseconds
            user_id: User ID
            session_id: Session ID
            request_id: Request ID
            component: Component name
            metadata: Additional metadata
            cancel_callback: Callback for cancellation
            
        Returns:
            Operation ID
        """
        async with self.lock:
            # Check concurrent operation limit
            if len(self.active_operations) >= self.max_concurrent_operations:
                raise Exception(f"Maximum concurrent operations ({self.max_concurrent_operations}) reached")
            
            # Create operation
            operation_id = str(uuid.uuid4())
            operation = LoadingOperation(
                id=operation_id,
                name=name,
                state=LoadingState.INITIALIZING,
                priority=priority,
                timeout=timeout,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                component=component,
                operation_type=operation_type,
                metadata=metadata or {},
                cancel_callback=cancel_callback
            )
            
            self.operations[operation_id] = operation
            self.active_operations.add(operation_id)
            
            # Update stats
            self.stats.total_operations += 1
            self.stats.active_operations += 1
            self.stats.operations_by_type[operation_type] = self.stats.operations_by_type.get(operation_type, 0) + 1
            self.stats.operations_by_priority[priority.value] = self.stats.operations_by_priority.get(priority.value, 0) + 1
            
            logger.info(f"Started loading operation: {name} (ID: {operation_id})")
            
            # Start background monitoring if not already running
            if not self._monitoring_task:
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            return operation_id
    
    async def update_progress(
        self,
        operation_id: str,
        progress: float,
        message: str = "",
        state: Optional[LoadingState] = None
    ):
        """
        Update the progress of a loading operation.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
            message: Status message
            state: New state (optional)
        """
        async with self.lock:
            if operation_id not in self.operations:
                logger.warning(f"Attempted to update non-existent operation: {operation_id}")
                return
            
            operation = self.operations[operation_id]
            
            # Update progress and state
            operation.progress = max(0, min(100, progress))
            operation.updated_at = datetime.now(timezone.utc)
            
            if message:
                operation.message = message
            
            if state:
                operation.state = state
                
                # Handle state transitions
                if state == LoadingState.LOADING and operation.started_at is None:
                    operation.started_at = datetime.now(timezone.utc)
                    logger.info(f"Operation {operation_id} started loading")
                
                elif state in [LoadingState.COMPLETED, LoadingState.FAILED, LoadingState.CANCELLED]:
                    if operation.completed_at is None:
                        operation.completed_at = datetime.now(timezone.utc)
                        self.active_operations.discard(operation_id)
                        
                        # Update stats
                        self.stats.active_operations -= 1
                        if state == LoadingState.COMPLETED:
                            self.stats.completed_operations += 1
                        elif state == LoadingState.FAILED:
                            self.stats.failed_operations += 1
                        elif state == LoadingState.CANCELLED:
                            self.stats.cancelled_operations += 1
                        
                        # Update duration stats
                        if operation.started_at:
                            duration = (operation.completed_at - operation.started_at).total_seconds()
                            self._update_duration_stats(operation_id, duration)
                        
                        logger.info(f"Operation {operation_id} completed with state: {state.value}")
            
            # Notify handlers
            await self._notify_handlers(operation_id, "progress_updated", {
                "progress": operation.progress,
                "message": operation.message,
                "state": operation.state.value
            })
    
    async def complete_operation(
        self,
        operation_id: str,
        result: Optional[Any] = None,
        message: str = "Operation completed successfully"
    ):
        """Mark an operation as completed."""
        await self.update_progress(operation_id, 100.0, message, LoadingState.COMPLETED)
        
        # Store result in metadata
        async with self.lock:
            if operation_id in self.operations:
                self.operations[operation_id].metadata["result"] = result
        
        await self._notify_handlers(operation_id, "completed", {
            "result": result,
            "message": message
        })
    
    async def fail_operation(
        self,
        operation_id: str,
        error: str,
        message: str = "Operation failed"
    ):
        """Mark an operation as failed."""
        await self.update_progress(operation_id, 0.0, message, LoadingState.FAILED)
        
        # Store error in metadata
        async with self.lock:
            if operation_id in self.operations:
                self.operations[operation_id].error = error
        
        await self._notify_handlers(operation_id, "failed", {
            "error": error,
            "message": message
        })
    
    async def cancel_operation(
        self,
        operation_id: str,
        reason: str = "Operation cancelled"
    ):
        """Cancel a loading operation."""
        async with self.lock:
            if operation_id not in self.operations:
                logger.warning(f"Attempted to cancel non-existent operation: {operation_id}")
                return False
            
            operation = self.operations[operation_id]
            
            # Check if operation can be cancelled
            if operation.state in [LoadingState.COMPLETED, LoadingState.FAILED, LoadingState.CANCELLED]:
                logger.warning(f"Cannot cancel operation {operation_id} in state: {operation.state.value}")
                return False
            
            # Call cancel callback if provided
            if operation.cancel_callback:
                try:
                    if asyncio.iscoroutinefunction(operation.cancel_callback):
                        await operation.cancel_callback(operation_id, reason)
                    else:
                        operation.cancel_callback(operation_id, reason)
                except Exception as e:
                    logger.error(f"Cancel callback error for operation {operation_id}: {e}")
        
        # Update state
        await self.update_progress(operation_id, 0.0, reason, LoadingState.CANCELLED)
        
        await self._notify_handlers(operation_id, "cancelled", {"reason": reason})
        
        return True
    
    def get_operation(self, operation_id: str) -> Optional[LoadingOperation]:
        """Get operation information by ID."""
        return self.operations.get(operation_id)
    
    def get_active_operations(self, user_id: Optional[str] = None) -> List[LoadingOperation]:
        """Get all active operations, optionally filtered by user."""
        operations = [
            self.operations[op_id] for op_id in self.active_operations
            if op_id in self.operations
        ]
        
        if user_id:
            operations = [op for op in operations if op.user_id == user_id]
        
        return operations
    
    def get_user_operations(self, user_id: str) -> List[LoadingOperation]:
        """Get all operations for a specific user."""
        return [
            operation for operation in self.operations.values()
            if operation.user_id == user_id
        ]
    
    def get_operations_by_type(self, operation_type: str) -> List[LoadingOperation]:
        """Get all operations of a specific type."""
        return [
            operation for operation in self.operations.values()
            if operation.operation_type == operation_type
        ]
    
    def get_operations_by_component(self, component: str) -> List[LoadingOperation]:
        """Get all operations for a specific component."""
        return [
            operation for operation in self.operations.values()
            if operation.component == component
        ]
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler for loading events."""
        if event_type not in self.operation_handlers:
            self.operation_handlers[event_type] = []
        self.operation_handlers[event_type].append(handler)
        logger.info(f"Registered loading handler for event: {event_type}")
    
    async def _notify_handlers(self, operation_id: str, event_type: str, data: Dict[str, Any]):
        """Notify all registered handlers for an event."""
        handlers = self.operation_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(operation_id, event_type, data)
                else:
                    handler(operation_id, event_type, data)
            except Exception as e:
                logger.error(f"Loading handler error for {event_type}: {e}")
    
    async def _monitoring_loop(self):
        """Background task to monitor operations and handle timeouts."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                timeout_operations = []
                
                async with self.lock:
                    for operation_id, operation in list(self.operations.items()):
                        # Check for timeouts
                        if (operation.timeout and 
                            operation.state in [LoadingState.INITIALIZING, LoadingState.LOADING, LoadingState.PROCESSING] and
                            operation.started_at and
                            (current_time - operation.started_at).total_seconds() * 1000 > operation.timeout):
                            
                            timeout_operations.append(operation_id)
                
                # Handle timed out operations
                for operation_id in timeout_operations:
                    await self.fail_operation(
                        operation_id,
                        f"Operation timed out after {self.operations[operation_id].timeout}ms",
                        "Operation timed out"
                    )
                
                # Clean up old completed operations (keep for 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                old_operations = [
                    op_id for op_id, op in self.operations.items()
                    if (op.completed_at and op.completed_at < cutoff_time)
                ]
                
                for op_id in old_operations:
                    del self.operations[op_id]
                
                if old_operations:
                    logger.debug(f"Cleaned up {len(old_operations)} old loading operations")
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Loading monitoring loop error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _cleanup_loop(self):
        """Background task to clean up resources."""
        while True:
            try:
                # Clean up operation handlers that might be causing memory leaks
                async with self.lock:
                    for event_type, handlers in list(self.operation_handlers.items()):
                        # Keep only last 10 handlers per event type
                        if len(handlers) > 10:
                            self.operation_handlers[event_type] = handlers[-10:]
                
                # Wait before next cleanup
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Loading cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    def _update_duration_stats(self, operation_id: str, duration: float):
        """Update duration statistics."""
        if duration > self.stats.longest_duration:
            self.stats.longest_duration = duration
            self.stats.longest_operation = operation_id
        
        # Update average duration
        completed_count = self.stats.completed_operations + self.stats.failed_operations + self.stats.cancelled_operations
        if completed_count > 0:
            total_duration = self.stats.average_duration * (completed_count - 1) + duration
            self.stats.average_duration = total_duration / completed_count
    
    def get_statistics(self) -> LoadingStats:
        """Get current loading statistics."""
        # Update active count
        self.stats.active_operations = len(self.active_operations)
        
        return self.stats
    
    def get_operation_summary(self, operation_id: str) -> Dict[str, Any]:
        """Get detailed summary of an operation."""
        operation = self.operations.get(operation_id)
        if not operation:
            return {"error": "Operation not found"}
        
        duration = None
        if operation.started_at and operation.completed_at:
            duration = (operation.completed_at - operation.started_at).total_seconds()
        
        return {
            "id": operation.id,
            "name": operation.name,
            "state": operation.state.value,
            "priority": operation.priority.value,
            "progress": operation.progress,
            "message": operation.message,
            "created_at": operation.created_at.isoformat(),
            "started_at": operation.started_at.isoformat() if operation.started_at else None,
            "updated_at": operation.updated_at.isoformat(),
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "duration_seconds": duration,
            "timeout_ms": operation.timeout,
            "user_id": operation.user_id,
            "session_id": operation.session_id,
            "request_id": operation.request_id,
            "component": operation.component,
            "operation_type": operation.operation_type,
            "metadata": operation.metadata,
            "error": operation.error
        }
    
    async def start_background_tasks(self):
        """Start background monitoring and cleanup tasks."""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Loading manager background tasks started")
    
    async def stop_background_tasks(self):
        """Stop background monitoring and cleanup tasks."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        logger.info("Loading manager background tasks stopped")
    
    async def cleanup(self):
        """Clean up all operations and resources."""
        async with self.lock:
            # Cancel all active operations
            for operation_id in list(self.active_operations):
                operation = self.operations[operation_id]
                if operation.state not in [LoadingState.COMPLETED, LoadingState.FAILED, LoadingState.CANCELLED]:
                    await self.cancel_operation(operation_id, "System shutdown")
            
            # Clear operations
            self.operations.clear()
            self.active_operations.clear()
            
            # Reset stats
            self.stats = LoadingStats()
        
        # Stop background tasks
        await self.stop_background_tasks()
        
        logger.info("Loading manager cleaned up")


# Global loading manager instance
loading_manager = LoadingManager()


def get_loading_manager() -> LoadingManager:
    """Get global loading manager instance."""
    return loading_manager


# Decorator for loading operation tracking
def track_loading_operation(
    name: str,
    operation_type: str = "general",
    priority: LoadingPriority = LoadingPriority.MEDIUM,
    timeout: Optional[int] = None
):
    """Decorator to automatically track function execution as a loading operation."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs if available
            user_id = kwargs.pop('user_id', None)
            session_id = kwargs.pop('session_id', None)
            request_id = kwargs.pop('request_id', None)
            component = kwargs.pop('component', None)
            metadata = kwargs.pop('metadata', None)
            
            # Start operation
            manager = get_loading_manager()
            operation_id = await manager.start_operation(
                name=name,
                operation_type=operation_type,
                priority=priority,
                timeout=timeout,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                component=component,
                metadata=metadata
            )
            
            try:
                # Update to loading state
                await manager.update_progress(operation_id, 0.0, "Starting operation...", LoadingState.LOADING)
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Complete operation
                await manager.complete_operation(operation_id, result)
                
                return result
                
            except Exception as e:
                # Fail operation
                await manager.fail_operation(operation_id, str(e))
                raise e
        
        return wrapper
    return decorator