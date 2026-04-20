"""
Test script for Phase 4: Service Integration Hardening

Tests the enhanced security manager, service health dashboard, and dependency injection system.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# Reset Prometheus registry to avoid duplicate metrics
try:
    import prometheus_client
    from prometheus_client import CollectorRegistry

    # Clear all existing collectors
    if hasattr(prometheus_client.REGISTRY, "_collector_to_names"):
        prometheus_client.REGISTRY._collector_to_names.clear()
    if hasattr(prometheus_client.REGISTRY, "_names_to_collectors"):
        prometheus_client.REGISTRY._names_to_collectors.clear()
    # Create new registry
    registry = CollectorRegistry()
    prometheus_client.REGISTRY = registry
except ImportError:
    pass

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_security_manager():
    """Test the enhanced security manager"""
    logger.info("=== Testing Security Manager ===")

    try:
        from ai_karen_engine.core.security_manager import (
            ProviderSecurityManager,
            SecurityPolicy,
            ProviderSecurityConfig,
            AccessLevel,
        )

        # Create security manager
        security_policy = SecurityPolicy(
            max_login_attempts=3,
            account_lockout_duration=60,
            session_timeout=3600,
            enable_audit_logging=True,
        )

        security_manager = ProviderSecurityManager(security_policy)

        # Test provider security configuration
        config = ProviderSecurityConfig(
            provider_name="test_provider",
            access_level=AccessLevel.READ_WRITE,
            api_key_required=True,
            rate_limit_per_minute=30,
        )

        security_manager.set_provider_security_config("test_provider", config)

        # Test access validation
        user_context = {"user_id": "test_user", "api_key": "test_key"}
        has_access = security_manager.validate_provider_access(
            "test_provider", AccessLevel.READ_WRITE, user_context
        )
        logger.info(f"Access validation result: {has_access}")

        # Test API key generation
        api_key = security_manager.generate_api_key("test_provider", "test_user", 3600)
        logger.info(f"Generated API key: {api_key[:20]}...")

        # Test security event logging
        security_events = security_manager.get_security_events(limit=5)
        logger.info(f"Security events count: {len(security_events)}")

        # Test security status
        status = security_manager.get_provider_security_status("test_provider")
        logger.info(f"Provider security status: {status}")

        # Test security audit export
        export_success = security_manager.export_security_audit(
            "/tmp/security_audit.json"
        )
        logger.info(f"Security audit export: {export_success}")

        # Test security summary
        summary = security_manager.get_security_summary()
        logger.info(f"Security summary: {json.dumps(summary, indent=2, default=str)}")

        logger.info("✓ Security manager tests passed")
        return True

    except Exception as e:
        logger.error(f"Security manager test failed: {e}")
        return False


async def test_service_health_dashboard():
    """Test the service health dashboard"""
    logger.info("=== Testing Service Health Dashboard ===")

    try:
        from ai_karen_engine.core.service_health_dashboard import (
            ServiceHealthDashboard,
            HealthCheck,
            HealthStatus,
            ServiceType,
            HealthMetric,
        )

        # Create dashboard
        dashboard = ServiceHealthDashboard()

        # Test health check recording
        health_check = HealthCheck(
            service_name="test_service",
            service_type=ServiceType.PROVIDER,
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            message="Service is healthy",
            metrics=[
                HealthMetric(
                    name="response_time",
                    value=150.0,
                    unit="ms",
                    timestamp=datetime.now(),
                ),
                HealthMetric(
                    name="cpu_usage",
                    value=45.0,
                    unit="percent",
                    timestamp=datetime.now(),
                ),
            ],
        )

        dashboard.record_health_check(health_check)

        # Test service health retrieval
        service_health = dashboard.get_service_health("test_service")
        logger.info(
            f"Service health status: {service_health.status if service_health else 'Not found'}"
        )

        # Test dashboard summary
        summary = dashboard.get_dashboard_summary()
        logger.info(f"Dashboard summary: {json.dumps(summary, indent=2, default=str)}")

        # Test metrics collection
        metrics = dashboard.get_service_metrics("test_service", "response_time", 60)
        logger.info(f"Response time metrics: {metrics}")

        # Test alert management
        active_alerts = dashboard.get_active_alerts()
        logger.info(f"Active alerts: {len(active_alerts)}")

        # Test health data export
        export_success = dashboard.export_health_data("/tmp/health_data.json")
        logger.info(f"Health data export: {export_success}")

        # Start monitoring
        await dashboard.start_monitoring(10)  # 10 second interval
        await asyncio.sleep(2)  # Let it run for a bit
        await dashboard.stop_monitoring()

        logger.info("✓ Service health dashboard tests passed")
        return True

    except Exception as e:
        logger.error(f"Service health dashboard test failed: {e}")
        return False


async def test_dependency_injection():
    """Test the enhanced dependency injection system"""
    logger.info("=== Testing Dependency Injection ===")

    try:
        from ai_karen_engine.core.enhanced_dependency_injection import (
            DependencyContainer,
            DependencyScope,
            DependencyStatus,
            CircuitBreakerManager,
            DependencyHealthMonitor,
        )

        # Create container
        container = DependencyContainer()

        # Test dependency registration
        class TestService:
            def __init__(self, name: str):
                self.name = name
                self.created_at = time.time()

            def health_check(self) -> bool:
                return True

        container.register(
            name="test_service",
            implementation_type=TestService,
            scope="singleton",
            dependencies=[],
            configuration={"name": "test_instance"},
        )

        # Test dependency resolution
        service = container.resolve("test_service")
        logger.info(f"Resolved service: {service.name}")

        # Test circuit breaker
        circuit_manager = container.resolve("circuit_breaker_manager")
        if circuit_manager:
            status = circuit_manager.get_circuit_breaker_status()
            logger.info(f"Circuit breaker status: {status}")

        # Test health monitoring
        await container.start_health_monitoring()
        await asyncio.sleep(1)  # Let health check run

        health_monitor = container.resolve("health_monitor")
        if health_monitor:
            health_summary = health_monitor.get_system_health_summary()
            logger.info(
                f"Health summary: {json.dumps(health_summary, indent=2, default=str)}"
            )

        await container.stop_health_monitoring()

        # Test scoped container
        with container.create_scope() as scoped_container:
            scoped_service = scoped_container.resolve("test_service")
            logger.info(f"Scoped service: {scoped_service.name}")

        # Test container disposal
        container.dispose()

        logger.info("✓ Dependency injection tests passed")
        return True

    except Exception as e:
        logger.error(f"Dependency injection test failed: {e}")
        return False


async def test_integration():
    """Test integration between all components"""
    logger.info("=== Testing Integration ===")

    try:
        from ai_karen_engine.core.security_manager import ProviderSecurityManager
        from ai_karen_engine.core.service_health_dashboard import (
            ServiceHealthDashboard,
            HealthCheck,
            HealthStatus,
            ServiceType,
        )
        from ai_karen_engine.core.enhanced_dependency_injection import (
            DependencyContainer,
        )

        # Create components
        security_manager = ProviderSecurityManager()
        dashboard = ServiceHealthDashboard()
        container = DependencyContainer()

        # Integrate security with health dashboard
        class SecureService:
            def __init__(self, security_manager):
                self.security_manager = security_manager
                self.name = "secure_service"

            def health_check(self) -> bool:
                return True

            def process_request(self, user_context: Dict[str, Any]) -> str:
                # Validate access
                if self.security_manager.validate_provider_access(
                    "secure_service", "read_write", user_context
                ):
                    return "Access granted"
                else:
                    return "Access denied"

        # Register secure service
        container.register(
            name="secure_service",
            implementation_type=SecureService,
            dependencies=["security_manager"],
            configuration={},
        )

        # Start monitoring
        await container.start_health_monitoring()
        await dashboard.start_monitoring(10)

        # Test integration
        secure_service = container.resolve("secure_service")

        # Test with valid user
        user_context = {"user_id": "test_user", "api_key": "test_key"}
        result = secure_service.process_request(user_context)
        logger.info(f"Secure service result: {result}")

        # Test health check
        health_check = HealthCheck(
            service_name="secure_service",
            service_type=ServiceType.PROVIDER,
            status=HealthStatus.HEALTHY,
            timestamp=datetime.now(),
            message="Secure service is healthy",
            metrics=[
                {
                    "name": "security_checks",
                    "value": 10,
                    "unit": "count",
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        )

        dashboard.record_health_check(health_check)

        # Stop monitoring
        await container.stop_health_monitoring()
        await dashboard.stop_monitoring()

        # Export integration report
        integration_report = {
            "timestamp": datetime.now().isoformat(),
            "security_summary": security_manager.get_security_summary(),
            "dashboard_summary": dashboard.get_dashboard_summary(),
            "container_health": container.resolve(
                "health_monitor"
            ).get_system_health_summary(),
        }

        with open("/tmp/integration_report.json", "w") as f:
            json.dump(integration_report, f, indent=2, default=str)

        logger.info("✓ Integration tests passed")
        return True

    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("Starting Phase 4: Service Integration Hardening tests")

    test_results = {
        "security_manager": await test_security_manager(),
        "service_health_dashboard": await test_service_health_dashboard(),
        "dependency_injection": await test_dependency_injection(),
        "integration": await test_integration(),
    }

    logger.info("\n=== Test Results ===")
    for test_name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")

    passed_tests = sum(test_results.values())
    total_tests = len(test_results)

    logger.info(f"\nSummary: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        logger.info("🎉 All Phase 4 tests passed!")
        return True
    else:
        logger.error("❌ Some Phase 4 tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
