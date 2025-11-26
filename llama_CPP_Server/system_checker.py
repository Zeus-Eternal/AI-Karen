#!/usr/bin/env python3
"""
System requirements checker for llama.cpp server

This script checks the system's hardware and software capabilities
and provides recommendations for optimal llama.cpp configuration.
"""

import os
import sys
import json
import platform
import logging
import subprocess
import multiprocessing
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Add _server directory to Python path
server_path = Path(__file__).parent / "_server"
sys.path.insert(0, str(server_path))

# Import configuration manager
ConfigManager = None
CONFIG_MANAGER_AVAILABLE = False
try:
    from _server.config_manager import ConfigManager as _ConfigManager
    ConfigManager = _ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemChecker:
    """Checks system requirements and provides recommendations"""
    
    # Minimum requirements
    MINIMUM_REQUIREMENTS = {
        "ram_gb": 4,
        "disk_space_gb": 10,
        "cpu_cores": 2,
        "python_version": "3.8.0"
    }
    
    # Recommended requirements
    RECOMMENDED_REQUIREMENTS = {
        "ram_gb": 16,
        "disk_space_gb": 50,
        "cpu_cores": 4,
        "python_version": "3.9.0"
    }
    
    # Optimal requirements
    OPTIMAL_REQUIREMENTS = {
        "ram_gb": 32,
        "disk_space_gb": 100,
        "cpu_cores": 8,
        "python_version": "3.10.0"
    }
    
    def __init__(self):
        """Initialize the system checker"""
        self.system_info = self._collect_system_info()
        self.requirements_met = self._check_requirements()
        self.recommendations = self._generate_recommendations()
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        info = {}
        
        # OS information
        info["os"] = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
        
        # Python information
        info["python"] = {
            "version": platform.python_version(),
            "version_info": platform.python_version_tuple(),
            "executable": sys.executable
        }
        
        # CPU information
        info["cpu"] = {
            "cores_physical": multiprocessing.cpu_count(),
            "cores_logical": os.cpu_count() or multiprocessing.cpu_count()
        }
        
        # Memory information
        try:
            import psutil
            memory = psutil.virtual_memory()
            info["memory"] = {
                "total_gb": round(memory.total / (1024 ** 3), 2),
                "available_gb": round(memory.available / (1024 ** 3), 2),
                "used_gb": round(memory.used / (1024 ** 3), 2),
                "percent_used": memory.percent
            }
        except ImportError:
            logger.warning("psutil not available, memory information will be limited")
            info["memory"] = {
                "total_gb": 0,
                "available_gb": 0,
                "used_gb": 0,
                "percent_used": 0
            }
        
        # Disk information
        try:
            disk_usage = os.statvfs('/')
            total_disk = disk_usage.f_frsize * disk_usage.f_blocks
            free_disk = disk_usage.f_frsize * disk_usage.f_bavail
            used_disk = disk_usage.f_frsize * (disk_usage.f_blocks - disk_usage.f_bavail)
            
            info["disk"] = {
                "total_gb": round(total_disk / (1024 ** 3), 2),
                "free_gb": round(free_disk / (1024 ** 3), 2),
                "used_gb": round(used_disk / (1024 ** 3), 2),
                "percent_used": round(used_disk / total_disk * 100, 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get disk information: {e}")
            info["disk"] = {
                "total_gb": 0,
                "free_gb": 0,
                "used_gb": 0,
                "percent_used": 0
            }
        
        # GPU information
        info["gpu"] = self._get_gpu_info()
        
        return info
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        gpu_info = {
            "available": False,
            "vendor": None,
            "model": None,
            "memory_gb": 0,
            "cuda_support": False,
            "cuda_version": None,
            "metal_support": False
        }
        
        # Check for NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            if result.returncode == 0:
                gpu_info["available"] = True
                gpu_info["vendor"] = "NVIDIA"
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        gpu_info["model"] = parts[0].strip()
                        gpu_info["memory_gb"] = int(parts[1].strip())
                
                # Check CUDA version
                try:
                    result = subprocess.run(
                        ["nvcc", "--version"],
                        capture_output=True, text=True, check=True
                    )
                    if result.returncode == 0:
                        # Extract version from output
                        for line in result.stdout.split('\n'):
                            if "release" in line:
                                version = line.split("release")[-1].split(",")[0].strip()
                                gpu_info["cuda_version"] = version
                                gpu_info["cuda_support"] = True
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Check for AMD GPU (Linux)
        if not gpu_info["available"] and platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["lspci", "-nn", "-d", "1002:"],
                    capture_output=True, text=True, check=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    gpu_info["available"] = True
                    gpu_info["vendor"] = "AMD"
                    # Extract model info from output
                    for line in result.stdout.split('\n'):
                        if "VGA" in line:
                            model = line.split(":")[-1].strip().split(" [")[0]
                            gpu_info["model"] = model
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        # Check for Metal support (macOS)
        if not gpu_info["available"] and platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True, check=True
                )
                if result.returncode == 0:
                    gpu_info["available"] = True
                    gpu_info["vendor"] = "Apple"
                    gpu_info["metal_support"] = True
                    
                    # Extract model info
                    for line in result.stdout.split('\n'):
                        if "Chipset Model:" in line:
                            gpu_info["model"] = line.split(":")[-1].strip()
                        elif "VRAM (Total):" in line:
                            vram = line.split(":")[-1].strip()
                            if "GB" in vram:
                                gpu_info["memory_gb"] = int(vram.replace(" GB", ""))
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        
        return gpu_info
    
    def _check_requirements(self) -> Dict[str, Dict[str, bool]]:
        """Check if system meets requirements"""
        requirements_met = {
            "minimum": {},
            "recommended": {},
            "optimal": {}
        }
        
        # Check RAM
        ram_gb = self.system_info["memory"]["total_gb"]
        requirements_met["minimum"]["ram"] = ram_gb >= self.MINIMUM_REQUIREMENTS["ram_gb"]
        requirements_met["recommended"]["ram"] = ram_gb >= self.RECOMMENDED_REQUIREMENTS["ram_gb"]
        requirements_met["optimal"]["ram"] = ram_gb >= self.OPTIMAL_REQUIREMENTS["ram_gb"]
        
        # Check disk space
        disk_gb = self.system_info["disk"]["free_gb"]
        requirements_met["minimum"]["disk"] = disk_gb >= self.MINIMUM_REQUIREMENTS["disk_space_gb"]
        requirements_met["recommended"]["disk"] = disk_gb >= self.RECOMMENDED_REQUIREMENTS["disk_space_gb"]
        requirements_met["optimal"]["disk"] = disk_gb >= self.OPTIMAL_REQUIREMENTS["disk_space_gb"]
        
        # Check CPU cores
        cpu_cores = self.system_info["cpu"]["cores_physical"]
        requirements_met["minimum"]["cpu"] = cpu_cores >= self.MINIMUM_REQUIREMENTS["cpu_cores"]
        requirements_met["recommended"]["cpu"] = cpu_cores >= self.RECOMMENDED_REQUIREMENTS["cpu_cores"]
        requirements_met["optimal"]["cpu"] = cpu_cores >= self.OPTIMAL_REQUIREMENTS["cpu_cores"]
        
        # Check Python version
        py_version = self.system_info["python"]["version"]
        py_version_tuple = tuple(map(int, py_version.split('.')))
        min_version = tuple(map(int, self.MINIMUM_REQUIREMENTS["python_version"].split('.')))
        rec_version = tuple(map(int, self.RECOMMENDED_REQUIREMENTS["python_version"].split('.')))
        opt_version = tuple(map(int, self.OPTIMAL_REQUIREMENTS["python_version"].split('.')))
        
        requirements_met["minimum"]["python"] = py_version_tuple >= min_version
        requirements_met["recommended"]["python"] = py_version_tuple >= rec_version
        requirements_met["optimal"]["python"] = py_version_tuple >= opt_version
        
        return requirements_met
    
    def _generate_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations based on system capabilities"""
        recommendations = {
            "overall": "minimum",
            "model_size": "small",
            "installation_method": "cpu",
            "performance_settings": {
                "num_threads": self.system_info["cpu"]["cores_physical"],
                "batch_size": 128,
                "context_window": 2048,
                "low_vram": True
            },
            "hardware_upgrades": [],
            "configuration_changes": []
        }
        
        # Determine overall system capability
        if all(self.requirements_met["optimal"].values()):
            recommendations["overall"] = "optimal"
            recommendations["model_size"] = "large"
            recommendations["performance_settings"]["batch_size"] = 512
            recommendations["performance_settings"]["context_window"] = 4096
            recommendations["performance_settings"]["low_vram"] = False
        elif all(self.requirements_met["recommended"].values()):
            recommendations["overall"] = "recommended"
            recommendations["model_size"] = "medium"
            recommendations["performance_settings"]["batch_size"] = 256
            recommendations["performance_settings"]["context_window"] = 3072
            recommendations["performance_settings"]["low_vram"] = False
        
        # Check GPU capabilities
        if self.system_info["gpu"]["available"]:
            if self.system_info["gpu"]["vendor"] == "NVIDIA" and self.system_info["gpu"]["cuda_support"]:
                recommendations["installation_method"] = "cuda"
                recommendations["performance_settings"]["low_vram"] = False
            elif self.system_info["gpu"]["vendor"] == "Apple" and self.system_info["gpu"]["metal_support"]:
                recommendations["installation_method"] = "metal"
                recommendations["performance_settings"]["low_vram"] = False
        
        # Generate hardware upgrade recommendations
        if not self.requirements_met["minimum"]["ram"]:
            recommendations["hardware_upgrades"].append("Upgrade RAM to at least 4GB")
        elif not self.requirements_met["recommended"]["ram"]:
            recommendations["hardware_upgrades"].append("Consider upgrading RAM to 16GB for better performance")
        elif not self.requirements_met["optimal"]["ram"]:
            recommendations["hardware_upgrades"].append("Consider upgrading RAM to 32GB for optimal performance")
        
        if not self.requirements_met["minimum"]["disk"]:
            recommendations["hardware_upgrades"].append("Free up at least 10GB of disk space")
        elif not self.requirements_met["recommended"]["disk"]:
            recommendations["hardware_upgrades"].append("Consider having at least 50GB of free disk space")
        elif not self.requirements_met["optimal"]["disk"]:
            recommendations["hardware_upgrades"].append("Consider having at least 100GB of free disk space")
        
        if not self.requirements_met["minimum"]["cpu"]:
            recommendations["hardware_upgrades"].append("Consider upgrading to a CPU with at least 2 cores")
        elif not self.requirements_met["recommended"]["cpu"]:
            recommendations["hardware_upgrades"].append("Consider upgrading to a CPU with at least 4 cores")
        elif not self.requirements_met["optimal"]["cpu"]:
            recommendations["hardware_upgrades"].append("Consider upgrading to a CPU with at least 8 cores")
        
        # Generate configuration recommendations
        if recommendations["installation_method"] == "cpu":
            recommendations["configuration_changes"].append("Use CPU-only installation method")
        elif recommendations["installation_method"] == "cuda":
            recommendations["configuration_changes"].append("Use CUDA installation method for GPU acceleration")
            if self.system_info["gpu"]["cuda_version"]:
                recommendations["configuration_changes"].append(f"CUDA version {self.system_info['gpu']['cuda_version']} detected")
        elif recommendations["installation_method"] == "metal":
            recommendations["configuration_changes"].append("Use Metal installation method for GPU acceleration")
        
        # Adjust settings based on available memory
        if self.system_info["memory"]["total_gb"] < 8:
            recommendations["configuration_changes"].append("Reduce batch size to 64 for systems with low memory")
            recommendations["performance_settings"]["batch_size"] = 64
        
        return recommendations
    
    def _show_header(self) -> None:
        """Display the checker header"""
        print("=" * 60)
        print("    System Requirements Checker")
        print("=" * 60)
        print()
        print("This tool checks your system's capabilities")
        print("and provides recommendations for llama.cpp.")
        print()
    
    def _clear_screen(self) -> None:
        """Clear the terminal screen"""
        os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    def display_system_info(self) -> None:
        """Display system information"""
        print("System Information:")
        print("-" * 40)
        
        # OS information
        print(f"Operating System: {self.system_info['os']['system']} {self.system_info['os']['release']}")
        print(f"Architecture: {self.system_info['os']['machine']}")
        print()
        
        # Python information
        print(f"Python Version: {self.system_info['python']['version']}")
        print(f"Python Executable: {self.system_info['python']['executable']}")
        print()
        
        # CPU information
        print(f"CPU Cores (Physical): {self.system_info['cpu']['cores_physical']}")
        print(f"CPU Cores (Logical): {self.system_info['cpu']['cores_logical']}")
        print()
        
        # Memory information
        print(f"Total RAM: {self.system_info['memory']['total_gb']} GB")
        print(f"Available RAM: {self.system_info['memory']['available_gb']} GB")
        print(f"Used RAM: {self.system_info['memory']['percent_used']}%")
        print()
        
        # Disk information
        print(f"Total Disk Space: {self.system_info['disk']['total_gb']} GB")
        print(f"Free Disk Space: {self.system_info['disk']['free_gb']} GB")
        print(f"Used Disk Space: {self.system_info['disk']['percent_used']}%")
        print()
        
        # GPU information
        if self.system_info['gpu']['available']:
            print(f"GPU Vendor: {self.system_info['gpu']['vendor']}")
            print(f"GPU Model: {self.system_info['gpu']['model']}")
            print(f"GPU Memory: {self.system_info['gpu']['memory_gb']} GB")
            
            if self.system_info['gpu']['cuda_support']:
                print(f"CUDA Support: Yes (Version {self.system_info['gpu']['cuda_version']})")
            else:
                print("CUDA Support: No")
            
            if self.system_info['gpu']['metal_support']:
                print("Metal Support: Yes")
            else:
                print("Metal Support: No")
        else:
            print("No compatible GPU detected")
        
        print()
    
    def display_requirements_check(self) -> None:
        """Display requirements check results"""
        print("Requirements Check:")
        print("-" * 40)
        
        # RAM
        print(f"RAM: {self.system_info['memory']['total_gb']} GB")
        print(f"  Minimum ({self.MINIMUM_REQUIREMENTS['ram_gb']} GB): {'✓' if self.requirements_met['minimum']['ram'] else '✗'}")
        print(f"  Recommended ({self.RECOMMENDED_REQUIREMENTS['ram_gb']} GB): {'✓' if self.requirements_met['recommended']['ram'] else '✗'}")
        print(f"  Optimal ({self.OPTIMAL_REQUIREMENTS['ram_gb']} GB): {'✓' if self.requirements_met['optimal']['ram'] else '✗'}")
        print()
        
        # Disk
        print(f"Disk Space: {self.system_info['disk']['free_gb']} GB")
        print(f"  Minimum ({self.MINIMUM_REQUIREMENTS['disk_space_gb']} GB): {'✓' if self.requirements_met['minimum']['disk'] else '✗'}")
        print(f"  Recommended ({self.RECOMMENDED_REQUIREMENTS['disk_space_gb']} GB): {'✓' if self.requirements_met['recommended']['disk'] else '✗'}")
        print(f"  Optimal ({self.OPTIMAL_REQUIREMENTS['disk_space_gb']} GB): {'✓' if self.requirements_met['optimal']['disk'] else '✗'}")
        print()
        
        # CPU
        print(f"CPU Cores: {self.system_info['cpu']['cores_physical']}")
        print(f"  Minimum ({self.MINIMUM_REQUIREMENTS['cpu_cores']}): {'✓' if self.requirements_met['minimum']['cpu'] else '✗'}")
        print(f"  Recommended ({self.RECOMMENDED_REQUIREMENTS['cpu_cores']}): {'✓' if self.requirements_met['recommended']['cpu'] else '✗'}")
        print(f"  Optimal ({self.OPTIMAL_REQUIREMENTS['cpu_cores']}): {'✓' if self.requirements_met['optimal']['cpu'] else '✗'}")
        print()
        
        # Python
        print(f"Python Version: {self.system_info['python']['version']}")
        print(f"  Minimum ({self.MINIMUM_REQUIREMENTS['python_version']}): {'✓' if self.requirements_met['minimum']['python'] else '✗'}")
        print(f"  Recommended ({self.RECOMMENDED_REQUIREMENTS['python_version']}): {'✓' if self.requirements_met['recommended']['python'] else '✗'}")
        print(f"  Optimal ({self.OPTIMAL_REQUIREMENTS['python_version']}): {'✓' if self.requirements_met['optimal']['python'] else '✗'}")
        print()
    
    def display_recommendations(self) -> None:
        """Display recommendations"""
        print("Recommendations:")
        print("-" * 40)
        
        print(f"Overall System Capability: {self.recommendations['overall'].upper()}")
        print(f"Recommended Model Size: {self.recommendations['model_size'].upper()}")
        print(f"Recommended Installation Method: {self.recommendations['installation_method'].upper()}")
        print()
        
        print("Performance Settings:")
        print(f"  Number of Threads: {self.recommendations['performance_settings']['num_threads']}")
        print(f"  Batch Size: {self.recommendations['performance_settings']['batch_size']}")
        print(f"  Context Window: {self.recommendations['performance_settings']['context_window']}")
        print(f"  Low VRAM Mode: {'Enabled' if self.recommendations['performance_settings']['low_vram'] else 'Disabled'}")
        print()
        
        if self.recommendations['hardware_upgrades']:
            print("Hardware Upgrade Recommendations:")
            for upgrade in self.recommendations['hardware_upgrades']:
                print(f"  - {upgrade}")
            print()
        
        if self.recommendations['configuration_changes']:
            print("Configuration Recommendations:")
            for change in self.recommendations['configuration_changes']:
                print(f"  - {change}")
            print()
    
    def save_report(self, file_path: str) -> bool:
        """Save system report to file"""
        report = {
            "system_info": self.system_info,
            "requirements_met": self.requirements_met,
            "recommendations": self.recommendations
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"System report saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save system report: {e}")
            return False
    
    def apply_recommendations(self) -> bool:
        """Apply recommendations to configuration"""
        if not CONFIG_MANAGER_AVAILABLE:
            print("Configuration manager not available. Cannot apply recommendations automatically.")
            return False
        
        try:
            if ConfigManager:
                config_manager = ConfigManager()
            else:
                print("ConfigManager not available. Cannot apply recommendations.")
                return False
            
            # Apply performance settings
            config_manager.set("performance.num_threads", self.recommendations["performance_settings"]["num_threads"])
            config_manager.set("performance.batch_size", self.recommendations["performance_settings"]["batch_size"])
            config_manager.set("performance.context_window", self.recommendations["performance_settings"]["context_window"])
            config_manager.set("performance.low_vram", self.recommendations["performance_settings"]["low_vram"])
            
            # Apply installation method
            if self.recommendations["installation_method"] == "cuda":
                config_manager.set("installation.install_method", "pip-cuda")
            elif self.recommendations["installation_method"] == "metal":
                config_manager.set("installation.install_method", "pip-metal")
            else:
                config_manager.set("installation.install_method", "pip")
            
            config_manager.save_config()
            print("Recommendations applied to configuration successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to apply recommendations: {e}")
            return False
    
    def run(self) -> bool:
        """Run the system checker"""
        self._clear_screen()
        self._show_header()
        
        # Display system information
        self.display_system_info()
        
        # Display requirements check
        self.display_requirements_check()
        
        # Display recommendations
        self.display_recommendations()
        
        # Ask user if they want to save report
        save_report = input("Save system report to file? (y/n): ").lower() == 'y'
        if save_report:
            file_path = input("Enter file path (default: system_report.json): ") or "system_report.json"
            self.save_report(file_path)
        
        # Ask user if they want to apply recommendations
        apply_recs = input("Apply recommendations to configuration? (y/n): ").lower() == 'y'
        if apply_recs:
            self.apply_recommendations()
        
        input("\nPress Enter to continue...")
        return True


def main():
    """Main entry point"""
    checker = SystemChecker()
    checker.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())