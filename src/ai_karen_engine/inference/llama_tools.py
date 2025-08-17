"""
Llama.cpp Tools Integration

This module provides a wrapper for llama.cpp binary tools including quantization,
conversion, and LoRA merging capabilities. It handles tool discovery, execution,
and progress tracking for model operations.

Key Features:
- Wrapper for llama.cpp binary tools (quantize, convert, merge-lora)
- Graceful degradation when tools are unavailable
- Progress tracking and error handling for tool operations
- Support for multiple quantization formats
- Architecture detection for model conversion
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class QuantizationFormat:
    """Quantization format specification."""
    name: str
    description: str
    size_reduction: float  # Approximate size reduction factor
    quality: str  # high, medium, low
    speed: str  # fast, medium, slow
    memory_usage: str  # low, medium, high
    recommended_for: List[str] = field(default_factory=list)


@dataclass
class ConversionJob:
    """Model conversion job information."""
    id: str
    source_path: str
    target_path: str
    operation: str  # convert, quantize, merge_lora
    status: str = "queued"  # queued, running, completed, failed, cancelled
    progress: float = 0.0
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # Operation-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Process control
    _process: Optional[subprocess.Popen] = None
    _cancelled: bool = False


@dataclass
class ModelArchitecture:
    """Model architecture information."""
    name: str
    family: str
    supported_formats: List[str]
    conversion_args: List[str] = field(default_factory=list)
    notes: str = ""


# -----------------------------
# Quantization Formats
# -----------------------------

QUANTIZATION_FORMATS = {
    "Q2_K": QuantizationFormat(
        name="Q2_K",
        description="2-bit quantization with K-means clustering",
        size_reduction=0.25,
        quality="low",
        speed="fast",
        memory_usage="low",
        recommended_for=["memory_constrained", "mobile"]
    ),
    "Q3_K": QuantizationFormat(
        name="Q3_K", 
        description="3-bit quantization with K-means clustering",
        size_reduction=0.375,
        quality="medium",
        speed="fast",
        memory_usage="low",
        recommended_for=["balanced", "mobile"]
    ),
    "Q4_K_M": QuantizationFormat(
        name="Q4_K_M",
        description="4-bit quantization with K-means clustering (medium)",
        size_reduction=0.5,
        quality="high",
        speed="medium",
        memory_usage="medium",
        recommended_for=["general_use", "recommended"]
    ),
    "Q5_K_M": QuantizationFormat(
        name="Q5_K_M",
        description="5-bit quantization with K-means clustering (medium)",
        size_reduction=0.625,
        quality="high",
        speed="medium",
        memory_usage="medium",
        recommended_for=["quality_focused"]
    ),
    "Q6_K": QuantizationFormat(
        name="Q6_K",
        description="6-bit quantization with K-means clustering",
        size_reduction=0.75,
        quality="high",
        speed="slow",
        memory_usage="high",
        recommended_for=["quality_focused"]
    ),
    "Q8_0": QuantizationFormat(
        name="Q8_0",
        description="8-bit quantization",
        size_reduction=1.0,
        quality="high",
        speed="slow",
        memory_usage="high",
        recommended_for=["quality_focused", "testing"]
    ),
    "IQ2_M": QuantizationFormat(
        name="IQ2_M",
        description="Improved 2-bit quantization (medium)",
        size_reduction=0.25,
        quality="medium",
        speed="fast",
        memory_usage="low",
        recommended_for=["memory_constrained", "experimental"]
    ),
    "IQ3_M": QuantizationFormat(
        name="IQ3_M",
        description="Improved 3-bit quantization (medium)",
        size_reduction=0.375,
        quality="medium",
        speed="fast",
        memory_usage="low",
        recommended_for=["balanced", "experimental"]
    ),
    "IQ4_M": QuantizationFormat(
        name="IQ4_M",
        description="Improved 4-bit quantization (medium)",
        size_reduction=0.5,
        quality="high",
        speed="medium",
        memory_usage="medium",
        recommended_for=["experimental"]
    )
}

# -----------------------------
# Model Architectures
# -----------------------------

MODEL_ARCHITECTURES = {
    "llama": ModelArchitecture(
        name="llama",
        family="llama",
        supported_formats=["safetensors", "bin", "pth"],
        conversion_args=["--vocab-type", "spm"],
        notes="Standard Llama architecture"
    ),
    "llama2": ModelArchitecture(
        name="llama2",
        family="llama",
        supported_formats=["safetensors", "bin", "pth"],
        conversion_args=["--vocab-type", "spm"],
        notes="Llama 2 architecture"
    ),
    "codellama": ModelArchitecture(
        name="codellama",
        family="llama",
        supported_formats=["safetensors", "bin", "pth"],
        conversion_args=["--vocab-type", "spm"],
        notes="Code Llama architecture"
    ),
    "mistral": ModelArchitecture(
        name="mistral",
        family="mistral",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "spm"],
        notes="Mistral architecture"
    ),
    "mixtral": ModelArchitecture(
        name="mixtral",
        family="mistral",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "spm"],
        notes="Mixtral MoE architecture"
    ),
    "qwen": ModelArchitecture(
        name="qwen",
        family="qwen",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "bpe"],
        notes="Qwen architecture"
    ),
    "qwen2": ModelArchitecture(
        name="qwen2",
        family="qwen",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "bpe"],
        notes="Qwen 2 architecture"
    ),
    "phi": ModelArchitecture(
        name="phi",
        family="phi",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "bpe"],
        notes="Phi architecture"
    ),
    "phi3": ModelArchitecture(
        name="phi3",
        family="phi",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "bpe"],
        notes="Phi-3 architecture"
    ),
    "gemma": ModelArchitecture(
        name="gemma",
        family="gemma",
        supported_formats=["safetensors", "bin"],
        conversion_args=["--vocab-type", "spm"],
        notes="Gemma architecture"
    )
}


# -----------------------------
# Llama Tools Implementation
# -----------------------------

class LlamaTools:
    """
    Wrapper for llama.cpp binary tools.
    
    Provides high-level interface for model conversion, quantization,
    and LoRA merging operations using llama.cpp tools.
    """
    
    def __init__(self, bin_dir: Optional[Union[str, Path]] = None):
        """
        Initialize llama.cpp tools wrapper.
        
        Args:
            bin_dir: Directory containing llama.cpp binaries (auto-detected if None)
        """
        self.bin_dir = Path(bin_dir) if bin_dir else self._find_bin_dir()
        self._lock = threading.RLock()
        
        # Job management
        self._jobs: Dict[str, ConversionJob] = {}
        self._job_threads: Dict[str, threading.Thread] = {}
        
        # Tool availability cache
        self._tools_available: Optional[bool] = None
        self._available_tools: Set[str] = set()
        
        # Check tool availability
        self._check_tools()
    
    def _find_bin_dir(self) -> Optional[Path]:
        """Auto-detect llama.cpp binary directory."""
        # Common installation paths
        search_paths = [
            Path.home() / ".local" / "bin",
            Path("/usr/local/bin"),
            Path("/usr/bin"),
            Path("/opt/homebrew/bin"),  # macOS Homebrew
            Path.cwd() / "llama.cpp" / "build" / "bin",
            Path.cwd() / "build" / "bin",
        ]
        
        # Check environment variable
        if "LLAMA_CPP_BIN_DIR" in os.environ:
            search_paths.insert(0, Path(os.environ["LLAMA_CPP_BIN_DIR"]))
        
        # Look for llama-quantize binary as indicator
        for path in search_paths:
            if path.exists():
                quantize_bin = path / "llama-quantize"
                if quantize_bin.exists() or (quantize_bin.with_suffix(".exe")).exists():
                    logger.info(f"Found llama.cpp tools in: {path}")
                    return path
        
        logger.warning("llama.cpp tools not found in standard locations")
        return None
    
    def _check_tools(self) -> None:
        """Check availability of llama.cpp tools."""
        if not self.bin_dir or not self.bin_dir.exists():
            self._tools_available = False
            return
        
        # Tools to check for
        tools = {
            "quantize": ["llama-quantize", "llama-quantize.exe"],
            "convert": ["convert-hf-to-gguf.py", "convert.py"],
            "merge_lora": ["export-lora", "export-lora.exe"]
        }
        
        available_tools = set()
        
        for tool_name, possible_names in tools.items():
            for name in possible_names:
                tool_path = self.bin_dir / name
                if tool_path.exists():
                    available_tools.add(tool_name)
                    break
        
        self._available_tools = available_tools
        self._tools_available = len(available_tools) > 0
        
        if self._tools_available:
            logger.info(f"Available llama.cpp tools: {', '.join(available_tools)}")
        else:
            logger.warning("No llama.cpp tools found")
    
    # ---------- Tool Availability ----------
    
    def is_available(self) -> bool:
        """Check if llama.cpp tools are available."""
        return self._tools_available or False
    
    def available_tools(self) -> Set[str]:
        """Get set of available tools."""
        return self._available_tools.copy()
    
    def can_quantize(self) -> bool:
        """Check if quantization is available."""
        return "quantize" in self._available_tools
    
    def can_convert(self) -> bool:
        """Check if conversion is available."""
        return "convert" in self._available_tools
    
    def can_merge_lora(self) -> bool:
        """Check if LoRA merging is available."""
        return "merge_lora" in self._available_tools
    
    # ---------- Quantization ----------
    
    def quantize(self, 
                in_path: str, 
                out_path: str, 
                format: str = "Q4_K_M",
                allow_requantize: bool = False,
                **kwargs) -> ConversionJob:
        """
        Quantize a GGUF model.
        
        Args:
            in_path: Input GGUF model path
            out_path: Output quantized model path
            format: Quantization format (Q4_K_M, Q5_K_M, etc.)
            allow_requantize: Allow requantizing already quantized models
            **kwargs: Additional arguments
            
        Returns:
            Conversion job object
        """
        if not self.can_quantize():
            raise RuntimeError("Quantization tool not available")
        
        if format not in QUANTIZATION_FORMATS:
            raise ValueError(f"Unsupported quantization format: {format}")
        
        job_id = f"quantize_{int(time.time())}_{hash(in_path) % 10000}"
        
        job = ConversionJob(
            id=job_id,
            source_path=in_path,
            target_path=out_path,
            operation="quantize",
            parameters={
                "format": format,
                "allow_requantize": allow_requantize,
                **kwargs
            }
        )
        
        with self._lock:
            self._jobs[job_id] = job
        
        # Start quantization in background
        thread = threading.Thread(
            target=self._quantize_worker,
            args=(job,),
            daemon=True
        )
        
        with self._lock:
            self._job_threads[job_id] = thread
        
        thread.start()
        
        logger.info(f"Started quantization job {job_id}: {in_path} -> {out_path} ({format})")
        return job
    
    def _quantize_worker(self, job: ConversionJob) -> None:
        """Worker function for quantization."""
        try:
            job.status = "running"
            job.started_at = time.time()
            
            # Find quantization tool
            quantize_bin = None
            for name in ["llama-quantize", "llama-quantize.exe"]:
                tool_path = self.bin_dir / name
                if tool_path.exists():
                    quantize_bin = tool_path
                    break
            
            if not quantize_bin:
                raise RuntimeError("Quantization binary not found")
            
            # Build command
            cmd = [
                str(quantize_bin),
                job.source_path,
                job.target_path,
                job.parameters["format"]
            ]
            
            if job.parameters.get("allow_requantize", False):
                cmd.append("--allow-requantize")
            
            # Add any additional arguments
            for key, value in job.parameters.items():
                if key not in ["format", "allow_requantize"] and value is not None:
                    if isinstance(value, bool) and value:
                        cmd.append(f"--{key}")
                    elif not isinstance(value, bool):
                        cmd.extend([f"--{key}", str(value)])
            
            job.logs.append(f"Running command: {' '.join(cmd)}")
            
            # Run quantization
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            job._process = process
            
            # Monitor progress
            while True:
                if job._cancelled:
                    process.terminate()
                    job.status = "cancelled"
                    break
                
                output = process.stdout.readline()
                if output:
                    line = output.strip()
                    job.logs.append(line)
                    
                    # Try to extract progress information
                    self._parse_quantize_progress(job, line)
                
                if process.poll() is not None:
                    break
            
            # Get final output
            remaining_output, _ = process.communicate()
            if remaining_output:
                for line in remaining_output.strip().split('\n'):
                    if line.strip():
                        job.logs.append(line.strip())
            
            if process.returncode == 0 and not job._cancelled:
                job.status = "completed"
                job.progress = 1.0
                job.completed_at = time.time()
                logger.info(f"Quantization completed: {job.id}")
            else:
                job.status = "failed"
                job.error = f"Process exited with code {process.returncode}"
                job.completed_at = time.time()
                logger.error(f"Quantization failed: {job.id} - {job.error}")
        
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
            logger.error(f"Quantization error: {job.id} - {e}")
        
        finally:
            job._process = None
            with self._lock:
                self._job_threads.pop(job.id, None)
    
    def _parse_quantize_progress(self, job: ConversionJob, line: str) -> None:
        """Parse progress information from quantization output."""
        # llama-quantize doesn't provide detailed progress, so we estimate
        if "quantizing" in line.lower():
            job.progress = 0.5  # Rough estimate
        elif "done" in line.lower() or "finished" in line.lower():
            job.progress = 0.9
    
    # ---------- Model Conversion ----------
    
    def convert_hf_to_gguf(self, 
                          hf_dir: str, 
                          out_path: str,
                          architecture: Optional[str] = None,
                          vocab_only: bool = False,
                          **kwargs) -> ConversionJob:
        """
        Convert HuggingFace model to GGUF format.
        
        Args:
            hf_dir: HuggingFace model directory
            out_path: Output GGUF file path
            architecture: Model architecture (auto-detected if None)
            vocab_only: Convert vocabulary only
            **kwargs: Additional conversion arguments
            
        Returns:
            Conversion job object
        """
        if not self.can_convert():
            raise RuntimeError("Conversion tool not available")
        
        # Auto-detect architecture if not provided
        if not architecture:
            architecture = self._detect_architecture(hf_dir)
        
        job_id = f"convert_{int(time.time())}_{hash(hf_dir) % 10000}"
        
        job = ConversionJob(
            id=job_id,
            source_path=hf_dir,
            target_path=out_path,
            operation="convert",
            parameters={
                "architecture": architecture,
                "vocab_only": vocab_only,
                **kwargs
            }
        )
        
        with self._lock:
            self._jobs[job_id] = job
        
        # Start conversion in background
        thread = threading.Thread(
            target=self._convert_worker,
            args=(job,),
            daemon=True
        )
        
        with self._lock:
            self._job_threads[job_id] = thread
        
        thread.start()
        
        logger.info(f"Started conversion job {job_id}: {hf_dir} -> {out_path}")
        return job
    
    def _convert_worker(self, job: ConversionJob) -> None:
        """Worker function for model conversion."""
        try:
            job.status = "running"
            job.started_at = time.time()
            
            # Find conversion script
            convert_script = None
            for name in ["convert-hf-to-gguf.py", "convert.py"]:
                script_path = self.bin_dir / name
                if script_path.exists():
                    convert_script = script_path
                    break
            
            if not convert_script:
                raise RuntimeError("Conversion script not found")
            
            # Build command
            cmd = ["python", str(convert_script)]
            
            # Add source directory
            cmd.append(job.source_path)
            
            # Add output path
            cmd.extend(["--outfile", job.target_path])
            
            # Add architecture-specific arguments
            architecture = job.parameters.get("architecture")
            if architecture and architecture in MODEL_ARCHITECTURES:
                arch_spec = MODEL_ARCHITECTURES[architecture]
                cmd.extend(arch_spec.conversion_args)
            
            # Add vocab-only flag
            if job.parameters.get("vocab_only", False):
                cmd.append("--vocab-only")
            
            # Add additional arguments
            for key, value in job.parameters.items():
                if key not in ["architecture", "vocab_only"] and value is not None:
                    if isinstance(value, bool) and value:
                        cmd.append(f"--{key}")
                    elif not isinstance(value, bool):
                        cmd.extend([f"--{key}", str(value)])
            
            job.logs.append(f"Running command: {' '.join(cmd)}")
            
            # Run conversion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            job._process = process
            
            # Monitor progress
            while True:
                if job._cancelled:
                    process.terminate()
                    job.status = "cancelled"
                    break
                
                output = process.stdout.readline()
                if output:
                    line = output.strip()
                    job.logs.append(line)
                    
                    # Try to extract progress information
                    self._parse_convert_progress(job, line)
                
                if process.poll() is not None:
                    break
            
            # Get final output
            remaining_output, _ = process.communicate()
            if remaining_output:
                for line in remaining_output.strip().split('\n'):
                    if line.strip():
                        job.logs.append(line.strip())
            
            if process.returncode == 0 and not job._cancelled:
                job.status = "completed"
                job.progress = 1.0
                job.completed_at = time.time()
                logger.info(f"Conversion completed: {job.id}")
            else:
                job.status = "failed"
                job.error = f"Process exited with code {process.returncode}"
                job.completed_at = time.time()
                logger.error(f"Conversion failed: {job.id} - {job.error}")
        
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
            logger.error(f"Conversion error: {job.id} - {e}")
        
        finally:
            job._process = None
            with self._lock:
                self._job_threads.pop(job.id, None)
    
    def _parse_convert_progress(self, job: ConversionJob, line: str) -> None:
        """Parse progress information from conversion output."""
        # Look for progress indicators in conversion output
        if "loading" in line.lower():
            job.progress = 0.1
        elif "converting" in line.lower():
            job.progress = 0.5
        elif "writing" in line.lower():
            job.progress = 0.8
        elif "done" in line.lower() or "finished" in line.lower():
            job.progress = 0.95
    
    def _detect_architecture(self, hf_dir: str) -> str:
        """Auto-detect model architecture from HuggingFace directory."""
        hf_path = Path(hf_dir)
        
        # Try to read config.json
        config_path = hf_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check model_type or architectures
                model_type = config.get("model_type", "").lower()
                architectures = config.get("architectures", [])
                
                if model_type:
                    # Direct mapping from model_type
                    if model_type in MODEL_ARCHITECTURES:
                        return model_type
                    
                    # Fuzzy matching
                    for arch_name in MODEL_ARCHITECTURES:
                        if arch_name in model_type:
                            return arch_name
                
                if architectures:
                    # Check architectures list
                    for arch in architectures:
                        arch_lower = arch.lower()
                        for arch_name in MODEL_ARCHITECTURES:
                            if arch_name in arch_lower:
                                return arch_name
                
            except Exception as e:
                logger.debug(f"Failed to parse config.json: {e}")
        
        # Fallback: try to infer from directory name
        dir_name = hf_path.name.lower()
        for arch_name in MODEL_ARCHITECTURES:
            if arch_name in dir_name:
                return arch_name
        
        # Default fallback
        logger.warning(f"Could not detect architecture for {hf_dir}, using 'llama'")
        return "llama"
    
    # ---------- LoRA Merging ----------
    
    def merge_lora(self, 
                  base_model: str, 
                  lora_path: str, 
                  out_path: str,
                  alpha: float = 1.0,
                  **kwargs) -> ConversionJob:
        """
        Merge LoRA adapter with base model.
        
        Args:
            base_model: Base GGUF model path
            lora_path: LoRA adapter path
            out_path: Output merged model path
            alpha: LoRA scaling factor
            **kwargs: Additional arguments
            
        Returns:
            Conversion job object
        """
        if not self.can_merge_lora():
            raise RuntimeError("LoRA merging tool not available")
        
        job_id = f"merge_lora_{int(time.time())}_{hash(base_model) % 10000}"
        
        job = ConversionJob(
            id=job_id,
            source_path=base_model,
            target_path=out_path,
            operation="merge_lora",
            parameters={
                "lora_path": lora_path,
                "alpha": alpha,
                **kwargs
            }
        )
        
        with self._lock:
            self._jobs[job_id] = job
        
        # Start merging in background
        thread = threading.Thread(
            target=self._merge_lora_worker,
            args=(job,),
            daemon=True
        )
        
        with self._lock:
            self._job_threads[job_id] = thread
        
        thread.start()
        
        logger.info(f"Started LoRA merge job {job_id}: {base_model} + {lora_path} -> {out_path}")
        return job
    
    def _merge_lora_worker(self, job: ConversionJob) -> None:
        """Worker function for LoRA merging."""
        try:
            job.status = "running"
            job.started_at = time.time()
            
            # Find LoRA export tool
            export_bin = None
            for name in ["export-lora", "export-lora.exe"]:
                tool_path = self.bin_dir / name
                if tool_path.exists():
                    export_bin = tool_path
                    break
            
            if not export_bin:
                raise RuntimeError("LoRA export binary not found")
            
            # Build command
            cmd = [
                str(export_bin),
                "-m", job.source_path,
                "-o", job.target_path,
                "--lora", job.parameters["lora_path"],
                "--lora-scaled", str(job.parameters["alpha"])
            ]
            
            # Add additional arguments
            for key, value in job.parameters.items():
                if key not in ["lora_path", "alpha"] and value is not None:
                    if isinstance(value, bool) and value:
                        cmd.append(f"--{key}")
                    elif not isinstance(value, bool):
                        cmd.extend([f"--{key}", str(value)])
            
            job.logs.append(f"Running command: {' '.join(cmd)}")
            
            # Run LoRA merge
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            job._process = process
            
            # Monitor progress
            while True:
                if job._cancelled:
                    process.terminate()
                    job.status = "cancelled"
                    break
                
                output = process.stdout.readline()
                if output:
                    line = output.strip()
                    job.logs.append(line)
                    
                    # Try to extract progress information
                    self._parse_merge_progress(job, line)
                
                if process.poll() is not None:
                    break
            
            # Get final output
            remaining_output, _ = process.communicate()
            if remaining_output:
                for line in remaining_output.strip().split('\n'):
                    if line.strip():
                        job.logs.append(line.strip())
            
            if process.returncode == 0 and not job._cancelled:
                job.status = "completed"
                job.progress = 1.0
                job.completed_at = time.time()
                logger.info(f"LoRA merge completed: {job.id}")
            else:
                job.status = "failed"
                job.error = f"Process exited with code {process.returncode}"
                job.completed_at = time.time()
                logger.error(f"LoRA merge failed: {job.id} - {job.error}")
        
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
            logger.error(f"LoRA merge error: {job.id} - {e}")
        
        finally:
            job._process = None
            with self._lock:
                self._job_threads.pop(job.id, None)
    
    def _parse_merge_progress(self, job: ConversionJob, line: str) -> None:
        """Parse progress information from LoRA merge output."""
        if "loading" in line.lower():
            job.progress = 0.2
        elif "merging" in line.lower():
            job.progress = 0.6
        elif "saving" in line.lower():
            job.progress = 0.9
        elif "done" in line.lower():
            job.progress = 0.95
    
    # ---------- Job Management ----------
    
    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        """Get conversion job by ID."""
        with self._lock:
            return self._jobs.get(job_id)
    
    def list_jobs(self, status: Optional[str] = None) -> List[ConversionJob]:
        """List conversion jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a conversion job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status in ["completed", "failed", "cancelled"]:
                return False
            
            job._cancelled = True
            
            # Terminate process if running
            if job._process:
                try:
                    job._process.terminate()
                except Exception as e:
                    logger.warning(f"Failed to terminate process for job {job_id}: {e}")
            
            logger.info(f"Cancelled conversion job: {job_id}")
            return True
    
    def cleanup_completed_jobs(self, older_than_hours: int = 24) -> int:
        """Clean up completed jobs older than specified hours."""
        cutoff_time = time.time() - (older_than_hours * 3600)
        cleaned = 0
        
        with self._lock:
            jobs_to_remove = []
            
            for job_id, job in self._jobs.items():
                if (job.status in ["completed", "failed", "cancelled"] and 
                    job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} old conversion jobs")
        return cleaned
    
    # ---------- Utility Methods ----------
    
    def get_quantization_formats(self) -> Dict[str, QuantizationFormat]:
        """Get available quantization formats."""
        return QUANTIZATION_FORMATS.copy()
    
    def get_recommended_quantization(self, 
                                   use_case: str = "general_use",
                                   memory_constraint: bool = False) -> str:
        """Get recommended quantization format for use case."""
        if memory_constraint:
            return "Q3_K"
        
        recommendations = {
            "general_use": "Q4_K_M",
            "quality_focused": "Q5_K_M",
            "memory_constrained": "Q3_K",
            "mobile": "Q2_K",
            "balanced": "Q4_K_M"
        }
        
        return recommendations.get(use_case, "Q4_K_M")
    
    def get_model_architectures(self) -> Dict[str, ModelArchitecture]:
        """Get supported model architectures."""
        return MODEL_ARCHITECTURES.copy()
    
    def estimate_quantized_size(self, original_size: int, format: str) -> int:
        """Estimate quantized model size."""
        if format not in QUANTIZATION_FORMATS:
            return original_size
        
        reduction_factor = QUANTIZATION_FORMATS[format].size_reduction
        return int(original_size * reduction_factor)


# -----------------------------
# Global Tools Instance
# -----------------------------

_global_tools: Optional[LlamaTools] = None
_global_tools_lock = threading.RLock()


def get_llama_tools() -> LlamaTools:
    """Get the global llama.cpp tools instance."""
    global _global_tools
    if _global_tools is None:
        with _global_tools_lock:
            if _global_tools is None:
                _global_tools = LlamaTools()
    return _global_tools


def initialize_llama_tools(bin_dir: Optional[str] = None) -> LlamaTools:
    """Initialize a fresh global llama.cpp tools instance."""
    global _global_tools
    with _global_tools_lock:
        _global_tools = LlamaTools(bin_dir=bin_dir)
    return _global_tools


# Convenience functions
def quantize_model(in_path: str, out_path: str, format: str = "Q4_K_M", **kwargs) -> ConversionJob:
    """Quantize model using global tools instance."""
    return get_llama_tools().quantize(in_path, out_path, format, **kwargs)


def convert_hf_to_gguf(hf_dir: str, out_path: str, **kwargs) -> ConversionJob:
    """Convert HuggingFace model using global tools instance."""
    return get_llama_tools().convert_hf_to_gguf(hf_dir, out_path, **kwargs)


__all__ = [
    "QuantizationFormat",
    "ConversionJob",
    "ModelArchitecture",
    "LlamaTools",
    "get_llama_tools",
    "initialize_llama_tools",
    "quantize_model",
    "convert_hf_to_gguf",
    "QUANTIZATION_FORMATS",
    "MODEL_ARCHITECTURES",
]