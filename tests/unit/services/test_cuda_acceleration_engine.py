"""
Unit tests for CUDA Acceleration Engine.

Tests GPU acceleration capabilities including device detection, memory management,
model inference offloading, and performance optimization.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

# Mock torch and CUDA modules before importing the engine
torch_mock = MagicMock()
torch_mock.cuda.is_available.return_value = True
torch_mock.cuda.device_count.return_value = 2
torch_mock.cuda.get_device_properties.return_value = MagicMock(
    name="NVIDIA GeForce RTX 3080",
    total_memory=10737418240,  # 10GB
    major=8,
    minor=6
)
torch_mock.cuda.memory_reserved.return_value = 8589934592  # 8GB free
torch_mock.version.cuda = "11.8"

with patch.dict('sys.modules', {
    'torch': torch_mock,
    'torch.cuda': torch_mock.cuda,
    'cupy': MagicMock(),
    'pynvml': MagicMock()
}):
    from src.ai_karen_engine.services.cuda_acceleration_engine import (
        CUDAAccelerationEngine,
        CUDADevice,
        CUDAInfo,
        GPUMemoryHandle,
        GPUMetrics,
        ModelComponent,
        BatchRequest,
        BatchResponse
    )


class TestCUDAAccelerationEngine:
    """Test suite for CUDA Acceleration Engine."""
    
    @pytest.fixture
    async def cuda_engine(self):
        """Create CUDA acceleration engine for testing."""
        engine = CUDAAccelerationEngine(
            max_gpu_memory_usage=0.8,
            cache_cleanup_threshold=0.9,
            batch_timeout=0.1,
            max_batch_size=16
        )
        yield engine
        await engine.shutdown()
    
    @pytest.fixture
    def mock_cuda_info(self):
        """Mock CUDA information."""
        return CUDAInfo(
            available=True,
            device_count=2,
            devices=[
                CUDADevice(
                    id=0,
                    name="NVIDIA GeForce RTX 3080",
                    compute_capability="8.6",
                    memory_total=10737418240,
                    memory_free=8589934592,
                    memory_used=2147483648,
                    utilization=25.0,
                    temperature=65.0,
                    power_usage=220.0
                ),
                CUDADevice(
                    id=1,
                    name="NVIDIA GeForce RTX 3070",
                    compute_capability="8.6",
                    memory_total=8589934592,
                    memory_free=6442450944,
                    memory_used=2147483648,
                    utilization=15.0,
                    temperature=60.0,
                    power_usage=180.0
                )
            ],
            cuda_version="11.8",
            driver_version="525.60.11",
            total_memory=19327352832
        )
    
    @pytest.mark.asyncio
    async def test_detect_cuda_availability_success(self, cuda_engine):
        """Test successful CUDA detection."""
        with patch.object(cuda_engine, '_get_device_info') as mock_get_device:
            mock_get_device.side_effect = [
                CUDADevice(0, "RTX 3080", "8.6", 10737418240, 8589934592, 2147483648, 25.0),
                CUDADevice(1, "RTX 3070", "8.6", 8589934592, 6442450944, 2147483648, 15.0)
            ]
            
            cuda_info = await cuda_engine.detect_cuda_availability()
            
            assert cuda_info.available is True
            assert cuda_info.device_count == 2
            assert len(cuda_info.devices) == 2
            assert cuda_info.cuda_version == "11.8"
            assert cuda_info.total_memory > 0
    
    @pytest.mark.asyncio
    async def test_detect_cuda_availability_not_available(self, cuda_engine):
        """Test CUDA detection when CUDA is not available."""
        with patch('torch.cuda.is_available', return_value=False):
            cuda_info = await cuda_engine.detect_cuda_availability()
            
            assert cuda_info.available is False
            assert cuda_info.device_count == 0
            assert len(cuda_info.devices) == 0
    
    @pytest.mark.asyncio
    async def test_initialize_cuda_context_success(self, cuda_engine, mock_cuda_info):
        """Test successful CUDA context initialization."""
        cuda_engine.cuda_info = mock_cuda_info
        
        with patch.object(cuda_engine, '_start_batch_processor') as mock_start_batch:
            mock_start_batch.return_value = None
            
            context = await cuda_engine.initialize_cuda_context()
            
            assert context is not None
            assert context['status'] == 'initialized'
            assert context['devices'] == 2
            assert cuda_engine.initialized is True
            assert len(cuda_engine.device_contexts) == 2
    
    @pytest.mark.asyncio
    async def test_initialize_cuda_context_no_cuda(self, cuda_engine):
        """Test CUDA context initialization when CUDA is not available."""
        cuda_engine.cuda_info = CUDAInfo(available=False, device_count=0)
        
        context = await cuda_engine.initialize_cuda_context()
        
        assert context is None
        assert cuda_engine.initialized is False
    
    @pytest.mark.asyncio
    async def test_offload_model_inference_to_gpu_success(self, cuda_engine, mock_cuda_info):
        """Test successful GPU model inference offloading."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        cuda_engine.device_contexts = {0: {'initialized': True}, 1: {'initialized': True}}
        
        model_info = {
            'id': 'test_model',
            'weights': {'layer1': 'weights_data'},
            'size': 1000000
        }
        input_data = "test input"
        
        with patch.object(cuda_engine, '_get_cached_model_components', return_value=None):
            with patch.object(cuda_engine, 'cache_model_components_on_gpu') as mock_cache:
                with patch.object(cuda_engine, '_select_optimal_device', return_value=0):
                    with patch.object(cuda_engine, '_gpu_inference', return_value="gpu_result"):
                        result = await cuda_engine.offload_model_inference_to_gpu(model_info, input_data)
                        
                        assert result == "gpu_result"
                        mock_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_offload_model_inference_fallback_to_cpu(self, cuda_engine):
        """Test fallback to CPU when GPU inference fails."""
        cuda_engine.cuda_info = CUDAInfo(available=False, device_count=0)
        cuda_engine.initialized = False
        
        model_info = {'id': 'test_model'}
        input_data = "test input"
        
        with patch.object(cuda_engine, 'fallback_to_cpu_on_gpu_failure', return_value="cpu_result") as mock_fallback:
            result = await cuda_engine.offload_model_inference_to_gpu(model_info, input_data)
            
            assert result == "cpu_result"
            mock_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_manage_gpu_memory_allocation_success(self, cuda_engine, mock_cuda_info):
        """Test successful GPU memory allocation."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        
        required_memory = 1000000  # 1MB
        
        with patch('torch.empty') as mock_empty:
            mock_tensor = MagicMock()
            mock_empty.return_value = mock_tensor
            
            handle = await cuda_engine.manage_gpu_memory_allocation(required_memory)
            
            assert handle is not None
            assert handle.size == required_memory
            assert handle.device_id in [0, 1]  # One of the available devices
            assert handle.ptr == mock_tensor
    
    @pytest.mark.asyncio
    async def test_manage_gpu_memory_allocation_insufficient_memory(self, cuda_engine, mock_cuda_info):
        """Test GPU memory allocation when insufficient memory available."""
        # Set all devices to have insufficient memory
        for device in mock_cuda_info.devices:
            device.memory_free = 100  # Very small amount
        
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        
        required_memory = 1000000  # 1MB (more than available)
        
        with patch.object(cuda_engine, '_cleanup_gpu_cache') as mock_cleanup:
            handle = await cuda_engine.manage_gpu_memory_allocation(required_memory)
            
            assert handle is None
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_model_components_on_gpu(self, cuda_engine, mock_cuda_info):
        """Test caching model components on GPU."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        cuda_engine.device_contexts = {0: {'initialized': True}, 1: {'initialized': True}}
        
        # Create mock tensor data
        mock_tensor = MagicMock()
        mock_tensor.to.return_value = mock_tensor
        
        components = [
            ModelComponent(
                id="model1_weights",
                name="Model 1 Weights",
                data=mock_tensor,
                size=1000000
            ),
            ModelComponent(
                id="model1_bias",
                name="Model 1 Bias",
                data=mock_tensor,
                size=100000
            )
        ]
        
        with patch.object(cuda_engine, '_select_optimal_device', return_value=0):
            await cuda_engine.cache_model_components_on_gpu(components)
            
            assert len(cuda_engine.model_cache) == 2
            assert "model1_weights" in cuda_engine.model_cache
            assert "model1_bias" in cuda_engine.model_cache
            
            # Check that components were moved to GPU
            for comp_id in ["model1_weights", "model1_bias"]:
                cached_comp = cuda_engine.model_cache[comp_id]
                assert cached_comp.device_id == 0
                assert cached_comp.access_count == 1
    
    @pytest.mark.asyncio
    async def test_monitor_gpu_utilization(self, cuda_engine, mock_cuda_info):
        """Test GPU utilization monitoring."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        cuda_engine.device_contexts = {0: {'initialized': True}, 1: {'initialized': True}}
        
        # Add some inference times for throughput calculation
        cuda_engine.inference_times = [0.1, 0.15, 0.12, 0.08, 0.2]
        cuda_engine.batch_times = [0.5, 0.6, 0.4, 0.7]
        
        with patch.object(cuda_engine, '_get_device_info') as mock_get_device:
            mock_get_device.side_effect = [
                CUDADevice(0, "RTX 3080", "8.6", 10737418240, 8589934592, 2147483648, 30.0, 70.0, 250.0),
                CUDADevice(1, "RTX 3070", "8.6", 8589934592, 6442450944, 2147483648, 20.0, 65.0, 200.0)
            ]
            
            metrics = await cuda_engine.monitor_gpu_utilization()
            
            assert isinstance(metrics, GPUMetrics)
            assert metrics.utilization_percentage == 25.0  # Average of 30.0 and 20.0
            assert metrics.temperature == 67.5  # Average of 70.0 and 65.0
            assert metrics.power_usage == 225.0  # Average of 250.0 and 200.0
            assert metrics.inference_throughput > 0
            assert metrics.batch_processing_efficiency > 0
    
    @pytest.mark.asyncio
    async def test_fallback_to_cpu_on_gpu_failure(self, cuda_engine):
        """Test CPU fallback mechanism."""
        def sync_computation():
            return "cpu_result"
        
        async def async_computation():
            return "async_cpu_result"
        
        # Test synchronous computation
        result = await cuda_engine.fallback_to_cpu_on_gpu_failure(sync_computation)
        assert result == "cpu_result"
        
        # Test asynchronous computation
        result = await cuda_engine.fallback_to_cpu_on_gpu_failure(async_computation)
        assert result == "async_cpu_result"
    
    @pytest.mark.asyncio
    async def test_optimize_gpu_batch_processing_success(self, cuda_engine, mock_cuda_info):
        """Test GPU batch processing optimization."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        
        batch_requests = [
            {
                'id': 'req1',
                'input_data': 'input1',
                'model_info': {'id': 'model1'},
                'priority': 1
            },
            {
                'id': 'req2',
                'input_data': 'input2',
                'model_info': {'id': 'model1'},
                'priority': 2
            }
        ]
        
        mock_batch_responses = [
            BatchResponse('req1', 'output1', 0.1, 0.05, True),
            BatchResponse('req2', 'output2', 0.12, 0.06, True)
        ]
        
        with patch.object(cuda_engine, '_process_batch', return_value=mock_batch_responses):
            responses = await cuda_engine.optimize_gpu_batch_processing(batch_requests)
            
            assert len(responses) == 2
            assert all(resp['success'] for resp in responses)
            assert all(resp['gpu_accelerated'] for resp in responses)
            assert responses[0]['request_id'] == 'req2'  # Higher priority first
            assert responses[1]['request_id'] == 'req1'
    
    @pytest.mark.asyncio
    async def test_optimize_gpu_batch_processing_cpu_fallback(self, cuda_engine):
        """Test batch processing fallback to CPU."""
        cuda_engine.cuda_info = CUDAInfo(available=False, device_count=0)
        cuda_engine.initialized = False
        
        batch_requests = [
            {
                'id': 'req1',
                'input_data': 'input1',
                'model_info': {'id': 'model1'}
            }
        ]
        
        with patch.object(cuda_engine, 'fallback_to_cpu_on_gpu_failure', return_value="cpu_result"):
            responses = await cuda_engine.optimize_gpu_batch_processing(batch_requests)
            
            assert len(responses) == 1
            assert responses[0]['success'] is True
            assert responses[0]['gpu_accelerated'] is False
            assert responses[0]['result'] == "cpu_result"
    
    @pytest.mark.asyncio
    async def test_cleanup_gpu_cache(self, cuda_engine):
        """Test GPU cache cleanup functionality."""
        cuda_engine.initialized = True
        
        # Add some old memory handles and cached models
        old_time = time.time() - 400  # 400 seconds ago (older than 5 minutes)
        recent_time = time.time() - 100  # 100 seconds ago (recent)
        
        # Mock memory handles
        old_handle = GPUMemoryHandle(0, 1000, MagicMock())
        old_handle.last_accessed = old_time
        recent_handle = GPUMemoryHandle(1, 2000, MagicMock())
        recent_handle.last_accessed = recent_time
        
        cuda_engine.memory_handles = {
            'old_handle': old_handle,
            'recent_handle': recent_handle
        }
        
        # Mock cached models
        old_component = ModelComponent('old_model', 'Old Model', MagicMock(), 1000)
        old_component.last_used = old_time
        recent_component = ModelComponent('recent_model', 'Recent Model', MagicMock(), 2000)
        recent_component.last_used = recent_time
        
        cuda_engine.model_cache = {
            'old_model': old_component,
            'recent_model': recent_component
        }
        
        with patch('gc.collect') as mock_gc:
            with patch('torch.cuda.empty_cache') as mock_empty_cache:
                await cuda_engine._cleanup_gpu_cache()
                
                # Check that old items were removed
                assert 'old_handle' not in cuda_engine.memory_handles
                assert 'recent_handle' in cuda_engine.memory_handles
                assert 'old_model' not in cuda_engine.model_cache
                assert 'recent_model' in cuda_engine.model_cache
                
                mock_gc.assert_called_once()
                mock_empty_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_performance_summary(self, cuda_engine, mock_cuda_info):
        """Test performance summary generation."""
        cuda_engine.cuda_info = mock_cuda_info
        cuda_engine.initialized = True
        
        # Add some metrics history
        cuda_engine.metrics_history = [
            GPUMetrics(50.0, 60.0, 70.0, 200.0, 10.0, 80.0),
            GPUMetrics(45.0, 55.0, 68.0, 190.0, 12.0, 85.0),
            GPUMetrics(48.0, 58.0, 72.0, 210.0, 11.0, 82.0)
        ]
        
        # Add inference times
        cuda_engine.inference_times = [0.1, 0.15, 0.12, 0.08, 0.2]
        
        with patch.object(cuda_engine, 'monitor_gpu_utilization') as mock_monitor:
            mock_monitor.return_value = GPUMetrics(47.0, 57.0, 69.0, 195.0, 11.5, 83.0)
            
            summary = await cuda_engine.get_performance_summary()
            
            assert summary['cuda_available'] is True
            assert summary['initialized'] is True
            assert summary['device_count'] == 0  # No device contexts set up in this test
            assert 'current_metrics' in summary
            assert 'averages' in summary
            assert 'inference_stats' in summary
            
            # Check inference statistics
            inference_stats = summary['inference_stats']
            assert inference_stats['count'] == 5
            assert inference_stats['avg_time'] == 0.13  # Average of [0.1, 0.15, 0.12, 0.08, 0.2]
            assert inference_stats['min_time'] == 0.08
            assert inference_stats['max_time'] == 0.2
    
    @pytest.mark.asyncio
    async def test_shutdown(self, cuda_engine):
        """Test CUDA engine shutdown."""
        cuda_engine.initialized = True
        cuda_engine.batch_processor_running = True
        
        # Add some resources to clean up
        cuda_engine.memory_handles = {'handle1': GPUMemoryHandle(0, 1000, MagicMock())}
        cuda_engine.model_cache = {'model1': ModelComponent('model1', 'Model 1', MagicMock(), 1000)}
        
        with patch.object(cuda_engine, '_cleanup_gpu_cache') as mock_cleanup:
            with patch('torch.cuda.empty_cache') as mock_empty_cache:
                await cuda_engine.shutdown()
                
                assert cuda_engine.batch_processor_running is False
                assert cuda_engine.initialized is False
                assert len(cuda_engine.memory_handles) == 0
                assert len(cuda_engine.model_cache) == 0
                
                mock_cleanup.assert_called_once()
                mock_empty_cache.assert_called_once()


class TestCUDADataModels:
    """Test CUDA data models and structures."""
    
    def test_cuda_device_creation(self):
        """Test CUDADevice creation and properties."""
        device = CUDADevice(
            id=0,
            name="NVIDIA GeForce RTX 3080",
            compute_capability="8.6",
            memory_total=10737418240,
            memory_free=8589934592,
            memory_used=2147483648,
            utilization=25.0,
            temperature=65.0,
            power_usage=220.0
        )
        
        assert device.id == 0
        assert device.name == "NVIDIA GeForce RTX 3080"
        assert device.compute_capability == "8.6"
        assert device.memory_total == 10737418240
        assert device.utilization == 25.0
    
    def test_cuda_info_creation(self):
        """Test CUDAInfo creation and properties."""
        devices = [
            CUDADevice(0, "RTX 3080", "8.6", 10737418240, 8589934592, 2147483648, 25.0),
            CUDADevice(1, "RTX 3070", "8.6", 8589934592, 6442450944, 2147483648, 15.0)
        ]
        
        cuda_info = CUDAInfo(
            available=True,
            device_count=2,
            devices=devices,
            cuda_version="11.8",
            driver_version="525.60.11",
            total_memory=19327352832
        )
        
        assert cuda_info.available is True
        assert cuda_info.device_count == 2
        assert len(cuda_info.devices) == 2
        assert cuda_info.cuda_version == "11.8"
        assert cuda_info.total_memory == 19327352832
    
    def test_gpu_memory_handle_creation(self):
        """Test GPUMemoryHandle creation and properties."""
        handle = GPUMemoryHandle(
            device_id=0,
            size=1000000,
            ptr=MagicMock()
        )
        
        assert handle.device_id == 0
        assert handle.size == 1000000
        assert handle.ptr is not None
        assert handle.allocated_at > 0
        assert handle.last_accessed > 0
    
    def test_gpu_metrics_creation(self):
        """Test GPUMetrics creation and properties."""
        metrics = GPUMetrics(
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
        assert metrics.power_usage == 250.0
        assert metrics.inference_throughput == 15.0
        assert metrics.batch_processing_efficiency == 85.0
    
    def test_model_component_creation(self):
        """Test ModelComponent creation and properties."""
        component = ModelComponent(
            id="model1_weights",
            name="Model 1 Weights",
            data=MagicMock(),
            size=1000000,
            device_id=0
        )
        
        assert component.id == "model1_weights"
        assert component.name == "Model 1 Weights"
        assert component.size == 1000000
        assert component.device_id == 0
        assert component.last_used > 0
        assert component.access_count == 0
    
    def test_batch_request_creation(self):
        """Test BatchRequest creation and properties."""
        request = BatchRequest(
            id="req1",
            input_data="test input",
            model_id="model1",
            priority=5
        )
        
        assert request.id == "req1"
        assert request.input_data == "test input"
        assert request.model_id == "model1"
        assert request.priority == 5
        assert request.created_at > 0
    
    def test_batch_response_creation(self):
        """Test BatchResponse creation and properties."""
        response = BatchResponse(
            request_id="req1",
            output_data="test output",
            processing_time=0.15,
            gpu_time=0.08,
            success=True
        )
        
        assert response.request_id == "req1"
        assert response.output_data == "test output"
        assert response.processing_time == 0.15
        assert response.gpu_time == 0.08
        assert response.success is True
        assert response.error is None


if __name__ == "__main__":
    pytest.main([__file__])