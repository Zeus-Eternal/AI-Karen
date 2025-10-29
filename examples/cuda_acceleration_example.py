"""
Example usage of CUDA Acceleration Engine for GPU-accelerated model inference.

This example demonstrates:
- CUDA device detection and initialization
- GPU model inference offloading
- Memory management and caching
- Batch processing optimization
- Performance monitoring
- CPU fallback mechanisms
"""

import asyncio
import logging
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from src.ai_karen_engine.services.cuda_acceleration_engine import (
        CUDAAccelerationEngine,
        ModelComponent,
        BatchRequest
    )
except ImportError as e:
    logger.error(f"Failed to import CUDA acceleration engine: {e}")
    logger.info("Make sure PyTorch with CUDA support is installed")
    exit(1)


async def demonstrate_cuda_detection():
    """Demonstrate CUDA device detection and initialization."""
    logger.info("=== CUDA Device Detection Demo ===")
    
    engine = CUDAAccelerationEngine()
    
    try:
        # Detect CUDA availability
        cuda_info = await engine.detect_cuda_availability()
        
        logger.info(f"CUDA Available: {cuda_info.available}")
        logger.info(f"Device Count: {cuda_info.device_count}")
        logger.info(f"CUDA Version: {cuda_info.cuda_version}")
        logger.info(f"Total GPU Memory: {cuda_info.total_memory / (1024**3):.1f} GB")
        
        # Display device information
        for device in cuda_info.devices:
            logger.info(f"Device {device.id}: {device.name}")
            logger.info(f"  Compute Capability: {device.compute_capability}")
            logger.info(f"  Memory: {device.memory_total / (1024**3):.1f} GB total, "
                       f"{device.memory_free / (1024**3):.1f} GB free")
            logger.info(f"  Utilization: {device.utilization:.1f}%")
            if device.temperature:
                logger.info(f"  Temperature: {device.temperature:.1f}°C")
            if device.power_usage:
                logger.info(f"  Power Usage: {device.power_usage:.1f}W")
        
        # Initialize CUDA context
        if cuda_info.available:
            logger.info("\nInitializing CUDA context...")
            context = await engine.initialize_cuda_context()
            
            if context:
                logger.info(f"CUDA context initialized successfully")
                logger.info(f"Initialized devices: {context['devices']}")
                logger.info(f"Total memory: {context['total_memory'] / (1024**3):.1f} GB")
            else:
                logger.warning("Failed to initialize CUDA context")
        
    except Exception as e:
        logger.error(f"CUDA detection failed: {e}")
    
    finally:
        await engine.shutdown()


async def demonstrate_gpu_inference():
    """Demonstrate GPU model inference offloading."""
    logger.info("\n=== GPU Model Inference Demo ===")
    
    engine = CUDAAccelerationEngine()
    
    try:
        # Initialize engine
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        if not engine.initialized:
            logger.warning("GPU not available, skipping inference demo")
            return
        
        # Simulate model information
        model_info = {
            'id': 'demo_model',
            'name': 'Demo Language Model',
            'type': 'transformer',
            'size': 1000000,  # 1MB
            'weights': {'layer1': 'mock_weights', 'layer2': 'mock_weights'}
        }
        
        # Test single inference
        logger.info("Testing single GPU inference...")
        start_time = time.time()
        
        result = await engine.offload_model_inference_to_gpu(
            model_info, 
            "What is the capital of France?"
        )
        
        inference_time = time.time() - start_time
        logger.info(f"GPU inference result: {result}")
        logger.info(f"Inference time: {inference_time:.3f}s")
        
        # Test multiple inferences
        logger.info("\nTesting multiple GPU inferences...")
        queries = [
            "Explain quantum computing",
            "Write a Python function",
            "What is machine learning?",
            "Describe neural networks",
            "How does CUDA work?"
        ]
        
        start_time = time.time()
        results = []
        
        for i, query in enumerate(queries):
            result = await engine.offload_model_inference_to_gpu(model_info, query)
            results.append(result)
            logger.info(f"Query {i+1} completed: {result}")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(queries)
        
        logger.info(f"Completed {len(queries)} inferences in {total_time:.3f}s")
        logger.info(f"Average time per inference: {avg_time:.3f}s")
        
    except Exception as e:
        logger.error(f"GPU inference demo failed: {e}")
    
    finally:
        await engine.shutdown()


async def demonstrate_memory_management():
    """Demonstrate GPU memory management."""
    logger.info("\n=== GPU Memory Management Demo ===")
    
    engine = CUDAAccelerationEngine()
    
    try:
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        if not engine.initialized:
            logger.warning("GPU not available, skipping memory demo")
            return
        
        # Test memory allocation
        logger.info("Testing GPU memory allocation...")
        
        memory_sizes = [1024*1024, 2*1024*1024, 5*1024*1024]  # 1MB, 2MB, 5MB
        handles = []
        
        for size in memory_sizes:
            logger.info(f"Allocating {size / (1024*1024):.1f} MB...")
            handle = await engine.manage_gpu_memory_allocation(size)
            
            if handle:
                handles.append(handle)
                logger.info(f"Allocated on device {handle.device_id}")
            else:
                logger.warning(f"Failed to allocate {size / (1024*1024):.1f} MB")
        
        logger.info(f"Successfully allocated {len(handles)} memory blocks")
        
        # Test model component caching
        logger.info("\nTesting model component caching...")
        
        # Create mock model components
        components = []
        for i in range(3):
            component = ModelComponent(
                id=f"model_{i}_weights",
                name=f"Model {i} Weights",
                data=f"mock_tensor_data_{i}",  # In real usage, this would be a tensor
                size=1024*1024  # 1MB
            )
            components.append(component)
        
        # Cache components on GPU
        await engine.cache_model_components_on_gpu(components)
        
        logger.info(f"Cached {len(engine.model_cache)} model components")
        for comp_id, comp in engine.model_cache.items():
            logger.info(f"  {comp_id}: {comp.size / (1024*1024):.1f} MB on device {comp.device_id}")
        
    except Exception as e:
        logger.error(f"Memory management demo failed: {e}")
    
    finally:
        await engine.shutdown()


async def demonstrate_batch_processing():
    """Demonstrate GPU batch processing optimization."""
    logger.info("\n=== GPU Batch Processing Demo ===")
    
    engine = CUDAAccelerationEngine(
        max_batch_size=8,
        batch_timeout=0.2
    )
    
    try:
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        # Create batch requests
        batch_requests = []
        for i in range(10):
            request = {
                'id': f'batch_req_{i}',
                'input_data': f'Query {i}: What is AI?',
                'model_info': {'id': 'batch_model', 'type': 'transformer'},
                'priority': i % 3  # Varying priorities
            }
            batch_requests.append(request)
        
        logger.info(f"Processing batch of {len(batch_requests)} requests...")
        
        # Process batch
        start_time = time.time()
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        batch_time = time.time() - start_time
        
        # Display results
        logger.info(f"Batch processing completed in {batch_time:.3f}s")
        logger.info(f"Average time per request: {batch_time / len(responses):.3f}s")
        
        successful_responses = [r for r in responses if r['success']]
        gpu_accelerated = [r for r in responses if r.get('gpu_accelerated', False)]
        
        logger.info(f"Successful responses: {len(successful_responses)}/{len(responses)}")
        logger.info(f"GPU accelerated: {len(gpu_accelerated)}/{len(responses)}")
        
        # Show sample responses
        for i, response in enumerate(responses[:3]):
            logger.info(f"Response {i+1}:")
            logger.info(f"  Request ID: {response['request_id']}")
            logger.info(f"  Success: {response['success']}")
            logger.info(f"  GPU Accelerated: {response.get('gpu_accelerated', False)}")
            logger.info(f"  Processing Time: {response['processing_time']:.3f}s")
            if response.get('gpu_time'):
                logger.info(f"  GPU Time: {response['gpu_time']:.3f}s")
        
    except Exception as e:
        logger.error(f"Batch processing demo failed: {e}")
    
    finally:
        await engine.shutdown()


async def demonstrate_performance_monitoring():
    """Demonstrate GPU performance monitoring."""
    logger.info("\n=== GPU Performance Monitoring Demo ===")
    
    engine = CUDAAccelerationEngine()
    
    try:
        await engine.detect_cuda_availability()
        await engine.initialize_cuda_context()
        
        if not engine.initialized:
            logger.warning("GPU not available, skipping monitoring demo")
            return
        
        # Simulate some workload to generate metrics
        model_info = {'id': 'perf_model', 'size': 500000}
        
        logger.info("Running workload to generate performance metrics...")
        for i in range(5):
            await engine.offload_model_inference_to_gpu(
                model_info, 
                f"Performance test query {i}"
            )
            await asyncio.sleep(0.1)  # Small delay between inferences
        
        # Monitor GPU utilization
        logger.info("\nMonitoring GPU utilization...")
        for i in range(3):
            metrics = await engine.monitor_gpu_utilization()
            
            logger.info(f"Measurement {i+1}:")
            logger.info(f"  GPU Utilization: {metrics.utilization_percentage:.1f}%")
            logger.info(f"  Memory Usage: {metrics.memory_usage_percentage:.1f}%")
            logger.info(f"  Temperature: {metrics.temperature:.1f}°C")
            logger.info(f"  Power Usage: {metrics.power_usage:.1f}W")
            logger.info(f"  Inference Throughput: {metrics.inference_throughput:.1f} inf/s")
            logger.info(f"  Batch Efficiency: {metrics.batch_processing_efficiency:.1f}%")
            
            await asyncio.sleep(1)  # Wait between measurements
        
        # Get comprehensive performance summary
        logger.info("\nGetting performance summary...")
        summary = await engine.get_performance_summary()
        
        logger.info("Performance Summary:")
        logger.info(f"  CUDA Available: {summary['cuda_available']}")
        logger.info(f"  Initialized: {summary['initialized']}")
        logger.info(f"  Device Count: {summary['device_count']}")
        logger.info(f"  Cached Models: {summary['cached_models']}")
        logger.info(f"  Memory Handles: {summary['memory_handles']}")
        
        if 'inference_stats' in summary and summary['inference_stats']:
            stats = summary['inference_stats']
            logger.info(f"  Inference Count: {stats['count']}")
            logger.info(f"  Average Time: {stats['avg_time']:.3f}s")
            logger.info(f"  Min Time: {stats['min_time']:.3f}s")
            logger.info(f"  Max Time: {stats['max_time']:.3f}s")
            logger.info(f"  Throughput: {stats['throughput']:.1f} inf/s")
        
    except Exception as e:
        logger.error(f"Performance monitoring demo failed: {e}")
    
    finally:
        await engine.shutdown()


async def demonstrate_cpu_fallback():
    """Demonstrate CPU fallback mechanisms."""
    logger.info("\n=== CPU Fallback Demo ===")
    
    # Create engine with CUDA disabled to test fallback
    engine = CUDAAccelerationEngine()
    
    try:
        # Force CUDA unavailable for testing
        engine.cuda_info = None
        engine.initialized = False
        
        logger.info("Testing CPU fallback for model inference...")
        
        model_info = {
            'id': 'fallback_model',
            'name': 'Fallback Test Model'
        }
        
        # Test inference fallback
        start_time = time.time()
        result = await engine.offload_model_inference_to_gpu(
            model_info, 
            "This should fallback to CPU"
        )
        fallback_time = time.time() - start_time
        
        logger.info(f"CPU fallback result: {result}")
        logger.info(f"Fallback processing time: {fallback_time:.3f}s")
        
        # Test batch processing fallback
        logger.info("\nTesting CPU fallback for batch processing...")
        
        batch_requests = [
            {
                'id': 'fallback_req_1',
                'input_data': 'Fallback query 1',
                'model_info': model_info
            },
            {
                'id': 'fallback_req_2',
                'input_data': 'Fallback query 2',
                'model_info': model_info
            }
        ]
        
        start_time = time.time()
        responses = await engine.optimize_gpu_batch_processing(batch_requests)
        batch_fallback_time = time.time() - start_time
        
        logger.info(f"CPU fallback batch completed in {batch_fallback_time:.3f}s")
        logger.info(f"All responses use CPU: {all(not r.get('gpu_accelerated', True) for r in responses)}")
        
        for response in responses:
            logger.info(f"  {response['request_id']}: {response['success']}, "
                       f"GPU: {response.get('gpu_accelerated', False)}")
        
    except Exception as e:
        logger.error(f"CPU fallback demo failed: {e}")
    
    finally:
        await engine.shutdown()


async def main():
    """Run all CUDA acceleration engine demonstrations."""
    logger.info("CUDA Acceleration Engine Demonstration")
    logger.info("=" * 50)
    
    try:
        # Run all demonstrations
        await demonstrate_cuda_detection()
        await demonstrate_gpu_inference()
        await demonstrate_memory_management()
        await demonstrate_batch_processing()
        await demonstrate_performance_monitoring()
        await demonstrate_cpu_fallback()
        
        logger.info("\n" + "=" * 50)
        logger.info("All demonstrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())