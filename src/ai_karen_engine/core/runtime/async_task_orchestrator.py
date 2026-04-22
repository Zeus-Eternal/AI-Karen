"""
Async Task Orchestrator for parallel processing and CPU-intensive task offloading.

This module provides the AsyncTaskOrchestrator class that manages background worker pools,
offloads CPU-intensive tasks to separate processes, and implements parallel task execution
with proper error handling and async/await patterns.
"""

import asyncio
import concurrent.futures
import functools
import logging
import multiprocessing
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable
from queue import Queue, Empty
import traceback

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that can be processed by the orchestrator."""
    CPU_INTENSIVE = "cpu_intensive"
    IO_BOUND = "io_bound"
    BLOCKING_OPERATION = "blocking_operation"
    BATCH_PROCESSING = "batch_processing"


class TaskPriority(Enum):
    """Priority levels for task scheduling."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """Represents a task to be executed by the orchestrator."""
    id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    task_type: TaskType = TaskType.CPU_INTENSIVE
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)


@dataclass
class TaskResult:
    """Represents the result of a task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    worker_id: Optional[str] = None


@dataclass
class WorkerPoolConfig:
    """Configuration for worker pools."""
    max_workers: Optional[int] = None
    thread_name_prefix: str = "AsyncTaskWorker"
    process_name_prefix: str = "AsyncTaskProcess"
    enable_process_pool: bool = True
    enable_thread_pool: bool = True


class AsyncTaskOrchestrator:
    """
    Orchestrates async task execution with background worker pool management.
    
    Provides CPU-intensive task offloading, parallel processing, and async/await
    wrappers for blocking operations to prevent main thread blocking.
    """
    
    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        """Initialize the async task orchestrator."""
        self.config = config or WorkerPoolConfig()
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._task_queue: Queue = Queue()
        self._results: Dict[str, TaskResult] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._batch_queues: Dict[str, List[Task]] = {}
        self._batch_timers: Dict[str, asyncio.Handle] = {}
        self._shutdown_event = asyncio.Event()
        self._worker_stats: Dict[str, Dict[str, Any]] = {}
        
        # Initialize worker pools
        self._initialize_worker_pools()
        
        logger.info(f"AsyncTaskOrchestrator initialized with config: {self.config}")
    
    def _initialize_worker_pools(self) -> None:
        """Initialize the worker pools based on configuration."""
        try:
            # Calculate optimal worker counts
            cpu_count = multiprocessing.cpu_count()
            
            if self.config.enable_process_pool:
                max_process_workers = self.config.max_workers or max(1, cpu_count - 1)
                self._process_pool = ProcessPoolExecutor(
                    max_workers=max_process_workers,
                    mp_context=multiprocessing.get_context('spawn')
                )
                logger.info(f"Process pool initialized with {max_process_workers} workers")
            
            if self.config.enable_thread_pool:
                max_thread_workers = self.config.max_workers or min(32, (cpu_count or 1) + 4)
                self._thread_pool = ThreadPoolExecutor(
                    max_workers=max_thread_workers,
                    thread_name_prefix=self.config.thread_name_prefix
                )
                logger.info(f"Thread pool initialized with {max_thread_workers} workers")
                
        except Exception as e:
            logger.error(f"Failed to initialize worker pools: {e}")
            raise
    
    async def offload_cpu_intensive_task(
        self, 
        task: Callable, 
        *args, 
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Offload a CPU-intensive task to a separate process.
        
        Args:
            task: The function to execute
            *args: Positional arguments for the function
            timeout: Optional timeout in seconds
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the task execution
            
        Raises:
            RuntimeError: If process pool is not available
            asyncio.TimeoutError: If task times out
        """
        if not self._process_pool:
            raise RuntimeError("Process pool not available")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Create a partial function with the arguments
            partial_func = functools.partial(task, *args, **kwargs)
            
            # Submit to process pool and await result
            future = self._process_pool.submit(partial_func)
            
            if timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, future.result),
                    timeout=timeout
                )
            else:
                result = await loop.run_in_executor(None, future.result)
            
            logger.debug(f"CPU-intensive task completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"CPU-intensive task timed out after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"CPU-intensive task failed: {e}")
            raise
    
    async def schedule_parallel_tasks(self, tasks: List[Task]) -> List[TaskResult]:
        """
        Schedule multiple tasks for parallel execution.
        
        Args:
            tasks: List of tasks to execute in parallel
            
        Returns:
            List of task results in the same order as input tasks
        """
        if not tasks:
            return []
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)
        
        # Create coroutines for each task
        coroutines = []
        for task in sorted_tasks:
            coroutine = self._execute_single_task(task)
            coroutines.append(coroutine)
        
        # Execute all tasks concurrently
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Process results and handle exceptions
            task_results = []
            for i, (task, result) in enumerate(zip(sorted_tasks, results)):
                if isinstance(result, Exception):
                    task_result = TaskResult(
                        task_id=task.id,
                        success=False,
                        error=result,
                        execution_time=0.0
                    )
                else:
                    task_result = result
                
                task_results.append(task_result)
                self._results[task.id] = task_result
            
            logger.info(f"Completed parallel execution of {len(tasks)} tasks")
            return task_results
            
        except Exception as e:
            logger.error(f"Parallel task execution failed: {e}")
            raise
    
    async def _execute_single_task(self, task: Task) -> TaskResult:
        """Execute a single task with proper error handling and retries."""
        start_time = time.time()
        
        for attempt in range(task.max_retries + 1):
            try:
                # Choose appropriate executor based on task type
                if task.task_type == TaskType.CPU_INTENSIVE:
                    result = await self._execute_in_process_pool(task)
                elif task.task_type == TaskType.IO_BOUND:
                    result = await self._execute_in_thread_pool(task)
                else:
                    result = await self._execute_async_task(task)
                
                execution_time = time.time() - start_time
                
                return TaskResult(
                    task_id=task.id,
                    success=True,
                    result=result,
                    execution_time=execution_time
                )
                
            except Exception as e:
                logger.warning(f"Task {task.id} failed on attempt {attempt + 1}: {e}")
                
                if attempt == task.max_retries:
                    execution_time = time.time() - start_time
                    return TaskResult(
                        task_id=task.id,
                        success=False,
                        error=e,
                        execution_time=execution_time
                    )
                
                # Wait before retry with exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    async def _execute_in_process_pool(self, task: Task) -> Any:
        """Execute task in process pool."""
        if not self._process_pool:
            raise RuntimeError("Process pool not available")
        
        loop = asyncio.get_event_loop()
        partial_func = functools.partial(task.func, *task.args, **task.kwargs)
        
        future = self._process_pool.submit(partial_func)
        
        if task.timeout:
            return await asyncio.wait_for(
                loop.run_in_executor(None, future.result),
                timeout=task.timeout
            )
        else:
            return await loop.run_in_executor(None, future.result)
    
    async def _execute_in_thread_pool(self, task: Task) -> Any:
        """Execute task in thread pool."""
        if not self._thread_pool:
            raise RuntimeError("Thread pool not available")
        
        loop = asyncio.get_event_loop()
        partial_func = functools.partial(task.func, *task.args, **task.kwargs)
        
        if task.timeout:
            return await asyncio.wait_for(
                loop.run_in_executor(self._thread_pool, partial_func),
                timeout=task.timeout
            )
        else:
            return await loop.run_in_executor(self._thread_pool, partial_func)
    
    async def _execute_async_task(self, task: Task) -> Any:
        """Execute async task directly."""
        if asyncio.iscoroutinefunction(task.func):
            if task.timeout:
                return await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                return await task.func(*task.args, **task.kwargs)
        else:
            # Wrap synchronous function in async
            return await asyncio.to_thread(task.func, *task.args, **task.kwargs)
    
    def create_background_worker_pool(self, size: int) -> 'BackgroundWorkerPool':
        """
        Create a background worker pool for continuous task processing.
        
        Args:
            size: Number of background workers
            
        Returns:
            BackgroundWorkerPool instance
        """
        return BackgroundWorkerPool(self, size)
    
    async def wrap_blocking_operation(
        self, 
        blocking_func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Wrap a blocking operation to prevent main thread blocking.
        
        Args:
            blocking_func: The blocking function to wrap
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of the blocking operation
        """
        try:
            # Use thread pool for blocking operations
            if self._thread_pool:
                loop = asyncio.get_event_loop()
                partial_func = functools.partial(blocking_func, *args, **kwargs)
                return await loop.run_in_executor(self._thread_pool, partial_func)
            else:
                # Fallback to asyncio.to_thread if thread pool not available
                return await asyncio.to_thread(blocking_func, *args, **kwargs)
                
        except Exception as e:
            logger.error(f"Blocking operation wrapper failed: {e}")
            raise
    
    async def batch_process_tasks(
        self, 
        tasks: List[Task], 
        batch_size: int = 10,
        batch_timeout: float = 1.0
    ) -> List[TaskResult]:
        """
        Process tasks in batches for improved throughput.
        
        Args:
            tasks: List of tasks to process
            batch_size: Maximum number of tasks per batch
            batch_timeout: Maximum time to wait for batch to fill
            
        Returns:
            List of task results
        """
        if not tasks:
            return []
        
        results = []
        
        # Process tasks in batches
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            
            # Execute batch in parallel
            batch_results = await self.schedule_parallel_tasks(batch)
            results.extend(batch_results)
            
            # Small delay between batches to prevent overwhelming the system
            if i + batch_size < len(tasks):
                await asyncio.sleep(0.01)
        
        logger.info(f"Batch processed {len(tasks)} tasks in {len(results)} results")
        return results
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a completed task."""
        return self._results.get(task_id)
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get statistics about worker pool usage."""
        stats = {
            'process_pool_active': self._process_pool is not None,
            'thread_pool_active': self._thread_pool is not None,
            'completed_tasks': len(self._results),
            'running_tasks': len(self._running_tasks),
            'batch_queues': len(self._batch_queues)
        }
        
        if self._process_pool:
            stats['process_pool_workers'] = self._process_pool._max_workers
        
        if self._thread_pool:
            stats['thread_pool_workers'] = self._thread_pool._max_workers
        
        return stats
    
    async def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the orchestrator and clean up resources.
        
        Args:
            wait: Whether to wait for running tasks to complete
        """
        logger.info("Shutting down AsyncTaskOrchestrator")
        
        self._shutdown_event.set()
        
        # Cancel running tasks if not waiting
        if not wait:
            for task in self._running_tasks.values():
                task.cancel()
        
        # Shutdown worker pools
        if self._process_pool:
            self._process_pool.shutdown(wait=wait)
            self._process_pool = None
        
        if self._thread_pool:
            self._thread_pool.shutdown(wait=wait)
            self._thread_pool = None
        
        # Clear internal state
        self._results.clear()
        self._running_tasks.clear()
        self._batch_queues.clear()
        
        logger.info("AsyncTaskOrchestrator shutdown complete")


class BackgroundWorkerPool:
    """Background worker pool for continuous task processing."""
    
    def __init__(self, orchestrator: AsyncTaskOrchestrator, size: int):
        """Initialize background worker pool."""
        self.orchestrator = orchestrator
        self.size = size
        self.workers: List[asyncio.Task] = []
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
    
    async def start(self) -> None:
        """Start the background workers."""
        if self.running:
            return
        
        self.running = True
        
        # Create worker tasks
        for i in range(self.size):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {self.size} background workers")
    
    async def _worker_loop(self, worker_id: str) -> None:
        """Main loop for background workers."""
        logger.debug(f"Background worker {worker_id} started")
        
        while self.running:
            try:
                # Wait for task with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute task
                result = await self.orchestrator._execute_single_task(task)
                
                # Store result
                self.orchestrator._results[task.id] = result
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # No task available, continue loop
                continue
            except Exception as e:
                logger.error(f"Background worker {worker_id} error: {e}")
                continue
        
        logger.debug(f"Background worker {worker_id} stopped")
    
    async def submit_task(self, task: Task) -> None:
        """Submit a task to the background worker pool."""
        await self.task_queue.put(task)
    
    async def stop(self) -> None:
        """Stop the background worker pool."""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for all tasks to complete
        await self.task_queue.join()
        
        # Cancel worker tasks
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        self.workers.clear()
        logger.info("Background worker pool stopped")


# Utility functions for common async patterns

async def run_in_background(func: Callable, *args, **kwargs) -> asyncio.Task:
    """Run a function in the background and return the task."""
    if asyncio.iscoroutinefunction(func):
        return asyncio.create_task(func(*args, **kwargs))
    else:
        return asyncio.create_task(asyncio.to_thread(func, *args, **kwargs))


def async_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for adding retry logic to async functions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator


def cpu_bound_task(func: Callable) -> Callable:
    """Decorator to mark a function as CPU-bound for automatic process pool execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # This would be used with the orchestrator to automatically offload
        return func(*args, **kwargs)
    
    wrapper._is_cpu_bound = True
    return wrapper