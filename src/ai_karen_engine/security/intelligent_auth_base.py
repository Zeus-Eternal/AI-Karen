"""
Base classes and interfaces for intelligent authentication services.

This module provides abstract base classes and interfaces for all components
of the intelligent authentication system, including service interfaces,
health monitoring, and dependency injection setup.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from enum import Enum

from ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    IntelligentAuthConfig,
    NLPFeatures,
    EmbeddingAnalysis,
    BehavioralAnalysis,
    ThreatAnalysis,
    SecurityAction
)

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealthStatus:
    """Health status information for a service component."""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'service_name': self.service_name,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'response_time': self.response_time,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


@dataclass
class IntelligentAuthHealthStatus:
    """Comprehensive health status for intelligent authentication system."""
    overall_status: ServiceStatus
    component_statuses: Dict[str, ServiceHealthStatus]
    last_updated: datetime
    processing_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_status': self.overall_status.value,
            'component_statuses': {
                name: status.to_dict() 
                for name, status in self.component_statuses.items()
            },
            'last_updated': self.last_updated.isoformat(),
            'processing_metrics': self.processing_metrics
        }

    def is_healthy(self) -> bool:
        """Check if the overall system is healthy."""
        return self.overall_status == ServiceStatus.HEALTHY

    def get_unhealthy_components(self) -> List[str]:
        """Get list of unhealthy component names."""
        return [
            name for name, status in self.component_statuses.items()
            if status.status == ServiceStatus.UNHEALTHY
        ]


@runtime_checkable
class HealthCheckable(Protocol):
    """Protocol for components that support health checking."""
    
    async def health_check(self) -> ServiceHealthStatus:
        """Perform health check and return status."""
        ...


@runtime_checkable
class Configurable(Protocol):
    """Protocol for components that support configuration updates."""
    
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """Update component configuration."""
        ...


class BaseIntelligentAuthService(ABC):
    """Abstract base class for intelligent authentication services."""

    def __init__(self, config: IntelligentAuthConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._health_status = ServiceHealthStatus(
            service_name=self.__class__.__name__,
            status=ServiceStatus.UNKNOWN,
            last_check=datetime.now()
        )

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service and its dependencies."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        pass

    async def health_check(self) -> ServiceHealthStatus:
        """Perform health check for this service."""
        start_time = time.time()
        
        try:
            # Perform service-specific health check
            is_healthy = await self._perform_health_check()
            
            self._health_status = ServiceHealthStatus(
                service_name=self.__class__.__name__,
                status=ServiceStatus.HEALTHY if is_healthy else ServiceStatus.DEGRADED,
                last_check=datetime.now(),
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Health check failed for {self.__class__.__name__}: {e}")
            self._health_status = ServiceHealthStatus(
                service_name=self.__class__.__name__,
                status=ServiceStatus.UNHEALTHY,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
        
        return self._health_status

    @abstractmethod
    async def _perform_health_check(self) -> bool:
        """Service-specific health check implementation."""
        pass

    async def update_config(self, config: IntelligentAuthConfig) -> bool:
        """Update service configuration."""
        try:
            old_config = self.config
            self.config = config
            
            # Allow service-specific configuration update logic
            success = await self._handle_config_update(old_config, config)
            
            if not success:
                self.config = old_config  # Rollback on failure
                
            return success
            
        except Exception as e:
            self.logger.error(f"Configuration update failed for {self.__class__.__name__}: {e}")
            return False

    async def _handle_config_update(self, old_config: IntelligentAuthConfig, 
                                   new_config: IntelligentAuthConfig) -> bool:
        """Handle service-specific configuration updates."""
        # Default implementation - subclasses can override
        return True


class CredentialAnalyzerInterface(ABC):
    """Interface for credential analysis services."""

    @abstractmethod
    async def analyze_credentials(self, email: str, password_hash: str) -> NLPFeatures:
        """Analyze credentials and extract NLP features."""
        pass

    @abstractmethod
    async def detect_suspicious_patterns(self, text: str) -> List[str]:
        """Detect suspicious patterns in credential text."""
        pass


class BehavioralEmbeddingInterface(ABC):
    """Interface for behavioral embedding services."""

    @abstractmethod
    async def generate_embedding(self, context: AuthContext) -> EmbeddingAnalysis:
        """Generate behavioral embedding from authentication context."""
        pass

    @abstractmethod
    async def calculate_similarity(self, embedding1: List[float], 
                                 embedding2: List[float]) -> float:
        """Calculate similarity between two embeddings."""
        pass

    @abstractmethod
    async def update_user_profile(self, user_id: str, embedding: List[float]) -> None:
        """Update user's behavioral profile with new embedding."""
        pass


class AnomalyDetectorInterface(ABC):
    """Interface for anomaly detection services."""

    @abstractmethod
    async def detect_anomalies(self, context: AuthContext, 
                             nlp_features: NLPFeatures,
                             embedding_analysis: EmbeddingAnalysis) -> BehavioralAnalysis:
        """Detect behavioral anomalies in authentication attempt."""
        pass

    @abstractmethod
    async def calculate_risk_score(self, context: AuthContext,
                                 nlp_features: NLPFeatures,
                                 embedding_analysis: EmbeddingAnalysis,
                                 behavioral_analysis: BehavioralAnalysis) -> float:
        """Calculate overall risk score for authentication attempt."""
        pass

    @abstractmethod
    async def learn_from_feedback(self, user_id: str, context: AuthContext,
                                feedback: Dict[str, Any]) -> None:
        """Learn from authentication feedback to improve detection."""
        pass


class ThreatIntelligenceInterface(ABC):
    """Interface for threat intelligence services."""

    @abstractmethod
    async def analyze_threat_context(self, context: AuthContext) -> ThreatAnalysis:
        """Analyze threat intelligence context for authentication attempt."""
        pass

    @abstractmethod
    async def check_ip_reputation(self, ip_address: str) -> float:
        """Check IP address reputation score."""
        pass

    @abstractmethod
    async def detect_attack_patterns(self, recent_attempts: List[AuthContext]) -> List[str]:
        """Detect coordinated attack patterns."""
        pass


class IntelligentAuthServiceInterface(ABC):
    """Main interface for the intelligent authentication service."""

    @abstractmethod
    async def analyze_login_attempt(self, context: AuthContext) -> AuthAnalysisResult:
        """Perform comprehensive analysis of login attempt."""
        pass

    @abstractmethod
    async def update_user_behavioral_profile(self, user_id: str, 
                                           context: AuthContext, 
                                           success: bool) -> None:
        """Update user's behavioral profile based on login outcome."""
        pass

    @abstractmethod
    async def provide_feedback(self, user_id: str, context: AuthContext,
                             feedback: Dict[str, Any]) -> None:
        """Provide feedback to improve ML models."""
        pass

    @abstractmethod
    def get_health_status(self) -> IntelligentAuthHealthStatus:
        """Get comprehensive health status of all components."""
        pass


class ServiceRegistry:
    """Registry for managing intelligent authentication service dependencies."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        self.logger = logging.getLogger(f"{__name__}.ServiceRegistry")

    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service
        self.logger.info(f"Registered service: {name}")

    def get_service(self, name: str) -> Optional[Any]:
        """Get a registered service instance."""
        return self._services.get(name)

    def has_service(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services

    async def initialize_all(self) -> bool:
        """Initialize all registered services."""
        if self._initialized:
            return True

        success = True
        for name, service in self._services.items():
            try:
                if hasattr(service, 'initialize'):
                    result = await service.initialize()
                    if not result:
                        self.logger.error(f"Failed to initialize service: {name}")
                        success = False
                else:
                    self.logger.warning(f"Service {name} does not support initialization")
            except Exception as e:
                self.logger.error(f"Error initializing service {name}: {e}")
                success = False

        self._initialized = success
        return success

    async def shutdown_all(self) -> None:
        """Shutdown all registered services."""
        for name, service in self._services.items():
            try:
                if hasattr(service, 'shutdown'):
                    await service.shutdown()
                    self.logger.info(f"Shutdown service: {name}")
            except Exception as e:
                self.logger.error(f"Error shutting down service {name}: {e}")

        self._initialized = False

    async def health_check_all(self) -> Dict[str, ServiceHealthStatus]:
        """Perform health check on all registered services."""
        health_statuses = {}
        
        for name, service in self._services.items():
            try:
                if hasattr(service, 'health_check'):
                    status = await service.health_check()
                    health_statuses[name] = status
                else:
                    # Create a basic health status for services without health check
                    health_statuses[name] = ServiceHealthStatus(
                        service_name=name,
                        status=ServiceStatus.UNKNOWN,
                        last_check=datetime.now(),
                        error_message="Health check not supported"
                    )
            except Exception as e:
                self.logger.error(f"Health check failed for service {name}: {e}")
                health_statuses[name] = ServiceHealthStatus(
                    service_name=name,
                    status=ServiceStatus.UNHEALTHY,
                    last_check=datetime.now(),
                    error_message=str(e)
                )

        return health_statuses

    def get_service_names(self) -> List[str]:
        """Get list of registered service names."""
        return list(self._services.keys())

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._initialized = False


class HealthMonitor:
    """Health monitoring service for intelligent authentication components."""

    def __init__(self, service_registry: ServiceRegistry, 
                 check_interval: float = 60.0):
        self.service_registry = service_registry
        self.check_interval = check_interval
        self.logger = logging.getLogger(f"{__name__}.HealthMonitor")
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_history: Dict[str, List[ServiceHealthStatus]] = {}

    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Started health monitoring")

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            
        self.logger.info("Stopped health monitoring")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all services."""
        health_statuses = await self.service_registry.health_check_all()
        
        for name, status in health_statuses.items():
            # Store health history
            if name not in self._health_history:
                self._health_history[name] = []
            
            self._health_history[name].append(status)
            
            # Keep only recent history (last 100 checks)
            if len(self._health_history[name]) > 100:
                self._health_history[name] = self._health_history[name][-100:]
            
            # Log unhealthy services
            if status.status == ServiceStatus.UNHEALTHY:
                self.logger.warning(
                    f"Service {name} is unhealthy: {status.error_message}"
                )

    def get_current_health_status(self) -> IntelligentAuthHealthStatus:
        """Get current health status of all components."""
        # Get latest health status for each service
        component_statuses = {}
        overall_status = ServiceStatus.HEALTHY
        
        for name, history in self._health_history.items():
            if history:
                latest_status = history[-1]
                component_statuses[name] = latest_status
                
                # Determine overall status
                if latest_status.status == ServiceStatus.UNHEALTHY:
                    overall_status = ServiceStatus.UNHEALTHY
                elif (latest_status.status == ServiceStatus.DEGRADED and 
                      overall_status == ServiceStatus.HEALTHY):
                    overall_status = ServiceStatus.DEGRADED

        # Calculate processing metrics
        processing_metrics = {}
        for name, history in self._health_history.items():
            if history:
                response_times = [status.response_time for status in history[-10:]]
                processing_metrics[f"{name}_avg_response_time"] = (
                    sum(response_times) / len(response_times)
                )

        return IntelligentAuthHealthStatus(
            overall_status=overall_status,
            component_statuses=component_statuses,
            last_updated=datetime.now(),
            processing_metrics=processing_metrics
        )

    def get_health_history(self, service_name: str, 
                          limit: int = 50) -> List[ServiceHealthStatus]:
        """Get health history for a specific service."""
        history = self._health_history.get(service_name, [])
        return history[-limit:] if limit > 0 else history


# Global service registry instance
_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return _service_registry


def register_service(name: str, service: Any) -> None:
    """Register a service in the global registry."""
    _service_registry.register_service(name, service)


def get_service(name: str) -> Optional[Any]:
    """Get a service from the global registry."""
    return _service_registry.get_service(name)


# Dependency injection helpers
async def get_credential_analyzer() -> Optional[CredentialAnalyzerInterface]:
    """Get credential analyzer service."""
    return get_service("credential_analyzer")


async def get_behavioral_embedding() -> Optional[BehavioralEmbeddingInterface]:
    """Get behavioral embedding service."""
    return get_service("behavioral_embedding")


async def get_anomaly_detector() -> Optional[AnomalyDetectorInterface]:
    """Get anomaly detector service."""
    return get_service("anomaly_detector")


async def get_threat_intelligence() -> Optional[ThreatIntelligenceInterface]:
    """Get threat intelligence service."""
    return get_service("threat_intelligence")


async def get_intelligent_auth_service() -> Optional[IntelligentAuthServiceInterface]:
    """Get main intelligent authentication service."""
    return get_service("intelligent_auth_service")