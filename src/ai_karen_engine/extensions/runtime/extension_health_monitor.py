"""
Extension Health Monitor service for monitoring extension health and performance.

This service provides capabilities for monitoring the health and performance
of extensions, collecting metrics, and generating alerts for issues.
"""

from typing import Dict, List, Any, Optional, Set
import asyncio
import logging
import time
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionHealthMonitor(BaseService):
    """
    Extension Health Monitor service for monitoring extension health and performance.
    
    This service provides capabilities for monitoring the health and performance
    of extensions, collecting metrics, and generating alerts for issues.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_health_monitor"))
        self._initialized = False
        self._extension_metrics: Dict[str, Dict[str, Any]] = {}
        self._extension_health: Dict[str, str] = {}  # extension_id -> health_status
        self._extension_alerts: List[Dict[str, Any]] = []
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Health Monitor service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Health Monitor service")
            
            # Initialize health status for all extensions
            self._extension_health = {}
            self._extension_metrics = {}
            self._extension_alerts = []
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Health Monitor service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Health Monitor service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def start_monitoring(self, extension_id: str, check_interval: int = 30) -> None:
        """Start monitoring an extension."""
        if extension_id in self._monitoring_tasks:
            self.logger.warning(f"Extension {extension_id} is already being monitored")
            return
            
        async def monitor_extension():
            while True:
                try:
                    # Check extension health
                    health_status = await self._check_extension_health(extension_id)
                    
                    # Update health status
                    async with self._lock:
                        self._extension_health[extension_id] = health_status
                        
                    # Check if health status has changed
                    if health_status != "healthy" and health_status != "unknown":
                        await self._generate_alert(extension_id, health_status)
                        
                except Exception as e:
                    self.logger.error(f"Error monitoring extension {extension_id}: {str(e)}")
                    async with self._lock:
                        self._extension_health[extension_id] = "error"
                    await self._generate_alert(extension_id, "error")
                    
                await asyncio.sleep(check_interval)
                
        # Start monitoring task
        task = asyncio.create_task(monitor_extension())
        self._monitoring_tasks[extension_id] = task
        self.logger.info(f"Started monitoring extension {extension_id}")
        
    async def stop_monitoring(self, extension_id: str) -> None:
        """Stop monitoring an extension."""
        if extension_id not in self._monitoring_tasks:
            self.logger.warning(f"Extension {extension_id} is not being monitored")
            return
            
        # Cancel monitoring task
        task = self._monitoring_tasks[extension_id]
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Remove from monitoring tasks
        del self._monitoring_tasks[extension_id]
        self.logger.info(f"Stopped monitoring extension {extension_id}")
        
    async def get_extension_health(self, extension_id: str) -> str:
        """Get the health status of an extension."""
        async with self._lock:
            return self._extension_health.get(extension_id, "unknown")
            
    async def get_all_extension_health(self) -> Dict[str, str]:
        """Get the health status of all extensions."""
        async with self._lock:
            return self._extension_health.copy()
            
    async def get_extension_metrics(self, extension_id: str) -> Dict[str, Any]:
        """Get the metrics for an extension."""
        async with self._lock:
            return self._extension_metrics.get(extension_id, {})
            
    async def get_extension_alerts(self, extension_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts for an extension or all extensions."""
        async with self._lock:
            if extension_id:
                return [alert for alert in self._extension_alerts if alert.get("extension_id") == extension_id]
            return self._extension_alerts.copy()
            
    async def _check_extension_health(self, extension_id: str) -> str:
        """Check the health of an extension."""
        # This is a placeholder implementation
        # In a real implementation, this would make HTTP requests or use other
        # mechanisms to check the health of the extension
        
        # For now, we'll just return "healthy" for all extensions
        return "healthy"
        
    async def _generate_alert(self, extension_id: str, health_status: str) -> None:
        """Generate an alert for an extension."""
        alert = {
            "extension_id": extension_id,
            "health_status": health_status,
            "timestamp": datetime.now().isoformat(),
            "message": f"Extension {extension_id} health status: {health_status}"
        }
        
        async with self._lock:
            self._extension_alerts.append(alert)
            
        self.logger.warning(f"Generated alert for extension {extension_id}: {health_status}")
        
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        # Check if monitoring tasks are running
        if self._monitoring_tasks:
            for extension_id, task in self._monitoring_tasks.items():
                if task.done():
                    status = ServiceStatus.ERROR
                    break
                    
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "monitored_extensions": len(self._monitoring_tasks),
                "total_alerts": len(self._extension_alerts)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Health Monitor service")
        
        # Cancel all monitoring tasks
        for extension_id, task in self._monitoring_tasks.items():
            task.cancel()
            
        # Wait for all tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
            
        self._monitoring_tasks.clear()
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Health Monitor service shutdown complete")