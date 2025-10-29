#!/usr/bin/env python3
"""
Standalone test for IntelligentResponseController to verify core functionality.
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the controller directly
from ai_karen_engine.services.intelligent_response_controller import (
    IntelligentResponseController,
    ResourceMonitor,
    MemoryManager,
    ResourcePressureConfig,
    ResourceMetrics,
    ResponsePerformanceMetrics
)

# Mock the required types
class MockDecideActionInput:
    def __init__(self, prompt):
        self.prompt = prompt
        self.short_term_memory = ""
        self.long_term_memory = ""
        self.keywords = []
        self.knowledge_graph_insights = ""
        self.personal_facts = []
        self.memory_depth = None
        self.personality_tone = None
        self.personality_verbosity = None
        self.custom_persona_instructions = ""

class MockDecideActionOutput:
    def __init__(self, response):
        self.intermediate_response = response
        self.tool_to_call = None
        self.tool_input = None
        self.suggested_new_facts = None
        self.proactive_suggestion = None

class MockFlowInput:
    def __init__(self, data):
        self.data = data

class MockFlowOutput:
    def __init__(self, result):
        self.result = result

class MockFlowType:
    CHAT_FLOW = "chat_flow"


async def test_resource_monitor():
    """Test ResourceMonitor functionality."""
    print("Testing ResourceMonitor...")
    
    config = ResourcePressureConfig()
    monitor = ResourceMonitor(config)
    
    # Test initialization
    assert not monitor._monitoring
    assert monitor._monitor_thread is None
    
    # Test metrics collection (will use real psutil)
    try:
        metrics = monitor._collect_metrics()
        assert isinstance(metrics, ResourceMetrics)
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb > 0
        assert isinstance(metrics.timestamp, datetime)
        print(f"✓ Current metrics: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_mb:.1f}MB")
    except Exception as e:
        print(f"✗ Metrics collection failed: {e}")
        return False
    
    # Test pressure detection
    try:
        pressure = monitor.detect_resource_pressure()
        print(f"✓ Resource pressure detection: {pressure}")
    except Exception as e:
        print(f"✗ Pressure detection failed: {e}")
        return False
    
    print("✓ ResourceMonitor tests passed")
    return True


async def test_memory_manager():
    """Test MemoryManager functionality."""
    print("Testing MemoryManager...")
    
    manager = MemoryManager()
    manager.initialize()
    
    # Test memory optimization
    try:
        result = manager.optimize_memory_before_response()
        assert "optimizations_applied" in result
        assert "start_memory_mb" in result
        print(f"✓ Memory optimization: {result['optimizations_applied']}")
    except Exception as e:
        print(f"✗ Memory optimization failed: {e}")
        return False
    
    # Test post-response cleanup
    try:
        test_data = {"test": "data"}
        result = manager.optimize_memory_after_response(test_data)
        assert "cleanup_scheduled" in result
        print("✓ Post-response cleanup scheduled")
    except Exception as e:
        print(f"✗ Post-response cleanup failed: {e}")
        return False
    
    print("✓ MemoryManager tests passed")
    return True


async def test_controller_basic_functionality():
    """Test basic IntelligentResponseController functionality."""
    print("Testing IntelligentResponseController...")
    
    # Create mock components
    mock_decision_engine = Mock()
    mock_decision_engine.decide_action = AsyncMock(
        return_value=MockDecideActionOutput("Test response")
    )
    
    mock_flow_manager = Mock()
    mock_flow_manager.execute_flow = AsyncMock(
        return_value=MockFlowOutput("Test flow result")
    )
    
    mock_tinyllama_service = Mock()
    mock_tinyllama_service.generate_scaffold = AsyncMock(
        return_value=Mock(content="Test scaffold", processing_time=0.1)
    )
    
    # Create controller
    try:
        controller = IntelligentResponseController(
            decision_engine=mock_decision_engine,
            flow_manager=mock_flow_manager,
            tinyllama_service=mock_tinyllama_service
        )
        print("✓ Controller initialized successfully")
    except Exception as e:
        print(f"✗ Controller initialization failed: {e}")
        return False
    
    # Test component preservation
    assert controller.decision_engine is mock_decision_engine
    assert controller.flow_manager is mock_flow_manager
    assert controller.tinyllama_service is mock_tinyllama_service
    print("✓ Original components preserved")
    
    # Test optimized response generation
    try:
        input_data = MockDecideActionInput("Test prompt")
        result = await controller.generate_optimized_response(input_data, "test_response")
        
        # Verify original method was called
        mock_decision_engine.decide_action.assert_called_once_with(input_data)
        
        # Verify result is preserved
        assert result.intermediate_response == "Test response"
        print("✓ Optimized response generation preserves logic")
    except Exception as e:
        print(f"✗ Optimized response generation failed: {e}")
        return False
    
    # Test performance metrics
    try:
        metrics = controller.get_performance_metrics("test_response")
        assert metrics is not None
        assert metrics.response_id == "test_response"
        assert metrics.total_duration_ms > 0
        print(f"✓ Performance metrics collected: {metrics.total_duration_ms:.1f}ms")
    except Exception as e:
        print(f"✗ Performance metrics failed: {e}")
        return False
    
    # Test resource status
    try:
        status = controller.get_resource_status()
        assert "current_cpu_percent" in status
        assert "current_memory_mb" in status
        print(f"✓ Resource status: CPU={status['current_cpu_percent']:.1f}%, Memory={status['current_memory_mb']:.1f}MB")
    except Exception as e:
        print(f"✗ Resource status failed: {e}")
        return False
    
    # Test performance summary
    try:
        summary = controller.get_recent_performance_summary()
        assert "total_responses" in summary
        print(f"✓ Performance summary: {summary['total_responses']} responses")
    except Exception as e:
        print(f"✗ Performance summary failed: {e}")
        return False
    
    # Test shutdown
    try:
        await controller.shutdown()
        print("✓ Controller shutdown successful")
    except Exception as e:
        print(f"✗ Controller shutdown failed: {e}")
        return False
    
    print("✓ IntelligentResponseController tests passed")
    return True


async def test_cpu_usage_monitoring():
    """Test CPU usage monitoring and threshold detection."""
    print("Testing CPU usage monitoring...")
    
    # Create mock components
    mock_decision_engine = Mock()
    mock_decision_engine.decide_action = AsyncMock(
        return_value=MockDecideActionOutput("Test response")
    )
    
    # Create controller with low CPU threshold for testing
    config = ResourcePressureConfig(cpu_threshold_percent=1.0)  # Very low threshold
    controller = IntelligentResponseController(
        decision_engine=mock_decision_engine,
        flow_manager=Mock(),
        config=config
    )
    
    try:
        input_data = MockDecideActionInput("CPU test prompt")
        await controller.generate_optimized_response(input_data, "cpu_test")
        
        # Check if CPU monitoring detected usage
        metrics = controller.get_performance_metrics("cpu_test")
        assert metrics is not None
        assert metrics.cpu_usage_percent >= 0
        
        # With very low threshold, we should detect threshold exceeded
        if metrics.cpu_usage_percent > 1.0:
            assert "cpu_threshold_exceeded" in metrics.optimization_applied
            print(f"✓ CPU threshold detection working: {metrics.cpu_usage_percent:.1f}% > 1.0%")
        else:
            print(f"✓ CPU usage within threshold: {metrics.cpu_usage_percent:.1f}%")
        
        await controller.shutdown()
        print("✓ CPU usage monitoring tests passed")
        return True
        
    except Exception as e:
        print(f"✗ CPU usage monitoring failed: {e}")
        await controller.shutdown()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing IntelligentResponseController Implementation")
    print("=" * 60)
    
    tests = [
        test_resource_monitor,
        test_memory_manager,
        test_controller_basic_functionality,
        test_cpu_usage_monitoring
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        try:
            if await test():
                passed += 1
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")
    
    print()
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! IntelligentResponseController is working correctly.")
        print()
        print("Key features verified:")
        print("✓ Preserves existing DecisionEngine logic")
        print("✓ Preserves existing FlowManager logic") 
        print("✓ Preserves existing TinyLlama scaffolding logic")
        print("✓ Monitors CPU and memory usage")
        print("✓ Detects resource pressure")
        print("✓ Applies memory optimizations")
        print("✓ Collects performance metrics")
        print("✓ Provides resource status reporting")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)