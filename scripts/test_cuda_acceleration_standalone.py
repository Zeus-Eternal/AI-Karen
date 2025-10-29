#!/usr/bin/env python3
"""
Standalone test script for CUDA Acceleration Engine.

This script tests the CUDA acceleration engine implementation without requiring
the full test framework. It can be run directly to verify functionality.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_cuda_detection():
    """Test CUDA device detection."""
    logger.info("Testing CUDA device detection...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        cuda_info = await engine.detect_cuda_availability()
        
        logger.info(f"CUDA Available: {cuda_info.available}")
        logger.info(f"Device Count: {cuda_info.device_count}")
        
        if cuda_info.available:
            logger.info(f"CUDA Version: {cuda_info.cuda_version}")
            logger.info(f"Total Memory: {cuda_info.total_memory / (1024**3):.1f} GB")
            
            for device in cuda_info.devices:
                logger.info(f"Device {device.id}: {device.name}")
                logger.info(f"  Compute: {device.compute_capability}")
                logger.info(f"  Memory: {device.memory_total / (1024**3):.1f} GB")
        
        await engine.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"CUDA detection test failed: {e}")
        return False


async def test_cuda_initialization():
    """Test CUDA context initialization."""
    logger.info("Testing CUDA context initialization...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Detect CUDA first
        cuda_info = await engine.detect_cuda_availability()
        
        if not cuda_info.available:
            logger.info("CUDA not available - skipping initialization test")
            await engine.shutdown()
            return True
        
        # Initialize context
        context = await engine.initialize_cuda_context()
        
        if context:
            logger.info(f"CUDA context initialized successfully")
            logger.info(f"Status: {context['status']}")
            logger.info(f"Devices: {context['devices']}")
            logger.info(f"Engine initialized: {engine.initialized}")
        else:
            logger.warning("CUDA context initialization returned None")
        
        await engine.shutdown()
        return context is not None
        
    except Exception as e:
        logger.error(f"CUDA initialization test failed: {e}")
        return False


async def test_gpu_inference():
    """Test GPU model inference offloading."""
    logger.info("Testing GPU model inference...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Test model info
        model_info = {
            'id': 'test_model',
            'name': 'Test Model',
            'size': 1000000,
            'weights': {'layer1': 'mock_weights'}
        }
        
        input_data = "Test input for GPU inference"
        
        # Perform inference
        start_time = time.time()
        result = await engine.offload_model_inference_to_gpu(model_info, input_data)
        inference_time = time.time() - start_time
        
        logger.info(f"Inference result: {result}")
        logger.info(f"Inference time: {inference_time:.3f}s")
        
        # Test multiple inferences
        logger.info("Testing multiple inferences...")
        results = []
        start_time = time.time()
        
        for i in range(3):
            result = await engine.offload_model_inference_to_gpu(
                model_info, 
                f"Test input {i}"
            )
            results.append(result)
        
        total_time = time.time() - start_time
        logger.info(f"Completed {len(results)} inferences in {total_time:.3f}s")
        
        await engine.shutdown()
        return len(results) == 3
        
    except Exception as e:
        logger.error(f"GPU inference test failed: {e}")
        return False


async def test_memory_management():
    """Test GPU memory management."""
    logger.info("Testing GPU memory management...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import (
            CUDAAccelerationEngine, ModelComponent
        )
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        if not engine.initialized:
            logger.info("GPU not initialized - skipping memory test")
            await engine.shutdown()
            return True
        
        # Test memory allocation
        logger.info("Testing memory allocation...")
        memory_size = 1024 * 1024  # 1MB
        
        handle = await engine.manage_gpu_memory_allocation(memory_size)
        
        if handle:
            logger.info(f"Allocated {memory_size} bytes on device {handle.device_id}")
            logger.info(f"Handle size: {handle.size}")
        else:
            logger.warning("Memory allocation returned None")
        
        # Test model component caching
        logger.info("Testing model component caching...")
        
        components = [
            ModelComponent(
                id="test_weights",
                name="Test Weights",
                data="mock_tensor_data",
                size=512 * 1024  # 512KB
            ),
            ModelComponent(
                id="test_bias",
                name="Test Bias",
                data="mock_bias_data",
                size=256 * 1024  # 256KB
            )
        ]
        
        await engine.cache_model_components_on_gpu(components)
        
        logger.info(f"Cached {len(engine.model_cache)} components")
        for comp_id, comp in engine.model_cache.items():
            logger.info(f"  {comp_id}: {comp.size} bytes on device {comp.device_id}")
        
        await engine.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Memory management test failed: {e}")
        return False


async def test_batch_processing():
    """Test GPU batch processing optimization."""
    logger.info("Testing GPU batch processing...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine(max_batch_size=4, batch_timeout=0.1)
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Create batch requests
        batch_requests = []
        for i in range(5):
            request = {
                'id': f'batch_req_{i}',
                'input_data': f'Batch input {i}',
                'model_info': {'id': 'batch_model'},
                'priority': i % 2  # Alternating priorities
            }
            batch_requests.append(request)
        
        logger.info(f"Processing batch of {len(batch_requests)} requests...")
        
        # Process batch
        start_time = time.time()
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        batch_time = time.time() - start_time
        
        logger.info(f"Batch completed in {batch_time:.3f}s")
        logger.info(f"Responses: {len(responses)}")
        
        successful = sum(1 for r in responses if r['success'])
        logger.info(f"Successful responses: {successful}/{len(responses)}")
        
        # Show sample responses
        for i, response in enumerate(responses[:2]):
            logger.info(f"Response {i+1}: {response['request_id']}, "
                       f"Success: {response['success']}, "
                       f"Time: {response['processing_time']:.3f}s")
        
        await engine.shutdown()
        return len(responses) == len(batch_requests)
        
    except Exception as e:
        logger.error(f"Batch processing test failed: {e}")
        return False


async def test_performance_monitoring():
    """Test GPU performance monitoring."""
    logger.info("Testing GPU performance monitoring...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Generate some activity for metrics
        model_info = {'id': 'perf_model'}
        for i in range(3):
            await engine.offload_model_inference_to_gpu(model_info, f"Perf test {i}")
        
        # Monitor utilization
        logger.info("Monitoring GPU utilization...")
        metrics = await engine.monitor_gpu_utilization()
        
        logger.info(f"GPU Utilization: {metrics.utilization_percentage:.1f}%")
        logger.info(f"Memory Usage: {metrics.memory_usage_percentage:.1f}%")
        logger.info(f"Temperature: {metrics.temperature:.1f}°C")
        logger.info(f"Power Usage: {metrics.power_usage:.1f}W")
        logger.info(f"Inference Throughput: {metrics.inference_throughput:.1f} inf/s")
        logger.info(f"Batch Efficiency: {metrics.batch_processing_efficiency:.1f}%")
        
        # Get performance summary
        logger.info("Getting performance summary...")
        summary = await engine.get_performance_summary()
        
        logger.info(f"CUDA Available: {summary['cuda_available']}")
        logger.info(f"Initialized: {summary['initialized']}")
        logger.info(f"Device Count: {summary['device_count']}")
        logger.info(f"Cached Models: {summary['cached_models']}")
        
        await engine.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"Performance monitoring test failed: {e}")
        return False


async def test_cpu_fallback():
    """Test CPU fallback mechanisms."""
    logger.info("Testing CPU fallback mechanisms...")
    
    try:
        from ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
        
        engine = CUDAAccelerationEngine()
        
        # Force CUDA unavailable for testing
        engine.cuda_info = None
        engine.initialized = False
        
        model_info = {'id': 'fallback_model'}
        input_data = "Fallback test input"
        
        # Test inference fallback
        logger.info("Testing inference fallback...")
        result = await engine.offload_model_inference_to_gpu(model_info, input_data)
        logger.info(f"Fallback result: {result}")
        
        # Test batch fallback
        logger.info("Testing batch fallback...")
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
            }
        ]
        
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        logger.info(f"Fallback batch responses: {len(responses)}")
        
        # Verify all responses use CPU
        cpu_responses = [r for r in responses if not r.get('gpu_accelerated', True)]
        logger.info(f"CPU responses: {len(cpu_responses)}/{len(responses)}")
        
        await engine.shutdown()
        return len(cpu_responses) == len(responses)
        
    except Exception as e:
        logger.error(f"CPU fallback test failed: {e}")
        return False


async def run_all_tests():
    """Run all CUDA acceleration engine tests."""
    logger.info("Running CUDA Acceleration Engine Tests")
    logger.info("=" * 50)
    
    tests = [
        ("CUDA Detection", test_cuda_detection),
        ("CUDA Initialization", test_cuda_initialization),
        ("GPU Inference", test_gpu_inference),
        ("Memory Management", test_memory_management),
        ("Batch Processing", test_batch_processing),
        ("Performance Monitoring", test_performance_monitoring),
        ("CPU Fallback", test_cpu_fallback)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results[test_name] = result
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name} Test: {status}")
        except Exception as e:
            logger.error(f"{test_name} Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Test Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! ✅")
        return True
    else:
        logger.warning(f"{total - passed} tests failed! ❌")
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()