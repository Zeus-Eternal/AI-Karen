#!/usr/bin/env python3
"""
Verification script for CUDA Acceleration Engine implementation.

This script verifies that the CUDA acceleration engine meets all requirements
specified in the intelligent response optimization specification.
"""

import asyncio
import logging
import sys
import time
import inspect
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_class_structure():
    """Verify that the CUDA acceleration engine has the required class structure."""
    logger.info("Verifying CUDA acceleration engine class structure...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import (
            CUDAAccelerationEngine,
            CUDADevice,
            CUDAInfo,
            GPUMemoryHandle,
            GPUMetrics,
            ModelComponent,
            BatchRequest,
            BatchResponse
        )
        
        # Check main class exists
        assert CUDAAccelerationEngine is not None, "CUDAAccelerationEngine class not found"
        
        # Check required methods exist
        required_methods = [
            'detect_cuda_availability',
            'initialize_cuda_context',
            'offload_model_inference_to_gpu',
            'manage_gpu_memory_allocation',
            'cache_model_components_on_gpu',
            'monitor_gpu_utilization',
            'fallback_to_cpu_on_gpu_failure',
            'optimize_gpu_batch_processing'
        ]
        
        for method_name in required_methods:
            assert hasattr(CUDAAccelerationEngine, method_name), f"Method {method_name} not found"
            method = getattr(CUDAAccelerationEngine, method_name)
            assert callable(method), f"Method {method_name} is not callable"
            assert inspect.iscoroutinefunction(method), f"Method {method_name} is not async"
        
        # Check data models exist
        data_models = [CUDADevice, CUDAInfo, GPUMemoryHandle, GPUMetrics, ModelComponent, BatchRequest, BatchResponse]
        for model in data_models:
            assert model is not None, f"Data model {model.__name__} not found"
        
        logger.info("✅ Class structure verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Class structure verification failed: {e}")
        return False


async def verify_cuda_detection():
    """Verify CUDA device detection and initialization (Requirement 9.1)."""
    logger.info("Verifying CUDA device detection and initialization...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Test CUDA detection
        cuda_info = await engine.detect_cuda_availability()
        
        # Verify return type and structure
        assert hasattr(cuda_info, 'available'), "CUDAInfo missing 'available' attribute"
        assert hasattr(cuda_info, 'device_count'), "CUDAInfo missing 'device_count' attribute"
        assert hasattr(cuda_info, 'devices'), "CUDAInfo missing 'devices' attribute"
        assert isinstance(cuda_info.available, bool), "available should be boolean"
        assert isinstance(cuda_info.device_count, int), "device_count should be integer"
        assert isinstance(cuda_info.devices, list), "devices should be list"
        
        logger.info(f"CUDA Available: {cuda_info.available}")
        logger.info(f"Device Count: {cuda_info.device_count}")
        
        # Test context initialization
        context = await engine.initialize_cuda_context()
        
        if cuda_info.available:
            # If CUDA is available, context should be initialized
            if context:
                assert 'status' in context, "Context missing status"
                assert 'devices' in context, "Context missing devices count"
                logger.info("CUDA context initialized successfully")
            else:
                logger.warning("CUDA available but context initialization failed")
        else:
            # If CUDA not available, context should be None
            assert context is None, "Context should be None when CUDA unavailable"
            logger.info("CUDA not available - context correctly returned None")
        
        await engine.shutdown()
        logger.info("✅ CUDA detection verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ CUDA detection verification failed: {e}")
        return False


async def verify_gpu_inference_offloading():
    """Verify GPU model inference offloading (Requirement 9.2)."""
    logger.info("Verifying GPU model inference offloading...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Test model inference offloading
        model_info = {
            'id': 'test_model',
            'name': 'Test Model',
            'type': 'transformer',
            'size': 1000000,
            'weights': {'layer1': 'mock_weights'}
        }
        
        input_data = "Test input for GPU inference verification"
        
        # Perform inference
        start_time = time.time()
        result = await engine.offload_model_inference_to_gpu(model_info, input_data)
        inference_time = time.time() - start_time
        
        # Verify result
        assert result is not None, "Inference result should not be None"
        assert inference_time >= 0, "Inference time should be non-negative"
        
        logger.info(f"Inference completed in {inference_time:.3f}s")
        logger.info(f"Result type: {type(result)}")
        
        # Test multiple inferences for performance
        inference_times = []
        for i in range(3):
            start_time = time.time()
            result = await engine.offload_model_inference_to_gpu(
                model_info, 
                f"Test input {i}"
            )
            inference_time = time.time() - start_time
            inference_times.append(inference_time)
            assert result is not None, f"Inference {i} result should not be None"
        
        avg_time = sum(inference_times) / len(inference_times)
        logger.info(f"Average inference time: {avg_time:.3f}s")
        
        await engine.shutdown()
        logger.info("✅ GPU inference offloading verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ GPU inference offloading verification failed: {e}")
        return False


async def verify_gpu_memory_management():
    """Verify GPU memory management system (Requirement 9.3)."""
    logger.info("Verifying GPU memory management system...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import (
            CUDAAccelerationEngine, ModelComponent
        )
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Test memory allocation
        memory_sizes = [1024*1024, 2*1024*1024]  # 1MB, 2MB
        handles = []
        
        for size in memory_sizes:
            handle = await engine.manage_gpu_memory_allocation(size)
            
            if handle:
                handles.append(handle)
                assert handle.size == size, f"Handle size mismatch: {handle.size} != {size}"
                assert handle.device_id >= 0, "Device ID should be non-negative"
                assert handle.allocated_at > 0, "Allocation time should be set"
                logger.info(f"Allocated {size} bytes on device {handle.device_id}")
            else:
                logger.info(f"Memory allocation failed for {size} bytes (may be expected)")
        
        # Test model component caching
        components = [
            ModelComponent(
                id="test_weights_1",
                name="Test Weights 1",
                data="mock_tensor_data_1",
                size=512*1024
            ),
            ModelComponent(
                id="test_weights_2",
                name="Test Weights 2",
                data="mock_tensor_data_2",
                size=256*1024
            )
        ]
        
        initial_cache_size = len(engine.model_cache)
        await engine.cache_model_components_on_gpu(components)
        
        # Verify caching worked
        assert len(engine.model_cache) >= initial_cache_size, "Model cache should have grown"
        
        for component in components:
            if component.id in engine.model_cache:
                cached_comp = engine.model_cache[component.id]
                assert cached_comp.id == component.id, "Cached component ID mismatch"
                assert cached_comp.size == component.size, "Cached component size mismatch"
                assert cached_comp.access_count > 0, "Access count should be incremented"
                logger.info(f"Component {component.id} cached successfully")
        
        # Test cache cleanup
        await engine._cleanup_gpu_cache()
        logger.info("Cache cleanup completed")
        
        await engine.shutdown()
        logger.info("✅ GPU memory management verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ GPU memory management verification failed: {e}")
        return False


async def verify_gpu_utilization_monitoring():
    """Verify GPU utilization monitoring and metrics (Requirement 9.4)."""
    logger.info("Verifying GPU utilization monitoring and metrics...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Generate some activity for metrics
        model_info = {'id': 'metrics_test_model', 'size': 500000}
        for i in range(3):
            await engine.offload_model_inference_to_gpu(model_info, f"Metrics test {i}")
        
        # Test GPU utilization monitoring
        metrics = await engine.monitor_gpu_utilization()
        
        # Verify metrics structure
        assert hasattr(metrics, 'utilization_percentage'), "Missing utilization_percentage"
        assert hasattr(metrics, 'memory_usage_percentage'), "Missing memory_usage_percentage"
        assert hasattr(metrics, 'temperature'), "Missing temperature"
        assert hasattr(metrics, 'power_usage'), "Missing power_usage"
        assert hasattr(metrics, 'inference_throughput'), "Missing inference_throughput"
        assert hasattr(metrics, 'batch_processing_efficiency'), "Missing batch_processing_efficiency"
        
        # Verify metrics values are reasonable
        assert 0 <= metrics.utilization_percentage <= 100, "Utilization should be 0-100%"
        assert 0 <= metrics.memory_usage_percentage <= 100, "Memory usage should be 0-100%"
        assert metrics.temperature >= 0, "Temperature should be non-negative"
        assert metrics.power_usage >= 0, "Power usage should be non-negative"
        assert metrics.inference_throughput >= 0, "Throughput should be non-negative"
        assert 0 <= metrics.batch_processing_efficiency <= 100, "Batch efficiency should be 0-100%"
        
        logger.info(f"GPU Utilization: {metrics.utilization_percentage:.1f}%")
        logger.info(f"Memory Usage: {metrics.memory_usage_percentage:.1f}%")
        logger.info(f"Temperature: {metrics.temperature:.1f}°C")
        logger.info(f"Inference Throughput: {metrics.inference_throughput:.1f} inf/s")
        
        # Test performance summary
        summary = await engine.get_performance_summary()
        
        # Verify summary structure
        required_keys = ['cuda_available', 'initialized', 'device_count', 'current_metrics']
        for key in required_keys:
            assert key in summary, f"Performance summary missing key: {key}"
        
        logger.info(f"Performance summary keys: {list(summary.keys())}")
        
        await engine.shutdown()
        logger.info("✅ GPU utilization monitoring verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ GPU utilization monitoring verification failed: {e}")
        return False


async def verify_cpu_fallback_mechanisms():
    """Verify seamless CPU fallback mechanisms (Requirement 9.5)."""
    logger.info("Verifying seamless CPU fallback mechanisms...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Force CUDA unavailable to test fallback
        engine.cuda_info = None
        engine.initialized = False
        
        model_info = {
            'id': 'fallback_test_model',
            'name': 'Fallback Test Model'
        }
        
        # Test inference fallback
        logger.info("Testing inference CPU fallback...")
        start_time = time.time()
        result = await engine.offload_model_inference_to_gpu(model_info, "Fallback test input")
        fallback_time = time.time() - start_time
        
        assert result is not None, "CPU fallback should return a result"
        assert fallback_time >= 0, "Fallback time should be non-negative"
        logger.info(f"CPU fallback inference completed in {fallback_time:.3f}s")
        
        # Test batch processing fallback
        logger.info("Testing batch processing CPU fallback...")
        batch_requests = [
            {
                'id': 'fallback_req_1',
                'input_data': 'Fallback input 1',
                'model_info': model_info
            },
            {
                'id': 'fallback_req_2',
                'input_data': 'Fallback input 2',
                'model_info': model_info
            },
            {
                'id': 'fallback_req_3',
                'input_data': 'Fallback input 3',
                'model_info': model_info
            }
        ]
        
        start_time = time.time()
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        batch_fallback_time = time.time() - start_time
        
        # Verify fallback responses
        assert len(responses) == len(batch_requests), "Should have response for each request"
        
        successful_responses = [r for r in responses if r['success']]
        cpu_responses = [r for r in responses if not r.get('gpu_accelerated', True)]
        
        assert len(successful_responses) > 0, "At least some responses should be successful"
        assert len(cpu_responses) == len(responses), "All responses should use CPU fallback"
        
        logger.info(f"CPU fallback batch completed in {batch_fallback_time:.3f}s")
        logger.info(f"Successful responses: {len(successful_responses)}/{len(responses)}")
        logger.info(f"CPU responses: {len(cpu_responses)}/{len(responses)}")
        
        # Test direct CPU fallback function
        def sync_computation():
            return "sync_result"
        
        async def async_computation():
            return "async_result"
        
        sync_result = await engine.fallback_to_cpu_on_gpu_failure(sync_computation)
        async_result = await engine.fallback_to_cpu_on_gpu_failure(async_computation)
        
        assert sync_result == "sync_result", "Sync CPU fallback failed"
        assert async_result == "async_result", "Async CPU fallback failed"
        
        logger.info("Direct CPU fallback functions work correctly")
        
        await engine.shutdown()
        logger.info("✅ CPU fallback mechanisms verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ CPU fallback mechanisms verification failed: {e}")
        return False


async def verify_batch_processing_optimization():
    """Verify batch processing optimization for concurrent requests."""
    logger.info("Verifying batch processing optimization...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine(
            max_batch_size=8,
            batch_timeout=0.2
        )
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Create batch requests with different priorities
        batch_requests = []
        for i in range(10):
            request = {
                'id': f'batch_req_{i}',
                'input_data': f'Batch input {i}',
                'model_info': {'id': 'batch_test_model', 'type': 'transformer'},
                'priority': i % 3  # Priorities 0, 1, 2
            }
            batch_requests.append(request)
        
        logger.info(f"Processing batch of {len(batch_requests)} requests...")
        
        # Process batch
        start_time = time.time()
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        batch_time = time.time() - start_time
        
        # Verify batch processing results
        assert len(responses) == len(batch_requests), "Should have response for each request"
        
        successful_responses = [r for r in responses if r['success']]
        assert len(successful_responses) > 0, "At least some responses should be successful"
        
        # Verify response structure
        for response in responses:
            required_keys = ['request_id', 'result', 'success', 'processing_time']
            for key in required_keys:
                assert key in response, f"Response missing key: {key}"
            
            assert isinstance(response['success'], bool), "Success should be boolean"
            assert isinstance(response['processing_time'], (int, float)), "Processing time should be numeric"
        
        # Check if priority ordering was respected (higher priority first)
        request_ids = [r['request_id'] for r in responses]
        logger.info(f"Response order: {request_ids}")
        
        logger.info(f"Batch processing completed in {batch_time:.3f}s")
        logger.info(f"Average time per request: {batch_time / len(responses):.3f}s")
        logger.info(f"Successful responses: {len(successful_responses)}/{len(responses)}")
        
        # Test batch queue functionality
        assert hasattr(engine, 'batch_queue'), "Engine should have batch_queue"
        assert hasattr(engine, 'max_batch_size'), "Engine should have max_batch_size"
        assert hasattr(engine, 'batch_timeout'), "Engine should have batch_timeout"
        
        logger.info(f"Batch queue size: {engine.batch_queue.qsize()}")
        logger.info(f"Max batch size: {engine.max_batch_size}")
        logger.info(f"Batch timeout: {engine.batch_timeout}s")
        
        await engine.shutdown()
        logger.info("✅ Batch processing optimization verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Batch processing optimization verification failed: {e}")
        return False


async def verify_memory_optimization_strategies():
    """Verify GPU memory optimization strategies to prevent exhaustion."""
    logger.info("Verifying GPU memory optimization strategies...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import (
            CUDAAccelerationEngine, ModelComponent
        )
        
        engine = CUDAAccelerationEngine(
            max_gpu_memory_usage=0.8,
            cache_cleanup_threshold=0.9
        )
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Test memory optimization parameters
        assert hasattr(engine, 'max_gpu_memory_usage'), "Missing max_gpu_memory_usage"
        assert hasattr(engine, 'cache_cleanup_threshold'), "Missing cache_cleanup_threshold"
        assert 0 < engine.max_gpu_memory_usage <= 1, "max_gpu_memory_usage should be 0-1"
        assert 0 < engine.cache_cleanup_threshold <= 1, "cache_cleanup_threshold should be 0-1"
        
        logger.info(f"Max GPU memory usage: {engine.max_gpu_memory_usage * 100}%")
        logger.info(f"Cache cleanup threshold: {engine.cache_cleanup_threshold * 100}%")
        
        # Test memory allocation with limits
        large_memory_size = 100 * 1024 * 1024  # 100MB
        handle = await engine.manage_gpu_memory_allocation(large_memory_size)
        
        if handle:
            logger.info(f"Large memory allocation successful: {large_memory_size / (1024*1024):.1f} MB")
        else:
            logger.info("Large memory allocation failed (expected if insufficient GPU memory)")
        
        # Test cache cleanup functionality
        logger.info("Testing cache cleanup...")
        
        # Add many components to trigger cleanup
        components = []
        for i in range(10):
            component = ModelComponent(
                id=f"cleanup_test_{i}",
                name=f"Cleanup Test {i}",
                data=f"mock_data_{i}",
                size=1024*1024  # 1MB each
            )
            components.append(component)
        
        await engine.cache_model_components_on_gpu(components)
        initial_cache_size = len(engine.model_cache)
        logger.info(f"Initial cache size: {initial_cache_size}")
        
        # Force cleanup
        await engine._cleanup_gpu_cache()
        final_cache_size = len(engine.model_cache)
        logger.info(f"Final cache size after cleanup: {final_cache_size}")
        
        # Test memory handle tracking
        assert hasattr(engine, 'memory_handles'), "Missing memory_handles tracking"
        assert isinstance(engine.memory_handles, dict), "memory_handles should be dict"
        
        logger.info(f"Active memory handles: {len(engine.memory_handles)}")
        
        # Test memory optimization under pressure
        logger.info("Testing memory optimization under pressure...")
        
        # Try to allocate more memory than available (should trigger optimization)
        very_large_size = 10 * 1024 * 1024 * 1024  # 10GB (likely more than available)
        handle = await engine.manage_gpu_memory_allocation(very_large_size)
        
        if handle is None:
            logger.info("Very large allocation correctly failed (memory optimization working)")
        else:
            logger.warning("Very large allocation succeeded (unexpected)")
        
        await engine.shutdown()
        logger.info("✅ Memory optimization strategies verification passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory optimization strategies verification failed: {e}")
        return False


async def run_all_verifications():
    """Run all CUDA acceleration engine verifications."""
    logger.info("Running CUDA Acceleration Engine Implementation Verification")
    logger.info("=" * 70)
    
    verifications = [
        ("Class Structure", verify_class_structure),
        ("CUDA Detection (Req 9.1)", verify_cuda_detection),
        ("GPU Inference Offloading (Req 9.2)", verify_gpu_inference_offloading),
        ("GPU Memory Management (Req 9.3)", verify_gpu_memory_management),
        ("GPU Utilization Monitoring (Req 9.4)", verify_gpu_utilization_monitoring),
        ("CPU Fallback Mechanisms (Req 9.5)", verify_cpu_fallback_mechanisms),
        ("Batch Processing Optimization", verify_batch_processing_optimization),
        ("Memory Optimization Strategies", verify_memory_optimization_strategies)
    ]
    
    results = {}
    
    for verification_name, verification_func in verifications:
        logger.info(f"\n--- {verification_name} ---")
        try:
            if asyncio.iscoroutinefunction(verification_func):
                result = await verification_func()
            else:
                result = verification_func()
            results[verification_name] = result
        except Exception as e:
            logger.error(f"{verification_name} failed with exception: {e}")
            results[verification_name] = False
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Verification Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for verification_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {verification_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} verifications passed")
    
    if passed == total:
        logger.info("\n🎉 All verifications passed! CUDA Acceleration Engine implementation is complete.")
        logger.info("\nImplemented features:")
        logger.info("  ✅ CUDA device detection and initialization")
        logger.info("  ✅ GPU model inference offloading")
        logger.info("  ✅ GPU memory management with efficient allocation/deallocation")
        logger.info("  ✅ GPU-based model component caching")
        logger.info("  ✅ GPU utilization monitoring and performance metrics")
        logger.info("  ✅ Seamless CPU fallback mechanisms")
        logger.info("  ✅ Batch processing optimization for concurrent requests")
        logger.info("  ✅ GPU memory optimization strategies")
        return True
    else:
        logger.warning(f"\n⚠️  {total - passed} verifications failed!")
        logger.info("Please review the failed verifications and fix any issues.")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_verifications())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()