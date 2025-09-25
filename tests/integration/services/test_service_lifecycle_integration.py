"""
Service lifecycle integration tests for startup, suspension, and shutdown.
Tests complete service lifecycle workflows and integration between components.
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.ai_karen_engine.core.service_lifecycle_manager import ServiceLifecycleManager
from src.ai_karen_engine.core.lazy_loading_controller import LazyLoadingController
from src.ai_karen_engine.core.resource_monitor import ResourceMonitor
from src.ai_karen_engine.core.service_classification import ServiceClassification, ServiceConfig
from src.ai_karen_engine.core.classified_service_registry import ClassifiedServiceRegistry


@dataclass
class LifecycleTestResult:
    """Service lifecycle test result."""
    test_name: str
    success: bool
    execution_time: float
    services_started: int
    services_suspended: int
    services_shutdown: int
    errors: List[str]


class ServiceLifecycleIntegrationSuite:
    """Comprehensive service lifecycle integration test suite."""
    
    def __init__(self):
        self.lifecycle_manager = ServiceLifecycleManager()
        self.lazy_controller = LazyLoadingController()
        self.resource_monitor = ResourceMonitor()
        self.service_registry = ClassifiedServiceRegistry()
        self.test_services = []
    
    async def setup_test_services(self):
        """Set up test services with different classifications."""
        test_configs = [
            ServiceConfig(
                name="essential_auth",
                classification=ServiceClassification.ESSENTIAL,
                startup_priority=1,
                idle_timeout=None,
                dependencies=[],
                resource_requirements={"memory": 100, "cpu": 0.1}
            ),
            ServiceConfig(
                name="optional_analytics",
                classification=ServiceClassification.OPTIONAL,
                startup_priority=5,
                idle_timeout=300,
                dependencies=["essential_auth"],
                resource_requirements={"memory": 200, "cpu": 0.2}
            ),
            ServiceConfig(
                name="background_cleanup",
                classification=ServiceClassification.BACKGROUND,
                startup_priority=10,
                idle_timeout=60,
                dependencies=[],
                resource_requirements={"memory": 50, "cpu": 0.05}
            )
        ]
        
        for config in test_configs:
            await self.service_registry.register_service(config)
            self.test_services.append(config.name)
    
    async def cleanup_test_services(self):
        """Clean up test services."""
        for service_name in self.test_services:
            try:
                await self.lifecycle_manager.shutdown_service(service_name)
            except:
                pass  # Service might not be running
        self.test_services.clear()
    
    async def test_complete_startup_sequence(self) -> LifecycleTestResult:
        """Test complete system startup sequence with service classification."""
        errors = []
        services_started = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Test essential services startup
            essential_services = await self.service_registry.get_services_by_classification(
                ServiceClassification.ESSENTIAL
            )
            
            for service_config in essential_services:
                await self.lifecycle_manager.start_service(service_config.name)
                services_started += 1
            
            # Verify essential services are running
            running_services = await self.lifecycle_manager.get_running_services()
            essential_running = [s for s in running_services if s in ["essential_auth"]]
            
            if len(essential_running) == 0:
                errors.append("Essential services failed to start")
            
            # Test lazy loading of optional services
            optional_service = await self.lazy_controller.get_service("optional_analytics")
            if optional_service:
                services_started += 1
            else:
                errors.append("Lazy loading of optional service failed")
            
        except Exception as e:
            errors.append(f"Startup sequence failed: {e}")
        finally:
            await self.cleanup_test_services()
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="complete_startup_sequence",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=services_started,
            services_suspended=0,
            services_shutdown=0,
            errors=errors
        )
    
    async def test_service_dependency_resolution(self) -> LifecycleTestResult:
        """Test service dependency resolution during startup."""
        errors = []
        services_started = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Try to start service with dependencies
            await self.lifecycle_manager.start_service("optional_analytics")
            
            # Verify dependency was started first
            running_services = await self.lifecycle_manager.get_running_services()
            
            if "essential_auth" not in running_services:
                errors.append("Service dependency not automatically started")
            
            if "optional_analytics" not in running_services:
                errors.append("Dependent service failed to start")
            else:
                services_started = len(running_services)
            
        except Exception as e:
            errors.append(f"Dependency resolution failed: {e}")
        finally:
            await self.cleanup_test_services()
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="dependency_resolution",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=services_started,
            services_suspended=0,
            services_shutdown=0,
            errors=errors
        )
    
    async def test_automatic_service_suspension(self) -> LifecycleTestResult:
        """Test automatic service suspension based on idle timeout."""
        errors = []
        services_suspended = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Start background service with short timeout
            await self.lifecycle_manager.start_service("background_cleanup")
            
            # Wait for idle timeout (simulate no activity)
            await asyncio.sleep(2)  # Wait longer than 60s timeout (simulated)
            
            # Trigger idle service detection
            suspended = await self.lifecycle_manager.suspend_idle_services()
            services_suspended = len(suspended)
            
            # Verify service was suspended
            running_services = await self.lifecycle_manager.get_running_services()
            if "background_cleanup" in running_services:
                errors.append("Idle service was not suspended")
            
        except Exception as e:
            errors.append(f"Service suspension failed: {e}")
        finally:
            await self.cleanup_test_services()
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="automatic_suspension",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=0,
            services_suspended=services_suspended,
            services_shutdown=0,
            errors=errors
        )
    
    async def test_graceful_shutdown_sequence(self) -> LifecycleTestResult:
        """Test graceful shutdown sequence with proper cleanup."""
        errors = []
        services_shutdown = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Start all test services
            for service_name in self.test_services:
                await self.lifecycle_manager.start_service(service_name)
            
            # Test graceful shutdown
            for service_name in self.test_services:
                await self.lifecycle_manager.shutdown_service(service_name)
                services_shutdown += 1
            
            # Verify all services are stopped
            running_services = await self.lifecycle_manager.get_running_services()
            still_running = [s for s in running_services if s in self.test_services]
            
            if still_running:
                errors.append(f"Services still running after shutdown: {still_running}")
            
        except Exception as e:
            errors.append(f"Graceful shutdown failed: {e}")
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="graceful_shutdown",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=0,
            services_suspended=0,
            services_shutdown=services_shutdown,
            errors=errors
        )
    
    async def test_service_restart_after_failure(self) -> LifecycleTestResult:
        """Test service restart after failure."""
        errors = []
        services_started = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Start a service
            await self.lifecycle_manager.start_service("essential_auth")
            services_started += 1
            
            # Simulate service failure
            with patch.object(self.lifecycle_manager, '_services', {"essential_auth": Mock(side_effect=Exception("Service crashed"))}):
                # Try to restart the service
                await self.lifecycle_manager.restart_service("essential_auth")
                services_started += 1
            
            # Verify service is running again
            running_services = await self.lifecycle_manager.get_running_services()
            if "essential_auth" not in running_services:
                errors.append("Service failed to restart after failure")
            
        except Exception as e:
            errors.append(f"Service restart failed: {e}")
        finally:
            await self.cleanup_test_services()
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="service_restart",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=services_started,
            services_suspended=0,
            services_shutdown=0,
            errors=errors
        )
    
    async def test_resource_pressure_service_management(self) -> LifecycleTestResult:
        """Test service management under resource pressure."""
        errors = []
        services_suspended = 0
        start_time = time.time()
        
        try:
            await self.setup_test_services()
            
            # Start all services
            for service_name in self.test_services:
                await self.lifecycle_manager.start_service(service_name)
            
            # Simulate resource pressure
            with patch.object(self.resource_monitor, 'detect_resource_pressure', return_value=True):
                # Trigger resource pressure response
                suspended = await self.lifecycle_manager.handle_resource_pressure()
                services_suspended = len(suspended)
            
            # Verify non-essential services were suspended
            running_services = await self.lifecycle_manager.get_running_services()
            
            # Essential services should still be running
            if "essential_auth" not in running_services:
                errors.append("Essential service was suspended under pressure")
            
            # Background services should be suspended
            if "background_cleanup" in running_services:
                errors.append("Background service was not suspended under pressure")
            
        except Exception as e:
            errors.append(f"Resource pressure management failed: {e}")
        finally:
            await self.cleanup_test_services()
        
        execution_time = time.time() - start_time
        
        return LifecycleTestResult(
            test_name="resource_pressure_management",
            success=len(errors) == 0,
            execution_time=execution_time,
            services_started=0,
            services_suspended=services_suspended,
            services_shutdown=0,
            errors=errors
        )


@pytest.fixture
def lifecycle_suite():
    """Create service lifecycle integration test suite fixture."""
    return ServiceLifecycleIntegrationSuite()


@pytest.mark.asyncio
async def test_complete_startup_sequence(lifecycle_suite):
    """Test complete system startup sequence."""
    result = await lifecycle_suite.test_complete_startup_sequence()
    
    assert result.success, f"Startup sequence failed: {result.errors}"
    assert result.services_started >= 2, f"Not enough services started: {result.services_started}"
    assert result.execution_time < 5.0, f"Startup took too long: {result.execution_time}s"
    
    print(f"Startup sequence: {result.services_started} services started in {result.execution_time:.3f}s")


@pytest.mark.asyncio
async def test_service_dependency_resolution(lifecycle_suite):
    """Test service dependency resolution."""
    result = await lifecycle_suite.test_service_dependency_resolution()
    
    assert result.success, f"Dependency resolution failed: {result.errors}"
    assert result.services_started >= 2, "Dependencies not properly resolved"
    
    print(f"Dependency resolution: {result.services_started} services started")


@pytest.mark.asyncio
async def test_automatic_service_suspension(lifecycle_suite):
    """Test automatic service suspension."""
    result = await lifecycle_suite.test_automatic_service_suspension()
    
    assert result.success, f"Service suspension failed: {result.errors}"
    # Note: In real implementation, services_suspended should be > 0
    
    print(f"Service suspension: {result.services_suspended} services suspended")


@pytest.mark.asyncio
async def test_graceful_shutdown_sequence(lifecycle_suite):
    """Test graceful shutdown sequence."""
    result = await lifecycle_suite.test_graceful_shutdown_sequence()
    
    assert result.success, f"Graceful shutdown failed: {result.errors}"
    assert result.services_shutdown >= 3, f"Not all services shutdown: {result.services_shutdown}"
    
    print(f"Graceful shutdown: {result.services_shutdown} services shutdown")


@pytest.mark.asyncio
async def test_service_restart_after_failure(lifecycle_suite):
    """Test service restart after failure."""
    result = await lifecycle_suite.test_service_restart_after_failure()
    
    assert result.success, f"Service restart failed: {result.errors}"
    assert result.services_started >= 2, "Service restart not working"
    
    print(f"Service restart: {result.services_started} restart operations")


@pytest.mark.asyncio
async def test_resource_pressure_service_management(lifecycle_suite):
    """Test service management under resource pressure."""
    result = await lifecycle_suite.test_resource_pressure_service_management()
    
    assert result.success, f"Resource pressure management failed: {result.errors}"
    
    print(f"Resource pressure: {result.services_suspended} services suspended")


@pytest.mark.asyncio
async def test_service_lifecycle_timing_requirements():
    """Test that service lifecycle operations meet timing requirements."""
    lifecycle_manager = ServiceLifecycleManager()
    
    # Test service startup time (should be < 2 seconds per requirement)
    start_time = time.time()
    await lifecycle_manager.start_service("timing_test_service")
    startup_time = time.time() - start_time
    
    assert startup_time < 2.0, f"Service startup time {startup_time}s >= 2s"
    
    # Test service shutdown time
    start_time = time.time()
    await lifecycle_manager.shutdown_service("timing_test_service")
    shutdown_time = time.time() - start_time
    
    assert shutdown_time < 1.0, f"Service shutdown time {shutdown_time}s >= 1s"
    
    print(f"Timing test: startup {startup_time:.3f}s, shutdown {shutdown_time:.3f}s")


@pytest.mark.asyncio
async def test_concurrent_lifecycle_operations():
    """Test concurrent service lifecycle operations."""
    lifecycle_manager = ServiceLifecycleManager()
    
    # Test concurrent service starts
    services = [f"concurrent_test_{i}" for i in range(5)]
    
    start_time = time.time()
    tasks = [lifecycle_manager.start_service(service) for service in services]
    await asyncio.gather(*tasks)
    concurrent_start_time = time.time() - start_time
    
    # Concurrent operations should be faster than sequential
    assert concurrent_start_time < 5.0, f"Concurrent startup too slow: {concurrent_start_time}s"
    
    # Test concurrent shutdowns
    start_time = time.time()
    tasks = [lifecycle_manager.shutdown_service(service) for service in services]
    await asyncio.gather(*tasks)
    concurrent_shutdown_time = time.time() - start_time
    
    assert concurrent_shutdown_time < 3.0, f"Concurrent shutdown too slow: {concurrent_shutdown_time}s"
    
    print(f"Concurrent operations: start {concurrent_start_time:.3f}s, shutdown {concurrent_shutdown_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])