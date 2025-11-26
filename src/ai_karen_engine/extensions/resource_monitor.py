"""
Resource monitor for the legacy extension system.

This module provides backward compatibility with the old resource monitor
while migrating to the new two-tier architecture.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import ExtensionRecord


class HealthStatus(Enum):
    """
    Enumeration for health status values.
    """
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class ResourceUsage:
    """
    Data class for resource usage information.
    """
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    disk_mb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    uptime_seconds: float = 0.0


class ResourceMonitor:
    """
    Monitor for extension resources in the legacy system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("extension.resource_monitor")
        self._usage_data: Dict[str, ResourceUsage] = {}
        self._start_times: Dict[str, float] = {}
    
    def register_extension(self, record: ExtensionRecord) -> None:
        """
        Register an extension for monitoring.
        
        Args:
            record: Extension record to monitor
        """
        name = record.manifest.name
        self._usage_data[name] = ResourceUsage()
        self._start_times[name] = time.time()
        self.logger.debug("Registered extension for monitoring: %s", name)
    
    def unregister_extension(self, name: str) -> None:
        """
        Unregister an extension from monitoring.
        
        Args:
            name: Extension name to unregister
        """
        if name in self._usage_data:
            del self._usage_data[name]
            self.logger.debug("Unregistered extension from monitoring: %s", name)
        
        if name in self._start_times:
            del self._start_times[name]
    
    def get_extension_usage(self, name: str) -> Optional[ResourceUsage]:
        """
        Get resource usage for an extension.
        
        Args:
            name: Extension name
            
        Returns:
            Resource usage data or None if not found
        """
        if name not in self._usage_data:
            return None
            
        usage = self._usage_data[name]
        
        # Update uptime
        if name in self._start_times:
            usage.uptime_seconds = time.time() - self._start_times[name]
        
        # For now, return placeholder values
        # This can be enhanced later to actually monitor resources
        return usage
    
    def get_all_usage(self) -> Dict[str, ResourceUsage]:
        """
        Get resource usage for all monitored extensions.
        
        Returns:
            Dictionary mapping extension names to resource usage data
        """
        result = {}
        for name in self._usage_data:
            usage = self.get_extension_usage(name)
            if usage:
                result[name] = usage
        return result


class ExtensionHealthChecker:
    """
    Health checker for extensions in the legacy system.
    """
    
    def __init__(self, resource_monitor: ResourceMonitor):
        self.resource_monitor = resource_monitor
        self.logger = logging.getLogger("extension.health_checker")
    
    async def check_extension_health(self, record: ExtensionRecord) -> HealthStatus:
        """
        Check the health of an extension.
        
        Args:
            record: Extension record to check
            
        Returns:
            Health status
        """
        name = record.manifest.name
        usage = self.resource_monitor.get_extension_usage(name)
        
        if not usage:
            return HealthStatus.RED
        
        # For now, return GREEN for all extensions
        # This can be enhanced later to actually check health
        return HealthStatus.GREEN
    
    async def check_all_extensions_health(
        self, 
        records: Dict[str, ExtensionRecord]
    ) -> Dict[str, HealthStatus]:
        """
        Check the health of all extensions.
        
        Args:
            records: Dictionary of extension records
            
        Returns:
            Dictionary mapping extension names to health status
        """
        result = {}
        for name, record in records.items():
            try:
                result[name] = await self.check_extension_health(record)
            except Exception as e:
                self.logger.error("Failed to check health for %s: %s", name, e)
                result[name] = HealthStatus.RED
        return result
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get a summary of extension health.
        
        Returns:
            Dictionary with health summary
        """
        # For now, return a placeholder summary
        # This can be enhanced later to actually summarize health
        return {
            "total_extensions": len(self.resource_monitor._usage_data),
            "healthy_extensions": len(self.resource_monitor._usage_data),
            "unhealthy_extensions": 0,
            "overall_health": HealthStatus.GREEN.value
        }
    
    async def start_monitoring(self) -> None:
        """
        Start monitoring extension resources.
        """
        self.logger.info("Started extension resource monitoring")
    
    async def stop_monitoring(self) -> None:
        """
        Stop monitoring extension resources.
        """
        self.logger.info("Stopped extension resource monitoring")