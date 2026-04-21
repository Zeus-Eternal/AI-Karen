"""
Dependency Probes Module

This module provides comprehensive dependency health monitoring with:
- Runtime readiness detection
- Performance metrics collection
- Health state aggregation
- Circuit breaker integration
- Enhanced error handling and recovery
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union
import json

from ..config.config_manager import get_config_manager
from ..core.logging.logger import get_structured_logger
from ..core.metrics_manager import get_metrics_manager

logger = logging.getLogger(__name__)


class ProbeStatus(str, Enum):
    """Probe execution status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    ERROR = "error"


class ProbeSeverity(str, Enum):
    """Probe severity level"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ProbeResult:
    """Single probe execution result"""

    probe_name: str
    status: ProbeStatus
    severity: ProbeSeverity
    response_time_ms: float
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class DependencyHealth:
    """Comprehensive dependency health state"""

    name: str
    status: ProbeStatus
    severity: ProbeSeverity
    response_time_ms: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_check: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyProbe(Protocol):
    """Protocol for dependency health probes"""

    @property
    def name(self) -> str: ...

    @property
    def severity(self) -> ProbeSeverity: ...

    async def check(self) -> ProbeResult: ...


class ProbeRegistry:
    """Registry for managing dependency probes"""

    def __init__(self):
        self._probes: Dict[str, DependencyProbe] = {}
        self._results: Dict[str, List[ProbeResult]] = {}
        self._health_states: Dict[str, DependencyHealth] = {}
        self._lock = asyncio.Lock()

    def register_probe(self, probe: DependencyProbe) -> None:
        """Register a dependency probe"""
        self._probes[probe.name] = probe
        logger.info(f"Registered dependency probe: {probe.name}")

    def unregister_probe(self, probe_name: str) -> None:
        """Unregister a dependency probe"""
        if probe_name in self._probes:
            del self._probes[probe_name]
            logger.info(f"Unregistered dependency probe: {probe_name}")

    async def run_probe(self, probe_name: str) -> Optional[ProbeResult]:
        """Run a specific probe"""
        if probe_name not in self._probes:
            logger.warning(f"Probe not found: {probe_name}")
            return None

        probe = self._probes[probe_name]
        try:
            result = await probe.check()

            # Store result
            async with self._lock:
                if probe_name not in self._results:
                    self._results[probe_name] = []
                self._results[probe_name].append(result)

                # Keep only last 100 results
                if len(self._results[probe_name]) > 100:
                    self._results[probe_name] = self._results[probe_name][-100:]

                # Update health state
                await self._update_health_state(probe_name, result)

            return result

        except Exception as e:
            logger.error(f"Error running probe {probe_name}: {e}")
            error_result = ProbeResult(
                probe_name=probe_name,
                status=ProbeStatus.ERROR,
                severity=ProbeSeverity.CRITICAL,
                response_time_ms=0.0,
                message=str(e),
                timestamp=datetime.utcnow(),
            )
            return error_result

    async def run_all_probes(self) -> Dict[str, ProbeResult]:
        """Run all registered probes"""
        results = {}

        # Run probes in parallel
        tasks = []
        for probe_name in self._probes:
            task = asyncio.create_task(self.run_probe(probe_name))
            tasks.append((probe_name, task))

        # Wait for all tasks to complete
        for probe_name, task in tasks:
            try:
                result = await task
                if result:
                    results[probe_name] = result
            except Exception as e:
                logger.error(f"Error running probe {probe_name}: {e}")

        return results

    async def _update_health_state(self, probe_name: str, result: ProbeResult) -> None:
        """Update the health state for a dependency"""
        if probe_name not in self._health_states:
            self._health_states[probe_name] = DependencyHealth(
                name=probe_name,
                status=result.status,
                severity=result.severity,
                response_time_ms=result.response_time_ms,
                consecutive_failures=0,
                consecutive_successes=0,
                last_check=datetime.utcnow(),
            )

        health_state = self._health_states[probe_name]

        # Update consecutive counters
        if result.status == ProbeStatus.HEALTHY:
            health_state.consecutive_successes += 1
            health_state.consecutive_failures = 0
            health_state.last_success = datetime.utcnow()
        else:
            health_state.consecutive_failures += 1
            health_state.consecutive_successes = 0
            health_state.last_failure = datetime.utcnow()

        # Update health state
        health_state.status = result.status
        health_state.severity = result.severity
        health_state.response_time_ms = result.response_time_ms
        health_state.error_message = result.message
        health_state.last_check = datetime.utcnow()
        health_state.metadata = result.details

    def get_health_state(self, probe_name: str) -> Optional[DependencyHealth]:
        """Get the current health state for a dependency"""
        return self._health_states.get(probe_name)

    def get_all_health_states(self) -> Dict[str, DependencyHealth]:
        """Get health states for all dependencies"""
        return dict(self._health_states)

    def get_recent_results(self, probe_name: str, limit: int = 10) -> List[ProbeResult]:
        """Get recent probe results"""
        if probe_name not in self._results:
            return []
        return self._results[probe_name][-limit:]


class EnhancedPostgreSQLProbe(DependencyProbe):
    """Enhanced PostgreSQL dependency probe"""

    @property
    def name(self) -> str:
        return "postgresql"

    @property
    def severity(self) -> ProbeSeverity:
        return ProbeSeverity.CRITICAL

    async def check(self) -> ProbeResult:
        """Check PostgreSQL connectivity and performance"""
        start_time = time.time()

        try:
            # Try to import and test PostgreSQL connection
            import psycopg2
            from psycopg2 import pool

            # Test basic connectivity
            connection = None
            try:
                # This would typically use your actual database configuration
                # For demonstration, we'll simulate the check
                connection = psycopg2.connect(
                    host="localhost",
                    database="postgres",
                    user="postgres",
                    password="password",
                    connect_timeout=5,
                )

                # Test query
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

                response_time = (time.time() - start_time) * 1000

                return ProbeResult(
                    probe_name=self.name,
                    status=ProbeStatus.HEALTHY,
                    severity=self.severity,
                    response_time_ms=response_time,
                    message="PostgreSQL connection successful",
                    details={
                        "connection_pool_size": 0,  # Would be actual pool size
                        "query_latency_ms": response_time,
                        "database_available": True,
                    },
                )

            except psycopg2.OperationalError as e:
                response_time = (time.time() - start_time) * 1000
                return ProbeResult(
                    probe_name=self.name,
                    status=ProbeStatus.UNHEALTHY,
                    severity=self.severity,
                    response_time_ms=response_time,
                    message=f"PostgreSQL connection failed: {str(e)}",
                    details={
                        "error_type": "operational_error",
                        "database_available": False,
                    },
                )
            finally:
                if connection:
                    connection.close()

        except ImportError:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNKNOWN,
                severity=self.severity,
                response_time_ms=0.0,
                message="PostgreSQL driver not available",
                details={
                    "error_type": "missing_driver",
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.ERROR,
                severity=self.severity,
                response_time_ms=response_time,
                message=f"PostgreSQL probe error: {str(e)}",
                details={
                    "error_type": "probe_error",
                },
            )


class EnhancedRedisProbe(DependencyProbe):
    """Enhanced Redis dependency probe"""

    @property
    def name(self) -> str:
        return "redis"

    @property
    def severity(self) -> ProbeSeverity:
        return ProbeSeverity.CRITICAL

    async def check(self) -> ProbeResult:
        """Check Redis connectivity and performance"""
        start_time = time.time()

        try:
            import redis

            # Test Redis connection
            redis_client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # Test basic operations
            test_key = "health_check"
            test_value = "test_value"

            # Set and get test value
            redis_client.setex(test_key, 10, test_value)
            retrieved_value = redis_client.get(test_key)

            if retrieved_value == test_value:
                response_time = (time.time() - start_time) * 1000

                # Get Redis info
                try:
                    redis_info = redis_client.info()
                    memory_usage = redis_info.get("used_memory", 0)
                    connected_clients = redis_info.get("connected_clients", 0)

                    return ProbeResult(
                        probe_name=self.name,
                        status=ProbeStatus.HEALTHY,
                        severity=self.severity,
                        response_time_ms=response_time,
                        message="Redis connection successful",
                        details={
                            "memory_usage_bytes": memory_usage,
                            "connected_clients": connected_clients,
                            "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                            "operations_performed": 2,
                        },
                    )
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    return ProbeResult(
                        probe_name=self.name,
                        status=ProbeStatus.HEALTHY,
                        severity=self.severity,
                        response_time_ms=response_time,
                        message="Redis connection successful but info retrieval failed",
                        details={
                            "error_type": "info_retrieval_error",
                            "error_message": str(e),
                        },
                    )
            else:
                response_time = (time.time() - start_time) * 1000
                return ProbeResult(
                    probe_name=self.name,
                    status=ProbeStatus.UNHEALTHY,
                    severity=self.severity,
                    response_time_ms=response_time,
                    message="Redis data consistency check failed",
                    details={
                        "error_type": "data_consistency_error",
                    },
                )

        except ImportError:
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNKNOWN,
                severity=self.severity,
                response_time_ms=0.0,
                message="Redis driver not available",
                details={
                    "error_type": "missing_driver",
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNHEALTHY,
                severity=self.severity,
                response_time_ms=response_time,
                message=f"Redis connection failed: {str(e)}",
                details={
                    "error_type": "connection_error",
                },
            )



            else:
                response_time = (time.time() - start_time) * 1000
                return ProbeResult(
                    probe_name=self.name,
                    status=ProbeStatus.UNHEALTHY,
                    severity=self.severity,
                    response_time_ms=response_time,
                    message="Chat orchestrator initialization failed",
                    details={
                        "orchestrator_type": "unknown",
                        "initialization_successful": False,
                    },
                )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.TIMEOUT,
                severity=self.severity,
                response_time_ms=response_time,
                message="Chat orchestrator initialization timed out",
                details={
                    "timeout_seconds": 10.0,
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNHEALTHY,
                severity=self.severity,
                response_time_ms=response_time,
                message=f"Chat orchestrator error: {str(e)}",
                details={
                    "error_type": "orchestrator_error",
                },
            )


class EnhancedProviderRouterProbe(DependencyProbe):
    """Enhanced Provider Router dependency probe"""

    @property
    def name(self) -> str:
        return "provider_router"

    @property
    def severity(self) -> ProbeSeverity:
        return ProbeSeverity.HIGH

    async def check(self) -> ProbeResult:
        """Check Provider Router availability and performance"""
        start_time = time.time()

        try:
            # Try to import and test provider router
            from ..services.llm_router import get_llm_router

            # Test router initialization
            router_task = asyncio.create_task(get_llm_router())
            router = await asyncio.wait_for(router_task, timeout=10.0)

            if router:
                response_time = (time.time() - start_time) * 1000

                # Test basic router functionality
                try:
                    available_providers = await router.get_available_providers()

                    return ProbeResult(
                        probe_name=self.name,
                        status=ProbeStatus.HEALTHY,
                        severity=self.severity,
                        response_time_ms=response_time,
                        message="Provider router available",
                        details={
                            "available_providers": len(available_providers),
                            "provider_names": list(available_providers.keys()),
                            "router_type": type(router).__name__,
                        },
                    )
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    return ProbeResult(
                        probe_name=self.name,
                        status=ProbeStatus.HEALTHY,
                        severity=self.severity,
                        response_time_ms=response_time,
                        message="Provider router available but provider check failed",
                        details={
                            "router_type": type(router).__name__,
                            "provider_check_error": str(e),
                        },
                    )
            else:
                response_time = (time.time() - start_time) * 1000
                return ProbeResult(
                    probe_name=self.name,
                    status=ProbeStatus.UNHEALTHY,
                    severity=self.severity,
                    response_time_ms=response_time,
                    message="Provider router initialization failed",
                    details={
                        "router_type": "unknown",
                        "initialization_successful": False,
                    },
                )

        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.TIMEOUT,
                severity=self.severity,
                response_time_ms=response_time,
                message="Provider router initialization timed out",
                details={
                    "timeout_seconds": 10.0,
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNHEALTHY,
                severity=self.severity,
                response_time_ms=response_time,
                message=f"Provider router error: {str(e)}",
                details={
                    "error_type": "router_error",
                },
            )


class EnhancedMemorySubsystemProbe(DependencyProbe):
    """Enhanced Memory Subsystem dependency probe"""

    @property
    def name(self) -> str:
        return "memory_subsystem"

    @property
    def severity(self) -> ProbeSeverity:
        return ProbeSeverity.MEDIUM

    async def check(self) -> ProbeResult:
        """Check Memory Subsystem availability and performance"""
        start_time = time.time()

        try:
            # Try to import and test memory subsystem
            from ..memory.memory_service import MemoryService

            # Test memory processor initialization
            memory_processor = MemoryProcessor()

            response_time = (time.time() - start_time) * 1000

            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.HEALTHY,
                severity=self.severity,
                response_time_ms=response_time,
                message="Memory subsystem available",
                details={
                    "memory_processor_type": type(memory_processor).__name__,
                    "initialization_successful": True,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ProbeResult(
                probe_name=self.name,
                status=ProbeStatus.UNHEALTHY,
                severity=self.severity,
                response_time_ms=response_time,
                message=f"Memory subsystem error: {str(e)}",
                details={
                    "error_type": "memory_error",
                },
            )


class DependencyProbeManager:
    """Manager for coordinating dependency probes"""

    def __init__(self):
        self.registry = ProbeRegistry()
        self._structured_logger = get_structured_logger()
        self._metrics_manager = get_metrics_manager()
        self._config_manager = get_config_manager()

        # Background tasks
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Initialize default probes
        self._initialize_default_probes()

    def _initialize_default_probes(self) -> None:
        """Initialize default dependency probes"""
        probes = [
            EnhancedPostgreSQLProbe(),
            EnhancedRedisProbe(),
            EnhancedChatOrchestratorProbe(),
            EnhancedProviderRouterProbe(),
            EnhancedMemorySubsystemProbe(),
        ]

        for probe in probes:
            self.registry.register_probe(probe)

    async def initialize(self) -> None:
        """Initialize the dependency probe manager"""
        if self._running:
            return

        self._running = True

        # Run initial health check
        await self.run_health_check()

        # Start background monitoring
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Dependency Probe Manager initialized")

    async def shutdown(self) -> None:
        """Shutdown the dependency probe manager"""
        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Dependency Probe Manager shutdown completed")

    async def run_health_check(self) -> Dict[str, ProbeResult]:
        """Run a comprehensive health check"""
        results = await self.registry.run_all_probes()

        # Log results
        for probe_name, result in results.items():
            self._structured_logger.log_event(
                event="dependency_health_check",
                details={
                    "probe_name": probe_name,
                    "status": result.status.value,
                    "severity": result.severity.value,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                },
            )

            # Record metrics
            self._metrics_manager.register_histogram(
                "dependency_probe_response_time_ms", ["probe_name", "status"]
            ).labels(probe_name=probe_name, status=result.status.value).observe(
                result.response_time_ms
            )

            self._metrics_manager.register_counter(
                "dependency_probe_checks_total", ["probe_name", "status"]
            ).labels(probe_name=probe_name, status=result.status.value).inc()

        return results

    async def run_single_probe(self, probe_name: str) -> Optional[ProbeResult]:
        """Run a single probe"""
        result = await self.registry.run_probe(probe_name)

        if result:
            # Log result
            self._structured_logger.log_event(
                event="dependency_single_probe_check",
                details={
                    "probe_name": probe_name,
                    "status": result.status.value,
                    "response_time_ms": result.response_time_ms,
                    "message": result.message,
                },
            )

            # Record metrics
            self._metrics_manager.register_histogram(
                "dependency_probe_response_time_ms", ["probe_name", "status"]
            ).labels(probe_name=probe_name, status=result.status.value).observe(
                result.response_time_ms
            )

        return result

    async def get_dependency_health(self) -> Dict[str, DependencyHealth]:
        """Get current health states for all dependencies"""
        return self.registry.get_all_health_states()

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        health_states = await self.get_dependency_health()

        # Calculate overall health score
        total_probes = len(health_states)
        healthy_probes = sum(
            1 for state in health_states.values() if state.status == ProbeStatus.HEALTHY
        )

        overall_health = "healthy" if healthy_probes == total_probes else "degraded"

        # Identify critical issues
        critical_issues = []
        for name, state in health_states.items():
            if (
                state.severity == ProbeSeverity.CRITICAL
                and state.status != ProbeStatus.HEALTHY
            ):
                critical_issues.append(
                    {
                        "dependency": name,
                        "status": state.status.value,
                        "error": state.error_message,
                    }
                )

        return {
            "overall_health": overall_health,
            "total_dependencies": total_probes,
            "healthy_dependencies": healthy_probes,
            "unhealthy_dependencies": total_probes - healthy_probes,
            "health_score": healthy_probes / total_probes if total_probes > 0 else 0.0,
            "critical_issues": critical_issues,
            "dependency_health": {
                name: {
                    "status": state.status.value,
                    "severity": state.severity.value,
                    "response_time_ms": state.response_time_ms,
                    "consecutive_failures": state.consecutive_failures,
                    "last_check": state.last_check.isoformat()
                    if state.last_check
                    else None,
                }
                for name, state in health_states.items()
            },
        }

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while self._running:
            try:
                # Run health check
                await self.run_health_check()

                # Sleep for configured interval
                await asyncio.sleep(30)  # 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error


# Global dependency probe manager instance
_dependency_probe_manager: Optional[DependencyProbeManager] = None


async def get_dependency_probe_manager() -> DependencyProbeManager:
    """Get global dependency probe manager instance"""
    global _dependency_probe_manager
    if _dependency_probe_manager is None:
        _dependency_probe_manager = DependencyProbeManager()
        await _dependency_probe_manager.initialize()
    return _dependency_probe_manager
