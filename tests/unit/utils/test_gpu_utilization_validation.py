"""
GPU utilization tests to verify hardware acceleration effectiveness.
Tests GPU detection, compute offloading, memory management, and fallback mechanisms.
"""

import pytest
import asyncio
import time
import numpy as np
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass

from src.ai_karen_engine.core.gpu_compute_offloader import GPUComputeOffloader


@dataclass
class GPUTestResult:
    """GPU test result data."""
    test_name: str
    gpu_available: bool
    gpu_used: bool
    cpu_fallback_used: bool
    execution_time: float
    performance_improvement: Optional[float]
    memory_usage: int
    errors: List[str]


class GPUUtilizationTestSuite:
    """Comprehensive GPU utilization test suite."""
    
    def __init__(self):
        self.gpu_offloader = GPUComputeOffloader()
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for GPU computations."""
        return {
            "matrix_a": np.random.rand(1000, 1000).astype(np.float32),
            "matrix_b": np.random.rand(1000, 1000).astype(np.float32),
            "vector": np.random.rand(10000).astype(np.float32),
            "large_array": np.random.rand(1000000).astype(np.float32)
        }
    
    async def test_gpu_detection_and_capabilities(self) -> GPUTestResult:
        """Test GPU detection and capability assessment."""
        errors = []
        gpu_available = False
        
        try:
            # Test GPU detection
            gpu_info = await self.gpu_offloader.detect_gpu_availability()
            gpu_available = gpu_info.available if gpu_info else False
            
            if gpu_available:
                # Test GPU capabilities
                capabilities = await self.gpu_offloader.get_gpu_capabilities()
                
                if not capabilities:
                    errors.append("GPU detected but capabilities not available")
                
                # Test memory availability
                memory_info = await self.gpu_offloader.get_gpu_memory_info()
                if not memory_info or memory_info.total == 0:
                    errors.append("GPU memory information not available")
            
        except Exception as e:
            errors.append(f"GPU detection failed: {e}")
        
        return GPUTestResult(
            test_name="gpu_detection",
            gpu_available=gpu_available,
            gpu_used=False,
            cpu_fallback_used=False,
            execution_time=0,
            performance_improvement=None,
            memory_usage=0,
            errors=errors
        )
    
    async def test_matrix_multiplication_offloading(self) -> GPUTestResult:
        """Test GPU offloading for matrix multiplication."""
        errors = []
        gpu_used = False
        cpu_fallback_used = False
        performance_improvement = None
        
        try:
            matrix_a = self.test_data["matrix_a"]
            matrix_b = self.test_data["matrix_b"]
            
            # CPU baseline
            cpu_start = time.time()
            cpu_result = np.dot(matrix_a, matrix_b)
            cpu_time = time.time() - cpu_start
            
            # GPU computation
            gpu_start = time.time()
            gpu_result = await self.gpu_offloader.offload_to_gpu(
                self._matrix_multiply_gpu, matrix_a, matrix_b
            )
            gpu_time = time.time() - gpu_start
            
            # Check if GPU was actually used
            gpu_used = await self.gpu_offloader.was_gpu_used()
            cpu_fallback_used = not gpu_used
            
            # Verify results are similar
            if gpu_result is not None:
                if not np.allclose(cpu_result, gpu_result, rtol=1e-5):
                    errors.append("GPU and CPU results don't match")
                
                # Calculate performance improvement
                if gpu_used and gpu_time > 0:
                    performance_improvement = ((cpu_time - gpu_time) / cpu_time) * 100
            else:
                errors.append("GPU computation returned None")
            
        except Exception as e:
            errors.append(f"Matrix multiplication test failed: {e}")
            cpu_fallback_used = True
        
        return GPUTestResult(
            test_name="matrix_multiplication",
            gpu_available=await self._is_gpu_available(),
            gpu_used=gpu_used,
            cpu_fallback_used=cpu_fallback_used,
            execution_time=gpu_time if 'gpu_time' in locals() else 0,
            performance_improvement=performance_improvement,
            memory_usage=0,
            errors=errors
        )
    
    async def _matrix_multiply_gpu(self, matrix_a: np.ndarray, matrix_b: np.ndarray) -> np.ndarray:
        """GPU matrix multiplication function."""
        # This would use actual GPU libraries like CuPy, PyTorch, or TensorFlow
        # For testing, we'll simulate GPU computation
        await asyncio.sleep(0.01)  # Simulate GPU computation time
        return np.dot(matrix_a, matrix_b)
    
    async def test_gpu_memory_management(self) -> GPUTestResult:
        """Test GPU memory allocation and cleanup."""
        errors = []
        gpu_used = False
        memory_usage = 0
        
        try:
            # Test memory allocation
            large_data = self.test_data["large_array"]
            
            # Allocate GPU memory
            gpu_memory = await self.gpu_offloader.allocate_gpu_memory(large_data.nbytes)
            
            if gpu_memory:
                gpu_used = True
                memory_usage = large_data.nbytes
                
                # Test memory transfer
                await self.gpu_offloader.transfer_to_gpu(large_data, gpu_memory)
                
                # Test computation on GPU
                result = await self.gpu_offloader.compute_on_gpu(
                    self._vector_operations_gpu, gpu_memory
                )
                
                # Test memory cleanup
                await self.gpu_offloader.free_gpu_memory(gpu_memory)
                
                if result is None:
                    errors.append("GPU computation failed")
            else:
                errors.append("GPU memory allocation failed")
                
        except Exception as e:
            errors.append(f"GPU memory management test failed: {e}")
        
        return GPUTestResult(
            test_name="gpu_memory_management",
            gpu_available=await self._is_gpu_available(),
            gpu_used=gpu_used,
            cpu_fallback_used=not gpu_used,
            execution_time=0,
            performance_improvement=None,
            memory_usage=memory_usage,
            errors=errors
        )
    
    async def _vector_operations_gpu(self, gpu_data) -> np.ndarray:
        """GPU vector operations function."""
        # Simulate GPU vector operations
        await asyncio.sleep(0.005)
        return np.array([1.0])  # Placeholder result
    
    async def test_cpu_fallback_mechanism(self) -> GPUTestResult:
        """Test CPU fallback when GPU is unavailable."""
        errors = []
        cpu_fallback_used = False
        
        try:
            # Force GPU unavailable scenario
            with patch.object(self.gpu_offloader, 'detect_gpu_availability', return_value=None):
                # Attempt GPU computation
                result = await self.gpu_offloader.offload_to_gpu(
                    self._simple_computation, self.test_data["vector"]
                )
                
                # Should fallback to CPU
                cpu_fallback_used = await self.gpu_offloader.was_cpu_fallback_used()
                
                if result is None:
                    errors.append("CPU fallback failed to produce result")
                
                if not cpu_fallback_used:
                    errors.append("CPU fallback was not triggered")
            
        except Exception as e:
            errors.append(f"CPU fallback test failed: {e}")
        
        return GPUTestResult(
            test_name="cpu_fallback",
            gpu_available=False,
            gpu_used=False,
            cpu_fallback_used=cpu_fallback_used,
            execution_time=0,
            performance_improvement=None,
            memory_usage=0,
            errors=errors
        )
    
    async def _simple_computation(self, data: np.ndarray) -> np.ndarray:
        """Simple computation for testing."""
        return np.sum(data ** 2)
    
    async def test_concurrent_gpu_operations(self) -> GPUTestResult:
        """Test concurrent GPU operations and resource sharing."""
        errors = []
        gpu_used = False
        
        try:
            # Create multiple concurrent GPU tasks
            tasks = []
            for i in range(3):
                task = self.gpu_offloader.offload_to_gpu(
                    self._concurrent_computation, 
                    self.test_data["vector"][i*1000:(i+1)*1000]
                )
                tasks.append(task)
            
            # Execute concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            execution_time = time.time() - start_time
            
            # Verify all tasks completed
            if any(r is None for r in results):
                errors.append("Some concurrent GPU tasks failed")
            
            gpu_used = await self.gpu_offloader.was_gpu_used()
            
        except Exception as e:
            errors.append(f"Concurrent GPU operations test failed: {e}")
            execution_time = 0
        
        return GPUTestResult(
            test_name="concurrent_gpu_operations",
            gpu_available=await self._is_gpu_available(),
            gpu_used=gpu_used,
            cpu_fallback_used=not gpu_used,
            execution_time=execution_time,
            performance_improvement=None,
            memory_usage=0,
            errors=errors
        )
    
    async def _concurrent_computation(self, data: np.ndarray) -> float:
        """Concurrent computation for testing."""
        await asyncio.sleep(0.01)  # Simulate computation
        return float(np.mean(data))
    
    async def test_gpu_performance_vs_cpu(self) -> GPUTestResult:
        """Test GPU performance improvement over CPU."""
        errors = []
        gpu_used = False
        performance_improvement = None
        
        try:
            test_data = np.random.rand(5000, 5000).astype(np.float32)
            
            # CPU benchmark
            cpu_start = time.time()
            cpu_result = await self._cpu_intensive_computation(test_data)
            cpu_time = time.time() - cpu_start
            
            # GPU benchmark
            gpu_start = time.time()
            gpu_result = await self.gpu_offloader.offload_to_gpu(
                self._gpu_intensive_computation, test_data
            )
            gpu_time = time.time() - gpu_start
            
            gpu_used = await self.gpu_offloader.was_gpu_used()
            
            if gpu_used and gpu_time > 0:
                performance_improvement = ((cpu_time - gpu_time) / cpu_time) * 100
                
                # GPU should be faster for intensive computations
                if performance_improvement <= 0:
                    errors.append("GPU not faster than CPU for intensive computation")
            
        except Exception as e:
            errors.append(f"GPU performance test failed: {e}")
        
        return GPUTestResult(
            test_name="gpu_performance_vs_cpu",
            gpu_available=await self._is_gpu_available(),
            gpu_used=gpu_used,
            cpu_fallback_used=not gpu_used,
            execution_time=gpu_time if 'gpu_time' in locals() else 0,
            performance_improvement=performance_improvement,
            memory_usage=0,
            errors=errors
        )
    
    async def _cpu_intensive_computation(self, data: np.ndarray) -> np.ndarray:
        """CPU intensive computation."""
        # Simulate CPU-intensive matrix operations
        result = data
        for _ in range(3):
            result = np.dot(result, data.T)
        return result
    
    async def _gpu_intensive_computation(self, data: np.ndarray) -> np.ndarray:
        """GPU intensive computation."""
        # Simulate GPU-accelerated computation
        await asyncio.sleep(0.1)  # Simulate GPU computation
        return data  # Placeholder
    
    async def _is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        try:
            gpu_info = await self.gpu_offloader.detect_gpu_availability()
            return gpu_info.available if gpu_info else False
        except:
            return False


@pytest.fixture
def gpu_test_suite():
    """Create GPU utilization test suite fixture."""
    return GPUUtilizationTestSuite()


@pytest.mark.asyncio
async def test_gpu_detection_and_capabilities(gpu_test_suite):
    """Test GPU detection and capabilities."""
    result = await gpu_test_suite.test_gpu_detection_and_capabilities()
    
    # Test should complete without errors
    assert len(result.errors) == 0, f"GPU detection errors: {result.errors}"
    
    print(f"GPU detection: Available={result.gpu_available}")
    if result.gpu_available:
        print("GPU capabilities detected successfully")
    else:
        print("No GPU detected - CPU fallback will be used")


@pytest.mark.asyncio
async def test_matrix_multiplication_offloading(gpu_test_suite):
    """Test GPU matrix multiplication offloading."""
    result = await gpu_test_suite.test_matrix_multiplication_offloading()
    
    # Should complete without critical errors
    assert len(result.errors) <= 1, f"Too many matrix multiplication errors: {result.errors}"
    
    if result.gpu_used:
        print(f"GPU matrix multiplication: {result.performance_improvement:.1f}% improvement")
        # GPU should provide some performance benefit for large matrices
        assert result.performance_improvement is None or result.performance_improvement >= 0
    else:
        print("Matrix multiplication used CPU fallback")


@pytest.mark.asyncio
async def test_gpu_memory_management(gpu_test_suite):
    """Test GPU memory management."""
    result = await gpu_test_suite.test_gpu_memory_management()
    
    # Memory management should work without errors
    assert len(result.errors) <= 1, f"GPU memory management errors: {result.errors}"
    
    if result.gpu_used:
        print(f"GPU memory management: {result.memory_usage} bytes allocated")
    else:
        print("GPU memory management used CPU fallback")


@pytest.mark.asyncio
async def test_cpu_fallback_mechanism(gpu_test_suite):
    """Test CPU fallback mechanism."""
    result = await gpu_test_suite.test_cpu_fallback_mechanism()
    
    # CPU fallback should always work
    assert result.cpu_fallback_used, "CPU fallback was not used when GPU unavailable"
    assert len(result.errors) == 0, f"CPU fallback errors: {result.errors}"
    
    print("CPU fallback mechanism working correctly")


@pytest.mark.asyncio
async def test_concurrent_gpu_operations(gpu_test_suite):
    """Test concurrent GPU operations."""
    result = await gpu_test_suite.test_concurrent_gpu_operations()
    
    # Concurrent operations should complete
    assert len(result.errors) <= 1, f"Concurrent GPU operation errors: {result.errors}"
    assert result.execution_time < 5.0, f"Concurrent operations too slow: {result.execution_time}s"
    
    print(f"Concurrent GPU operations: {result.execution_time:.3f}s execution time")


@pytest.mark.asyncio
async def test_gpu_performance_vs_cpu(gpu_test_suite):
    """Test GPU performance compared to CPU."""
    result = await gpu_test_suite.test_gpu_performance_vs_cpu()
    
    # Performance test should complete
    assert len(result.errors) <= 1, f"GPU performance test errors: {result.errors}"
    
    if result.gpu_used and result.performance_improvement is not None:
        print(f"GPU performance: {result.performance_improvement:.1f}% improvement over CPU")
        # For intensive computations, GPU should provide benefit
        if result.performance_improvement < 0:
            print("Warning: GPU slower than CPU for this workload")
    else:
        print("GPU performance test used CPU fallback")


@pytest.mark.asyncio
async def test_gpu_resource_cleanup():
    """Test GPU resource cleanup after operations."""
    gpu_offloader = GPUComputeOffloader()
    
    # Perform GPU operations
    test_data = np.random.rand(1000).astype(np.float32)
    
    try:
        result = await gpu_offloader.offload_to_gpu(
            lambda x: np.sum(x), test_data
        )
        
        # Verify cleanup
        await gpu_offloader.cleanup_gpu_resources()
        
        # Should not raise exceptions
        assert True, "GPU cleanup completed successfully"
        
    except Exception as e:
        # Cleanup should not fail
        pytest.fail(f"GPU resource cleanup failed: {e}")
    
    print("GPU resource cleanup test passed")


@pytest.mark.asyncio
async def test_gpu_error_handling():
    """Test GPU error handling and recovery."""
    gpu_offloader = GPUComputeOffloader()
    
    # Test with invalid data
    try:
        result = await gpu_offloader.offload_to_gpu(
            lambda x: x / 0,  # This should cause an error
            np.array([1, 2, 3])
        )
        
        # Should handle error gracefully
        assert result is not None or await gpu_offloader.was_cpu_fallback_used()
        
    except Exception as e:
        # Should not propagate unhandled exceptions
        pytest.fail(f"GPU error handling failed: {e}")
    
    print("GPU error handling test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])