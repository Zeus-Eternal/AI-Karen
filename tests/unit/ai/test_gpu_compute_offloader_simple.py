"""
Simple tests for GPU Compute Offloader to avoid hanging issues
"""

import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.core.gpu_compute_offloader import (
    GPUComputeOffloader,
    GPUInfo,
    GPUBackend,
    GPUMemoryStrategy,
    GPUMemoryManager,
    GPUTask,
    is_gpu_computation_beneficial
)


class TestGPUMemoryManagerSimple:
    """Simple tests for GPU memory manager"""
    
    def test_memory_manager_init(self):
        """Test memory manager initialization"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        assert manager.strategy == GPUMemoryStrategy.LAZY
        assert manager._total_allocated == 0
    
    def test_memory_allocation(self):
        """Test basic memory allocation"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        
        block_id = manager.allocate(100)
        assert block_id is not None
        assert manager._total_allocated == 100
        
        success = manager.deallocate(block_id)
        assert success is True
        assert manager._total_allocated == 0
    
    def test_memory_stats(self):
        """Test memory usage statistics"""
        manager = GPUMemoryManager(GPUMemoryStrategy.LAZY)
        
        stats = manager.get_memory_usage()
        assert stats['total_allocated_mb'] == 0
        assert stats['active_blocks'] == 0
        
        block_id = manager.allocate(200)
        stats = manager.get_memory_usage()
        assert stats['total_allocated_mb'] == 200
        assert stats['active_blocks'] == 1


class TestGPUInfoSimple:
    """Simple tests for GPU info"""
    
    def test_gpu_info_creation(self):
        """Test GPU info creation"""
        info = GPUInfo(
            backend=GPUBackend.CUDA,
            device_count=1,
            total_memory=8192,
            available_memory=6144
        )
        
        assert info.backend == GPUBackend.CUDA
        assert info.device_count == 1
        assert info.total_memory == 8192
        assert info.available_memory == 6144
        assert info.device_names == []


class TestGPUTaskSimple:
    """Simple tests for GPU task"""
    
    def test_gpu_task_creation(self):
        """Test GPU task creation"""
        def dummy_func(x):
            return x * 2
        
        task = GPUTask(
            task_id="test_1",
            computation=dummy_func,
            data=42,
            priority=5
        )
        
        assert task.task_id == "test_1"
        assert task.computation == dummy_func
        assert task.data == 42
        assert task.priority == 5
    
    def test_task_priority_ordering(self):
        """Test task priority ordering"""
        task1 = GPUTask("task1", lambda x: x, 1, priority=1)
        task2 = GPUTask("task2", lambda x: x, 2, priority=5)
        
        # Higher priority should come first
        assert task2 < task1


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_is_gpu_computation_beneficial(self):
        """Test GPU computation benefit heuristics"""
        # Low complexity
        assert is_gpu_computation_beneficial(15, "low") is True
        assert is_gpu_computation_beneficial(5, "low") is False
        
        # Medium complexity
        assert is_gpu_computation_beneficial(8, "medium") is True
        assert is_gpu_computation_beneficial(3, "medium") is False
        
        # High complexity
        assert is_gpu_computation_beneficial(2, "high") is True
        assert is_gpu_computation_beneficial(0.5, "high") is False


class TestGPUComputeOffloaderSimple:
    """Simple tests for GPU compute offloader"""
    
    def test_offloader_creation(self):
        """Test offloader creation"""
        offloader = GPUComputeOffloader(
            max_workers=2,
            memory_strategy=GPUMemoryStrategy.LAZY,
            enable_cpu_fallback=True
        )
        
        assert offloader.max_workers == 2
        assert offloader.enable_cpu_fallback is True
        assert not offloader._initialized
    
    @pytest.mark.asyncio
    async def test_cpu_fallback_simple(self):
        """Test simple CPU fallback execution"""
        offloader = GPUComputeOffloader(enable_cpu_fallback=True)
        
        def simple_computation(x):
            return x * 2
        
        result = await offloader.fallback_to_cpu(simple_computation, 21)
        assert result == 42
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_no_gpu_fallback(self):
        """Test offloading when no GPU is available"""
        offloader = GPUComputeOffloader(enable_cpu_fallback=True)
        
        # Mock no GPU available
        offloader._gpu_info = GPUInfo(GPUBackend.NONE, 0, 0, 0)
        offloader._initialized = True
        
        def test_computation(x):
            return x ** 2
        
        result = await offloader.offload_to_gpu(test_computation, 5)
        assert result == 25
        
        await offloader.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_management_simple(self):
        """Test simple memory management"""
        offloader = GPUComputeOffloader()
        offloader._initialized = True
        
        memory_info = await offloader.manage_gpu_memory()
        assert 'memory_stats' in memory_info
        
        await offloader.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])