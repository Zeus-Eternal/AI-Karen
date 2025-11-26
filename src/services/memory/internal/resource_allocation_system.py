"""
Resource Allocation System for Intelligent Response Optimization

This module optimizes resource allocation based on query requirements,
system state, and processing priorities to ensure efficient resource
utilization while maintaining performance targets.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import psutil
import threading
import time

from ...internal.query_analyzer import QueryAnalysis, ComplexityLevel, Priority
from ...internal.response_strategy_engine import ResponseStrategy, ProcessingMode

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of system resources"""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK_IO = "disk_io"
    NETWORK = "network"


class AllocationStatus(Enum):
    """Resource allocation status"""
    ALLOCATED = "allocated"
    PENDING = "pending"
    DENIED = "denied"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass
class ResourceRequest:
    """Resource allocation request"""
    request_id: str
    query_id: str
    cpu_percent: float
    memory_mb: int
    gpu_percent: Optional[float]
    timeout_seconds: int
    priority: Priority
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class ResourceAllocation:
    """Active resource allocation"""
    allocation_id: str
    request: ResourceRequest
    allocated_cpu: float
    allocated_memory: int
    allocated_gpu: Optional[float]
    status: AllocationStatus
    allocated_at: datetime
    expires_at: datetime
    actual_usage: Dict[str, float]


@dataclass
class SystemResources:
    """Current system resource state"""
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_mb: int
    gpu_usage_percent: Optional[float]
    gpu_memory_available_mb: Optional[int]
    disk_io_percent: float
    network_io_mbps: float
    load_average: float
    active_processes: int
    timestamp: datetime


@dataclass
class ResourceLimits:
    """Resource limits and thresholds"""
    max_cpu_per_request: float
    max_memory_per_request: int
    max_concurrent_requests: int
    cpu_threshold_warning: float
    cpu_threshold_critical: float
    memory_threshold_warning: float
    memory_threshold_critical: float
    gpu_threshold_warning: Optional[float]
    gpu_threshold_critical: Optional[float]


class ResourceAllocationSystem:
    """
    Advanced resource allocation system that optimizes resource distribution
    based on query requirements, system state, and performance targets.
    """
    
    def __init__(self):
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_queue: List[ResourceRequest] = []
        self.resource_history: List[SystemResources] = []
        self.resource_limits = self._load_resource_limits()
        self.monitoring_active = False
        self.monitor_thread = None
        self._lock = threading.Lock()
        
        # Start resource monitoring
        self.start_monitoring()
    
    def _load_resource_limits(self) -> ResourceLimits:
        """Load resource limits and thresholds"""
        return ResourceLimits(
            max_cpu_per_request=5.0,  # 5% CPU per request (requirement)
            max_memory_per_request=500 * 1024 * 1024,  # 500MB per request
            max_concurrent_requests=10,
            cpu_threshold_warning=70.0,
            cpu_threshold_critical=85.0,
            memory_threshold_warning=75.0,
            memory_threshold_critical=90.0,
            gpu_threshold_warning=80.0,
            gpu_threshold_critical=95.0
        )
    
    def start_monitoring(self) -> None:
        """Start system resource monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
            logger.info("Resource monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system resource monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitor_resources(self) -> None:
        """Monitor system resources continuously"""
        while self.monitoring_active:
            try:
                resources = self._get_current_resources()
                
                with self._lock:
                    self.resource_history.append(resources)
                    # Keep only last 100 measurements
                    if len(self.resource_history) > 100:
                        self.resource_history.pop(0)
                
                # Check for resource pressure and cleanup expired allocations
                self._check_resource_pressure(resources)
                self._cleanup_expired_allocations()
                
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _get_current_resources(self) -> SystemResources:
        """Get current system resource usage"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            memory_available = memory.available // (1024 * 1024)  # Convert to MB
            
            # GPU usage (if available)
            gpu_usage = None
            gpu_memory_available = None
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    gpu_usage = gpu.load * 100
                    gpu_memory_available = gpu.memoryFree
            except ImportError:
                pass  # GPU monitoring not available
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_percent = 0  # Simplified for now
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_io_mbps = 0  # Simplified for now
            
            # Load average
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            
            # Active processes
            active_processes = len(psutil.pids())
            
            return SystemResources(
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_usage,
                memory_available_mb=memory_available,
                gpu_usage_percent=gpu_usage,
                gpu_memory_available_mb=gpu_memory_available,
                disk_io_percent=disk_io_percent,
                network_io_mbps=network_io_mbps,
                load_average=load_avg,
                active_processes=active_processes,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            # Return default values on error
            return SystemResources(
                cpu_usage_percent=50.0,
                memory_usage_percent=50.0,
                memory_available_mb=1000,
                gpu_usage_percent=None,
                gpu_memory_available_mb=None,
                disk_io_percent=0,
                network_io_mbps=0,
                load_average=1.0,
                active_processes=100,
                timestamp=datetime.utcnow()
            )
    
    async def allocate_resources(
        self,
        query_analysis: QueryAnalysis,
        response_strategy: ResponseStrategy,
        query_id: str
    ) -> Optional[ResourceAllocation]:
        """
        Allocate resources for query processing based on analysis and strategy
        
        Args:
            query_analysis: Query analysis results
            response_strategy: Determined response strategy
            query_id: Unique query identifier
            
        Returns:
            ResourceAllocation: Allocated resources or None if denied
        """
        try:
            # Create resource request
            request = ResourceRequest(
                request_id=f"req_{query_id}_{int(time.time())}",
                query_id=query_id,
                cpu_percent=response_strategy.resource_allocation.cpu_limit,
                memory_mb=response_strategy.resource_allocation.memory_limit // (1024 * 1024),
                gpu_percent=response_strategy.resource_allocation.gpu_allocation,
                timeout_seconds=response_strategy.resource_allocation.timeout_seconds,
                priority=query_analysis.processing_priority,
                created_at=datetime.utcnow(),
                metadata={
                    'complexity': query_analysis.complexity.value,
                    'content_type': query_analysis.content_type.value,
                    'processing_mode': response_strategy.processing_mode.value
                }
            )
            
            # Check if allocation is possible
            if not await self._can_allocate_resources(request):
                logger.warning(f"Resource allocation denied for query {query_id}")
                return None
            
            # Allocate resources
            allocation = await self._perform_allocation(request)
            
            with self._lock:
                self.active_allocations[allocation.allocation_id] = allocation
            
            logger.info(f"Resources allocated for query {query_id}: CPU {allocation.allocated_cpu}%, Memory {allocation.allocated_memory}MB")
            return allocation
            
        except Exception as e:
            logger.error(f"Error allocating resources for query {query_id}: {e}")
            return None
    
    async def _can_allocate_resources(self, request: ResourceRequest) -> bool:
        """Check if resources can be allocated for the request"""
        try:
            current_resources = self._get_current_resources()
            
            # Check CPU availability
            total_allocated_cpu = sum(alloc.allocated_cpu for alloc in self.active_allocations.values())
            if total_allocated_cpu + request.cpu_percent > self.resource_limits.max_cpu_per_request * self.resource_limits.max_concurrent_requests:
                return False
            
            # Check if system CPU usage is too high
            if current_resources.cpu_usage_percent > self.resource_limits.cpu_threshold_critical:
                # Only allow high priority requests
                if request.priority not in [Priority.URGENT, Priority.HIGH]:
                    return False
            
            # Check memory availability
            required_memory = request.memory_mb
            if required_memory > current_resources.memory_available_mb:
                return False
            
            # Check memory usage threshold
            if current_resources.memory_usage_percent > self.resource_limits.memory_threshold_critical:
                if request.priority not in [Priority.URGENT, Priority.HIGH]:
                    return False
            
            # Check concurrent request limit
            if len(self.active_allocations) >= self.resource_limits.max_concurrent_requests:
                # Only allow if higher priority than existing requests
                lowest_priority_allocation = min(
                    self.active_allocations.values(),
                    key=lambda x: self._get_priority_value(x.request.priority),
                    default=None
                )
                if lowest_priority_allocation and self._get_priority_value(request.priority) <= self._get_priority_value(lowest_priority_allocation.request.priority):
                    return False
            
            # Check GPU availability if requested
            if request.gpu_percent and current_resources.gpu_usage_percent:
                if current_resources.gpu_usage_percent > self.resource_limits.gpu_threshold_critical:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking resource availability: {e}")
            return False
    
    async def _perform_allocation(self, request: ResourceRequest) -> ResourceAllocation:
        """Perform the actual resource allocation"""
        try:
            allocation_id = f"alloc_{request.query_id}_{int(time.time())}"
            
            # Calculate actual allocation (may be less than requested based on system state)
            current_resources = self._get_current_resources()
            
            # Allocate CPU (ensure we don't exceed 5% per request)
            allocated_cpu = min(request.cpu_percent, self.resource_limits.max_cpu_per_request)
            
            # Allocate memory
            allocated_memory = min(request.memory_mb, current_resources.memory_available_mb // 2)  # Don't use more than half available
            
            # Allocate GPU if requested and available
            allocated_gpu = None
            if request.gpu_percent and current_resources.gpu_usage_percent is not None:
                allocated_gpu = min(request.gpu_percent, 50.0)  # Max 50% GPU per request
            
            # Set expiration time
            expires_at = datetime.utcnow() + timedelta(seconds=request.timeout_seconds)
            
            allocation = ResourceAllocation(
                allocation_id=allocation_id,
                request=request,
                allocated_cpu=allocated_cpu,
                allocated_memory=allocated_memory,
                allocated_gpu=allocated_gpu,
                status=AllocationStatus.ALLOCATED,
                allocated_at=datetime.utcnow(),
                expires_at=expires_at,
                actual_usage={}
            )
            
            return allocation
            
        except Exception as e:
            logger.error(f"Error performing allocation: {e}")
            raise
    
    def _get_priority_value(self, priority: Priority) -> int:
        """Get numeric value for priority comparison"""
        priority_values = {
            Priority.LOW: 1,
            Priority.NORMAL: 2,
            Priority.HIGH: 3,
            Priority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    async def release_resources(self, allocation_id: str) -> bool:
        """Release allocated resources"""
        try:
            with self._lock:
                if allocation_id in self.active_allocations:
                    allocation = self.active_allocations[allocation_id]
                    allocation.status = AllocationStatus.RELEASED
                    del self.active_allocations[allocation_id]
                    
                    logger.info(f"Resources released for allocation {allocation_id}")
                    return True
                else:
                    logger.warning(f"Allocation {allocation_id} not found for release")
                    return False
                    
        except Exception as e:
            logger.error(f"Error releasing resources for allocation {allocation_id}: {e}")
            return False
    
    async def update_resource_usage(self, allocation_id: str, usage_data: Dict[str, float]) -> None:
        """Update actual resource usage for an allocation"""
        try:
            with self._lock:
                if allocation_id in self.active_allocations:
                    allocation = self.active_allocations[allocation_id]
                    allocation.actual_usage.update(usage_data)
                    
                    # Check if usage exceeds allocation
                    if usage_data.get('cpu_percent', 0) > allocation.allocated_cpu * 1.2:  # 20% tolerance
                        logger.warning(f"CPU usage exceeded allocation for {allocation_id}")
                    
                    if usage_data.get('memory_mb', 0) > allocation.allocated_memory * 1.2:
                        logger.warning(f"Memory usage exceeded allocation for {allocation_id}")
                        
        except Exception as e:
            logger.error(f"Error updating resource usage for allocation {allocation_id}: {e}")
    
    def _check_resource_pressure(self, resources: SystemResources) -> None:
        """Check for resource pressure and take action"""
        try:
            # CPU pressure
            if resources.cpu_usage_percent > self.resource_limits.cpu_threshold_critical:
                logger.warning(f"Critical CPU usage: {resources.cpu_usage_percent}%")
                self._handle_cpu_pressure()
            elif resources.cpu_usage_percent > self.resource_limits.cpu_threshold_warning:
                logger.info(f"High CPU usage: {resources.cpu_usage_percent}%")
            
            # Memory pressure
            if resources.memory_usage_percent > self.resource_limits.memory_threshold_critical:
                logger.warning(f"Critical memory usage: {resources.memory_usage_percent}%")
                self._handle_memory_pressure()
            elif resources.memory_usage_percent > self.resource_limits.memory_threshold_warning:
                logger.info(f"High memory usage: {resources.memory_usage_percent}%")
            
            # GPU pressure
            if resources.gpu_usage_percent and self.resource_limits.gpu_threshold_critical:
                if resources.gpu_usage_percent > self.resource_limits.gpu_threshold_critical:
                    logger.warning(f"Critical GPU usage: {resources.gpu_usage_percent}%")
                    
        except Exception as e:
            logger.error(f"Error checking resource pressure: {e}")
    
    def _handle_cpu_pressure(self) -> None:
        """Handle high CPU usage by reducing allocations"""
        try:
            with self._lock:
                # Find lowest priority allocations to reduce or terminate
                low_priority_allocations = [
                    alloc for alloc in self.active_allocations.values()
                    if alloc.request.priority in [Priority.LOW, Priority.NORMAL]
                ]
                
                # Reduce CPU allocation for low priority requests
                for allocation in low_priority_allocations[:3]:  # Limit to 3 allocations
                    allocation.allocated_cpu *= 0.8  # Reduce by 20%
                    logger.info(f"Reduced CPU allocation for {allocation.allocation_id}")
                    
        except Exception as e:
            logger.error(f"Error handling CPU pressure: {e}")
    
    def _handle_memory_pressure(self) -> None:
        """Handle high memory usage"""
        try:
            with self._lock:
                # Find allocations that can be reduced
                reducible_allocations = [
                    alloc for alloc in self.active_allocations.values()
                    if alloc.allocated_memory > 100 * 1024 * 1024  # > 100MB
                ]
                
                # Reduce memory allocation
                for allocation in reducible_allocations[:2]:  # Limit to 2 allocations
                    allocation.allocated_memory = int(allocation.allocated_memory * 0.8)
                    logger.info(f"Reduced memory allocation for {allocation.allocation_id}")
                    
        except Exception as e:
            logger.error(f"Error handling memory pressure: {e}")
    
    def _cleanup_expired_allocations(self) -> None:
        """Clean up expired resource allocations"""
        try:
            now = datetime.utcnow()
            expired_allocations = []
            
            with self._lock:
                for allocation_id, allocation in list(self.active_allocations.items()):
                    if now > allocation.expires_at:
                        expired_allocations.append(allocation_id)
                        allocation.status = AllocationStatus.EXPIRED
                        del self.active_allocations[allocation_id]
            
            if expired_allocations:
                logger.info(f"Cleaned up {len(expired_allocations)} expired allocations")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired allocations: {e}")
    
    async def get_resource_statistics(self) -> Dict[str, Any]:
        """Get resource allocation statistics"""
        try:
            current_resources = self._get_current_resources()
            
            with self._lock:
                active_count = len(self.active_allocations)
                total_allocated_cpu = sum(alloc.allocated_cpu for alloc in self.active_allocations.values())
                total_allocated_memory = sum(alloc.allocated_memory for alloc in self.active_allocations.values())
                
                priority_distribution = {}
                for allocation in self.active_allocations.values():
                    priority = allocation.request.priority.value
                    priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
            
            return {
                'current_resources': {
                    'cpu_usage': current_resources.cpu_usage_percent,
                    'memory_usage': current_resources.memory_usage_percent,
                    'memory_available_mb': current_resources.memory_available_mb,
                    'gpu_usage': current_resources.gpu_usage_percent,
                    'load_average': current_resources.load_average
                },
                'allocations': {
                    'active_count': active_count,
                    'total_allocated_cpu': total_allocated_cpu,
                    'total_allocated_memory_mb': total_allocated_memory,
                    'priority_distribution': priority_distribution
                },
                'limits': {
                    'max_cpu_per_request': self.resource_limits.max_cpu_per_request,
                    'max_memory_per_request_mb': self.resource_limits.max_memory_per_request // (1024 * 1024),
                    'max_concurrent_requests': self.resource_limits.max_concurrent_requests
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting resource statistics: {e}")
            return {'error': str(e)}
    
    async def optimize_allocations(self) -> Dict[str, Any]:
        """Optimize current resource allocations"""
        try:
            optimizations_applied = []
            
            current_resources = self._get_current_resources()
            
            with self._lock:
                # Optimize CPU allocations
                if current_resources.cpu_usage_percent < 30:  # Low CPU usage
                    # Can increase allocations for high priority requests
                    high_priority_allocations = [
                        alloc for alloc in self.active_allocations.values()
                        if alloc.request.priority in [Priority.HIGH, Priority.URGENT]
                    ]
                    
                    for allocation in high_priority_allocations:
                        if allocation.allocated_cpu < self.resource_limits.max_cpu_per_request:
                            old_cpu = allocation.allocated_cpu
                            allocation.allocated_cpu = min(
                                allocation.allocated_cpu * 1.2,
                                self.resource_limits.max_cpu_per_request
                            )
                            optimizations_applied.append(f"Increased CPU for {allocation.allocation_id}: {old_cpu:.1f}% -> {allocation.allocated_cpu:.1f}%")
                
                # Optimize memory allocations
                if current_resources.memory_usage_percent < 50:  # Low memory usage
                    memory_constrained_allocations = [
                        alloc for alloc in self.active_allocations.values()
                        if alloc.allocated_memory < alloc.request.memory_mb
                    ]
                    
                    for allocation in memory_constrained_allocations[:2]:  # Limit optimizations
                        old_memory = allocation.allocated_memory
                        allocation.allocated_memory = min(
                            allocation.allocated_memory * 1.3,
                            allocation.request.memory_mb
                        )
                        optimizations_applied.append(f"Increased memory for {allocation.allocation_id}: {old_memory}MB -> {allocation.allocated_memory}MB")
            
            return {
                'optimizations_applied': optimizations_applied,
                'optimization_count': len(optimizations_applied),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing allocations: {e}")
            return {'error': str(e), 'optimizations_applied': []}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_monitoring()