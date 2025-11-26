"""
CUDA Acceleration Engine for GPU-accelerated model inference and optimization.

This module provides GPU CUDA acceleration capabilities for computationally intensive tasks,
including model inference offloading, GPU memory management, and performance optimization.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import gc

try:
    import torch
    import torch.cuda as cuda
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    cuda = None

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    pynvml = None

logger = logging.getLogger(__name__)


@dataclass
class CUDADevice:
    """Information about a CUDA-capable GPU device."""
    id: int
    name: str
    compute_capability: str
    memory_total: int  # in bytes
    memory_free: int   # in bytes
    memory_used: int   # in bytes
    utilization: float  # percentage
    temperature: Optional[float] = None
    power_usage: Optional[float] = None


@dataclass
class CUDAInfo:
    """Information about CUDA availability and devices."""
    available: bool
    device_count: int
    devices: List[CUDADevice] = field(default_factory=list)
    cuda_version: Optional[str] = None
    driver_version: Optional[str] = None
    total_memory: int = 0


@dataclass
class GPUMemoryHandle:
    """Handle for GPU memory allocation."""
    device_id: int
    size: int
    ptr: Optional[Any] = None
    allocated_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


@dataclass
class GPUMetrics:
    """GPU performance and utilization metrics."""
    utilization_percentage: float
    memory_usage_percentage: float
    temperature: float
    power_usage: float
    inference_throughput: float  # inferences per second
    batch_processing_efficiency: float  # percentage
    memory_bandwidth_utilization: float = 0.0
    compute_efficiency: float = 0.0


@dataclass
class ModelComponent:
    """Represents a cacheable model component."""
    id: str
    name: str
    data: Any
    size: int
    device_id: Optional[int] = None
    last_used: float = field(default_factory=time.time)
    access_count: int = 0


@dataclass
class BatchRequest:
    """Request for batch processing."""
    id: str
    input_data: Any
    model_id: str
    priority: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class BatchResponse:
    """Response from batch processing."""
    request_id: str
    output_data: Any
    processing_time: float
    gpu_time: float
    success: bool
    error: Optional[str] = None


class CUDAAccelerationEngine:
    """
    GPU CUDA acceleration engine for performance optimization.
    
    Provides GPU acceleration capabilities including:
    - CUDA device detection and initialization
    - GPU model inference offloading
    - GPU memory management
    - Model component caching on GPU
    - Performance monitoring
    - CPU fallback mechanisms
    - Batch processing optimization
    """
    
    def __init__(self, 
                 max_gpu_memory_usage: float = 0.8,
                 cache_cleanup_threshold: float = 0.9,
                 batch_timeout: float = 0.1,
                 max_batch_size: int = 32):
        """
        Initialize CUDA acceleration engine.
        
        Args:
            max_gpu_memory_usage: Maximum GPU memory usage percentage (0.0-1.0)
            cache_cleanup_threshold: Memory threshold to trigger cache cleanup
            batch_timeout: Maximum time to wait for batch completion (seconds)
            max_batch_size: Maximum number of requests in a batch
        """
        self.max_gpu_memory_usage = max_gpu_memory_usage
        self.cache_cleanup_threshold = cache_cleanup_threshold
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size
        
        self.cuda_info: Optional[CUDAInfo] = None
        self.initialized = False
        self.memory_handles: Dict[str, GPUMemoryHandle] = {}
        self.model_cache: Dict[str, ModelComponent] = {}
        self.device_contexts: Dict[int, Any] = {}
        
        # Batch processing
        self.batch_queue: queue.Queue = queue.Queue()
        self.batch_processor_running = False
        self.batch_executor = ThreadPoolExecutor(max_workers=2)
        
        # Performance tracking
        self.metrics_history: List[GPUMetrics] = []
        self.inference_times: List[float] = []
        self.batch_times: List[float] = []
        
        # Thread safety
        self.lock = threading.RLock()
        
        logger.info("CUDA Acceleration Engine initialized")
    
    async def detect_cuda_availability(self) -> CUDAInfo:
        """
        Detect CUDA availability and enumerate devices.
        
        Returns:
            CUDAInfo object with device information
        """
        logger.info("Detecting CUDA availability...")
        
        cuda_info = CUDAInfo(available=False, device_count=0)
        
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available - CUDA acceleration disabled")
            return cuda_info
        
        try:
            if not torch.cuda.is_available():
                logger.warning("CUDA not available on this system")
                return cuda_info
            
            device_count = torch.cuda.device_count()
            cuda_info.available = True
            cuda_info.device_count = device_count
            cuda_info.cuda_version = torch.version.cuda
            
            # Initialize PYNVML for detailed device info
            if PYNVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    cuda_info.driver_version = pynvml.nvmlSystemGetDriverVersion().decode()
                except Exception as e:
                    logger.warning(f"Failed to initialize PYNVML: {e}")
            
            # Enumerate devices
            total_memory = 0
            for device_id in range(device_count):
                device_info = await self._get_device_info(device_id)
                cuda_info.devices.append(device_info)
                total_memory += device_info.memory_total
            
            cuda_info.total_memory = total_memory
            
            logger.info(f"CUDA available: {device_count} devices, "
                       f"total memory: {total_memory / (1024**3):.1f} GB")
            
        except Exception as e:
            logger.error(f"Error detecting CUDA availability: {e}")
            cuda_info.available = False
        
        self.cuda_info = cuda_info
        return cuda_info
    
    async def _get_device_info(self, device_id: int) -> CUDADevice:
        """Get detailed information about a specific CUDA device."""
        try:
            with torch.cuda.device(device_id):
                props = torch.cuda.get_device_properties(device_id)
                memory_total = props.total_memory
                memory_free = torch.cuda.memory_reserved(device_id)
                memory_used = memory_total - memory_free
                
                device_info = CUDADevice(
                    id=device_id,
                    name=props.name,
                    compute_capability=f"{props.major}.{props.minor}",
                    memory_total=memory_total,
                    memory_free=memory_free,
                    memory_used=memory_used,
                    utilization=0.0  # Will be updated by monitoring
                )
                
                # Get additional info from PYNVML if available
                if PYNVML_AVAILABLE:
                    try:
                        handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        device_info.utilization = util.gpu
                        
                        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                        device_info.temperature = temp
                        
                        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                        device_info.power_usage = power
                        
                    except Exception as e:
                        logger.debug(f"Could not get extended device info: {e}")
                
                return device_info
                
        except Exception as e:
            logger.error(f"Error getting device {device_id} info: {e}")
            return CUDADevice(
                id=device_id,
                name="Unknown",
                compute_capability="0.0",
                memory_total=0,
                memory_free=0,
                memory_used=0,
                utilization=0.0
            )
    
    async def initialize_cuda_context(self) -> Optional[Dict[str, Any]]:
        """
        Initialize CUDA context and prepare for GPU operations.
        
        Returns:
            Dictionary with context information or None if initialization failed
        """
        if self.initialized:
            return {"status": "already_initialized", "devices": len(self.cuda_info.devices)}
        
        logger.info("Initializing CUDA context...")
        
        try:
            # Detect CUDA availability first
            if not self.cuda_info:
                await self.detect_cuda_availability()
            
            if not self.cuda_info.available:
                logger.warning("CUDA not available - initialization skipped")
                return None
            
            # Initialize device contexts
            for device in self.cuda_info.devices:
                try:
                    with torch.cuda.device(device.id):
                        # Create a small tensor to initialize the context
                        test_tensor = torch.zeros(1, device=f'cuda:{device.id}')
                        del test_tensor
                        torch.cuda.empty_cache()
                        
                        self.device_contexts[device.id] = {
                            'initialized': True,
                            'memory_pool': {},
                            'cached_models': {}
                        }
                        
                        logger.info(f"Initialized CUDA context for device {device.id}: {device.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to initialize device {device.id}: {e}")
                    continue
            
            # Start batch processor if we have initialized devices
            if self.device_contexts:
                await self._start_batch_processor()
                self.initialized = True
                
                logger.info(f"CUDA acceleration engine initialized with {len(self.device_contexts)} devices")
                
                return {
                    "status": "initialized",
                    "devices": len(self.device_contexts),
                    "total_memory": self.cuda_info.total_memory,
                    "cuda_version": self.cuda_info.cuda_version
                }
            else:
                logger.error("No CUDA devices could be initialized")
                return None
                
        except Exception as e:
            logger.error(f"CUDA context initialization failed: {e}")
            return None
    
    async def _start_batch_processor(self):
        """Start the batch processing background task."""
        if not self.batch_processor_running:
            self.batch_processor_running = True
            asyncio.create_task(self._batch_processor_loop())
            logger.info("Batch processor started")
    
    async def _batch_processor_loop(self):
        """Background loop for processing batched requests."""
        while self.batch_processor_running:
            try:
                batch_requests = []
                start_time = time.time()
                
                # Collect requests for batching
                while (len(batch_requests) < self.max_batch_size and 
                       (time.time() - start_time) < self.batch_timeout):
                    try:
                        request = self.batch_queue.get_nowait()
                        batch_requests.append(request)
                    except queue.Empty:
                        if batch_requests:
                            break
                        await asyncio.sleep(0.001)  # Small delay to prevent busy waiting
                
                # Process batch if we have requests
                if batch_requests:
                    await self._process_batch(batch_requests)
                
            except Exception as e:
                logger.error(f"Error in batch processor loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_batch(self, requests: List[BatchRequest]) -> List[BatchResponse]:
        """Process a batch of requests on GPU."""
        batch_start = time.time()
        responses = []
        
        try:
            # Group requests by model for efficient processing
            model_groups = {}
            for req in requests:
                if req.model_id not in model_groups:
                    model_groups[req.model_id] = []
                model_groups[req.model_id].append(req)
            
            # Process each model group
            for model_id, model_requests in model_groups.items():
                try:
                    model_responses = await self._process_model_batch(model_id, model_requests)
                    responses.extend(model_responses)
                except Exception as e:
                    logger.error(f"Error processing batch for model {model_id}: {e}")
                    # Create error responses
                    for req in model_requests:
                        responses.append(BatchResponse(
                            request_id=req.id,
                            output_data=None,
                            processing_time=0.0,
                            gpu_time=0.0,
                            success=False,
                            error=str(e)
                        ))
            
            batch_time = time.time() - batch_start
            self.batch_times.append(batch_time)
            
            # Keep only recent batch times for metrics
            if len(self.batch_times) > 1000:
                self.batch_times = self.batch_times[-500:]
            
            logger.debug(f"Processed batch of {len(requests)} requests in {batch_time:.3f}s")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Create error responses for all requests
            for req in requests:
                responses.append(BatchResponse(
                    request_id=req.id,
                    output_data=None,
                    processing_time=0.0,
                    gpu_time=0.0,
                    success=False,
                    error=str(e)
                ))
        
        return responses
    
    async def _process_model_batch(self, model_id: str, requests: List[BatchRequest]) -> List[BatchResponse]:
        """Process a batch of requests for a specific model."""
        responses = []
        
        try:
            # Select best device for this model
            device_id = await self._select_optimal_device(model_id)
            if device_id is None:
                raise RuntimeError("No suitable GPU device available")
            
            # Process requests on selected device
            with torch.cuda.device(device_id):
                for req in requests:
                    start_time = time.time()
                    gpu_start = time.time()
                    
                    try:
                        # Simulate GPU processing (replace with actual model inference)
                        output = await self._gpu_inference(req.input_data, model_id, device_id)
                        
                        gpu_time = time.time() - gpu_start
                        total_time = time.time() - start_time
                        
                        responses.append(BatchResponse(
                            request_id=req.id,
                            output_data=output,
                            processing_time=total_time,
                            gpu_time=gpu_time,
                            success=True
                        ))
                        
                        self.inference_times.append(total_time)
                        
                    except Exception as e:
                        logger.error(f"GPU inference failed for request {req.id}: {e}")
                        responses.append(BatchResponse(
                            request_id=req.id,
                            output_data=None,
                            processing_time=time.time() - start_time,
                            gpu_time=0.0,
                            success=False,
                            error=str(e)
                        ))
            
            # Keep only recent inference times for metrics
            if len(self.inference_times) > 1000:
                self.inference_times = self.inference_times[-500:]
                
        except Exception as e:
            logger.error(f"Model batch processing failed: {e}")
            for req in requests:
                responses.append(BatchResponse(
                    request_id=req.id,
                    output_data=None,
                    processing_time=0.0,
                    gpu_time=0.0,
                    success=False,
                    error=str(e)
                ))
        
        return responses
    
    async def _gpu_inference(self, input_data: Any, model_id: str, device_id: int) -> Any:
        """Perform GPU inference for given input data."""
        # This is a placeholder for actual GPU model inference
        # In a real implementation, this would:
        # 1. Load model components to GPU if not cached
        # 2. Transfer input data to GPU
        # 3. Run inference
        # 4. Transfer results back to CPU
        
        # Simulate GPU computation
        await asyncio.sleep(0.001)  # Simulate processing time
        
        # For now, return a simple processed result
        return f"GPU_processed_{model_id}_{input_data}"
    
    async def _select_optimal_device(self, model_id: str) -> Optional[int]:
        """Select the optimal GPU device for a given model."""
        if not self.device_contexts:
            return None
        
        # Simple selection based on available memory
        best_device = None
        max_free_memory = 0
        
        for device_id in self.device_contexts.keys():
            try:
                with torch.cuda.device(device_id):
                    free_memory = torch.cuda.memory_reserved(device_id)
                    if free_memory > max_free_memory:
                        max_free_memory = free_memory
                        best_device = device_id
            except Exception as e:
                logger.debug(f"Could not check memory for device {device_id}: {e}")
                continue
        
        return best_device
    
    async def offload_model_inference_to_gpu(self, model_info: Dict[str, Any], input_data: Any) -> Any:
        """
        Offload model inference to GPU for computationally intensive tasks.
        
        Args:
            model_info: Dictionary containing model information and configuration
            input_data: Input data for inference
            
        Returns:
            Inference results or None if GPU processing failed
        """
        if not self.initialized or not self.cuda_info.available:
            logger.debug("GPU not available, falling back to CPU")
            return await self._cpu_inference(model_info, input_data)
        
        try:
            model_id = model_info.get('id', 'unknown')
            
            # Check if model components are cached on GPU
            cached_model = await self._get_cached_model_components(model_id)
            if not cached_model:
                # Load model components to GPU
                await self.cache_model_components_on_gpu([
                    ModelComponent(
                        id=f"{model_id}_weights",
                        name=f"{model_id} weights",
                        data=model_info.get('weights', {}),
                        size=model_info.get('size', 0)
                    )
                ])
            
            # Select optimal device
            device_id = await self._select_optimal_device(model_id)
            if device_id is None:
                raise RuntimeError("No suitable GPU device available")
            
            # Perform GPU inference
            start_time = time.time()
            result = await self._gpu_inference(input_data, model_id, device_id)
            inference_time = time.time() - start_time
            
            # Update performance metrics
            self.inference_times.append(inference_time)
            
            logger.debug(f"GPU inference completed in {inference_time:.3f}s for model {model_id}")
            return result
            
        except Exception as e:
            logger.error(f"GPU inference failed: {e}")
            # Fallback to CPU
            return await self._cpu_inference(model_info, input_data)
    
    async def _cpu_inference(self, model_info: Dict[str, Any], input_data: Any) -> Any:
        """Fallback CPU inference implementation."""
        # Placeholder for CPU inference
        model_id = model_info.get('id', 'unknown')
        await asyncio.sleep(0.01)  # Simulate CPU processing time
        return f"CPU_processed_{model_id}_{input_data}"
    
    async def manage_gpu_memory_allocation(self, required_memory: int) -> Optional[GPUMemoryHandle]:
        """
        Manage GPU memory allocation with efficient allocation and deallocation.
        
        Args:
            required_memory: Required memory size in bytes
            
        Returns:
            GPUMemoryHandle if allocation successful, None otherwise
        """
        if not self.initialized or not self.cuda_info.available:
            logger.debug("GPU not available for memory allocation")
            return None
        
        try:
            with self.lock:
                # Find device with sufficient free memory
                target_device = None
                for device in self.cuda_info.devices:
                    if device.memory_free >= required_memory:
                        target_device = device
                        break
                
                if not target_device:
                    # Try to free up memory by cleaning cache
                    await self._cleanup_gpu_cache()
                    
                    # Check again after cleanup
                    for device in self.cuda_info.devices:
                        if device.memory_free >= required_memory:
                            target_device = device
                            break
                
                if not target_device:
                    logger.warning(f"Insufficient GPU memory for allocation: {required_memory} bytes")
                    return None
                
                # Allocate memory on target device
                with torch.cuda.device(target_device.id):
                    try:
                        # Allocate tensor as memory handle
                        memory_tensor = torch.empty(
                            required_memory // 4,  # Assuming float32 (4 bytes per element)
                            dtype=torch.float32,
                            device=f'cuda:{target_device.id}'
                        )
                        
                        handle = GPUMemoryHandle(
                            device_id=target_device.id,
                            size=required_memory,
                            ptr=memory_tensor
                        )
                        
                        # Store handle for tracking
                        handle_id = f"mem_{target_device.id}_{int(time.time() * 1000000)}"
                        self.memory_handles[handle_id] = handle
                        
                        # Update device memory info
                        target_device.memory_free -= required_memory
                        target_device.memory_used += required_memory
                        
                        logger.debug(f"Allocated {required_memory} bytes on GPU {target_device.id}")
                        return handle
                        
                    except torch.cuda.OutOfMemoryError:
                        logger.error(f"GPU out of memory on device {target_device.id}")
                        return None
                    
        except Exception as e:
            logger.error(f"GPU memory allocation failed: {e}")
            return None
    
    async def _cleanup_gpu_cache(self):
        """Clean up GPU cache to free memory."""
        try:
            with self.lock:
                current_time = time.time()
                
                # Remove old memory handles
                expired_handles = []
                for handle_id, handle in self.memory_handles.items():
                    # Remove handles not accessed in last 5 minutes
                    if current_time - handle.last_accessed > 300:
                        expired_handles.append(handle_id)
                
                for handle_id in expired_handles:
                    handle = self.memory_handles.pop(handle_id)
                    if handle.ptr is not None:
                        del handle.ptr
                    logger.debug(f"Cleaned up expired memory handle {handle_id}")
                
                # Remove old cached models
                expired_models = []
                for model_id, component in self.model_cache.items():
                    if current_time - component.last_used > 600:  # 10 minutes
                        expired_models.append(model_id)
                
                for model_id in expired_models:
                    component = self.model_cache.pop(model_id)
                    if hasattr(component.data, 'cpu'):
                        component.data = component.data.cpu()
                    logger.debug(f"Moved cached model {model_id} to CPU")
                
                # Force garbage collection and clear CUDA cache
                gc.collect()
                if torch and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                logger.debug("GPU cache cleanup completed")
                
        except Exception as e:
            logger.error(f"GPU cache cleanup failed: {e}")
    
    async def cache_model_components_on_gpu(self, components: List[ModelComponent]) -> None:
        """
        Cache frequently used model components in GPU memory for faster access.
        
        Args:
            components: List of model components to cache
        """
        if not self.initialized or not self.cuda_info.available:
            logger.debug("GPU not available for model caching")
            return
        
        try:
            with self.lock:
                for component in components:
                    # Check if already cached
                    if component.id in self.model_cache:
                        # Update access time
                        self.model_cache[component.id].last_used = time.time()
                        self.model_cache[component.id].access_count += 1
                        continue
                    
                    # Select device for caching
                    device_id = await self._select_optimal_device(component.id)
                    if device_id is None:
                        logger.warning(f"No suitable device for caching component {component.id}")
                        continue
                    
                    try:
                        with torch.cuda.device(device_id):
                            # Move component data to GPU if it's a tensor
                            if hasattr(component.data, 'to'):
                                gpu_data = component.data.to(f'cuda:{device_id}')
                            else:
                                # For non-tensor data, create a placeholder
                                gpu_data = component.data
                            
                            # Create cached component
                            cached_component = ModelComponent(
                                id=component.id,
                                name=component.name,
                                data=gpu_data,
                                size=component.size,
                                device_id=device_id,
                                last_used=time.time(),
                                access_count=1
                            )
                            
                            self.model_cache[component.id] = cached_component
                            
                            logger.debug(f"Cached model component {component.id} on GPU {device_id}")
                            
                    except Exception as e:
                        logger.error(f"Failed to cache component {component.id}: {e}")
                        continue
                
                # Check if we need to clean up cache due to memory pressure
                total_cached_size = sum(comp.size for comp in self.model_cache.values())
                if total_cached_size > self.cuda_info.total_memory * self.cache_cleanup_threshold:
                    await self._cleanup_gpu_cache()
                    
        except Exception as e:
            logger.error(f"Model component caching failed: {e}")
    
    async def _get_cached_model_components(self, model_id: str) -> Optional[ModelComponent]:
        """Get cached model components for a given model."""
        with self.lock:
            for comp_id, component in self.model_cache.items():
                if model_id in comp_id:
                    component.last_used = time.time()
                    component.access_count += 1
                    return component
        return None
    
    async def monitor_gpu_utilization(self) -> GPUMetrics:
        """
        Monitor GPU utilization and collect performance metrics.
        
        Returns:
            GPUMetrics object with current utilization data
        """
        if not self.initialized or not self.cuda_info.available:
            return GPUMetrics(
                utilization_percentage=0.0,
                memory_usage_percentage=0.0,
                temperature=0.0,
                power_usage=0.0,
                inference_throughput=0.0,
                batch_processing_efficiency=0.0
            )
        
        try:
            # Calculate average metrics across all devices
            total_utilization = 0.0
            total_memory_usage = 0.0
            total_temperature = 0.0
            total_power = 0.0
            device_count = 0
            
            for device in self.cuda_info.devices:
                if device.id in self.device_contexts:
                    # Update device info
                    updated_device = await self._get_device_info(device.id)
                    
                    total_utilization += updated_device.utilization
                    memory_usage_pct = (updated_device.memory_used / updated_device.memory_total) * 100
                    total_memory_usage += memory_usage_pct
                    
                    if updated_device.temperature:
                        total_temperature += updated_device.temperature
                    if updated_device.power_usage:
                        total_power += updated_device.power_usage
                    
                    device_count += 1
            
            # Calculate throughput metrics
            inference_throughput = 0.0
            if self.inference_times:
                recent_times = self.inference_times[-100:]  # Last 100 inferences
                avg_time = sum(recent_times) / len(recent_times)
                inference_throughput = 1.0 / avg_time if avg_time > 0 else 0.0
            
            # Calculate batch processing efficiency
            batch_efficiency = 0.0
            if self.batch_times:
                recent_batch_times = self.batch_times[-50:]  # Last 50 batches
                avg_batch_time = sum(recent_batch_times) / len(recent_batch_times)
                # Efficiency based on how well we utilize batch processing
                batch_efficiency = min(100.0, (self.max_batch_size / max(1, avg_batch_time)) * 10)
            
            metrics = GPUMetrics(
                utilization_percentage=total_utilization / max(1, device_count),
                memory_usage_percentage=total_memory_usage / max(1, device_count),
                temperature=total_temperature / max(1, device_count),
                power_usage=total_power / max(1, device_count),
                inference_throughput=inference_throughput,
                batch_processing_efficiency=batch_efficiency
            )
            
            # Store metrics history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-500:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"GPU monitoring failed: {e}")
            return GPUMetrics(
                utilization_percentage=0.0,
                memory_usage_percentage=0.0,
                temperature=0.0,
                power_usage=0.0,
                inference_throughput=0.0,
                batch_processing_efficiency=0.0
            )
    
    async def fallback_to_cpu_on_gpu_failure(self, computation: Callable) -> Any:
        """
        Implement seamless CPU fallback when GPU resources are unavailable.
        
        Args:
            computation: Function to execute on CPU as fallback
            
        Returns:
            Result of CPU computation
        """
        try:
            logger.debug("Executing CPU fallback computation")
            
            # If computation is a coroutine function, await it
            if asyncio.iscoroutinefunction(computation):
                result = await computation()
            else:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(self.batch_executor, computation)
            
            logger.debug("CPU fallback computation completed")
            return result
            
        except Exception as e:
            logger.error(f"CPU fallback computation failed: {e}")
            raise
    
    async def optimize_gpu_batch_processing(self, batch_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize batch processing for multiple concurrent GPU requests.
        
        Args:
            batch_requests: List of request dictionaries
            
        Returns:
            List of response dictionaries
        """
        if not self.initialized or not self.cuda_info.available:
            logger.debug("GPU not available, processing requests individually on CPU")
            responses = []
            for req in batch_requests:
                try:
                    result = await self._cpu_inference(req.get('model_info', {}), req.get('input_data'))
                    responses.append({
                        'request_id': req.get('id', 'unknown'),
                        'result': result,
                        'success': True,
                        'processing_time': 0.01,  # Estimated CPU time
                        'gpu_accelerated': False
                    })
                except Exception as e:
                    responses.append({
                        'request_id': req.get('id', 'unknown'),
                        'result': None,
                        'success': False,
                        'error': str(e),
                        'processing_time': 0.0,
                        'gpu_accelerated': False
                    })
            return responses
        
        try:
            # Convert to BatchRequest objects
            batch_reqs = []
            for i, req in enumerate(batch_requests):
                batch_req = BatchRequest(
                    id=req.get('id', f'batch_req_{i}'),
                    input_data=req.get('input_data'),
                    model_id=req.get('model_info', {}).get('id', 'unknown'),
                    priority=req.get('priority', 0)
                )
                batch_reqs.append(batch_req)
            
            # Sort by priority (higher priority first)
            batch_reqs.sort(key=lambda x: x.priority, reverse=True)
            
            # Process batch
            batch_responses = await self._process_batch(batch_reqs)
            
            # Convert back to dictionary format
            responses = []
            for batch_resp in batch_responses:
                responses.append({
                    'request_id': batch_resp.request_id,
                    'result': batch_resp.output_data,
                    'success': batch_resp.success,
                    'error': batch_resp.error,
                    'processing_time': batch_resp.processing_time,
                    'gpu_time': batch_resp.gpu_time,
                    'gpu_accelerated': True
                })
            
            logger.debug(f"Processed batch of {len(batch_requests)} requests")
            return responses
            
        except Exception as e:
            logger.error(f"Batch processing optimization failed: {e}")
            # Return error responses
            return [{
                'request_id': req.get('id', 'unknown'),
                'result': None,
                'success': False,
                'error': str(e),
                'processing_time': 0.0,
                'gpu_accelerated': False
            } for req in batch_requests]
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        try:
            current_metrics = await self.monitor_gpu_utilization()
            
            # Calculate averages from history
            avg_utilization = 0.0
            avg_memory_usage = 0.0
            avg_temperature = 0.0
            
            if self.metrics_history:
                recent_metrics = self.metrics_history[-100:]  # Last 100 measurements
                avg_utilization = sum(m.utilization_percentage for m in recent_metrics) / len(recent_metrics)
                avg_memory_usage = sum(m.memory_usage_percentage for m in recent_metrics) / len(recent_metrics)
                avg_temperature = sum(m.temperature for m in recent_metrics) / len(recent_metrics)
            
            # Calculate inference statistics
            inference_stats = {}
            if self.inference_times:
                recent_times = self.inference_times[-1000:]
                inference_stats = {
                    'count': len(recent_times),
                    'avg_time': sum(recent_times) / len(recent_times),
                    'min_time': min(recent_times),
                    'max_time': max(recent_times),
                    'throughput': len(recent_times) / sum(recent_times) if sum(recent_times) > 0 else 0
                }
            
            return {
                'cuda_available': self.cuda_info.available if self.cuda_info else False,
                'initialized': self.initialized,
                'device_count': len(self.device_contexts),
                'current_metrics': {
                    'utilization': current_metrics.utilization_percentage,
                    'memory_usage': current_metrics.memory_usage_percentage,
                    'temperature': current_metrics.temperature,
                    'power_usage': current_metrics.power_usage,
                    'inference_throughput': current_metrics.inference_throughput,
                    'batch_efficiency': current_metrics.batch_processing_efficiency
                },
                'averages': {
                    'utilization': avg_utilization,
                    'memory_usage': avg_memory_usage,
                    'temperature': avg_temperature
                },
                'inference_stats': inference_stats,
                'cached_models': len(self.model_cache),
                'memory_handles': len(self.memory_handles),
                'batch_queue_size': self.batch_queue.qsize()
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {
                'cuda_available': False,
                'initialized': False,
                'error': str(e)
            }
    
    async def shutdown(self):
        """Shutdown CUDA acceleration engine and clean up resources."""
        logger.info("Shutting down CUDA acceleration engine...")
        
        try:
            # Stop batch processor
            self.batch_processor_running = False
            
            # Clean up GPU cache
            await self._cleanup_gpu_cache()
            
            # Clear memory handles
            with self.lock:
                for handle in self.memory_handles.values():
                    if handle.ptr is not None:
                        del handle.ptr
                self.memory_handles.clear()
                
                # Clear model cache
                for component in self.model_cache.values():
                    if hasattr(component.data, 'cpu'):
                        component.data = component.data.cpu()
                self.model_cache.clear()
            
            # Clear CUDA cache
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Shutdown thread pool
            self.batch_executor.shutdown(wait=True)
            
            self.initialized = False
            logger.info("CUDA acceleration engine shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during CUDA engine shutdown: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        if self.initialized:
            # Note: Can't use async in __del__, so we do basic cleanup
            try:
                self.batch_processor_running = False
                if hasattr(self, 'batch_executor'):
                    self.batch_executor.shutdown(wait=False)
            except Exception:
                pass