"""
Background Task Extension Example

This extension demonstrates how to implement background tasks in the Kari AI
extension system, including scheduled tasks, event-driven tasks, and manual execution.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter

from src.extensions.base import BaseExtension


logger = logging.getLogger(__name__)


class BackgroundTaskExtension(BaseExtension):
    """
    Example extension demonstrating background task capabilities.
    
    This extension shows how to:
    - Define scheduled background tasks
    - Handle manual task execution
    - Respond to events
    - Provide task status via API
    """
    
    def __init__(self, manifest, context):
        """Initialize the background task extension."""
        super().__init__(manifest, context)
        
        # Extension state
        self.task_execution_count = 0
        self.last_cleanup_time = None
        self.last_report_time = None
        self.last_health_check_time = None
        self.health_status = "unknown"
        
        # Task results storage
        self.task_results = {}
    
    async def _initialize(self) -> None:
        """Initialize the extension."""
        logger.info("Initializing Background Task Extension")
        
        # Initialize extension state
        self.task_execution_count = 0
        self.health_status = "healthy"
        
        logger.info("Background Task Extension initialized successfully")
    
    async def _shutdown(self) -> None:
        """Shutdown the extension."""
        logger.info("Shutting down Background Task Extension")
        
        # Clean up any resources
        self.task_results.clear()
        
        logger.info("Background Task Extension shut down successfully")
    
    def create_api_router(self) -> Optional[APIRouter]:
        """Create API router for the extension."""
        router = APIRouter()
        
        @router.get("/status")
        async def get_extension_status():
            """Get extension status and task information."""
            return {
                "extension": self.manifest.name,
                "version": self.manifest.version,
                "status": "active",
                "task_execution_count": self.task_execution_count,
                "last_cleanup_time": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
                "last_report_time": self.last_report_time.isoformat() if self.last_report_time else None,
                "last_health_check_time": self.last_health_check_time.isoformat() if self.last_health_check_time else None,
                "health_status": self.health_status,
                "recent_task_results": list(self.task_results.values())[-10:]  # Last 10 results
            }
        
        @router.get("/tasks")
        async def list_available_tasks():
            """List all available background tasks."""
            return {
                "tasks": [
                    {
                        "name": "hourly_cleanup",
                        "description": "Cleanup task that runs every hour",
                        "schedule": "0 * * * *",
                        "last_execution": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None
                    },
                    {
                        "name": "daily_report",
                        "description": "Generate daily report at 9 AM",
                        "schedule": "0 9 * * *",
                        "last_execution": self.last_report_time.isoformat() if self.last_report_time else None
                    },
                    {
                        "name": "system_health_check",
                        "description": "Check system health every 5 minutes",
                        "schedule": "*/5 * * * *",
                        "last_execution": self.last_health_check_time.isoformat() if self.last_health_check_time else None
                    },
                    {
                        "name": "manual_task",
                        "description": "Task that can only be executed manually",
                        "schedule": None,
                        "last_execution": None
                    }
                ]
            }
        
        @router.post("/tasks/{task_name}/execute")
        async def execute_task_manually(task_name: str, parameters: Dict[str, Any] = None):
            """Execute a task manually."""
            if parameters is None:
                parameters = {}
            
            # This would typically be handled by the background task manager
            # For demonstration, we'll call the task function directly
            try:
                if task_name == "hourly_cleanup":
                    result = await self.hourly_cleanup_task(
                        execution_id="manual",
                        task_name=task_name,
                        extension_name=self.manifest.name,
                        **parameters
                    )
                elif task_name == "daily_report":
                    result = await self.daily_report_task(
                        execution_id="manual",
                        task_name=task_name,
                        extension_name=self.manifest.name,
                        **parameters
                    )
                elif task_name == "system_health_check":
                    result = await self.system_health_check_task(
                        execution_id="manual",
                        task_name=task_name,
                        extension_name=self.manifest.name,
                        **parameters
                    )
                elif task_name == "manual_task":
                    result = await self.manual_task(
                        execution_id="manual",
                        task_name=task_name,
                        extension_name=self.manifest.name,
                        **parameters
                    )
                else:
                    return {"error": f"Unknown task: {task_name}"}
                
                return {
                    "task_name": task_name,
                    "execution_id": "manual",
                    "status": "completed",
                    "result": result,
                    "executed_at": datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error executing task {task_name}: {e}")
                return {
                    "task_name": task_name,
                    "execution_id": "manual",
                    "status": "failed",
                    "error": str(e),
                    "executed_at": datetime.now(timezone.utc).isoformat()
                }
        
        return router
    
    # Background Task Functions
    
    async def hourly_cleanup_task(
        self, 
        execution_id: str, 
        task_name: str, 
        extension_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Hourly cleanup task.
        
        This task runs every hour to perform maintenance operations.
        """
        logger.info(f"Starting hourly cleanup task (execution: {execution_id})")
        
        try:
            # Simulate cleanup operations
            await asyncio.sleep(1)  # Simulate work
            
            # Update state
            self.last_cleanup_time = datetime.now(timezone.utc)
            self.task_execution_count += 1
            
            # Perform cleanup operations
            cleaned_items = 0
            
            # Clean up old task results (keep only last 100)
            if len(self.task_results) > 100:
                old_keys = list(self.task_results.keys())[:-100]
                for key in old_keys:
                    del self.task_results[key]
                    cleaned_items += 1
            
            result = {
                "task": "hourly_cleanup",
                "execution_id": execution_id,
                "cleaned_items": cleaned_items,
                "execution_time": self.last_cleanup_time.isoformat(),
                "status": "success"
            }
            
            # Store result
            self.task_results[execution_id] = result
            
            logger.info(f"Hourly cleanup task completed (execution: {execution_id})")
            return result
            
        except Exception as e:
            logger.error(f"Hourly cleanup task failed (execution: {execution_id}): {e}")
            raise
    
    async def daily_report_task(
        self, 
        execution_id: str, 
        task_name: str, 
        extension_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Daily report generation task.
        
        This task runs daily at 9 AM to generate reports.
        """
        logger.info(f"Starting daily report task (execution: {execution_id})")
        
        try:
            # Simulate report generation
            await asyncio.sleep(2)  # Simulate work
            
            # Update state
            self.last_report_time = datetime.now(timezone.utc)
            self.task_execution_count += 1
            
            # Generate report data
            report_data = {
                "date": self.last_report_time.date().isoformat(),
                "total_task_executions": self.task_execution_count,
                "extension_status": self.health_status,
                "last_cleanup": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
                "last_health_check": self.last_health_check_time.isoformat() if self.last_health_check_time else None,
                "active_task_results": len(self.task_results)
            }
            
            result = {
                "task": "daily_report",
                "execution_id": execution_id,
                "report_data": report_data,
                "execution_time": self.last_report_time.isoformat(),
                "status": "success"
            }
            
            # Store result
            self.task_results[execution_id] = result
            
            logger.info(f"Daily report task completed (execution: {execution_id})")
            return result
            
        except Exception as e:
            logger.error(f"Daily report task failed (execution: {execution_id}): {e}")
            raise
    
    async def system_health_check_task(
        self, 
        execution_id: str, 
        task_name: str, 
        extension_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        System health check task.
        
        This task runs every 5 minutes to check system health.
        """
        logger.info(f"Starting system health check task (execution: {execution_id})")
        
        try:
            # Simulate health checks
            await asyncio.sleep(0.5)  # Simulate work
            
            # Update state
            self.last_health_check_time = datetime.now(timezone.utc)
            self.task_execution_count += 1
            
            # Perform health checks
            health_checks = {
                "extension_status": "healthy",
                "memory_usage": "normal",
                "task_queue": "normal",
                "api_endpoints": "responsive"
            }
            
            # Determine overall health
            all_healthy = all(status in ["healthy", "normal", "responsive"] for status in health_checks.values())
            self.health_status = "healthy" if all_healthy else "degraded"
            
            result = {
                "task": "system_health_check",
                "execution_id": execution_id,
                "health_checks": health_checks,
                "overall_status": self.health_status,
                "execution_time": self.last_health_check_time.isoformat(),
                "status": "success"
            }
            
            # Store result
            self.task_results[execution_id] = result
            
            logger.info(f"System health check task completed (execution: {execution_id})")
            return result
            
        except Exception as e:
            logger.error(f"System health check task failed (execution: {execution_id}): {e}")
            self.health_status = "error"
            raise
    
    async def manual_task(
        self, 
        execution_id: str, 
        task_name: str, 
        extension_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Manual task that can only be executed on demand.
        
        This demonstrates tasks that are not scheduled but can be triggered manually.
        """
        logger.info(f"Starting manual task (execution: {execution_id})")
        
        try:
            # Get parameters from kwargs
            message = kwargs.get("message", "Hello from manual task!")
            delay = kwargs.get("delay", 1)
            
            # Simulate work
            await asyncio.sleep(delay)
            
            # Update state
            self.task_execution_count += 1
            
            result = {
                "task": "manual_task",
                "execution_id": execution_id,
                "message": message,
                "delay": delay,
                "execution_time": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            
            # Store result
            self.task_results[execution_id] = result
            
            logger.info(f"Manual task completed (execution: {execution_id})")
            return result
            
        except Exception as e:
            logger.error(f"Manual task failed (execution: {execution_id}): {e}")
            raise
    
    # Event Handlers
    
    async def handle_extension_loaded_event(
        self, 
        execution_id: str, 
        task_name: str, 
        extension_name: str,
        event_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle extension loaded events.
        
        This demonstrates event-driven task execution.
        """
        logger.info(f"Handling extension loaded event (execution: {execution_id})")
        
        try:
            loaded_extension = event_data.get("extension_name", "unknown") if event_data else "unknown"
            
            result = {
                "task": "handle_extension_loaded_event",
                "execution_id": execution_id,
                "loaded_extension": loaded_extension,
                "handled_at": datetime.now(timezone.utc).isoformat(),
                "status": "success"
            }
            
            # Store result
            self.task_results[execution_id] = result
            
            logger.info(f"Extension loaded event handled (execution: {execution_id})")
            return result
            
        except Exception as e:
            logger.error(f"Extension loaded event handler failed (execution: {execution_id}): {e}")
            raise
    
    # Override health check to include task-specific information
    async def health_check(self) -> Dict[str, Any]:
        """Extension health check with task information."""
        base_health = await super().health_check()
        
        # Add task-specific health information
        base_health.update({
            "task_execution_count": self.task_execution_count,
            "last_cleanup": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
            "last_report": self.last_report_time.isoformat() if self.last_report_time else None,
            "last_health_check": self.last_health_check_time.isoformat() if self.last_health_check_time else None,
            "health_status": self.health_status,
            "stored_results": len(self.task_results)
        })
        
        return base_health