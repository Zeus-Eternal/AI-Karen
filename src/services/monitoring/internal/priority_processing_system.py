"""
Priority-Based Processing System for Intelligent Response Optimization

This module implements priority-based processing for different query types,
ensuring high-priority queries get faster processing while maintaining
overall system efficiency and fairness.
"""

import asyncio
import heapq
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import threading
import time
import uuid

from ...internal.query_analyzer import QueryAnalysis, Priority, ComplexityLevel, ContentType
from ...internal.response_strategy_engine import ResponseStrategy, ProcessingMode
from ...internal.resource_allocation_system import ResourceAllocation

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Processing status for queries"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class QueueType(Enum):
    """Different queue types for processing"""
    URGENT = "urgent"
    HIGH_PRIORITY = "high_priority"
    NORMAL = "normal"
    LOW_PRIORITY = "low_priority"
    BACKGROUND = "background"


@dataclass
class ProcessingTask:
    """Task for priority-based processing"""
    task_id: str
    query_id: str
    query_analysis: QueryAnalysis
    response_strategy: ResponseStrategy
    resource_allocation: Optional[ResourceAllocation]
    processing_function: Callable
    callback: Optional[Callable]
    priority_score: float
    queue_type: QueueType
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ProcessingStatus = ProcessingStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Enable priority queue ordering (higher priority_score = higher priority)"""
        return self.priority_score > other.priority_score


@dataclass
class ProcessingMetrics:
    """Metrics for processing performance"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_processing_time: float
    queue_lengths: Dict[str, int]
    throughput_per_minute: float
    priority_distribution: Dict[str, int]
    resource_utilization: Dict[str, float]
    timestamp: datetime


class PriorityProcessingSystem:
    """
    Advanced priority-based processing system that manages query processing
    based on priority levels, resource availability, and system performance.
    """
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.processing_queues: Dict[QueueType, List[ProcessingTask]] = {
            queue_type: [] for queue_type in QueueType
        }
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: List[ProcessingTask] = []
        self.processing_workers: List[asyncio.Task] = []
        self.metrics_history: List[ProcessingMetrics] = []
        
        self._lock = threading.Lock()
        self._shutdown_event = asyncio.Event()
        self._worker_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # Priority weights for different queue types
        self.priority_weights = {
            QueueType.URGENT: 1000,
            QueueType.HIGH_PRIORITY: 500,
            QueueType.NORMAL: 100,
            QueueType.LOW_PRIORITY: 50,
            QueueType.BACKGROUND: 10
        }
        
        # Processing time limits by priority
        self.time_limits = {
            QueueType.URGENT: 5,      # 5 seconds
            QueueType.HIGH_PRIORITY: 15,   # 15 seconds
            QueueType.NORMAL: 30,     # 30 seconds
            QueueType.LOW_PRIORITY: 60,    # 60 seconds
            QueueType.BACKGROUND: 120  # 120 seconds
        }
        
        # Start processing workers
        self.start_workers()
    
    def start_workers(self) -> None:
        """Start processing worker tasks"""
        try:
            # Create worker tasks for different priority levels
            for i in range(self.max_concurrent_tasks):
                worker_task = asyncio.create_task(self._processing_worker(f"worker_{i}"))
                self.processing_workers.append(worker_task)
            
            # Start metrics collection
            metrics_task = asyncio.create_task(self._metrics_collector())
            self.processing_workers.append(metrics_task)
            
            logger.info(f"Started {len(self.processing_workers)} processing workers")
            
        except Exception as e:
            logger.error(f"Error starting processing workers: {e}")
    
    async def submit_task(
        self,
        query_analysis: QueryAnalysis,
        response_strategy: ResponseStrategy,
        processing_function: Callable,
        resource_allocation: Optional[ResourceAllocation] = None,
        callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a task for priority-based processing
        
        Args:
            query_analysis: Query analysis results
            response_strategy: Response strategy configuration
            processing_function: Function to execute for processing
            resource_allocation: Optional resource allocation
            callback: Optional callback function for completion
            metadata: Optional task metadata
            
        Returns:
            str: Task ID for tracking
        """
        try:
            task_id = str(uuid.uuid4())
            query_id = metadata.get('query_id', task_id) if metadata else task_id
            
            # Determine queue type and priority score
            queue_type = self._determine_queue_type(query_analysis, response_strategy)
            priority_score = self._calculate_priority_score(query_analysis, response_strategy, queue_type)
            
            # Create processing task
            task = ProcessingTask(
                task_id=task_id,
                query_id=query_id,
                query_analysis=query_analysis,
                response_strategy=response_strategy,
                resource_allocation=resource_allocation,
                processing_function=processing_function,
                callback=callback,
                priority_score=priority_score,
                queue_type=queue_type,
                created_at=datetime.utcnow(),
                timeout_seconds=self.time_limits.get(queue_type, 30),
                metadata=metadata or {}
            )
            
            # Add to appropriate queue
            with self._lock:
                heapq.heappush(self.processing_queues[queue_type], task)
            
            logger.info(f"Task {task_id} submitted to {queue_type.value} queue with priority {priority_score}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    def _determine_queue_type(self, query_analysis: QueryAnalysis, response_strategy: ResponseStrategy) -> QueueType:
        """Determine appropriate queue type based on query analysis"""
        try:
            # Check priority from query analysis
            if query_analysis.processing_priority == Priority.URGENT:
                return QueueType.URGENT
            elif query_analysis.processing_priority == Priority.HIGH:
                return QueueType.HIGH_PRIORITY
            elif query_analysis.processing_priority == Priority.LOW:
                return QueueType.LOW_PRIORITY
            
            # Check processing mode
            if response_strategy.processing_mode == ProcessingMode.FAST:
                return QueueType.HIGH_PRIORITY
            elif response_strategy.processing_mode == ProcessingMode.COMPREHENSIVE:
                return QueueType.NORMAL
            
            # Check complexity
            if query_analysis.complexity == ComplexityLevel.SIMPLE:
                return QueueType.HIGH_PRIORITY
            elif query_analysis.complexity == ComplexityLevel.COMPLEX:
                return QueueType.NORMAL
            
            # Default to normal priority
            return QueueType.NORMAL
            
        except Exception as e:
            logger.error(f"Error determining queue type: {e}")
            return QueueType.NORMAL
    
    def _calculate_priority_score(
        self, 
        query_analysis: QueryAnalysis, 
        response_strategy: ResponseStrategy,
        queue_type: QueueType
    ) -> float:
        """Calculate priority score for task ordering"""
        try:
            base_score = self.priority_weights[queue_type]
            
            # Adjust based on query characteristics
            priority_multiplier = {
                Priority.URGENT: 2.0,
                Priority.HIGH: 1.5,
                Priority.NORMAL: 1.0,
                Priority.LOW: 0.7
            }.get(query_analysis.processing_priority, 1.0)
            
            # Adjust based on complexity (simpler queries get slight boost)
            complexity_multiplier = {
                ComplexityLevel.SIMPLE: 1.1,
                ComplexityLevel.MODERATE: 1.0,
                ComplexityLevel.COMPLEX: 0.9
            }.get(query_analysis.complexity, 1.0)
            
            # Adjust based on processing mode
            mode_multiplier = {
                ProcessingMode.FAST: 1.2,
                ProcessingMode.BALANCED: 1.0,
                ProcessingMode.COMPREHENSIVE: 0.8,
                ProcessingMode.STREAMING: 1.1
            }.get(response_strategy.processing_mode, 1.0)
            
            # Adjust based on estimated response time (faster responses get boost)
            time_multiplier = 1.0
            if response_strategy.estimated_generation_time < 5:
                time_multiplier = 1.1
            elif response_strategy.estimated_generation_time > 15:
                time_multiplier = 0.9
            
            # Add small random component to prevent starvation
            import random
            random_factor = 1.0 + (random.random() - 0.5) * 0.1  # ±5% randomness
            
            final_score = base_score * priority_multiplier * complexity_multiplier * mode_multiplier * time_multiplier * random_factor
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return self.priority_weights.get(queue_type, 100)
    
    async def _processing_worker(self, worker_id: str) -> None:
        """Processing worker that handles tasks from queues"""
        logger.info(f"Processing worker {worker_id} started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get next task from highest priority queue
                task = await self._get_next_task()
                
                if task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)
                    continue
                
                # Acquire semaphore for concurrent processing limit
                async with self._worker_semaphore:
                    await self._process_task(task, worker_id)
                
            except Exception as e:
                logger.error(f"Error in processing worker {worker_id}: {e}")
                await asyncio.sleep(1)  # Wait before retrying
        
        logger.info(f"Processing worker {worker_id} stopped")
    
    async def _get_next_task(self) -> Optional[ProcessingTask]:
        """Get next task from highest priority queue"""
        try:
            with self._lock:
                # Check queues in priority order
                for queue_type in [QueueType.URGENT, QueueType.HIGH_PRIORITY, QueueType.NORMAL, QueueType.LOW_PRIORITY, QueueType.BACKGROUND]:
                    queue = self.processing_queues[queue_type]
                    if queue:
                        task = heapq.heappop(queue)
                        task.status = ProcessingStatus.PROCESSING
                        task.started_at = datetime.utcnow()
                        self.active_tasks[task.task_id] = task
                        return task
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            return None
    
    async def _process_task(self, task: ProcessingTask, worker_id: str) -> None:
        """Process a single task"""
        try:
            logger.info(f"Worker {worker_id} processing task {task.task_id} (priority: {task.priority_score})")
            
            # Set timeout for task processing
            try:
                result = await asyncio.wait_for(
                    task.processing_function(task.query_analysis, task.response_strategy, task.resource_allocation),
                    timeout=task.timeout_seconds
                )
                
                # Task completed successfully
                task.status = ProcessingStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                
                # Call callback if provided
                if task.callback:
                    try:
                        await task.callback(task, result)
                    except Exception as callback_error:
                        logger.error(f"Error in task callback: {callback_error}")
                
                logger.info(f"Task {task.task_id} completed successfully by worker {worker_id}")
                
            except asyncio.TimeoutError:
                task.status = ProcessingStatus.TIMEOUT
                task.completed_at = datetime.utcnow()
                logger.warning(f"Task {task.task_id} timed out after {task.timeout_seconds} seconds")
                
                # Retry if possible
                if task.retry_count < task.max_retries:
                    await self._retry_task(task)
                
            except Exception as processing_error:
                task.status = ProcessingStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.task_id} failed: {processing_error}")
                
                # Retry if possible
                if task.retry_count < task.max_retries:
                    await self._retry_task(task)
            
            # Move task from active to completed
            with self._lock:
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]
                self.completed_tasks.append(task)
                
                # Keep only last 1000 completed tasks
                if len(self.completed_tasks) > 1000:
                    self.completed_tasks.pop(0)
            
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {e}")
            task.status = ProcessingStatus.FAILED
            task.completed_at = datetime.utcnow()
    
    async def _retry_task(self, task: ProcessingTask) -> None:
        """Retry a failed or timed out task"""
        try:
            task.retry_count += 1
            task.status = ProcessingStatus.QUEUED
            task.started_at = None
            
            # Reduce priority slightly for retry
            task.priority_score *= 0.9
            
            # Add back to queue
            with self._lock:
                heapq.heappush(self.processing_queues[task.queue_type], task)
            
            logger.info(f"Task {task.task_id} queued for retry (attempt {task.retry_count}/{task.max_retries})")
            
        except Exception as e:
            logger.error(f"Error retrying task {task.task_id}: {e}")
    
    async def _metrics_collector(self) -> None:
        """Collect processing metrics periodically"""
        while not self._shutdown_event.is_set():
            try:
                metrics = await self._collect_metrics()
                
                with self._lock:
                    self.metrics_history.append(metrics)
                    # Keep only last 100 metrics
                    if len(self.metrics_history) > 100:
                        self.metrics_history.pop(0)
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)
    
    async def _collect_metrics(self) -> ProcessingMetrics:
        """Collect current processing metrics"""
        try:
            with self._lock:
                # Count tasks by status
                total_tasks = len(self.completed_tasks) + len(self.active_tasks)
                completed_tasks = len([t for t in self.completed_tasks if t.status == ProcessingStatus.COMPLETED])
                failed_tasks = len([t for t in self.completed_tasks if t.status == ProcessingStatus.FAILED])
                
                # Calculate average processing time
                processing_times = []
                for task in self.completed_tasks:
                    if task.started_at and task.completed_at:
                        processing_time = (task.completed_at - task.started_at).total_seconds()
                        processing_times.append(processing_time)
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
                
                # Queue lengths
                queue_lengths = {
                    queue_type.value: len(queue) 
                    for queue_type, queue in self.processing_queues.items()
                }
                
                # Calculate throughput (tasks completed in last minute)
                one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
                recent_completions = [
                    t for t in self.completed_tasks 
                    if t.completed_at and t.completed_at > one_minute_ago
                ]
                throughput = len(recent_completions)
                
                # Priority distribution
                priority_distribution = {}
                for task in list(self.active_tasks.values()) + self.completed_tasks[-100:]:  # Last 100 completed
                    priority = task.query_analysis.processing_priority.value
                    priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
                
                # Resource utilization (simplified)
                resource_utilization = {
                    'active_workers': len(self.active_tasks),
                    'max_workers': self.max_concurrent_tasks,
                    'utilization_percent': (len(self.active_tasks) / self.max_concurrent_tasks) * 100
                }
                
                return ProcessingMetrics(
                    total_tasks=total_tasks,
                    completed_tasks=completed_tasks,
                    failed_tasks=failed_tasks,
                    average_processing_time=avg_processing_time,
                    queue_lengths=queue_lengths,
                    throughput_per_minute=throughput,
                    priority_distribution=priority_distribution,
                    resource_utilization=resource_utilization,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return ProcessingMetrics(
                total_tasks=0,
                completed_tasks=0,
                failed_tasks=0,
                average_processing_time=0,
                queue_lengths={},
                throughput_per_minute=0,
                priority_distribution={},
                resource_utilization={},
                timestamp=datetime.utcnow()
            )
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        try:
            # Check active tasks
            with self._lock:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    return self._task_to_dict(task)
                
                # Check completed tasks
                for task in self.completed_tasks:
                    if task.task_id == task_id:
                        return self._task_to_dict(task)
                
                # Check queued tasks
                for queue in self.processing_queues.values():
                    for task in queue:
                        if task.task_id == task_id:
                            return self._task_to_dict(task)
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return None
    
    def _task_to_dict(self, task: ProcessingTask) -> Dict[str, Any]:
        """Convert task to dictionary representation"""
        return {
            'task_id': task.task_id,
            'query_id': task.query_id,
            'status': task.status.value,
            'queue_type': task.queue_type.value,
            'priority_score': task.priority_score,
            'created_at': task.created_at.isoformat(),
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'retry_count': task.retry_count,
            'processing_time': (
                (task.completed_at - task.started_at).total_seconds() 
                if task.started_at and task.completed_at else None
            ),
            'metadata': task.metadata
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued or active task"""
        try:
            with self._lock:
                # Check active tasks (cannot cancel running tasks easily)
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.status = ProcessingStatus.CANCELLED
                    logger.info(f"Marked active task {task_id} for cancellation")
                    return True
                
                # Check queued tasks
                for queue_type, queue in self.processing_queues.items():
                    for i, task in enumerate(queue):
                        if task.task_id == task_id:
                            task.status = ProcessingStatus.CANCELLED
                            queue.pop(i)
                            heapq.heapify(queue)  # Restore heap property
                            self.completed_tasks.append(task)
                            logger.info(f"Cancelled queued task {task_id}")
                            return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and metrics"""
        try:
            with self._lock:
                queue_status = {}
                for queue_type, queue in self.processing_queues.items():
                    queue_status[queue_type.value] = {
                        'length': len(queue),
                        'oldest_task_age': (
                            (datetime.utcnow() - min(task.created_at for task in queue)).total_seconds()
                            if queue else 0
                        ),
                        'average_priority': (
                            sum(task.priority_score for task in queue) / len(queue)
                            if queue else 0
                        )
                    }
                
                return {
                    'queues': queue_status,
                    'active_tasks': len(self.active_tasks),
                    'max_concurrent': self.max_concurrent_tasks,
                    'total_completed': len(self.completed_tasks),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown the processing system gracefully"""
        try:
            logger.info("Shutting down priority processing system...")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for workers to complete
            if self.processing_workers:
                await asyncio.gather(*self.processing_workers, return_exceptions=True)
            
            logger.info("Priority processing system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, '_shutdown_event') and not self._shutdown_event.is_set():
            asyncio.create_task(self.shutdown())