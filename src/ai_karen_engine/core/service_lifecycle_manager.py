"""
Service Lifecycle Manager for Startup Optimization.

This module implements comprehensive service lifecycle management with essential-only startup,
dependency-based sequencing, idle service detection, graceful shutdown, and service consolidation.
"""

import asyncio
import logging
import time
import weakref
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Union, Tuple
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

from .service_classification import (
    ServiceConfig, ServiceClassification, DeploymentMode,
    ServiceConfigurationLoader, DependencyGraphAnalyzer
)
from .classified_service_registry import ClassifiedServiceRegistry, ServiceLifecycleState
from .lazy_loading_controller import LazyLoadingController

logger = logging.getLogger(__name__)


class StartupMode(str, Enum):
    """Startup modes for different optimization levels."""
    ESSENTIAL_ONLY = "essential_only"    # Only essential services
    FAST_START = "fast_start"           # Essential + critical optional
    NORMAL = "normal"                   # All enabled services
    FULL = "full"                       # All services including disabled


class ConsolidationStrategy(str, Enum):
    """Strategies for service consolidation."""
    MEMORY_BASED = "memory_based"       # Consolidate based on memory usage
    FUNCTIONAL = "functional"           # Consolidate by functionality
    DEPENDENCY = "dependency"           # Consolidate by dependency relationships
    HYBRID = "hybrid"                   # Combination of strategies


@dataclass
class ServiceMetrics:
    """Metrics for service performance tracking."""
    startup_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_accessed: Optional[float] = None
    access_count: int = 0
    idle_time: float = 0.0
    suspension_count: int = 0
    consolidation_savings_mb: float = 0.0


@dataclass
class ConsolidationGroup:
    """Information about a service consolidation group."""
    name: str
    services: List[str]
    strategy: ConsolidationStrategy
    estimated_memory_savings_mb: float
    consolidated_instance: Optional[Any] = None
    active: bool = False


@dataclass
class StartupSequence:
    """Represents a service startup sequence with timing and dependencies."""
    services: List[str]
    estimated_time_seconds: float
    parallel_groups: List[List[str]]
    critical_path: List[str]


class ServiceLifecycleManager:
    """
    Comprehensive service lifecycle manager for startup optimization.
    
    Manages service startup sequencing, idle detection, graceful shutdown,
    and service consolidation to optimize system performance.
    """
    
    def __init__(
        self,
        registry: ClassifiedServiceRegistry,
        lazy_controller: Optional[LazyLoadingController] = None,
        startup_mode: StartupMode = StartupMode.FAST_START,
        idle_timeout_seconds: int = 300,
        enable_consolidation: bool = True
    ):
        """
        Initialize the service lifecycle manager.
        
        Args:
            registry: Classified service registry
            lazy_controller: Optional lazy loading controller
            startup_mode: Default startup mode
            idle_timeout_seconds: Default idle timeout for services
            enable_consolidation: Whether to enable service consolidation
        """
        self.registry = registry
        self.lazy_controller = lazy_controller or LazyLoadingController(registry)
        self.startup_mode = startup_mode
        self.idle_timeout_seconds = idle_timeout_seconds
        self.enable_consolidation = enable_consolidation
        
        # Service lifecycle state
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.consolidation_groups: Dict[str, ConsolidationGroup] = {}
        self.startup_sequences: Dict[StartupMode, StartupSequence] = {}
        
        # Monitoring and management
        self.idle_monitor_task: Optional[asyncio.Task] = None
        self.resource_monitor_task: Optional[asyncio.Task] = None
        self.monitor_interval = 30  # seconds
        self.shutdown_in_progress = False
        
        # Performance tracking
        self.performance_metrics = {
            "startup_time_saved_seconds": 0.0,
            "memory_saved_mb": 0.0,
            "services_consolidated": 0,
            "services_suspended": 0,
            "graceful_shutdowns": 0,
            "forced_shutdowns": 0,
        }
        
        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="lifecycle")
        
        self._initialize_service_metrics()
        self._calculate_startup_sequences()
        
        logger.info(f"Initialized ServiceLifecycleManager with mode: {startup_mode.value}")
    
    def _initialize_service_metrics(self) -> None:
        """Initialize metrics for all registered services."""
        for service_name in self.registry.classified_services:
            self.service_metrics[service_name] = ServiceMetrics()
    
    def _calculate_startup_sequences(self) -> None:
        """Calculate optimal startup sequences for different modes."""
        analyzer = self.registry.dependency_analyzer
        
        for mode in StartupMode:
            services = self._get_services_for_startup_mode(mode)
            sequence = self._optimize_startup_sequence(services, analyzer)
            self.startup_sequences[mode] = sequence
            
            logger.debug(f"Calculated startup sequence for {mode.value}: {len(sequence.services)} services")
    
    def _get_services_for_startup_mode(self, mode: StartupMode) -> List[str]:
        """Get list of services to start for a given startup mode."""
        all_services = list(self.registry.classified_services.keys())
        
        if mode == StartupMode.ESSENTIAL_ONLY:
            return [
                name for name, info in self.registry.classified_services.items()
                if (info.config.classification == ServiceClassification.ESSENTIAL and 
                    info.config.enabled)
            ]
        elif mode == StartupMode.FAST_START:
            # Essential + high-priority optional services
            services = []
            for name, info in self.registry.classified_services.items():
                if not info.config.enabled:
                    continue
                if info.config.classification == ServiceClassification.ESSENTIAL:
                    services.append(name)
                elif (info.config.classification == ServiceClassification.OPTIONAL and 
                      info.config.startup_priority <= 50):
                    services.append(name)
            return services
        elif mode == StartupMode.NORMAL:
            return [
                name for name, info in self.registry.classified_services.items()
                if info.config.enabled
            ]
        else:  # FULL
            return all_services
    
    def _optimize_startup_sequence(
        self, 
        services: List[str], 
        analyzer: DependencyGraphAnalyzer
    ) -> StartupSequence:
        """Optimize startup sequence for parallel execution where possible."""
        # Get dependency-ordered sequence
        full_order = analyzer.get_startup_order()
        filtered_order = [s for s in full_order if s in services]
        
        # Calculate parallel groups (services that can start simultaneously)
        parallel_groups = []
        remaining_services = set(filtered_order)
        
        while remaining_services:
            # Find services with no unmet dependencies in remaining set
            current_group = []
            for service in filtered_order:
                if service not in remaining_services:
                    continue
                
                service_info = self.registry.classified_services[service]
                dependencies = set(service_info.config.dependencies)
                unmet_deps = dependencies.intersection(remaining_services)
                
                if not unmet_deps:
                    current_group.append(service)
            
            if not current_group:
                # Break circular dependencies by taking the first remaining service
                current_group = [next(iter(remaining_services))]
                logger.warning(f"Breaking potential circular dependency with service: {current_group[0]}")
            
            parallel_groups.append(current_group)
            remaining_services -= set(current_group)
        
        # Estimate startup time (assuming parallel execution within groups)
        estimated_time = 0.0
        for group in parallel_groups:
            # Take the maximum estimated startup time in the group
            group_time = max(
                self._estimate_service_startup_time(service) 
                for service in group
            )
            estimated_time += group_time
        
        # Identify critical path (longest dependency chain)
        critical_path = self._find_critical_path(filtered_order, analyzer)
        
        return StartupSequence(
            services=filtered_order,
            estimated_time_seconds=estimated_time,
            parallel_groups=parallel_groups,
            critical_path=critical_path
        )
    
    def _estimate_service_startup_time(self, service_name: str) -> float:
        """Estimate startup time for a service based on classification and complexity."""
        if service_name not in self.registry.classified_services:
            return 1.0
        
        config = self.registry.classified_services[service_name].config
        
        # Base time by classification
        base_times = {
            ServiceClassification.ESSENTIAL: 0.5,
            ServiceClassification.OPTIONAL: 2.0,
            ServiceClassification.BACKGROUND: 1.0,
        }
        
        base_time = base_times.get(config.classification, 1.0)
        
        # Adjust for dependencies (more dependencies = longer startup)
        dependency_factor = 1 + (len(config.dependencies) * 0.2)
        
        # Adjust for resource requirements
        resource_factor = 1.0
        if config.resource_requirements.memory_mb:
            # More memory = potentially longer startup
            resource_factor += config.resource_requirements.memory_mb / 1000
        
        return base_time * dependency_factor * resource_factor
    
    def _find_critical_path(
        self, 
        services: List[str], 
        analyzer: DependencyGraphAnalyzer
    ) -> List[str]:
        """Find the critical path (longest dependency chain) in the startup sequence."""
        # Build dependency graph for the given services
        service_deps = {}
        for service in services:
            if service in self.registry.classified_services:
                config = self.registry.classified_services[service].config
                service_deps[service] = [
                    dep for dep in config.dependencies if dep in services
                ]
        
        # Find longest path using DFS
        def dfs_longest_path(service: str, visited: Set[str]) -> List[str]:
            if service in visited:
                return []  # Avoid cycles
            
            visited.add(service)
            longest_path = [service]
            max_length = 0
            
            for dep in service_deps.get(service, []):
                dep_path = dfs_longest_path(dep, visited.copy())
                if len(dep_path) > max_length:
                    max_length = len(dep_path)
                    longest_path = [service] + dep_path
            
            return longest_path
        
        # Find the longest path starting from any service
        critical_path = []
        for service in services:
            path = dfs_longest_path(service, set())
            if len(path) > len(critical_path):
                critical_path = path
        
        return critical_path
    
    async def start_essential_services(self) -> Dict[str, str]:
        """
        Start only essential services for fast startup.
        
        Returns:
            Dictionary mapping service names to their status
        """
        logger.info("Starting essential services only...")
        start_time = time.time()
        
        sequence = self.startup_sequences[StartupMode.ESSENTIAL_ONLY]
        results = await self._execute_startup_sequence(sequence)
        
        startup_time = time.time() - start_time
        self.performance_metrics["startup_time_saved_seconds"] += max(0, 
            self.startup_sequences[StartupMode.NORMAL].estimated_time_seconds - startup_time
        )
        
        logger.info(f"Essential services startup completed in {startup_time:.2f}s")
        
        # Start monitoring tasks
        await self._start_monitoring_tasks()
        
        return results
    
    async def start_services_by_mode(self, mode: StartupMode) -> Dict[str, str]:
        """
        Start services according to the specified startup mode.
        
        Args:
            mode: Startup mode to use
            
        Returns:
            Dictionary mapping service names to their status
        """
        logger.info(f"Starting services in {mode.value} mode...")
        start_time = time.time()
        
        if mode not in self.startup_sequences:
            self._calculate_startup_sequences()
        
        sequence = self.startup_sequences[mode]
        results = await self._execute_startup_sequence(sequence)
        
        startup_time = time.time() - start_time
        logger.info(f"Service startup ({mode.value}) completed in {startup_time:.2f}s")
        
        # Start monitoring if not already running
        await self._start_monitoring_tasks()
        
        return results
    
    async def _execute_startup_sequence(self, sequence: StartupSequence) -> Dict[str, str]:
        """Execute a startup sequence with parallel execution where possible."""
        results = {}
        
        logger.info(f"Executing startup sequence: {len(sequence.parallel_groups)} parallel groups")
        
        for group_index, group in enumerate(sequence.parallel_groups):
            logger.debug(f"Starting group {group_index + 1}: {group}")
            
            # Start all services in the group concurrently
            group_tasks = []
            for service_name in group:
                task = asyncio.create_task(self._start_single_service(service_name))
                group_tasks.append((service_name, task))
            
            # Wait for all services in the group to complete
            for service_name, task in group_tasks:
                try:
                    status = await task
                    results[service_name] = status
                except Exception as e:
                    logger.error(f"Failed to start service {service_name}: {e}")
                    results[service_name] = "error"
        
        return results
    
    async def _start_single_service(self, service_name: str) -> str:
        """Start a single service and update metrics."""
        start_time = time.time()
        
        try:
            # Use lazy loading controller if available
            if self.lazy_controller:
                await self.lazy_controller.get_service(service_name)
            else:
                await self.registry.load_service_on_demand(service_name)
            
            # Update metrics
            startup_time = time.time() - start_time
            if service_name in self.service_metrics:
                self.service_metrics[service_name].startup_time = startup_time
                self.service_metrics[service_name].last_accessed = time.time()
            
            logger.debug(f"Started service {service_name} in {startup_time:.2f}s")
            return "ready"
            
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            return "error"
    
    async def detect_idle_services(self) -> List[str]:
        """
        Detect services that have been idle for too long.
        
        Returns:
            List of idle service names
        """
        idle_services = []
        current_time = time.time()
        
        for service_name, classified_info in self.registry.classified_services.items():
            config = classified_info.config
            
            # Skip essential services
            if config.classification == ServiceClassification.ESSENTIAL:
                continue
            
            # Check if service is active
            if classified_info.lifecycle_state != ServiceLifecycleState.ACTIVE:
                continue
            
            # Determine idle timeout
            idle_timeout = config.idle_timeout or self.idle_timeout_seconds
            
            # Check last access time
            metrics = self.service_metrics.get(service_name)
            if metrics and metrics.last_accessed:
                idle_time = current_time - metrics.last_accessed
                if idle_time >= idle_timeout:
                    idle_services.append(service_name)
                    metrics.idle_time = idle_time
        
        return idle_services
    
    async def suspend_idle_services(self) -> List[str]:
        """
        Suspend services that have been idle for too long.
        
        Returns:
            List of suspended service names
        """
        idle_services = await self.detect_idle_services()
        suspended_services = []
        
        for service_name in idle_services:
            try:
                await self._suspend_service(service_name)
                suspended_services.append(service_name)
                self.performance_metrics["services_suspended"] += 1
            except Exception as e:
                logger.error(f"Failed to suspend idle service {service_name}: {e}")
        
        if suspended_services:
            logger.info(f"Suspended {len(suspended_services)} idle services: {suspended_services}")
        
        return suspended_services
    
    async def _suspend_service(self, service_name: str) -> None:
        """Suspend a service to free up resources."""
        logger.debug(f"Suspending service: {service_name}")
        
        # Update metrics before suspension
        if service_name in self.service_metrics:
            metrics = self.service_metrics[service_name]
            metrics.suspension_count += 1
            
            # Estimate memory savings
            if service_name in self.registry.classified_services:
                config = self.registry.classified_services[service_name].config
                if config.resource_requirements.memory_mb:
                    metrics.consolidation_savings_mb += config.resource_requirements.memory_mb
                    self.performance_metrics["memory_saved_mb"] += config.resource_requirements.memory_mb
        
        # Use registry's suspension mechanism
        await self.registry._suspend_service(service_name)
        
        # Force garbage collection to free memory
        gc.collect()
    
    async def shutdown_service_gracefully(
        self, 
        service_name: str, 
        timeout_seconds: Optional[float] = None
    ) -> bool:
        """
        Shutdown a service gracefully with proper resource cleanup.
        
        Args:
            service_name: Name of the service to shutdown
            timeout_seconds: Timeout for graceful shutdown
            
        Returns:
            True if shutdown was successful, False otherwise
        """
        if service_name not in self.registry.classified_services:
            logger.warning(f"Service {service_name} not found for shutdown")
            return False
        
        config = self.registry.classified_services[service_name].config
        timeout = timeout_seconds or config.graceful_shutdown_timeout
        
        logger.info(f"Gracefully shutting down service: {service_name}")
        
        try:
            # Get service instance if it exists
            if service_name in self.registry._instances:
                instance = self.registry._instances[service_name]
                
                # Call shutdown method if available
                if hasattr(instance, 'shutdown'):
                    shutdown_func = getattr(instance, 'shutdown')
                    
                    if asyncio.iscoroutinefunction(shutdown_func):
                        await asyncio.wait_for(shutdown_func(), timeout=timeout)
                    else:
                        # Run in executor to avoid blocking
                        await asyncio.get_event_loop().run_in_executor(
                            self.executor, shutdown_func
                        )
                
                # Call cleanup method if available
                if hasattr(instance, 'cleanup'):
                    cleanup_func = getattr(instance, 'cleanup')
                    
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await asyncio.wait_for(cleanup_func(), timeout=timeout)
                    else:
                        await asyncio.get_event_loop().run_in_executor(
                            self.executor, cleanup_func
                        )
                
                # Remove from registry
                del self.registry._instances[service_name]
            
            # Update service state
            classified_info = self.registry.classified_services[service_name]
            classified_info.lifecycle_state = ServiceLifecycleState.SHUTDOWN
            
            # Update metrics
            self.performance_metrics["graceful_shutdowns"] += 1
            
            logger.info(f"Successfully shutdown service: {service_name}")
            return True
            
        except asyncio.TimeoutError:
            logger.warning(f"Graceful shutdown timeout for service {service_name}, forcing shutdown")
            return await self._force_shutdown_service(service_name)
        except Exception as e:
            logger.error(f"Error during graceful shutdown of {service_name}: {e}")
            return await self._force_shutdown_service(service_name)
    
    async def _force_shutdown_service(self, service_name: str) -> bool:
        """Force shutdown a service that didn't respond to graceful shutdown."""
        try:
            # Remove from registry instances
            if service_name in self.registry._instances:
                del self.registry._instances[service_name]
            
            # Update service state
            if service_name in self.registry.classified_services:
                classified_info = self.registry.classified_services[service_name]
                classified_info.lifecycle_state = ServiceLifecycleState.SHUTDOWN
            
            # Update metrics
            self.performance_metrics["forced_shutdowns"] += 1
            
            logger.warning(f"Force shutdown service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to force shutdown service {service_name}: {e}")
            return False
    
    def identify_consolidation_opportunities(self) -> Dict[str, ConsolidationGroup]:
        """
        Identify services that can be consolidated to reduce resource usage.
        
        Returns:
            Dictionary mapping group names to consolidation opportunities
        """
        opportunities = {}
        
        # Get consolidation groups from dependency analyzer
        analyzer_groups = self.registry.dependency_analyzer.get_consolidation_groups()
        
        for group_name, service_names in analyzer_groups.items():
            # Calculate potential memory savings
            total_memory = 0
            for service_name in service_names:
                if service_name in self.registry.classified_services:
                    config = self.registry.classified_services[service_name].config
                    if config.resource_requirements.memory_mb:
                        total_memory += config.resource_requirements.memory_mb
            
            # Estimate 20-30% memory savings from consolidation
            estimated_savings = total_memory * 0.25
            
            opportunities[group_name] = ConsolidationGroup(
                name=group_name,
                services=service_names,
                strategy=ConsolidationStrategy.FUNCTIONAL,
                estimated_memory_savings_mb=estimated_savings
            )
        
        # Add memory-based consolidation opportunities
        self._identify_memory_based_consolidation(opportunities)
        
        # Add dependency-based consolidation opportunities
        self._identify_dependency_based_consolidation(opportunities)
        
        return opportunities
    
    def _identify_memory_based_consolidation(self, opportunities: Dict[str, ConsolidationGroup]) -> None:
        """Identify consolidation opportunities based on memory usage patterns."""
        # Group services by similar memory requirements
        memory_groups = {}
        
        for service_name, classified_info in self.registry.classified_services.items():
            config = classified_info.config
            memory_mb = config.resource_requirements.memory_mb or 0
            
            # Group by memory ranges
            if memory_mb < 64:
                group_key = "low_memory"
            elif memory_mb < 256:
                group_key = "medium_memory"
            else:
                group_key = "high_memory"
            
            if group_key not in memory_groups:
                memory_groups[group_key] = []
            memory_groups[group_key].append(service_name)
        
        # Create consolidation opportunities for groups with multiple services
        for group_key, services in memory_groups.items():
            if len(services) >= 3:  # Only consolidate if 3+ services
                total_memory = sum(
                    self.registry.classified_services[s].config.resource_requirements.memory_mb or 0
                    for s in services
                )
                
                group_name = f"memory_consolidation_{group_key}"
                if group_name not in opportunities:
                    opportunities[group_name] = ConsolidationGroup(
                        name=group_name,
                        services=services,
                        strategy=ConsolidationStrategy.MEMORY_BASED,
                        estimated_memory_savings_mb=total_memory * 0.15  # 15% savings
                    )
    
    def _identify_dependency_based_consolidation(self, opportunities: Dict[str, ConsolidationGroup]) -> None:
        """Identify consolidation opportunities based on dependency relationships."""
        # Find services that are frequently used together
        co_usage_groups = {}
        
        if self.lazy_controller:
            usage_patterns = self.lazy_controller.usage_patterns
            
            for service_name, pattern in usage_patterns.items():
                if len(pattern.common_co_accessed_services) >= 2:
                    # Create a group key based on sorted co-accessed services
                    group_services = sorted([service_name] + list(pattern.common_co_accessed_services))
                    group_key = "_".join(group_services[:3])  # Limit key length
                    
                    if group_key not in co_usage_groups:
                        co_usage_groups[group_key] = set()
                    co_usage_groups[group_key].update(group_services)
        
        # Create consolidation opportunities
        for group_key, services in co_usage_groups.items():
            if len(services) >= 2:
                services_list = list(services)
                total_memory = sum(
                    self.registry.classified_services[s].config.resource_requirements.memory_mb or 0
                    for s in services_list
                    if s in self.registry.classified_services
                )
                
                group_name = f"dependency_consolidation_{group_key}"
                if group_name not in opportunities:
                    opportunities[group_name] = ConsolidationGroup(
                        name=group_name,
                        services=services_list,
                        strategy=ConsolidationStrategy.DEPENDENCY,
                        estimated_memory_savings_mb=total_memory * 0.2  # 20% savings
                    )
    
    async def consolidate_services(self, group: ConsolidationGroup) -> bool:
        """
        Consolidate a group of services into a single process.
        
        Args:
            group: Consolidation group to process
            
        Returns:
            True if consolidation was successful, False otherwise
        """
        if not self.enable_consolidation:
            logger.warning("Service consolidation is disabled")
            return False
        
        logger.info(f"Consolidating service group: {group.name} ({len(group.services)} services)")
        
        try:
            # Create consolidated service wrapper
            consolidated_instance = ConsolidatedServiceWrapper(
                group_name=group.name,
                service_names=group.services,
                registry=self.registry
            )
            
            # Initialize the consolidated service
            await consolidated_instance.initialize()
            
            # Update group information
            group.consolidated_instance = consolidated_instance
            group.active = True
            self.consolidation_groups[group.name] = group
            
            # Update metrics
            self.performance_metrics["services_consolidated"] += len(group.services)
            self.performance_metrics["memory_saved_mb"] += group.estimated_memory_savings_mb
            
            logger.info(f"Successfully consolidated {len(group.services)} services in group {group.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to consolidate service group {group.name}: {e}")
            return False
    
    async def _start_monitoring_tasks(self) -> None:
        """Start background monitoring tasks."""
        if self.idle_monitor_task is None:
            self.idle_monitor_task = asyncio.create_task(self._idle_monitoring_loop())
        
        if self.resource_monitor_task is None:
            self.resource_monitor_task = asyncio.create_task(self._resource_monitoring_loop())
        
        logger.info("Started service lifecycle monitoring tasks")
    
    async def _idle_monitoring_loop(self) -> None:
        """Background task to monitor and suspend idle services."""
        logger.info("Started idle service monitoring")
        
        try:
            while not self.shutdown_in_progress:
                await asyncio.sleep(self.monitor_interval)
                
                try:
                    await self.suspend_idle_services()
                except Exception as e:
                    logger.error(f"Error in idle monitoring: {e}")
                
        except asyncio.CancelledError:
            logger.info("Idle monitoring stopped")
        except Exception as e:
            logger.error(f"Unexpected error in idle monitoring: {e}")
    
    async def _resource_monitoring_loop(self) -> None:
        """Background task to monitor resource usage and update metrics."""
        logger.info("Started resource monitoring")
        
        try:
            while not self.shutdown_in_progress:
                await asyncio.sleep(self.monitor_interval)
                
                try:
                    await self._update_resource_metrics()
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
                
        except asyncio.CancelledError:
            logger.info("Resource monitoring stopped")
        except Exception as e:
            logger.error(f"Unexpected error in resource monitoring: {e}")
    
    async def _update_resource_metrics(self) -> None:
        """Update resource usage metrics for all services."""
        try:
            # Get system-wide metrics
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            # Update metrics for active services
            for service_name, classified_info in self.registry.classified_services.items():
                if classified_info.lifecycle_state == ServiceLifecycleState.ACTIVE:
                    if service_name in self.service_metrics:
                        metrics = self.service_metrics[service_name]
                        
                        # Estimate per-service resource usage (simplified)
                        config = classified_info.config
                        estimated_memory = config.resource_requirements.memory_mb or 64
                        
                        metrics.memory_usage_mb = estimated_memory
                        metrics.cpu_usage_percent = cpu_percent / len(self.registry._instances) if self.registry._instances else 0
                        
        except Exception as e:
            logger.warning(f"Failed to update resource metrics: {e}")
    
    async def shutdown_all_services(self, timeout_seconds: float = 30.0) -> Dict[str, bool]:
        """
        Shutdown all services gracefully in proper dependency order.
        
        Args:
            timeout_seconds: Total timeout for all shutdowns
            
        Returns:
            Dictionary mapping service names to shutdown success status
        """
        logger.info("Shutting down all services...")
        self.shutdown_in_progress = True
        
        # Stop monitoring tasks
        if self.idle_monitor_task:
            self.idle_monitor_task.cancel()
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
        
        # Get shutdown order (reverse of startup order)
        shutdown_order = self.registry.dependency_analyzer.get_shutdown_order()
        
        # Filter to only include active services
        active_services = [
            name for name in shutdown_order
            if (name in self.registry._instances and 
                name in self.registry.classified_services)
        ]
        
        results = {}
        per_service_timeout = timeout_seconds / len(active_services) if active_services else timeout_seconds
        
        # Shutdown services in order
        for service_name in active_services:
            try:
                success = await self.shutdown_service_gracefully(service_name, per_service_timeout)
                results[service_name] = success
            except Exception as e:
                logger.error(f"Error shutting down service {service_name}: {e}")
                results[service_name] = False
        
        # Shutdown consolidated services
        for group in self.consolidation_groups.values():
            if group.active and group.consolidated_instance:
                try:
                    await group.consolidated_instance.shutdown()
                    group.active = False
                except Exception as e:
                    logger.error(f"Error shutting down consolidated group {group.name}: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        successful_shutdowns = sum(1 for success in results.values() if success)
        logger.info(f"Shutdown complete: {successful_shutdowns}/{len(results)} services shutdown successfully")
        
        return results
    
    def get_lifecycle_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive lifecycle management report.
        
        Returns:
            Dictionary with lifecycle statistics and metrics
        """
        # Calculate current statistics
        total_services = len(self.registry.classified_services)
        active_services = sum(
            1 for info in self.registry.classified_services.values()
            if info.lifecycle_state == ServiceLifecycleState.ACTIVE
        )
        suspended_services = sum(
            1 for info in self.registry.classified_services.values()
            if info.lifecycle_state == ServiceLifecycleState.SUSPENDED
        )
        
        report = {
            "startup_mode": self.startup_mode.value,
            "total_services": total_services,
            "active_services": active_services,
            "suspended_services": suspended_services,
            "consolidation_enabled": self.enable_consolidation,
            "performance_metrics": self.performance_metrics.copy(),
            "startup_sequences": {
                mode.value: {
                    "service_count": len(seq.services),
                    "estimated_time_seconds": seq.estimated_time_seconds,
                    "parallel_groups": len(seq.parallel_groups),
                    "critical_path_length": len(seq.critical_path)
                }
                for mode, seq in self.startup_sequences.items()
            },
            "consolidation_groups": {
                name: {
                    "services": group.services,
                    "strategy": group.strategy.value,
                    "estimated_savings_mb": group.estimated_memory_savings_mb,
                    "active": group.active
                }
                for name, group in self.consolidation_groups.items()
            },
            "service_metrics": {
                name: {
                    "startup_time": metrics.startup_time,
                    "memory_usage_mb": metrics.memory_usage_mb,
                    "cpu_usage_percent": metrics.cpu_usage_percent,
                    "access_count": metrics.access_count,
                    "idle_time": metrics.idle_time,
                    "suspension_count": metrics.suspension_count
                }
                for name, metrics in self.service_metrics.items()
            }
        }
        
        return report


class ConsolidatedServiceWrapper:
    """
    Wrapper for consolidated services that provides a unified interface.
    
    This class manages multiple services as a single consolidated unit,
    providing transparent access to individual service methods while
    optimizing resource usage.
    """
    
    def __init__(
        self,
        group_name: str,
        service_names: List[str],
        registry: ClassifiedServiceRegistry
    ):
        """
        Initialize the consolidated service wrapper.
        
        Args:
            group_name: Name of the consolidation group
            service_names: List of service names to consolidate
            registry: Service registry for accessing services
        """
        self.group_name = group_name
        self.service_names = service_names
        self.registry = registry
        self.service_instances: Dict[str, Any] = {}
        self.initialized = False
        
        logger.info(f"Created consolidated service wrapper: {group_name}")
    
    async def initialize(self) -> None:
        """Initialize all services in the consolidation group."""
        logger.info(f"Initializing consolidated service group: {self.group_name}")
        
        for service_name in self.service_names:
            try:
                instance = await self.registry.load_service_on_demand(service_name)
                self.service_instances[service_name] = instance
                logger.debug(f"Loaded service {service_name} into consolidated group")
            except Exception as e:
                logger.error(f"Failed to load service {service_name} in consolidated group: {e}")
        
        self.initialized = True
        logger.info(f"Consolidated service group {self.group_name} initialized with {len(self.service_instances)} services")
    
    def get_service(self, service_name: str) -> Any:
        """Get a service instance from the consolidated group."""
        if not self.initialized:
            raise RuntimeError(f"Consolidated service group {self.group_name} not initialized")
        
        if service_name not in self.service_instances:
            raise ValueError(f"Service {service_name} not found in consolidated group {self.group_name}")
        
        return self.service_instances[service_name]
    
    async def shutdown(self) -> None:
        """Shutdown all services in the consolidated group."""
        logger.info(f"Shutting down consolidated service group: {self.group_name}")
        
        for service_name, instance in self.service_instances.items():
            try:
                if hasattr(instance, 'shutdown'):
                    if asyncio.iscoroutinefunction(instance.shutdown):
                        await instance.shutdown()
                    else:
                        instance.shutdown()
                logger.debug(f"Shutdown service {service_name} in consolidated group")
            except Exception as e:
                logger.error(f"Error shutting down service {service_name} in consolidated group: {e}")
        
        self.service_instances.clear()
        self.initialized = False
        logger.info(f"Consolidated service group {self.group_name} shutdown complete")