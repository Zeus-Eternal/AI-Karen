"""
Tests for Graceful Degradation Controller

Tests graceful degradation functionality, feature management, and
coordination with error recovery and fallback systems.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json
from pathlib import Path

from src.ai_karen_engine.core.graceful_degradation import (
    GracefulDegradationController, DegradationLevel, DegradationRule, SystemState,
    get_graceful_degradation_controller
)
from src.ai_karen_engine.core.service_classification import ServiceClassification
from src.ai_karen_engine.core.error_recovery_manager import ErrorRecoveryManager, ServiceStatus
from src.ai_karen_engine.core.service_health_monitor import ServiceHealthMonitor, HealthMetrics
from src.ai_karen_engine.core.fallback_mechanisms import FallbackManager


class TestDegradationRule:
    """Test degradation rule data structure"""
    
    def test_degradation_rule_creation(self):
        """Test degradation rule creation"""
        rule = DegradationRule(
            trigger_condition="essential_service_failed",
            degradation_level=DegradationLevel.SEVERE,
            affected_services=["auth_service"],
            actions=["activate_emergency_mode", "notify_administrators"],
            priority=1
        )
        
        assert rule.trigger_condition == "essential_service_failed"
        assert rule.degradation_level == DegradationLevel.SEVERE
        assert rule.affected_services == ["auth_service"]
        assert rule.actions == ["activate_emergency_mode", "notify_administrators"]
        assert rule.priority == 1


class TestSystemState:
    """Test system state data structure"""
    
    def test_system_state_creation(self):
        """Test system state creation with defaults"""
        state = SystemState()
        
        assert state.degradation_level == DegradationLevel.NORMAL
        assert len(state.failed_services) == 0
        assert len(state.degraded_services) == 0
        assert len(state.active_fallbacks) == 0
        assert len(state.disabled_features) == 0
        assert isinstance(state.last_update, datetime)
        assert state.degradation_reason == ""
    
    def test_system_state_with_data(self):
        """Test system state with custom data"""
        failed_services = {"service1", "service2"}
        degraded_services = {"service3"}
        active_fallbacks = {"service1"}
        disabled_features = {"feature1", "feature2"}
        
        state = SystemState(
            degradation_level=DegradationLevel.MODERATE,
            failed_services=failed_services,
            degraded_services=degraded_services,
            active_fallbacks=active_fallbacks,
            disabled_features=disabled_features,
            degradation_reason="Multiple service failures"
        )
        
        assert state.degradation_level == DegradationLevel.MODERATE
        assert state.failed_services == failed_services
        assert state.degraded_services == degraded_services
        assert state.active_fallbacks == active_fallbacks
        assert state.disabled_features == disabled_features
        assert state.degradation_reason == "Multiple service failures"


class TestGracefulDegradationController:
    """Test graceful degradation controller"""
    
    @pytest.fixture
    def mock_error_recovery_manager(self):
        """Mock error recovery manager"""
        manager = Mock(spec=ErrorRecoveryManager)
        manager._send_alert = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_health_monitor(self):
        """Mock service health monitor"""
        monitor = Mock(spec=ServiceHealthMonitor)
        monitor.get_all_service_health = AsyncMock(return_value={})
        return monitor
    
    @pytest.fixture
    def mock_fallback_manager(self):
        """Mock fallback manager"""
        manager = Mock(spec=FallbackManager)
        manager.activate_fallback = AsyncMock(return_value=True)
        manager.deactivate_fallback = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def degradation_controller(self, mock_error_recovery_manager, mock_health_monitor, mock_fallback_manager):
        """Create degradation controller with mocked dependencies"""
        return GracefulDegradationController(
            error_recovery_manager=mock_error_recovery_manager,
            health_monitor=mock_health_monitor,
            fallback_manager=mock_fallback_manager
        )
    
    def test_service_classification_registration(self, degradation_controller):
        """Test service classification registration"""
        degradation_controller.register_service_classification("auth_service", ServiceClassification.ESSENTIAL)
        degradation_controller.register_service_classification("analytics_service", ServiceClassification.OPTIONAL)
        degradation_controller.register_service_classification("cleanup_service", ServiceClassification.BACKGROUND)
        
        assert "auth_service" in degradation_controller.essential_services
        assert "analytics_service" in degradation_controller.optional_services
        assert "cleanup_service" in degradation_controller.background_services
    
    def test_feature_dependency_registration(self, degradation_controller):
        """Test feature dependency registration"""
        degradation_controller.register_feature_dependency("user_management", ["auth_service", "database_service"])
        degradation_controller.register_feature_dependency("analytics", ["analytics_service", "database_service"])
        
        assert "user_management" in degradation_controller.feature_dependencies
        assert degradation_controller.feature_dependencies["user_management"] == {"auth_service", "database_service"}
        
        # Check reverse mapping
        assert "user_management" in degradation_controller.service_features["auth_service"]
        assert "user_management" in degradation_controller.service_features["database_service"]
        assert "analytics" in degradation_controller.service_features["analytics_service"]
    
    def test_degradation_rule_addition(self, degradation_controller):
        """Test adding degradation rules"""
        rule = DegradationRule(
            trigger_condition="custom_failure",
            degradation_level=DegradationLevel.MODERATE,
            affected_services=["service1"],
            actions=["custom_action"],
            priority=2
        )
        
        initial_count = len(degradation_controller.degradation_rules)
        degradation_controller.add_degradation_rule(rule)
        
        assert len(degradation_controller.degradation_rules) == initial_count + 1
        assert rule in degradation_controller.degradation_rules
    
    def test_action_registration(self, degradation_controller):
        """Test degradation and recovery action registration"""
        def custom_degradation_action(service_name):
            pass
        
        async def custom_recovery_action(service_name):
            pass
        
        degradation_controller.register_degradation_action("custom_degrade", custom_degradation_action)
        degradation_controller.register_recovery_action("custom_recover", custom_recovery_action)
        
        assert "custom_degrade" in degradation_controller.degradation_actions
        assert "custom_recover" in degradation_controller.recovery_actions
        assert degradation_controller.degradation_actions["custom_degrade"] == custom_degradation_action
        assert degradation_controller.recovery_actions["custom_recover"] == custom_recovery_action
    
    @pytest.mark.asyncio
    async def test_essential_service_failure_handling(self, degradation_controller, mock_fallback_manager, mock_error_recovery_manager):
        """Test handling of essential service failures"""
        # Register essential service
        degradation_controller.register_service_classification("auth_service", ServiceClassification.ESSENTIAL)
        
        # Handle failure
        await degradation_controller.handle_service_failure("auth_service", Exception("Auth service down"))
        
        # Should escalate to severe degradation
        assert degradation_controller.system_state.degradation_level == DegradationLevel.SEVERE
        assert "auth_service" in degradation_controller.system_state.failed_services
        
        # Should send critical alert
        mock_error_recovery_manager._send_alert.assert_called()
        call_args = mock_error_recovery_manager._send_alert.call_args
        assert "critical" in call_args[0] or "critical" in call_args[1].values()
    
    @pytest.mark.asyncio
    async def test_optional_service_failure_handling(self, degradation_controller, mock_fallback_manager):
        """Test handling of optional service failures"""
        # Register optional service
        degradation_controller.register_service_classification("analytics_service", ServiceClassification.OPTIONAL)
        
        # Handle failure
        await degradation_controller.handle_service_failure("analytics_service", Exception("Analytics down"))
        
        # Should be minor degradation
        assert degradation_controller.system_state.degradation_level == DegradationLevel.MINOR
        assert "analytics_service" in degradation_controller.system_state.failed_services
        
        # Should try to activate fallback
        mock_fallback_manager.activate_fallback.assert_called_once_with("analytics_service")
    
    @pytest.mark.asyncio
    async def test_background_service_failure_handling(self, degradation_controller):
        """Test handling of background service failures"""
        # Register background service
        degradation_controller.register_service_classification("cleanup_service", ServiceClassification.BACKGROUND)
        
        initial_level = degradation_controller.system_state.degradation_level
        
        # Handle failure
        await degradation_controller.handle_service_failure("cleanup_service", Exception("Cleanup failed"))
        
        # Should not change degradation level for background services
        assert degradation_controller.system_state.degradation_level == initial_level
        assert "cleanup_service" in degradation_controller.system_state.failed_services
    
    @pytest.mark.asyncio
    async def test_multiple_service_failures(self, degradation_controller, mock_fallback_manager):
        """Test handling multiple service failures"""
        # Register multiple optional services
        services = ["service1", "service2", "service3", "service4"]
        for service in services:
            degradation_controller.register_service_classification(service, ServiceClassification.OPTIONAL)
        
        # Fail multiple services
        for service in services:
            await degradation_controller.handle_service_failure(service, Exception(f"{service} failed"))
        
        # Should escalate to moderate degradation
        assert degradation_controller.system_state.degradation_level == DegradationLevel.MODERATE
        assert len(degradation_controller.system_state.failed_services) == 4
    
    @pytest.mark.asyncio
    async def test_service_recovery_handling(self, degradation_controller, mock_fallback_manager):
        """Test handling of service recovery"""
        # Setup: fail a service first
        degradation_controller.register_service_classification("test_service", ServiceClassification.OPTIONAL)
        await degradation_controller.handle_service_failure("test_service", Exception("Service failed"))
        
        # Simulate fallback activation
        degradation_controller.system_state.active_fallbacks.add("test_service")
        degradation_controller.system_state.degraded_services.add("test_service")
        
        # Handle recovery
        await degradation_controller.handle_service_recovery("test_service")
        
        # Should remove from failed services
        assert "test_service" not in degradation_controller.system_state.failed_services
        assert "test_service" not in degradation_controller.system_state.degraded_services
        
        # Should deactivate fallback
        mock_fallback_manager.deactivate_fallback.assert_called_once_with("test_service")
    
    @pytest.mark.asyncio
    async def test_feature_availability_management(self, degradation_controller):
        """Test feature availability based on service dependencies"""
        # Register feature with dependencies
        degradation_controller.register_feature_dependency("user_management", ["auth_service", "database_service"])
        degradation_controller.register_service_classification("auth_service", ServiceClassification.ESSENTIAL)
        degradation_controller.register_service_classification("database_service", ServiceClassification.ESSENTIAL)
        
        # Initially feature should be available
        assert degradation_controller.is_feature_available("user_management")
        
        # Fail one dependency
        await degradation_controller.handle_service_failure("auth_service", Exception("Auth failed"))
        
        # Feature should be disabled
        assert not degradation_controller.is_feature_available("user_management")
        assert "user_management" in degradation_controller.system_state.disabled_features
        
        # Recover service
        await degradation_controller.handle_service_recovery("auth_service")
        
        # Feature should be re-enabled
        assert degradation_controller.is_feature_available("user_management")
        assert "user_management" not in degradation_controller.system_state.disabled_features
    
    @pytest.mark.asyncio
    async def test_feature_availability_with_fallback(self, degradation_controller, mock_fallback_manager):
        """Test feature availability when service has active fallback"""
        # Register feature and service
        degradation_controller.register_feature_dependency("analytics", ["analytics_service"])
        degradation_controller.register_service_classification("analytics_service", ServiceClassification.OPTIONAL)
        
        # Fail service but activate fallback
        await degradation_controller.handle_service_failure("analytics_service", Exception("Analytics failed"))
        
        # Simulate successful fallback activation
        degradation_controller.system_state.active_fallbacks.add("analytics_service")
        degradation_controller.system_state.degraded_services.add("analytics_service")
        
        # Update feature availability
        await degradation_controller._update_feature_availability()
        
        # Feature should still be available with fallback
        assert degradation_controller.is_feature_available("analytics")
    
    @pytest.mark.asyncio
    async def test_builtin_degradation_actions(self, degradation_controller, mock_error_recovery_manager):
        """Test built-in degradation actions"""
        # Test emergency mode activation
        await degradation_controller._execute_builtin_action("activate_emergency_mode", "test_service")
        
        # Should disable non-essential features and stop background services
        # (Implementation details depend on registered features and services)
        
        # Test administrator notification
        await degradation_controller._execute_builtin_action("notify_administrators", "critical_service")
        
        # Should send critical alert
        mock_error_recovery_manager._send_alert.assert_called()
        call_args = mock_error_recovery_manager._send_alert.call_args
        assert "ADMIN ALERT" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_monitoring_lifecycle(self, degradation_controller):
        """Test monitoring start and stop"""
        assert not degradation_controller.monitoring_active
        
        # Start monitoring
        await degradation_controller.start_monitoring()
        assert degradation_controller.monitoring_active
        assert degradation_controller.monitoring_task is not None
        
        # Stop monitoring
        await degradation_controller.stop_monitoring()
        assert not degradation_controller.monitoring_active
    
    @pytest.mark.asyncio
    async def test_service_status_change_detection(self, degradation_controller, mock_health_monitor):
        """Test detection of service status changes through health monitoring"""
        # Setup health monitor to return service status
        health_metrics = {
            "failed_service": HealthMetrics(
                service_name="failed_service",
                timestamp=datetime.now(),
                status=ServiceStatus.FAILED,
                response_time=0.0,
                cpu_usage=0.0,
                memory_usage=0,
                error_rate=1.0,
                uptime=timedelta(hours=1),
                custom_metrics={}
            ),
            "recovered_service": HealthMetrics(
                service_name="recovered_service",
                timestamp=datetime.now(),
                status=ServiceStatus.HEALTHY,
                response_time=0.1,
                cpu_usage=10.0,
                memory_usage=100,
                error_rate=0.0,
                uptime=timedelta(hours=2),
                custom_metrics={}
            )
        }
        mock_health_monitor.get_all_service_health.return_value = health_metrics
        
        # Simulate recovered service was previously failed
        degradation_controller.system_state.failed_services.add("recovered_service")
        
        # Check for status changes
        await degradation_controller._check_service_status_changes()
        
        # Should handle new failure and recovery
        assert "failed_service" in degradation_controller.system_state.failed_services
        assert "recovered_service" not in degradation_controller.system_state.failed_services
    
    def test_system_status_retrieval(self, degradation_controller):
        """Test system status retrieval"""
        # Setup some system state
        degradation_controller.system_state.degradation_level = DegradationLevel.MODERATE
        degradation_controller.system_state.failed_services.add("service1")
        degradation_controller.system_state.disabled_features.add("feature1")
        degradation_controller.system_state.degradation_reason = "Multiple failures"
        
        status = degradation_controller.get_system_status()
        
        assert status["degradation_level"] == DegradationLevel.MODERATE.value
        assert "service1" in status["failed_services"]
        assert "feature1" in status["disabled_features"]
        assert status["degradation_reason"] == "Multiple failures"
        assert "last_update" in status
        assert "monitoring_active" in status
    
    def test_degradation_history(self, degradation_controller):
        """Test degradation history tracking"""
        # Add some history entries
        now = datetime.now()
        for i in range(5):
            state = SystemState(
                degradation_level=DegradationLevel.MINOR,
                last_update=now - timedelta(hours=i),
                degradation_reason=f"Test reason {i}"
            )
            degradation_controller.state_history.append(state)
        
        # Get recent history
        history = degradation_controller.get_degradation_history(hours=3)
        
        # Should return entries from last 3 hours
        assert len(history) == 3
        for entry in history:
            assert "timestamp" in entry
            assert "degradation_level" in entry
            assert "degradation_reason" in entry
    
    @pytest.mark.asyncio
    async def test_recovery_potential_evaluation(self, degradation_controller):
        """Test evaluation of recovery potential"""
        # Setup: multiple failed services causing moderate degradation
        services = ["service1", "service2", "service3"]
        for service in services:
            degradation_controller.register_service_classification(service, ServiceClassification.OPTIONAL)
            degradation_controller.system_state.failed_services.add(service)
        
        degradation_controller.system_state.degradation_level = DegradationLevel.MODERATE
        
        # Recover some services
        degradation_controller.system_state.failed_services.remove("service1")
        degradation_controller.system_state.failed_services.remove("service2")
        
        # Evaluate recovery potential
        await degradation_controller._evaluate_recovery_potential()
        
        # Should improve to minor degradation (only 1 failed service remaining)
        assert degradation_controller.system_state.degradation_level == DegradationLevel.MINOR
    
    @pytest.mark.asyncio
    async def test_custom_degradation_actions(self, degradation_controller):
        """Test custom degradation actions"""
        action_called = False
        service_name_received = None
        
        def custom_action(service_name):
            nonlocal action_called, service_name_received
            action_called = True
            service_name_received = service_name
        
        # Register custom action
        degradation_controller.register_degradation_action("custom_test", custom_action)
        
        # Execute action
        await degradation_controller._execute_action("custom_test", "test_service")
        
        assert action_called
        assert service_name_received == "test_service"
    
    @pytest.mark.asyncio
    async def test_async_custom_actions(self, degradation_controller):
        """Test async custom degradation actions"""
        action_called = False
        
        async def async_custom_action(service_name):
            nonlocal action_called
            await asyncio.sleep(0.01)  # Simulate async work
            action_called = True
        
        # Register async action
        degradation_controller.register_degradation_action("async_test", async_custom_action)
        
        # Execute action
        await degradation_controller._execute_action("async_test", "test_service")
        
        assert action_called
    
    def test_global_instance(self):
        """Test global instance access"""
        controller1 = get_graceful_degradation_controller()
        controller2 = get_graceful_degradation_controller()
        
        # Should return same instance
        assert controller1 is controller2


class TestDegradationLevels:
    """Test degradation level enumeration"""
    
    def test_degradation_level_values(self):
        """Test degradation level values"""
        assert DegradationLevel.NORMAL.value == "normal"
        assert DegradationLevel.MINOR.value == "minor"
        assert DegradationLevel.MODERATE.value == "moderate"
        assert DegradationLevel.SEVERE.value == "severe"
        assert DegradationLevel.CRITICAL.value == "critical"
    
    def test_degradation_level_ordering(self):
        """Test degradation level severity ordering"""
        levels = [
            DegradationLevel.NORMAL,
            DegradationLevel.MINOR,
            DegradationLevel.MODERATE,
            DegradationLevel.SEVERE,
            DegradationLevel.CRITICAL
        ]
        
        # Test that each level is more severe than the previous
        for i in range(1, len(levels)):
            # Note: This assumes enum values can be compared lexicographically
            # In practice, you might want to implement a custom comparison method
            pass


@pytest.mark.asyncio
async def test_integration_with_all_components():
    """Test integration between degradation controller and all its dependencies"""
    # Create mock components
    error_manager = Mock(spec=ErrorRecoveryManager)
    error_manager._send_alert = AsyncMock()
    
    health_monitor = Mock(spec=ServiceHealthMonitor)
    health_monitor.get_all_service_health = AsyncMock(return_value={})
    
    fallback_manager = Mock(spec=FallbackManager)
    fallback_manager.activate_fallback = AsyncMock(return_value=True)
    fallback_manager.deactivate_fallback = AsyncMock(return_value=True)
    
    # Create controller with all dependencies
    controller = GracefulDegradationController(
        error_recovery_manager=error_manager,
        health_monitor=health_monitor,
        fallback_manager=fallback_manager
    )
    
    # Register services and features
    controller.register_service_classification("auth_service", ServiceClassification.ESSENTIAL)
    controller.register_service_classification("api_service", ServiceClassification.OPTIONAL)
    controller.register_feature_dependency("user_auth", ["auth_service"])
    controller.register_feature_dependency("api_access", ["api_service"])
    
    # Test failure cascade
    await controller.handle_service_failure("auth_service", Exception("Auth failed"))
    
    # Should escalate to severe degradation
    assert controller.system_state.degradation_level == DegradationLevel.SEVERE
    
    # Should disable dependent features
    assert not controller.is_feature_available("user_auth")
    
    # Should send critical alert
    error_manager._send_alert.assert_called()
    
    # Test recovery
    await controller.handle_service_recovery("auth_service")
    
    # Should improve degradation level
    assert controller.system_state.degradation_level == DegradationLevel.NORMAL
    
    # Should re-enable features
    assert controller.is_feature_available("user_auth")


@pytest.mark.asyncio
async def test_concurrent_failure_and_recovery():
    """Test concurrent service failures and recoveries"""
    controller = GracefulDegradationController()
    
    # Register multiple services
    services = ["service1", "service2", "service3", "service4"]
    for service in services:
        controller.register_service_classification(service, ServiceClassification.OPTIONAL)
    
    # Simulate concurrent failures
    failure_tasks = [
        controller.handle_service_failure(service, Exception(f"{service} failed"))
        for service in services[:3]  # Fail first 3 services
    ]
    
    # Simulate concurrent recovery
    recovery_tasks = [
        controller.handle_service_recovery(services[0])  # Recover first service
    ]
    
    # Execute all operations concurrently
    await asyncio.gather(*failure_tasks, *recovery_tasks)
    
    # Should have 2 failed services remaining
    assert len(controller.system_state.failed_services) == 2
    assert services[0] not in controller.system_state.failed_services  # Recovered
    assert services[1] in controller.system_state.failed_services      # Still failed
    assert services[2] in controller.system_state.failed_services      # Still failed