#!/usr/bin/env python3
"""
Simple unit tests for CUDA Acceleration Engine that can run with pytest.
"""

import pytest
import asyncio
import sys
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch


def load_cuda_engine():
    """Load CUDA engine directly from file."""
    cuda_engine_path = Path(__file__).parent / "src" / "ai_karen_engine" / "services" / "cuda_acceleration_engine.py"
    spec = importlib.util.spec_from_file_location("cuda_acceleration_engine", cuda_engine_path)
    cuda_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cuda_module)
    return cuda_module


@pytest.fixture
def cuda_module():
    """Fixture to provide CUDA module."""
    return load_cuda_engine()


@pytest.fixture
def cuda_engine(cuda_module):
    """Fixture to provide CUDA engine instance."""
    return cuda_module.CUDAAccelerationEngine()


class TestCUDAAccelerationEngine:
    """Test suite for CUDA Acceleration Engine."""
    
    def test_cuda_engine_instantiation(self, cuda_module):
        """Test CUDA engine can be instantiated."""
        engine = cuda_module.CUDAAccelerationEngine()
        assert engine is not None
        assert engine.max_gpu_memory_usage == 0.8
        assert engine.cache_cleanup_threshold == 0.9
        assert engine.batch_timeout == 0.1
        assert engine.max_batch_size == 32
    
    def test_cuda_engine_custom_config(self, cuda_module):
        """Test CUDA engine with custom configuration."""
        engine = cuda_module.CUDAAccelerationEngine(
            max_gpu_memory_usage=0.7,
            cache_cleanup_threshold=0.8,
            batch_timeout=0.2,
            max_batch_size=16
        )
        assert engine.max_gpu_memory_usage == 0.7
        assert engine.cache_cleanup_threshold == 0.8
        assert engine.batch_timeout == 0.2
        assert engine.max_batch_size == 16
    
    def test_cuda_data_models(self, cuda_module):
        """Test CUDA data model creation."""
        # Test CUDADevice
        device = cuda_module.CUDADevice(
            id=0,
            name="Test GPU",
            compute_capability="8.6",
            memory_total=1000000,
            memory_free=800000,
            memory_used=200000,
            utilization=50.0
        )
        assert device.id == 0
        assert device.name == "Test GPU"
        assert device.compute_capability == "8.6"
        assert device.utilization == 50.0
        
        # Test CUDAInfo
        cuda_info = cuda_module.CUDAInfo(
            available=True,
            device_count=1,
            devices=[device]
        )
        assert cuda_info.available is True
        assert cuda_info.device_count == 1
        assert len(cuda_info.devices) == 1
        
        # Test GPUMemoryHandle
        handle = cuda_module.GPUMemoryHandle(device_id=0, size=1000000)
        assert handle.device_id == 0
        assert handle.size == 1000000
        assert handle.allocated_at > 0
        
        # Test GPUMetrics
        metrics = cuda_module.GPUMetrics(
            utilization_percentage=75.0,
            memory_usage_percentage=60.0,
            temperature=70.0,
            power_usage=250.0,
            inference_throughput=15.0,
            batch_processing_efficiency=85.0
        )
        assert metrics.utilization_percentage == 75.0
        assert metrics.memory_usage_percentage == 60.0
        assert metrics.temperature == 70.0
        
        # Test ModelComponent
        component = cuda_module.ModelComponent(
            id="test_model",
            name="Test Model",
            data="mock_data",
            size=1000000
        )
        assert component.id == "test_model"
        assert component.name == "Test Model"
        assert component.size == 1000000
        
        # Test BatchRequest
        request = cuda_module.BatchRequest(
            id="req1",
            input_data="test_input",
            model_id="model1",
            priority=1
        )
        assert request.id == "req1"
        assert request.input_data == "test_input"
        assert request.model_id == "model1"
        assert request.priority == 1
        
        # Test BatchResponse
        response = cuda_module.BatchResponse(
            request_id="req1",
            output_data="test_output",
            processing_time=0.1,
            gpu_time=0.05,
            success=True
        )
        assert response.request_id == "req1"
        assert response.output_data == "test_output"
        assert response.processing_time == 0.1
        assert response.success is True
    
    def test_required_methods_exist(self, cuda_engine):
        """Test that all required methods exist."""
        required_methods = [
            'detect_cuda_availability',
            'initialize_cuda_context',
            'offload_model_inference_to_gpu',
            'manage_gpu_memory_allocation',
            'cache_model_components_on_gpu',
            'monitor_gpu_utilization',
            'fallback_to_cpu_on_gpu_failure',
            'optimize_gpu_batch_processing',
            'get_performance_summary',
            'shutdown'
        ]
        
        for method_name in required_methods:
            assert hasattr(cuda_engine, method_name), f"Method {method_name} not found"
            method = getattr(cuda_engine, method_name)
            assert callable(method), f"Method {method_name} is not callable"
    
    @pytest.mark.asyncio
    async def test_cuda_detection(self, cuda_engine):
        """Test CUDA detection functionality."""
        cuda_info = await cuda_engine.detect_cuda_availability()
        
        assert hasattr(cuda_info, 'available')
        assert hasattr(cuda_info, 'device_count')
        assert hasattr(cuda_info, 'devices')
        assert isinstance(cuda_info.available, bool)
        assert isinstance(cuda_info.device_count, int)
        assert isinstance(cuda_info.devices, list)
    
    @pytest.mark.asyncio
    async def test_cuda_initialization(self, cuda_engine):
        """Test CUDA context initialization."""
        # First detect CUDA
        await cuda_engine.detect_cuda_availability()
        
        # Then initialize context
        context = await cuda_engine.initialize_cuda_context()
        
        # Context can be None if CUDA is not available
        if context is not None:
            assert 'status' in context
            assert 'devices' in context
    
    @pytest.mark.asyncio
    async def test_cpu_fallback(self, cuda_engine):
        """Test CPU fallback mechanisms."""
        def sync_computation():
            return "sync_result"
        
        async def async_computation():
            return "async_result"
        
        # Test sync fallback
        sync_result = await cuda_engine.fallback_to_cpu_on_gpu_failure(sync_computation)
        assert sync_result == "sync_result"
        
        # Test async fallback
        async_result = await cuda_engine.fallback_to_cpu_on_gpu_failure(async_computation)
        assert async_result == "async_result"
    
    @pytest.mark.asyncio
    async def test_model_inference(self, cuda_engine):
        """Test model inference (should fallback to CPU without CUDA)."""
        model_info = {
            'id': 'test_model',
            'name': 'Test Model',
            'size': 1000000
        }
        
        result = await cuda_engine.offload_model_inference_to_gpu(model_info, "test input")
        assert result is not None
        # Should contain CPU processing indication
        assert "CPU_processed" in str(result)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, cuda_engine):
        """Test batch processing optimization."""
        batch_requests = [
            {
                'id': 'req1',
                'input_data': 'input1',
                'model_info': {'id': 'model1'}
            },
            {
                'id': 'req2',
                'input_data': 'input2',
                'model_info': {'id': 'model1'}
            }
        ]
        
        responses = await cuda_engine.optimize_gpu_batch_processing(batch_requests)
        
        assert len(responses) == 2
        for response in responses:
            assert 'request_id' in response
            assert 'success' in response
            assert 'result' in response
            assert 'processing_time' in response
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, cuda_engine):
        """Test GPU performance monitoring."""
        metrics = await cuda_engine.monitor_gpu_utilization()
        
        assert hasattr(metrics, 'utilization_percentage')
        assert hasattr(metrics, 'memory_usage_percentage')
        assert hasattr(metrics, 'temperature')
        assert hasattr(metrics, 'power_usage')
        assert hasattr(metrics, 'inference_throughput')
        assert hasattr(metrics, 'batch_processing_efficiency')
        
        # Values should be non-negative
        assert metrics.utilization_percentage >= 0
        assert metrics.memory_usage_percentage >= 0
        assert metrics.temperature >= 0
        assert metrics.power_usage >= 0
        assert metrics.inference_throughput >= 0
        assert metrics.batch_processing_efficiency >= 0
    
    @pytest.mark.asyncio
    async def test_performance_summary(self, cuda_engine):
        """Test performance summary generation."""
        summary = await cuda_engine.get_performance_summary()
        
        required_keys = ['cuda_available', 'initialized', 'device_count']
        for key in required_keys:
            assert key in summary, f"Summary missing key: {key}"
        
        assert isinstance(summary['cuda_available'], bool)
        assert isinstance(summary['initialized'], bool)
        assert isinstance(summary['device_count'], int)
    
    @pytest.mark.asyncio
    async def test_shutdown(self, cuda_engine):
        """Test engine shutdown."""
        # Should not raise any exceptions
        await cuda_engine.shutdown()
        assert cuda_engine.initialized is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])