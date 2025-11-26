"""
Base Service Class

This module provides the base class that all services in the KAREN AI system should extend.
It provides common functionality such as initialization, configuration, logging, and metrics.
"""

import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import logging
from typing import Any, Dict, List, Optional, Union


class BaseService(ABC):
    """
    Base class for all services in the KAREN AI system.
    
    This class provides common functionality that all services need:
    - Initialization and configuration
    - Logging
    - Metrics collection
    - Error handling
    - Health checks
    - Lifecycle management
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service.
        
        Args:
            config: Optional configuration dictionary for the service
        """
        self._config = config or {}
        self._logger = logging.getLogger(self.__class__.__name__)
        self._metrics = SimpleMetricsClient()
        self._error_handler = SimpleErrorHandler()
        self._initialized = False
        self._started = False
        self._stopped = False
        self._health_status = {
            "healthy": False,
            "message": "Service not initialized",
            "timestamp": time.time()
        }
        self._dependencies = {}
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """
        Initialize the service and its dependencies.
        
        This method should be called before using the service.
        It will call the abstract method _initialize_service which should be implemented by subclasses.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        async with self._lock:
            if self._initialized:
                self._logger.warning("Service already initialized")
                return True
                
            try:
                self._logger.info(f"Initializing {self.__class__.__name__}")
                
                # Initialize dependencies
                await self._initialize_dependencies()
                
                # Initialize the service
                await self._initialize_service()
                
                self._initialized = True
                self._update_health_status(True, "Service initialized successfully")
                self._logger.info(f"{self.__class__.__name__} initialized successfully")
                return True
                
            except Exception as e:
                error_msg = f"Failed to initialize {self.__class__.__name__}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                self._update_health_status(False, error_msg)
                await self._error_handler.handle_error(e, context={"service": self.__class__.__name__})
                return False
    
    @abstractmethod
    async def _initialize_service(self) -> None:
        """
        Initialize the service-specific resources.
        
        This method should be implemented by subclasses to initialize
        any resources needed by the service.
        """
        pass
    
    async def _initialize_dependencies(self) -> None:
        """
        Initialize service dependencies.
        
        This method can be overridden by subclasses to initialize
        any dependencies needed by the service.
        """
        pass
    
    async def start(self) -> bool:
        """
        Start the service.
        
        This method should be called after initialization to start the service.
        It will call the abstract method _start_service which should be implemented by subclasses.
        
        Returns:
            bool: True if the service was started successfully, False otherwise
        """
        async with self._lock:
            if not self._initialized:
                self._logger.error("Cannot start service before initialization")
                return False
                
            if self._started:
                self._logger.warning("Service already started")
                return True
                
            try:
                self._logger.info(f"Starting {self.__class__.__name__}")
                
                # Start the service
                await self._start_service()
                
                self._started = True
                self._stopped = False
                self._update_health_status(True, "Service started successfully")
                self._logger.info(f"{self.__class__.__name__} started successfully")
                return True
                
            except Exception as e:
                error_msg = f"Failed to start {self.__class__.__name__}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                self._update_health_status(False, error_msg)
                await self._error_handler.handle_error(e, context={"service": self.__class__.__name__})
                return False
    
    @abstractmethod
    async def _start_service(self) -> None:
        """
        Start the service-specific resources.
        
        This method should be implemented by subclasses to start
        any resources needed by the service.
        """
        pass
    
    async def stop(self) -> bool:
        """
        Stop the service.
        
        This method should be called to gracefully stop the service.
        It will call the abstract method _stop_service which should be implemented by subclasses.
        
        Returns:
            bool: True if the service was stopped successfully, False otherwise
        """
        async with self._lock:
            if not self._started:
                self._logger.warning("Service not started")
                return True
                
            if self._stopped:
                self._logger.warning("Service already stopped")
                return True
                
            try:
                self._logger.info(f"Stopping {self.__class__.__name__}")
                
                # Stop the service
                await self._stop_service()
                
                self._started = False
                self._stopped = True
                self._update_health_status(False, "Service stopped")
                self._logger.info(f"{self.__class__.__name__} stopped successfully")
                return True
                
            except Exception as e:
                error_msg = f"Failed to stop {self.__class__.__name__}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                self._update_health_status(False, error_msg)
                await self._error_handler.handle_error(e, context={"service": self.__class__.__name__})
                return False
    
    @abstractmethod
    async def _stop_service(self) -> None:
        """
        Stop the service-specific resources.
        
        This method should be implemented by subclasses to stop
        any resources used by the service.
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the service.
        
        This method checks the health of the service and its dependencies.
        It will call the abstract method _health_check_service which should be implemented by subclasses.
        
        Returns:
            Dict[str, Any]: A dictionary containing the health status of the service
        """
        async with self._lock:
            health_info = {
                "service": self.__class__.__name__,
                "initialized": self._initialized,
                "started": self._started,
                "stopped": self._stopped,
                "dependencies": await self._check_dependencies(),
                "timestamp": time.time()
            }
            
            # Check the service-specific health
            try:
                service_health = await self._health_check_service()
                health_info.update(service_health)
                
                # Update overall health status
                if service_health.get("healthy", True) and health_info["dependencies"]["healthy"]:
                    self._update_health_status(True, "Service is healthy")
                else:
                    self._update_health_status(False, "Service is unhealthy")
                    
            except Exception as e:
                error_msg = f"Health check failed for {self.__class__.__name__}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                self._update_health_status(False, error_msg)
                health_info["error"] = error_msg
                health_info["traceback"] = traceback.format_exc()
            
            health_info["health_status"] = self._health_status
            return health_info
    
    @abstractmethod
    async def _health_check_service(self) -> Dict[str, Any]:
        """
        Check the health of the service-specific resources.
        
        This method should be implemented by subclasses to check
        the health of any resources used by the service.
        
        Returns:
            Dict[str, Any]: A dictionary containing the health status of the service
        """
        pass
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """
        Check the health of the service dependencies.
        
        Returns:
            Dict[str, Any]: A dictionary containing the health status of the dependencies
        """
        dependency_health = {
            "healthy": True,
            "dependencies": {}
        }
        
        for name, dependency in self._dependencies.items():
            try:
                if hasattr(dependency, "health_check"):
                    health = await dependency.health_check()
                    dependency_health["dependencies"][name] = health
                    if not health.get("healthy", True):
                        dependency_health["healthy"] = False
                else:
                    dependency_health["dependencies"][name] = {
                        "healthy": True,
                        "message": "No health check method"
                    }
            except Exception as e:
                error_msg = f"Dependency health check failed for {name}: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                dependency_health["dependencies"][name] = {
                    "healthy": False,
                    "error": error_msg
                }
                dependency_health["healthy"] = False
        
        return dependency_health
    
    def _update_health_status(self, healthy: bool, message: str) -> None:
        """
        Update the health status of the service.
        
        Args:
            healthy: Whether the service is healthy
            message: A message describing the health status
        """
        self._health_status = {
            "healthy": healthy,
            "message": message,
            "timestamp": time.time()
        }
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: The default value to return if the key is not found
            
        Returns:
            Any: The configuration value or the default value
        """
        return self._config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The configuration value
        """
        self._config[key] = value
    
    def get_logger(self) -> logging.Logger:
        """
        Get the logger for the service.
        
        Returns:
            logging.Logger: The logger for the service
        """
        return self._logger
    
    def get_metrics(self) -> 'SimpleMetricsClient':
        """
        Get the metrics client for the service.
        
        Returns:
            MetricsClient: The metrics client for the service
        """
        return self._metrics
    
    def get_error_handler(self) -> 'SimpleErrorHandler':
        """
        Get the error handler for the service.
        
        Returns:
            ErrorHandler: The error handler for the service
        """
        return self._error_handler
    
    def add_dependency(self, name: str, dependency: Any) -> None:
        """
        Add a dependency to the service.
        
        Args:
            name: The name of the dependency
            dependency: The dependency object
        """
        self._dependencies[name] = dependency
    
    def remove_dependency(self, name: str) -> bool:
        """
        Remove a dependency from the service.
        
        Args:
            name: The name of the dependency
            
        Returns:
            bool: True if the dependency was removed, False otherwise
        """
        if name in self._dependencies:
            del self._dependencies[name]
            return True
        return False
    
    def get_dependency(self, name: str) -> Optional[Any]:
        """
        Get a dependency by name.
        
        Args:
            name: The name of the dependency
            
        Returns:
            Optional[Any]: The dependency object or None if not found
        """
        return self._dependencies.get(name)
    
    async def execute_with_metrics(self, operation_name: str, func, *args, **kwargs) -> Any:
        """
        Execute a function with metrics collection.
        
        Args:
            operation_name: The name of the operation for metrics
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: The result of the function
        """
        start_time = time.time()
        success = False
        result = None
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            self._logger.error(f"Error executing {operation_name}: {str(e)}", exc_info=True)
            await self._error_handler.handle_error(e, context={"operation": operation_name})
            raise
        finally:
            duration = time.time() - start_time
            self._metrics.record_timing(operation_name, duration)
            self._metrics.increment_counter(f"{operation_name}_count", 1)
            if success:
                self._metrics.increment_counter(f"{operation_name}_success_count", 1)
            else:
                self._metrics.increment_counter(f"{operation_name}_failure_count", 1)
    
    async def execute_with_retry(self, operation_name: str, func, max_retries: int = 3, 
                               retry_delay: float = 1.0, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            operation_name: The name of the operation for metrics
            func: The function to execute
            max_retries: The maximum number of retries
            retry_delay: The delay between retries in seconds
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Any: The result of the function
            
        Raises:
            Exception: If the function fails after all retries
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.execute_with_metrics(operation_name, func, *args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    self._logger.warning(f"Attempt {attempt + 1} failed for {operation_name}, retrying in {retry_delay}s: {str(e)}")
                    await asyncio.sleep(retry_delay)
                else:
                    self._logger.error(f"All {max_retries + 1} attempts failed for {operation_name}: {str(e)}")
        
        if last_exception is not None:
            raise last_exception
        else:
            raise RuntimeError("All attempts failed but no exception was captured")
    
    async def execute_with_fallback(self, operation_name: str, primary_func, fallback_func, 
                                 *args, **kwargs) -> Any:
        """
        Execute a function with fallback logic.
        
        Args:
            operation_name: The name of the operation for metrics
            primary_func: The primary function to execute
            fallback_func: The fallback function to execute if the primary fails
            *args: Arguments to pass to the functions
            **kwargs: Keyword arguments to pass to the functions
            
        Returns:
            Any: The result of the primary function or the fallback function
        """
        try:
            return await self.execute_with_metrics(operation_name, primary_func, *args, **kwargs)
        except Exception as e:
            self._logger.warning(f"Primary function failed for {operation_name}, using fallback: {str(e)}")
            self._metrics.increment_counter(f"{operation_name}_fallback_count", 1)
            return await self.execute_with_metrics(f"{operation_name}_fallback", fallback_func, *args, **kwargs)
    
    def is_initialized(self) -> bool:
        """
        Check if the service is initialized.
        
        Returns:
            bool: True if the service is initialized, False otherwise
        """
        return self._initialized
    
    def is_started(self) -> bool:
        """
        Check if the service is started.
        
        Returns:
            bool: True if the service is started, False otherwise
        """
        return self._started
    
    def is_stopped(self) -> bool:
        """
        Check if the service is stopped.
        
        Returns:
            bool: True if the service is stopped, False otherwise
        """
        return self._stopped
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the service.
        
        Returns:
            Dict[str, Any]: A dictionary containing the health status of the service
        """
        return self._health_status


class SimpleMetricsClient:
    """Simple metrics client for demonstration purposes."""
    
    def __init__(self):
        self._counters = {}
        self._timings = {}
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None) -> None:
        if tags is None:
            tags = {}
        """Increment a counter metric."""
        if name not in self._counters:
            self._counters[name] = 0
        self._counters[name] += value
    
    def record_timing(self, name: str, value: float) -> None:
        """Record a timing metric."""
        if name not in self._timings:
            self._timings[name] = []
        self._timings[name].append(value)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": self._counters,
            "timings": {name: {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0
            } for name, values in self._timings.items()}
        }


class SimpleErrorHandler:
    """Simple error handler for demonstration purposes."""
    
    def __init__(self):
        self._errors = []
    
    async def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        if context is None:
            context = {}
        """Handle an error."""
        error_info = {
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {},
            "timestamp": time.time()
        }
        self._errors.append(error_info)
        logging.error(f"Error handled: {error_info}")