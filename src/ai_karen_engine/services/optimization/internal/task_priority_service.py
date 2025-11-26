"""
Task Priority Service Helper

This module provides helper functionality for task priority operations in KAREN AI system.
It handles task prioritization, task scheduling, and other task-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid
import heapq

logger = logging.getLogger(__name__)


class TaskPriorityServiceHelper:
    """
    Helper service for task priority operations.
    
    This service provides methods for prioritizing, scheduling, and managing
    tasks in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the task priority service helper.
        
        Args:
            config: Configuration dictionary for the task priority service
        """
        self.config = config
        self.task_priority_enabled = config.get("task_priority_enabled", True)
        self.auto_prioritize = config.get("auto_prioritize", False)
        self.prioritization_interval = config.get("prioritization_interval", 60)  # 1 minute
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.task_queue = []
        self.task_priorities = {}
        self.task_schedules = {}
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the task priority service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing task priority service")
            
            # Initialize task priority
            if self.task_priority_enabled:
                await self._initialize_task_priority()
                
            self._is_initialized = True
            logger.info("Task priority service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing task priority service: {str(e)}")
            return False
    
    async def _initialize_task_priority(self) -> None:
        """Initialize task priority."""
        # In a real implementation, this would set up task priority
        logger.info("Initializing task priority")
        
    async def start(self) -> bool:
        """
        Start the task priority service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting task priority service")
            
            # Start task priority
            if self.task_priority_enabled:
                await self._start_task_priority()
                
            self._is_running = True
            logger.info("Task priority service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting task priority service: {str(e)}")
            return False
    
    async def _start_task_priority(self) -> None:
        """Start task priority."""
        # In a real implementation, this would start task priority
        logger.info("Starting task priority")
        
    async def stop(self) -> bool:
        """
        Stop the task priority service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping task priority service")
            
            # Stop task priority
            if self.task_priority_enabled:
                await self._stop_task_priority()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Task priority service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping task priority service: {str(e)}")
            return False
    
    async def _stop_task_priority(self) -> None:
        """Stop task priority."""
        # In a real implementation, this would stop task priority
        logger.info("Stopping task priority")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the task priority service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Task priority service is not initialized"}
                
            # Check task priority health
            task_health = {"status": "healthy", "message": "Task priority is healthy"}
            if self.task_priority_enabled:
                task_health = await self._health_check_task_priority()
                
            # Determine overall health
            overall_status = task_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Task priority service is {overall_status}",
                "task_health": task_health,
                "task_queue_size": len(self.task_queue),
                "task_priorities_count": len(self.task_priorities),
                "task_schedules_count": len(self.task_schedules)
            }
            
        except Exception as e:
            logger.error(f"Error checking task priority service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_task_priority(self) -> Dict[str, Any]:
        """Check task priority health."""
        # In a real implementation, this would check task priority health
        return {"status": "healthy", "message": "Task priority is healthy"}
        
    async def prioritize_task(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prioritize a task.
        
        Args:
            data: Optional data for the task prioritization
            context: Optional context for the task prioritization
            
        Returns:
            Dictionary containing the prioritization result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Get prioritization parameters
            task_id = data.get("task_id") if data else None
            task_data = data.get("task_data") if data else None
            priority = data.get("priority") if data else None
            options = data.get("options", {}) if data else {}
            
            # Validate task_id
            if not task_id:
                return {"status": "error", "message": "Task ID is required for task prioritization"}
            if not task_data:
                return {"status": "error", "message": "Task data is required for task prioritization"}
                
            # If priority is not provided, calculate it
            if priority is None:
                priority = await self._calculate_task_priority(task_id, task_data, options, context)
                
            # Create prioritization
            prioritization_id = str(uuid.uuid4())
            prioritization = {
                "prioritization_id": prioritization_id,
                "task_id": task_id,
                "priority": priority,
                "status": "prioritized",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add prioritization to task priorities
            self.task_priorities[task_id] = prioritization
            
            # Add task to queue
            await self._add_task_to_queue(task_id, priority, task_data, options, context)
            
            return {
                "status": "success",
                "message": "Task prioritized successfully",
                "prioritization_id": prioritization_id,
                "task_id": task_id,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"Error prioritizing task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _calculate_task_priority(self, task_id: str, task_data: Dict[str, Any], options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate task priority."""
        # In a real implementation, this would calculate task priority based on various factors
        logger.info(f"Calculating priority for task: {task_id}")
        
        # Get task type
        task_type = task_data.get("type", "default")
        
        # Get task urgency
        urgency = task_data.get("urgency", 0.5)  # 0.0 to 1.0
        
        # Get task importance
        importance = task_data.get("importance", 0.5)  # 0.0 to 1.0
        
        # Get task complexity
        complexity = task_data.get("complexity", 0.5)  # 0.0 to 1.0
        
        # Get task deadline (if any)
        deadline = task_data.get("deadline")
        deadline_factor = 0.0
        if deadline:
            deadline_time = datetime.fromisoformat(deadline)
            current_time = datetime.now()
            time_to_deadline = (deadline_time - current_time).total_seconds()
            
            # Calculate deadline factor (higher priority as deadline approaches)
            if time_to_deadline > 0:
                deadline_factor = min(1.0, 1.0 - (time_to_deadline / 86400.0))  # Normalize to days
            else:
                deadline_factor = 1.0  # Overdue
        
        # Calculate priority based on factors
        priority = (urgency * 0.3) + (importance * 0.3) + (deadline_factor * 0.3) + ((1.0 - complexity) * 0.1)
        
        # Adjust priority based on task type
        if task_type == "critical":
            priority = min(1.0, priority + 0.2)
        elif task_type == "urgent":
            priority = min(1.0, priority + 0.1)
        elif task_type == "background":
            priority = max(0.0, priority - 0.2)
        
        return priority
    
    async def _add_task_to_queue(self, task_id: str, priority: float, task_data: Dict[str, Any], options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> None:
        """Add task to queue."""
        # Check if queue is full
        if len(self.task_queue) >= self.max_queue_size:
            # Remove lowest priority task
            heapq.heappop(self.task_queue)
        
        # Add task to queue (using negative priority for max heap)
        heapq.heappush(self.task_queue, (-priority, task_id, task_data))
    
    async def get_next_task(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the next task from the queue.
        
        Args:
            data: Optional data for the request
            context: Optional context for the request
            
        Returns:
            Dictionary containing the next task
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Check if queue is empty
            if not self.task_queue:
                return {"status": "success", "message": "No tasks in queue", "task": None}
                
            # Get next task
            _, task_id, task_data = heapq.heappop(self.task_queue)
            
            # Get task priority
            task_priority = self.task_priorities.get(task_id)
            priority = task_priority["priority"] if task_priority else 0.0
            
            return {
                "status": "success",
                "message": "Next task retrieved successfully",
                "task": {
                    "task_id": task_id,
                    "priority": priority,
                    "task_data": task_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting next task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def schedule_task(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a task.
        
        Args:
            data: Optional data for the task scheduling
            context: Optional context for the task scheduling
            
        Returns:
            Dictionary containing the scheduling result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Get scheduling parameters
            task_id = data.get("task_id") if data else None
            task_data = data.get("task_data") if data else None
            schedule_time = data.get("schedule_time") if data else None
            options = data.get("options", {}) if data else {}
            
            # Validate task_id
            if not task_id:
                return {"status": "error", "message": "Task ID is required for task scheduling"}
            if not task_data:
                return {"status": "error", "message": "Task data is required for task scheduling"}
            if not schedule_time:
                return {"status": "error", "message": "Schedule time is required for task scheduling"}
                
            # Parse schedule time
            if isinstance(schedule_time, str):
                schedule_time = datetime.fromisoformat(schedule_time)
            elif not isinstance(schedule_time, datetime):
                return {"status": "error", "message": "Invalid schedule time format"}
                
            # Create schedule
            schedule_id = str(uuid.uuid4())
            schedule = {
                "schedule_id": schedule_id,
                "task_id": task_id,
                "task_data": task_data,
                "schedule_time": schedule_time.isoformat(),
                "status": "scheduled",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add schedule to task schedules
            self.task_schedules[schedule_id] = schedule
            
            return {
                "status": "success",
                "message": "Task scheduled successfully",
                "schedule_id": schedule_id,
                "task_id": task_id,
                "schedule_time": schedule_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_scheduled_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get scheduled tasks.
        
        Args:
            data: Optional data for the request
            context: Optional context for the request
            
        Returns:
            Dictionary containing the scheduled tasks
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Get current time
            current_time = datetime.now()
            
            # Get scheduled tasks
            scheduled_tasks = []
            for schedule_id, schedule in self.task_schedules.items():
                schedule_time = datetime.fromisoformat(schedule["schedule_time"])
                
                # Check if task is scheduled for now or in the past
                if schedule_time <= current_time:
                    scheduled_tasks.append({
                        "schedule_id": schedule_id,
                        "task_id": schedule["task_id"],
                        "task_data": schedule["task_data"],
                        "schedule_time": schedule["schedule_time"]
                    })
                    
                    # Remove schedule
                    self.task_schedules.pop(schedule_id)
            
            return {
                "status": "success",
                "message": "Scheduled tasks retrieved successfully",
                "scheduled_tasks": scheduled_tasks,
                "count": len(scheduled_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduled tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def reprioritize_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reprioritize tasks.
        
        Args:
            data: Optional data for the task reprioritization
            context: Optional context for the task reprioritization
            
        Returns:
            Dictionary containing the reprioritization result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Get reprioritization parameters
            reprioritization_type = data.get("reprioritization_type", "auto") if data else "auto"
            options = data.get("options", {}) if data else {}
            
            # Create reprioritization
            reprioritization_id = str(uuid.uuid4())
            reprioritization = {
                "reprioritization_id": reprioritization_id,
                "reprioritization_type": reprioritization_type,
                "status": "reprioritizing",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Reprioritize tasks
            result = await self._reprioritize_tasks(reprioritization_type, options, context)
            
            return {
                "status": "success",
                "message": "Tasks reprioritized successfully",
                "reprioritization_id": reprioritization_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error reprioritizing tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _reprioritize_tasks(self, reprioritization_type: str, options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reprioritize tasks."""
        # In a real implementation, this would reprioritize tasks
        logger.info(f"Reprioritizing tasks with type: {reprioritization_type}")
        
        # Simulate task reprioritization
        await asyncio.sleep(1)
        
        # Get current tasks in queue
        current_tasks = []
        temp_queue = []
        
        # Extract tasks from queue
        while self.task_queue:
            neg_priority, task_id, task_data = heapq.heappop(self.task_queue)
            priority = -neg_priority
            current_tasks.append((priority, task_id, task_data))
            temp_queue.append((neg_priority, task_id, task_data))
        
        # Restore queue
        for item in temp_queue:
            heapq.heappush(self.task_queue, item)
        
        # Reprioritize tasks based on reprioritization type
        reprioritized_tasks = []
        for priority, task_id, task_data in current_tasks:
            if reprioritization_type in ["auto", "urgency"]:
                # Increase priority for urgent tasks
                if task_data.get("urgency", 0.5) > 0.7:
                    priority = min(1.0, priority + 0.1)
            if reprioritization_type in ["auto", "importance"]:
                # Increase priority for important tasks
                if task_data.get("importance", 0.5) > 0.7:
                    priority = min(1.0, priority + 0.1)
            if reprioritization_type in ["auto", "deadline"]:
                # Increase priority for tasks with approaching deadlines
                deadline = task_data.get("deadline")
                if deadline:
                    deadline_time = datetime.fromisoformat(deadline)
                    current_time = datetime.now()
                    time_to_deadline = (deadline_time - current_time).total_seconds()
                    if 0 < time_to_deadline < 3600:  # Less than 1 hour
                        priority = min(1.0, priority + 0.2)
            
            # Update task priority
            self.task_priorities[task_id]["priority"] = priority
            old_priority = float(-neg_priority) if isinstance(neg_priority, (int, float)) else 0.0
            reprioritized_tasks.append({
                "task_id": task_id,
                "old_priority": old_priority,
                "new_priority": priority,
                "change": priority - old_priority
            })
        
        # Rebuild queue with new priorities
        self.task_queue = []
        for priority, task_id, task_data in current_tasks:
            heapq.heappush(self.task_queue, (-priority, task_id, task_data))
        
        # Return reprioritization result
        result = {
            "reprioritization_type": reprioritization_type,
            "status": "completed",
            "message": "Task reprioritization completed successfully",
            "reprioritization_time": 1.0,  # Simulated reprioritization time
            "reprioritized_tasks": reprioritized_tasks,
            "total_tasks": len(reprioritized_tasks)
        }
        
        return result
    
    async def balance_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Balance tasks across resources.
        
        Args:
            data: Optional data for the task balancing
            context: Optional context for the task balancing
            
        Returns:
            Dictionary containing the balancing result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Check if task priority is enabled
            if not self.task_priority_enabled:
                return {"status": "error", "message": "Task priority is disabled"}
                
            # Get balancing parameters
            resources = data.get("resources", []) if data else []
            balancing_strategy = data.get("balancing_strategy", "load") if data else "load"
            options = data.get("options", {}) if data else {}
            
            # Create balancing
            balancing_id = str(uuid.uuid4())
            balancing = {
                "balancing_id": balancing_id,
                "resources": resources,
                "balancing_strategy": balancing_strategy,
                "status": "balancing",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Balance tasks
            result = await self._balance_tasks(resources, balancing_strategy, options, context)
            
            return {
                "status": "success",
                "message": "Tasks balanced successfully",
                "balancing_id": balancing_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error balancing tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _balance_tasks(self, resources: List[str], balancing_strategy: str, options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Balance tasks across resources."""
        # In a real implementation, this would balance tasks across resources
        logger.info(f"Balancing tasks across resources: {resources} with strategy: {balancing_strategy}")
        
        # Simulate task balancing
        await asyncio.sleep(1)
        
        # Get current tasks in queue
        current_tasks = []
        temp_queue = []
        
        # Extract tasks from queue
        while self.task_queue:
            neg_priority, task_id, task_data = heapq.heappop(self.task_queue)
            priority = -neg_priority
            current_tasks.append((priority, task_id, task_data))
            temp_queue.append((neg_priority, task_id, task_data))
        
        # Restore queue
        for item in temp_queue:
            heapq.heappush(self.task_queue, item)
        
        # If no resources provided, use default resources
        if not resources:
            resources = ["resource1", "resource2", "resource3"]
        
        # Distribute tasks across resources based on balancing strategy
        balanced_tasks = {}
        for resource in resources:
            balanced_tasks[resource] = []
        
        # Distribute tasks based on balancing strategy
        if balancing_strategy == "round_robin":
            for i, (priority, task_id, task_data) in enumerate(current_tasks):
                resource = resources[i % len(resources)]
                balanced_tasks[resource].append({
                    "task_id": task_id,
                    "priority": priority,
                    "task_data": task_data
                })
        elif balancing_strategy == "load":
            # Sort tasks by priority (highest first)
            current_tasks.sort(key=lambda x: x[0], reverse=True)
            
            # Distribute tasks to least loaded resource
            resource_loads = {resource: 0 for resource in resources}
            
            for priority, task_id, task_data in current_tasks:
                # Find least loaded resource
                least_loaded_resource = min(resource_loads.items(), key=lambda x: x[1])[0]
                
                # Add task to least loaded resource
                balanced_tasks[least_loaded_resource].append({
                    "task_id": task_id,
                    "priority": priority,
                    "task_data": task_data
                })
                
                # Update resource load
                resource_loads[least_loaded_resource] += 1
        elif balancing_strategy == "priority":
            # Sort tasks by priority (highest first)
            current_tasks.sort(key=lambda x: x[0], reverse=True)
            
            # Distribute tasks based on priority and resource capacity
            resource_capacities = {resource: 1.0 for resource in resources}
            
            for priority, task_id, task_data in current_tasks:
                # Find resource with highest capacity
                highest_capacity_resource = max(resource_capacities.items(), key=lambda x: x[1])[0]
                
                # Add task to highest capacity resource
                balanced_tasks[highest_capacity_resource].append({
                    "task_id": task_id,
                    "priority": priority,
                    "task_data": task_data
                })
                
                # Update resource capacity
                resource_capacities[highest_capacity_resource] *= 0.9  # Reduce capacity
        
        # Calculate statistics
        task_counts = {resource: len(tasks) for resource, tasks in balanced_tasks.items()}
        total_tasks = sum(task_counts.values())
        average_tasks_per_resource = total_tasks / len(resources) if resources else 0
        
        # Return balancing result
        result = {
            "balancing_strategy": balancing_strategy,
            "status": "completed",
            "message": "Task balancing completed successfully",
            "balancing_time": 1.0,  # Simulated balancing time
            "balanced_tasks": balanced_tasks,
            "task_counts": task_counts,
            "total_tasks": total_tasks,
            "average_tasks_per_resource": average_tasks_per_resource
        }
        
        return result
    
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the task priority service.
        
        Args:
            data: Optional data for the status request
            context: Optional context for the status request
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            status = {
                "task_priority_enabled": self.task_priority_enabled,
                "auto_prioritize": self.auto_prioritize,
                "prioritization_interval": self.prioritization_interval,
                "max_queue_size": self.max_queue_size,
                "is_running": self._is_running,
                "task_queue_size": len(self.task_queue),
                "task_priorities_count": len(self.task_priorities),
                "task_schedules_count": len(self.task_schedules)
            }
            
            return {
                "status": "success",
                "message": "Task priority status retrieved successfully",
                "task_priority_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting task priority status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the task priority service.
        
        Args:
            data: Optional data for the stats request
            context: Optional context for the stats request
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task priority service is not initialized"}
                
            # Get current tasks in queue
            current_tasks = []
            temp_queue = []
            
            # Extract tasks from queue
            while self.task_queue:
                neg_priority, task_id, task_data = heapq.heappop(self.task_queue)
                priority = -neg_priority
                current_tasks.append((priority, task_id, task_data))
                temp_queue.append((neg_priority, task_id, task_data))
            
            # Restore queue
            for item in temp_queue:
                heapq.heappush(self.task_queue, item)
            
            # Calculate priority distribution
            priority_distribution = {
                "high": len([t for t in current_tasks if t[0] > 0.7]),
                "medium": len([t for t in current_tasks if 0.3 <= t[0] <= 0.7]),
                "low": len([t for t in current_tasks if t[0] < 0.3])
            }
            
            # Calculate type distribution
            type_distribution = {}
            for priority, task_id, task_data in current_tasks:
                task_type = task_data.get("type", "default")
                if task_type not in type_distribution:
                    type_distribution[task_type] = 0
                type_distribution[task_type] += 1
            
            # Calculate average priority
            average_priority = sum(t[0] for t in current_tasks) / len(current_tasks) if current_tasks else 0
            
            # Calculate highest and lowest priority
            highest_priority = max(t[0] for t in current_tasks) if current_tasks else 0
            lowest_priority = min(t[0] for t in current_tasks) if current_tasks else 0
            
            # Get scheduled tasks
            scheduled_tasks = []
            current_time = datetime.now()
            for schedule_id, schedule in self.task_schedules.items():
                schedule_time = datetime.fromisoformat(schedule["schedule_time"])
                scheduled_tasks.append({
                    "schedule_id": schedule_id,
                    "task_id": schedule["task_id"],
                    "schedule_time": schedule["schedule_time"],
                    "time_until_schedule": (schedule_time - current_time).total_seconds()
                })
            
            # Sort scheduled tasks by schedule time
            scheduled_tasks.sort(key=lambda x: x["time_until_schedule"])
            
            stats = {
                "task_priority_enabled": self.task_priority_enabled,
                "auto_prioritize": self.auto_prioritize,
                "prioritization_interval": self.prioritization_interval,
                "max_queue_size": self.max_queue_size,
                "is_running": self._is_running,
                "task_queue_size": len(self.task_queue),
                "task_priorities_count": len(self.task_priorities),
                "task_schedules_count": len(self.task_schedules),
                "priority_distribution": priority_distribution,
                "type_distribution": type_distribution,
                "average_priority": average_priority,
                "highest_priority": highest_priority,
                "lowest_priority": lowest_priority,
                "scheduled_tasks": scheduled_tasks[:10]  # Return top 10 scheduled tasks
            }
            
            return {
                "status": "success",
                "message": "Task priority statistics retrieved successfully",
                "task_priority_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting task priority statistics: {str(e)}")
            return {"status": "error", "message": str(e)}