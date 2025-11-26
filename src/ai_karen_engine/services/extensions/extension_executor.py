"""
Extension Executor Service

This service provides capabilities for executing extensions, including
managing their lifecycle, handling errors, and providing execution context.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
import json
import asyncio
import threading
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from contextlib import contextmanager

from .extension_registry import Extension, ExtensionType, ExtensionStatus
import time

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Enumeration of execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionPriority(Enum):
    """Enumeration of execution priorities."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ExecutionContext:
    """Context for extension execution."""
    execution_id: str
    extension_id: str
    request: Any
    context: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    auth: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class ExecutionResult:
    """Result of extension execution."""
    execution_id: str
    extension_id: str
    status: ExecutionStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    context: Optional[ExecutionContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionQueue:
    """Queue for extension executions."""
    id: str
    name: str
    max_concurrent: int = 5
    max_pending: int = 100
    timeout: float = 300.0  # 5 minutes
    executions: Dict[str, ExecutionContext] = field(default_factory=dict)
    running: Set[str] = field(default_factory=set)
    pending: List[str] = field(default_factory=list)
    completed: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)


class ExtensionExecutor:
    """
    Provides capabilities for executing extensions.
    
    This class is responsible for:
    - Executing extensions in a controlled environment
    - Managing execution context and lifecycle
    - Handling errors and timeouts
    - Providing execution queues and prioritization
    - Tracking execution results and metrics
    """
    
    def __init__(self):
        self._queues: Dict[str, ExecutionQueue] = {}
        self._results: Dict[str, ExecutionResult] = {}
        self._active_executions: Dict[str, threading.Thread] = {}
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._worker_active = False
        
        # Callbacks for execution events
        self._on_execution_started: Optional[Callable[[ExecutionContext], None]] = None
        self._on_execution_completed: Optional[Callable[[ExecutionResult], None]] = None
        self._on_execution_failed: Optional[Callable[[ExecutionResult], None]] = None
        self._on_execution_timeout: Optional[Callable[[ExecutionContext], None]] = None
        self._on_execution_cancelled: Optional[Callable[[ExecutionContext], None]] = None
    
    def initialize(self) -> None:
        """Initialize the extension executor."""
        # Create default queue
        self.create_queue("default", "Default execution queue")
        
        # Start worker thread
        self._start_worker()
        
        logger.info("Initialized extension executor")
    
    def shutdown(self) -> None:
        """Shutdown the extension executor."""
        # Stop worker thread
        self._stop_worker()
        
        # Cancel all active executions
        for execution_id in list(self._active_executions.keys()):
            self.cancel_execution(execution_id)
        
        logger.info("Shutdown extension executor")
    
    def create_queue(
        self,
        queue_id: str,
        name: str,
        max_concurrent: int = 5,
        max_pending: int = 100,
        timeout: float = 300.0
    ) -> ExecutionQueue:
        """
        Create an execution queue.
        
        Args:
            queue_id: ID of the queue
            name: Name of the queue
            max_concurrent: Maximum concurrent executions
            max_pending: Maximum pending executions
            timeout: Timeout for executions
            
        Returns:
            Created execution queue
        """
        queue = ExecutionQueue(
            id=queue_id,
            name=name,
            max_concurrent=max_concurrent,
            max_pending=max_pending,
            timeout=timeout
        )
        
        self._queues[queue_id] = queue
        
        logger.info(f"Created execution queue: {queue_id}")
        return queue
    
    def get_queue(self, queue_id: str) -> Optional[ExecutionQueue]:
        """Get an execution queue by ID."""
        return self._queues.get(queue_id)
    
    def execute_extension(
        self,
        extension_id: str,
        request: Any,
        context: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        auth: Optional[Dict[str, Any]] = None,
        flags: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        priority: ExecutionPriority = ExecutionPriority.NORMAL,
        queue_id: str = "default",
        execution_id: Optional[str] = None
    ) -> str:
        """
        Execute an extension.
        
        Args:
            extension_id: ID of the extension to execute
            request: Request data for the extension
            context: Context data for the extension
            params: Parameters for the extension
            auth: Authentication data for the extension
            flags: Flags for the extension
            timeout: Timeout for the execution
            priority: Priority of the execution
            queue_id: ID of the queue to use
            execution_id: ID for the execution
            
        Returns:
            ID of the execution
        """
        # Get queue
        queue = self._queues.get(queue_id)
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Create execution context
        execution_id = execution_id or str(uuid.uuid4())
        execution_context = ExecutionContext(
            execution_id=execution_id,
            extension_id=extension_id,
            request=request,
            context=context or {},
            params=params or {},
            auth=auth or {},
            flags=flags or {},
            timeout=timeout or queue.timeout,
            priority=priority
        )
        
        # Add to queue
        if len(queue.pending) >= queue.max_pending:
            raise ValueError(f"Queue is full: {queue_id}")
        
        queue.executions[execution_id] = execution_context
        queue.pending.append(execution_id)
        
        logger.info(f"Queued execution: {execution_id} for extension: {extension_id}")
        return execution_id
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get an execution context by ID."""
        for queue in self._queues.values():
            if execution_id in queue.executions:
                return queue.executions[execution_id]
        
        return None
    
    def get_result(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get an execution result by ID."""
        return self._results.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            True if execution was cancelled, False if not found or already completed
        """
        # Find execution
        execution_context = self.get_execution(execution_id)
        if not execution_context:
            logger.warning(f"Execution not found: {execution_id}")
            return False
        
        # Check if already completed
        result = self.get_result(execution_id)
        if result and result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            logger.warning(f"Execution already completed: {execution_id}")
            return False
        
        # Remove from pending queue
        for queue in self._queues.values():
            if execution_id in queue.pending:
                queue.pending.remove(execution_id)
                break
        
        # Cancel if running
        if execution_id in self._active_executions:
            # Mark as cancelled
            if execution_id not in self._results:
                self._results[execution_id] = ExecutionResult(
                    execution_id=execution_id,
                    extension_id=execution_context.extension_id,
                    status=ExecutionStatus.CANCELLED,
                    error="Cancelled by user",
                    context=execution_context
                )
            
            # Call execution cancelled callback if set
            if self._on_execution_cancelled:
                self._on_execution_cancelled(execution_context)
            
            logger.info(f"Cancelled execution: {execution_id}")
            return True
        
        return False
    
    def set_executor_callbacks(
        self,
        on_execution_started: Optional[Callable[[ExecutionContext], None]] = None,
        on_execution_completed: Optional[Callable[[ExecutionResult], None]] = None,
        on_execution_failed: Optional[Callable[[ExecutionResult], None]] = None,
        on_execution_timeout: Optional[Callable[[ExecutionContext], None]] = None,
        on_execution_cancelled: Optional[Callable[[ExecutionContext], None]] = None
    ) -> None:
        """Set callbacks for execution events."""
        self._on_execution_started = on_execution_started
        self._on_execution_completed = on_execution_completed
        self._on_execution_failed = on_execution_failed
        self._on_execution_timeout = on_execution_timeout
        self._on_execution_cancelled = on_execution_cancelled
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about extension executions.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_queues": len(self._queues),
            "total_executions": sum(len(q.executions) for q in self._queues.values()),
            "active_executions": len(self._active_executions),
            "pending_executions": sum(len(q.pending) for q in self._queues.values()),
            "completed_executions": sum(len(q.completed) for q in self._queues.values()),
            "failed_executions": sum(len(q.failed) for q in self._queues.values()),
            "executions_by_status": {},
            "executions_by_priority": {},
            "executions_by_queue": {}
        }
        
        # Count executions by status
        for result in self._results.values():
            status = result.status.value
            if status not in stats["executions_by_status"]:
                stats["executions_by_status"][status] = 0
            stats["executions_by_status"][status] += 1
        
        # Count executions by priority
        for queue in self._queues.values():
            for execution in queue.executions.values():
                priority = execution.priority.name
                if priority not in stats["executions_by_priority"]:
                    stats["executions_by_priority"][priority] = 0
                stats["executions_by_priority"][priority] += 1
        
        # Count executions by queue
        for queue in self._queues.values():
            stats["executions_by_queue"][queue.id] = len(queue.executions)
        
        return stats
    
    def _start_worker(self) -> None:
        """Start the worker thread."""
        if not self._worker_active:
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop)
            self._worker_thread.daemon = True
            self._worker_thread.start()
            self._worker_active = True
            logger.info("Started executor worker thread")
    
    def _stop_worker(self) -> None:
        """Stop the worker thread."""
        if self._worker_active:
            self._stop_event.set()
            if self._worker_thread:
                self._worker_thread.join(timeout=5.0)
            self._worker_active = False
            logger.info("Stopped executor worker thread")
    
    def _worker_loop(self) -> None:
        """Main worker loop."""
        while not self._stop_event.is_set():
            try:
                # Process queues
                for queue in self._queues.values():
                    self._process_queue(queue)
                
                # Clean up completed executions
                self._cleanup_executions()
                
                # Wait for next iteration
                self._stop_event.wait(0.1)
                
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                self._stop_event.wait(1.0)
    
    def _process_queue(self, queue: ExecutionQueue) -> None:
        """Process an execution queue."""
        # Check if we can start new executions
        if len(queue.running) >= queue.max_concurrent:
            return
        
        # Get next execution from pending queue
        if not queue.pending:
            return
        
        # Sort by priority
        pending_executions = [
            queue.executions[execution_id]
            for execution_id in queue.pending
        ]
        pending_executions.sort(key=lambda e: e.priority.value, reverse=True)
        
        # Start next execution
        execution_context = pending_executions[0]
        queue.pending.remove(execution_context.execution_id)
        queue.running.add(execution_context.execution_id)
        
        # Start execution thread
        thread = threading.Thread(
            target=self._execute_extension,
            args=(queue, execution_context)
        )
        thread.daemon = True
        thread.start()
        
        self._active_executions[execution_context.execution_id] = thread
    
    def _execute_extension(self, queue: ExecutionQueue, execution_context: ExecutionContext) -> None:
        """Execute an extension."""
        execution_id = execution_context.execution_id
        extension_id = execution_context.extension_id
        
        try:
            # Update execution context
            execution_context.started_at = datetime.now()
            
            # Call execution started callback if set
            if self._on_execution_started:
                self._on_execution_started(execution_context)
            
            # Create execution result
            result = ExecutionResult(
                execution_id=execution_id,
                extension_id=extension_id,
                status=ExecutionStatus.RUNNING,
                context=execution_context
            )
            
            # Store result
            self._results[execution_id] = result
            
            # Execute extension
            # In a real implementation, this would load and execute the extension
            # For now, we'll just simulate execution
            start_time = time.time()
            
            try:
                # Simulate execution
                time.sleep(0.1)
                
                # Get result
                execution_result = {
                    "success": True,
                    "data": f"Result for extension {extension_id}",
                    "execution_time": time.time() - start_time
                }
                
                # Update result
                result.status = ExecutionStatus.COMPLETED
                result.result = execution_result
                result.execution_time = time.time() - start_time
                
                # Add to completed queue
                queue.completed.append(execution_id)
                
                # Call execution completed callback if set
                if self._on_execution_completed:
                    self._on_execution_completed(result)
                
                logger.info(f"Completed execution: {execution_id} for extension: {extension_id}")
                
            except Exception as e:
                # Update result
                result.status = ExecutionStatus.FAILED
                result.error = str(e)
                result.execution_time = time.time() - start_time
                
                # Add to failed queue
                queue.failed.append(execution_id)
                
                # Call execution failed callback if set
                if self._on_execution_failed:
                    self._on_execution_failed(result)
                
                logger.error(f"Failed execution: {execution_id} for extension: {extension_id} with error: {str(e)}")
            
        except Exception as e:
            # Create error result
            result = ExecutionResult(
                execution_id=execution_id,
                extension_id=extension_id,
                status=ExecutionStatus.FAILED,
                error=str(e),
                context=execution_context
            )
            
            # Store result
            self._results[execution_id] = result
            
            # Add to failed queue
            queue.failed.append(execution_id)
            
            # Call execution failed callback if set
            if self._on_execution_failed:
                self._on_execution_failed(result)
            
            logger.error(f"Failed execution: {execution_id} for extension: {extension_id} with error: {str(e)}")
        
        finally:
            # Remove from running queue
            queue.running.discard(execution_id)
            
            # Remove from active executions
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
            
            # Update execution context
            execution_context.completed_at = datetime.now()
    
    def _cleanup_executions(self) -> None:
        """Clean up completed and failed executions."""
        # Keep only the last 1000 executions in memory
        if len(self._results) > 1000:
            # Get oldest execution IDs
            execution_ids = list(self._results.keys())
            oldest_ids = execution_ids[:-1000]
            
            # Remove oldest results
            for execution_id in oldest_ids:
                del self._results[execution_id]
        
        # Clean up queue executions
        for queue in self._queues.values():
            # Keep only the last 100 executions in each queue
            if len(queue.completed) > 100:
                queue.completed = queue.completed[-100:]
            
            if len(queue.failed) > 100:
                queue.failed = queue.failed[-100:]
            
            # Remove executions that are no longer in results
            execution_ids = list(queue.executions.keys())
            for execution_id in execution_ids:
                if execution_id not in self._results:
                    del queue.executions[execution_id]
                    queue.running.discard(execution_id)
                    if execution_id in queue.pending:
                        queue.pending.remove(execution_id)