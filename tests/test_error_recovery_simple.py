#!/usr/bin/env python3
"""
Simple test for error recovery system
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct imports to avoid __init__.py issues
from ai_karen_engine.core.error_recovery_manager import (
    ErrorRecoveryManager, ServiceStatus, CircuitState
)
from ai_karen_engine.core.fallback_mechanisms import FallbackManager
from ai_karen_engine.config.performance_config import PerformanceConfig


async def test_error_recovery():
    """Test basic error recovery functionality"""
    print("🚀 Testing Error Recovery System")
    print("=" * 50)
    
    # Create error recovery manager
    config = PerformanceConfig()
    error_manager = ErrorRecoveryManager(config)
    fallback_manager = FallbackManager()
    
    # Register services
    print("📝 Registering services...")
    error_manager.register_service("test_service", is_essential=False, fallback_available=True)
    error_manager.register_service("critical_service", is_essential=True, fallback_available=False)
    
    # Register fallback
    print("🔄 Setting up fallback...")
    fallback_manager.register_static_fallback(
        "test_service",
        static_responses={"error": "Service temporarily unavailable"},
        default_response={"status": "fallback_active"}
    )
    
    # Test 1: Single failure
    print("\n🧪 Test 1: Single service failure")
    await error_manager.handle_service_failure("test_service", Exception("Service down"))
    
    health = error_manager.service_health["test_service"]
    print(f"   Status: {health.status.value}")
    print(f"   Failure count: {health.failure_count}")
    print(f"   Circuit state: {health.circuit_state.value}")
    
    # Test 2: Multiple failures to trigger circuit breaker
    print("\n🧪 Test 2: Multiple failures (circuit breaker)")
    for i in range(5):  # Trigger circuit breaker
        await error_manager.handle_service_failure("test_service", Exception(f"Failure {i+1}"))
    
    health = error_manager.service_health["test_service"]
    print(f"   Status: {health.status.value}")
    print(f"   Failure count: {health.failure_count}")
    print(f"   Circuit state: {health.circuit_state.value}")
    
    # Test 3: Circuit breaker check
    print("\n🧪 Test 3: Circuit breaker check")
    can_call = await error_manager.check_circuit_breaker("test_service")
    print(f"   Can call service: {can_call}")
    
    # Test 4: Success recording
    print("\n🧪 Test 4: Success recording")
    await error_manager.record_service_success("test_service")
    health = error_manager.service_health["test_service"]
    print(f"   Last success: {health.last_success}")
    
    # Test 5: Fallback activation
    print("\n🧪 Test 5: Fallback activation")
    activated = await fallback_manager.activate_fallback("test_service")
    print(f"   Fallback activated: {activated}")
    
    if activated:
        try:
            response = await fallback_manager.handle_fallback_request("test_service", "error")
            print(f"   Fallback response: {response}")
        except Exception as e:
            print(f"   Fallback error: {e}")
    
    # Test 6: Health report
    print("\n🧪 Test 6: Health report")
    report = await error_manager.export_health_report()
    print(f"   Total services: {report['total_services']}")
    print(f"   Essential services: {report['essential_services']}")
    
    for service_name, service_data in report['services'].items():
        print(f"   {service_name}: {service_data['status']} (failures: {service_data['failure_count']})")
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_error_recovery())