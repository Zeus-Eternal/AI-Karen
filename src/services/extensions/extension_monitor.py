"""
Extension Monitor Service

This service monitors the health and performance of extensions in the AI Karen system,
providing metrics and alerts for extension issues.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus


class ExtensionMonitor(BaseService):
    """
    Extension Monitor service for monitoring extension health and performance.
    
    This service provides capabilities for monitoring the health and performance
    of extensions, collecting metrics, and generating alerts for issues.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_monitor"))
        self._initialized = False
        self._extension_metrics: Dict[str, Dict[str, Any]] = {}
        self._extension_health: Dict[str, str] = {}  # extension_id -> health_status
        self._extension_alerts: List[Dict[str, Any]] = []
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize the Extension Monitor service."""
        try:
            self.logger.info("Initializing Extension Monitor service")
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Monitor service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Monitor service: {e}")
            self._status = ServiceStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the Extension Monitor service."""
        try:
            self.logger.info("Shutting down Extension Monitor service")
            
            # Stop all monitoring tasks
            async with self._lock:
                for task in self._monitoring_tasks.values():
                    task.cancel()
                
                self._monitoring_tasks.clear()
                self._extension_metrics.clear()
                self._extension_health.clear()
                self._extension_alerts.clear()
            
            self._initialized = False
            self._status = ServiceStatus.STOPPED
            self.logger.info("Extension Monitor service shutdown successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Extension Monitor service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check the health of the Extension Monitor service."""
        return self._initialized and self._status == ServiceStatus.RUNNING
    
    async def register_extension(self, extension_id: str) -> bool:
        """
        Register an extension for monitoring.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was registered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_metrics:
                self.logger.warning(f"Extension {extension_id} is already registered for monitoring")
                return True
            
            # Initialize metrics for the extension
            self._extension_metrics[extension_id] = {
                "execution_count": 0,
                "execution_success_count": 0,
                "execution_error_count": 0,
                "average_execution_time": 0.0,
                "last_execution_time": None,
                "last_execution_status": None,
                "total_execution_time": 0.0
            }
            
            self._extension_health[extension_id] = "healthy"
            
            # Start monitoring task for the extension
            self._monitoring_tasks[extension_id] = asyncio.create_task(
                self._monitor_extension(extension_id)
            )
        
        self.logger.info(f"Extension {extension_id} registered for monitoring")
        return True
    
    async def unregister_extension(self, extension_id: str) -> bool:
        """
        Unregister an extension from monitoring.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            True if the extension was unregistered successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_metrics:
                self.logger.warning(f"Extension {extension_id} is not registered for monitoring")
                return False
            
            # Stop monitoring task for the extension
            if extension_id in self._monitoring_tasks:
                self._monitoring_tasks[extension_id].cancel()
                del self._monitoring_tasks[extension_id]
            
            # Remove extension metrics and health status
            del self._extension_metrics[extension_id]
            del self._extension_health[extension_id]
        
        self.logger.info(f"Extension {extension_id} unregistered from monitoring")
        return True
    
    async def record_execution(
        self,
        extension_id: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Record an execution for an extension.
        
        Args:
            extension_id: The ID of the extension
            execution_time: The execution time in seconds
            success: Whether the execution was successful
            error_message: Optional error message if the execution failed
            
        Returns:
            True if the execution was recorded successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id not in self._extension_metrics:
                self.logger.warning(f"Extension {extension_id} is not registered for monitoring")
                return False
            
            metrics = self._extension_metrics[extension_id]
            
            # Update metrics
            metrics["execution_count"] += 1
            metrics["total_execution_time"] += execution_time
            
            if success:
                metrics["execution_success_count"] += 1
                metrics["last_execution_status"] = "success"
            else:
                metrics["execution_error_count"] += 1
                metrics["last_execution_status"] = "error"
                
                # Create alert for error
                await self._create_alert(
                    extension_id,
                    "execution_error",
                    f"Extension execution failed: {error_message or 'Unknown error'}"
                )
            
            # Update average execution time
            metrics["average_execution_time"] = (
                metrics["total_execution_time"] / metrics["execution_count"]
            )
            
            metrics["last_execution_time"] = asyncio.get_event_loop().time()
            
            # Update health status based on error rate
            error_rate = metrics["execution_error_count"] / metrics["execution_count"]
            if error_rate > 0.5:
                self._extension_health[extension_id] = "critical"
            elif error_rate > 0.2:
                self._extension_health[extension_id] = "warning"
            else:
                self._extension_health[extension_id] = "healthy"
        
        return True
    
    async def get_extension_metrics(self, extension_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the metrics for an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The extension metrics or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id in self._extension_metrics:
                return self._extension_metrics[extension_id].copy()
            else:
                return None
    
    async def get_extension_health(self, extension_id: str) -> Optional[str]:
        """
        Get the health status of an extension.
        
        Args:
            extension_id: The ID of the extension
            
        Returns:
            The health status of the extension or None if not found
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            return self._extension_health.get(extension_id)
    
    async def get_all_extension_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the metrics for all extensions.
        
        Returns:
            Dictionary mapping extension IDs to extension metrics
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            result = {}
            for ext_id, metrics in self._extension_metrics.items():
                result[ext_id] = metrics.copy()
            return result
    
    async def get_all_extension_health(self) -> Dict[str, str]:
        """
        Get the health status of all extensions.
        
        Returns:
            Dictionary mapping extension IDs to health status
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            return self._extension_health.copy()
    
    async def get_extension_alerts(self, extension_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get alerts for extensions.
        
        Args:
            extension_id: Optional extension ID to filter alerts for
            
        Returns:
            List of extension alerts
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id is None:
                return self._extension_alerts.copy()
            else:
                return [
                    alert for alert in self._extension_alerts
                    if alert.get("extension_id") == extension_id
                ]
    
    async def clear_extension_alerts(self, extension_id: Optional[str] = None) -> bool:
        """
        Clear alerts for extensions.
        
        Args:
            extension_id: Optional extension ID to clear alerts for
            
        Returns:
            True if the alerts were cleared successfully, False otherwise
        """
        if not self._initialized:
            raise RuntimeError("Extension Monitor service is not initialized")
        
        async with self._lock:
            if extension_id is None:
                self._extension_alerts.clear()
            else:
                self._extension_alerts = [
                    alert for alert in self._extension_alerts
                    if alert.get("extension_id") != extension_id
                ]
        
        return True
    
    async def _start_monitoring_tasks(self) -> None:
        """Start monitoring tasks for all registered extensions."""
        # This is a placeholder for starting monitoring tasks
        # In a real implementation, this would start tasks for all registered extensions
        pass
    
    async def _monitor_extension(self, extension_id: str) -> None:
        """
        Monitor an extension.
        
        Args:
            extension_id: The ID of the extension to monitor
        """
        try:
            while True:
                # Check extension health
                await self._check_extension_health(extension_id)
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
        except Exception as e:
            self.logger.error(f"Error monitoring extension {extension_id}: {e}")
    
    async def _check_extension_health(self, extension_id: str) -> None:
        """
        Check the health of an extension.
        
        Args:
            extension_id: The ID of the extension to check
        """
        # This is a placeholder for extension health checking
        # In a real implementation, this would perform actual health checks
        
        async with self._lock:
            if extension_id not in self._extension_metrics:
                return
            
            metrics = self._extension_metrics[extension_id]
            
            # Check if extension has been inactive for too long
            if metrics["last_execution_time"] is not None:
                current_time = asyncio.get_event_loop().time()
                inactive_time = current_time - metrics["last_execution_time"]
                
                if inactive_time > 300:  # 5 minutes
                    await self._create_alert(
                        extension_id,
                        "inactivity",
                        f"Extension has been inactive for {inactive_time:.1f} seconds"
                    )
    
    async def _create_alert(
        self,
        extension_id: str,
        alert_type: str,
        message: str
    ) -> None:
        """
        Create an alert for an extension.
        
        Args:
            extension_id: The ID of the extension
            alert_type: The type of the alert
            message: The alert message
        """
        alert = {
            "extension_id": extension_id,
            "type": alert_type,
            "message": message,
            "timestamp": asyncio.get_event_loop().time(),
            "resolved": False
        }
        
        self._extension_alerts.append(alert)
        self.logger.warning(f"Extension alert created: {alert}")