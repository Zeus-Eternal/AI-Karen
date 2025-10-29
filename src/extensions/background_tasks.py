"""
Background Task System for the AI Karen Extensions System.

This module provides comprehensive background task management for extensions,
including scheduled tasks, event-driven tasks, task isolation, and monitoring.
"""

import asyncio
import logging
import traceback
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from croniter import croniter
import uuid
import json
from pathlib import Path

from .models import ExtensionManifest, ExtensionRecord, ExtensionBackgroundTask


logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Background task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class TaskTriggerType(str, Enum):
    """Task trigger type enumeration."""
    CRON = "cron"
    INTERVAL = "interval"
    EVENT = "event"
    MANUAL = "manual"


@dataclass
class TaskExecution:
    """Represents a single task execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    extension_name: str = ""
    status: TaskStatus = TaskStatus.PENDING
    trigger_type: TaskTriggerType = TaskTriggerType.MANUAL
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDefinition:
    """Defines a background task."""
    name: str
    extension_name: str
    function_path: str
    description: Optional[str] = None
    schedule: Optional[str] = None  # Cron expression
    interval_seconds: Optional[int] = None
    trigger_type: TaskTriggerType = TaskTriggerType.MANUAL
    enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventTrigger:
    """Defines an event-driven task trigger."""
    event_type: str
    task_name: str
    extension_name: str
    filter_conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class TaskResourceMonitor:
    """Monitors resource usage for task executions."""
    
    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def start_monitoring(self, execution_id: str, task_name: str) -> None:
        """Start monitoring a task execution."""
        self.active_tasks[execution_id] = {
            'task_name': task_name,
            'start_time': datetime.now(timezone.utc),
            'start_memory': self._get_memory_usage(),
            'start_cpu': self._get_cpu_usage()
        }
    
    async def stop_monitoring(self, execution_id: str) -> Dict[str, Any]:
        """Stop monitoring and return resource usage."""
        if execution_id not in self.active_tasks:
            return {}
        
        task_info = self.active_tasks.pop(execution_id)
        end_time = datetime.now(timezone.utc)
        
        return {
            'duration_seconds': (end_time - task_info['start_time']).total_seconds(),
            'memory_usage_mb': self._get_memory_usage() - task_info['start_memory'],
            'cpu_usage_percent': self._get_cpu_usage() - task_info['start_cpu'],
            'peak_memory_mb': self._get_peak_memory_usage(execution_id),
            'avg_cpu_percent': self._get_avg_cpu_usage(execution_id)
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            return 0.0
    
    def _get_peak_memory_usage(self, execution_id: str) -> float:
        """Get peak memory usage for a task."""
        # Simplified implementation - in production, this would track over time
        return self._get_memory_usage()
    
    def _get_avg_cpu_usage(self, execution_id: str) -> float:
        """Get average CPU usage for a task."""
        # Simplified implementation - in production, this would track over time
        return self._get_cpu_usage()


class TaskExecutor:
    """Executes background tasks with isolation and monitoring."""
    
    def __init__(self, resource_monitor: TaskResourceMonitor):
        self.resource_monitor = resource_monitor
        self.active_executions: Dict[str, asyncio.Task] = {}
    
    async def execute_task(
        self, 
        task_def: TaskDefinition, 
        extension_instance: Any,
        trigger_type: TaskTriggerType = TaskTriggerType.MANUAL,
        event_data: Optional[Dict[str, Any]] = None
    ) -> TaskExecution:
        """Execute a background task."""
        execution = TaskExecution(
            task_name=task_def.name,
            extension_name=task_def.extension_name,
            trigger_type=trigger_type,
            scheduled_at=datetime.now(timezone.utc),
            metadata=event_data or {}
        )
        
        try:
            logger.info(f"Starting task execution: {task_def.name} ({execution.id})")
            
            # Start resource monitoring
            await self.resource_monitor.start_monitoring(execution.id, task_def.name)
            
            # Update execution status
            execution.status = TaskStatus.RUNNING
            execution.started_at = datetime.now(timezone.utc)
            
            # Create task with timeout
            task_coro = self._run_task_function(task_def, extension_instance, execution, event_data)
            task = asyncio.create_task(task_coro)
            self.active_executions[execution.id] = task
            
            # Wait for completion with timeout
            try:
                execution.result = await asyncio.wait_for(task, timeout=task_def.timeout_seconds)
                execution.status = TaskStatus.COMPLETED
                
            except asyncio.TimeoutError:
                task.cancel()
                execution.status = TaskStatus.FAILED
                execution.error = f"Task timed out after {task_def.timeout_seconds} seconds"
                logger.error(f"Task {task_def.name} timed out")
                
            except Exception as e:
                execution.status = TaskStatus.FAILED
                execution.error = str(e)
                execution.traceback = traceback.format_exc()
                logger.error(f"Task {task_def.name} failed: {e}")
            
            # Complete execution
            execution.completed_at = datetime.now(timezone.utc)
            if execution.started_at:
                execution.duration_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
            
            # Stop resource monitoring
            execution.resource_usage = await self.resource_monitor.stop_monitoring(execution.id)
            
            # Remove from active executions
            if execution.id in self.active_executions:
                del self.active_executions[execution.id]
            
            logger.info(
                f"Task execution completed: {task_def.name} ({execution.id}) - "
                f"Status: {execution.status.value}"
            )
            
            return execution
            
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.traceback = traceback.format_exc()
            execution.completed_at = datetime.now(timezone.utc)
            
            logger.error(f"Task execution error: {task_def.name} ({execution.id}) - {e}")
            return execution
    
    async def _run_task_function(
        self, 
        task_def: TaskDefinition, 
        extension_instance: Any,
        execution: TaskExecution,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Run the actual task function."""
        try:
            # Parse function path
            module_path, function_name = task_def.function_path.rsplit('.', 1)
            
            # Get the function from the extension instance
            if hasattr(extension_instance, function_name):
                task_function = getattr(extension_instance, function_name)
            else:
                # Try to import from module path
                parts = module_path.split('.')
                current = extension_instance
                for part in parts:
                    if hasattr(current, part):
                        current = getattr(current, part)
                    else:
                        raise AttributeError(f"Function path not found: {task_def.function_path}")
                
                if hasattr(current, function_name):
                    task_function = getattr(current, function_name)
                else:
                    raise AttributeError(f"Function not found: {function_name}")
            
            # Prepare function arguments
            kwargs = {
                'execution_id': execution.id,
                'task_name': task_def.name,
                'extension_name': task_def.extension_name
            }
            
            if event_data:
                kwargs['event_data'] = event_data
            
            # Call the function
            if asyncio.iscoroutinefunction(task_function):
                result = await task_function(**kwargs)
            else:
                result = task_function(**kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Error running task function {task_def.function_path}: {e}")
            raise
    
    async def cancel_task(self, execution_id: str) -> bool:
        """Cancel a running task."""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            del self.active_executions[execution_id]
            logger.info(f"Task execution cancelled: {execution_id}")
            return True
        return False
    
    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs."""
        return list(self.active_executions.keys())


class TaskScheduler:
    """Manages scheduled task execution."""
    
    def __init__(self, task_executor: TaskExecutor):
        self.task_executor = task_executor
        self.scheduled_tasks: Dict[str, TaskDefinition] = {}
        self.scheduler_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self) -> None:
        """Start the task scheduler."""
        if self.running:
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Task scheduler started")
    
    async def stop(self) -> None:
        """Stop the task scheduler."""
        self.running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
            self.scheduler_task = None
        
        logger.info("Task scheduler stopped")
    
    def add_scheduled_task(self, task_def: TaskDefinition) -> None:
        """Add a scheduled task."""
        task_key = f"{task_def.extension_name}.{task_def.name}"
        self.scheduled_tasks[task_key] = task_def
        logger.info(f"Added scheduled task: {task_key}")
    
    def remove_scheduled_task(self, extension_name: str, task_name: str) -> None:
        """Remove a scheduled task."""
        task_key = f"{extension_name}.{task_name}"
        if task_key in self.scheduled_tasks:
            del self.scheduled_tasks[task_key]
            logger.info(f"Removed scheduled task: {task_key}")
    
    def get_scheduled_tasks(self) -> List[TaskDefinition]:
        """Get all scheduled tasks."""
        return list(self.scheduled_tasks.values())
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check each scheduled task
                for task_def in list(self.scheduled_tasks.values()):
                    if not task_def.enabled:
                        continue
                    
                    should_run = False
                    
                    # Check cron schedule
                    if task_def.trigger_type == TaskTriggerType.CRON and task_def.schedule:
                        should_run = self._should_run_cron_task(task_def, current_time)
                    
                    # Check interval schedule
                    elif task_def.trigger_type == TaskTriggerType.INTERVAL and task_def.interval_seconds:
                        should_run = self._should_run_interval_task(task_def, current_time)
                    
                    if should_run:
                        # Schedule task execution (don't await to avoid blocking)
                        asyncio.create_task(self._execute_scheduled_task(task_def))
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    def _should_run_cron_task(self, task_def: TaskDefinition, current_time: datetime) -> bool:
        """Check if a cron task should run."""
        try:
            if not task_def.schedule:
                return False
            
            # Use croniter to check if task should run
            cron = croniter(task_def.schedule, current_time - timedelta(minutes=1))
            next_run = cron.get_next(datetime)
            
            # Check if next run time is within the last minute
            return next_run <= current_time
            
        except Exception as e:
            logger.error(f"Error checking cron schedule for {task_def.name}: {e}")
            return False
    
    def _should_run_interval_task(self, task_def: TaskDefinition, current_time: datetime) -> bool:
        """Check if an interval task should run."""
        # This is a simplified implementation
        # In production, you'd track last execution times
        return True  # For now, always run interval tasks when checked
    
    async def _execute_scheduled_task(self, task_def: TaskDefinition) -> None:
        """Execute a scheduled task."""
        try:
            # This would need access to the extension instance
            # For now, we'll log that the task should be executed
            logger.info(f"Scheduled task ready for execution: {task_def.name}")
            
            # In the full implementation, this would:
            # 1. Get the extension instance from the extension manager
            # 2. Execute the task using the task executor
            # 3. Store the execution result
            
        except Exception as e:
            logger.error(f"Error executing scheduled task {task_def.name}: {e}")


class EventManager:
    """Manages event-driven task triggers."""
    
    def __init__(self, task_executor: TaskExecutor):
        self.task_executor = task_executor
        self.event_triggers: Dict[str, List[EventTrigger]] = {}
        self.event_handlers: Dict[str, Callable] = {}
    
    def register_event_trigger(self, trigger: EventTrigger) -> None:
        """Register an event trigger."""
        if trigger.event_type not in self.event_triggers:
            self.event_triggers[trigger.event_type] = []
        
        self.event_triggers[trigger.event_type].append(trigger)
        logger.info(f"Registered event trigger: {trigger.event_type} -> {trigger.task_name}")
    
    def unregister_event_trigger(self, event_type: str, task_name: str, extension_name: str) -> None:
        """Unregister an event trigger."""
        if event_type in self.event_triggers:
            self.event_triggers[event_type] = [
                t for t in self.event_triggers[event_type]
                if not (t.task_name == task_name and t.extension_name == extension_name)
            ]
            logger.info(f"Unregistered event trigger: {event_type} -> {task_name}")
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """Emit an event and trigger associated tasks."""
        triggered_tasks = []
        
        if event_type not in self.event_triggers:
            return triggered_tasks
        
        for trigger in self.event_triggers[event_type]:
            if not trigger.enabled:
                continue
            
            # Check filter conditions
            if self._matches_filter(event_data, trigger.filter_conditions):
                # Trigger the task (this would need extension manager integration)
                logger.info(
                    f"Event {event_type} triggered task: "
                    f"{trigger.extension_name}.{trigger.task_name}"
                )
                triggered_tasks.append(f"{trigger.extension_name}.{trigger.task_name}")
        
        return triggered_tasks
    
    def _matches_filter(self, event_data: Dict[str, Any], filter_conditions: Dict[str, Any]) -> bool:
        """Check if event data matches filter conditions."""
        if not filter_conditions:
            return True
        
        for key, expected_value in filter_conditions.items():
            if key not in event_data:
                return False
            
            actual_value = event_data[key]
            
            # Simple equality check (can be enhanced with operators)
            if actual_value != expected_value:
                return False
        
        return True
    
    def get_event_triggers(self) -> Dict[str, List[EventTrigger]]:
        """Get all event triggers."""
        return self.event_triggers.copy()


class BackgroundTaskManager:
    """Main background task management system for extensions."""
    
    def __init__(self, extension_manager=None):
        self.extension_manager = extension_manager
        
        # Core components
        self.resource_monitor = TaskResourceMonitor()
        self.task_executor = TaskExecutor(self.resource_monitor)
        self.task_scheduler = TaskScheduler(self.task_executor)
        self.event_manager = EventManager(self.task_executor)
        
        # Task tracking
        self.task_definitions: Dict[str, TaskDefinition] = {}
        self.execution_history: List[TaskExecution] = []
        self.max_history_size = 1000
        
        # State
        self.running = False
    
    async def initialize(self) -> None:
        """Initialize the background task manager."""
        try:
            logger.info("Initializing Background Task Manager")
            
            # Start scheduler
            await self.task_scheduler.start()
            
            self.running = True
            logger.info("Background Task Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Background Task Manager: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the background task manager."""
        try:
            logger.info("Shutting down Background Task Manager")
            
            self.running = False
            
            # Stop scheduler
            await self.task_scheduler.stop()
            
            # Cancel active tasks
            active_executions = self.task_executor.get_active_executions()
            for execution_id in active_executions:
                await self.task_executor.cancel_task(execution_id)
            
            logger.info("Background Task Manager shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during Background Task Manager shutdown: {e}")
    
    def register_extension_tasks(self, extension_record: ExtensionRecord) -> None:
        """Register background tasks for an extension."""
        try:
            extension_name = extension_record.manifest.name
            logger.info(f"Registering background tasks for extension: {extension_name}")
            
            # Get background tasks from extension instance
            if extension_record.instance:
                task_configs = extension_record.instance.create_background_tasks()
                
                for task_config in task_configs:
                    task_def = TaskDefinition(
                        name=task_config['name'],
                        extension_name=extension_name,
                        function_path=task_config['function'],
                        description=task_config.get('description'),
                        schedule=task_config.get('schedule'),
                        trigger_type=TaskTriggerType.CRON if task_config.get('schedule') else TaskTriggerType.MANUAL,
                        enabled=True
                    )
                    
                    # Register task
                    task_key = f"{extension_name}.{task_def.name}"
                    self.task_definitions[task_key] = task_def
                    
                    # Add to scheduler if it's a scheduled task
                    if task_def.trigger_type == TaskTriggerType.CRON:
                        self.task_scheduler.add_scheduled_task(task_def)
                    
                    logger.info(f"Registered task: {task_key}")
            
            # Also register tasks from manifest
            for task_config in extension_record.manifest.background_tasks:
                if task_config.enabled:
                    task_def = TaskDefinition(
                        name=task_config.name,
                        extension_name=extension_name,
                        function_path=task_config.function,
                        description=task_config.description,
                        schedule=task_config.schedule,
                        trigger_type=TaskTriggerType.CRON,
                        enabled=True
                    )
                    
                    task_key = f"{extension_name}.{task_def.name}"
                    self.task_definitions[task_key] = task_def
                    self.task_scheduler.add_scheduled_task(task_def)
                    
                    logger.info(f"Registered manifest task: {task_key}")
            
        except Exception as e:
            logger.error(f"Error registering tasks for extension {extension_name}: {e}")
    
    def unregister_extension_tasks(self, extension_name: str) -> None:
        """Unregister background tasks for an extension."""
        try:
            logger.info(f"Unregistering background tasks for extension: {extension_name}")
            
            # Remove tasks from definitions
            tasks_to_remove = [
                key for key in self.task_definitions.keys()
                if key.startswith(f"{extension_name}.")
            ]
            
            for task_key in tasks_to_remove:
                task_def = self.task_definitions[task_key]
                
                # Remove from scheduler
                self.task_scheduler.remove_scheduled_task(extension_name, task_def.name)
                
                # Remove from definitions
                del self.task_definitions[task_key]
                
                logger.info(f"Unregistered task: {task_key}")
            
        except Exception as e:
            logger.error(f"Error unregistering tasks for extension {extension_name}: {e}")
    
    async def execute_task_manually(
        self, 
        extension_name: str, 
        task_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> TaskExecution:
        """Execute a task manually."""
        try:
            task_key = f"{extension_name}.{task_name}"
            
            if task_key not in self.task_definitions:
                raise ValueError(f"Task not found: {task_key}")
            
            task_def = self.task_definitions[task_key]
            
            # Get extension instance
            if not self.extension_manager:
                raise RuntimeError("Extension manager not available")
            
            extension_record = self.extension_manager.get_extension_by_name(extension_name)
            if not extension_record or not extension_record.instance:
                raise RuntimeError(f"Extension not loaded: {extension_name}")
            
            # Execute task
            execution = await self.task_executor.execute_task(
                task_def,
                extension_record.instance,
                TaskTriggerType.MANUAL,
                parameters
            )
            
            # Store execution in history
            self._add_to_history(execution)
            
            return execution
            
        except Exception as e:
            logger.error(f"Error executing task manually {extension_name}.{task_name}: {e}")
            raise
    
    async def emit_event(self, event_type: str, event_data: Dict[str, Any]) -> List[str]:
        """Emit an event that may trigger tasks."""
        return await self.event_manager.emit_event(event_type, event_data)
    
    def register_event_trigger(
        self, 
        event_type: str, 
        extension_name: str, 
        task_name: str,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an event trigger for a task."""
        trigger = EventTrigger(
            event_type=event_type,
            task_name=task_name,
            extension_name=extension_name,
            filter_conditions=filter_conditions or {},
            enabled=True
        )
        
        self.event_manager.register_event_trigger(trigger)
    
    def get_task_definitions(self) -> List[TaskDefinition]:
        """Get all registered task definitions."""
        return list(self.task_definitions.values())
    
    def get_task_definition(self, extension_name: str, task_name: str) -> Optional[TaskDefinition]:
        """Get a specific task definition."""
        task_key = f"{extension_name}.{task_name}"
        return self.task_definitions.get(task_key)
    
    def get_execution_history(
        self, 
        extension_name: Optional[str] = None,
        task_name: Optional[str] = None,
        limit: int = 100
    ) -> List[TaskExecution]:
        """Get task execution history."""
        history = self.execution_history
        
        # Filter by extension
        if extension_name:
            history = [e for e in history if e.extension_name == extension_name]
        
        # Filter by task name
        if task_name:
            history = [e for e in history if e.task_name == task_name]
        
        # Sort by completion time (most recent first)
        history.sort(key=lambda e: e.completed_at or datetime.min, reverse=True)
        
        return history[:limit]
    
    def get_active_executions(self) -> List[str]:
        """Get active task executions."""
        return self.task_executor.get_active_executions()
    
    async def cancel_task_execution(self, execution_id: str) -> bool:
        """Cancel a running task execution."""
        return await self.task_executor.cancel_task(execution_id)
    
    def _add_to_history(self, execution: TaskExecution) -> None:
        """Add execution to history."""
        self.execution_history.append(execution)
        
        # Trim history if it gets too large
        if len(self.execution_history) > self.max_history_size:
            self.execution_history = self.execution_history[-self.max_history_size:]
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get background task manager statistics."""
        return {
            'running': self.running,
            'registered_tasks': len(self.task_definitions),
            'scheduled_tasks': len(self.task_scheduler.get_scheduled_tasks()),
            'active_executions': len(self.get_active_executions()),
            'total_executions': len(self.execution_history),
            'event_triggers': sum(len(triggers) for triggers in self.event_manager.get_event_triggers().values())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Background task manager health check."""
        try:
            stats = self.get_manager_stats()
            
            return {
                'status': 'healthy' if self.running else 'stopped',
                'registered_tasks': stats['registered_tasks'],
                'scheduled_tasks': stats['scheduled_tasks'],
                'active_executions': stats['active_executions'],
                'scheduler_running': self.task_scheduler.running,
                'resource_monitor_active': len(self.resource_monitor.active_tasks) > 0
            }
            
        except Exception as e:
            logger.error(f"Background task manager health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }