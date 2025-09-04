"""
Error Recovery Manager with Circuit Breaker Pattern

This module implements comprehensive error handling and graceful degradation
for the performance optimization system, including circuit breakers, fallback
mechanisms, and automatic recovery attempts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
import json
from pathlib import Path

from ..config.performance_config import PerformanceConfig


class ServiceStatus(Enum):
    """Service health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    CIRCUIT_OPEN = "circuit_open"


class CircuitState(Enum):
    """Circuit breaker state enumeration"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class ServiceHealth:
    """Service health tracking data"""
    service_name: str
    status: ServiceStatus = ServiceStatus.HEALTHY
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_opened_at: Optional[datetime] = None
    recovery_attempts: int = 0
    is_essential: bool = False
    fallback_available: bool = False
    error_messages: List[str] = field(default_factory=list)


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    half_open_max_calls: int = 3
    success_threshold: int = 2  # successes needed to close circuit


class ErrorRecoveryManager:
    """
    Manages error recovery, circuit breakers, and graceful degradation
    for all services in the performance optimization system.
    """
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Service health tracking
        self.service_health: Dict[str, ServiceHealth] = {}
        self.circuit_config = CircuitBreakerConfig()
        
        # Fallback mechanisms
        self.fallback_handlers: Dict[str, Callable] = {}
        self.essential_services: Set[str] = set()
        
        # Recovery and monitoring
        self.recovery_tasks: Dict[str, asyncio.Task] = {}
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Error logging and alerting
        self.error_log_path = Path("logs/error_recovery.log")
        self.alert_handlers: List[Callable] = []
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup dedicated error recovery logging"""
        self.error_log_path.parent.mkdir(exist_ok=True)
        
        # Create dedicated logger for error recovery
        self.recovery_logger = logging.getLogger("error_recovery")
        self.recovery_logger.setLevel(logging.INFO)
        
        # File handler for error recovery logs
        handler = logging.FileHandler(self.error_log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.recovery_logger.addHandler(handler)
    
    def register_service(self, service_name: str, is_essential: bool = False, 
                        fallback_available: bool = False):
        """Register a service for health monitoring and error recovery"""
        self.service_health[service_name] = ServiceHealth(
            service_name=service_name,
            is_essential=is_essential,
            fallback_available=fallback_available
        )
        
        if is_essential:
            self.essential_services.add(service_name)
        
        self.logger.info(f"Registered service {service_name} for error recovery monitoring")
    
    def register_fallback_handler(self, service_name: str, handler: Callable):
        """Register a fallback handler for a service"""
        self.fallback_handlers[service_name] = handler
        if service_name in self.service_health:
            self.service_health[service_name].fallback_available = True
        
        self.logger.info(f"Registered fallback handler for service {service_name}")
    
    def register_alert_handler(self, handler: Callable):
        """Register an alert handler for error notifications"""
        self.alert_handlers.append(handler)
    
    async def handle_service_failure(self, service_name: str, error: Exception) -> bool:
        """
        Handle a service failure and determine recovery strategy
        
        Returns:
            bool: True if service should continue operating (with fallback), False if should stop
        """
        if service_name not in self.service_health:
            self.register_service(service_name)
        
        health = self.service_health[service_name]
        health.failure_count += 1
        health.last_failure = datetime.now()
        health.error_messages.append(str(error))
        
        # Keep only last 10 error messages
        if len(health.error_messages) > 10:
            health.error_messages = health.error_messages[-10:]
        
        self.recovery_logger.error(
            f"Service failure: {service_name} - {error} "
            f"(failure count: {health.failure_count})"
        )
        
        # Check if circuit breaker should open
        if health.failure_count >= self.circuit_config.failure_threshold:
            await self._open_circuit_breaker(service_name)
        
        # Determine recovery strategy based on service type
        if health.is_essential:
            # Essential service - attempt immediate recovery
            await self._attempt_service_recovery(service_name)
            return True  # Keep trying
        else:
            # Optional service - use fallback or graceful degradation
            return await self._handle_optional_service_failure(service_name)
    
    async def _open_circuit_breaker(self, service_name: str):
        """Open circuit breaker for a failing service"""
        health = self.service_health[service_name]
        health.circuit_state = CircuitState.OPEN
        health.circuit_opened_at = datetime.now()
        health.status = ServiceStatus.CIRCUIT_OPEN
        
        self.recovery_logger.warning(f"Circuit breaker opened for service {service_name}")
        
        # Send alert
        await self._send_alert(
            f"Circuit breaker opened for service {service_name}",
            "critical" if health.is_essential else "warning"
        )
        
        # Schedule recovery attempt
        if service_name not in self.recovery_tasks:
            self.recovery_tasks[service_name] = asyncio.create_task(
                self._schedule_recovery_attempt(service_name)
            )
    
    async def _schedule_recovery_attempt(self, service_name: str):
        """Schedule automatic recovery attempt after timeout"""
        await asyncio.sleep(self.circuit_config.recovery_timeout)
        
        health = self.service_health[service_name]
        if health.circuit_state == CircuitState.OPEN:
            health.circuit_state = CircuitState.HALF_OPEN
            health.status = ServiceStatus.RECOVERING
            
            self.recovery_logger.info(f"Attempting recovery for service {service_name}")
            
            # Try recovery
            success = await self._attempt_service_recovery(service_name)
            
            if success:
                await self._close_circuit_breaker(service_name)
            else:
                # Recovery failed, open circuit again
                await self._open_circuit_breaker(service_name)
        
        # Clean up recovery task
        if service_name in self.recovery_tasks:
            del self.recovery_tasks[service_name]
    
    async def _close_circuit_breaker(self, service_name: str):
        """Close circuit breaker after successful recovery"""
        health = self.service_health[service_name]
        health.circuit_state = CircuitState.CLOSED
        health.status = ServiceStatus.HEALTHY
        health.failure_count = 0
        health.recovery_attempts = 0
        health.last_success = datetime.now()
        
        self.recovery_logger.info(f"Circuit breaker closed for service {service_name}")
        
        await self._send_alert(
            f"Service {service_name} recovered successfully",
            "info"
        )
    
    async def _attempt_service_recovery(self, service_name: str) -> bool:
        """
        Attempt to recover a failed service
        
        Returns:
            bool: True if recovery successful, False otherwise
        """
        health = self.service_health[service_name]
        health.recovery_attempts += 1
        
        try:
            # Try to import and use service lifecycle manager if available
            try:
                from .service_lifecycle_manager import ServiceLifecycleManager
                from .service_registry import ServiceRegistry
                
                # Get service registry and lifecycle manager
                registry = ServiceRegistry()
                lifecycle_manager = ServiceLifecycleManager(registry)
                
                # Attempt to restart the service
                await lifecycle_manager.restart_service(service_name)
            except ImportError:
                # If lifecycle manager not available, just test health
                self.recovery_logger.info(f"ServiceLifecycleManager not available, testing health directly")
            except Exception as e:
                self.recovery_logger.warning(f"Could not restart service {service_name}: {e}")
            
            # Test service health
            if await self._test_service_health(service_name):
                health.status = ServiceStatus.HEALTHY
                health.last_success = datetime.now()
                
                self.recovery_logger.info(f"Successfully recovered service {service_name}")
                return True
            else:
                health.status = ServiceStatus.FAILED
                return False
                
        except Exception as e:
            self.recovery_logger.error(f"Recovery attempt failed for {service_name}: {e}")
            health.status = ServiceStatus.FAILED
            return False
    
    async def _test_service_health(self, service_name: str) -> bool:
        """Test if a service is healthy after recovery attempt"""
        try:
            # Import here to avoid circular imports
            from .service_registry import ServiceRegistry
            
            registry = ServiceRegistry()
            service = registry.get_service(service_name)
            
            if service and hasattr(service, 'health_check'):
                return await service.health_check()
            
            # If no health check method, assume healthy if service exists
            return service is not None
            
        except Exception as e:
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    async def _handle_optional_service_failure(self, service_name: str) -> bool:
        """Handle failure of an optional service with fallback mechanisms"""
        health = self.service_health[service_name]
        
        # Try fallback handler if available
        if service_name in self.fallback_handlers:
            try:
                fallback_handler = self.fallback_handlers[service_name]
                await fallback_handler()
                
                health.status = ServiceStatus.DEGRADED
                self.recovery_logger.info(f"Using fallback for service {service_name}")
                
                await self._send_alert(
                    f"Service {service_name} using fallback mechanism",
                    "warning"
                )
                
                return True  # Continue with fallback
                
            except Exception as e:
                self.recovery_logger.error(f"Fallback failed for {service_name}: {e}")
        
        # No fallback available - graceful degradation
        health.status = ServiceStatus.FAILED
        
        await self._send_alert(
            f"Service {service_name} failed - graceful degradation active",
            "warning"
        )
        
        return False  # Stop service
    
    async def check_circuit_breaker(self, service_name: str) -> bool:
        """
        Check if a service call should be allowed through circuit breaker
        
        Returns:
            bool: True if call should proceed, False if circuit is open
        """
        if service_name not in self.service_health:
            return True  # Allow if not monitored
        
        health = self.service_health[service_name]
        
        if health.circuit_state == CircuitState.CLOSED:
            return True
        elif health.circuit_state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (health.circuit_opened_at and 
                datetime.now() - health.circuit_opened_at > 
                timedelta(seconds=self.circuit_config.recovery_timeout)):
                health.circuit_state = CircuitState.HALF_OPEN
                return True
            return False
        elif health.circuit_state == CircuitState.HALF_OPEN:
            # Allow limited calls in half-open state
            return True
        
        return False
    
    async def record_service_success(self, service_name: str):
        """Record a successful service call"""
        if service_name not in self.service_health:
            return
        
        health = self.service_health[service_name]
        health.last_success = datetime.now()
        
        # Handle circuit breaker state transitions
        if health.circuit_state == CircuitState.HALF_OPEN:
            # Count successes in half-open state
            if health.recovery_attempts >= self.circuit_config.success_threshold:
                await self._close_circuit_breaker(service_name)
        elif health.circuit_state == CircuitState.CLOSED:
            # Reset failure count on success
            health.failure_count = max(0, health.failure_count - 1)
    
    async def get_service_health_status(self, service_name: str) -> Optional[ServiceHealth]:
        """Get current health status of a service"""
        return self.service_health.get(service_name)
    
    async def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health status of all monitored services"""
        return self.service_health.copy()
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started error recovery monitoring")
    
    async def stop_monitoring(self):
        """Stop continuous health monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all recovery tasks
        for task in self.recovery_tasks.values():
            task.cancel()
        
        self.recovery_tasks.clear()
        self.logger.info("Stopped error recovery monitoring")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop for service health"""
        while self.monitoring_active:
            try:
                await self._check_all_service_health()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _check_all_service_health(self):
        """Check health of all registered services"""
        for service_name in self.service_health.keys():
            try:
                is_healthy = await self._test_service_health(service_name)
                health = self.service_health[service_name]
                
                if is_healthy:
                    if health.status in [ServiceStatus.FAILED, ServiceStatus.DEGRADED]:
                        # Service recovered
                        await self.record_service_success(service_name)
                        self.recovery_logger.info(f"Service {service_name} recovered")
                else:
                    if health.status == ServiceStatus.HEALTHY:
                        # Service just failed
                        await self.handle_service_failure(
                            service_name, 
                            Exception("Health check failed")
                        )
                        
            except Exception as e:
                self.logger.error(f"Error checking health of {service_name}: {e}")
    
    async def _send_alert(self, message: str, severity: str = "info"):
        """Send alert through registered alert handlers"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": severity,
            "source": "error_recovery_manager"
        }
        
        # Log the alert
        if severity == "critical":
            self.recovery_logger.critical(message)
        elif severity == "warning":
            self.recovery_logger.warning(message)
        else:
            self.recovery_logger.info(message)
        
        # Send through alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert_data)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
    
    async def export_health_report(self) -> Dict[str, Any]:
        """Export comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.monitoring_active,
            "total_services": len(self.service_health),
            "essential_services": len(self.essential_services),
            "services": {}
        }
        
        for service_name, health in self.service_health.items():
            report["services"][service_name] = {
                "status": health.status.value,
                "circuit_state": health.circuit_state.value,
                "failure_count": health.failure_count,
                "recovery_attempts": health.recovery_attempts,
                "is_essential": health.is_essential,
                "fallback_available": health.fallback_available,
                "last_failure": health.last_failure.isoformat() if health.last_failure else None,
                "last_success": health.last_success.isoformat() if health.last_success else None,
                "recent_errors": health.error_messages[-3:]  # Last 3 errors
            }
        
        return report


# Global instance for easy access
_error_recovery_manager = None

def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get global error recovery manager instance"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager()
    return _error_recovery_manager