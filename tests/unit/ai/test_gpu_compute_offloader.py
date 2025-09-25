"""
Tests for GPU Compute Offloader

Tests GPU detection, memory management, task offloading, and CPU fallback functionality.
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.gpu_compute_offloader import (
    GPUComputeOffloader,
    GPUInfo,
    GPUBackend,
    GPUMemoryStrategy,
    GPUMemoryManager,
    GPUTask,
    create_gpu_offloader,
    is_gpu_computation_beneficial,
    matrix_multiply_gpu_optimized,
    ml_inference_gpu_optimized,
    image_processing_gpu_optimized
)


class TestGPUMemoryManager:
    """Test GPU memory management functionality"""
    
    def test_memory_manager_initialization(self):
        """Test memory manager initialization with different strategies"""
        # Test lazy strategy
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        assert manager.strategy == GPUMemoryStrategy.LAZY
        assert manager._total_allocated == 0
        
        # Test pooled strategy
        manager = GPUMemoryManager(GPUMemoryStrategy.POOLED)
        assert manager.strategy == GPUMemoryStrategy.POOLED
    
    def test_memory_allocation_and_deallocation(self):
        """Test basic memory allocation and deallocation"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        
        # Allocate memory
        block_id = manager.allocate(100, device_id=0)
        assert block_id is not None
        assert manager._total_allocated == 100
        
        # Deallocate memory
        success = manager.deallocate(block_id)
        assert success is True
        assert manager._total_allocated == 0
    
    def test_pooled_memory_strategy(self):
        """Test pooled memory management strategy"""
        manager = GPUMemoryManager(GPUMemoryStrategy.POOLED)
        
        # Allocate and deallocate to populate pool
        block_id = manager.allocate(100, device_id=0)
        manager.deallocate(block_id)
        
        # Allocate again - should reuse from pool
        new_block_id = manager.allocate(100, device_id=0)
        assert new_block_id == block_id  # Should reuse the same block
    
    def test_memory_usage_statistics(self):
        """Test memory usage statistics"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        
        # Initial state
        stats = manager.get_memory_usage()
        assert stats['total_allocated_mb'] == 0
        assert stats['active_blocks'] == 0
        
        # After allocation
        block_id = manager.allocate(200)
        stats = manager.get_memory_usage()
        assert stats['total_allocated_mb'] == 200
        assert stats['active_blocks'] == 1
    
    def test_cleanup_expired_blocks(self):
        """Test cleanup of expired memory blocks"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        
        # Allocate some blocks
        block1 = manager.allocate(100)
        block2 = manager.allocate(150)
        
        # Manually set old timestamp for block1
        manager._allocated_blocks[block1]['allocated_at'] = time.time() - 400
        
        # Cleanup with 300 second threshold
        cleaned = manager.cleanup_expired_blocks(max_age_seconds=300)
        assert cleaned == 1
        assert manager._total_allocated == 150  # Only block2 remains


class TestGPUInfo:
    """Test GPU information data structure"""
    
    def test_gpu_info_creation(self):
        """Test GPU info creation and defaults"""
        info = GPUInfo(
            backend=GPUBackend.CUDA,
            device_count=2,
            total_memory=8192,
            available_memory=6144
        )
        
        assert info.backend == GPUBackend.CUDA
        assert info.device_count == 2
        assert info.total_memory == 8192
        assert info.available_memory == 6144
        assert info.device_names == []  # Default empty list
    
    def test_gpu_info_with_device_names(self):
        """Test GPU info with device names"""
        device_names = ["GeForce RTX 3080", "GeForce RTX 3090"]
        info = GPUInfo(
            backend=GPUBackend.CUDA,
            device_count=2,
            total_memory=8192,
            available_memory=6144,
            device_names=device_names
        )
        
        assert info.device_names == device_names


class TestGPUTask:
    """Test GPU task data structure"""
    
    def test_gpu_task_creation(self):
        """Test GPU task creation"""
        def dummy_computation(x):
            return x * 2
        
        task = GPUTask(
            task_id="test_task_1",
            computation=dummy_computation,
            data=42,
            priority=5
        )
        
        assert task.task_id == "test_task_1"
        assert task.computation == dummy_computation
        assert task.data == 42
        assert task.priority == 5
    
    def test_gpu_task_priority_ordering(self):
        """Test GPU task priority ordering"""
        task1 = GPUTask("task1", lambda x: x, 1, priority=1)
        task2 = GPUTask("task2", lambda x: x, 2, priority=5)
        task3 = GPUTask("task3", lambda x: x, 3, priority=3)
        
        # Higher priority should come first
        assert task2 < task3 < task1


class TestGPUComputeOffloader:
    """Test main GPU compute offloader functionality"""
    
    @pytest.fixture
    def offloader(self):
        """Create GPU compute offloader for testing"""
        return GPUComputeOffloader(
            max_workers=2,
            memory_strategy=GPUMemoryStrategy.LAZY,
            enable_cpu_fallback=True
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, offloader):
        """Test GPU compute offloader initialization"""
        assert not offloader._initialized
        
        success = await offloader.initialize()
        assert success is True
        assert offloader._initialized is True
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_gpu_detection_no_gpu(self, offloader):
        """Test GPU detection when no GPU is available"""
        with patch.object(offloader, '_detect_cuda') as mock_cuda, \
             patch.object(offloader, '_detect_metal') as mock_metal, \
             patch.object(offloader, '_detect_opencl') as mock_opencl:
            
            # Mock all detection methods to return no GPU
            no_gpu_info = GPUInfo(GPUBackend.NONE, 0, 0, 0)
            mock_cuda.return_value = no_gpu_info
            mock_metal.return_value = no_gpu_info
            mock_opencl.return_value = no_gpu_info
            
            gpu_info = await offloader.detect_gpu_availability()
            assert gpu_info.backend == GPUBackend.NONE
            assert gpu_info.device_count == 0
    
    @pytest.mark.asyncio
    async def test_cuda_detection_with_pynvml(self, offloader):
        """Test CUDA detection with pynvml"""
        with patch('src.ai_karen_engine.core.gpu_compute_offloader.pynvml') as mock_pynvml:
            # Mock pynvml functions
            mock_pynvml.nvmlInit.return_value = None
            mock_pynvml.nvmlDeviceGetCount.return_value = 1
            
            mock_handle = Mock()
            mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
            mock_pynvml.nvmlDeviceGetName.return_value = b"GeForce RTX 3080"
            
            mock_memory_info = Mock()
            mock_memory_info.total = 8 * 1024 * 1024 * 1024  # 8GB in bytes
            mock_memory_info.free = 6 * 1024 * 1024 * 1024   # 6GB free
            mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_memory_info
            
            mock_pynvml.nvmlSystemGetDriverVersion.return_value = b"470.82.01"
            
            gpu_info = await offloader._detect_cuda()
            
            assert gpu_info.backend == GPUBackend.CUDA
            assert gpu_info.device_count == 1
            assert gpu_info.total_memory == 8192  # 8GB in MB
            assert gpu_info.available_memory == 6144  # 6GB in MB
            assert gpu_info.device_names == ["GeForce RTX 3080"]
            assert gpu_info.driver_version == "470.82.01"
    
    @pytest.mark.asyncio
    async def test_cuda_detection_with_nvidia_smi(self, offloader):
        """Test CUDA detection fallback to nvidia-smi"""
        with patch('src.ai_karen_engine.core.gpu_compute_offloader.pynvml', side_effect=ImportError):
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                # Mock nvidia-smi output
                mock_process = Mock()
                mock_process.returncode = 0
                mock_process.communicate.return_value = (
                    b"1, GeForce RTX 3080, 8192, 6144\n",
                    b""
                )
                mock_subprocess.return_value = mock_process
                
                gpu_info = await offloader._detect_cuda()
                
                assert gpu_info.backend == GPUBackend.CUDA
                assert gpu_info.device_count == 1
                assert gpu_info.total_memory == 8192
                assert gpu_info.available_memory == 6144
                assert gpu_info.device_names == ["GeForce RTX 3080"]
    
    @pytest.mark.asyncio
    async def test_metal_detection(self, offloader):
        """Test Metal GPU detection on macOS"""
        with patch('platform.system', return_value='Darwin'):
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = Mock()
                mock_process.returncode = 0
                mock_process.communicate.return_value = (
                    b"Graphics: Apple M1 Pro\nMetal: Supported\n",
                    b""
                )
                mock_subprocess.return_value = mock_process
                
                gpu_info = await offloader._detect_metal()
                
                assert gpu_info.backend == GPUBackend.METAL
                assert gpu_info.device_count == 1
                assert gpu_info.device_names == ["Metal GPU"]
    
    @pytest.mark.asyncio
    async def test_opencl_detection(self, offloader):
        """Test OpenCL GPU detection"""
        with patch('src.ai_karen_engine.core.gpu_compute_offloader.cl') as mock_cl:
            # Mock OpenCL platform and devices
            mock_device = Mock()
            mock_device.name = "AMD Radeon RX 6800"
            mock_device.global_mem_size = 16 * 1024 * 1024 * 1024  # 16GB
            
            mock_platform = Mock()
            mock_platform.get_devices.return_value = [mock_device]
            
            mock_cl.get_platforms.return_value = [mock_platform]
            mock_cl.device_type.GPU = "GPU"
            
            gpu_info = await offloader._detect_opencl()
            
            assert gpu_info.backend == GPUBackend.OPENCL
            assert gpu_info.device_count == 1
            assert gpu_info.total_memory == 16384  # 16GB in MB
            assert gpu_info.device_names == ["AMD Radeon RX 6800"]
    
    @pytest.mark.asyncio
    async def test_cpu_fallback_execution(self, offloader):
        """Test CPU fallback execution"""
        await offloader.initialize()
        
        def test_computation(x):
            return x * 2
        
        result = await offloader.fallback_to_cpu(test_computation, 21)
        assert result == 42
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_gpu_offload_with_cpu_fallback(self, offloader):
        """Test GPU offload that falls back to CPU"""
        # Mock no GPU available
        offloader._gpu_info = GPUInfo(GPUBackend.NONE, 0, 0, 0)
        await offloader.initialize()
        
        def test_computation(x):
            return x ** 2
        
        result = await offloader.offload_to_gpu(test_computation, 5)
        assert result == 25
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_batch_gpu_offload(self, offloader):
        """Test batch GPU task processing"""
        await offloader.initialize()
        
        def multiply_by_two(x):
            return x * 2
        
        def add_ten(x):
            return x + 10
        
        tasks = [
            (multiply_by_two, 5),
            (add_ten, 15),
            (multiply_by_two, 8)
        ]
        
        results = await offloader.batch_offload_to_gpu(tasks)
        assert results == [10, 25, 16]
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_gpu_memory_management(self, offloader):
        """Test GPU memory management operations"""
        await offloader.initialize()
        
        memory_info = await offloader.manage_gpu_memory()
        assert 'memory_stats' in memory_info
        assert 'cleaned_blocks' in memory_info
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_gpu_utilization_stats(self, offloader):
        """Test GPU utilization statistics"""
        # Mock GPU available
        offloader._gpu_info = GPUInfo(
            backend=GPUBackend.CUDA,
            device_count=1,
            total_memory=8192,
            available_memory=6144
        )
        await offloader.initialize()
        
        stats = await offloader.get_gpu_utilization()
        assert stats['gpu_available'] is True
        assert stats['backend'] == 'cuda'
        assert stats['device_count'] == 1
        assert stats['total_memory_mb'] == 8192
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_gpu_utilization_no_gpu(self, offloader):
        """Test GPU utilization when no GPU available"""
        offloader._gpu_info = GPUInfo(GPUBackend.NONE, 0, 0, 0)
        await offloader.initialize()
        
        stats = await offloader.get_gpu_utilization()
        assert stats['gpu_available'] is False
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, offloader):
        """Test proper shutdown and cleanup"""
        await offloader.initialize()
        assert offloader._initialized is True
        
        await offloader.shutdown()
        assert offloader._initialized is False


class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.mark.asyncio
    async def test_create_gpu_offloader_factory(self):
        """Test GPU offloader factory function"""
        offloader = await create_gpu_offloader(
            max_workers=3,
            memory_strategy=GPUMemoryStrategy.POOLED,
            enable_cpu_fallback=False
        )
        
        assert offloader.max_workers == 3
        assert offloader._memory_manager.strategy == GPUMemoryStrategy.POOLED
        assert offloader.enable_cpu_fallback is False
        assert offloader._initialized is True
        
        await offloader.shutdown()
    
    def test_is_gpu_computation_beneficial(self):
        """Test GPU computation benefit heuristics"""
        # Low complexity tasks
        assert is_gpu_computation_beneficial(15, "low") is True
        assert is_gpu_computation_beneficial(5, "low") is False
        
        # Medium complexity tasks
        assert is_gpu_computation_beneficial(8, "medium") is True
        assert is_gpu_computation_beneficial(3, "medium") is False
        
        # High complexity tasks
        assert is_gpu_computation_beneficial(2, "high") is True
        assert is_gpu_computation_beneficial(0.5, "high") is False


class TestGPUOptimizedFunctions:
    """Test GPU-optimized computation functions"""
    
    def test_matrix_multiply_gpu_optimized(self):
        """Test GPU-optimized matrix multiplication"""
        matrix_a = np.array([[1, 2], [3, 4]])
        matrix_b = np.array([[5, 6], [7, 8]])
        
        result = matrix_multiply_gpu_optimized((matrix_a, matrix_b))
        expected = np.array([[19, 22], [43, 50]])
        
        np.testing.assert_array_equal(result, expected)
    
    def test_matrix_multiply_with_lists(self):
        """Test matrix multiplication with list inputs"""
        matrix_a = [[1, 2], [3, 4]]
        matrix_b = [[5, 6], [7, 8]]
        
        result = matrix_multiply_gpu_optimized((matrix_a, matrix_b))
        expected = np.array([[19, 22], [43, 50]])
        
        np.testing.assert_array_equal(result, expected)
    
    def test_ml_inference_gpu_optimized(self):
        """Test GPU-optimized ML inference"""
        model_data = {
            'model': 'test_model',
            'input': [1, 2, 3, 4]
        }
        
        result = ml_inference_gpu_optimized(model_data)
        assert result['prediction'] == 'gpu_optimized_result'
        assert result['confidence'] == 0.95
    
    def test_ml_inference_invalid_data(self):
        """Test ML inference with invalid data"""
        model_data = {'invalid': 'data'}
        
        result = ml_inference_gpu_optimized(model_data)
        assert 'error' in result
    
    def test_image_processing_gpu_optimized(self):
        """Test GPU-optimized image processing"""
        image_data = {
            'image': 'test_image_data',
            'operation': 'blur'
        }
        
        result = image_processing_gpu_optimized(image_data)
        assert result['processed_image'] == 'gpu_processed_blur'
        assert 'processing_time_ms' in result
    
    def test_image_processing_invalid_data(self):
        """Test image processing with invalid data"""
        image_data = {'invalid': 'data'}
        
        result = image_processing_gpu_optimized(image_data)
        assert 'error' in result


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_offload_with_timeout(self):
        """Test GPU offload with timeout"""
        offloader = GPUComputeOffloader(enable_cpu_fallback=True)
        await offloader.initialize()
        
        def slow_computation(x):
            time.sleep(0.1)  # Simulate slow computation
            return x * 2
        
        # Test with sufficient timeout
        result = await offloader.offload_to_gpu(
            slow_computation, 5, timeout=0.2
        )
        assert result == 10
        
        # Test with insufficient timeout
        with pytest.raises(asyncio.TimeoutError):
            await offloader.offload_to_gpu(
                slow_computation, 5, timeout=0.05
            )
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_offload_without_cpu_fallback(self):
        """Test GPU offload failure without CPU fallback"""
        offloader = GPUComputeOffloader(enable_cpu_fallback=False)
        offloader._gpu_info = GPUInfo(GPUBackend.NONE, 0, 0, 0)
        await offloader.initialize()
        
        def test_computation(x):
            return x * 2
        
        with pytest.raises(RuntimeError, match="CPU fallback is disabled"):
            await offloader.offload_to_gpu(test_computation, 5)
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_allocation_failure(self):
        """Test handling of GPU memory allocation failure"""
        offloader = GPUComputeOffloader()
        offloader._gpu_info = GPUInfo(
            backend=GPUBackend.CUDA,
            device_count=1,
            total_memory=1024,
            available_memory=512
        )
        await offloader.initialize()
        
        # Mock memory allocation failure
        with patch.object(offloader._memory_manager, 'allocate', return_value=None):
            def test_computation(x):
                return x * 2
            
            # Should fall back to CPU
            result = await offloader.offload_to_gpu(
                test_computation, 5, memory_requirement=1000
            )
            assert result == 10
        
        await offloader.shutdown()


if __name__ == "__main__":
    pytest.main([__file__])