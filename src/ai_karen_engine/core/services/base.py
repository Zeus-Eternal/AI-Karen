"""
Base service classes and interfaces for the AI Karen engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from enum import Enum
try:
    from pydantic import BaseModel, ConfigDict
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict
import logging
import asyncio
from datetime import datetime


class ServiceStatus(str, Enum):
    """Service lifecycle status."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServiceConfig(BaseModel):
    """Base configuration for services."""
    name: str
    enabled: bool = True
    dependencies: List[str] = []
    config: Dict[str, Any] = {}
    timeout: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 60


class ServiceHealth(BaseModel):
    """Service health information."""
    status: ServiceStatus
    last_check: datetime
    error_message: Optional[str] = None
    uptime: float = 0.0
    metrics: Dict[str, Any] = {}


class BaseService(ABC):
    """
    Abstract base class for all services in the AI Karen engine.
    
    Provides common functionality for service lifecycle management,
    health checking, and dependency management.
    """
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = logging.getLogger(f"service.{config.name}")
        self._status = ServiceStatus.INITIALIZING
        self._start_time: Optional[datetime] = None
        self._health: ServiceHealth = ServiceHealth(
            status=ServiceStatus.INITIALIZING,
            last_check=datetime.now()
        )
        self._shutdown_event = asyncio.Event()
    
    @property
    def name(self) -> str:
        """Service name."""
        return self.config.name
    
    @property
    def status(self) -> ServiceStatus:
        """Current service status."""
        return self._status
    
    @property
    def health(self) -> ServiceHealth:
        """Current service health."""
        return self._health
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service.
        Called once during service startup.
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """
        Start the service.
        Called after initialization is complete.
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the service gracefully.
        Called during service shutdown.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Perform a health check.
        Returns True if service is healthy, False otherwise.
        """
        pass
    
    async def startup(self) -> None:
        """
        Complete service startup sequence.
        """
        try:
            self._status = ServiceStatus.INITIALIZING
            self.logger.info(f"Initializing service: {self.name}")
            
            await self.initialize()
            
            self._status = ServiceStatus.READY
            self.logger.info(f"Starting service: {self.name}")
            
            await self.start()
            
            self._status = ServiceStatus.RUNNING
            self._start_time = datetime.now()
            self.logger.info(f"Service started: {self.name}")
            
            # Start health check loop
            asyncio.create_task(self._health_check_loop())
            
        except Exception as e:
            self._status = ServiceStatus.ERROR
            self._health.error_message = str(e)
            self.logger.error(f"Failed to start service {self.name}: {e}")
            raise
    
    async def shutdown(self) -> None:
        """
        Complete service shutdown sequence.
        """
        try:
            self._status = ServiceStatus.STOPPING
            self.logger.info(f"Stopping service: {self.name}")
            
            # Signal shutdown to health check loop
            self._shutdown_event.set()
            
            await self.stop()
            
            self._status = ServiceStatus.STOPPED
            self.logger.info(f"Service stopped: {self.name}")
            
        except Exception as e:
            self._status = ServiceStatus.ERROR
            self._health.error_message = str(e)
            self.logger.error(f"Failed to stop service {self.name}: {e}")
            raise
    
    async def _health_check_loop(self) -> None:
        """
        Background health check loop.
        """
        while not self._shutdown_event.is_set():
            try:
                is_healthy = await self.health_check()
                
                self._health.last_check = datetime.now()
                if self._start_time:
                    self._health.uptime = (datetime.now() - self._start_time).total_seconds()
                
                if not is_healthy and self._status == ServiceStatus.RUNNING:
                    self._status = ServiceStatus.ERROR
                    self.logger.warning(f"Health check failed for service: {self.name}")
                elif is_healthy and self._status == ServiceStatus.ERROR:
                    self._status = ServiceStatus.RUNNING
                    self.logger.info(f"Health check recovered for service: {self.name}")
                
                self._health.status = self._status
                
            except Exception as e:
                self.logger.error(f"Health check error for service {self.name}: {e}")
                self._health.error_message = str(e)
            
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.health_check_interval
                )
                break  # Shutdown event was set
            except asyncio.TimeoutError:
                continue  # Continue health check loop
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.
        Override in subclasses to provide custom metrics.
        """
        return {
            "status": self.status.value,
            "uptime": self._health.uptime,
            "last_health_check": self._health.last_check.isoformat(),
            "error_message": self._health.error_message
        }


class SingletonService(BaseService):
    """
    Base class for singleton services.
    Ensures only one instance of the service exists.
    """
    
    _instances: Dict[str, 'SingletonService'] = {}
    
    def __new__(cls, config: ServiceConfig):
        if config.name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[config.name] = instance
        return cls._instances[config.name]