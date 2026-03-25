#!/usr/bin/env python3
"""
Performance benchmarking and optimization tools for llama.cpp server

This module provides functionality to benchmark server performance,
analyze bottlenecks, and provide optimization recommendations.
"""

import os
import sys
import json
import time
import psutil
import platform
import statistics
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, asdict

# Local imports
try:
    from .config_manager import ConfigManager  # type: ignore
    from .error_handler import ErrorCategory, ErrorLevel, handle_error  # type: ignore
    from .system_optimizer import SystemOptimizer, get_system_optimizer  # type: ignore
except ImportError:
    # Fallback for standalone usage
    class ConfigManager:
        def __init__(self, config_path=None):
            self.config = {}
        
        def get(self, key, default=None):
            return default
        
        def set(self, key, value):
            pass
        
        def save_config(self):
            return True
    
    class ErrorCategory:
        SYSTEM = 0
        PERFORMANCE = 1
    
    class ErrorLevel:
        ERROR = 0
        WARNING = 1
    
    def handle_error(category, code, details=None, level=ErrorLevel.ERROR):
        pass
    
    class SystemOptimizer:
        def __init__(self):
            self.system_specs = None
            self.recommended_profile = "balanced"
            self.optimization_settings = {}
        
        def get_system_specs(self):
            return None
    
    def get_system_optimizer():
        return SystemOptimizer()


@dataclass
class BenchmarkResult:
    """Benchmark result"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        result = {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat()
        }
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    gpu_usage_percent: Optional[float]
    gpu_memory_usage_percent: Optional[float]
    request_latency_ms: float
    throughput_requests_per_second: float
    error_rate_percent: float
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class PerformanceBenchmark:
    """Performance benchmarking and optimization tools"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize performance benchmark
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config_manager = ConfigManager(config_path)
        self.system_optimizer = get_system_optimizer()
        
        # Initialize logger
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = log_dir / "performance_benchmark.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Initialize results storage
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def benchmark_cpu(self, duration_seconds: int = 10) -> BenchmarkResult:
        """Benchmark CPU performance
        
        Args:
            duration_seconds: Duration of benchmark in seconds
            
        Returns:
            BenchmarkResult: CPU benchmark result
        """
        try:
            # Get CPU info
            cpu_freq = psutil.cpu_freq()
            cpu_info = {
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "frequency": cpu_freq[0].current if cpu_freq and len(cpu_freq) > 0 else 0
            }
            
            # Run CPU benchmark
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            cpu_percentages = []
            while time.time() < end_time:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_percentages.append(cpu_percent)
            
            # Calculate average CPU usage
            avg_cpu_usage = statistics.mean(cpu_percentages)
            
            # Calculate CPU score (higher is better)
            cpu_score = avg_cpu_usage * cpu_info["cores"]
            
            return BenchmarkResult(
                name="CPU Performance",
                value=cpu_score,
                unit="score",
                timestamp=datetime.now(),
                details={
                    "average_usage_percent": avg_cpu_usage,
                    "cores": cpu_info["cores"],
                    "threads": cpu_info["threads"],
                    "frequency_mhz": cpu_info["frequency"],
                    "duration_seconds": duration_seconds
                }
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "001",
                    f"Failed to benchmark CPU: {e}",
                    ErrorLevel.ERROR
                )
            return BenchmarkResult(
                name="CPU Performance",
                value=0,
                unit="score",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def benchmark_memory(self, duration_seconds: int = 10) -> BenchmarkResult:
        """Benchmark memory performance
        
        Args:
            duration_seconds: Duration of benchmark in seconds
            
        Returns:
            BenchmarkResult: Memory benchmark result
        """
        try:
            # Get memory info
            memory = psutil.virtual_memory()
            
            # Run memory benchmark
            start_time = time.time()
            end_time = start_time + duration_seconds
            
            memory_percentages = []
            while time.time() < end_time:
                mem_percent = memory.percent
                memory_percentages.append(mem_percent)
                time.sleep(0.1)
            
            # Calculate average memory usage
            avg_memory_usage = statistics.mean(memory_percentages)
            
            # Calculate memory score (lower is better for usage, higher for available)
            available_memory_gb = memory.available / (1024**3)
            memory_score = available_memory_gb * (100 - avg_memory_usage) / 100
            
            return BenchmarkResult(
                name="Memory Performance",
                value=memory_score,
                unit="GB_available",
                timestamp=datetime.now(),
                details={
                    "average_usage_percent": avg_memory_usage,
                    "total_gb": memory.total / (1024**3),
                    "available_gb": available_memory_gb,
                    "used_gb": memory.used / (1024**3),
                    "duration_seconds": duration_seconds
                }
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "002",
                    f"Failed to benchmark memory: {e}",
                    ErrorLevel.ERROR
                )
            return BenchmarkResult(
                name="Memory Performance",
                value=0,
                unit="GB_available",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def benchmark_disk(self, test_file_size_mb: int = 100) -> BenchmarkResult:
        """Benchmark disk performance
        
        Args:
            test_file_size_mb: Size of test file in MB
            
        Returns:
            BenchmarkResult: Disk benchmark result
        """
        try:
            # Create test file
            test_file = Path("benchmark_test.tmp")
            
            # Benchmark write speed
            start_time = time.time()
            
            with open(test_file, 'wb') as f:
                # Write test data
                chunk = b'0' * 1024 * 1024  # 1MB chunk
                for _ in range(test_file_size_mb):
                    f.write(chunk)
            
            write_time = time.time() - start_time
            write_speed_mb_s = test_file_size_mb / write_time
            
            # Benchmark read speed
            start_time = time.time()
            
            with open(test_file, 'rb') as f:
                # Read test data
                while f.read(1024 * 1024):  # Read 1MB at a time
                    pass
            
            read_time = time.time() - start_time
            read_speed_mb_s = test_file_size_mb / read_time
            
            # Clean up test file
            test_file.unlink()
            
            # Calculate average speed
            avg_speed_mb_s = (write_speed_mb_s + read_speed_mb_s) / 2
            
            return BenchmarkResult(
                name="Disk Performance",
                value=avg_speed_mb_s,
                unit="MB/s",
                timestamp=datetime.now(),
                details={
                    "write_speed_mb_s": write_speed_mb_s,
                    "read_speed_mb_s": read_speed_mb_s,
                    "test_file_size_mb": test_file_size_mb,
                    "write_time_s": write_time,
                    "read_time_s": read_time
                }
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "003",
                    f"Failed to benchmark disk: {e}",
                    ErrorLevel.ERROR
                )
            return BenchmarkResult(
                name="Disk Performance",
                value=0,
                unit="MB/s",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def benchmark_gpu(self, duration_seconds: int = 10) -> Optional[BenchmarkResult]:
        """Benchmark GPU performance if available
        
        Args:
            duration_seconds: Duration of benchmark in seconds
            
        Returns:
            Optional[BenchmarkResult]: GPU benchmark result if GPU is available, None otherwise
        """
        try:
            # Check if GPU is available
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                if device_count == 0:
                    pynvml.nvmlShutdown()
                    return None
                
                # Get GPU info
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Run GPU benchmark
                start_time = time.time()
                end_time = start_time + duration_seconds
                
                gpu_usages = []
                gpu_memory_usages = []
                
                while time.time() < end_time:
                    # Get GPU utilization
                    gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_usages.append(gpu_util.gpu)
                    gpu_memory_usages.append(gpu_util.memory)
                    
                    time.sleep(0.1)
                
                pynvml.nvmlShutdown()
                
                # Calculate average GPU usage
                avg_gpu_usage = statistics.mean(gpu_usages)
                avg_gpu_memory_usage = statistics.mean(gpu_memory_usages)
                
                # Calculate GPU score (higher is better)
                gpu_score = avg_gpu_usage * avg_gpu_memory_usage / 100
                
                return BenchmarkResult(
                    name="GPU Performance",
                    value=gpu_score,
                    unit="score",
                    timestamp=datetime.now(),
                    details={
                        "average_usage_percent": avg_gpu_usage,
                        "average_memory_usage_percent": avg_gpu_memory_usage,
                        "gpu_name": gpu_name,
                        "duration_seconds": duration_seconds
                    }
                )
            except (ImportError, Exception):
                # GPU not available or failed to benchmark
                return None
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "004",
                    f"Failed to benchmark GPU: {e}",
                    ErrorLevel.WARNING
                )
            return None
    
    def benchmark_inference(self, model_path: Optional[Union[str, Path]] = None,
                           prompt: str = "Hello, how are you?",
                           max_tokens: int = 256,
                           num_iterations: int = 5) -> BenchmarkResult:
        """Benchmark inference performance
        
        Args:
            model_path: Path to model file
            prompt: Test prompt
            max_tokens: Maximum number of tokens to generate
            num_iterations: Number of iterations to run
            
        Returns:
            BenchmarkResult: Inference benchmark result
        """
        try:
            # Try to import llama_cpp
            try:
                from llama_cpp import Llama
            except ImportError:
                if ErrorCategory and ErrorLevel:
                    handle_error(
                        ErrorCategory.PERFORMANCE,
                        "005",
                        "llama_cpp not available for inference benchmark",
                        ErrorLevel.WARNING
                    )
                return BenchmarkResult(
                    name="Inference Performance",
                    value=0,
                    unit="tokens/s",
                    timestamp=datetime.now(),
                    details={"error": "llama_cpp not available"}
                )
            
            # Use default model if not specified
            if not model_path:
                model_path = self.config_manager.get("models.directory", "models")
                if isinstance(model_path, str):
                    model_path = Path(model_path)
                
                # Look for a model file
                model_files = list(model_path.glob("*.gguf"))
                if not model_files:
                    return BenchmarkResult(
                        name="Inference Performance",
                        value=0,
                        unit="tokens/s",
                        timestamp=datetime.now(),
                        details={"error": "No model files found"}
                    )
                
                model_path = model_files[0]
            
            # Load model
            llm = Llama(model_path=str(model_path), n_ctx=2048, n_threads=4)
            
            # Run inference benchmark
            latencies = []
            tokens_generated = []
            
            for _ in range(num_iterations):
                start_time = time.time()
                
                output = llm(
                    prompt,
                    max_tokens=max_tokens,
                    stop=["\n"],
                    echo=False
                )
                
                end_time = time.time()
                
                # Calculate latency
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                # Count tokens generated
                tokens = 0
                try:
                    # Handle different response types
                    if isinstance(output, dict):
                        if "usage" in output and "completion_tokens" in output["usage"]:
                            tokens = output["usage"]["completion_tokens"]
                        elif "choices" in output and len(output["choices"]) > 0 and "text" in output["choices"][0]:
                            text = output["choices"][0]["text"]
                            tokens = len(text.split())
                    elif hasattr(output, '__getitem__'):
                        # Handle object that supports item access
                        try:
                            if "usage" in output and "completion_tokens" in output["usage"]:  # type: ignore
                                tokens = output["usage"]["completion_tokens"]  # type: ignore
                            elif "choices" in output and len(output["choices"]) > 0 and "text" in output["choices"][0]:  # type: ignore
                                text = output["choices"][0]["text"]  # type: ignore
                                tokens = len(text.split())
                        except (TypeError, AttributeError):
                            # Fallback to estimating tokens
                            tokens = 0
                    else:
                        # Handle iterators or other types by converting to string and counting words
                        try:
                            output_str = str(output)
                            tokens = len(output_str.split())
                        except Exception:
                            tokens = 0
                except Exception:
                    # Fallback to estimating tokens
                    tokens = 0
                
                tokens_generated.append(tokens)
            
            # Calculate metrics
            avg_latency_ms = statistics.mean(latencies)
            avg_tokens = statistics.mean(tokens_generated)
            
            # Calculate tokens per second
            if avg_latency_ms > 0:
                tokens_per_second = (avg_tokens / avg_latency_ms) * 1000
            else:
                tokens_per_second = 0
            
            return BenchmarkResult(
                name="Inference Performance",
                value=tokens_per_second,
                unit="tokens/s",
                timestamp=datetime.now(),
                details={
                    "average_latency_ms": avg_latency_ms,
                    "average_tokens": avg_tokens,
                    "max_tokens": max_tokens,
                    "num_iterations": num_iterations,
                    "model_path": str(model_path),
                    "prompt": prompt
                }
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "006",
                    f"Failed to benchmark inference: {e}",
                    ErrorLevel.ERROR
                )
            return BenchmarkResult(
                name="Inference Performance",
                value=0,
                unit="tokens/s",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def run_comprehensive_benchmark(self, model_path: Optional[Union[str, Path]] = None) -> List[BenchmarkResult]:
        """Run comprehensive benchmark suite
        
        Args:
            model_path: Path to model file for inference benchmark
            
        Returns:
            List[BenchmarkResult]: List of benchmark results
        """
        results = []
        
        # CPU benchmark
        self.logger.info("Running CPU benchmark...")
        cpu_result = self.benchmark_cpu()
        results.append(cpu_result)
        
        # Memory benchmark
        self.logger.info("Running memory benchmark...")
        memory_result = self.benchmark_memory()
        results.append(memory_result)
        
        # Disk benchmark
        self.logger.info("Running disk benchmark...")
        disk_result = self.benchmark_disk()
        results.append(disk_result)
        
        # GPU benchmark (if available)
        self.logger.info("Running GPU benchmark...")
        gpu_result = self.benchmark_gpu()
        if gpu_result:
            results.append(gpu_result)
        
        # Inference benchmark (if model is available)
        self.logger.info("Running inference benchmark...")
        inference_result = self.benchmark_inference(model_path)
        results.append(inference_result)
        
        # Save results
        self._save_benchmark_results(results)
        
        return results
    
    def _save_benchmark_results(self, results: List[BenchmarkResult]):
        """Save benchmark results to file
        
        Args:
            results: List of benchmark results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"benchmark_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump([result.to_dict() for result in results], f, indent=2)
            
            self.logger.info(f"Saved benchmark results to {results_file}")
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "007",
                    f"Failed to save benchmark results: {e}",
                    ErrorLevel.ERROR
                )
    
    def get_current_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics
        
        Returns:
            PerformanceMetrics: Current performance metrics
        """
        try:
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Get GPU usage (if available)
            gpu_usage = None
            gpu_memory_usage = None
            
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_usage = gpu_util.gpu
                    gpu_memory_usage = gpu_util.memory
                
                pynvml.nvmlShutdown()
            except (ImportError, Exception):
                pass
            
            # Placeholder for request metrics (would be obtained from server)
            request_latency = 50.0  # ms
            throughput = 10.0  # requests per second
            error_rate = 0.5  # percent
            
            # Ensure numeric values are properly converted to float
            def safe_float(value):
                if value is None:
                    return None
                try:
                    if isinstance(value, list):
                        # Take the first value if it's a list
                        value = value[0] if value else 0
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0
            
            # Ensure numeric values are properly converted to float
            def safe_float_metric(value, default=0.0):
                if value is None:
                    return default
                try:
                    if isinstance(value, list):
                        # Take the first value if it's a list
                        value = value[0] if value else 0
                    return float(value)
                except (TypeError, ValueError):
                    return default
            
            return PerformanceMetrics(
                cpu_usage_percent=safe_float_metric(cpu_usage),
                memory_usage_percent=safe_float_metric(memory_usage),
                disk_usage_percent=safe_float_metric(disk_usage),
                gpu_usage_percent=safe_float_metric(gpu_usage),
                gpu_memory_usage_percent=safe_float_metric(gpu_memory_usage),
                request_latency_ms=safe_float_metric(request_latency),
                throughput_requests_per_second=safe_float_metric(throughput),
                error_rate_percent=safe_float_metric(error_rate)
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "008",
                    f"Failed to get performance metrics: {e}",
                    ErrorLevel.ERROR
                )
            # Return default metrics
            return PerformanceMetrics(
                cpu_usage_percent=0,
                memory_usage_percent=0,
                disk_usage_percent=0,
                gpu_usage_percent=None,
                gpu_memory_usage_percent=None,
                request_latency_ms=0,
                throughput_requests_per_second=0,
                error_rate_percent=0
            )
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics
        
        Returns:
            PerformanceMetrics: Current performance metrics
        """
        return self.get_current_performance_metrics()
    
    def run_full_benchmark(self, backend=None) -> Dict[str, Any]:
        """Run full benchmark suite
        
        Args:
            backend: Backend instance for inference benchmark
            
        Returns:
            Dict[str, Any]: Benchmark results
        """
        results = self.run_comprehensive_benchmark()
        
        # Convert to dictionary
        benchmark_results = {}
        for result in results:
            benchmark_results[result.name] = {
                "value": result.value,
                "unit": result.unit,
                "details": result.details
            }
        
        return benchmark_results
    
    def benchmark_system(self, backend=None) -> Dict[str, Any]:
        """Benchmark system performance
        
        Args:
            backend: Backend instance for inference benchmark
            
        Returns:
            Dict[str, Any]: Benchmark results
        """
        return self.run_full_benchmark(backend)
    
    def get_optimization_recommendations(self, results: List[BenchmarkResult]) -> List[str]:
        """Get optimization recommendations based on benchmark results
        
        Args:
            results: List of benchmark results
            
        Returns:
            List[str]: List of optimization recommendations
        """
        recommendations = []
        
        # Analyze CPU results
        cpu_result = next((r for r in results if r.name == "CPU Performance"), None)
        if cpu_result and cpu_result.details:
            cpu_usage = cpu_result.details.get("average_usage_percent", 0)
            if cpu_usage > 90:
                recommendations.append("CPU usage is consistently high. Consider reducing the number of threads or upgrading CPU.")
            elif cpu_usage < 30:
                recommendations.append("CPU usage is low. Consider increasing the number of threads for better performance.")
        
        # Analyze memory results
        memory_result = next((r for r in results if r.name == "Memory Performance"), None)
        if memory_result and memory_result.details:
            memory_usage = memory_result.details.get("average_usage_percent", 0)
            if memory_usage > 90:
                recommendations.append("Memory usage is consistently high. Consider reducing context window or enabling low VRAM mode.")
            elif memory_usage < 30:
                recommendations.append("Memory usage is low. Consider increasing context window or loading more models.")
        
        # Analyze disk results
        disk_result = next((r for r in results if r.name == "Disk Performance"), None)
        if disk_result and disk_result.details:
            read_speed = disk_result.details.get("read_speed_mb_s", 0)
            write_speed = disk_result.details.get("write_speed_mb_s", 0)
            
            if read_speed < 50:
                recommendations.append("Disk read speed is slow. Consider using SSD for models and cache.")
            
            if write_speed < 50:
                recommendations.append("Disk write speed is slow. Consider using SSD for models and cache.")
        
        # Analyze GPU results
        gpu_result = next((r for r in results if r.name == "GPU Performance"), None)
        if gpu_result and gpu_result.details:
            gpu_usage = gpu_result.details.get("average_usage_percent", 0)
            if gpu_usage < 50:
                recommendations.append("GPU usage is low. Consider offloading more layers to GPU for better performance.")
        
        # Analyze inference results
        inference_result = next((r for r in results if r.name == "Inference Performance"), None)
        if inference_result and inference_result.details:
            tokens_per_second = inference_result.value
            latency = inference_result.details.get("average_latency_ms", 0)
            
            if tokens_per_second < 10:
                recommendations.append("Inference speed is slow. Consider using a quantized model or enabling GPU acceleration.")
            
            if latency > 1000:
                recommendations.append("Inference latency is high. Consider reducing context window or using a smaller model.")
        
        # Add general recommendations
        recommendations.append("Regularly monitor performance metrics to identify bottlenecks.")
        recommendations.append("Consider system-specific optimizations based on your hardware configuration.")
        
        return recommendations
    
    def compare_benchmarks(self, baseline_file: Union[str, Path], 
                          current_file: Union[str, Path]) -> Dict[str, Any]:
        """Compare benchmark results
        
        Args:
            baseline_file: Path to baseline benchmark results
            current_file: Path to current benchmark results
            
        Returns:
            Dict[str, Any]: Comparison results
        """
        try:
            # Load baseline results
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            # Load current results
            with open(current_file, 'r') as f:
                current_data = json.load(f)
            
            # Compare results
            comparison = {}
            
            for baseline_result in baseline_data:
                name = baseline_result["name"]
                
                # Find corresponding current result
                current_result = next((r for r in current_data if r["name"] == name), None)
                
                if current_result:
                    # Calculate percentage change
                    baseline_value = baseline_result["value"]
                    current_value = current_result["value"]
                    
                    if baseline_value != 0:
                        percent_change = ((current_value - baseline_value) / baseline_value) * 100
                    else:
                        percent_change = 0
                    
                    comparison[name] = {
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "percent_change": percent_change,
                        "unit": baseline_result["unit"],
                        "improved": percent_change > 0 if baseline_result["unit"] in ["tokens/s", "MB/s", "score"] else percent_change < 0
                    }
            
            return comparison
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.PERFORMANCE,
                    "009",
                    f"Failed to compare benchmarks: {e}",
                    ErrorLevel.ERROR
                )
            return {}


def get_performance_benchmark(config_path: Optional[Union[str, Path]] = None) -> PerformanceBenchmark:
    """Get performance benchmark instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        PerformanceBenchmark: Performance benchmark instance
    """
    return PerformanceBenchmark(config_path)


if __name__ == "__main__":
    # Test performance benchmark
    benchmark = get_performance_benchmark()
    
    print("Running comprehensive benchmark...")
    results = benchmark.run_comprehensive_benchmark()
    
    print("\nBenchmark Results:")
    for result in results:
        print(f"- {result.name}: {result.value} {result.unit}")
    
    print("\nOptimization Recommendations:")
    recommendations = benchmark.get_optimization_recommendations(results)
    for recommendation in recommendations:
        print(f"- {recommendation}")
    
    print("\nCurrent Performance Metrics:")
    metrics = benchmark.get_current_performance_metrics()
    print(json.dumps(metrics.to_dict(), indent=2))