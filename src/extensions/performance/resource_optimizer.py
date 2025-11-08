"""
Extension Resource Optimizer

Optimizes resource usage for extensions including memory, CPU, and I/O.
"""

import asyncio
import gc
import os
import psutil
import time
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ..models import ExtensionRecord


class ResourceType(Enum):
    """Types of resources that can be optimized."""
    MEMORY = "memory"
    CPU = "cpu"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    FILE_HANDLES = "file_handles"


@dataclass
class ResourceUsage:
    """Resource usage metrics for an extension."""
    extension_name: str
    timestamp: float
    memory_mb: float
    cpu_percent: float
    disk_read_mb: float
    disk_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    file_handles: int
    threads: int


@dataclass
class ResourceLimits:
    """Resource limits for an extension."""
    max_memory_mb: Optional[float] = None
    max_cpu_percent: Optional[float] = None
    max_disk_io_mb_per_sec: Optional[float] = None
    max_network_io_mb_per_sec: Optional[float] = None
    max_file_handles: Optional[int] = None
    max_threads: Optional[int] = None


@dataclass
class OptimizationAction:
    """An optimization action to be taken."""
    extension_name: str
    action_type: str
    description: str
    priority: int
    estimated_savings: Dict[ResourceType, float]


class ExtensionResourceOptimizer:
    """
    Optimizes resource usage for extensions to improve overall system performance.
    
    Features:
    - Real-time resource monitoring
    - Automatic resource optimization
    - Memory garbage collection
    - CPU throttling
    - I/O optimization
    - Resource limit enforcement
    """
    
    def __init__(
        self,
        monitoring_interval: float = 30.0,
        optimization_interval: float = 300.0,  # 5 minutes
        memory_threshold: float = 0.8,  # 80% of system memory
        cpu_threshold: float = 0.7,    # 70% of system CPU
    ):
        self.monitoring_interval = monitoring_interval
        self.optimization_interval = optimization_interval
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        
        self._extension_processes: Dict[str, psutil.Process] = {}
        self._resource_usage_history: Dict[str, List[ResourceUsage]] = {}
        self._resource_limits: Dict[str, ResourceLimits] = {}
        self._optimization_actions: List[OptimizationAction] = []
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> None:
        """Start the resource optimizer."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        
        self.logger.info("Extension resource optimizer started")
    
    async def stop(self) -> None:
        """Stop the resource optimizer."""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Extension resource optimizer stopped")
    
    async def register_extension(
        self,
        extension_name: str,
        process_id: int,
        limits: Optional[ResourceLimits] = None
    ) -> None:
        """Register an extension for resource monitoring."""
        try:
            process = psutil.Process(process_id)
            self._extension_processes[extension_name] = process
            
            if limits:
                self._resource_limits[extension_name] = limits
            
            self._resource_usage_history[extension_name] = []
            
            self.logger.info(f"Registered extension {extension_name} for resource monitoring")
            
        except psutil.NoSuchProcess:
            self.logger.error(f"Process {process_id} not found for extension {extension_name}")
    
    async def unregister_extension(self, extension_name: str) -> None:
        """Unregister an extension from resource monitoring."""
        self._extension_processes.pop(extension_name, None)
        self._resource_limits.pop(extension_name, None)
        self._resource_usage_history.pop(extension_name, None)
        
        self.logger.info(f"Unregistered extension {extension_name} from resource monitoring")
    
    async def get_resource_usage(
        self,
        extension_name: str,
        time_window: Optional[float] = None
    ) -> List[ResourceUsage]:
        """Get resource usage history for an extension."""
        history = self._resource_usage_history.get(extension_name, [])
        
        if time_window is None:
            return history
        
        cutoff_time = time.time() - time_window
        return [usage for usage in history if usage.timestamp >= cutoff_time]
    
    async def get_system_resource_usage(self) -> Dict[str, float]:
        """Get current system resource usage."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_io = psutil.disk_io_counters()
            network_io = psutil.net_io_counters()
            
            return {
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'cpu_percent': cpu_percent,
                'disk_read_mb_per_sec': getattr(disk_io, 'read_bytes', 0) / (1024**2),
                'disk_write_mb_per_sec': getattr(disk_io, 'write_bytes', 0) / (1024**2),
                'network_sent_mb_per_sec': getattr(network_io, 'bytes_sent', 0) / (1024**2),
                'network_recv_mb_per_sec': getattr(network_io, 'bytes_recv', 0) / (1024**2),
            }
        except Exception as e:
            self.logger.error(f"Failed to get system resource usage: {e}")
            return {}
    
    async def optimize_extension_memory(self, extension_name: str) -> bool:
        """Optimize memory usage for a specific extension."""
        try:
            process = self._extension_processes.get(extension_name)
            if not process:
                return False
            
            # Force garbage collection
            gc.collect()
            
            # Get memory usage before optimization
            memory_before = process.memory_info().rss / (1024**2)
            
            # Trigger extension-specific memory optimization
            await self._trigger_extension_memory_cleanup(extension_name)
            
            # Force another garbage collection
            gc.collect()
            
            # Get memory usage after optimization
            memory_after = process.memory_info().rss / (1024**2)
            
            savings = memory_before - memory_after
            if savings > 0:
                self.logger.info(
                    f"Memory optimization for {extension_name}: "
                    f"saved {savings:.1f} MB ({memory_before:.1f} -> {memory_after:.1f} MB)"
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed for {extension_name}: {e}")
            return False
    
    async def optimize_extension_cpu(self, extension_name: str) -> bool:
        """Optimize CPU usage for a specific extension."""
        try:
            process = self._extension_processes.get(extension_name)
            if not process:
                return False
            
            # Lower process priority
            try:
                if hasattr(process, 'nice'):
                    current_nice = process.nice()
                    if current_nice < 10:  # Only increase if not already high
                        process.nice(min(current_nice + 5, 19))
                        self.logger.info(f"Lowered CPU priority for {extension_name}")
                        return True
            except psutil.AccessDenied:
                self.logger.warning(f"Cannot change CPU priority for {extension_name}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"CPU optimization failed for {extension_name}: {e}")
            return False
    
    async def enforce_resource_limits(self, extension_name: str) -> List[str]:
        """Enforce resource limits for an extension."""
        violations = []
        
        try:
            process = self._extension_processes.get(extension_name)
            limits = self._resource_limits.get(extension_name)
            
            if not process or not limits:
                return violations
            
            # Check memory limit
            if limits.max_memory_mb:
                memory_mb = process.memory_info().rss / (1024**2)
                if memory_mb > limits.max_memory_mb:
                    violations.append(f"Memory usage {memory_mb:.1f} MB exceeds limit {limits.max_memory_mb} MB")
                    await self.optimize_extension_memory(extension_name)
            
            # Check CPU limit
            if limits.max_cpu_percent:
                cpu_percent = process.cpu_percent()
                if cpu_percent > limits.max_cpu_percent:
                    violations.append(f"CPU usage {cpu_percent:.1f}% exceeds limit {limits.max_cpu_percent}%")
                    await self.optimize_extension_cpu(extension_name)
            
            # Check file handle limit
            if limits.max_file_handles:
                try:
                    file_handles = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
                    if file_handles > limits.max_file_handles:
                        violations.append(f"File handles {file_handles} exceeds limit {limits.max_file_handles}")
                except (psutil.AccessDenied, AttributeError):
                    pass
            
            # Check thread limit
            if limits.max_threads:
                try:
                    threads = process.num_threads()
                    if threads > limits.max_threads:
                        violations.append(f"Thread count {threads} exceeds limit {limits.max_threads}")
                except psutil.AccessDenied:
                    pass
            
        except Exception as e:
            self.logger.error(f"Resource limit enforcement failed for {extension_name}: {e}")
        
        return violations
    
    async def get_optimization_recommendations(self) -> List[OptimizationAction]:
        """Get optimization recommendations based on resource usage patterns."""
        recommendations = []
        
        for extension_name, history in self._resource_usage_history.items():
            if len(history) < 10:  # Need sufficient data
                continue
            
            recent_usage = history[-10:]  # Last 10 measurements
            
            # Analyze memory usage patterns
            memory_usage = [u.memory_mb for u in recent_usage]
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)
            
            if max_memory > avg_memory * 1.5:  # High memory variance
                recommendations.append(OptimizationAction(
                    extension_name=extension_name,
                    action_type="memory_optimization",
                    description=f"High memory variance detected (avg: {avg_memory:.1f} MB, max: {max_memory:.1f} MB)",
                    priority=2,
                    estimated_savings={ResourceType.MEMORY: max_memory - avg_memory}
                ))
            
            # Analyze CPU usage patterns
            cpu_usage = [u.cpu_percent for u in recent_usage]
            avg_cpu = sum(cpu_usage) / len(cpu_usage)
            
            if avg_cpu > 50:  # High CPU usage
                recommendations.append(OptimizationAction(
                    extension_name=extension_name,
                    action_type="cpu_optimization",
                    description=f"High CPU usage detected (avg: {avg_cpu:.1f}%)",
                    priority=1,
                    estimated_savings={ResourceType.CPU: avg_cpu * 0.2}  # Estimate 20% reduction
                ))
        
        return sorted(recommendations, key=lambda x: x.priority)
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                await self._collect_resource_metrics()
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop."""
        while self._running:
            try:
                await self._perform_optimizations()
                await asyncio.sleep(self.optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Resource optimization error: {e}")
                await asyncio.sleep(self.optimization_interval)
    
    async def _collect_resource_metrics(self) -> None:
        """Collect resource usage metrics for all registered extensions."""
        current_time = time.time()
        
        for extension_name, process in self._extension_processes.items():
            try:
                if not process.is_running():
                    continue
                
                # Get process metrics
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                
                # Get I/O metrics if available
                try:
                    io_counters = process.io_counters()
                    disk_read_mb = io_counters.read_bytes / (1024**2)
                    disk_write_mb = io_counters.write_bytes / (1024**2)
                except (psutil.AccessDenied, AttributeError):
                    disk_read_mb = disk_write_mb = 0
                
                # Get network metrics (simplified)
                network_sent_mb = network_recv_mb = 0
                
                # Get file handle count
                try:
                    file_handles = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
                except (psutil.AccessDenied, AttributeError):
                    file_handles = 0
                
                # Get thread count
                try:
                    threads = process.num_threads()
                except psutil.AccessDenied:
                    threads = 0
                
                # Create usage record
                usage = ResourceUsage(
                    extension_name=extension_name,
                    timestamp=current_time,
                    memory_mb=memory_info.rss / (1024**2),
                    cpu_percent=cpu_percent,
                    disk_read_mb=disk_read_mb,
                    disk_write_mb=disk_write_mb,
                    network_sent_mb=network_sent_mb,
                    network_recv_mb=network_recv_mb,
                    file_handles=file_handles,
                    threads=threads
                )
                
                # Store usage history (keep last 1000 entries)
                history = self._resource_usage_history[extension_name]
                history.append(usage)
                if len(history) > 1000:
                    history.pop(0)
                
                # Check resource limits
                violations = await self.enforce_resource_limits(extension_name)
                if violations:
                    self.logger.warning(f"Resource violations for {extension_name}: {violations}")
                
            except psutil.NoSuchProcess:
                # Process no longer exists
                await self.unregister_extension(extension_name)
            except Exception as e:
                self.logger.error(f"Failed to collect metrics for {extension_name}: {e}")
    
    async def _perform_optimizations(self) -> None:
        """Perform automatic optimizations based on system state."""
        try:
            # Get system resource usage
            system_usage = await self.get_system_resource_usage()
            
            # Check if system is under pressure
            memory_pressure = system_usage.get('memory_percent', 0) > self.memory_threshold * 100
            cpu_pressure = system_usage.get('cpu_percent', 0) > self.cpu_threshold * 100
            
            if memory_pressure or cpu_pressure:
                self.logger.info("System under resource pressure, performing optimizations")
                
                # Get optimization recommendations
                recommendations = await self.get_optimization_recommendations()
                
                # Execute high-priority optimizations
                for action in recommendations[:5]:  # Limit to top 5 actions
                    if action.action_type == "memory_optimization" and memory_pressure:
                        await self.optimize_extension_memory(action.extension_name)
                    elif action.action_type == "cpu_optimization" and cpu_pressure:
                        await self.optimize_extension_cpu(action.extension_name)
        
        except Exception as e:
            self.logger.error(f"Optimization execution failed: {e}")
    
    async def _trigger_extension_memory_cleanup(self, extension_name: str) -> None:
        """Trigger extension-specific memory cleanup."""
        # This would typically send a signal to the extension to perform cleanup
        # For now, we'll just force garbage collection
        gc.collect()
        
        # In a real implementation, this might:
        # - Send IPC message to extension process
        # - Call extension cleanup API
        # - Clear extension caches
        pass