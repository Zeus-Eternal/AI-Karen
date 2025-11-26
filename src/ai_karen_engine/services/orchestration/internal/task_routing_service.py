"""
Task Routing Service Helper

This module provides helper functionality for task routing operations in KAREN AI system.
It handles task routing, task execution, and other task routing-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class TaskRoutingServiceHelper:
    """
    Helper service for task routing operations.
    
    This service provides methods for routing, executing, and monitoring tasks
    in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the task routing service helper.
        
        Args:
            config: Configuration dictionary for the task routing service
        """
        self.config = config
        self.task_routing_enabled = config.get("task_routing_enabled", True)
        self.routing_strategies = config.get("routing_strategies", ["priority", "load_balancing", "specialization"])
        self.task_queue = []
        self.active_tasks = {}
        self.completed_tasks = []
        self.max_active_tasks = config.get("max_active_tasks", 10)
        self.task_timeout = config.get("task_timeout", 300)  # 5 minutes
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the task routing service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing task routing service")
            
            # Initialize task routing
            if self.task_routing_enabled:
                await self._initialize_task_routing()
                
            self._is_initialized = True
            logger.info("Task routing service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing task routing service: {str(e)}")
            return False
    
    async def _initialize_task_routing(self) -> None:
        """Initialize task routing."""
        # In a real implementation, this would set up task routing
        logger.info(f"Initializing task routing with strategies: {self.routing_strategies}")
        
    async def start(self) -> bool:
        """
        Start the task routing service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting task routing service")
            
            # Start task routing
            if self.task_routing_enabled:
                await self._start_task_routing()
                
            self._is_running = True
            logger.info("Task routing service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting task routing service: {str(e)}")
            return False
    
    async def _start_task_routing(self) -> None:
        """Start task routing."""
        # In a real implementation, this would start task routing
        logger.info("Starting task routing")
        
        # Start task processing
        asyncio.create_task(self._process_tasks())
        
    async def stop(self) -> bool:
        """
        Stop the task routing service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping task routing service")
            
            # Stop task routing
            if self.task_routing_enabled:
                await self._stop_task_routing()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Task routing service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping task routing service: {str(e)}")
            return False
    
    async def _stop_task_routing(self) -> None:
        """Stop task routing."""
        # In a real implementation, this would stop task routing
        logger.info("Stopping task routing")
        
        # Wait for active tasks to complete
        while self.active_tasks:
            await asyncio.sleep(1)
            
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the task routing service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Task routing service is not initialized"}
                
            # Check task routing health
            routing_health = {"status": "healthy", "message": "Task routing is healthy"}
            if self.task_routing_enabled:
                routing_health = await self._health_check_task_routing()
                
            # Determine overall health
            overall_status = routing_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Task routing service is {overall_status}",
                "routing_health": routing_health,
                "task_queue_size": len(self.task_queue),
                "active_tasks_count": len(self.active_tasks),
                "completed_tasks_count": len(self.completed_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error checking task routing service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_task_routing(self) -> Dict[str, Any]:
        """Check task routing health."""
        # In a real implementation, this would check task routing health
        return {"status": "healthy", "message": "Task routing is healthy"}
        
    async def route_task(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a task.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Check if task routing is enabled
            if not self.task_routing_enabled:
                return {"status": "error", "message": "Task routing is disabled"}
                
            # Get task parameters
            task_type = data.get("task_type") if data else None
            task_data = data.get("task_data") if data else {}
            priority = data.get("priority", 5) if data else 5  # Default priority: 5 (medium)
            routing_strategy = data.get("routing_strategy") if data else None
            
            # Validate task type
            if not task_type:
                return {"status": "error", "message": "Task type is required"}
                
            # Validate routing strategy
            if routing_strategy and routing_strategy not in self.routing_strategies:
                return {"status": "error", "message": f"Unsupported routing strategy: {routing_strategy}"}
                
            # Create task
            task_id = str(uuid.uuid4())
            task = {
                "task_id": task_id,
                "task_type": task_type,
                "task_data": task_data,
                "priority": priority,
                "routing_strategy": routing_strategy,
                "status": "queued",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add task to queue
            self.task_queue.append(task)
            
            # Sort queue by priority (higher priority first)
            self.task_queue.sort(key=lambda x: x["priority"], reverse=True)
            
            return {
                "status": "success",
                "message": "Task routed successfully",
                "task_id": task_id,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"Error routing task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def execute_task(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Check if task routing is enabled
            if not self.task_routing_enabled:
                return {"status": "error", "message": "Task routing is disabled"}
                
            # Get task parameters
            task_id = data.get("task_id") if data else None
            task_type = data.get("task_type") if data else None
            task_data = data.get("task_data") if data else {}
            priority = data.get("priority", 5) if data else 5  # Default priority: 5 (medium)
            routing_strategy = data.get("routing_strategy") if data else None
            
            # If task_id is provided, execute the specific task
            if task_id:
                # Check if task is in active tasks
                if task_id in self.active_tasks:
                    return {"status": "error", "message": f"Task {task_id} is already active"}
                    
                # Check if task is in completed tasks
                for task in self.completed_tasks:
                    if task["task_id"] == task_id:
                        return {"status": "error", "message": f"Task {task_id} is already completed"}
                        
                # Check if task is in queue
                for i, task in enumerate(self.task_queue):
                    if task["task_id"] == task_id:
                        # Move task from queue to active tasks
                        task = self.task_queue.pop(i)
                        task["status"] = "active"
                        task["started_at"] = datetime.now().isoformat()
                        self.active_tasks[task_id] = task
                        
                        # Execute task
                        result = await self._execute_task(task, context)
                        
                        # Move task from active to completed
                        task = self.active_tasks.pop(task_id)
                        task["status"] = "completed"
                        task["completed_at"] = datetime.now().isoformat()
                        task["result"] = result
                        self.completed_tasks.append(task)
                        
                        return {
                            "status": "success",
                            "message": "Task executed successfully",
                            "task_id": task_id,
                            "result": result
                        }
                        
                return {"status": "error", "message": f"Task {task_id} not found"}
            else:
                # If task_id is not provided, create and execute a new task
                return await self.route_task(data, context)
                
        except Exception as e:
            logger.error(f"Error executing task: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_task(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task."""
        # In a real implementation, this would execute the task
        logger.info(f"Executing task {task['task_id']} of type {task['task_type']}")
        
        # Simulate task execution
        await asyncio.sleep(1)
        
        # Return task result
        return {
            "status": "success",
            "message": "Task executed successfully",
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "result": f"Result for task {task['task_id']}"
        }
    
    async def _process_tasks(self) -> None:
        """Process tasks from the queue."""
        while self._is_running:
            try:
                # Check if we have capacity for more active tasks
                if len(self.active_tasks) < self.max_active_tasks and self.task_queue:
                    # Get the next task from the queue
                    task = self.task_queue.pop(0)
                    
                    # Move task to active tasks
                    task["status"] = "active"
                    task["started_at"] = datetime.now().isoformat()
                    self.active_tasks[task["task_id"]] = task
                    
                    # Execute task
                    asyncio.create_task(self._execute_task_and_complete(task))
                    
                # Wait a bit before checking again
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing tasks: {str(e)}")
                await asyncio.sleep(1)
    
    async def _execute_task_and_complete(self, task: Dict[str, Any]) -> None:
        """Execute a task and move it to completed tasks."""
        try:
            # Execute task
            result = await self._execute_task(task)
            
            # Move task from active to completed
            task = self.active_tasks.pop(task["task_id"])
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            task["result"] = result
            self.completed_tasks.append(task)
            
        except Exception as e:
            logger.error(f"Error executing task {task['task_id']}: {str(e)}")
            
            # Move task from active to completed with error status
            task = self.active_tasks.pop(task["task_id"])
            task["status"] = "failed"
            task["completed_at"] = datetime.now().isoformat()
            task["error"] = str(e)
            self.completed_tasks.append(task)
    
    async def monitor_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor tasks.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Get monitoring parameters
            task_id = data.get("task_id") if data else None
            status = data.get("status") if data else None
            task_type = data.get("task_type") if data else None
            
            # Filter tasks based on parameters
            filtered_tasks = []
            
            # Check active tasks
            for task_id, task in self.active_tasks.items():
                if task_id == task_id or status == task["status"] or task_type == task["task_type"]:
                    filtered_tasks.append(task)
                    
            # Check completed tasks
            for task in self.completed_tasks:
                if task_id == task["task_id"] or status == task["status"] or task_type == task["task_type"]:
                    filtered_tasks.append(task)
                    
            # Check queued tasks
            for task in self.task_queue:
                if task_id == task["task_id"] or status == task["status"] or task_type == task["task_type"]:
                    filtered_tasks.append(task)
                    
            return {
                "status": "success",
                "message": "Tasks monitored successfully",
                "task_count": len(filtered_tasks),
                "tasks": filtered_tasks
            }
            
        except Exception as e:
            logger.error(f"Error monitoring tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def list_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List tasks.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Get list parameters
            status = data.get("status") if data else None
            task_type = data.get("task_type") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all tasks
            all_tasks = []
            
            # Add queued tasks
            for task in self.task_queue:
                all_tasks.append(task)
                
            # Add active tasks
            for task in self.active_tasks.values():
                all_tasks.append(task)
                
            # Add completed tasks
            for task in self.completed_tasks:
                all_tasks.append(task)
                
            # Filter tasks based on parameters
            filtered_tasks = []
            for task in all_tasks:
                if status and task["status"] != status:
                    continue
                if task_type and task["task_type"] != task_type:
                    continue
                filtered_tasks.append(task)
                
            # Sort tasks by creation time (newest first)
            filtered_tasks.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_tasks = filtered_tasks[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Tasks listed successfully",
                "total_count": len(filtered_tasks),
                "limit": limit,
                "offset": offset,
                "tasks": paginated_tasks
            }
            
        except Exception as e:
            logger.error(f"Error listing tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def search_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search tasks.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Get search parameters
            query = data.get("query") if data else None
            task_type = data.get("task_type") if data else None
            status = data.get("status") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            if not query:
                return {"status": "error", "message": "Query is required for search"}
                
            # Get all tasks
            all_tasks = []
            
            # Add queued tasks
            for task in self.task_queue:
                all_tasks.append(task)
                
            # Add active tasks
            for task in self.active_tasks.values():
                all_tasks.append(task)
                
            # Add completed tasks
            for task in self.completed_tasks:
                all_tasks.append(task)
                
            # Search tasks based on query
            matched_tasks = []
            for task in all_tasks:
                # Check if task matches query
                task_json = json.dumps(task, default=str)
                if query.lower() in task_json.lower():
                    # Check additional filters
                    if task_type and task["task_type"] != task_type:
                        continue
                    if status and task["status"] != status:
                        continue
                    if start_time and task["created_at"] < start_time:
                        continue
                    if end_time and task["created_at"] > end_time:
                        continue
                    matched_tasks.append(task)
                    
            # Sort tasks by creation time (newest first)
            matched_tasks.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_tasks = matched_tasks[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Tasks searched successfully",
                "query": query,
                "total_count": len(matched_tasks),
                "limit": limit,
                "offset": offset,
                "tasks": paginated_tasks
            }
            
        except Exception as e:
            logger.error(f"Error searching tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_tasks(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze tasks.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Get analysis parameters
            analysis_type = data.get("analysis_type", "summary") if data else "summary"
            task_type = data.get("task_type") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            
            # Get all tasks
            all_tasks = []
            
            # Add queued tasks
            for task in self.task_queue:
                all_tasks.append(task)
                
            # Add active tasks
            for task in self.active_tasks.values():
                all_tasks.append(task)
                
            # Add completed tasks
            for task in self.completed_tasks:
                all_tasks.append(task)
                
            # Filter tasks based on parameters
            filtered_tasks = []
            for task in all_tasks:
                if task_type and task["task_type"] != task_type:
                    continue
                if start_time and task["created_at"] < start_time:
                    continue
                if end_time and task["created_at"] > end_time:
                    continue
                filtered_tasks.append(task)
                
            # Analyze based on analysis type
            if analysis_type == "summary":
                analysis = await self._analyze_tasks_summary(filtered_tasks)
            elif analysis_type == "performance":
                analysis = await self._analyze_tasks_performance(filtered_tasks)
            elif analysis_type == "types":
                analysis = await self._analyze_tasks_types(filtered_tasks)
            elif analysis_type == "status":
                analysis = await self._analyze_tasks_status(filtered_tasks)
            else:
                return {"status": "error", "message": f"Unsupported analysis type: {analysis_type}"}
                
            return {
                "status": "success",
                "message": "Tasks analyzed successfully",
                "analysis_type": analysis_type,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing tasks: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _analyze_tasks_summary(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tasks for summary statistics."""
        # Count by status
        status_counts = {}
        for task in tasks:
            status = task["status"]
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1
                
        # Count by task type
        type_counts = {}
        for task in tasks:
            task_type = task["task_type"]
            if task_type not in type_counts:
                type_counts[task_type] = 0
            type_counts[task_type] += 1
                
        # Calculate average execution time for completed tasks
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        total_execution_time = 0
        for task in completed_tasks:
            if "started_at" in task and "completed_at" in task:
                start_time = datetime.fromisoformat(task["started_at"])
                end_time = datetime.fromisoformat(task["completed_at"])
                execution_time = (end_time - start_time).total_seconds()
                total_execution_time += execution_time
                
        average_execution_time = total_execution_time / len(completed_tasks) if completed_tasks else 0
        
        return {
            "analysis_type": "summary",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "status_counts": status_counts,
            "type_counts": type_counts,
            "average_execution_time": average_execution_time
        }
    
    async def _analyze_tasks_performance(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tasks for performance metrics."""
        # Get completed tasks
        completed_tasks = [t for t in tasks if t["status"] == "completed"]
        
        # Calculate execution times
        execution_times = []
        for task in completed_tasks:
            if "started_at" in task and "completed_at" in task:
                start_time = datetime.fromisoformat(task["started_at"])
                end_time = datetime.fromisoformat(task["completed_at"])
                execution_time = (end_time - start_time).total_seconds()
                execution_times.append(execution_time)
                
        # Calculate statistics
        if execution_times:
            min_execution_time = min(execution_times)
            max_execution_time = max(execution_times)
            avg_execution_time = sum(execution_times) / len(execution_times)
            
            # Sort for median calculation
            execution_times.sort()
            median_execution_time = execution_times[len(execution_times) // 2]
        else:
            min_execution_time = 0
            max_execution_time = 0
            avg_execution_time = 0
            median_execution_time = 0
            
        return {
            "analysis_type": "performance",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "min_execution_time": min_execution_time,
            "max_execution_time": max_execution_time,
            "avg_execution_time": avg_execution_time,
            "median_execution_time": median_execution_time
        }
    
    async def _analyze_tasks_types(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tasks by type."""
        # Group by task type
        type_tasks = {}
        for task in tasks:
            task_type = task["task_type"]
            if task_type not in type_tasks:
                type_tasks[task_type] = []
            type_tasks[task_type].append(task)
                
        # Calculate statistics for each type
        type_stats = {}
        for task_type, t_tasks in type_tasks.items():
            # Count by status
            status_counts = {}
            for task in t_tasks:
                status = task["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                    
            # Calculate average execution time for completed tasks
            completed_tasks = [t for t in t_tasks if t["status"] == "completed"]
            total_execution_time = 0
            for task in completed_tasks:
                if "started_at" in task and "completed_at" in task:
                    start_time = datetime.fromisoformat(task["started_at"])
                    end_time = datetime.fromisoformat(task["completed_at"])
                    execution_time = (end_time - start_time).total_seconds()
                    total_execution_time += execution_time
                    
            average_execution_time = total_execution_time / len(completed_tasks) if completed_tasks else 0
            
            type_stats[task_type] = {
                "total_tasks": len(t_tasks),
                "status_counts": status_counts,
                "average_execution_time": average_execution_time
            }
                
        return {
            "analysis_type": "types",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "type_stats": type_stats
        }
    
    async def _analyze_tasks_status(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tasks by status."""
        # Group by status
        status_tasks = {}
        for task in tasks:
            status = task["status"]
            if status not in status_tasks:
                status_tasks[status] = []
            status_tasks[status].append(task)
                
        # Calculate statistics for each status
        status_stats = {}
        for status, s_tasks in status_tasks.items():
            # Count by task type
            type_counts = {}
            for task in s_tasks:
                task_type = task["task_type"]
                if task_type not in type_counts:
                    type_counts[task_type] = 0
                type_counts[task_type] += 1
                    
            # Calculate average execution time for completed tasks
            if status == "completed":
                total_execution_time = 0
                for task in s_tasks:
                    if "started_at" in task and "completed_at" in task:
                        start_time = datetime.fromisoformat(task["started_at"])
                        end_time = datetime.fromisoformat(task["completed_at"])
                        execution_time = (end_time - start_time).total_seconds()
                        total_execution_time += execution_time
                        
                average_execution_time = total_execution_time / len(s_tasks) if s_tasks else 0
            else:
                average_execution_time = 0
                
            status_stats[status] = {
                "total_tasks": len(s_tasks),
                "type_counts": type_counts,
                "average_execution_time": average_execution_time
            }
                
        return {
            "analysis_type": "status",
            "generated_at": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "status_stats": status_stats
        }
        
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the task routing service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            status = {
                "task_routing_enabled": self.task_routing_enabled,
                "routing_strategies": self.routing_strategies,
                "is_running": self._is_running,
                "task_queue_size": len(self.task_queue),
                "active_tasks_count": len(self.active_tasks),
                "completed_tasks_count": len(self.completed_tasks),
                "max_active_tasks": self.max_active_tasks,
                "task_timeout": self.task_timeout
            }
            
            return {
                "status": "success",
                "message": "Task routing status retrieved successfully",
                "task_routing_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting task routing status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the task routing service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Task routing service is not initialized"}
                
            # Get all tasks
            all_tasks = []
            
            # Add queued tasks
            for task in self.task_queue:
                all_tasks.append(task)
                
            # Add active tasks
            for task in self.active_tasks.values():
                all_tasks.append(task)
                
            # Add completed tasks
            for task in self.completed_tasks:
                all_tasks.append(task)
                
            # Count by status
            status_counts = {}
            for task in all_tasks:
                status = task["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Count by task type
            type_counts = {}
            for task in all_tasks:
                task_type = task["task_type"]
                if task_type not in type_counts:
                    type_counts[task_type] = 0
                type_counts[task_type] += 1
                
            # Calculate average execution time for completed tasks
            completed_tasks = [t for t in all_tasks if t["status"] == "completed"]
            total_execution_time = 0
            for task in completed_tasks:
                if "started_at" in task and "completed_at" in task:
                    start_time = datetime.fromisoformat(task["started_at"])
                    end_time = datetime.fromisoformat(task["completed_at"])
                    execution_time = (end_time - start_time).total_seconds()
                    total_execution_time += execution_time
                    
            average_execution_time = total_execution_time / len(completed_tasks) if completed_tasks else 0
            
            stats = {
                "task_routing_enabled": self.task_routing_enabled,
                "routing_strategies": self.routing_strategies,
                "is_running": self._is_running,
                "total_tasks": len(all_tasks),
                "task_queue_size": len(self.task_queue),
                "active_tasks_count": len(self.active_tasks),
                "completed_tasks_count": len(self.completed_tasks),
                "max_active_tasks": self.max_active_tasks,
                "task_timeout": self.task_timeout,
                "status_counts": status_counts,
                "type_counts": type_counts,
                "average_execution_time": average_execution_time
            }
            
            return {
                "status": "success",
                "message": "Task routing statistics retrieved successfully",
                "task_routing_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting task routing statistics: {str(e)}")
            return {"status": "error", "message": str(e)}