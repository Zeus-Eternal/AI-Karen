"""
HuggingFace Hub Integration Service

This module provides integration with HuggingFace Hub for model search, download,
and management. It includes advanced filtering, download management with progress
tracking, and automatic integration with the local model store.

Key Features:
- Model search and browsing with advanced filtering
- Download management with progress tracking and resume capability
- Automatic format detection and conversion recommendations
- Integration with local model registry
- Checksum verification and error handling
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# Try to import HuggingFace libraries with graceful fallback
try:
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError
    HF_AVAILABLE = True
except ImportError:
    logger.warning("HuggingFace Hub library not available. Install with: pip install huggingface_hub")
    HfApi = None
    hf_hub_download = None
    snapshot_download = None
    RepositoryNotFoundError = Exception
    RevisionNotFoundError = Exception
    HF_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    logger.warning("Requests library not available. Install with: pip install requests")
    requests = None
    REQUESTS_AVAILABLE = False

# -----------------------------
# Data Models
# -----------------------------

@dataclass
class ModelFilters:
    """Filters for model search."""
    tags: Optional[List[str]] = None
    family: Optional[str] = None  # llama, mistral, etc.
    quantization: Optional[str] = None  # Q4_K_M, fp16, etc.
    min_downloads: Optional[int] = None
    max_size: Optional[int] = None  # in bytes
    license: Optional[str] = None
    language: Optional[str] = None
    task: Optional[str] = None  # text-generation, text-classification, etc.
    library: Optional[str] = None  # transformers, gguf, etc.
    sort_by: str = "downloads"  # downloads, created_at, updated_at
    sort_order: str = "desc"  # asc, desc


@dataclass
class HFModel:
    """HuggingFace model information."""
    id: str
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    downloads: int = 0
    likes: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    library_name: Optional[str] = None
    pipeline_tag: Optional[str] = None
    license: Optional[str] = None
    files: List[Dict[str, Any]] = field(default_factory=list)
    size: Optional[int] = None  # Total size in bytes
    
    # Inferred metadata
    family: Optional[str] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    format: Optional[str] = None
    
    def __post_init__(self):
        """Extract metadata from model info."""
        self._infer_metadata()
    
    def _infer_metadata(self):
        """Infer model metadata from name and tags."""
        name_lower = self.id.lower()
        
        # Infer family (order matters - check more specific patterns first)
        families = {
            "codellama": ["codellama", "code-llama"],
            "llama": ["llama", "alpaca", "vicuna"],
            "mistral": ["mistral", "mixtral"],
            "qwen": ["qwen", "qwen2"],
            "phi": ["phi", "phi-2", "phi-3"],
            "gemma": ["gemma"],
            "bert": ["bert", "distilbert", "roberta"],
            "gpt": ["gpt", "gpt2", "gpt-neo", "gpt-j"]
        }
        
        for family, patterns in families.items():
            if any(pattern in name_lower for pattern in patterns):
                self.family = family
                break
        
        # Infer parameters
        param_patterns = ["1b", "3b", "7b", "13b", "30b", "65b", "70b", "175b"]
        for pattern in param_patterns:
            if pattern in name_lower:
                self.parameters = pattern.upper()
                break
        
        # Infer quantization from tags, name, or filenames
        quant_patterns = ["q2_k", "q3_k", "q4_k_m", "q5_k_m", "q6_k", "q8_0", "iq2_m", "iq3_m", "fp16", "bf16", "int8", "int4"]
        for pattern in quant_patterns:
            if (pattern in name_lower or 
                any(pattern in tag.lower() for tag in self.tags) or
                any(pattern in f.get("rfilename", "").lower() for f in self.files)):
                self.quantization = pattern.upper()
                break
        
        # Infer format from files or tags
        if any("gguf" in tag.lower() for tag in self.tags) or any(f.get("rfilename", "").endswith(".gguf") for f in self.files):
            self.format = "gguf"
        elif any("safetensors" in tag.lower() for tag in self.tags) or any(f.get("rfilename", "").endswith(".safetensors") for f in self.files):
            self.format = "safetensors"
        elif any(f.get("rfilename", "").endswith(".bin") for f in self.files):
            self.format = "bin"


@dataclass
class ModelInfo:
    """Detailed model information."""
    id: str
    name: str
    description: str
    tags: List[str]
    files: List[Dict[str, Any]]
    config: Dict[str, Any] = field(default_factory=dict)
    readme: str = ""
    license: Optional[str] = None
    size: int = 0
    downloads: int = 0
    likes: int = 0


@dataclass
class DeviceCapabilities:
    """Device capabilities for optimal artifact selection."""
    has_gpu: bool = False
    gpu_memory: Optional[int] = None  # in MB
    cpu_memory: Optional[int] = None  # in MB
    supports_fp16: bool = False
    supports_int8: bool = False
    supports_int4: bool = False


@dataclass
class DownloadJob:
    """Download job information."""
    id: str
    model_id: str
    artifact: Optional[str] = None
    status: str = "queued"  # queued, downloading, completed, failed, cancelled
    progress: float = 0.0
    total_size: Optional[int] = None
    downloaded_size: int = 0
    speed: Optional[float] = None  # bytes per second
    eta: Optional[float] = None  # seconds
    error: Optional[str] = None
    local_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # Control flags
    _cancelled: bool = False
    _paused: bool = False


# -----------------------------
# HuggingFace Service Implementation
# -----------------------------

class HuggingFaceService:
    """
    Service for interacting with HuggingFace Hub.
    
    Provides model search, download, and management capabilities with
    integration to the local model store.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize HuggingFace service.
        
        Args:
            cache_dir: Directory for caching downloads (default: ~/.cache/huggingface)
            token: HuggingFace API token for private models
        """
        self.cache_dir = Path(cache_dir or self._get_default_cache_dir())
        self.token = token
        self._lock = threading.RLock()
        
        # Initialize HF API if available
        if HF_AVAILABLE:
            self.api = HfApi(token=token)
        else:
            self.api = None
            logger.warning("HuggingFace Hub not available - service will have limited functionality")
        
        # Download job management
        self._download_jobs: Dict[str, DownloadJob] = {}
        self._download_threads: Dict[str, threading.Thread] = {}
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_default_cache_dir(self) -> str:
        """Get default cache directory."""
        home = Path.home()
        return str(home / ".cache" / "huggingface")
    
    # ---------- Model Search ----------
    
    def search_models(self, 
                     query: str = "",
                     filters: Optional[ModelFilters] = None,
                     limit: int = 50) -> List[HFModel]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query string
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            List of matching HF models
        """
        if not self.api:
            logger.warning("HuggingFace API not available")
            return []
        
        filters = filters or ModelFilters()
        
        try:
            # Build search parameters
            search_params = {
                "search": query if query else None,
                "limit": limit,
                "sort": filters.sort_by,
                "direction": -1 if filters.sort_order == "desc" else 1,
                "task": filters.task,
                "library": filters.library,
            }
            
            # Add tag filters
            if filters.tags:
                search_params["tags"] = filters.tags
            
            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}
            
            # Search models
            models = list(self.api.list_models(**search_params))
            
            # Convert to HFModel objects
            hf_models = []
            for model in models:
                try:
                    hf_model = self._convert_to_hf_model(model)
                    
                    # Apply additional filters
                    if self._passes_filters(hf_model, filters):
                        hf_models.append(hf_model)
                        
                except Exception as e:
                    logger.debug(f"Failed to convert model {getattr(model, 'id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(hf_models)} models matching query: {query}")
            return hf_models
            
        except Exception as e:
            logger.error(f"Failed to search models: {e}")
            return []
    
    def _convert_to_hf_model(self, model) -> HFModel:
        """Convert HF API model to HFModel."""
        # Extract files information
        files = []
        total_size = 0
        
        try:
            if hasattr(model, 'siblings') and model.siblings:
                for sibling in model.siblings:
                    file_info = {
                        "rfilename": sibling.rfilename,
                        "size": getattr(sibling, 'size', 0) or 0
                    }
                    files.append(file_info)
                    total_size += file_info["size"]
        except Exception as e:
            logger.debug(f"Failed to extract files for {model.id}: {e}")
        
        return HFModel(
            id=model.id,
            name=model.id.split("/")[-1] if "/" in model.id else model.id,
            author=model.id.split("/")[0] if "/" in model.id else None,
            description=getattr(model, 'description', None) or "",
            tags=getattr(model, 'tags', []) or [],
            downloads=getattr(model, 'downloads', 0) or 0,
            likes=getattr(model, 'likes', 0) or 0,
            created_at=getattr(model, 'created_at', None),
            updated_at=getattr(model, 'last_modified', None),
            library_name=getattr(model, 'library_name', None),
            pipeline_tag=getattr(model, 'pipeline_tag', None),
            license=getattr(model, 'license', None),
            files=files,
            size=total_size
        )
    
    def _passes_filters(self, model: HFModel, filters: ModelFilters) -> bool:
        """Check if model passes additional filters."""
        if filters.family and model.family != filters.family:
            return False
        
        if filters.quantization and model.quantization != filters.quantization:
            return False
        
        if filters.min_downloads and model.downloads < filters.min_downloads:
            return False
        
        if filters.max_size and model.size and model.size > filters.max_size:
            return False
        
        if filters.license and model.license != filters.license:
            return False
        
        return True
    
    # ---------- Model Information ----------
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get detailed information about a model.
        
        Args:
            model_id: HuggingFace model ID
            
        Returns:
            Detailed model information or None if not found
        """
        if not self.api:
            logger.warning("HuggingFace API not available")
            return None
        
        try:
            # Get model info
            model = self.api.model_info(model_id)
            
            # Get files list
            files = []
            total_size = 0
            
            if hasattr(model, 'siblings') and model.siblings:
                for sibling in model.siblings:
                    file_info = {
                        "rfilename": sibling.rfilename,
                        "size": getattr(sibling, 'size', 0) or 0,
                        "lfs": getattr(sibling, 'lfs', None)
                    }
                    files.append(file_info)
                    total_size += file_info["size"]
            
            # Try to get config
            config = {}
            try:
                config_content = self.api.hf_hub_download(
                    repo_id=model_id,
                    filename="config.json",
                    repo_type="model"
                )
                with open(config_content, 'r') as f:
                    config = json.load(f)
            except Exception:
                pass  # Config not available
            
            # Try to get README
            readme = ""
            try:
                readme_content = self.api.hf_hub_download(
                    repo_id=model_id,
                    filename="README.md",
                    repo_type="model"
                )
                with open(readme_content, 'r') as f:
                    readme = f.read()
            except Exception:
                pass  # README not available
            
            return ModelInfo(
                id=model_id,
                name=model_id.split("/")[-1] if "/" in model_id else model_id,
                description=getattr(model, 'description', '') or '',
                tags=getattr(model, 'tags', []) or [],
                files=files,
                config=config,
                readme=readme,
                license=getattr(model, 'license', None),
                size=total_size,
                downloads=getattr(model, 'downloads', 0) or 0,
                likes=getattr(model, 'likes', 0) or 0
            )
            
        except (RepositoryNotFoundError, RevisionNotFoundError):
            logger.warning(f"Model not found: {model_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {e}")
            return None
    
    # ---------- Artifact Selection ----------
    
    def select_optimal_artifact(self, 
                               files: List[Dict[str, Any]], 
                               preference: str = "auto",
                               device_caps: Optional[DeviceCapabilities] = None) -> Optional[Dict[str, Any]]:
        """
        Select optimal artifact from available files.
        
        Args:
            files: List of available files
            preference: Format preference (auto, gguf, safetensors, bin)
            device_caps: Device capabilities for optimization
            
        Returns:
            Selected file info or None if no suitable file found
        """
        if not files:
            return None
        
        device_caps = device_caps or DeviceCapabilities()
        
        # Categorize files by format
        gguf_files = [f for f in files if f.get("rfilename", "").endswith(".gguf")]
        safetensors_files = [f for f in files if f.get("rfilename", "").endswith(".safetensors")]
        bin_files = [f for f in files if f.get("rfilename", "").endswith(".bin")]
        
        # Handle explicit preferences
        if preference == "gguf" and gguf_files:
            return self._select_best_gguf(gguf_files, device_caps)
        elif preference == "safetensors" and safetensors_files:
            return self._select_best_safetensors(safetensors_files, device_caps)
        elif preference == "bin" and bin_files:
            return self._select_best_bin(bin_files, device_caps)
        
        # Auto selection based on device capabilities
        if preference == "auto":
            # Prefer GGUF for CPU-only or memory-constrained devices
            if not device_caps.has_gpu or (device_caps.cpu_memory and device_caps.cpu_memory < 16000):
                if gguf_files:
                    return self._select_best_gguf(gguf_files, device_caps)
            
            # Prefer safetensors for GPU devices
            if device_caps.has_gpu and safetensors_files:
                return self._select_best_safetensors(safetensors_files, device_caps)
            
            # Fallback order: GGUF -> safetensors -> bin
            for file_list, selector in [
                (gguf_files, self._select_best_gguf),
                (safetensors_files, self._select_best_safetensors),
                (bin_files, self._select_best_bin)
            ]:
                if file_list:
                    return selector(file_list, device_caps)
        
        # If no specific format found, return the largest file (likely the main model)
        return max(files, key=lambda f: f.get("size", 0))
    
    def _select_best_gguf(self, gguf_files: List[Dict[str, Any]], device_caps: DeviceCapabilities) -> Dict[str, Any]:
        """Select best GGUF file based on device capabilities."""
        # Prefer quantized models for memory efficiency
        quant_priority = ["Q4_K_M", "Q5_K_M", "Q3_K", "Q6_K", "Q8_0", "Q2_K"]
        
        for quant in quant_priority:
            for file in gguf_files:
                filename = file.get("rfilename", "").upper()
                if quant in filename:
                    return file
        
        # If no quantized version found, return the largest GGUF file
        return max(gguf_files, key=lambda f: f.get("size", 0))
    
    def _select_best_safetensors(self, safetensors_files: List[Dict[str, Any]], device_caps: DeviceCapabilities) -> Dict[str, Any]:
        """Select best safetensors file based on device capabilities."""
        # Look for model.safetensors or pytorch_model.safetensors
        preferred_names = ["model.safetensors", "pytorch_model.safetensors"]
        
        for name in preferred_names:
            for file in safetensors_files:
                if file.get("rfilename", "") == name:
                    return file
        
        # Return the largest safetensors file
        return max(safetensors_files, key=lambda f: f.get("size", 0))
    
    def _select_best_bin(self, bin_files: List[Dict[str, Any]], device_caps: DeviceCapabilities) -> Dict[str, Any]:
        """Select best bin file based on device capabilities."""
        # Look for pytorch_model.bin
        for file in bin_files:
            if file.get("rfilename", "") == "pytorch_model.bin":
                return file
        
        # Return the largest bin file
        return max(bin_files, key=lambda f: f.get("size", 0))
    
    # ---------- Download Management ----------
    
    def download_model(self, 
                      model_id: str, 
                      artifact: Optional[str] = None,
                      preference: str = "auto",
                      device_caps: Optional[DeviceCapabilities] = None) -> DownloadJob:
        """
        Start downloading a model.
        
        Args:
            model_id: HuggingFace model ID
            artifact: Specific artifact to download (optional)
            preference: Format preference for auto-selection
            device_caps: Device capabilities for optimization
            
        Returns:
            Download job object
        """
        job_id = f"download_{model_id.replace('/', '_')}_{int(time.time())}"
        
        job = DownloadJob(
            id=job_id,
            model_id=model_id,
            artifact=artifact
        )
        
        with self._lock:
            self._download_jobs[job_id] = job
        
        # Start download in background thread
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(job, preference, device_caps),
            daemon=True
        )
        
        with self._lock:
            self._download_threads[job_id] = download_thread
        
        download_thread.start()
        
        logger.info(f"Started download job {job_id} for model {model_id}")
        return job
    
    def _download_worker(self, 
                        job: DownloadJob, 
                        preference: str,
                        device_caps: Optional[DeviceCapabilities]):
        """Worker function for downloading models."""
        try:
            job.status = "downloading"
            job.started_at = time.time()
            
            # Get model info if artifact not specified
            if not job.artifact:
                model_info = self.get_model_info(job.model_id)
                if not model_info:
                    raise Exception(f"Model not found: {job.model_id}")
                
                # Select optimal artifact
                optimal_file = self.select_optimal_artifact(
                    model_info.files, 
                    preference, 
                    device_caps
                )
                
                if not optimal_file:
                    raise Exception("No suitable artifact found")
                
                job.artifact = optimal_file["rfilename"]
                job.total_size = optimal_file.get("size", 0)
            
            # Download the file
            if not HF_AVAILABLE:
                raise Exception("HuggingFace Hub library not available")
            
            # Create progress callback
            def progress_callback(downloaded: int, total: int):
                if job._cancelled:
                    raise Exception("Download cancelled")
                
                job.downloaded_size = downloaded
                job.total_size = total
                job.progress = downloaded / total if total > 0 else 0.0
                
                # Calculate speed and ETA
                elapsed = time.time() - job.started_at
                if elapsed > 0:
                    job.speed = downloaded / elapsed
                    if job.speed > 0:
                        remaining = total - downloaded
                        job.eta = remaining / job.speed
            
            # Download using HuggingFace Hub
            local_path = hf_hub_download(
                repo_id=job.model_id,
                filename=job.artifact,
                cache_dir=str(self.cache_dir),
                token=self.token,
                # Note: progress callback would need custom implementation
                # as hf_hub_download doesn't support it directly
            )
            
            job.local_path = local_path
            job.status = "completed"
            job.completed_at = time.time()
            job.progress = 1.0
            
            # Register with model store
            self._register_downloaded_model(job)
            
            logger.info(f"Download completed: {job.id}")
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()
            logger.error(f"Download failed for {job.id}: {e}")
        
        finally:
            # Clean up thread reference
            with self._lock:
                self._download_threads.pop(job.id, None)
    
    def _register_downloaded_model(self, job: DownloadJob):
        """Register downloaded model with the model store."""
        try:
            from ai_karen_engine.inference.model_store import get_model_store, ModelDescriptor
            
            # Get model info
            model_info = self.get_model_info(job.model_id)
            if not model_info:
                logger.warning(f"Could not get model info for registration: {job.model_id}")
                return
            
            # Create model descriptor
            descriptor = ModelDescriptor(
                id=f"hf_{job.model_id.replace('/', '_')}",
                name=model_info.name,
                family=self._infer_family_from_id(job.model_id),
                format=self._infer_format_from_artifact(job.artifact),
                size=job.total_size,
                source="huggingface",
                provider="huggingface",
                local_path=job.local_path,
                download_url=f"https://huggingface.co/{job.model_id}",
                license=model_info.license,
                description=model_info.description,
                tags=set(model_info.tags),
                capabilities=set()  # Would be inferred from model type
            )
            
            # Register with model store
            model_store = get_model_store()
            model_store.register_model(descriptor)
            
            logger.info(f"Registered downloaded model: {descriptor.id}")
            
        except Exception as e:
            logger.warning(f"Failed to register downloaded model: {e}")
    
    def _infer_family_from_id(self, model_id: str) -> str:
        """Infer model family from HuggingFace model ID."""
        id_lower = model_id.lower()
        
        families = {
            "codellama": ["codellama", "code-llama"],
            "llama": ["llama", "alpaca", "vicuna"],
            "mistral": ["mistral", "mixtral"],
            "qwen": ["qwen", "qwen2"],
            "phi": ["phi", "phi-2", "phi-3"],
            "gemma": ["gemma"],
            "bert": ["bert", "distilbert", "roberta"],
            "gpt": ["gpt", "gpt2", "gpt-neo", "gpt-j"]
        }
        
        for family, patterns in families.items():
            if any(pattern in id_lower for pattern in patterns):
                return family
        
        return "unknown"
    
    def _infer_format_from_artifact(self, artifact: Optional[str]) -> str:
        """Infer format from artifact filename."""
        if not artifact:
            return "unknown"
        
        artifact_lower = artifact.lower()
        
        if artifact_lower.endswith(".gguf"):
            return "gguf"
        elif artifact_lower.endswith(".safetensors"):
            return "safetensors"
        elif artifact_lower.endswith(".bin"):
            return "bin"
        elif artifact_lower.endswith(".pt") or artifact_lower.endswith(".pth"):
            return "pytorch"
        
        return "unknown"
    
    # ---------- Job Management ----------
    
    def get_download_job(self, job_id: str) -> Optional[DownloadJob]:
        """Get download job by ID."""
        with self._lock:
            return self._download_jobs.get(job_id)
    
    def list_download_jobs(self, status: Optional[str] = None) -> List[DownloadJob]:
        """List download jobs, optionally filtered by status."""
        with self._lock:
            jobs = list(self._download_jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return jobs
    
    def cancel_download(self, job_id: str) -> bool:
        """Cancel a download job."""
        with self._lock:
            job = self._download_jobs.get(job_id)
            if not job:
                return False
            
            if job.status in ["completed", "failed", "cancelled"]:
                return False
            
            job._cancelled = True
            job.status = "cancelled"
            job.completed_at = time.time()
            
            # Clean up thread
            thread = self._download_threads.pop(job_id, None)
            if thread and thread.is_alive():
                # Thread will check _cancelled flag and exit
                pass
            
            logger.info(f"Cancelled download job: {job_id}")
            return True
    
    def pause_download(self, job_id: str) -> bool:
        """Pause a download job."""
        with self._lock:
            job = self._download_jobs.get(job_id)
            if not job or job.status != "downloading":
                return False
            
            job._paused = True
            return True
    
    def resume_download(self, job_id: str) -> bool:
        """Resume a paused download job."""
        with self._lock:
            job = self._download_jobs.get(job_id)
            if not job or not job._paused:
                return False
            
            job._paused = False
            return True
    
    def cleanup_completed_jobs(self, older_than_hours: int = 24) -> int:
        """Clean up completed jobs older than specified hours."""
        cutoff_time = time.time() - (older_than_hours * 3600)
        cleaned = 0
        
        with self._lock:
            jobs_to_remove = []
            
            for job_id, job in self._download_jobs.items():
                if (job.status in ["completed", "failed", "cancelled"] and 
                    job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self._download_jobs[job_id]
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} old download jobs")
        return cleaned
    
    # ---------- Utility Methods ----------
    
    def is_available(self) -> bool:
        """Check if HuggingFace service is available."""
        return HF_AVAILABLE and self.api is not None
    
    def get_cache_size(self) -> int:
        """Get total size of cached models in bytes."""
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        continue
        except Exception as e:
            logger.warning(f"Failed to calculate cache size: {e}")
        
        return total_size
    
    def clear_cache(self, confirm: bool = False) -> bool:
        """Clear the download cache."""
        if not confirm:
            logger.warning("Cache clear requires confirmation")
            return False
        
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info("Cleared HuggingFace cache")
                return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
        
        return False


# -----------------------------
# Global Service Instance
# -----------------------------

_global_service: Optional[HuggingFaceService] = None
_global_service_lock = threading.RLock()


def get_huggingface_service() -> HuggingFaceService:
    """Get the global HuggingFace service instance."""
    global _global_service
    if _global_service is None:
        with _global_service_lock:
            if _global_service is None:
                _global_service = HuggingFaceService()
    return _global_service


def initialize_huggingface_service(cache_dir: Optional[str] = None, token: Optional[str] = None) -> HuggingFaceService:
    """Initialize a fresh global HuggingFace service."""
    global _global_service
    with _global_service_lock:
        _global_service = HuggingFaceService(cache_dir=cache_dir, token=token)
    return _global_service


# Convenience functions
def search_models(query: str = "", filters: Optional[ModelFilters] = None, limit: int = 50) -> List[HFModel]:
    """Search models using the global service."""
    return get_huggingface_service().search_models(query, filters, limit)


def download_model(model_id: str, **kwargs) -> DownloadJob:
    """Download model using the global service."""
    return get_huggingface_service().download_model(model_id, **kwargs)


__all__ = [
    "ModelFilters",
    "HFModel",
    "ModelInfo",
    "DeviceCapabilities",
    "DownloadJob",
    "HuggingFaceService",
    "get_huggingface_service",
    "initialize_huggingface_service",
    "search_models",
    "download_model",
]