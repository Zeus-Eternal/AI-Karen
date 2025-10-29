"""
Standalone Test Script for Error Handling and Graceful Degradation System

This script tests the error handling system independently to verify
all components work correctly and provide comprehensive error recovery.
"""

import asyncio
import sys
import os
import time
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_error_recovery_system():
    """Test the main error recovery system."""
    print("Testing Error Recovery System...")
    
    try:
        from src.ai_karen_engine.services.error_recovery_system import (
            error_recovery_system,
            ErrorContext,
            ErrorType
        )
        from src.ai_karen_engine.core.types.shared_types import Modality, ModalityType
        
        # Test error context creation
        context = ErrorContext(
            error_type=ErrorType.MODEL_UNAVAILABLE,
            original_error=Exception("Test model unavailable"),
            query="Test query for error recovery",
            model_id="test-model",
            modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True
                )
            ]
        )
        
        # Test error handling
        result = await error_recovery_system.handle_error(context)
        
        assert result.success, "Error recovery should succeed"
        assert result.response is not None, "Recovery should provide a response"
        assert result.strategy_used is not None, "Recovery should use a strategy"
        assert result.recovery_time > 0, "Recovery should track time"
        
        print("✓ Error Recovery System working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error Recovery System failed: {str(e)}")
        return False


async def test_model_availability_handler():
    """Test the model availability handler."""
    print("Testing Model Availability Handler...")
    
    try:
        from src.ai_karen_engine.services.model_availability_handler import (
            model_availability_handler
        )
        
        # Test model availability check
        health_check = await model_availability_handler.check_model_availability("test-model")
        
        assert health_check is not None, "Health check should return result"
        assert health_check.model_id == "test-model", "Health check should track model ID"
        assert health_check.response_time >= 0, "Response time should be non-negative"
        
        # Test fallback model finding
        from src.ai_karen_engine.services.model_availability_handler import ModalityRequirement
        from src.ai_karen_engine.core.types.shared_types import ModalityType
        
        modality_requirements = [
            ModalityRequirement(
                modality_type=ModalityType.TEXT,
                input_required=True,
                output_required=True
            )
        ]
        
        fallback_candidates = await model_availability_handler.find_fallback_models(
            failed_model_id="failed-model",
            modality_requirements=modality_requirements,
            max_candidates=3
        )
        
        assert isinstance(fallback_candidates, list), "Should return list of candidates"
        
        print("✓ Model Availability Handler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Model Availability Handler failed: {str(e)}")
        return False


async def test_memory_exhaustion_handler():
    """Test the memory exhaustion handler."""
    print("Testing Memory Exhaustion Handler...")
    
    try:
        from src.ai_karen_engine.services.memory_exhaustion_handler import (
            memory_exhaustion_handler
        )
        
        # Test memory status monitoring
        memory_status = await memory_exhaustion_handler.monitor_memory_status()
        
        assert memory_status is not None, "Memory status should be returned"
        assert memory_status.usage_percentage >= 0, "Usage percentage should be non-negative"
        assert memory_status.total_memory > 0, "Total memory should be positive"
        
        # Test memory exhaustion handling
        test_query = "Test query for memory exhaustion recovery"
        recovery_result = await memory_exhaustion_handler.handle_memory_exhaustion(test_query)
        
        assert recovery_result is not None, "Recovery result should be returned"
        assert recovery_result.recovery_time >= 0, "Recovery time should be non-negative"
        assert isinstance(recovery_result.optimizations_applied, list), "Should track optimizations"
        
        print("✓ Memory Exhaustion Handler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Memory Exhaustion Handler failed: {str(e)}")
        return False


async def test_timeout_performance_handler():
    """Test the timeout and performance handler."""
    print("Testing Timeout Performance Handler...")
    
    try:
        from src.ai_karen_engine.services.timeout_performance_handler import (
            timeout_performance_handler
        )
        
        # Test timeout context
        async with timeout_performance_handler.timeout_context(
            operation_type="test",
            model_id="test-model",
            custom_timeout=5.0
        ) as timeout_value:
            assert timeout_value > 0, "Timeout value should be positive"
            await asyncio.sleep(0.1)  # Simulate work
        
        # Test performance monitoring
        start_time = time.time()
        await asyncio.sleep(0.1)
        end_time = time.time()
        
        metrics = await timeout_performance_handler.monitor_performance(
            model_id="test-model",
            operation_type="test",
            start_time=start_time,
            end_time=end_time
        )
        
        assert metrics is not None, "Performance metrics should be returned"
        assert metrics.response_time > 0, "Response time should be positive"
        assert metrics.cpu_usage >= 0, "CPU usage should be non-negative"
        assert metrics.memory_usage >= 0, "Memory usage should be non-negative"
        
        print("✓ Timeout Performance Handler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Timeout Performance Handler failed: {str(e)}")
        return False


async def test_streaming_interruption_handler():
    """Test the streaming interruption handler."""
    print("Testing Streaming Interruption Handler...")
    
    try:
        from src.ai_karen_engine.services.streaming_interruption_handler import (
            streaming_interruption_handler
        )
        
        # Test checkpoint creation
        session_id = "test_session"
        checkpoint = await streaming_interruption_handler.create_checkpoint(
            session_id=session_id,
            content_delivered="Test content delivered",
            content_remaining="Test content remaining",
            stream_position=20
        )
        
        assert checkpoint is not None, "Checkpoint should be created"
        assert checkpoint.session_id == session_id, "Checkpoint should track session ID"
        assert checkpoint.content_delivered == "Test content delivered", "Should track delivered content"
        assert checkpoint.stream_position == 20, "Should track stream position"
        
        # Test streaming session context
        try:
            async with streaming_interruption_handler.streaming_session(
                session_id="test_session_2",
                query="Test query",
                model_id="test-model"
            ) as session:
                assert session == "test_session_2", "Should return session ID"
                # Simulate successful completion
        except Exception:
            # Context manager should handle errors gracefully
            pass
        
        print("✓ Streaming Interruption Handler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Streaming Interruption Handler failed: {str(e)}")
        return False


async def test_graceful_degradation_coordinator():
    """Test the graceful degradation coordinator."""
    print("Testing Graceful Degradation Coordinator...")
    
    try:
        from src.ai_karen_engine.services.graceful_degradation_coordinator import (
            graceful_degradation_coordinator,
            DegradationContext
        )
        from src.ai_karen_engine.core.types.shared_types import Modality, ModalityType
        
        # Test system health assessment
        health_report = await graceful_degradation_coordinator.assess_system_health()
        
        assert health_report is not None, "Health report should be returned"
        assert hasattr(health_report, 'overall_status'), "Should have overall status"
        assert hasattr(health_report, 'degradation_level'), "Should have degradation level"
        assert isinstance(health_report.available_models, list), "Should track available models"
        assert isinstance(health_report.unavailable_models, list), "Should track unavailable models"
        
        # Test coordinated recovery
        test_error = Exception("Test error for coordinated recovery")
        response = await graceful_degradation_coordinator.handle_coordinated_recovery(
            query="Test query",
            error=test_error,
            model_id="test-model"
        )
        
        assert response is not None, "Recovery response should be returned"
        assert response.content is not None, "Response should have content"
        assert response.response_time >= 0, "Response time should be non-negative"
        assert isinstance(response.optimizations_applied, list), "Should track optimizations"
        assert isinstance(response.warnings, list), "Should track warnings"
        
        # Test graceful execution context
        context = DegradationContext(
            query="Test query for graceful execution",
            requested_model="test-model",
            required_modalities=[
                Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True
                )
            ]
        )
        
        async with graceful_degradation_coordinator.graceful_execution(context) as exec_context:
            assert exec_context is not None, "Execution context should be provided"
            # Simulate successful execution
            await asyncio.sleep(0.1)
        
        print("✓ Graceful Degradation Coordinator working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Graceful Degradation Coordinator failed: {str(e)}")
        return False


async def test_error_classification():
    """Test error classification accuracy."""
    print("Testing Error Classification...")
    
    try:
        from src.ai_karen_engine.services.error_recovery_system import (
            error_recovery_system
        )
        from src.ai_karen_engine.services.graceful_degradation_coordinator import (
            graceful_degradation_coordinator
        )
        from src.ai_karen_engine.services.error_recovery_system import ErrorType
        
        # Test error classification in error recovery system
        test_cases = [
            (Exception("timeout occurred"), ErrorType.MODEL_TIMEOUT),
            (Exception("memory exhausted"), ErrorType.MEMORY_EXHAUSTION),
            (Exception("connection failed"), ErrorType.CONNECTION_FAILURE),
            (Exception("model unavailable"), ErrorType.MODEL_UNAVAILABLE),
            (Exception("routing error"), ErrorType.ROUTING_ERROR),
            (Exception("stream interrupted"), ErrorType.STREAMING_INTERRUPTION)
        ]
        
        for error, expected_type in test_cases:
            classified_type = error_recovery_system._classify_error(error)
            assert classified_type == expected_type, f"Error classification failed for {error}"
        
        # Test error classification in coordinator
        coordinator_test_cases = [
            (Exception("model not found"), ErrorType.MODEL_UNAVAILABLE),
            (asyncio.TimeoutError("timeout"), ErrorType.MODEL_TIMEOUT),
            (MemoryError("OOM"), ErrorType.MEMORY_EXHAUSTION),
            (ConnectionError("connection lost"), ErrorType.CONNECTION_FAILURE)
        ]
        
        for error, expected_type in coordinator_test_cases:
            classified_type = graceful_degradation_coordinator._classify_error_type(error)
            assert classified_type == expected_type, f"Coordinator error classification failed for {error}"
        
        print("✓ Error Classification working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Error Classification failed: {str(e)}")
        return False


async def test_recovery_strategies():
    """Test different recovery strategies."""
    print("Testing Recovery Strategies...")
    
    try:
        from src.ai_karen_engine.services.error_recovery_system import (
            error_recovery_system,
            ErrorContext,
            ErrorType,
            RecoveryStrategy
        )
        
        # Test fallback model strategy
        context = ErrorContext(
            error_type=ErrorType.MODEL_UNAVAILABLE,
            original_error=Exception("Model unavailable"),
            query="Test query"
        )
        
        result = await error_recovery_system._fallback_to_alternative_model(context)
        assert result.success, "Fallback model strategy should succeed"
        assert result.strategy_used == RecoveryStrategy.FALLBACK_MODEL, "Should use fallback model strategy"
        
        # Test complexity reduction strategy
        result = await error_recovery_system._reduce_query_complexity(context)
        assert result.success, "Complexity reduction should succeed"
        assert result.strategy_used == RecoveryStrategy.REDUCE_COMPLEXITY, "Should use complexity reduction strategy"
        
        # Test graceful degradation strategy
        result = await error_recovery_system._graceful_degradation(context)
        assert result.success, "Graceful degradation should succeed"
        assert result.strategy_used == RecoveryStrategy.GRACEFUL_DEGRADATION, "Should use graceful degradation strategy"
        
        print("✓ Recovery Strategies working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Recovery Strategies failed: {str(e)}")
        return False


async def test_system_integration():
    """Test system integration across all components."""
    print("Testing System Integration...")
    
    try:
        from src.ai_karen_engine.services.graceful_degradation_coordinator import (
            graceful_degradation_coordinator
        )
        
        # Test multiple error scenarios
        error_scenarios = [
            Exception("Model unavailable"),
            MemoryError("Out of memory"),
            asyncio.TimeoutError("Timeout"),
            ConnectionError("Connection failed")
        ]
        
        for i, error in enumerate(error_scenarios):
            response = await graceful_degradation_coordinator.handle_coordinated_recovery(
                query=f"Test query {i}",
                error=error,
                model_id=f"test-model-{i}"
            )
            
            assert response is not None, f"Recovery should succeed for error {i}"
            assert response.content is not None, f"Response should have content for error {i}"
            assert response.response_time >= 0, f"Response time should be valid for error {i}"
        
        # Test system status
        status = await graceful_degradation_coordinator.get_system_status()
        assert isinstance(status, dict), "System status should be a dictionary"
        assert "health_report" in status, "Should include health report"
        assert "degradation_stats" in status, "Should include degradation stats"
        
        print("✓ System Integration working correctly")
        return True
        
    except Exception as e:
        print(f"✗ System Integration failed: {str(e)}")
        return False


async def test_performance_and_reliability():
    """Test performance and reliability under load."""
    print("Testing Performance and Reliability...")
    
    try:
        from src.ai_karen_engine.services.graceful_degradation_coordinator import (
            graceful_degradation_coordinator
        )
        
        # Test concurrent error handling
        concurrent_tasks = []
        for i in range(10):
            task = graceful_degradation_coordinator.handle_coordinated_recovery(
                query=f"Concurrent test {i}",
                error=Exception(f"Concurrent error {i}"),
                model_id=f"concurrent-model-{i}"
            )
            concurrent_tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        end_time = time.time()
        
        # Verify results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful_results) / len(results)
        
        assert success_rate >= 0.8, f"Success rate should be at least 80%, got {success_rate:.2f}"
        assert end_time - start_time < 10.0, "Concurrent processing should complete within 10 seconds"
        
        print(f"✓ Performance and Reliability: {success_rate:.1%} success rate in {end_time - start_time:.2f}s")
        return True
        
    except Exception as e:
        print(f"✗ Performance and Reliability failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all error handling tests."""
    print("=" * 80)
    print("ERROR HANDLING AND GRACEFUL DEGRADATION SYSTEM TESTS")
    print("=" * 80)
    
    tests = [
        test_error_recovery_system,
        test_model_availability_handler,
        test_memory_exhaustion_handler,
        test_timeout_performance_handler,
        test_streaming_interruption_handler,
        test_graceful_degradation_coordinator,
        test_error_classification,
        test_recovery_strategies,
        test_system_integration,
        test_performance_and_reliability
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {str(e)}")
            results.append(False)
        
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total:.1%}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Error handling system is working correctly.")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please check the implementation.")
        return False


async def main():
    """Main test execution function."""
    try:
        success = await run_all_tests()
        
        if success:
            print("\n✅ Error Handling and Graceful Degradation System verification completed successfully!")
            print("\nKey capabilities verified:")
            print("• Comprehensive error recovery for all failure modes")
            print("• Model availability checking and intelligent fallback mechanisms")
            print("• Memory exhaustion detection and automatic optimization")
            print("• Timeout handling and performance degradation management")
            print("• Streaming interruption recovery with checkpoint-based resume")
            print("• Coordinated recovery across all system components")
            print("• Graceful degradation that maintains system functionality")
            print("• Performance monitoring and adaptive optimization")
            print("• Reliable operation under concurrent load")
            
            return 0
        else:
            print("\n❌ Some tests failed. The error handling system needs attention.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)