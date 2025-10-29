"""
Comprehensive GPU Memory Management Tests
Validates efficient GPU memory allocation, deallocation, and fallback mechanisms.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from src.ai_karen_engine.services.cuda_acceleration_engine import CUDAAccelerationEngine
from src.ai_karen_engine.core.shared_types import (
    CUDAInfo, CUDADevice, GPUMetrics, GPUMemoryHandle, ModelInfo, ModelType
)


class TestGPUMemoryManagementValidation:
    """Test suite for comprehensive GPU memory management validation."""
    
    @pytest.fixture
    async def cuda_engine(self):
        """Create a CUDA acceleration engine for testing."""
        engine = CUDAAccelerationEngine()
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def mock_cuda_devices(self):
        """Create mock CUDA devices with different memory configurations."""
        return [
            CUDADevice(
                id=0,
                name="NVIDIA GeForce RTX 4090",
                compute_capability="8.9",
                memory_total=24576,  # 24GB
                memory_free=20480,   # 20GB free
                memory_used=4096,    # 4GB used
                utilization=30.0
            ),
            CUDADevice(
                id=1,
                name="NVIDIA GeForce RTX 3080",
                compute_capability="8.6",
                memory_total=10240,  # 10GB
                memory_free=8192,    # 8GB free
                memory_used=2048,    # 2GB used
                utilization=45.0
            ),
            CUDADevice(
                id=2,
                name="NVIDIA GeForce RTX 3060",
                compute_capability="8.6",
                memory_total=8192,   # 8GB
                memory_free=1024,    # 1GB free (low memory)
                memory_used=7168,    # 7GB used
                utilization=85.0
            )
        ]
    
    @pytest.fixture
    def sample_models(self):
        """Create sample models with different memory requirements."""
        return [
            {
                "model": ModelInfo(
                    id="small-model",
                    name="Small Language Model",
                    type=ModelType.LLAMA_CPP,
                    path="/models/small-model.gguf",
                    size=1000000000,  # 1GB
                    metadata=Mock(parameter_count=1000000000)
                ),
                "memory_requirement": 1024  # 1GB in MB
            },
            {
                "model": ModelInfo(
                    id="medium-model",
                    name="Medium Language Model",
                    type=ModelType.LLAMA_CPP,
                    path="/models/medium-model.gguf",
                    size=7000000000,  # 7GB
                    metadata=Mock(parameter_count=7000000000)
                ),
                "memory_requirement": 7168  # 7GB in MB
            },
            {
                "model": ModelInfo(
                    id="large-model",
                    name="Large Language Model",
                    type=ModelType.LLAMA_CPP,
                    path="/models/large-model.gguf",
                    size=13000000000,  # 13GB
                    metadata=Mock(parameter_count=13000000000)
                ),
                "memory_requirement": 13312  # 13GB in MB
            }
        ]
    
    @pytest.mark.asyncio
    async def test_gpu_memory_allocation_efficiency(self, cuda_engine, mock_cuda_devices, sample_models):
        """Test efficient GPU memory allocation for different model sizes."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=len(mock_cuda_devices),
            devices=mock_cuda_devices,
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=sum(device.memory_total for device in mock_cuda_devices)
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            allocation_results = []
            
            for model_data in sample_models:
                model = model_data["model"]
                required_memory = model_data["memory_requirement"] * 1024 * 1024  # Convert to bytes
                
                # Mock memory allocation
                with patch('torch.cuda.mem_get_info') as mock_mem_info, \
                     patch('torch.cuda.set_device') as mock_set_device, \
                     patch('torch.cuda.empty_cache') as mock_empty_cache:
                    
                    # Find suitable device
                    suitable_device = None
                    for device in mock_cuda_devices:
                        if device.memory_free * 1024 * 1024 >= required_memory:
                            suitable_device = device
                            break
                    
                    if suitable_device:
                        # Mock successful allocation
                        mock_mem_info.return_value = (
                            suitable_device.memory_free * 1024 * 1024 - required_memory,  # Free after allocation
                            suitable_device.memory_total * 1024 * 1024  # Total memory
                        )
                        
                        start_time = time.time()
                        memory_handle = await cuda_engine.manage_gpu_memory_allocation(required_memory)
                        allocation_time = time.time() - start_time
                        
                        allocation_results.append({
                            'model_id': model.id,
                            'required_memory_mb': required_memory // (1024 * 1024),
                            'allocated_device': suitable_device.id,
                            'allocation_time': allocation_time,
                            'success': True
                        })
                        
                        # Verify allocation properties
                        assert memory_handle is not None, f"Should allocate memory for {model.id}"
                        assert hasattr(memory_handle, 'device_id'), "Memory handle should have device ID"
                        assert hasattr(memory_handle, 'allocated_bytes'), "Memory handle should track allocated bytes"
                        assert allocation_time < 1.0, f"Allocation should be fast for {model.id}"
                    
                    else:
                        # No suitable device found
                        allocation_results.append({
                            'model_id': model.id,
                            'required_memory_mb': required_memory // (1024 * 1024),
                            'allocated_device': None,
                            'allocation_time': 0,
                            'success': False
                        })
            
            # Verify allocation efficiency
            successful_allocations = [r for r in allocation_results if r['success']]
            assert len(successful_allocations) >= 2, "Should successfully allocate memory for at least 2 models"
            
            avg_allocation_time = statistics.mean([r['allocation_time'] for r in successful_allocations])
            assert avg_allocation_time < 0.5, f"Average allocation time {avg_allocation_time:.3f}s should be under 0.5s"
            
            print(f"\nGPU Memory Allocation Results:")
            for result in allocation_results:
                status = "SUCCESS" if result['success'] else "FAILED"
                device_info = f"GPU {result['allocated_device']}" if result['allocated_device'] is not None else "No suitable device"
                print(f"  {result['model_id']}: {result['required_memory_mb']}MB -> {device_info} ({status})")
    
    @pytest.mark.asyncio
    async def test_memory_deallocation_and_cleanup(self, cuda_engine, mock_cuda_devices):
        """Test proper memory deallocation and cleanup."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=len(mock_cuda_devices),
            devices=mock_cuda_devices,
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=sum(device.memory_total for device in mock_cuda_devices)
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            # Allocate memory
            allocated_handles = []
            allocation_sizes = [1024, 2048, 4096]  # MB
            
            for size_mb in allocation_sizes:
                size_bytes = size_mb * 1024 * 1024
                
                with patch('torch.cuda.mem_get_info', return_value=(10737418240, 25769803776)):  # 10GB free, 24GB total
                    memory_handle = await cuda_engine.manage_gpu_memory_allocation(size_bytes)
                    allocated_handles.append({
                        'handle': memory_handle,
                        'size_mb': size_mb
                    })
            
            # Verify allocations
            assert len(allocated_handles) == len(allocation_sizes), "Should allocate all requested memory blocks"
            
            # Test deallocation
            deallocation_results = []
            
            for handle_data in allocated_handles:
                handle = handle_data['handle']
                size_mb = handle_data['size_mb']
                
                with patch.object(cuda_engine, '_deallocate_gpu_memory') as mock_dealloc:
                    mock_dealloc.return_value = AsyncMock(return_value=True)
                    
                    start_time = time.time()
                    success = await cuda_engine.deallocate_gpu_memory(handle)
                    deallocation_time = time.time() - start_time
                    
                    deallocation_results.append({
                        'size_mb': size_mb,
                        'deallocation_time': deallocation_time,
                        'success': success
                    })
                    
                    assert success, f"Should successfully deallocate {size_mb}MB"
                    assert deallocation_time < 0.5, f"Deallocation should be fast for {size_mb}MB"
            
            # Test memory cleanup
            with patch('torch.cuda.empty_cache') as mock_empty_cache:
                await cuda_engine.cleanup_gpu_memory()
                mock_empty_cache.assert_called(), "Should call empty_cache for cleanup"
            
            print(f"\nGPU Memory Deallocation Results:")
            for result in deallocation_results:
                print(f"  {result['size_mb']}MB: {result['deallocation_time']:.3f}s ({'SUCCESS' if result['success'] else 'FAILED'})")
    
    @pytest.mark.asyncio
    async def test_memory_fragmentation_handling(self, cuda_engine, mock_cuda_devices):
        """Test handling of GPU memory fragmentation."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=1,
            devices=[mock_cuda_devices[0]],  # Use high-memory device
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=mock_cuda_devices[0].memory_total
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            # Simulate fragmented memory allocation pattern
            fragmentation_test_sizes = [2048, 1024, 2048, 1024, 4096]  # MB, alternating sizes
            allocated_handles = []
            
            for i, size_mb in enumerate(fragmentation_test_sizes):
                size_bytes = size_mb * 1024 * 1024
                
                # Simulate decreasing available memory
                remaining_memory = (20480 - sum(fragmentation_test_sizes[:i+1])) * 1024 * 1024
                
                with patch('torch.cuda.mem_get_info', return_value=(remaining_memory, 25769803776)):
                    try:
                        memory_handle = await cuda_engine.manage_gpu_memory_allocation(size_bytes)
                        allocated_handles.append(memory_handle)
                    except RuntimeError as e:
                        if "memory" in str(e).lower():
                            # Expected when memory is exhausted
                            break
                        else:
                            raise
            
            # Test defragmentation
            with patch.object(cuda_engine, '_defragment_gpu_memory') as mock_defrag:
                mock_defrag.return_value = AsyncMock(return_value=True)
                
                defrag_success = await cuda_engine.defragment_gpu_memory()
                assert defrag_success, "Memory defragmentation should succeed"
                mock_defrag.assert_called_once(), "Should call defragmentation"
            
            print(f"\nMemory Fragmentation Handling:")
            print(f"Allocated blocks: {len(allocated_handles)}")
            print(f"Defragmentation successful: {defrag_success}")
    
    @pytest.mark.asyncio
    async def test_memory_pressure_detection(self, cuda_engine, mock_cuda_devices):
        """Test detection and handling of GPU memory pressure."""
        # Use low-memory device for pressure testing
        low_memory_device = mock_cuda_devices[2]  # RTX 3060 with 1GB free
        
        cuda_info = CUDAInfo(
            available=True,
            device_count=1,
            devices=[low_memory_device],
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=low_memory_device.memory_total
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            # Test memory pressure detection
            with patch('torch.cuda.mem_get_info', return_value=(1073741824, 8589934592)):  # 1GB free, 8GB total
                memory_pressure = await cuda_engine.detect_memory_pressure()
                
                assert memory_pressure is True, "Should detect memory pressure with low available memory"
            
            # Test pressure handling strategies
            pressure_handling_results = []
            
            strategies = [
                "reduce_batch_size",
                "enable_gradient_checkpointing",
                "use_cpu_offloading",
                "clear_cache"
            ]
            
            for strategy in strategies:
                with patch.object(cuda_engine, f'_apply_{strategy}') as mock_strategy:
                    mock_strategy.return_value = AsyncMock(return_value=True)
                    
                    start_time = time.time()
                    success = await cuda_engine.apply_memory_pressure_strategy(strategy)
                    strategy_time = time.time() - start_time
                    
                    pressure_handling_results.append({
                        'strategy': strategy,
                        'success': success,
                        'execution_time': strategy_time
                    })
                    
                    assert success, f"Memory pressure strategy '{strategy}' should succeed"
                    assert strategy_time < 1.0, f"Strategy '{strategy}' should execute quickly"
            
            print(f"\nMemory Pressure Handling:")
            print(f"Memory pressure detected: {memory_pressure}")
            for result in pressure_handling_results:
                print(f"  {result['strategy']}: {result['execution_time']:.3f}s ({'SUCCESS' if result['success'] else 'FAILED'})")
    
    @pytest.mark.asyncio
    async def test_cpu_fallback_on_memory_exhaustion(self, cuda_engine, mock_cuda_devices, sample_models):
        """Test CPU fallback when GPU memory is exhausted."""
        # Use device with limited memory
        limited_device = mock_cuda_devices[2]
        
        cuda_info = CUDAInfo(
            available=True,
            device_count=1,
            devices=[limited_device],
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=limited_device.memory_total
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            large_model = sample_models[2]  # 13GB model, won't fit in 8GB device
            
            # Attempt GPU allocation (should fail)
            with patch('torch.cuda.mem_get_info', return_value=(1073741824, 8589934592)):  # 1GB free, 8GB total
                gpu_allocation_failed = False
                
                try:
                    await cuda_engine.manage_gpu_memory_allocation(large_model["memory_requirement"] * 1024 * 1024)
                except RuntimeError as e:
                    if "memory" in str(e).lower():
                        gpu_allocation_failed = True
                
                assert gpu_allocation_failed, "GPU allocation should fail for oversized model"
            
            # Test CPU fallback
            with patch.object(cuda_engine, '_run_cpu_inference') as mock_cpu_inference:
                mock_cpu_inference.return_value = AsyncMock(return_value="CPU inference result")
                
                start_time = time.time()
                result = await cuda_engine.fallback_to_cpu_on_gpu_failure(
                    lambda: mock_cpu_inference(large_model["model"], Mock())
                )
                fallback_time = time.time() - start_time
                
                assert result == "CPU inference result", "CPU fallback should return correct result"
                assert fallback_time < 2.0, f"CPU fallback should complete reasonably quickly, took {fallback_time:.3f}s"
                mock_cpu_inference.assert_called_once(), "Should call CPU inference"
            
            print(f"\nCPU Fallback Results:")
            print(f"GPU allocation failed as expected: {gpu_allocation_failed}")
            print(f"CPU fallback time: {fallback_time:.3f}s")
            print(f"CPU fallback result: {result}")
    
    @pytest.mark.asyncio
    async def test_multi_gpu_memory_balancing(self, cuda_engine, mock_cuda_devices, sample_models):
        """Test memory load balancing across multiple GPUs."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=len(mock_cuda_devices),
            devices=mock_cuda_devices,
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=sum(device.memory_total for device in mock_cuda_devices)
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            # Test memory balancing algorithm
            memory_requests = [
                {"id": "request_1", "size_mb": 2048},  # 2GB
                {"id": "request_2", "size_mb": 4096},  # 4GB
                {"id": "request_3", "size_mb": 1024},  # 1GB
                {"id": "request_4", "size_mb": 6144},  # 6GB
                {"id": "request_5", "size_mb": 3072},  # 3GB
            ]
            
            allocation_plan = await cuda_engine.plan_multi_gpu_allocation(memory_requests)
            
            # Verify allocation plan
            assert len(allocation_plan) > 0, "Should create allocation plan"
            
            # Verify all requests are assigned
            assigned_requests = set()
            for device_id, requests in allocation_plan.items():
                for request in requests:
                    assigned_requests.add(request["id"])
            
            requested_ids = {req["id"] for req in memory_requests}
            assert assigned_requests == requested_ids, "All requests should be assigned to devices"
            
            # Verify memory constraints
            for device_id, requests in allocation_plan.items():
                device = mock_cuda_devices[device_id]
                total_allocated = sum(req["size_mb"] for req in requests)
                
                assert total_allocated <= device.memory_free, (
                    f"Device {device_id} allocation {total_allocated}MB exceeds available {device.memory_free}MB"
                )
            
            # Execute allocation plan
            execution_results = []
            
            for device_id, requests in allocation_plan.items():
                device = mock_cuda_devices[device_id]
                
                with patch('torch.cuda.set_device') as mock_set_device, \
                     patch('torch.cuda.mem_get_info', return_value=(device.memory_free * 1024 * 1024, device.memory_total * 1024 * 1024)):
                    
                    for request in requests:
                        start_time = time.time()
                        memory_handle = await cuda_engine.manage_gpu_memory_allocation(request["size_mb"] * 1024 * 1024)
                        allocation_time = time.time() - start_time
                        
                        execution_results.append({
                            'request_id': request["id"],
                            'device_id': device_id,
                            'size_mb': request["size_mb"],
                            'allocation_time': allocation_time,
                            'success': memory_handle is not None
                        })
            
            # Verify execution results
            successful_allocations = [r for r in execution_results if r['success']]
            assert len(successful_allocations) == len(memory_requests), "All allocations should succeed"
            
            avg_allocation_time = statistics.mean([r['allocation_time'] for r in successful_allocations])
            assert avg_allocation_time < 0.5, f"Average allocation time {avg_allocation_time:.3f}s should be under 0.5s"
            
            print(f"\nMulti-GPU Memory Balancing:")
            print(f"Total requests: {len(memory_requests)}")
            print(f"Devices used: {len(allocation_plan)}")
            print(f"Successful allocations: {len(successful_allocations)}")
            print(f"Average allocation time: {avg_allocation_time:.3f}s")
            
            for device_id, requests in allocation_plan.items():
                total_mb = sum(req["size_mb"] for req in requests)
                print(f"  GPU {device_id}: {len(requests)} requests, {total_mb}MB total")
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, cuda_engine, mock_cuda_devices):
        """Test detection and prevention of GPU memory leaks."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=1,
            devices=[mock_cuda_devices[0]],
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=mock_cuda_devices[0].memory_total
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            # Simulate memory allocation and tracking
            initial_memory_usage = 4096  # 4GB initially used
            allocated_memory = []
            
            # Allocate memory blocks
            allocation_sizes = [1024, 2048, 1024, 4096]  # MB
            
            for size_mb in allocation_sizes:
                size_bytes = size_mb * 1024 * 1024
                
                # Mock memory info with increasing usage
                current_usage = initial_memory_usage + sum(allocated_memory)
                free_memory = (mock_cuda_devices[0].memory_total - current_usage) * 1024 * 1024
                
                with patch('torch.cuda.mem_get_info', return_value=(free_memory, mock_cuda_devices[0].memory_total * 1024 * 1024)):
                    memory_handle = await cuda_engine.manage_gpu_memory_allocation(size_bytes)
                    allocated_memory.append(size_mb)
                    
                    # Track allocation
                    await cuda_engine.track_memory_allocation(memory_handle, size_bytes)
            
            # Simulate partial deallocation (potential leak scenario)
            deallocated_count = len(allocated_memory) // 2  # Deallocate half
            
            for i in range(deallocated_count):
                # Mock deallocation
                with patch.object(cuda_engine, '_deallocate_gpu_memory', return_value=AsyncMock(return_value=True)):
                    await cuda_engine.deallocate_gpu_memory(Mock())
            
            # Detect memory leaks
            leak_detection_result = await cuda_engine.detect_memory_leaks()
            
            # Verify leak detection
            assert leak_detection_result is not None, "Should perform leak detection"
            
            if hasattr(leak_detection_result, 'potential_leaks'):
                potential_leaks = leak_detection_result.potential_leaks
                expected_leaks = len(allocated_memory) - deallocated_count
                
                # Should detect remaining allocations as potential leaks
                assert len(potential_leaks) >= expected_leaks // 2, "Should detect some potential leaks"
            
            # Test leak cleanup
            with patch.object(cuda_engine, '_cleanup_leaked_memory') as mock_cleanup:
                mock_cleanup.return_value = AsyncMock(return_value=True)
                
                cleanup_success = await cuda_engine.cleanup_memory_leaks()
                assert cleanup_success, "Memory leak cleanup should succeed"
                mock_cleanup.assert_called_once(), "Should call leak cleanup"
            
            print(f"\nMemory Leak Detection:")
            print(f"Allocated blocks: {len(allocated_memory)}")
            print(f"Deallocated blocks: {deallocated_count}")
            print(f"Leak detection performed: {leak_detection_result is not None}")
            print(f"Cleanup successful: {cleanup_success}")
    
    @pytest.mark.asyncio
    async def test_memory_optimization_strategies(self, cuda_engine, mock_cuda_devices):
        """Test various GPU memory optimization strategies."""
        cuda_info = CUDAInfo(
            available=True,
            device_count=1,
            devices=[mock_cuda_devices[1]],  # Use RTX 3080 with moderate memory
            cuda_version="12.0",
            driver_version="525.60",
            total_memory=mock_cuda_devices[1].memory_total
        )
        
        with patch.object(cuda_engine, 'detect_cuda_availability', return_value=cuda_info):
            optimization_strategies = [
                {
                    "name": "mixed_precision",
                    "description": "Use mixed precision to reduce memory usage",
                    "expected_reduction": 0.3  # 30% reduction
                },
                {
                    "name": "gradient_checkpointing",
                    "description": "Enable gradient checkpointing",
                    "expected_reduction": 0.2  # 20% reduction
                },
                {
                    "name": "model_sharding",
                    "description": "Shard model across devices",
                    "expected_reduction": 0.4  # 40% reduction
                },
                {
                    "name": "dynamic_batching",
                    "description": "Optimize batch sizes dynamically",
                    "expected_reduction": 0.15  # 15% reduction
                }
            ]
            
            optimization_results = []
            
            for strategy in optimization_strategies:
                strategy_name = strategy["name"]
                expected_reduction = strategy["expected_reduction"]
                
                # Mock strategy implementation
                with patch.object(cuda_engine, f'_apply_{strategy_name}') as mock_strategy:
                    mock_strategy.return_value = AsyncMock(return_value={
                        'success': True,
                        'memory_saved_mb': 2048 * expected_reduction,  # Simulate memory savings
                        'performance_impact': 0.05  # 5% performance impact
                    })
                    
                    start_time = time.time()
                    result = await cuda_engine.apply_memory_optimization_strategy(strategy_name)
                    optimization_time = time.time() - start_time
                    
                    optimization_results.append({
                        'strategy': strategy_name,
                        'success': result['success'],
                        'memory_saved_mb': result['memory_saved_mb'],
                        'performance_impact': result['performance_impact'],
                        'optimization_time': optimization_time
                    })
                    
                    assert result['success'], f"Optimization strategy '{strategy_name}' should succeed"
                    assert result['memory_saved_mb'] > 0, f"Strategy '{strategy_name}' should save memory"
                    assert optimization_time < 1.0, f"Strategy '{strategy_name}' should apply quickly"
            
            # Verify overall optimization effectiveness
            total_memory_saved = sum(r['memory_saved_mb'] for r in optimization_results)
            avg_performance_impact = statistics.mean([r['performance_impact'] for r in optimization_results])
            
            assert total_memory_saved > 1000, f"Total memory saved {total_memory_saved:.0f}MB should be significant"
            assert avg_performance_impact < 0.1, f"Average performance impact {avg_performance_impact:.2%} should be minimal"
            
            print(f"\nMemory Optimization Strategies:")
            print(f"Total memory saved: {total_memory_saved:.0f}MB")
            print(f"Average performance impact: {avg_performance_impact:.2%}")
            
            for result in optimization_results:
                print(f"  {result['strategy']}: {result['memory_saved_mb']:.0f}MB saved, "
                      f"{result['performance_impact']:.2%} impact, {result['optimization_time']:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])