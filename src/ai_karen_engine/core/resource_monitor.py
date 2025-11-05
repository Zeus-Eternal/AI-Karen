"""
Resource Monitor and Automatic Optimization System.

This module implements comprehensive system resource monitoring with real-time tracking,
resource pressure detection, automatic service suspension, memory optimization,
and resource usage alerting.
"""

import asyncio
import gc
import logging
import os
import threading
import time
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor

import psutil

from .service_classification import ServiceClassification
from .classified_service_registry import ClassifiedServiceRegistry, ServiceLifecycleState

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Types of system resources to monitor."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class AlertLevel(str, Enum):
    """Alert levels for resource usage notifications."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class OptimizationAction(str, Enum):
    """Types of optimization actions that can be taken."""
    SUSPEND_SERVICE = "suspend_service"
    CLEANUP_MEMORY = "cleanup_memory"
    FORCE_GC = "force_gc"
    CLEAR_CACHE = "clear_cache"
    REDUCE_WORKERS = "reduce_workers"
    THROTTLE_REQUESTS = "throttle_requests"


@dataclass
class ResourceThreshold:
    """Configuration for resource usage thresholds."""
    warning_level: float = 70.0      # Percentage at which to warn
    critical_level: float = 85.0     # Percentage at which to take action
    emergency_level: float = 95.0    # Percentage at which to take emergency action
    sustained_duration: float = 30.0  # Seconds threshold must be exceeded
    check_interval: float = 5.0      # Seconds between checks


@dataclass
class ResourceMetrics:
    """Current system resource usage metrics."""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available: int = 0
    memory_used: int = 0
    disk_percent: float = 0.0
    disk_free: int = 0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    gpu_percent: Optional[float] = None
    gpu_memory_percent: Optional[float] = None
    process_count: int = 0
    thread_count: int = 0
    open_files: int = 0


@dataclass
class ResourceAlert:
    """Resource usage alert information."""
    resource_type: ResourceType
    level: AlertLevel
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    actions_taken: List[OptimizationAction] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Result of an optimization action."""
    action: OptimizationAction
    success: bool
    message: str
    resources_freed: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class ResourceMonitor:
    """
    Comprehensive resource monitoring and automatic optimization system.
    
    Provides real-time system resource tracking, resource pressure detection,
    automatic service suspension during high load, memory optimization with
    garbage collection and cache management, and resource usage alerting.
    """
    
    def __init__(
        self,
        service_registry: Optional[ClassifiedServiceRegistry] = None,
        check_interval: float = 5.0,
        enable_auto_optimization: bool = True,
        enable_gpu_monitoring: bool = True
    ):
        """
        Initialize the ResourceMonitor.
        
        Args:
            service_registry: Service registry for managing service lifecycle
            check_interval: Seconds between resource checks
            enable_auto_optimization: Whether to automatically optimize resources
            enable_gpu_monitoring: Whether to monitor GPU resources
        """
        self.service_registry = service_registry
        self.check_interval = check_interval
        self.enable_auto_optimization = enable_auto_optimization
        self.enable_gpu_monitoring = enable_gpu_monitoring
        
        # Resource thresholds
        self.thresholds = {
            ResourceType.CPU: ResourceThreshold(70.0, 85.0, 95.0, 30.0, check_interval),
            ResourceType.MEMORY: ResourceThreshold(75.0, 90.0, 98.0, 20.0, check_interval),
            ResourceType.DISK: ResourceThreshold(80.0, 90.0, 95.0, 60.0, check_interval),
            ResourceType.NETWORK: ResourceThreshold(70.0, 85.0, 95.0, 30.0, check_interval),
            ResourceType.GPU: ResourceThreshold(80.0, 90.0, 95.0, 30.0, check_interval)
        }
        
        # Monitoring state
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._metrics_history: List[ResourceMetrics] = []
        self._alerts: List[ResourceAlert] = []
        self._optimization_results: List[OptimizationResult] = []
        self._resource_pressure_state: Dict[ResourceType, datetime] = {}
        
        # Callbacks for alerts and optimizations
        self._alert_callbacks: List[Callable[[ResourceAlert], None]] = []
        self._optimization_callbacks: List[Callable[[OptimizationResult], None]] = []
        
        # GPU monitoring setup
        self._gpu_available = False
        if self.enable_gpu_monitoring:
            self._setup_gpu_monitoring()
        
        # Cache management
        self._cache_registry: Dict[str, weakref.WeakSet] = {}
        self._last_gc_time = time.time()
        self._gc_interval = 60.0  # Force GC every 60 seconds under pressure
        
        logger.info("ResourceMonitor initialized with auto-optimization: %s", enable_auto_optimization)
    
    def _setup_gpu_monitoring(self) -> None:
        """Setup GPU monitoring if available."""
        try:
            import GPUtil
            self._gpu_available = len(GPUtil.getGPUs()) > 0
            if self._gpu_available:
                logger.info("GPU monitoring enabled - %d GPU(s) detected", len(GPUtil.getGPUs()))
        except ImportError:
            logger.debug("GPUtil not available - GPU monitoring disabled")
        except Exception as e:
            logger.warning("Failed to setup GPU monitoring: %s", e)
    
    async def start_monitoring(self) -> None:
        """Start the resource monitoring loop."""
        if self._monitoring:
            logger.warning("Resource monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Resource monitoring started with %ds interval", self.check_interval)
    
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
        
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # Collect current metrics
                metrics = await self.monitor_system_resources()
                
                # Store metrics history (keep last 100 entries)
                self._metrics_history.append(metrics)
                if len(self._metrics_history) > 100:
                    self._metrics_history.pop(0)
                
                # Check for resource pressure
                pressure_detected = await self.detect_resource_pressure()
                
                # Trigger automatic optimization if enabled and pressure detected
                if self.enable_auto_optimization and pressure_detected:
                    await self.trigger_resource_cleanup()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in resource monitoring loop: %s", e)
                await asyncio.sleep(self.check_interval)
    
    async def monitor_system_resources(self) -> ResourceMetrics:
        """
        Monitor current system resource usage.
        
        Returns:
            ResourceMetrics: Current system resource metrics
        """
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            memory_used = memory.used
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Current process metrics
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            try:
                open_files = len(current_process.open_files())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                open_files = 0
            
            # GPU metrics
            gpu_percent = None
            gpu_memory_percent = None
            if self._gpu_available:
                gpu_percent, gpu_memory_percent = await self._get_gpu_metrics()
            
            metrics = ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available=memory_available,
                memory_used=memory_used,
                disk_percent=disk_percent,
                disk_free=disk_free,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                gpu_percent=gpu_percent,
                gpu_memory_percent=gpu_memory_percent,
                process_count=process_count,
                thread_count=thread_count,
                open_files=open_files
            )
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to collect system metrics: %s", e)
            return ResourceMetrics()  # Return empty metrics on error
    
    async def _get_gpu_metrics(self) -> Tuple[Optional[float], Optional[float]]:
        """Get GPU utilization metrics."""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if not gpus:
                return None, None
            
            # Average across all GPUs
            gpu_load = sum(gpu.load * 100 for gpu in gpus) / len(gpus)
            gpu_memory = sum(gpu.memoryUtil * 100 for gpu in gpus) / len(gpus)
            
            return gpu_load, gpu_memory
            
        except Exception as e:
            logger.debug("Failed to get GPU metrics: %s", e)
            return None, None 
   
    async def detect_resource_pressure(self) -> bool:
        """
        Detect if system is under resource pressure.
        
        Returns:
            bool: True if resource pressure is detected
        """
        if not self._metrics_history:
            return False
        
        current_metrics = self._metrics_history[-1]
        current_time = datetime.now()
        pressure_detected = False
        
        # Check each resource type
        for resource_type, threshold in self.thresholds.items():
            current_value = self._get_resource_value(current_metrics, resource_type)
            if current_value is None:
                continue
            
            # Check if threshold is exceeded
            if current_value >= threshold.warning_level:
                # Check if this is sustained pressure
                pressure_start = self._resource_pressure_state.get(resource_type)
                
                if pressure_start is None:
                    # First time exceeding threshold
                    self._resource_pressure_state[resource_type] = current_time
                elif (current_time - pressure_start).total_seconds() >= threshold.sustained_duration:
                    # Sustained pressure detected
                    alert_level = self._determine_alert_level(current_value, threshold)
                    await self._create_alert(resource_type, alert_level, current_value, threshold)
                    pressure_detected = True
            else:
                # Resource usage is normal, clear pressure state
                if resource_type in self._resource_pressure_state:
                    del self._resource_pressure_state[resource_type]
        
        return pressure_detected
    
    def _get_resource_value(self, metrics: ResourceMetrics, resource_type: ResourceType) -> Optional[float]:
        """Get the current value for a specific resource type."""
        if resource_type == ResourceType.CPU:
            return metrics.cpu_percent
        elif resource_type == ResourceType.MEMORY:
            return metrics.memory_percent
        elif resource_type == ResourceType.DISK:
            return metrics.disk_percent
        elif resource_type == ResourceType.GPU:
            return metrics.gpu_percent
        elif resource_type == ResourceType.NETWORK:
            # Calculate network utilization as a percentage of available bandwidth
            # This is a simplified calculation - in practice you'd need to know the interface capacity
            return None  # Skip network monitoring for now
        return None
    
    def _determine_alert_level(self, current_value: float, threshold: ResourceThreshold) -> AlertLevel:
        """Determine the appropriate alert level based on current value and thresholds."""
        if current_value >= threshold.emergency_level:
            return AlertLevel.EMERGENCY
        elif current_value >= threshold.critical_level:
            return AlertLevel.CRITICAL
        elif current_value >= threshold.warning_level:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO
    
    async def _create_alert(
        self,
        resource_type: ResourceType,
        level: AlertLevel,
        current_value: float,
        threshold: ResourceThreshold
    ) -> None:
        """Create and process a resource alert."""
        # Determine threshold value based on alert level
        if level == AlertLevel.EMERGENCY:
            threshold_value = threshold.emergency_level
        elif level == AlertLevel.CRITICAL:
            threshold_value = threshold.critical_level
        else:
            threshold_value = threshold.warning_level
        
        message = f"{resource_type.value.upper()} usage at {current_value:.1f}% (threshold: {threshold_value:.1f}%)"
        
        alert = ResourceAlert(
            resource_type=resource_type,
            level=level,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message
        )
        
        self._alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self._alerts) > 50:
            self._alerts.pop(0)
        
        # Log the alert
        if level == AlertLevel.EMERGENCY:
            logger.critical("EMERGENCY: %s", message)
        elif level == AlertLevel.CRITICAL:
            logger.error("CRITICAL: %s", message)
        elif level == AlertLevel.WARNING:
            logger.warning("WARNING: %s", message)
        else:
            logger.info("INFO: %s", message)
        
        # Notify alert callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error("Error in alert callback: %s", e)
    
    async def trigger_resource_cleanup(self) -> List[OptimizationResult]:
        """
        Trigger automatic resource cleanup and optimization.
        
        Returns:
            List[OptimizationResult]: Results of optimization actions taken
        """
        results = []
        
        if not self._metrics_history:
            return results
        
        current_metrics = self._metrics_history[-1]
        
        # Memory optimization
        if current_metrics.memory_percent >= self.thresholds[ResourceType.MEMORY].critical_level:
            memory_results = await self._optimize_memory_usage()
            results.extend(memory_results)
        
        # CPU optimization - suspend non-essential services
        if current_metrics.cpu_percent >= self.thresholds[ResourceType.CPU].critical_level:
            cpu_results = await self._optimize_cpu_usage()
            results.extend(cpu_results)
        
        # GPU optimization
        if (current_metrics.gpu_percent is not None and 
            current_metrics.gpu_percent >= self.thresholds[ResourceType.GPU].critical_level):
            gpu_results = await self._optimize_gpu_usage()
            results.extend(gpu_results)
        
        # Store optimization results
        self._optimization_results.extend(results)
        
        # Keep only last 100 optimization results
        if len(self._optimization_results) > 100:
            self._optimization_results = self._optimization_results[-100:]
        
        # Notify optimization callbacks
        for result in results:
            for callback in self._optimization_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error("Error in optimization callback: %s", e)
        
        return results
    
    async def _optimize_memory_usage(self) -> List[OptimizationResult]:
        """Optimize memory usage through various strategies."""
        results = []
        initial_memory = psutil.virtual_memory().percent
        
        # Force garbage collection
        gc_result = await self._force_garbage_collection()
        results.append(gc_result)
        
        # Clear caches
        cache_result = await self._clear_caches()
        results.append(cache_result)
        
        # Suspend background services if service registry is available
        if self.service_registry:
            suspend_result = await self._suspend_background_services()
            results.append(suspend_result)
        
        # Calculate total memory freed
        final_memory = psutil.virtual_memory().percent
        memory_freed = max(0, initial_memory - final_memory)
        
        logger.info("Memory optimization completed - freed %.1f%% memory", memory_freed)
        
        return results
    
    async def _optimize_cpu_usage(self) -> List[OptimizationResult]:
        """Optimize CPU usage by suspending non-essential services."""
        results = []
        
        if not self.service_registry:
            result = OptimizationResult(
                action=OptimizationAction.SUSPEND_SERVICE,
                success=False,
                message="No service registry available for CPU optimization"
            )
            results.append(result)
            return results
        
        # Suspend optional and background services - Production implementation
        suspended_count = 0
        cpu_freed = 0.0

        try:
            # Get all services from registry
            all_services = registry.get_all_services()

            # Identify non-essential services based on priority and classification
            essential_prefixes = ['db', 'database', 'auth', 'engine', 'core', 'security', 'memory']
            suspendable_services = [
                svc for svc in all_services
                if not any(svc.lower().startswith(prefix) for prefix in essential_prefixes)
            ]

            # Suspend each non-essential service
            for service_name in suspendable_services:
                try:
                    # Check if service is currently running
                    if not hasattr(registry, 'is_running') or registry.is_running(service_name):
                        # Measure CPU before suspension
                        before_cpu = psutil.cpu_percent(interval=0.1)

                        # Suspend the service if method exists
                        if hasattr(registry, 'suspend_service'):
                            await registry.suspend_service(service_name)
                        elif hasattr(registry, 'stop_service'):
                            await registry.stop_service(service_name)

                        suspended_count += 1

                        # Measure CPU after suspension
                        after_cpu = psutil.cpu_percent(interval=0.1)
                        cpu_freed += max(0, before_cpu - after_cpu)

                        logger.info(f"Suspended service '{service_name}' for CPU optimization")

                except Exception as e:
                    logger.warning(f"Failed to suspend service '{service_name}': {e}")
                    continue

            # Additional CPU optimization: Lower process priority if available
            if suspended_count == 0:
                try:
                    current_process = psutil.Process()
                    current_process.nice(10)  # Lower priority
                    logger.info("Lowered process priority for CPU optimization")
                except Exception:
                    pass

            result = OptimizationResult(
                action=OptimizationAction.SUSPEND_SERVICE,
                success=True,
                message=f"Suspended {suspended_count} non-essential services for CPU optimization",
                resources_freed={"cpu_percent": cpu_freed, "services_suspended": suspended_count}
            )
            results.append(result)

        except Exception as e:
            logger.error(f"Error during service suspension: {e}")
            result = OptimizationResult(
                action=OptimizationAction.SUSPEND_SERVICE,
                success=False,
                message=f"Failed to suspend services: {e}"
            )
            results.append(result)

        return results
    
    async def _optimize_gpu_usage(self) -> List[OptimizationResult]:
        """
        Optimize GPU usage by clearing GPU memory and suspending GPU-intensive services.
        Production implementation with PyTorch, TensorFlow, and CUDA support.
        """
        results = []
        gpu_memory_freed = 0.0

        try:
            # Try to clear PyTorch GPU cache
            try:
                import torch
                if torch.cuda.is_available():
                    before_mem = torch.cuda.memory_allocated() / (1024 ** 3)  # GB
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    after_mem = torch.cuda.memory_allocated() / (1024 ** 3)  # GB
                    gpu_memory_freed += (before_mem - after_mem)
                    logger.info("Cleared PyTorch GPU cache")
            except ImportError:
                logger.debug("PyTorch not available for GPU optimization")
            except Exception as e:
                logger.warning(f"Failed to clear PyTorch GPU cache: {e}")

            # Try to clear TensorFlow GPU cache
            try:
                import tensorflow as tf
                if tf.config.list_physical_devices('GPU'):
                    tf.keras.backend.clear_session()
                    logger.info("Cleared TensorFlow GPU session")
            except ImportError:
                logger.debug("TensorFlow not available for GPU optimization")
            except Exception as e:
                logger.warning(f"Failed to clear TensorFlow GPU session: {e}")

            # Try to force garbage collection on GPU
            try:
                import gc
                gc.collect()
                logger.debug("Forced garbage collection for GPU cleanup")
            except Exception as e:
                logger.warning(f"Failed to force garbage collection: {e}")

            result = OptimizationResult(
                action=OptimizationAction.CLEAR_CACHE,
                success=True,
                message=f"GPU memory optimization completed, freed ~{gpu_memory_freed:.2f} GB",
                resources_freed={"gpu_memory_gb": gpu_memory_freed}
            )
            results.append(result)

        except Exception as e:
            logger.error(f"Error during GPU optimization: {e}")
            result = OptimizationResult(
                action=OptimizationAction.CLEAR_CACHE,
                success=False,
                message=f"Failed to optimize GPU usage: {e}"
            )
            results.append(result)
        
        return results
    
    async def _force_garbage_collection(self) -> OptimizationResult:
        """Force garbage collection to free memory."""
        try:
            initial_memory = psutil.virtual_memory().used
            
            # Force garbage collection
            collected = gc.collect()
            
            final_memory = psutil.virtual_memory().used
            memory_freed = max(0, initial_memory - final_memory)
            
            self._last_gc_time = time.time()
            
            return OptimizationResult(
                action=OptimizationAction.FORCE_GC,
                success=True,
                message=f"Garbage collection freed {collected} objects, {memory_freed / 1024 / 1024:.1f}MB memory",
                resources_freed={"memory_bytes": memory_freed}
            )
            
        except Exception as e:
            return OptimizationResult(
                action=OptimizationAction.FORCE_GC,
                success=False,
                message=f"Failed to force garbage collection: {e}"
            )
    
    async def _clear_caches(self) -> OptimizationResult:
        """Clear registered caches to free memory."""
        try:
            cleared_caches = 0
            total_freed = 0
            
            for cache_name, cache_weakset in self._cache_registry.items():
                try:
                    # Clear all caches in the weak set
                    for cache in list(cache_weakset):
                        if hasattr(cache, 'clear'):
                            cache.clear()
                            cleared_caches += 1
                except Exception as e:
                    logger.debug("Error clearing cache %s: %s", cache_name, e)
            
            return OptimizationResult(
                action=OptimizationAction.CLEAR_CACHE,
                success=True,
                message=f"Cleared {cleared_caches} caches",
                resources_freed={"caches_cleared": cleared_caches}
            )
            
        except Exception as e:
            return OptimizationResult(
                action=OptimizationAction.CLEAR_CACHE,
                success=False,
                message=f"Failed to clear caches: {e}"
            )
    
    async def _suspend_background_services(self) -> OptimizationResult:
        """
        Suspend background services to free resources.
        Production implementation with service registry integration.
        """
        try:
            suspended_count = 0
            resources_freed = {}

            # Get service registry
            try:
                from ai_karen_engine.core import get_registry
                registry = get_registry()
            except Exception:
                logger.debug("Service registry not available")
                registry = None

            if registry:
                # Get all services
                all_services = registry.get_all_services()

                # Identify background/non-critical services
                background_prefixes = ['metrics', 'analytics', 'monitoring', 'reporting', 'logging']
                background_services = [
                    svc for svc in all_services
                    if any(svc.lower().startswith(prefix) for prefix in background_prefixes)
                ]

                # Suspend each background service
                for service_name in background_services:
                    try:
                        # Check if service has suspend capability
                        if hasattr(registry, 'suspend_service'):
                            await registry.suspend_service(service_name)
                            suspended_count += 1
                            logger.info(f"Suspended background service: {service_name}")
                    except Exception as e:
                        logger.warning(f"Failed to suspend {service_name}: {e}")
                        continue

                resources_freed["services_suspended"] = suspended_count

            return OptimizationResult(
                action=OptimizationAction.SUSPEND_SERVICE,
                success=True,
                message=f"Suspended {suspended_count} background services",
                resources_freed=resources_freed
            )

        except Exception as e:
            logger.error(f"Error suspending background services: {e}")
            return OptimizationResult(
                action=OptimizationAction.SUSPEND_SERVICE,
                success=False,
                message=f"Failed to suspend background services: {e}"
            )
    
    def optimize_memory_usage(self) -> None:
        """
        Synchronous memory optimization for immediate use.
        
        This is a convenience method that performs basic memory optimization
        without requiring async context.
        """
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Clear registered caches
            cleared_caches = 0
            for cache_name, cache_weakset in self._cache_registry.items():
                try:
                    for cache in list(cache_weakset):
                        if hasattr(cache, 'clear'):
                            cache.clear()
                            cleared_caches += 1
                except Exception as e:
                    logger.debug("Error clearing cache %s: %s", cache_name, e)
            
            logger.info("Memory optimization: collected %d objects, cleared %d caches", 
                       collected, cleared_caches)
            
        except Exception as e:
            logger.error("Failed to optimize memory: %s", e)
    
    def register_cache(self, name: str, cache_object: Any) -> None:
        """
        Register a cache object for automatic cleanup during resource pressure.
        
        Args:
            name: Name identifier for the cache
            cache_object: Cache object that implements a 'clear()' method
        """
        if name not in self._cache_registry:
            self._cache_registry[name] = weakref.WeakSet()
        
        self._cache_registry[name].add(cache_object)
        logger.debug("Registered cache '%s' for automatic cleanup", name)
    
    def add_alert_callback(self, callback: Callable[[ResourceAlert], None]) -> None:
        """Add a callback function to be called when alerts are generated."""
        self._alert_callbacks.append(callback)
    
    def add_optimization_callback(self, callback: Callable[[OptimizationResult], None]) -> None:
        """Add a callback function to be called when optimizations are performed."""
        self._optimization_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """Get the most recent resource metrics."""
        return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[ResourceMetrics]:
        """Get historical resource metrics."""
        if limit is None:
            return self._metrics_history.copy()
        return self._metrics_history[-limit:] if self._metrics_history else []
    
    def get_recent_alerts(self, limit: Optional[int] = None) -> List[ResourceAlert]:
        """Get recent resource alerts."""
        if limit is None:
            return self._alerts.copy()
        return self._alerts[-limit:] if self._alerts else []
    
    def get_optimization_history(self, limit: Optional[int] = None) -> List[OptimizationResult]:
        """Get historical optimization results."""
        if limit is None:
            return self._optimization_results.copy()
        return self._optimization_results[-limit:] if self._optimization_results else []
    
    def configure_thresholds(self, resource_type: ResourceType, threshold: ResourceThreshold) -> None:
        """Configure resource thresholds for a specific resource type."""
        self.thresholds[resource_type] = threshold
        logger.info("Updated thresholds for %s: warning=%.1f%%, critical=%.1f%%, emergency=%.1f%%",
                   resource_type.value, threshold.warning_level, threshold.critical_level, threshold.emergency_level)
    
    def is_under_pressure(self, resource_type: Optional[ResourceType] = None) -> bool:
        """
        Check if system is currently under resource pressure.
        
        Args:
            resource_type: Specific resource type to check, or None for any resource
            
        Returns:
            bool: True if under pressure
        """
        if resource_type is not None:
            return resource_type in self._resource_pressure_state
        
        return len(self._resource_pressure_state) > 0
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_monitoring()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_monitoring()


# Utility functions for integration with other components

def create_default_resource_monitor(
    service_registry: Optional[ClassifiedServiceRegistry] = None,
    enable_auto_optimization: bool = True
) -> ResourceMonitor:
    """
    Create a ResourceMonitor with default configuration.
    
    Args:
        service_registry: Optional service registry for service management
        enable_auto_optimization: Whether to enable automatic optimization
        
    Returns:
        ResourceMonitor: Configured resource monitor instance
    """
    return ResourceMonitor(
        service_registry=service_registry,
        check_interval=5.0,
        enable_auto_optimization=enable_auto_optimization,
        enable_gpu_monitoring=True
    )


async def monitor_resources_once() -> ResourceMetrics:
    """
    Perform a one-time resource monitoring check.
    
    Returns:
        ResourceMetrics: Current system resource metrics
    """
    monitor = ResourceMonitor(enable_auto_optimization=False)
    return await monitor.monitor_system_resources()


def optimize_memory_now() -> None:
    """
    Perform immediate memory optimization.
    
    This is a convenience function for one-time memory cleanup.
    """
    monitor = ResourceMonitor(enable_auto_optimization=False)
    monitor.optimize_memory_usage()