"""
Enhanced Dependency Injection System

Provides hardened dependency management with lifecycle control, dependency resolution,
circuit breaking, and comprehensive error handling for service registry operations.
"""

import asyncio
import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, get_type_hints
from contextlib import asynccontextmanager, contextmanager
import inspect
import hashlib
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyScope(Enum):
    """Dependency lifecycle scope"""

    TRANSIENT = "transient"  # New instance each time
    SINGLETON = "singleton"  # Single instance for application lifetime
    REQUEST = "request"  # Single instance per request
    SCOPED = "scoped"  # Single instance per scope


class DependencyStatus(Enum):
    """Dependency health status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    DESTROYING = "destroying"


class CircuitBreakerState(Enum):
    """Circuit breaker state"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, no requests allowed
    HALF_OPEN = "half_open"  # Testing if service is restored


@dataclass
class DependencyDescriptor:
    """Dependency descriptor"""

    name: str
    implementation_type: Type
    interface_type: Optional[Type] = None
    scope: DependencyScope = DependencyScope.SINGLETON
    factory: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    lazy_init: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 3
    health_check_enabled: bool = True
    health_check_interval: int = 60

    def __post_init__(self):
        if self.interface_type is None:
            self.interface_type = self.implementation_type


@dataclass
class DependencyInstance:
    """Dependency instance with metadata"""

    descriptor: DependencyDescriptor
    instance: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    status: DependencyStatus = DependencyStatus.UNKNOWN
    error_count: int = 0
    last_error: Optional[str] = None
    health_check_passed: bool = True

    def is_expired(self) -> bool:
        """Check if instance should be recreated"""
        if self.descriptor.scope == DependencyScope.TRANSIENT:
            return True

        # Check for timeout-based expiration
        age = (datetime.now() - self.created_at).total_seconds()
        if age > self.descriptor.timeout_seconds:
            return True

        return False


@dataclass
class CircuitBreaker:
    """Circuit breaker for dependency protection"""

    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_requests: int = 3
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0
    last_success_time: Optional[datetime] = None

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.success_count < self.half_open_max_requests
        return False

    def record_failure(self):
        """Record a failure"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker {self.name} opened after {self.failure_count} failures"
            )

    def record_success(self):
        """Record a success"""
        self.success_count += 1
        self.last_success_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.half_open_max_requests:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(
                    f"Circuit breaker {self.name} closed after successful recovery"
                )

    def should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = (
                    datetime.now() - self.last_failure_time
                ).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        f"Circuit breaker {self.name} transitioning to half-open state"
                    )
                    return True
        return False


@dataclass
class DependencyHealthMetrics:
    """Health metrics for a dependency"""

    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_health_check: Optional[datetime] = None
    health_check_passed: bool = True
    error_rate: float = 0.0
    uptime_percentage: float = 100.0

    def update_request(self, success: bool, response_time: float):
        """Update metrics with request result"""
        self.total_requests += 1

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        # Update average response time
        if self.total_requests == 1:
            self.average_response_time = response_time
        else:
            self.average_response_time = (
                self.average_response_time * (self.total_requests - 1) + response_time
            ) / self.total_requests

        # Update error rate
        self.error_rate = (
            (self.failed_requests / self.total_requests) * 100
            if self.total_requests > 0
            else 0
        )

    def get_status(self) -> DependencyStatus:
        """Get dependency status based on metrics"""
        if self.total_requests == 0:
            return DependencyStatus.UNKNOWN

        if self.error_rate > 50:
            return DependencyStatus.UNHEALTHY
        elif self.error_rate > 10:
            return DependencyStatus.DEGRADED
        else:
            return DependencyStatus.HEALTHY


class DependencyResolver:
    """Resolves dependencies with proper injection"""

    def __init__(self, container: "DependencyContainer"):
        self.container = container
        self._resolution_stack: Set[str] = set()
        self._request_scope: Dict[str, Any] = {}

    def resolve(self, dependency_name: str) -> Any:
        """Resolve a dependency by name"""
        if dependency_name in self._resolution_stack:
            raise ValueError(f"Circular dependency detected: {dependency_name}")

        self._resolution_stack.add(dependency_name)

        try:
            return self._resolve_dependency(dependency_name)
        finally:
            self._resolution_stack.remove(dependency_name)

    def _resolve_dependency(self, dependency_name: str) -> Any:
        """Internal dependency resolution"""
        descriptor = self.container.get_descriptor(dependency_name)
        if not descriptor:
            raise ValueError(f"Dependency not found: {dependency_name}")

        # Check circuit breaker
        circuit_breaker = self.container.get_circuit_breaker(dependency_name)
        if circuit_breaker and not circuit_breaker.can_execute():
            raise ValueError(f"Circuit breaker open for dependency: {dependency_name}")

        # Get or create instance
        instance = self.container.get_instance(dependency_name)

        if instance is None or instance.is_expired():
            instance = self._create_instance(descriptor)
            self.container.set_instance(dependency_name, instance)

        # Update access tracking
        instance.last_accessed = datetime.now()
        instance.access_count += 1

        return instance.instance

    def _create_instance(self, descriptor: DependencyDescriptor) -> DependencyInstance:
        """Create a new dependency instance"""
        start_time = time.time()

        try:
            # Resolve dependencies first
            resolved_deps = {}
            for dep_name in descriptor.dependencies:
                resolved_deps[dep_name] = self.resolve(dep_name)

            # Merge configuration with dependencies for constructor
            constructor_args = {**resolved_deps}
            if descriptor.configuration:
                constructor_args.update(descriptor.configuration)

            # Create instance
            if descriptor.factory:
                instance = descriptor.factory(**constructor_args)
            else:
                instance = descriptor.implementation_type(**constructor_args)

            # Apply configuration if present
            if descriptor.configuration:
                self._apply_configuration(instance, descriptor.configuration)

            creation_time = time.time() - start_time

            logger.info(
                f"Created dependency instance: {descriptor.name} in {creation_time:.3f}s"
            )

            return DependencyInstance(
                descriptor=descriptor,
                instance=instance,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                status=DependencyStatus.HEALTHY,
            )

        except Exception as e:
            logger.error(f"Failed to create dependency {descriptor.name}: {e}")

            # Update circuit breaker
            circuit_breaker = self.container.get_circuit_breaker(descriptor.name)
            if circuit_breaker:
                circuit_breaker.record_failure()

            raise

    def _apply_configuration(self, instance: Any, configuration: Dict[str, Any]):
        """Apply configuration to instance"""
        for key, value in configuration.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
            else:
                logger.warning(
                    f"Configuration key {key} not found on {instance.__class__.__name__}"
                )

        # Special handling for container injection
        if hasattr(instance, "container") and instance.container is None:
            if "container" in configuration:
                instance.container = configuration["container"]
            else:
                # If no container provided, use self (the container creating the instance)
                instance.container = self


class DependencyContainer:
    """Main dependency injection container"""

    def __init__(self):
        self._descriptors: Dict[str, DependencyDescriptor] = {}
        self._instances: Dict[str, DependencyInstance] = {}
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._health_metrics: Dict[str, DependencyHealthMetrics] = {}
        self._resolver = DependencyResolver(self)
        self._lock = threading.RLock()
        self._running = False
        self._health_task: Optional[asyncio.Task] = None

        # Initialize with built-in services
        self._initialize_built_services()

    def _initialize_built_services(self):
        """Initialize built-in services"""
        # Circuit breaker service
        self.register(
            "circuit_breaker_manager",
            CircuitBreakerManager,
            scope=DependencyScope.SINGLETON,
            dependencies=[],  # Will be resolved with container reference
            configuration={"container": self},  # Pass container as configuration
        )

        # Health monitoring service
        self.register(
            "health_monitor", DependencyHealthMonitor, scope=DependencyScope.SINGLETON
        )

    def register(
        self,
        name: str,
        implementation_type: Type,
        interface_type: Optional[Type] = None,
        scope: DependencyScope = DependencyScope.SINGLETON,
        factory: Optional[Callable] = None,
        dependencies: List[str] = None,
        configuration: Dict[str, Any] = None,
        tags: Set[str] = None,
        lazy_init: bool = True,
        timeout_seconds: int = 30,
        retry_attempts: int = 3,
        health_check_enabled: bool = True,
        health_check_interval: int = 60,
    ):
        """Register a dependency"""
        descriptor = DependencyDescriptor(
            name=name,
            implementation_type=implementation_type,
            interface_type=interface_type,
            scope=scope,
            factory=factory,
            dependencies=dependencies or [],
            configuration=configuration or {},
            tags=tags or set(),
            lazy_init=lazy_init,
            timeout_seconds=timeout_seconds,
            retry_attempts=retry_attempts,
            health_check_enabled=health_check_enabled,
            health_check_interval=health_check_interval,
        )

        with self._lock:
            self._descriptors[name] = descriptor

            # Initialize circuit breaker
            self._circuit_breakers[name] = CircuitBreaker(name=name)

            # Initialize health metrics
            self._health_metrics[name] = DependencyHealthMetrics(name=name)

            # Eager initialization if requested
            if not lazy_init:
                try:
                    self.get_instance(name)
                except Exception as e:
                    logger.warning(f"Failed to eagerly initialize {name}: {e}")

        logger.info(f"Registered dependency: {name} -> {implementation_type.__name__}")

    def get_descriptor(self, name: str) -> Optional[DependencyDescriptor]:
        """Get dependency descriptor"""
        return self._descriptors.get(name)

    def get_instance(self, name: str) -> Optional[DependencyInstance]:
        """Get dependency instance"""
        with self._lock:
            return self._instances.get(name)

    def set_instance(self, name: str, instance: DependencyInstance):
        """Set dependency instance"""
        with self._lock:
            self._instances[name] = instance

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for dependency"""
        return self._circuit_breakers.get(name)

    def get_health_metrics(self, name: str) -> Optional[DependencyHealthMetrics]:
        """Get health metrics for dependency"""
        return self._health_metrics.get(name)

    def resolve(self, name: str) -> Any:
        """Resolve a dependency"""
        return self._resolver.resolve(name)

    def _create_instance(self, descriptor: DependencyDescriptor) -> DependencyInstance:
        """Create a new dependency instance"""
        return self._resolver._create_instance(descriptor)

    def create_scope(self) -> "ScopedContainer":
        """Create a new scoped container"""
        return ScopedContainer(self)

    async def start_health_monitoring(self):
        """Start health monitoring for all dependencies"""
        if self._running:
            return

        self._running = True
        self._health_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Dependency health monitoring started")

    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        logger.info("Dependency health monitoring stopped")

    async def _health_monitoring_loop(self):
        """Health monitoring loop"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all dependencies"""
        for name, descriptor in self._descriptors.items():
            if not descriptor.health_check_enabled:
                continue

            try:
                await self._check_dependency_health(name, descriptor)
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")

    async def _check_dependency_health(
        self, name: str, descriptor: DependencyDescriptor
    ):
        """Check health of a specific dependency"""
        start_time = time.time()

        try:
            # Try to resolve the dependency
            instance = self.get_instance(name)
            if instance is None:
                instance = DependencyInstance(
                    descriptor=descriptor,
                    instance=None,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                )
                self.set_instance(name, instance)

            # Perform health check
            if instance.instance and hasattr(instance.instance, "health_check"):
                health_result = instance.instance.health_check()
                instance.health_check_passed = health_result
            else:
                # Basic health check - just try to access the instance
                _ = str(instance.instance)
                instance.health_check_passed = True

            # Update metrics
            metrics = self.get_health_metrics(name)
            if metrics:
                metrics.last_health_check = datetime.now()
                metrics.health_check_passed = instance.health_check_passed

                response_time = time.time() - start_time
                metrics.update_request(True, response_time)

                # Update circuit breaker
                circuit_breaker = self.get_circuit_breaker(name)
                if circuit_breaker:
                    circuit_breaker.record_success()

                # Update instance status
                instance.status = metrics.get_status()

            logger.debug(f"Health check passed for {name}")

        except Exception as e:
            # Health check failed
            logger.warning(f"Health check failed for {name}: {e}")

            instance = self.get_instance(name)
            if instance:
                instance.status = DependencyStatus.UNHEALTHY
                instance.health_check_passed = False
                instance.last_error = str(e)
                instance.error_count += 1

            # Update metrics
            metrics = self.get_health_metrics(name)
            if metrics:
                metrics.last_health_check = datetime.now()
                metrics.health_check_passed = False

                response_time = time.time() - start_time
                metrics.update_request(False, response_time)

                # Update circuit breaker
                circuit_breaker = self.get_circuit_breaker(name)
                if circuit_breaker:
                    circuit_breaker.record_failure()

    def dispose(self):
        """Dispose all dependencies"""
        with self._lock:
            for name, instance in self._instances.items():
                try:
                    if hasattr(instance.instance, "dispose"):
                        instance.instance.dispose()
                    elif hasattr(instance.instance, "__del__"):
                        del instance.instance
                except Exception as e:
                    logger.error(f"Error disposing {name}: {e}")

            self._instances.clear()
            self._descriptors.clear()
            self._circuit_breakers.clear()
            self._health_metrics.clear()


class ScopedContainer:
    """Scoped dependency container for request-scoped dependencies"""

    def __init__(self, parent: DependencyContainer):
        self.parent = parent
        self._scoped_instances: Dict[str, DependencyInstance] = {}
        self._resolver = DependencyResolver(self)

    def resolve(self, name: str) -> Any:
        """Resolve dependency with scope support"""
        descriptor = self.parent.get_descriptor(name)
        if not descriptor:
            raise ValueError(f"Dependency not found: {name}")

        # Check scope
        if descriptor.scope == DependencyScope.SINGLETON:
            return self.parent.resolve(name)
        elif descriptor.scope == DependencyScope.REQUEST:
            return self._resolve_request_scoped(name)
        elif descriptor.scope == DependencyScope.SCOPED:
            return self._resolve_scoped(name)
        else:  # TRANSIENT
            return self._resolve_transient(name)

    def _resolve_request_scoped(self, name: str) -> Any:
        """Resolve request-scoped dependency"""
        if name not in self._scoped_instances:
            descriptor = self.parent.get_descriptor(name)
            instance = self._create_instance(descriptor)
            self._scoped_instances[name] = instance

        instance = self._scoped_instances[name]
        instance.last_accessed = datetime.now()
        instance.access_count += 1

        return instance.instance

    def _resolve_scoped(self, name: str) -> Any:
        """Resolve scoped dependency"""
        # For now, treat like singleton
        return self.parent.resolve(name)

    def _resolve_transient(self, name: str) -> Any:
        """Resolve transient dependency"""
        descriptor = self.parent.get_descriptor(name)
        instance = self._create_instance(descriptor)
        return instance.instance

    def _create_instance(self, descriptor: DependencyDescriptor) -> DependencyInstance:
        """Create instance using parent resolver"""
        # Temporarily add to parent instances
        old_resolver = self.parent._resolver
        self.parent._resolver = self._resolver

        try:
            instance = self.parent._create_instance(descriptor)
            return instance
        finally:
            self.parent._resolver = old_resolver

    def __enter__(self):
        """Enter context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        self.dispose()

    def dispose(self):
        """Dispose scoped instances"""
        for name, instance in self._scoped_instances.items():
            try:
                if hasattr(instance.instance, "dispose"):
                    instance.instance.dispose()
            except Exception as e:
                logger.error(f"Error disposing scoped {name}: {e}")

        self._scoped_instances.clear()


class CircuitBreakerManager:
    """Manages circuit breakers for dependencies"""

    def __init__(self, container: Optional[DependencyContainer] = None):
        self.container = container
        self._lock = threading.RLock()

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker for dependency"""
        return self.container.get_circuit_breaker(name)

    def reset_circuit_breaker(self, name: str):
        """Reset circuit breaker for dependency"""
        with self._lock:
            circuit_breaker = self.container.get_circuit_breaker(name)
            if circuit_breaker:
                circuit_breaker.state = CircuitBreakerState.CLOSED
                circuit_breaker.failure_count = 0
                circuit_breaker.success_count = 0
                logger.info(f"Circuit breaker {name} reset")

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        status = {}
        with self._lock:
            for name, breaker in self.container._circuit_breakers.items():
                status[name] = {
                    "state": breaker.state.value,
                    "failure_count": breaker.failure_count,
                    "success_count": breaker.success_count,
                    "last_failure_time": breaker.last_failure_time.isoformat()
                    if breaker.last_failure_time
                    else None,
                    "last_success_time": breaker.last_success_time.isoformat()
                    if breaker.last_success_time
                    else None,
                    "can_execute": breaker.can_execute(),
                }
        return status


class DependencyHealthMonitor:
    """Monitors dependency health and provides insights"""

    def __init__(self, container: DependencyContainer):
        self.container = container
        self._lock = threading.RLock()

    def get_dependency_health(self, name: Optional[str] = None) -> Dict[str, Any]:
        """Get health status for dependencies"""
        with self._lock:
            if name:
                metrics = self.container.get_health_metrics(name)
                if not metrics:
                    return {}

                instance = self.container.get_instance(name)
                descriptor = self.container.get_descriptor(name)

                return {
                    "name": name,
                    "status": instance.status.value if instance else "unknown",
                    "health_check_passed": metrics.health_check_passed,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "error_rate": metrics.error_rate,
                    "average_response_time": metrics.average_response_time,
                    "uptime_percentage": metrics.uptime_percentage,
                    "last_health_check": metrics.last_health_check.isoformat()
                    if metrics.last_health_check
                    else None,
                    "scope": descriptor.scope.value if descriptor else "unknown",
                    "tags": list(descriptor.tags) if descriptor else [],
                }
            else:
                # Return all dependencies health
                health_data = {}
                for dep_name in self.container._descriptors.keys():
                    health_data[dep_name] = self.get_dependency_health(dep_name)
                return health_data

    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        with self._lock:
            all_health = self.get_dependency_health()

            status_counts = defaultdict(int)
            total_requests = 0
            total_errors = 0

            for health in all_health.values():
                status_counts[health.get("status", "unknown")] += 1
                total_requests += health.get("total_requests", 0)
                total_errors += health.get("failed_requests", 0)

            overall_error_rate = (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "total_dependencies": len(all_health),
                "healthy_dependencies": status_counts.get("healthy", 0),
                "degraded_dependencies": status_counts.get("degraded", 0),
                "unhealthy_dependencies": status_counts.get("unhealthy", 0),
                "unknown_dependencies": status_counts.get("unknown", 0),
                "overall_error_rate": overall_error_rate,
                "total_requests": total_requests,
                "total_errors": total_errors,
                "system_status": "healthy"
                if overall_error_rate < 5
                else "degraded"
                if overall_error_rate < 20
                else "unhealthy",
            }

    def export_health_report(self, output_file: str) -> bool:
        """Export comprehensive health report"""
        try:
            report = {
                "export_timestamp": datetime.now().isoformat(),
                "system_summary": self.get_system_health_summary(),
                "dependency_health": self.get_dependency_health(),
                "circuit_breaker_status": {},
            }

            # Get circuit breaker status
            circuit_manager = self.container.resolve("circuit_breaker_manager")
            if circuit_manager:
                report["circuit_breaker_status"] = (
                    circuit_manager.get_circuit_breaker_status()
                )

            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Health report exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export health report: {e}")
            return False


# Convenience functions for easy use
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def register(name: str, implementation_type: Type, **kwargs):
    """Register a dependency globally"""
    container = get_container()
    container.register(name, implementation_type, **kwargs)


def resolve(name: str) -> Any:
    """Resolve a dependency globally"""
    container = get_container()
    return container.resolve(name)


@asynccontextmanager
async def dependency_scope():
    """Context manager for creating a dependency scope"""
    container = get_container()
    scoped_container = container.create_scope()

    try:
        yield scoped_container
    finally:
        scoped_container.dispose()
