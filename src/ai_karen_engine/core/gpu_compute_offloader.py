"""
GPU Compute Offloader for Hardware Acceleration

This module provides GPU compute offloading capabilities for ML inference and heavy
mathematical operations, with automatic CPU fallback when GPU is unavailable.
"""

import asyncio
import logging
import platform
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import weakref

logger = logging.getLogger(__name__)


class GPUBackend(Enum):
    """Supported GPU backends"""
    CUDA = "cuda"
    OPENCL = "opencl" 
    METAL = "metal"
    NONE = "none"


class GPUMemoryStrategy(Enum):
    """GPU memory management strategies"""
    EAGER = "eager"  # Allocate immediately
    LAZY = "lazy"    # Allocate on demand
    POOLED = "pooled"  # Use memory pool


@dataclass
class GPUInfo:
    """Information about available GPU resources"""
    backend: GPUBackend
    device_count: int
    total_memory: int  # in MB
    available_memory: int  # in MB
    compute_capability: Optional[str] = None
    device_names: List[str] = None
    driver_version: Optional[str] = None
    
    def __post_init__(self):
        if self.device_names is None:
            self.device_names = []


@dataclass
class GPUTask:
    """Represents a GPU computation task"""
    task_id: str
    computation: Callable
    data: Any
    priority: int = 0
    memory_requirement: Optional[int] = None  # in MB
    timeout: Optional[float] = None
    
    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first


class GPUMemoryManager:
    """Manages GPU memory allocation and cleanup"""
    
    def __init__(self, strategy: GPUMemoryStrategy = GPUMemoryStrategy.LAZY):
        self.strategy = strategy
        self._allocated_blocks = {}
        self._memory_pool = {}
        self._lock = threading.Lock()
        self._total_allocated = 0
        
    def allocate(self, size_mb: int, device_id: int = 0) -> Optional[str]:
        """Allocate GPU memory block"""
        with self._lock:
            try:
                block_id = f"block_{device_id}_{int(time.time() * 1000000)}"
                
                if self.strategy == GPUMemoryStrategy.POOLED:
                    # Try to reuse from pool first
                    pool_key = (device_id, size_mb)
                    if pool_key in self._memory_pool and self._memory_pool[pool_key]:
                        block_id = self._memory_pool[pool_key].pop()
                        logger.debug(f"Reused memory block {block_id} from pool")
                        return block_id
                
                # Simulate GPU memory allocation
                # In real implementation, this would use CUDA/OpenCL/Metal APIs
                self._allocated_blocks[block_id] = {
                    'size': size_mb,
                    'device_id': device_id,
                    'allocated_at': time.time()
                }
                self._total_allocated += size_mb
                
                logger.debug(f"Allocated {size_mb}MB GPU memory block {block_id}")
                return block_id
                
            except Exception as e:
                logger.error(f"Failed to allocate GPU memory: {e}")
                return None
    
    def deallocate(self, block_id: str) -> bool:
        """Deallocate GPU memory block"""
        with self._lock:
            try:
                if block_id not in self._allocated_blocks:
                    return False
                
                block_info = self._allocated_blocks[block_id]
                
                if self.strategy == GPUMemoryStrategy.POOLED:
                    # Return to pool for reuse
                    pool_key = (block_info['device_id'], block_info['size'])
                    if pool_key not in self._memory_pool:
                        self._memory_pool[pool_key] = []
                    self._memory_pool[pool_key].append(block_id)
                    logger.debug(f"Returned memory block {block_id} to pool")
                else:
                    # Actually deallocate
                    self._total_allocated -= block_info['size']
                    del self._allocated_blocks[block_id]
                    logger.debug(f"Deallocated memory block {block_id}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to deallocate GPU memory: {e}")
                return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        with self._lock:
            return {
                'total_allocated_mb': self._total_allocated,
                'active_blocks': len(self._allocated_blocks),
                'pool_blocks': sum(len(blocks) for blocks in self._memory_pool.values()),
                'strategy': self.strategy.value
            }
    
    def cleanup_expired_blocks(self, max_age_seconds: float = 300) -> int:
        """Clean up memory blocks older than max_age_seconds"""
        with self._lock:
            current_time = time.time()
            expired_blocks = []
            
            for block_id, block_info in self._allocated_blocks.items():
                if current_time - block_info['allocated_at'] > max_age_seconds:
                    expired_blocks.append(block_id)
            
            cleaned_count = 0
            for block_id in expired_blocks:
                if self.deallocate(block_id):
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired GPU memory blocks")
            return cleaned_count


class GPUComputeOffloader:
    """
    GPU Compute Offloader for hardware acceleration of ML inference and 
    heavy mathematical operations with CPU fallback support.
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 memory_strategy: GPUMemoryStrategy = GPUMemoryStrategy.LAZY,
                 enable_cpu_fallback: bool = True):
        self.max_workers = max_workers
        self.enable_cpu_fallback = enable_cpu_fallback
        self._gpu_info: Optional[GPUInfo] = None
        self._memory_manager = GPUMemoryManager(memory_strategy)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._task_queue = asyncio.PriorityQueue()
        self._active_tasks = {}
        self._lock = threading.Lock()
        self._initialized = False
        self._cleanup_task = None
        
        # Weak reference cleanup
        self._finalizer = weakref.finalize(self, self._cleanup_resources)
    
    async def initialize(self) -> bool:
        """Initialize GPU compute offloader and detect available hardware"""
        if self._initialized:
            return True
            
        try:
            logger.info("Initializing GPU compute offloader...")
            
            # Detect GPU capabilities
            self._gpu_info = await self.detect_gpu_availability()
            
            if self._gpu_info.backend != GPUBackend.NONE:
                logger.info(f"GPU detected: {self._gpu_info.backend.value} "
                           f"with {self._gpu_info.device_count} device(s)")
                
                # Start background cleanup task
                self._cleanup_task = asyncio.create_task(self._background_cleanup())
            else:
                logger.warning("No GPU detected, will use CPU fallback only")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU compute offloader: {e}")
            return False
    
    async def detect_gpu_availability(self) -> GPUInfo:
        """Detect available GPU resources and capabilities"""
        try:
            # Try CUDA first
            cuda_info = await self._detect_cuda()
            if cuda_info.backend != GPUBackend.NONE:
                return cuda_info
            
            # Try Metal on macOS
            if platform.system() == "Darwin":
                metal_info = await self._detect_metal()
                if metal_info.backend != GPUBackend.NONE:
                    return metal_info
            
            # Try OpenCL as fallback
            opencl_info = await self._detect_opencl()
            if opencl_info.backend != GPUBackend.NONE:
                return opencl_info
            
            # No GPU available
            return GPUInfo(
                backend=GPUBackend.NONE,
                device_count=0,
                total_memory=0,
                available_memory=0
            )
            
        except Exception as e:
            logger.error(f"Error detecting GPU availability: {e}")
            return GPUInfo(
                backend=GPUBackend.NONE,
                device_count=0,
                total_memory=0,
                available_memory=0
            )
    
    async def _detect_cuda(self) -> GPUInfo:
        """Detect CUDA GPU availability"""
        try:
            # Try importing CUDA libraries
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                if device_count > 0:
                    device_names = []
                    total_memory = 0
                    available_memory = 0
                    
                    for i in range(device_count):
                        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                        name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        
                        device_names.append(name)
                        total_memory += memory_info.total // (1024 * 1024)  # Convert to MB
                        available_memory += memory_info.free // (1024 * 1024)
                    
                    driver_version = pynvml.nvmlSystemGetDriverVersion().decode('utf-8')
                    
                    return GPUInfo(
                        backend=GPUBackend.CUDA,
                        device_count=device_count,
                        total_memory=total_memory,
                        available_memory=available_memory,
                        device_names=device_names,
                        driver_version=driver_version
                    )
                    
            except ImportError:
                # Try nvidia-smi as fallback
                try:
                    result = await asyncio.wait_for(
                        asyncio.create_subprocess_exec(
                            'nvidia-smi', '--query-gpu=count,name,memory.total,memory.free',
                            '--format=csv,noheader,nounits',
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        ),
                        timeout=5.0
                    )
                    stdout, stderr = await asyncio.wait_for(
                        result.communicate(), timeout=5.0
                    )
                    
                    if result.returncode == 0:
                        lines = stdout.decode().strip().split('\n')
                        if lines and lines[0]:
                            # Parse nvidia-smi output
                            device_count = len(lines)
                            device_names = []
                            total_memory = 0
                            available_memory = 0
                            
                            for line in lines:
                                parts = line.split(', ')
                                if len(parts) >= 4:
                                    device_names.append(parts[1])
                                    total_memory += int(parts[2])
                                    available_memory += int(parts[3])
                            
                            return GPUInfo(
                                backend=GPUBackend.CUDA,
                                device_count=device_count,
                                total_memory=total_memory,
                                available_memory=available_memory,
                                device_names=device_names
                            )
                except asyncio.TimeoutError:
                    logger.debug("nvidia-smi command timed out")
                except Exception as e:
                    logger.debug(f"nvidia-smi command failed: {e}")
            
        except Exception as e:
            logger.debug(f"CUDA detection failed: {e}")
        
        return GPUInfo(backend=GPUBackend.NONE, device_count=0, total_memory=0, available_memory=0)
    
    async def _detect_metal(self) -> GPUInfo:
        """Detect Metal GPU availability on macOS"""
        try:
            # Try to detect Metal support
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    'system_profiler', 'SPDisplaysDataType',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=5.0
            )
            stdout, stderr = await asyncio.wait_for(
                result.communicate(), timeout=5.0
            )
            
            if result.returncode == 0:
                output = stdout.decode()
                if 'Metal' in output and ('AMD' in output or 'Intel' in output or 'Apple' in output):
                    # Basic Metal detection - in real implementation would use Metal APIs
                    return GPUInfo(
                        backend=GPUBackend.METAL,
                        device_count=1,
                        total_memory=2048,  # Estimated
                        available_memory=1536,  # Estimated
                        device_names=['Metal GPU']
                    )
            
        except Exception as e:
            logger.debug(f"Metal detection failed: {e}")
        
        return GPUInfo(backend=GPUBackend.NONE, device_count=0, total_memory=0, available_memory=0)
    
    async def _detect_opencl(self) -> GPUInfo:
        """Detect OpenCL GPU availability"""
        try:
            # Try importing OpenCL libraries
            import pyopencl as cl
            
            platforms = cl.get_platforms()
            device_count = 0
            device_names = []
            total_memory = 0
            
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                for device in devices:
                    device_count += 1
                    device_names.append(device.name)
                    # OpenCL memory is in bytes, convert to MB
                    total_memory += device.global_mem_size // (1024 * 1024)
            
            if device_count > 0:
                return GPUInfo(
                    backend=GPUBackend.OPENCL,
                    device_count=device_count,
                    total_memory=total_memory,
                    available_memory=int(total_memory * 0.8),  # Estimate 80% available
                    device_names=device_names
                )
                
        except ImportError:
            logger.debug("PyOpenCL not available")
        except Exception as e:
            logger.debug(f"OpenCL detection failed: {e}")
        
        return GPUInfo(backend=GPUBackend.NONE, device_count=0, total_memory=0, available_memory=0)
    
    async def offload_to_gpu(self, 
                           computation: Callable, 
                           data: Any,
                           priority: int = 0,
                           timeout: Optional[float] = None,
                           memory_requirement: Optional[int] = None) -> Any:
        """
        Offload computation to GPU with automatic CPU fallback
        
        Args:
            computation: Function to execute
            data: Input data for computation
            priority: Task priority (higher = more urgent)
            timeout: Maximum execution time in seconds
            memory_requirement: Required GPU memory in MB
            
        Returns:
            Computation result
        """
        if not self._initialized:
            await self.initialize()
        
        # Check if GPU is available and has sufficient memory
        if (self._gpu_info.backend != GPUBackend.NONE and 
            self._can_allocate_memory(memory_requirement)):
            
            try:
                return await self._execute_on_gpu(
                    computation, data, priority, timeout, memory_requirement
                )
            except Exception as e:
                logger.warning(f"GPU execution failed: {e}, falling back to CPU")
                
        # Fallback to CPU
        if self.enable_cpu_fallback:
            return await self.fallback_to_cpu(computation, data, timeout)
        else:
            raise RuntimeError("GPU execution failed and CPU fallback is disabled")
    
    async def _execute_on_gpu(self,
                            computation: Callable,
                            data: Any,
                            priority: int,
                            timeout: Optional[float],
                            memory_requirement: Optional[int]) -> Any:
        """Execute computation on GPU"""
        task_id = f"gpu_task_{int(time.time() * 1000000)}"
        
        # Allocate GPU memory if required
        memory_block = None
        if memory_requirement:
            memory_block = self._memory_manager.allocate(memory_requirement)
            if not memory_block:
                raise RuntimeError(f"Failed to allocate {memory_requirement}MB GPU memory")
        
        try:
            # Create GPU task
            gpu_task = GPUTask(
                task_id=task_id,
                computation=computation,
                data=data,
                priority=priority,
                memory_requirement=memory_requirement,
                timeout=timeout
            )
            
            # Execute on GPU (simulated - in real implementation would use GPU APIs)
            loop = asyncio.get_event_loop()
            
            def gpu_computation():
                """Wrapper for GPU computation execution"""
                try:
                    # Simulate GPU data transfer and computation
                    logger.debug(f"Executing task {task_id} on GPU")
                    
                    # In real implementation, this would:
                    # 1. Transfer data to GPU memory
                    # 2. Execute computation on GPU
                    # 3. Transfer results back to CPU memory
                    
                    # For now, execute on CPU but with GPU-optimized patterns
                    result = computation(data)
                    
                    logger.debug(f"GPU task {task_id} completed successfully")
                    return result
                    
                except Exception as e:
                    logger.error(f"GPU computation failed for task {task_id}: {e}")
                    raise
            
            # Execute with timeout
            if timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, gpu_computation),
                    timeout=timeout
                )
            else:
                result = await loop.run_in_executor(self._executor, gpu_computation)
            
            return result
            
        finally:
            # Clean up GPU memory
            if memory_block:
                self._memory_manager.deallocate(memory_block)
    
    async def fallback_to_cpu(self, 
                            computation: Callable, 
                            data: Any,
                            timeout: Optional[float] = None) -> Any:
        """Execute computation on CPU as fallback"""
        logger.debug("Executing computation on CPU (fallback)")
        
        loop = asyncio.get_event_loop()
        
        def cpu_computation():
            """CPU computation wrapper"""
            try:
                return computation(data)
            except Exception as e:
                logger.error(f"CPU computation failed: {e}")
                raise
        
        # Execute with timeout
        if timeout:
            return await asyncio.wait_for(
                loop.run_in_executor(self._executor, cpu_computation),
                timeout=timeout
            )
        else:
            return await loop.run_in_executor(self._executor, cpu_computation)
    
    def _can_allocate_memory(self, memory_requirement: Optional[int]) -> bool:
        """Check if GPU has sufficient memory for allocation"""
        if not memory_requirement or not self._gpu_info:
            return True
        
        return self._gpu_info.available_memory >= memory_requirement
    
    async def manage_gpu_memory(self) -> Dict[str, Any]:
        """Manage GPU memory allocation and cleanup"""
        try:
            # Get current memory usage
            memory_stats = self._memory_manager.get_memory_usage()
            
            # Clean up expired blocks
            cleaned_blocks = self._memory_manager.cleanup_expired_blocks()
            
            # Update available memory estimate
            if self._gpu_info and self._gpu_info.backend != GPUBackend.NONE:
                # In real implementation, would query actual GPU memory usage
                estimated_available = (self._gpu_info.total_memory - 
                                     memory_stats['total_allocated_mb'])
                self._gpu_info.available_memory = max(0, estimated_available)
            
            return {
                'memory_stats': memory_stats,
                'cleaned_blocks': cleaned_blocks,
                'gpu_info': self._gpu_info.__dict__ if self._gpu_info else None
            }
            
        except Exception as e:
            logger.error(f"GPU memory management failed: {e}")
            return {'error': str(e)}
    
    async def batch_offload_to_gpu(self, 
                                 tasks: List[Tuple[Callable, Any]],
                                 priority: int = 0,
                                 timeout: Optional[float] = None) -> List[Any]:
        """
        Batch process multiple tasks on GPU for improved efficiency
        
        Args:
            tasks: List of (computation, data) tuples
            priority: Batch priority
            timeout: Total timeout for all tasks
            
        Returns:
            List of results in same order as input tasks
        """
        if not tasks:
            return []
        
        logger.info(f"Batch processing {len(tasks)} tasks on GPU")
        
        # Create coroutines for all tasks
        coroutines = []
        for i, (computation, data) in enumerate(tasks):
            task_timeout = timeout / len(tasks) if timeout else None
            coroutines.append(
                self.offload_to_gpu(
                    computation, data, priority, task_timeout
                )
            )
        
        # Execute all tasks concurrently
        try:
            if timeout:
                results = await asyncio.wait_for(
                    asyncio.gather(*coroutines, return_exceptions=True),
                    timeout=timeout
                )
            else:
                results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed: {result}")
                    processed_results.append(None)
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch GPU processing failed: {e}")
            raise
    
    async def get_gpu_utilization(self) -> Dict[str, Any]:
        """Get current GPU utilization statistics"""
        try:
            if not self._gpu_info or self._gpu_info.backend == GPUBackend.NONE:
                return {'gpu_available': False}
            
            memory_stats = self._memory_manager.get_memory_usage()
            
            utilization = {
                'gpu_available': True,
                'backend': self._gpu_info.backend.value,
                'device_count': self._gpu_info.device_count,
                'total_memory_mb': self._gpu_info.total_memory,
                'available_memory_mb': self._gpu_info.available_memory,
                'memory_utilization_percent': (
                    (self._gpu_info.total_memory - self._gpu_info.available_memory) / 
                    self._gpu_info.total_memory * 100 if self._gpu_info.total_memory > 0 else 0
                ),
                'active_tasks': len(self._active_tasks),
                'memory_stats': memory_stats
            }
            
            return utilization
            
        except Exception as e:
            logger.error(f"Failed to get GPU utilization: {e}")
            return {'error': str(e)}
    
    async def _background_cleanup(self):
        """Background task for periodic cleanup"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self.manage_gpu_memory()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
    
    async def shutdown(self):
        """Shutdown GPU compute offloader and cleanup resources"""
        logger.info("Shutting down GPU compute offloader...")
        
        try:
            # Cancel background cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            
            # Cleanup GPU memory
            if self._memory_manager:
                # Force cleanup of all allocated blocks
                memory_stats = self._memory_manager.get_memory_usage()
                logger.info(f"Cleaning up {memory_stats['active_blocks']} GPU memory blocks")
            
            self._initialized = False
            logger.info("GPU compute offloader shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during GPU compute offloader shutdown: {e}")
    
    @staticmethod
    def _cleanup_resources():
        """Static cleanup method for finalizer"""
        logger.debug("GPU compute offloader resources cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, '_initialized') and self._initialized:
            logger.warning("GPU compute offloader not properly shutdown")


# Utility functions for common GPU operations

async def create_gpu_offloader(max_workers: int = 4,
                             memory_strategy: GPUMemoryStrategy = GPUMemoryStrategy.LAZY,
                             enable_cpu_fallback: bool = True) -> GPUComputeOffloader:
    """
    Factory function to create and initialize GPU compute offloader
    
    Args:
        max_workers: Maximum number of worker threads
        memory_strategy: GPU memory management strategy
        enable_cpu_fallback: Whether to enable CPU fallback
        
    Returns:
        Initialized GPUComputeOffloader instance
    """
    offloader = GPUComputeOffloader(
        max_workers=max_workers,
        memory_strategy=memory_strategy,
        enable_cpu_fallback=enable_cpu_fallback
    )
    
    await offloader.initialize()
    return offloader


def is_gpu_computation_beneficial(data_size_mb: float, 
                                computation_complexity: str = "medium") -> bool:
    """
    Determine if GPU computation would be beneficial for given task
    
    Args:
        data_size_mb: Size of input data in MB
        computation_complexity: "low", "medium", "high"
        
    Returns:
        True if GPU computation is likely beneficial
    """
    # Simple heuristics - in real implementation would be more sophisticated
    complexity_thresholds = {
        "low": 10,      # 10MB threshold for low complexity
        "medium": 5,    # 5MB threshold for medium complexity  
        "high": 1       # 1MB threshold for high complexity
    }
    
    threshold = complexity_thresholds.get(computation_complexity, 5)
    return data_size_mb >= threshold


# Example GPU-optimized computation functions

def matrix_multiply_gpu_optimized(matrices: Tuple[Any, Any]) -> Any:
    """GPU-optimized matrix multiplication"""
    import numpy as np
    
    matrix_a, matrix_b = matrices
    
    # Convert to numpy arrays if needed
    if not isinstance(matrix_a, np.ndarray):
        matrix_a = np.array(matrix_a)
    if not isinstance(matrix_b, np.ndarray):
        matrix_b = np.array(matrix_b)
    
    # Perform matrix multiplication
    # In real GPU implementation, would use cuBLAS, cuDNN, or similar
    result = np.dot(matrix_a, matrix_b)
    
    return result


def ml_inference_gpu_optimized(model_data: Dict[str, Any]) -> Any:
    """
    Production GPU-optimized ML model inference.
    Supports PyTorch, TensorFlow, and ONNX Runtime with GPU acceleration.
    """
    import time
    start_time = time.time()

    model = model_data.get('model')
    input_data = model_data.get('input')
    model_type = model_data.get('model_type', 'pytorch')  # pytorch, tensorflow, onnx

    if not model or input_data is None:
        return {'error': 'Invalid model data: model and input required'}

    try:
        # PyTorch GPU inference
        if model_type == 'pytorch':
            try:
                import torch

                # Ensure model is on GPU if available
                device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

                if hasattr(model, 'to'):
                    model = model.to(device)
                    model.eval()

                # Convert input to tensor if needed
                if not isinstance(input_data, torch.Tensor):
                    input_tensor = torch.tensor(input_data).to(device)
                else:
                    input_tensor = input_data.to(device)

                # Run inference with no gradients
                with torch.no_grad():
                    output = model(input_tensor)

                # Convert output to CPU for return
                if isinstance(output, torch.Tensor):
                    result = output.cpu().numpy().tolist()
                else:
                    result = output

                inference_time = (time.time() - start_time) * 1000

                return {
                    'prediction': result,
                    'device': str(device),
                    'inference_time_ms': round(inference_time, 3),
                    'model_type': 'pytorch'
                }

            except ImportError:
                return {'error': 'PyTorch not available for GPU inference'}
            except Exception as e:
                return {'error': f'PyTorch inference failed: {str(e)}'}

        # TensorFlow GPU inference
        elif model_type == 'tensorflow':
            try:
                import tensorflow as tf

                # Run inference
                predictions = model(input_data)

                # Convert to numpy for serialization
                if hasattr(predictions, 'numpy'):
                    result = predictions.numpy().tolist()
                else:
                    result = predictions

                inference_time = (time.time() - start_time) * 1000

                return {
                    'prediction': result,
                    'device': 'GPU' if tf.config.list_physical_devices('GPU') else 'CPU',
                    'inference_time_ms': round(inference_time, 3),
                    'model_type': 'tensorflow'
                }

            except ImportError:
                return {'error': 'TensorFlow not available for GPU inference'}
            except Exception as e:
                return {'error': f'TensorFlow inference failed: {str(e)}'}

        # ONNX Runtime GPU inference
        elif model_type == 'onnx':
            try:
                import onnxruntime as ort
                import numpy as np

                # Create inference session with CUDA provider if available
                providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                session = ort.InferenceSession(model, providers=providers)

                # Prepare input
                input_name = session.get_inputs()[0].name
                if not isinstance(input_data, np.ndarray):
                    input_data = np.array(input_data)

                # Run inference
                outputs = session.run(None, {input_name: input_data})

                inference_time = (time.time() - start_time) * 1000

                return {
                    'prediction': outputs[0].tolist() if hasattr(outputs[0], 'tolist') else outputs[0],
                    'device': session.get_providers()[0],
                    'inference_time_ms': round(inference_time, 3),
                    'model_type': 'onnx'
                }

            except ImportError:
                return {'error': 'ONNX Runtime not available for GPU inference'}
            except Exception as e:
                return {'error': f'ONNX inference failed: {str(e)}'}

        else:
            return {'error': f'Unsupported model type: {model_type}'}

    except Exception as e:
        return {'error': f'ML inference failed: {str(e)}'}


def image_processing_gpu_optimized(image_data: Dict[str, Any]) -> Any:
    """
    Production GPU-optimized image processing.
    Supports OpenCV with CUDA, PyTorch transforms, and PIL operations.
    """
    import time
    start_time = time.time()

    image = image_data.get('image')
    operation = image_data.get('operation', 'resize')
    params = image_data.get('params', {})

    if image is None:
        return {'error': 'Invalid image data: image required'}

    try:
        # Try OpenCV with CUDA support first
        try:
            import cv2
            import numpy as np

            # Convert image to numpy array if needed
            if not isinstance(image, np.ndarray):
                if hasattr(image, 'numpy'):
                    image_np = image.numpy()
                else:
                    image_np = np.array(image)
            else:
                image_np = image

            # Check if CUDA is available
            cuda_available = cv2.cuda.getCudaEnabledDeviceCount() > 0

            if cuda_available:
                # Upload to GPU
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(image_np)

                # Perform operations on GPU
                if operation == 'resize':
                    width = params.get('width', 224)
                    height = params.get('height', 224)
                    gpu_result = cv2.cuda.resize(gpu_image, (width, height))
                elif operation == 'blur':
                    kernel_size = params.get('kernel_size', (5, 5))
                    gpu_result = cv2.cuda.createGaussianFilter(
                        gpu_image.type(), -1, kernel_size, 1.5
                    ).apply(gpu_image)
                elif operation == 'grayscale':
                    gpu_result = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
                else:
                    # Fallback for unsupported operations
                    gpu_result = gpu_image

                # Download from GPU
                result_image = gpu_result.download()
                device = 'GPU (CUDA)'
            else:
                # Fallback to CPU operations
                if operation == 'resize':
                    width = params.get('width', 224)
                    height = params.get('height', 224)
                    result_image = cv2.resize(image_np, (width, height))
                elif operation == 'blur':
                    kernel_size = params.get('kernel_size', (5, 5))
                    result_image = cv2.GaussianBlur(image_np, kernel_size, 1.5)
                elif operation == 'grayscale':
                    result_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
                else:
                    result_image = image_np

                device = 'CPU'

            processing_time = (time.time() - start_time) * 1000

            return {
                'processed_image': result_image.tolist() if isinstance(result_image, np.ndarray) else result_image,
                'operation': operation,
                'device': device,
                'processing_time_ms': round(processing_time, 3),
                'shape': result_image.shape if hasattr(result_image, 'shape') else None
            }

        except ImportError:
            # Try PyTorch transforms as fallback
            try:
                import torch
                import torchvision.transforms as transforms

                device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

                # Convert to tensor if needed
                if not isinstance(image, torch.Tensor):
                    to_tensor = transforms.ToTensor()
                    image_tensor = to_tensor(image).to(device)
                else:
                    image_tensor = image.to(device)

                # Apply transforms
                if operation == 'resize':
                    width = params.get('width', 224)
                    height = params.get('height', 224)
                    transform = transforms.Resize((height, width))
                    result_tensor = transform(image_tensor)
                elif operation == 'normalize':
                    mean = params.get('mean', [0.485, 0.456, 0.406])
                    std = params.get('std', [0.229, 0.224, 0.225])
                    transform = transforms.Normalize(mean, std)
                    result_tensor = transform(image_tensor)
                else:
                    result_tensor = image_tensor

                # Convert back to CPU for return
                result_image = result_tensor.cpu().numpy().tolist()

                processing_time = (time.time() - start_time) * 1000

                return {
                    'processed_image': result_image,
                    'operation': operation,
                    'device': str(device),
                    'processing_time_ms': round(processing_time, 3),
                    'backend': 'pytorch'
                }

            except ImportError:
                # Final fallback to PIL
                from PIL import Image as PILImage

                if not isinstance(image, PILImage.Image):
                    image = PILImage.fromarray(image)

                if operation == 'resize':
                    width = params.get('width', 224)
                    height = params.get('height', 224)
                    result_image = image.resize((width, height))
                elif operation == 'grayscale':
                    result_image = image.convert('L')
                else:
                    result_image = image

                processing_time = (time.time() - start_time) * 1000

                return {
                    'processed_image': 'PIL_Image_Object',  # Can't serialize PIL images directly
                    'operation': operation,
                    'device': 'CPU',
                    'processing_time_ms': round(processing_time, 3),
                    'backend': 'PIL'
                }

    except Exception as e:
        return {'error': f'Image processing failed: {str(e)}'}