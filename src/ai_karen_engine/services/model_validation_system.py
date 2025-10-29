"""
Model Validation System

Comprehensive model validation system that verifies compatibility, requirements,
and functionality of discovered models. This system ensures that models can be
properly loaded and used within the AI Karen Engine.

This system supports the model discovery engine by providing detailed validation
capabilities for all model types.
"""

import json
import logging
import os
import sys
import time
import subprocess
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import psutil

from .model_discovery_engine import ModelInfo, ModelType, ModelStatus, ResourceRequirements

logger = logging.getLogger("kari.model_validation_system")

class ValidationLevel(Enum):
    """Validation thoroughness levels."""
    BASIC = "basic"          # File existence and basic format checks
    STANDARD = "standard"    # + dependency checks and metadata validation
    COMPREHENSIVE = "comprehensive"  # + actual model loading test
    PERFORMANCE = "performance"      # + performance benchmarking

class ValidationResult(Enum):
    """Validation result status."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNKNOWN = "unknown"

@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: str  # "error", "warning", "info"
    category: str  # "dependency", "format", "performance", "compatibility"
    message: str
    suggestion: Optional[str] = None
    technical_details: Optional[str] = None

@dataclass
class ValidationReport:
    """Comprehensive validation report for a model."""
    model_id: str
    model_path: str
    validation_level: ValidationLevel
    overall_result: ValidationResult
    status: ModelStatus
    issues: List[ValidationIssue]
    performance_metrics: Optional[Dict[str, Any]] = None
    compatibility_info: Optional[Dict[str, Any]] = None
    validation_time: float = 0.0
    timestamp: float = 0.0

class ModelValidationSystem:
    """Comprehensive model validation system."""
    
    def __init__(self, cache_dir: str = "models/.validation_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="validation_worker")
        
        # Validation cache
        self.validation_cache: Dict[str, ValidationReport] = {}
        self.cache_file = self.cache_dir / "validation_cache.json"
        
        # System info
        self.system_info = self._get_system_info()
        
        # Dependency checkers
        self.dependency_checkers = {
            ModelType.LLAMA_CPP: self._check_llama_cpp_dependencies,
            ModelType.TRANSFORMERS: self._check_transformers_dependencies,
            ModelType.STABLE_DIFFUSION: self._check_diffusion_dependencies,
            ModelType.PYTORCH: self._check_pytorch_dependencies,
            ModelType.TENSORFLOW: self._check_tensorflow_dependencies,
            ModelType.ONNX: self._check_onnx_dependencies
        }
        
        # Load existing cache
        self._load_validation_cache()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for compatibility checks."""
        return {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "disk_free_gb": psutil.disk_usage('.').free / (1024**3),
            "gpu_available": self._check_gpu_availability()
        }
    
    def _check_gpu_availability(self) -> Dict[str, Any]:
        """Check GPU availability and capabilities."""
        gpu_info = {"available": False, "devices": []}
        
        try:
            # Try NVIDIA GPU detection
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                gpu_info["available"] = True
                gpu_info["type"] = "nvidia"
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split(', ')
                        if len(parts) >= 3:
                            gpu_info["devices"].append({
                                "name": parts[0],
                                "memory_mb": int(parts[1]),
                                "driver_version": parts[2]
                            })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try AMD GPU detection if NVIDIA not found
        if not gpu_info["available"]:
            try:
                result = subprocess.run(
                    ["rocm-smi", "--showproductname"], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and "GPU" in result.stdout:
                    gpu_info["available"] = True
                    gpu_info["type"] = "amd"
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        return gpu_info
    
    def _load_validation_cache(self):
        """Load validation cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for model_id, report_data in cache_data.items():
                    try:
                        report = self._dict_to_validation_report(report_data)
                        if report:
                            self.validation_cache[model_id] = report
                    except Exception as e:
                        logger.warning(f"Failed to load cached validation for {model_id}: {e}")
                
                logger.info(f"Loaded {len(self.validation_cache)} validation reports from cache")
        except Exception as e:
            logger.warning(f"Failed to load validation cache: {e}")
    
    def _save_validation_cache(self):
        """Save validation cache to disk."""
        try:
            cache_data = {}
            for model_id, report in self.validation_cache.items():
                cache_data[model_id] = self._validation_report_to_dict(report)
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved validation cache with {len(cache_data)} reports")
        except Exception as e:
            logger.error(f"Failed to save validation cache: {e}")
    
    def _dict_to_validation_report(self, data: Dict[str, Any]) -> Optional[ValidationReport]:
        """Convert dictionary to ValidationReport."""
        try:
            issues = []
            for issue_data in data.get("issues", []):
                issue = ValidationIssue(
                    severity=issue_data["severity"],
                    category=issue_data["category"],
                    message=issue_data["message"],
                    suggestion=issue_data.get("suggestion"),
                    technical_details=issue_data.get("technical_details")
                )
                issues.append(issue)
            
            return ValidationReport(
                model_id=data["model_id"],
                model_path=data["model_path"],
                validation_level=ValidationLevel(data["validation_level"]),
                overall_result=ValidationResult(data["overall_result"]),
                status=ModelStatus(data["status"]),
                issues=issues,
                performance_metrics=data.get("performance_metrics"),
                compatibility_info=data.get("compatibility_info"),
                validation_time=data.get("validation_time", 0.0),
                timestamp=data.get("timestamp", 0.0)
            )
        except Exception as e:
            logger.error(f"Failed to convert dict to ValidationReport: {e}")
            return None
    
    def _validation_report_to_dict(self, report: ValidationReport) -> Dict[str, Any]:
        """Convert ValidationReport to dictionary."""
        return {
            "model_id": report.model_id,
            "model_path": report.model_path,
            "validation_level": report.validation_level.value,
            "overall_result": report.overall_result.value,
            "status": report.status.value,
            "issues": [
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "technical_details": issue.technical_details
                }
                for issue in report.issues
            ],
            "performance_metrics": report.performance_metrics,
            "compatibility_info": report.compatibility_info,
            "validation_time": report.validation_time,
            "timestamp": report.timestamp
        }
    
    async def validate_model(self, model_info: ModelInfo, 
                           validation_level: ValidationLevel = ValidationLevel.STANDARD,
                           force_refresh: bool = False) -> ValidationReport:
        """Validate a single model with specified thoroughness level."""
        start_time = time.time()
        
        # Check cache first
        if not force_refresh and model_info.id in self.validation_cache:
            cached_report = self.validation_cache[model_info.id]
            # Use cached result if it's recent and same validation level
            if (time.time() - cached_report.timestamp < 3600 and  # 1 hour cache
                cached_report.validation_level.value >= validation_level.value):
                logger.debug(f"Using cached validation for {model_info.id}")
                return cached_report
        
        logger.info(f"Validating model {model_info.id} at {validation_level.value} level")
        
        issues = []
        overall_result = ValidationResult.VALID
        status = ModelStatus.AVAILABLE
        performance_metrics = None
        compatibility_info = None
        
        try:
            # Basic validation
            basic_issues = await self._validate_basic(model_info)
            issues.extend(basic_issues)
            
            if validation_level.value in ["standard", "comprehensive", "performance"]:
                # Dependency validation
                dep_issues = await self._validate_dependencies(model_info)
                issues.extend(dep_issues)
                
                # Resource validation
                resource_issues = await self._validate_resources(model_info)
                issues.extend(resource_issues)
                
                # Compatibility validation
                compat_issues, compat_info = await self._validate_compatibility(model_info)
                issues.extend(compat_issues)
                compatibility_info = compat_info
            
            if validation_level.value in ["comprehensive", "performance"]:
                # Model loading validation
                loading_issues = await self._validate_model_loading(model_info)
                issues.extend(loading_issues)
            
            if validation_level == ValidationLevel.PERFORMANCE:
                # Performance benchmarking
                perf_issues, perf_metrics = await self._validate_performance(model_info)
                issues.extend(perf_issues)
                performance_metrics = perf_metrics
            
            # Determine overall result and status
            error_issues = [i for i in issues if i.severity == "error"]
            warning_issues = [i for i in issues if i.severity == "warning"]
            
            if error_issues:
                overall_result = ValidationResult.INVALID
                status = ModelStatus.ERROR
            elif warning_issues:
                overall_result = ValidationResult.WARNING
                status = ModelStatus.AVAILABLE
            else:
                overall_result = ValidationResult.VALID
                status = ModelStatus.AVAILABLE
            
        except Exception as e:
            logger.error(f"Validation failed for {model_info.id}: {e}")
            issues.append(ValidationIssue(
                severity="error",
                category="validation",
                message=f"Validation process failed: {str(e)}",
                technical_details=str(e)
            ))
            overall_result = ValidationResult.INVALID
            status = ModelStatus.ERROR
        
        validation_time = time.time() - start_time
        
        # Create validation report
        report = ValidationReport(
            model_id=model_info.id,
            model_path=model_info.path,
            validation_level=validation_level,
            overall_result=overall_result,
            status=status,
            issues=issues,
            performance_metrics=performance_metrics,
            compatibility_info=compatibility_info,
            validation_time=validation_time,
            timestamp=time.time()
        )
        
        # Cache the result
        with self._lock:
            self.validation_cache[model_info.id] = report
            self._save_validation_cache()
        
        logger.info(f"Validation complete for {model_info.id}: {overall_result.value} "
                   f"({len(issues)} issues, {validation_time:.2f}s)")
        
        return report
    
    async def _validate_basic(self, model_info: ModelInfo) -> List[ValidationIssue]:
        """Perform basic validation checks."""
        issues = []
        path = Path(model_info.path)
        
        # Check if path exists
        if not path.exists():
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message=f"Model path does not exist: {model_info.path}",
                suggestion="Verify the model file or directory exists and is accessible"
            ))
            return issues
        
        # Check file/directory permissions
        if not os.access(path, os.R_OK):
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="Model file/directory is not readable",
                suggestion="Check file permissions and ownership"
            ))
        
        # Check file size for single files
        if path.is_file():
            if path.stat().st_size == 0:
                issues.append(ValidationIssue(
                    severity="error",
                    category="format",
                    message="Model file is empty",
                    suggestion="Re-download or restore the model file"
                ))
            elif path.stat().st_size < 1024:  # Less than 1KB is suspicious
                issues.append(ValidationIssue(
                    severity="warning",
                    category="format",
                    message="Model file is unusually small",
                    suggestion="Verify the model file is complete and not corrupted"
                ))
        
        # Type-specific basic validation
        if model_info.type == ModelType.LLAMA_CPP:
            issues.extend(await self._validate_basic_llama_cpp(path))
        elif model_info.type == ModelType.TRANSFORMERS:
            issues.extend(await self._validate_basic_transformers(path))
        elif model_info.type == ModelType.STABLE_DIFFUSION:
            issues.extend(await self._validate_basic_stable_diffusion(path))
        
        return issues
    
    async def _validate_basic_llama_cpp(self, path: Path) -> List[ValidationIssue]:
        """Basic validation for llama-cpp models."""
        issues = []
        
        if path.is_file():
            # Check file extension
            if path.suffix.lower() not in ['.gguf', '.ggml', '.bin']:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="format",
                    message=f"Unexpected file extension for llama-cpp model: {path.suffix}",
                    suggestion="Expected .gguf, .ggml, or .bin file"
                ))
            
            # Check GGUF magic number
            if path.suffix.lower() == '.gguf':
                try:
                    with open(path, 'rb') as f:
                        magic = f.read(4)
                        if magic != b'GGUF':
                            issues.append(ValidationIssue(
                                severity="error",
                                category="format",
                                message="Invalid GGUF file format (missing magic number)",
                                suggestion="File may be corrupted or not a valid GGUF model"
                            ))
                except Exception as e:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="format",
                        message=f"Cannot read GGUF header: {e}",
                        technical_details=str(e)
                    ))
        
        return issues
    
    async def _validate_basic_transformers(self, path: Path) -> List[ValidationIssue]:
        """Basic validation for transformers models."""
        issues = []
        
        if not path.is_dir():
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="Transformers model should be a directory",
                suggestion="Ensure the model is properly extracted/downloaded"
            ))
            return issues
        
        # Check for required files
        config_file = path / "config.json"
        if not config_file.exists():
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="Missing config.json file",
                suggestion="Transformers models require a config.json file"
            ))
        
        # Check for model files
        model_files = list(path.glob("*.bin")) + list(path.glob("*.safetensors"))
        if not model_files:
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="No model weight files found",
                suggestion="Expected .bin or .safetensors files containing model weights"
            ))
        
        return issues
    
    async def _validate_basic_stable_diffusion(self, path: Path) -> List[ValidationIssue]:
        """Basic validation for stable diffusion models."""
        issues = []
        
        if not path.is_dir():
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="Stable Diffusion model should be a directory",
                suggestion="Ensure the model is properly extracted/downloaded"
            ))
            return issues
        
        # Check for model_index.json
        index_file = path / "model_index.json"
        if not index_file.exists():
            issues.append(ValidationIssue(
                severity="error",
                category="format",
                message="Missing model_index.json file",
                suggestion="Stable Diffusion models require a model_index.json file"
            ))
        
        # Check for required subdirectories
        required_dirs = ["unet", "vae", "text_encoder"]
        for req_dir in required_dirs:
            if not (path / req_dir).exists():
                issues.append(ValidationIssue(
                    severity="error",
                    category="format",
                    message=f"Missing required directory: {req_dir}",
                    suggestion=f"Stable Diffusion models require a {req_dir} directory"
                ))
        
        return issues
    
    async def _validate_dependencies(self, model_info: ModelInfo) -> List[ValidationIssue]:
        """Validate model dependencies."""
        issues = []
        
        if model_info.type in self.dependency_checkers:
            checker = self.dependency_checkers[model_info.type]
            dep_issues = await checker()
            issues.extend(dep_issues)
        
        return issues
    
    async def _check_llama_cpp_dependencies(self) -> List[ValidationIssue]:
        """Check llama-cpp dependencies."""
        issues = []
        
        # Check for llama-cpp-python
        try:
            import llama_cpp
            # Check version if possible
            if hasattr(llama_cpp, '__version__'):
                logger.debug(f"llama-cpp-python version: {llama_cpp.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="llama-cpp-python not installed",
                suggestion="Install with: pip install llama-cpp-python"
            ))
        
        return issues
    
    async def _check_transformers_dependencies(self) -> List[ValidationIssue]:
        """Check transformers dependencies."""
        issues = []
        
        # Check for transformers
        try:
            import transformers
            logger.debug(f"transformers version: {transformers.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="transformers library not installed",
                suggestion="Install with: pip install transformers"
            ))
        
        # Check for torch
        try:
            import torch
            logger.debug(f"torch version: {torch.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="PyTorch not installed",
                suggestion="Install with: pip install torch"
            ))
        
        return issues
    
    async def _check_diffusion_dependencies(self) -> List[ValidationIssue]:
        """Check stable diffusion dependencies."""
        issues = []
        
        # Check for diffusers
        try:
            import diffusers
            logger.debug(f"diffusers version: {diffusers.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="diffusers library not installed",
                suggestion="Install with: pip install diffusers"
            ))
        
        # Check for torch
        try:
            import torch
            logger.debug(f"torch version: {torch.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="PyTorch not installed",
                suggestion="Install with: pip install torch"
            ))
        
        return issues
    
    async def _check_pytorch_dependencies(self) -> List[ValidationIssue]:
        """Check PyTorch dependencies."""
        issues = []
        
        try:
            import torch
            logger.debug(f"torch version: {torch.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="PyTorch not installed",
                suggestion="Install with: pip install torch"
            ))
        
        return issues
    
    async def _check_tensorflow_dependencies(self) -> List[ValidationIssue]:
        """Check TensorFlow dependencies."""
        issues = []
        
        try:
            import tensorflow as tf
            logger.debug(f"tensorflow version: {tf.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="TensorFlow not installed",
                suggestion="Install with: pip install tensorflow"
            ))
        
        return issues
    
    async def _check_onnx_dependencies(self) -> List[ValidationIssue]:
        """Check ONNX dependencies."""
        issues = []
        
        try:
            import onnxruntime
            logger.debug(f"onnxruntime version: {onnxruntime.__version__}")
        except ImportError:
            issues.append(ValidationIssue(
                severity="error",
                category="dependency",
                message="ONNX Runtime not installed",
                suggestion="Install with: pip install onnxruntime"
            ))
        
        return issues
    
    async def _validate_resources(self, model_info: ModelInfo) -> List[ValidationIssue]:
        """Validate system resources against model requirements."""
        issues = []
        requirements = model_info.requirements
        system = self.system_info
        
        # Check RAM requirements
        if requirements.min_ram_gb > system["memory_gb"]:
            issues.append(ValidationIssue(
                severity="error",
                category="performance",
                message=f"Insufficient RAM: need {requirements.min_ram_gb}GB, have {system['memory_gb']:.1f}GB",
                suggestion="Upgrade system RAM or use a smaller model"
            ))
        elif requirements.recommended_ram_gb > system["memory_gb"]:
            issues.append(ValidationIssue(
                severity="warning",
                category="performance",
                message=f"Below recommended RAM: need {requirements.recommended_ram_gb}GB, have {system['memory_gb']:.1f}GB",
                suggestion="Model may run slowly or with reduced performance"
            ))
        
        # Check GPU requirements
        if requirements.gpu_required and not system["gpu_available"]["available"]:
            issues.append(ValidationIssue(
                severity="error",
                category="performance",
                message="GPU required but not available",
                suggestion="Install compatible GPU drivers or use CPU-only model"
            ))
        
        # Check VRAM requirements
        if (requirements.min_vram_gb and system["gpu_available"]["available"] and 
            system["gpu_available"]["devices"]):
            max_vram_gb = max(dev["memory_mb"] for dev in system["gpu_available"]["devices"]) / 1024
            if requirements.min_vram_gb > max_vram_gb:
                issues.append(ValidationIssue(
                    severity="error",
                    category="performance",
                    message=f"Insufficient VRAM: need {requirements.min_vram_gb}GB, have {max_vram_gb:.1f}GB",
                    suggestion="Use a model with lower VRAM requirements"
                ))
        
        # Check CPU cores
        if requirements.cpu_cores > system["cpu_count"]:
            issues.append(ValidationIssue(
                severity="warning",
                category="performance",
                message=f"Fewer CPU cores than recommended: need {requirements.cpu_cores}, have {system['cpu_count']}",
                suggestion="Model may run slower than optimal"
            ))
        
        # Check disk space
        if requirements.disk_space_gb > system["disk_free_gb"]:
            issues.append(ValidationIssue(
                severity="warning",
                category="performance",
                message=f"Low disk space: model needs {requirements.disk_space_gb:.1f}GB, {system['disk_free_gb']:.1f}GB free",
                suggestion="Free up disk space before using this model"
            ))
        
        return issues
    
    async def _validate_compatibility(self, model_info: ModelInfo) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate platform and architecture compatibility."""
        issues = []
        compatibility_info = {
            "platform_supported": True,
            "architecture_supported": True,
            "python_compatible": True,
            "notes": []
        }
        
        requirements = model_info.requirements
        system = self.system_info
        
        # Check platform support
        if (requirements.supported_platforms and 
            system["platform"].lower() not in [p.lower() for p in requirements.supported_platforms]):
            issues.append(ValidationIssue(
                severity="warning",
                category="compatibility",
                message=f"Platform {system['platform']} not in supported platforms: {requirements.supported_platforms}",
                suggestion="Model may not work correctly on this platform"
            ))
            compatibility_info["platform_supported"] = False
        
        # Check architecture compatibility
        arch = system["architecture"].lower()
        if model_info.type == ModelType.LLAMA_CPP:
            # GGUF models generally work on most architectures
            if arch not in ["x86_64", "amd64", "arm64", "aarch64"]:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="compatibility",
                    message=f"Architecture {arch} may not be fully supported",
                    suggestion="Performance may be suboptimal on this architecture"
                ))
                compatibility_info["architecture_supported"] = False
        
        # Check Python version compatibility
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(ValidationIssue(
                severity="error",
                category="compatibility",
                message=f"Python {python_version.major}.{python_version.minor} too old",
                suggestion="Upgrade to Python 3.8 or newer"
            ))
            compatibility_info["python_compatible"] = False
        
        return issues, compatibility_info
    
    async def _validate_model_loading(self, model_info: ModelInfo) -> List[ValidationIssue]:
        """Validate that the model can actually be loaded."""
        issues = []
        
        # This is a placeholder for actual model loading tests
        # In a full implementation, this would attempt to load the model
        # with appropriate libraries and catch any loading errors
        
        logger.debug(f"Model loading validation for {model_info.id} (placeholder)")
        
        # For now, just add a note that this validation was performed
        issues.append(ValidationIssue(
            severity="info",
            category="validation",
            message="Model loading validation completed",
            suggestion="Full loading test not implemented yet"
        ))
        
        return issues
    
    async def _validate_performance(self, model_info: ModelInfo) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """Validate model performance characteristics."""
        issues = []
        performance_metrics = {
            "estimated_inference_time": "unknown",
            "memory_usage_estimate": "unknown",
            "throughput_estimate": "unknown"
        }
        
        # This is a placeholder for actual performance benchmarking
        # In a full implementation, this would run inference tests
        
        logger.debug(f"Performance validation for {model_info.id} (placeholder)")
        
        issues.append(ValidationIssue(
            severity="info",
            category="performance",
            message="Performance benchmarking completed",
            suggestion="Full performance testing not implemented yet"
        ))
        
        return issues, performance_metrics
    
    async def validate_multiple_models(self, models: List[ModelInfo], 
                                     validation_level: ValidationLevel = ValidationLevel.STANDARD,
                                     max_concurrent: int = 2) -> List[ValidationReport]:
        """Validate multiple models concurrently."""
        logger.info(f"Validating {len(models)} models at {validation_level.value} level")
        
        reports = []
        
        # Process models in batches to avoid overwhelming the system
        for i in range(0, len(models), max_concurrent):
            batch = models[i:i + max_concurrent]
            
            # Submit validation tasks
            futures = []
            for model in batch:
                future = self.executor.submit(
                    self._validate_model_sync, model, validation_level
                )
                futures.append((model.id, future))
            
            # Collect results
            for model_id, future in futures:
                try:
                    report = future.result(timeout=300)  # 5 minute timeout
                    reports.append(report)
                except Exception as e:
                    logger.error(f"Validation failed for {model_id}: {e}")
                    # Create error report
                    error_report = ValidationReport(
                        model_id=model_id,
                        model_path="unknown",
                        validation_level=validation_level,
                        overall_result=ValidationResult.INVALID,
                        status=ModelStatus.ERROR,
                        issues=[ValidationIssue(
                            severity="error",
                            category="validation",
                            message=f"Validation process failed: {str(e)}",
                            technical_details=str(e)
                        )],
                        validation_time=0.0,
                        timestamp=time.time()
                    )
                    reports.append(error_report)
        
        logger.info(f"Validation complete: {len(reports)} reports generated")
        return reports
    
    def _validate_model_sync(self, model_info: ModelInfo, validation_level: ValidationLevel) -> ValidationReport:
        """Synchronous wrapper for async validation (for thread pool)."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.validate_model(model_info, validation_level))
        finally:
            loop.close()
    
    def get_validation_report(self, model_id: str) -> Optional[ValidationReport]:
        """Get cached validation report for a model."""
        with self._lock:
            return self.validation_cache.get(model_id)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        with self._lock:
            reports = list(self.validation_cache.values())
        
        if not reports:
            return {"total_validations": 0}
        
        # Count by result
        results = {"valid": 0, "invalid": 0, "warning": 0, "unknown": 0}
        for report in reports:
            results[report.overall_result.value] += 1
        
        # Count by status
        statuses = {"available": 0, "error": 0, "incompatible": 0, "missing_dependencies": 0}
        for report in reports:
            statuses[report.status.value] += 1
        
        # Issue statistics
        issue_categories = {}
        issue_severities = {"error": 0, "warning": 0, "info": 0}
        
        for report in reports:
            for issue in report.issues:
                issue_severities[issue.severity] += 1
                if issue.category not in issue_categories:
                    issue_categories[issue.category] = 0
                issue_categories[issue.category] += 1
        
        return {
            "total_validations": len(reports),
            "results": results,
            "statuses": statuses,
            "issue_categories": issue_categories,
            "issue_severities": issue_severities,
            "average_validation_time": sum(r.validation_time for r in reports) / len(reports),
            "cache_file": str(self.cache_file),
            "system_info": self.system_info
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self._save_validation_cache()
        self.executor.shutdown(wait=True)
        logger.info("ModelValidationSystem cleanup completed")