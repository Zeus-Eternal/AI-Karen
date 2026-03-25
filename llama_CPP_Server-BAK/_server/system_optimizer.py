#!/usr/bin/env python3
"""
System optimizer for automatic configuration based on hardware detection

This module provides functionality to automatically optimize system settings
based on detected hardware capabilities and system resources.
"""

import os
import sys
import json
import psutil
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict

# Local imports with type: ignore to avoid circular import issues
try:
    from .config_manager import ConfigManager  # type: ignore
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

try:
    from .error_handler import ErrorCategory, ErrorLevel, handle_error  # type: ignore
except ImportError:
    # Fallback for standalone usage
    class ErrorCategory:
        SYSTEM = 0
        CONFIGURATION = 1
    
    class ErrorLevel:
        ERROR = 0
    
    def handle_error(category, code, details=None, level=ErrorLevel.ERROR):
        pass


@dataclass
class SystemSpecs:
    """System specifications"""
    os: str
    os_version: str
    architecture: str
    cpu_name: str
    cpu_cores: int
    cpu_threads: int
    ram_total_gb: float
    gpu_available: bool
    gpu_name: Optional[str]
    gpu_memory_gb: Optional[float]
    disk_free_gb: float
    disk_total_gb: float
    python_version: str
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class SystemOptimizer:
    """System optimizer for automatic configuration"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the system optimizer
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.config_manager = ConfigManager(config_path)
        self.system_specs = self._detect_system_specs()
        self.recommended_profile = self._determine_optimal_profile()
        self.optimization_settings = self._generate_optimization_settings()
    
    def _detect_system_specs(self) -> SystemSpecs:
        """Detect system specifications
        
        Returns:
            SystemSpecs: Detected system specifications
        """
        try:
            # Get OS information
            os_info = platform.system()
            os_version = platform.version()
            
            # Get architecture
            architecture = platform.machine()
            
            # Get CPU information
            cpu_name = "Unknown"
            cpu_cores = psutil.cpu_count(logical=False) or 4
            cpu_threads = psutil.cpu_count(logical=True) or 8
            
            # Try to get CPU name
            try:
                if os_info == "Linux":
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if "model name" in line:
                                cpu_name = line.split(":")[1].strip()
                                break
                elif os_info == "Windows":
                    import wmi
                    c = wmi.WMI()
                    for processor in c.Win32_Processor():
                        cpu_name = processor.Name
                        break
                elif os_info == "Darwin":  # macOS
                    import subprocess
                    result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        cpu_name = result.stdout.strip()
            except Exception:
                # If we can't get the CPU name, just use "Unknown"
                pass
            
            # Get RAM information
            ram = psutil.virtual_memory()
            ram_total_gb = round(ram.total / (1024**3), 2)
            
            # Get GPU information
            gpu_available = False
            gpu_name = None
            gpu_memory_gb = None
            
            try:
                # Try to detect NVIDIA GPU
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    device_count = pynvml.nvmlDeviceGetCount()
                    if device_count > 0:
                        gpu_available = True
                        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                        gpu_name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                        gpu_memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        gpu_memory_gb = round(gpu_memory_info.total / (1024**3), 2)
                    pynvml.nvmlShutdown()
                except (ImportError, Exception):
                    # Try to detect AMD GPU or other alternatives
                    try:
                        import subprocess
                        result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True)
                        if "VGA" in result.stdout and ("NVIDIA" in result.stdout or "AMD" in result.stdout):
                            gpu_available = True
                            # We can't easily get the exact GPU name and memory without additional libraries
                            gpu_name = "Detected GPU"
                            gpu_memory_gb = 4.0  # Default assumption
                    except (ImportError, Exception):
                        pass
            except Exception:
                pass
            
            # Get disk information
            disk = psutil.disk_usage('/')
            disk_free_gb = round(disk.free / (1024**3), 2)
            disk_total_gb = round(disk.total / (1024**3), 2)
            
            # Get Python version
            python_version = platform.python_version()
            
            return SystemSpecs(
                os=os_info,
                os_version=os_version,
                architecture=architecture,
                cpu_name=cpu_name,
                cpu_cores=cpu_cores,
                cpu_threads=cpu_threads,
                ram_total_gb=ram_total_gb,
                gpu_available=gpu_available,
                gpu_name=gpu_name,
                gpu_memory_gb=gpu_memory_gb,
                disk_free_gb=disk_free_gb,
                disk_total_gb=disk_total_gb,
                python_version=python_version
            )
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.SYSTEM,
                    "001",
                    f"Failed to detect system specs: {e}",
                    ErrorLevel.ERROR
                )
            # Return default specs if detection fails
            return SystemSpecs(
                os="Unknown",
                os_version="Unknown",
                architecture="Unknown",
                cpu_name="Unknown",
                cpu_cores=4,
                cpu_threads=8,
                ram_total_gb=8.0,
                gpu_available=False,
                gpu_name=None,
                gpu_memory_gb=None,
                disk_free_gb=10.0,
                disk_total_gb=50.0,
                python_version=platform.python_version()
            )
    
    def _determine_optimal_profile(self) -> str:
        """Determine optimal performance profile based on system specs
        
        Returns:
            str: Optimal profile name
        """
        # Define profiles in order of performance requirements
        profiles = ["minimal", "balanced", "performance", "high_performance"]
        
        # Start with minimal profile and upgrade based on specs
        profile = "minimal"
        
        # Check RAM
        if self.system_specs.ram_total_gb >= 8.0:
            profile = "balanced"
        
        if self.system_specs.ram_total_gb >= 16.0:
            profile = "performance"
        
        if self.system_specs.ram_total_gb >= 32.0:
            profile = "high_performance"
        
        # Check GPU
        if self.system_specs.gpu_available:
            # GPU allows for better performance
            if profile == "minimal":
                profile = "balanced"
            elif profile == "balanced":
                profile = "performance"
        
        # Check CPU
        if self.system_specs.cpu_cores >= 8:
            # More CPU cores allow for better performance
            if profile == "minimal":
                profile = "balanced"
            elif profile == "balanced":
                profile = "performance"
        
        return profile
    
    def _generate_optimization_settings(self) -> Dict[str, Any]:
        """Generate optimization settings based on system specs
        
        Returns:
            Dict[str, Any]: Optimization settings
        """
        settings = {}
        
        # Server settings
        settings["server"] = {
            "host": "localhost",
            "port": 8080,
            "log_level": "INFO"
        }
        
        # Performance settings based on profile
        if self.recommended_profile == "minimal":
            settings["performance"] = {
                "num_threads": min(self.system_specs.cpu_threads, 4),
                "batch_size": 1,
                "context_window": 2048,
                "low_vram": True,
                "max_loaded_models": 1
            }
        elif self.recommended_profile == "balanced":
            settings["performance"] = {
                "num_threads": min(self.system_specs.cpu_threads, 8),
                "batch_size": 1,
                "context_window": 4096,
                "low_vram": not self.system_specs.gpu_available,
                "max_loaded_models": 2 if self.system_specs.ram_total_gb >= 16.0 else 1
            }
        elif self.recommended_profile == "performance":
            settings["performance"] = {
                "num_threads": self.system_specs.cpu_threads,
                "batch_size": 2 if self.system_specs.ram_total_gb >= 32.0 else 1,
                "context_window": 8192,
                "low_vram": False,
                "max_loaded_models": 3 if self.system_specs.ram_total_gb >= 32.0 else 2
            }
        elif self.recommended_profile == "high_performance":
            settings["performance"] = {
                "num_threads": self.system_specs.cpu_threads,
                "batch_size": 4 if self.system_specs.ram_total_gb >= 64.0 else 2,
                "context_window": 16384,
                "low_vram": False,
                "max_loaded_models": 5 if self.system_specs.ram_total_gb >= 64.0 else 3
            }
        
        # Model settings
        settings["models"] = {
            "directory": "models",
            "max_cache_gb": min(self.system_specs.ram_total_gb * 0.3, 16.0),
            "download_parallel": 2 if self.system_specs.ram_total_gb >= 16.0 else 1
        }
        
        # GPU settings if available
        if self.system_specs.gpu_available:
            settings["gpu"] = {
                "enabled": True,
                "layers": 43 if self.system_specs.gpu_memory_gb and self.system_specs.gpu_memory_gb >= 8.0 else 20,
                "memory_split": self.system_specs.gpu_memory_gb if self.system_specs.gpu_memory_gb else 4.0
            }
        else:
            settings["gpu"] = {
                "enabled": False,
                "layers": 0,
                "memory_split": 0.0
            }
        
        return settings
    
    def apply_optimization_settings(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """Apply optimization settings to configuration
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use provided config path or fall back to the one from initialization
            target_config_path = Path(config_path) if config_path else self.config_path
            
            if target_config_path:
                # Load existing config if it exists
                config_manager = ConfigManager(target_config_path)
            else:
                # Use the config manager from initialization
                config_manager = self.config_manager
            
            # Apply optimization settings
            for section, settings in self.optimization_settings.items():
                for key, value in settings.items():
                    config_manager.set(f"{section}.{key}", value)
            
            # Save configuration
            return config_manager.save_config()
        except Exception as e:
            if ErrorCategory and ErrorLevel:
                handle_error(
                    ErrorCategory.CONFIGURATION,
                    "001",
                    f"Failed to apply optimization settings: {e}",
                    ErrorLevel.ERROR
                )
            return False
    
    def get_system_specs(self) -> SystemSpecs:
        """Get detected system specifications
        
        Returns:
            SystemSpecs: System specifications
        """
        return self.system_specs
    
    def get_optimization_profile(self) -> str:
        """Get recommended optimization profile
        
        Returns:
            str: Optimization profile name
        """
        return self.recommended_profile
    
    def get_optimization_settings(self) -> Dict[str, Any]:
        """Get optimization settings
        
        Returns:
            Dict[str, Any]: Optimization settings
        """
        return self.optimization_settings
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information
        
        Returns:
            Dict[str, Any]: System information
        """
        return self.system_specs.to_dict()
    
    def optimize_all(self, optimize_cpu: bool = True, optimize_memory: bool = True,
                   optimize_disk: bool = True, optimize_gpu: bool = True) -> Dict[str, Any]:
        """Apply all optimizations
        
        Args:
            optimize_cpu: Whether to optimize CPU settings
            optimize_memory: Whether to optimize memory settings
            optimize_disk: Whether to optimize disk settings
            optimize_gpu: Whether to optimize GPU settings
            
        Returns:
            Dict[str, Any]: Applied optimizations
        """
        optimizations = {}
        
        if optimize_cpu:
            optimizations["cpu"] = {
                "threads": self.optimization_settings["performance"]["num_threads"],
                "batch_size": self.optimization_settings["performance"]["batch_size"]
            }
        
        if optimize_memory:
            optimizations["memory"] = {
                "context_window": self.optimization_settings["performance"]["context_window"],
                "low_vram": self.optimization_settings["performance"]["low_vram"],
                "max_loaded_models": self.optimization_settings["performance"]["max_loaded_models"]
            }
        
        if optimize_disk:
            optimizations["disk"] = {
                "max_cache_gb": self.optimization_settings["models"]["max_cache_gb"]
            }
        
        if optimize_gpu and self.system_specs.gpu_available:
            optimizations["gpu"] = self.optimization_settings["gpu"]
        
        # Apply the optimizations
        self.apply_optimization_settings()
        
        return optimizations
    
    def optimize_cpu(self) -> Dict[str, Any]:
        """Optimize CPU settings
        
        Returns:
            Dict[str, Any]: Applied CPU optimizations
        """
        optimizations = {
            "threads": self.optimization_settings["performance"]["num_threads"],
            "batch_size": self.optimization_settings["performance"]["batch_size"]
        }
        
        # Apply optimizations
        self.apply_optimization_settings()
        
        return optimizations
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory settings
        
        Returns:
            Dict[str, Any]: Applied memory optimizations
        """
        optimizations = {
            "context_window": self.optimization_settings["performance"]["context_window"],
            "low_vram": self.optimization_settings["performance"]["low_vram"],
            "max_loaded_models": self.optimization_settings["performance"]["max_loaded_models"]
        }
        
        # Apply optimizations
        self.apply_optimization_settings()
        
        return optimizations
    
    def optimize_disk(self) -> Dict[str, Any]:
        """Optimize disk settings
        
        Returns:
            Dict[str, Any]: Applied disk optimizations
        """
        optimizations = {
            "max_cache_gb": self.optimization_settings["models"]["max_cache_gb"]
        }
        
        # Apply optimizations
        self.apply_optimization_settings()
        
        return optimizations
    
    def optimize_gpu(self) -> Dict[str, Any]:
        """Optimize GPU settings
        
        Returns:
            Dict[str, Any]: Applied GPU optimizations
        """
        optimizations = {}
        
        if self.system_specs.gpu_available:
            optimizations = self.optimization_settings["gpu"]
            
            # Apply optimizations
            self.apply_optimization_settings()
        
        return optimizations
    
    def get_recommendations(self) -> List[str]:
        """Get system optimization recommendations
        
        Returns:
            List[str]: List of recommendations
        """
        recommendations = []
        
        # RAM recommendations
        if self.system_specs.ram_total_gb < 8.0:
            recommendations.append("Consider upgrading RAM to at least 8GB for better performance")
        elif self.system_specs.ram_total_gb < 16.0:
            recommendations.append("Consider upgrading RAM to 16GB or more for improved performance")
        
        # GPU recommendations
        if not self.system_specs.gpu_available:
            recommendations.append("Consider adding a GPU for better performance with large models")
        elif self.system_specs.gpu_memory_gb and self.system_specs.gpu_memory_gb < 8.0:
            recommendations.append("Consider upgrading to a GPU with at least 8GB VRAM for better performance")
        
        # CPU recommendations
        if self.system_specs.cpu_cores < 4:
            recommendations.append("Consider upgrading to a CPU with at least 4 cores for better performance")
        elif self.system_specs.cpu_cores < 8:
            recommendations.append("Consider upgrading to a CPU with 8 or more cores for improved performance")
        
        # Disk recommendations
        if self.system_specs.disk_free_gb < 10.0:
            recommendations.append("Consider freeing up disk space or adding more storage for models")
        
        return recommendations


def get_system_optimizer(config_path: Optional[Union[str, Path]] = None) -> SystemOptimizer:
    """Get system optimizer instance
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        SystemOptimizer: System optimizer instance
    """
    return SystemOptimizer(config_path)


def optimize_system(config_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Dict[str, Any]]:
    """Optimize system settings
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Tuple[bool, Dict[str, Any]]: (success, optimization_settings)
    """
    try:
        optimizer = get_system_optimizer(config_path)
        success = optimizer.apply_optimization_settings()
        return success, optimizer.get_optimization_settings()
    except Exception as e:
        if ErrorCategory and ErrorLevel:
            handle_error(
                ErrorCategory.SYSTEM,
                "002",
                f"Failed to optimize system: {e}",
                ErrorLevel.ERROR
            )
        return False, {}


if __name__ == "__main__":
    # Test the system optimizer
    optimizer = get_system_optimizer()
    
    print("System Specifications:")
    print(json.dumps(optimizer.get_system_specs().to_dict(), indent=2))
    
    print(f"\nRecommended Profile: {optimizer.get_optimization_profile()}")
    
    print("\nOptimization Settings:")
    print(json.dumps(optimizer.get_optimization_settings(), indent=2))
    
    print("\nRecommendations:")
    for recommendation in optimizer.get_recommendations():
        print(f"- {recommendation}")