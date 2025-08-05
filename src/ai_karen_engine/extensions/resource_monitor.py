"""
Extension resource monitoring and management.
"""

from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

# Optional psutil import for resource monitoring
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from ai_karen_engine.extensions.models import ExtensionRecord, ExtensionStatus
from ai_karen_engine.hooks.hook_types import HookTypes


class HealthStatus(Enum):
    """Health status with color-coded states."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class ResourceUsage:
    """Resource usage statistics for an extension."""

    memory_mb: float
    cpu_percent: float
    disk_mb: float
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    uptime_seconds: float = 0
    
    # Hook monitoring metrics
    hooks_registered: int = 0
    hooks_executed: int = 0
    hooks_failed: int = 0
    hook_execution_time_ms: float = 0.0
    last_hook_execution: Optional[float] = None


@dataclass
class ResourceLimits:
    """Resource limits for an extension."""

    max_memory_mb: int
    max_cpu_percent: int
    max_disk_mb: int


class ResourceMonitor:
    """
    Monitors resource usage of extensions and enforces limits.
    """

    def __init__(self, check_interval: float = 30.0):
        """
        Initialize the resource monitor.

        Args:
            check_interval: How often to check resource usage (seconds)
        """
        self.check_interval = check_interval
        self.logger = logging.getLogger("extension.resource_monitor")

        # Resource tracking
        self.extension_usage: Dict[str, ResourceUsage] = {}
        self.extension_limits: Dict[str, ResourceLimits] = {}
        self.extension_start_times: Dict[str, float] = {}
        self.extension_actions: Dict[str, str] = {}

        # Enforcement configuration
        self.default_action = os.getenv("RESOURCE_MONITOR_ACTION", "warn").lower()
        self.throttle_seconds = float(
            os.getenv("RESOURCE_MONITOR_THROTTLE_SECONDS", "1")
        )

        # Monitoring control
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()

    def register_extension(self, record: ExtensionRecord) -> None:
        """
        Register an extension for resource monitoring.

        Args:
            record: Extension record to monitor
        """
        name = record.manifest.name

        with self._lock:
            # Set resource limits from manifest
            self.extension_limits[name] = ResourceLimits(
                max_memory_mb=record.manifest.resources.max_memory_mb,
                max_cpu_percent=record.manifest.resources.max_cpu_percent,
                max_disk_mb=record.manifest.resources.max_disk_mb,
            )

            # Initialize usage tracking
            self.extension_usage[name] = ResourceUsage(
                memory_mb=0.0, cpu_percent=0.0, disk_mb=0.0
            )

            # Record start time
            self.extension_start_times[name] = time.time()

            # Determine enforcement action
            action = getattr(record.manifest.resources, "enforcement_action", None)
            if not action or action == "default":
                self.extension_actions[name] = self.default_action
            else:
                self.extension_actions[name] = action.lower()

        self.logger.debug(f"Registered extension {name} for resource monitoring")

    def unregister_extension(self, name: str) -> None:
        """
        Unregister an extension from resource monitoring.

        Args:
            name: Extension name to unregister
        """
        with self._lock:
            self.extension_usage.pop(name, None)
            self.extension_limits.pop(name, None)
            self.extension_start_times.pop(name, None)
            self.extension_actions.pop(name, None)

        self.logger.debug(f"Unregistered extension {name} from resource monitoring")

    async def start_monitoring(self) -> None:
        """Start the resource monitoring loop."""
        if self._monitoring:
            self.logger.warning("Resource monitoring is already running")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started extension resource monitoring")

    async def stop_monitoring(self) -> None:
        """Stop the resource monitoring loop."""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Stopped extension resource monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._check_all_extensions()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_all_extensions(self) -> None:
        """Check resource usage for all registered extensions."""
        with self._lock:
            extensions_to_check = list(self.extension_usage.keys())

        for name in extensions_to_check:
            try:
                await self._check_extension_resources(name)
            except Exception as e:
                self.logger.error(
                    f"Failed to check resources for extension {name}: {e}"
                )

    async def _check_extension_resources(self, name: str) -> None:
        """
        Check resource usage for a specific extension.

        Args:
            name: Extension name
        """
        if not PSUTIL_AVAILABLE:
            # Fallback: use mock data when psutil is not available
            start_time = self.extension_start_times.get(name, time.time())
            uptime_seconds = time.time() - start_time

            with self._lock:
                if name in self.extension_usage:
                    self.extension_usage[name] = ResourceUsage(
                        memory_mb=10.0,  # Mock data
                        cpu_percent=5.0,  # Mock data
                        disk_mb=1.0,  # Mock data
                        network_bytes_sent=0,
                        network_bytes_recv=0,
                        uptime_seconds=uptime_seconds,
                    )
            return

        # Get current process info (simplified - in reality you'd track extension processes)
        try:
            process = psutil.Process()  # Current process for now

            # Calculate resource usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

            cpu_percent = process.cpu_percent()

            # Disk usage (simplified - would track extension-specific disk usage)
            disk_mb = 0.0

            # Network usage
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent if net_io else 0
            network_bytes_recv = net_io.bytes_recv if net_io else 0

            # Calculate uptime
            start_time = self.extension_start_times.get(name, time.time())
            uptime_seconds = time.time() - start_time

            # Update usage statistics
            with self._lock:
                if name in self.extension_usage:
                    self.extension_usage[name] = ResourceUsage(
                        memory_mb=memory_mb,
                        cpu_percent=cpu_percent,
                        disk_mb=disk_mb,
                        network_bytes_sent=network_bytes_sent,
                        network_bytes_recv=network_bytes_recv,
                        uptime_seconds=uptime_seconds,
                    )

            # Check limits
            await self._check_resource_limits(name)

        except Exception as e:
            if (
                PSUTIL_AVAILABLE
                and hasattr(psutil, "NoSuchProcess")
                and isinstance(e, psutil.NoSuchProcess)
            ):
                self.logger.warning(f"Process not found for extension {name}")
            else:
                self.logger.error(
                    f"Failed to get resource usage for extension {name}: {e}"
                )

    async def _check_resource_limits(self, name: str) -> None:
        """
        Check if an extension is exceeding resource limits.

        Args:
            name: Extension name
        """
        with self._lock:
            usage = self.extension_usage.get(name)
            limits = self.extension_limits.get(name)

        if not usage or not limits:
            return

        violations = []

        # Check memory limit
        if usage.memory_mb > limits.max_memory_mb:
            violations.append(
                f"Memory: {usage.memory_mb:.1f}MB > {limits.max_memory_mb}MB"
            )

        # Check CPU limit
        if usage.cpu_percent > limits.max_cpu_percent:
            violations.append(
                f"CPU: {usage.cpu_percent:.1f}% > {limits.max_cpu_percent}%"
            )

        # Check disk limit
        if usage.disk_mb > limits.max_disk_mb:
            violations.append(f"Disk: {usage.disk_mb:.1f}MB > {limits.max_disk_mb}MB")

        if violations:
            self.logger.warning(
                f"Extension {name} exceeding limits: {'; '.join(violations)}"
            )
            await self._enforce_action(name)

    async def _enforce_action(self, name: str) -> None:
        """Enforce configured action when limits are exceeded."""
        action = self.extension_actions.get(name, self.default_action)
        if action == "shutdown":
            self.logger.error(f"Shutting down extension {name} due to resource limits")
            self.unregister_extension(name)
        elif action == "throttle":
            self.logger.warning(
                f"Throttling extension {name} for {self.throttle_seconds} seconds"
            )
            await asyncio.sleep(self.throttle_seconds)

    def get_extension_usage(self, name: str) -> Optional[ResourceUsage]:
        """
        Get current resource usage for an extension.

        Args:
            name: Extension name

        Returns:
            ResourceUsage or None if not found
        """
        with self._lock:
            return self.extension_usage.get(name)

    def get_all_usage(self) -> Dict[str, ResourceUsage]:
        """Get resource usage for all extensions."""
        with self._lock:
            return self.extension_usage.copy()

    def get_extension_limits(self, name: str) -> Optional[ResourceLimits]:
        """
        Get resource limits for an extension.

        Args:
            name: Extension name

        Returns:
            ResourceLimits or None if not found
        """
        with self._lock:
            return self.extension_limits.get(name)

    def is_extension_healthy(self, name: str) -> bool:
        """
        Check if an extension is within healthy resource limits.

        Args:
            name: Extension name

        Returns:
            True if healthy, False otherwise
        """
        with self._lock:
            usage = self.extension_usage.get(name)
            limits = self.extension_limits.get(name)

        if not usage or not limits:
            return True  # Assume healthy if no data

        # Check if within limits (with some tolerance)
        memory_ok = usage.memory_mb <= limits.max_memory_mb * 0.9  # 90% threshold
        cpu_ok = usage.cpu_percent <= limits.max_cpu_percent * 0.9
        disk_ok = usage.disk_mb <= limits.max_disk_mb * 0.9

        return memory_ok and cpu_ok and disk_ok
    
    def update_hook_metrics(
        self,
        extension_name: str,
        hooks_registered: int = 0,
        hook_executed: bool = False,
        hook_failed: bool = False,
        execution_time_ms: float = 0.0
    ) -> None:
        """
        Update hook execution metrics for an extension.
        
        Args:
            extension_name: Name of the extension
            hooks_registered: Number of hooks registered (if changed)
            hook_executed: Whether a hook was executed
            hook_failed: Whether a hook execution failed
            execution_time_ms: Hook execution time in milliseconds
        """
        with self._lock:
            if extension_name not in self.extension_usage:
                return
            
            usage = self.extension_usage[extension_name]
            
            # Update hook registration count
            if hooks_registered > 0:
                usage.hooks_registered = hooks_registered
            
            # Update execution metrics
            if hook_executed:
                usage.hooks_executed += 1
                usage.hook_execution_time_ms += execution_time_ms
                usage.last_hook_execution = time.time()
            
            if hook_failed:
                usage.hooks_failed += 1
    
    def get_hook_metrics(self, extension_name: str) -> Optional[Dict[str, any]]:
        """
        Get hook execution metrics for an extension.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            Dictionary with hook metrics or None if not found
        """
        with self._lock:
            usage = self.extension_usage.get(extension_name)
            
        if not usage:
            return None
        
        return {
            "hooks_registered": usage.hooks_registered,
            "hooks_executed": usage.hooks_executed,
            "hooks_failed": usage.hooks_failed,
            "hook_success_rate": (
                (usage.hooks_executed - usage.hooks_failed) / usage.hooks_executed * 100
                if usage.hooks_executed > 0 else 100.0
            ),
            "average_execution_time_ms": (
                usage.hook_execution_time_ms / usage.hooks_executed
                if usage.hooks_executed > 0 else 0.0
            ),
            "total_execution_time_ms": usage.hook_execution_time_ms,
            "last_hook_execution": usage.last_hook_execution
        }
    
    def get_all_hook_metrics(self) -> Dict[str, Dict[str, any]]:
        """Get hook metrics for all extensions."""
        metrics = {}
        
        with self._lock:
            extension_names = list(self.extension_usage.keys())
        
        for name in extension_names:
            hook_metrics = self.get_hook_metrics(name)
            if hook_metrics:
                metrics[name] = hook_metrics
        
        return metrics
    
    def is_extension_hook_healthy(self, extension_name: str) -> bool:
        """
        Check if an extension's hook system is healthy.
        
        Args:
            extension_name: Name of the extension
            
        Returns:
            True if hook system is healthy, False otherwise
        """
        metrics = self.get_hook_metrics(extension_name)
        if not metrics:
            return True  # Assume healthy if no metrics
        
        # Check hook failure rate (should be less than 10%)
        success_rate = metrics["hook_success_rate"]
        if success_rate < 90.0 and metrics["hooks_executed"] > 10:
            return False
        
        # Check average execution time (should be reasonable)
        avg_time = metrics["average_execution_time_ms"]
        if avg_time > 5000.0:  # 5 seconds threshold
            return False
        
        return True


class ExtensionHealthChecker:
    """
    Monitors the health of extensions and provides health status.
    """

    def __init__(self, resource_monitor: ResourceMonitor):
        """
        Initialize the health checker.

        Args:
            resource_monitor: Resource monitor instance
        """
        self.resource_monitor = resource_monitor
        self.logger = logging.getLogger("extension.health_checker")

        # Health tracking
        self.extension_health: Dict[str, HealthStatus] = {}
        self.last_health_check: Dict[str, float] = {}

    def _determine_health_status(self, name: str) -> HealthStatus:
        """Determine health status based on resource usage and hook health."""
        usage = self.resource_monitor.get_extension_usage(name)
        limits = self.resource_monitor.get_extension_limits(name)

        if not usage or not limits:
            return HealthStatus.GREEN

        # Check resource usage ratios
        ratios = [
            usage.memory_mb / limits.max_memory_mb if limits.max_memory_mb else 0,
            usage.cpu_percent / limits.max_cpu_percent if limits.max_cpu_percent else 0,
            usage.disk_mb / limits.max_disk_mb if limits.max_disk_mb else 0,
        ]

        worst_resource_ratio = max(ratios)
        
        # Check hook health
        hook_healthy = self.resource_monitor.is_extension_hook_healthy(name)
        
        # Determine overall health status
        if not hook_healthy:
            return HealthStatus.RED
        
        if worst_resource_ratio < 0.7:
            return HealthStatus.GREEN
        elif worst_resource_ratio < 1.0:
            return HealthStatus.YELLOW
        else:
            return HealthStatus.RED

    async def check_extension_health(self, record: ExtensionRecord) -> HealthStatus:
        """
        Check the health of a specific extension.

        Args:
            record: Extension record to check

        Returns:
            HealthStatus value
        """
        name = record.manifest.name
        current_time = time.time()

        try:
            # Check if extension is active
            if record.status != ExtensionStatus.ACTIVE:
                status = HealthStatus.RED
            else:
                status = self._determine_health_status(name)

            # Check if extension instance is responsive
            if record.instance and hasattr(record.instance, "get_status"):
                try:
                    inst_status = record.instance.get_status()
                    if not inst_status.get("initialized", False):
                        status = HealthStatus.RED
                except Exception as e:
                    self.logger.warning(f"Extension {name} status check failed: {e}")
                    status = HealthStatus.RED

            # Update health tracking
            self.extension_health[name] = status
            self.last_health_check[name] = current_time

            if status == HealthStatus.RED:
                self.logger.warning(f"Extension {name} health check failed")

            return status

        except Exception as e:
            self.logger.error(f"Health check failed for extension {name}: {e}")
            self.extension_health[name] = HealthStatus.RED
            return HealthStatus.RED

    async def check_all_extensions_health(
        self, extensions: Dict[str, ExtensionRecord]
    ) -> Dict[str, HealthStatus]:
        """
        Check health of all extensions.

        Args:
            extensions: Dictionary of extension records

        Returns:
            Dictionary mapping extension names to health status
        """
        health_results: Dict[str, HealthStatus] = {}

        for name, record in extensions.items():
            health_results[name] = await self.check_extension_health(record)

        return health_results

    def get_extension_health(self, name: str) -> Optional[HealthStatus]:
        """
        Get cached health status for an extension.

        Args:
            name: Extension name

        Returns:
            Health status or None if not checked
        """
        return self.extension_health.get(name)

    def get_health_summary(self) -> Dict[str, any]:
        """
        Get a summary of extension health status.

        Returns:
            Dictionary with health summary
        """
        total_extensions = len(self.extension_health)
        healthy_extensions = sum(
            1
            for status in self.extension_health.values()
            if status == HealthStatus.GREEN
        )
        unhealthy_extensions = total_extensions - healthy_extensions

        return {
            "total_extensions": total_extensions,
            "healthy_extensions": healthy_extensions,
            "unhealthy_extensions": unhealthy_extensions,
            "health_percentage": (healthy_extensions / total_extensions * 100)
            if total_extensions > 0
            else 100,
            "last_check_times": self.last_health_check.copy(),
            "extension_health": self.extension_health.copy(),
        }


__all__ = [
    "ResourceMonitor",
    "ExtensionHealthChecker",
    "HealthStatus",
    "ResourceUsage",
    "ResourceLimits",
]
