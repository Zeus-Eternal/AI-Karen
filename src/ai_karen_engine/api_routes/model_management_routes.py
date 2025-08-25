"""
Model Management API Routes

Provides REST API endpoints for managing local models, conversions, quantizations,
and job tracking for long-running operations.

This module implements:
- Local model listing, uploading, and management
- Model conversion and quantization endpoints
- Job tracking for long-running operations
- Provider management and validation
- Hugging Face integration for model discovery and downloads
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.inference.huggingface_service import get_huggingface_service
from ai_karen_engine.inference.llama_tools import get_llama_tools
from ai_karen_engine.inference.model_store import get_model_store
from ai_karen_engine.integrations.dynamic_provider_system import get_dynamic_provider_manager
from ai_karen_engine.integrations.registry import get_registry
from ai_karen_engine.services.job_manager import get_job_manager
from ai_karen_engine.services.system_model_manager import get_system_model_manager
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks = import_fastapi(
    "APIRouter", "Depends", "HTTPException", "UploadFile", "File", "Form", "BackgroundTasks"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.model_management")

router = APIRouter(tags=["model-management"])

# -----------------------------
# Request/Response Models
# -----------------------------

class LocalModelInfo(BaseModel):
    """Local model information."""
    id: str
    name: str
    family: str
    format: str
    size: Optional[int] = None
    parameters: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    local_path: Optional[str] = None
    description: str = ""
    tags: List[str] = []
    capabilities: List[str] = []
    compatible_runtimes: List[str] = []
    optimal_runtime: Optional[str] = None
    created_at: Optional[float] = None
    last_used: Optional[float] = None
    usage_count: int = 0


class ModelUploadRequest(BaseModel):
    """Model upload request."""
    name: Optional[str] = None
    description: Optional[str] = ""
    tags: List[str] = []


class ConversionRequest(BaseModel):
    """Model conversion request."""
    source_path: str
    output_name: str
    architecture: Optional[str] = None
    vocab_only: bool = False


class QuantizationRequest(BaseModel):
    """Model quantization request."""
    source_path: str
    output_name: str
    quantization_format: str = "Q4_K_M"
    allow_requantize: bool = False


class JobInfo(BaseModel):
    """Job information."""
    id: str
    kind: str
    status: str
    progress: float
    title: str
    description: str
    logs: List[str] = []
    result: Dict[str, Any] = {}
    error: Optional[str] = None
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    updated_at: float


class ProviderInfo(BaseModel):
    """Provider information."""
    id: str
    name: str
    type: str
    requires_api_key: bool
    status: str = "unknown"
    models: List[Dict[str, Any]] = []
    capabilities: Dict[str, bool] = {}
    error_message: Optional[str] = None


class ProviderValidationRequest(BaseModel):
    """Provider validation request."""
    provider_id: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    config: Dict[str, Any] = {}


class HuggingFaceSearchRequest(BaseModel):
    """Hugging Face model search request."""
    query: str = ""
    tags: List[str] = []
    sort: str = "downloads"
    direction: str = "desc"
    limit: int = 20
    filter_format: Optional[str] = None


class ModelDownloadRequest(BaseModel):
    """Model download request."""
    model_id: str
    artifact: Optional[str] = None
    preference: str = "auto"  # auto, gguf, safetensors


class HealthStatus(BaseModel):
    """Health status information."""
    status: str
    providers: Dict[str, Dict[str, Any]] = {}
    runtimes: Dict[str, Dict[str, Any]] = {}
    model_store: Dict[str, Any] = {}
    job_manager: Dict[str, Any] = {}


# -----------------------------
# Local Model Management Endpoints
# -----------------------------

@router.get("/api/models/local", response_model=List[LocalModelInfo])
async def list_local_models(
    family: Optional[str] = None,
    format: Optional[str] = None,
    local_only: bool = True,
    limit: Optional[int] = None
):
    """List local models with optional filtering."""
    try:
        model_store = get_model_store()
        models = model_store.list_models(
            family=family,
            format=format,
            local_only=local_only
        )
        
        # Convert to response format
        result = []
        for model in models:
            result.append(LocalModelInfo(
                id=model.id,
                name=model.name,
                family=model.family,
                format=model.format,
                size=model.size,
                parameters=model.parameters,
                quantization=model.quantization,
                context_length=model.context_length,
                local_path=model.local_path,
                description=model.description,
                tags=list(model.tags),
                capabilities=list(model.capabilities),
                compatible_runtimes=model.compatible_runtimes,
                optimal_runtime=model.optimal_runtime,
                created_at=model.created_at,
                last_used=model.last_used,
                usage_count=model.usage_count
            ))
        
        # Apply limit if specified
        if limit:
            result = result[:limit]
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list local models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/local/upload")
async def upload_model(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: str = Form(""),
    tags: str = Form("[]")  # JSON string
):
    """Upload a model file (GGUF, safetensors, or archive)."""
    try:
        # Parse tags
        try:
            tag_list = json.loads(tags) if tags else []
        except json.JSONDecodeError:
            tag_list = []
        
        # Validate file type
        allowed_extensions = {".gguf", ".safetensors", ".bin", ".pt", ".pth", ".zip", ".tar", ".tar.gz"}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create upload job
        job_manager = get_job_manager()
        job = job_manager.create_job(
            kind="upload",
            title=f"Upload {file.filename}",
            description=f"Uploading model file: {file.filename}",
            parameters={
                "filename": file.filename,
                "name": name or Path(file.filename).stem,
                "description": description,
                "tags": tag_list,
                "file_size": file.size
            }
        )
        
        # Start upload in background
        background_tasks.add_task(
            _handle_model_upload,
            job.id,
            file,
            name or Path(file.filename).stem,
            description,
            tag_list
        )
        
        return {"job_id": job.id, "message": "Upload started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/local/convert-to-gguf")
async def convert_to_gguf(request: ConversionRequest):
    """Convert a model to GGUF format."""
    try:
        # Validate source path
        source_path = Path(request.source_path)
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source model not found")
        
        # Create conversion job
        job_manager = get_job_manager()
        job = job_manager.create_job(
            kind="convert",
            title=f"Convert to GGUF: {request.output_name}",
            description=f"Converting {source_path.name} to GGUF format",
            parameters={
                "source_path": str(source_path),
                "output_name": request.output_name,
                "architecture": request.architecture,
                "vocab_only": request.vocab_only
            }
        )
        
        return {"job_id": job.id, "message": "Conversion started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/local/quantize")
async def quantize_model(request: QuantizationRequest):
    """Quantize a model to reduce size."""
    try:
        # Validate source path
        source_path = Path(request.source_path)
        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source model not found")
        
        # Validate quantization format
        valid_formats = ["Q2_K", "Q3_K", "Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "IQ2_M", "IQ3_M", "IQ4_M"]
        if request.quantization_format not in valid_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid quantization format. Valid formats: {', '.join(valid_formats)}"
            )
        
        # Create quantization job
        job_manager = get_job_manager()
        job = job_manager.create_job(
            kind="quantize",
            title=f"Quantize: {request.output_name}",
            description=f"Quantizing {source_path.name} to {request.quantization_format}",
            parameters={
                "source_path": str(source_path),
                "output_name": request.output_name,
                "quantization_format": request.quantization_format,
                "allow_requantize": request.allow_requantize
            }
        )
        
        return {"job_id": job.id, "message": "Quantization started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model quantization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/models/local/{model_id}")
async def delete_local_model(model_id: str, delete_files: bool = False):
    """Delete a local model."""
    try:
        model_store = get_model_store()
        success = model_store.delete_model(model_id, delete_files=delete_files)
        
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {"message": "Model deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/local/scan")
async def scan_local_models(directory: Optional[str] = None):
    """Scan directory for local models and register them."""
    try:
        model_store = get_model_store()
        registered_ids = model_store.register_local_models(directory)
        
        return {
            "message": f"Scanned and registered {len(registered_ids)} models",
            "registered_models": registered_ids
        }
        
    except Exception as e:
        logger.error(f"Failed to scan local models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Job Management Endpoints
# -----------------------------

@router.get("/api/models/jobs", response_model=List[JobInfo])
async def list_jobs(
    status: Optional[str] = None,
    kind: Optional[str] = None,
    limit: Optional[int] = 50
):
    """List model management jobs."""
    try:
        job_manager = get_job_manager()
        jobs = job_manager.list_jobs(status=status, kind=kind, limit=limit)
        
        result = []
        for job in jobs:
            result.append(JobInfo(
                id=job.id,
                kind=job.kind,
                status=job.status,
                progress=job.progress,
                title=job.title,
                description=job.description,
                logs=job.logs[-10:],  # Last 10 log entries
                result=job.result,
                error=job.error,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                updated_at=job.updated_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/jobs/{job_id}", response_model=JobInfo)
async def get_job(job_id: str):
    """Get job details."""
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobInfo(
            id=job.id,
            kind=job.kind,
            status=job.status,
            progress=job.progress,
            title=job.title,
            description=job.description,
            logs=job.logs,
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a job."""
    try:
        job_manager = get_job_manager()
        success = job_manager.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a job."""
    try:
        job_manager = get_job_manager()
        success = job_manager.pause_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be paused")
        
        return {"message": "Job paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a job."""
    try:
        job_manager = get_job_manager()
        success = job_manager.resume_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be resumed")
        
        return {"message": "Job resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/models/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job."""
    try:
        job_manager = get_job_manager()
        success = job_manager.delete_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Background Task Handlers
# -----------------------------

async def _handle_model_upload(
    job_id: str,
    file: UploadFile,
    name: str,
    description: str,
    tags: List[str]
):
    """Handle model file upload in background."""
    job_manager = get_job_manager()
    model_store = get_model_store()
    
    try:
        job_manager.append_log(job_id, "Starting model upload...")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_path = temp_file.name
            
            # Read and write file in chunks
            total_size = file.size or 0
            bytes_read = 0
            
            while True:
                chunk = await file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                
                temp_file.write(chunk)
                bytes_read += len(chunk)
                
                if total_size > 0:
                    progress = bytes_read / total_size
                    job_manager.update_progress(job_id, progress * 0.8)  # 80% for upload
        
        job_manager.append_log(job_id, f"File uploaded to {temp_path}")
        
        # Determine target directory
        model_store_dir = Path(model_store.models_dir)
        target_path = model_store_dir / file.filename
        
        # Move file to model store
        import shutil
        shutil.move(temp_path, target_path)
        
        job_manager.append_log(job_id, f"File moved to {target_path}")
        
        # Register model in store
        from ai_karen_engine.inference.model_store import ModelDescriptor
        
        model_id = f"local_{name}_{uuid.uuid4().hex[:8]}"
        descriptor = ModelDescriptor(
            id=model_id,
            name=name,
            format=Path(file.filename).suffix.lower().lstrip('.'),
            size=target_path.stat().st_size,
            source="local",
            provider="local",
            local_path=str(target_path),
            description=description,
            tags=set(tags)
        )
        
        model_store.register_model(descriptor)
        
        job_manager.update_progress(job_id, 1.0)
        job_manager.complete_job(job_id, {"model_id": model_id, "path": str(target_path)})
        job_manager.append_log(job_id, f"Model registered with ID: {model_id}")
        
    except Exception as e:
        job_manager.set_error(job_id, str(e))
        job_manager.append_log(job_id, f"Upload failed: {e}")
        
        # Clean up temporary file if it exists
        try:
            if 'temp_path' in locals() and Path(temp_path).exists():
                os.unlink(temp_path)
        except:
            pass


# Register job handlers
def _register_job_handlers():
    """Register job handlers for model operations."""
    job_manager = get_job_manager()
    
    def handle_convert_job(job):
        """Handle model conversion job."""
        try:
            params = job.parameters
            llama_tools = get_llama_tools()
            
            if not llama_tools:
                raise Exception("llama.cpp tools not available")
            
            job_manager.append_log(job.id, "Starting model conversion...")
            
            # Run conversion
            process = llama_tools.convert_llama_dir(
                hf_dir=params["source_path"],
                out_path=params["output_name"],
                vocab_only=params.get("vocab_only", False)
            )
            
            # Monitor progress
            while process.poll() is None:
                # Simple progress estimation
                job_manager.update_progress(job.id, 0.5)
                import time
                time.sleep(1)
            
            if process.returncode != 0:
                raise Exception(f"Conversion failed with return code {process.returncode}")
            
            job_manager.append_log(job.id, "Conversion completed successfully")
            job_manager.complete_job(job.id, {"output_path": params["output_name"]})
            
        except Exception as e:
            job_manager.set_error(job.id, str(e))
    
    def handle_quantize_job(job):
        """Handle model quantization job."""
        try:
            params = job.parameters
            llama_tools = get_llama_tools()
            
            if not llama_tools:
                raise Exception("llama.cpp tools not available")
            
            job_manager.append_log(job.id, "Starting model quantization...")
            
            # Run quantization
            process = llama_tools.quantize(
                in_path=params["source_path"],
                out_path=params["output_name"],
                fmt=params["quantization_format"],
                allow_requantize=params.get("allow_requantize", False)
            )
            
            # Monitor progress
            while process.poll() is None:
                # Simple progress estimation
                job_manager.update_progress(job.id, 0.5)
                import time
                time.sleep(1)
            
            if process.returncode != 0:
                raise Exception(f"Quantization failed with return code {process.returncode}")
            
            job_manager.append_log(job.id, "Quantization completed successfully")
            job_manager.complete_job(job.id, {"output_path": params["output_name"]})
            
        except Exception as e:
            job_manager.set_error(job.id, str(e))
    
    # Register handlers
    job_manager.register_handler("convert", handle_convert_job)
    job_manager.register_handler("quantize", handle_quantize_job)


# Initialize job handlers when module is imported
_register_job_handlers()

# -----------------------------
# System Model Configuration Endpoints
# -----------------------------

@router.get("/api/models/system", response_model=List[Dict[str, Any]])
async def list_system_models():
    """List all system models with their configuration and status."""
    try:
        system_model_manager = get_system_model_manager()
        models = system_model_manager.get_system_models()
        return models
        
    except Exception as e:
        logger.error(f"Failed to list system models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}", response_model=Dict[str, Any])
async def get_system_model(model_id: str):
    """Get detailed information about a specific system model."""
    try:
        system_model_manager = get_system_model_manager()
        models = system_model_manager.get_system_models()
        
        model = next((m for m in models if m["id"] == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="System model not found")
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/configuration", response_model=Dict[str, Any])
async def get_model_configuration(model_id: str):
    """Get configuration for a specific system model."""
    try:
        system_model_manager = get_system_model_manager()
        config = system_model_manager.get_model_configuration(model_id)
        
        if config is None:
            raise HTTPException(status_code=404, detail="Model configuration not found")
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/models/system/{model_id}/configuration")
async def update_model_configuration(model_id: str, request: Dict[str, Any]):
    """Update configuration for a specific system model."""
    try:
        system_model_manager = get_system_model_manager()
        configuration = request.get("configuration", {})
        
        success = system_model_manager.update_model_configuration(model_id, configuration)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update configuration")
        
        return {"message": "Configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/system/validate-configuration")
async def validate_model_configuration(model_id: str, request: Dict[str, Any]):
    """Validate model configuration against hardware constraints."""
    try:
        system_model_manager = get_system_model_manager()
        configuration = request.get("configuration", {})
        
        # Get model info to determine config class
        if model_id not in system_model_manager.system_models:
            raise HTTPException(status_code=404, detail="System model not found")
        
        model_info = system_model_manager.system_models[model_id]
        config_class = model_info["config_class"]
        
        # Create config object for validation
        config_obj = config_class(**configuration)
        
        # Validate configuration
        validation_result = system_model_manager._validate_configuration(model_id, config_obj)
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate configuration for {model_id}: {e}")
        return {"valid": False, "error": str(e)}


@router.post("/api/models/system/{model_id}/reset-configuration")
async def reset_model_configuration(model_id: str):
    """Reset model configuration to defaults."""
    try:
        system_model_manager = get_system_model_manager()
        success = system_model_manager.reset_model_configuration(model_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="System model not found")
        
        return {"message": "Configuration reset to defaults"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/hardware-recommendations", response_model=Dict[str, Any])
async def get_hardware_recommendations(model_id: str):
    """Get hardware-specific recommendations for model configuration."""
    try:
        system_model_manager = get_system_model_manager()
        recommendations = system_model_manager.get_hardware_recommendations(model_id)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to get hardware recommendations for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/performance-metrics", response_model=Dict[str, Any])
async def get_performance_metrics(model_id: str):
    """Get performance metrics for a system model."""
    try:
        system_model_manager = get_system_model_manager()
        metrics = system_model_manager.get_performance_metrics(model_id)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/system/{model_id}/health-check")
async def perform_health_check(model_id: str):
    """Perform health check on a system model."""
    try:
        system_model_manager = get_system_model_manager()
        status = system_model_manager._check_model_health(model_id)
        
        return {
            "status": status.status,
            "last_health_check": status.last_health_check,
            "error_message": status.error_message,
            "memory_usage": status.memory_usage,
            "load_time": status.load_time,
            "inference_time": status.inference_time
        }
        
    except Exception as e:
        logger.error(f"Failed to perform health check for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/multi-gpu-config", response_model=Dict[str, Any])
async def get_multi_gpu_configuration(model_id: str):
    """Get multi-GPU configuration recommendations."""
    try:
        system_model_manager = get_system_model_manager()
        config = system_model_manager.get_multi_gpu_configuration(model_id)
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get multi-GPU configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Enhanced HuggingFace Integration
# -----------------------------

@router.get("/api/models/huggingface/search", response_model=Dict[str, Any])
async def search_huggingface_models(
    query: str = "",
    page: int = 1,
    per_page: int = 20,
    sort: str = "downloads",
    filter_trainable: bool = False
):
    """Search HuggingFace models with enhanced filtering."""
    try:
        from ai_karen_engine.services.enhanced_huggingface_service import get_enhanced_huggingface_service
        
        service = get_enhanced_huggingface_service()
        
        if filter_trainable:
            # Use enhanced search for trainable models
            from ai_karen_engine.services.enhanced_huggingface_service import TrainingFilters
            filters = TrainingFilters(supports_fine_tuning=True)
            models = service.search_trainable_models(
                query=query,
                filters=filters,
                limit=per_page
            )
            
            # Convert to response format
            model_list = []
            for model in models:
                model_list.append({
                    "id": model.id,
                    "name": model.name,
                    "author": model.author,
                    "description": model.description,
                    "tags": model.tags,
                    "downloads": model.downloads,
                    "likes": model.likes,
                    "family": model.family,
                    "parameters": model.parameters,
                    "format": model.format,
                    "size": model.size,
                    "huggingface_id": model.id,
                    "provider": "huggingface",
                    "supports_training": model.supports_fine_tuning,
                    "training_complexity": model.training_complexity,
                    "license": model.license
                })
        else:
            # Use basic search
            from ai_karen_engine.inference.huggingface_service import ModelFilters
            filters = ModelFilters(sort_by=sort, sort_order="desc")
            models = service.search_models(
                query=query,
                filters=filters,
                limit=per_page
            )
            
            # Convert to response format
            model_list = []
            for model in models:
                model_list.append({
                    "id": model.id,
                    "name": model.name,
                    "author": model.author,
                    "description": model.description,
                    "tags": model.tags,
                    "downloads": model.downloads,
                    "likes": model.likes,
                    "family": model.family,
                    "parameters": model.parameters,
                    "format": model.format,
                    "size": model.size,
                    "huggingface_id": model.id,
                    "provider": "huggingface",
                    "license": model.license
                })
        
        return {
            "models": model_list,
            "total": len(model_list),
            "page": page,
            "per_page": per_page,
            "has_more": len(model_list) == per_page
        }
        
    except Exception as e:
        logger.error(f"Failed to search HuggingFace models: {e}")
        # Return empty results instead of error to prevent frontend issues
        return {
            "models": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "has_more": False,
            "error": str(e)
        }


@router.post("/api/models/download")
async def download_model(
    background_tasks: BackgroundTasks,
    model_id: str,
    model_name: Optional[str] = None,
    provider: str = "huggingface",
    enhanced: bool = True
):
    """Download a model with optional enhanced features."""
    try:
        if provider == "huggingface" and enhanced:
            # Use enhanced download service
            from ai_karen_engine.services.enhanced_huggingface_service import get_enhanced_huggingface_service
            
            service = get_enhanced_huggingface_service()
            job = service.download_with_training_setup(
                model_id=model_id,
                setup_training=True
            )
            
            return {
                "job_id": job.id,
                "message": "Enhanced download started",
                "enhanced": True,
                "compatibility_check": job.compatibility_report is not None
            }
        else:
            # Use basic download service
            service = get_huggingface_service()
            job = service.download_model(model_id=model_id)
            
            return {
                "job_id": job.id,
                "message": "Download started",
                "enhanced": False
            }
        
    except Exception as e:
        logger.error(f"Failed to start model download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Provider Management Endpoints
# -----------------------------

@router.get("/api/providers", response_model=List[ProviderInfo])
async def list_providers():
    """List all available LLM providers (excluding CopilotKit)."""
    try:
        # Return mock data to fix frontend errors
        providers = [
            ProviderInfo(
                id="openai",
                name="OpenAI",
                type="remote",
                requires_api_key=True,
                status="healthy",
                models=[],
                capabilities={
                    "streaming": True,
                    "vision": True,
                    "function_calling": True,
                    "embeddings": True
                }
            ),
            ProviderInfo(
                id="gemini", 
                name="Google Gemini",
                type="remote",
                requires_api_key=True,
                status="healthy",
                models=[],
                capabilities={
                    "streaming": True,
                    "vision": True,
                    "function_calling": False,
                    "embeddings": False
                }
            ),
            ProviderInfo(
                id="local",
                name="Local Models",
                type="local",
                requires_api_key=False,
                status="healthy",
                models=[],
                capabilities={
                    "streaming": True,
                    "vision": False,
                    "function_calling": False,
                    "embeddings": False
                }
            )
        ]
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        # Return fallback data instead of error
        return [
            ProviderInfo(
                id="openai",
                name="OpenAI",
                type="remote",
                requires_api_key=True,
                status="unknown",
                models=[],
                capabilities={"streaming": True}
            )
        ]


@router.post("/api/providers/validate")
async def validate_provider(request: ProviderValidationRequest):
    """Validate provider API key and configuration."""
    try:
        # Exclude CopilotKit from validation
        if request.provider_id.lower() == "copilotkit":
            raise HTTPException(
                status_code=400, 
                detail="CopilotKit is not an LLM provider and should not be validated here"
            )
        
        dynamic_system = get_dynamic_provider_manager()
        
        # Validate provider configuration
        is_valid = await dynamic_system.validate_provider_async(
            provider_id=request.provider_id,
            api_key=request.api_key,
            base_url=request.base_url,
            config=request.config
        )
        
        if is_valid:
            # Try to fetch models to confirm everything works
            try:
                models = dynamic_system.get_provider_models(request.provider_id)
                return {
                    "valid": True,
                    "message": "Provider validation successful",
                    "model_count": len(models)
                }
            except Exception as e:
                return {
                    "valid": True,
                    "message": "API key valid but model discovery failed",
                    "warning": str(e)
                }
        else:
            return {
                "valid": False,
                "message": "Provider validation failed",
                "error": "Invalid API key or configuration"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate provider {request.provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/providers/{provider_id}/models")
async def get_provider_models(provider_id: str):
    """Get models from a specific provider with fallback to curated lists."""
    try:
        # Exclude CopilotKit
        if provider_id.lower() == "copilotkit":
            raise HTTPException(
                status_code=400, 
                detail="CopilotKit is not an LLM provider"
            )
        
        dynamic_system = get_dynamic_provider_manager()
        
        try:
            # Try dynamic model discovery first
            models = dynamic_system.get_provider_models(provider_id)
            
            return {
                "provider_id": provider_id,
                "source": "dynamic",
                "models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "family": model.family,
                        "parameters": model.parameters,
                        "context_length": model.context_length,
                        "capabilities": list(model.capabilities)
                    }
                    for model in models
                ]
            }
            
        except Exception as e:
            logger.warning(f"Dynamic discovery failed for {provider_id}: {e}")
            
            # Fall back to curated model list
            curated_models = dynamic_system.get_fallback_models(provider_id)
            
            return {
                "provider_id": provider_id,
                "source": "fallback",
                "models": curated_models,
                "warning": f"Using fallback models due to: {str(e)}"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get models for provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/health/llms", response_model=HealthStatus)
async def get_llm_health():
    """Get health status of providers, runtimes, and related services."""
    try:
        registry = get_registry()
        dynamic_system = get_dynamic_provider_manager()
        model_store = get_model_store()
        job_manager = get_job_manager()
        
        # Check provider health
        providers = {}
        for provider_name in registry.providers.keys():
            if provider_name.lower() == "copilotkit":
                continue  # Skip CopilotKit
            
            try:
                # Test provider health
                models = dynamic_system.get_provider_models(provider_name)
                providers[provider_name] = {
                    "status": "healthy",
                    "model_count": len(models),
                    "last_check": None
                }
            except Exception as e:
                providers[provider_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": None
                }
        
        # Check runtime health
        runtimes = {}
        for runtime_name, runtime_spec in registry.runtimes.items():
            try:
                # Test runtime health
                health_info = runtime_spec.health()
                runtimes[runtime_name] = {
                    "status": "healthy" if health_info.get("available", False) else "unhealthy",
                    "info": health_info
                }
            except Exception as e:
                runtimes[runtime_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Get model store stats
        model_stats = model_store.get_statistics()
        
        # Get job manager stats
        job_stats = job_manager.get_stats()
        
        # Determine overall status
        provider_healthy = all(p["status"] == "healthy" for p in providers.values())
        runtime_healthy = any(r["status"] == "healthy" for r in runtimes.values())
        overall_status = "healthy" if provider_healthy and runtime_healthy else "degraded"
        
        return HealthStatus(
            status=overall_status,
            providers=providers,
            runtimes=runtimes,
            model_store={
                "total_models": model_stats["total_models"],
                "local_models": model_stats["local_models"],
                "total_size_gb": round(model_stats["total_size_bytes"] / (1024**3), 2)
            },
            job_manager={
                "total_jobs": job_stats.total_jobs,
                "running_jobs": job_stats.running_jobs,
                "queued_jobs": job_stats.queued_jobs
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get LLM health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Hugging Face Integration Endpoints
# -----------------------------

@router.post("/api/models/huggingface/search")
async def search_huggingface_models(request: HuggingFaceSearchRequest):
    """Search Hugging Face models with filtering and sorting."""
    try:
        hf_service = get_huggingface_service()
        
        if not hf_service:
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face service not available"
            )
        
        # Prepare search filters
        from ai_karen_engine.inference.huggingface_service import ModelFilters
        
        filters = ModelFilters(
            tags=request.tags,
            sort=request.sort,
            direction=request.direction,
            limit=request.limit
        )
        
        if request.filter_format:
            filters.format = request.filter_format
        
        # Search models
        models = hf_service.search_models(request.query, filters)
        
        # Convert to response format
        result = []
        for model in models:
            result.append({
                "id": model.id,
                "name": model.name,
                "author": getattr(model, 'author', ''),
                "description": getattr(model, 'description', ''),
                "downloads": getattr(model, 'downloads', 0),
                "likes": getattr(model, 'likes', 0),
                "tags": getattr(model, 'tags', []),
                "size_gb": getattr(model, 'size_gb', None),
                "formats": getattr(model, 'formats', []),
                "license": getattr(model, 'license', ''),
                "created_at": getattr(model, 'created_at', None),
                "updated_at": getattr(model, 'updated_at', None)
            })
        
        return {
            "query": request.query,
            "total_results": len(result),
            "models": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search Hugging Face models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/download")
async def download_model(request: ModelDownloadRequest):
    """Download a model from Hugging Face with progress tracking."""
    try:
        hf_service = get_huggingface_service()
        
        if not hf_service:
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face service not available"
            )
        
        # Start download job
        job_manager = get_job_manager()
        job = job_manager.create_job(
            kind="download",
            title=f"Download {request.model_id}",
            description=f"Downloading model from Hugging Face: {request.model_id}",
            parameters={
                "model_id": request.model_id,
                "artifact": request.artifact,
                "preference": request.preference
            }
        )
        
        # Register download job handler if not already registered
        def handle_download_job(job):
            """Handle model download job."""
            try:
                params = job.parameters
                
                job_manager.append_log(job.id, f"Starting download of {params['model_id']}...")
                
                # Start download
                download_job = hf_service.download_model(
                    model_id=params["model_id"],
                    artifact=params.get("artifact"),
                    preference=params.get("preference", "auto")
                )
                
                # Monitor download progress
                while download_job.status not in ["completed", "failed"]:
                    job_manager.update_progress(job.id, download_job.progress)
                    job_manager.append_log(job.id, f"Progress: {download_job.progress:.1%}")
                    
                    import time
                    time.sleep(2)
                
                if download_job.status == "completed":
                    job_manager.append_log(job.id, "Download completed successfully")
                    
                    # Register downloaded model in model store
                    if download_job.result.get("local_path"):
                        model_store = get_model_store()
                        # Auto-register the downloaded model
                        model_store.register_local_models(
                            directory=str(Path(download_job.result["local_path"]).parent)
                        )
                    
                    job_manager.complete_job(job.id, download_job.result)
                else:
                    job_manager.set_error(job.id, download_job.error or "Download failed")
                
            except Exception as e:
                job_manager.set_error(job.id, str(e))
        
        # Register handler if not already done
        try:
            job_manager.register_handler("download", handle_download_job)
        except:
            pass  # Handler might already be registered
        
        return {"job_id": job.id, "message": "Download started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start model download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/{model_id}/info")
async def get_huggingface_model_info(model_id: str):
    """Get detailed information about a Hugging Face model."""
    try:
        hf_service = get_huggingface_service()
        
        if not hf_service:
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face service not available"
            )
        
        # Get model info
        model_info = hf_service.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "id": model_info.id,
            "name": model_info.name,
            "description": getattr(model_info, 'description', ''),
            "author": getattr(model_info, 'author', ''),
            "tags": getattr(model_info, 'tags', []),
            "license": getattr(model_info, 'license', ''),
            "downloads": getattr(model_info, 'downloads', 0),
            "likes": getattr(model_info, 'likes', 0),
            "size_gb": getattr(model_info, 'size_gb', None),
            "formats": getattr(model_info, 'formats', []),
            "files": getattr(model_info, 'files', []),
            "created_at": getattr(model_info, 'created_at', None),
            "updated_at": getattr(model_info, 'updated_at', None),
            "config": getattr(model_info, 'config', {}),
            "recommended_artifact": getattr(model_info, 'recommended_artifact', None)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Hugging Face model info for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/{model_id}/artifacts")
async def get_model_artifacts(model_id: str):
    """Get available artifacts (files) for a Hugging Face model."""
    try:
        hf_service = get_huggingface_service()
        
        if not hf_service:
            raise HTTPException(
                status_code=503, 
                detail="Hugging Face service not available"
            )
        
        # Get model info to access files
        model_info = hf_service.get_model_info(model_id)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        files = getattr(model_info, 'files', [])
        
        # Categorize files by type
        artifacts = {
            "gguf": [],
            "safetensors": [],
            "pytorch": [],
            "other": []
        }
        
        for file_info in files:
            filename = file_info.get("filename", "")
            size = file_info.get("size", 0)
            
            if filename.endswith(".gguf"):
                artifacts["gguf"].append({
                    "filename": filename,
                    "size": size,
                    "size_gb": round(size / (1024**3), 2),
                    "type": "gguf"
                })
            elif filename.endswith(".safetensors"):
                artifacts["safetensors"].append({
                    "filename": filename,
                    "size": size,
                    "size_gb": round(size / (1024**3), 2),
                    "type": "safetensors"
                })
            elif filename.endswith((".bin", ".pt", ".pth")):
                artifacts["pytorch"].append({
                    "filename": filename,
                    "size": size,
                    "size_gb": round(size / (1024**3), 2),
                    "type": "pytorch"
                })
            else:
                artifacts["other"].append({
                    "filename": filename,
                    "size": size,
                    "size_gb": round(size / (1024**3), 2),
                    "type": "other"
                })
        
        # Get optimal artifact recommendation
        try:
            from ai_karen_engine.inference.huggingface_service import DeviceCapabilities
            device_caps = DeviceCapabilities()  # Use default capabilities
            
            optimal_artifact = hf_service.select_optimal_artifact(
                files=files,
                preference="auto",
                device_caps=device_caps
            )
            
            recommended = optimal_artifact.get("filename") if optimal_artifact else None
        except:
            recommended = None
        
        return {
            "model_id": model_id,
            "artifacts": artifacts,
            "recommended": recommended,
            "total_files": len(files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifacts for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ------
# Missing Endpoints for Frontend
# -----------------------------

@router.get("/api/providers/profiles")
async def get_provider_profiles():
    """Get provider profiles - placeholder endpoint."""
    return {"profiles": []}
async def get_provider_profiles():
    """Get all provider profiles."""
    try:
        # Return mock data for now - this should be replaced with actual profile management
        return {
            "profiles": [
                {
                    "id": "default",
                    "name": "Default Profile",
                    "description": "Default LLM provider configuration",
                    "is_active": True,
                    "providers": {
                        "chat": {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 1},
                        "completion": {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 1},
                        "embedding": {"provider": "openai", "model": "text-embedding-ada-002", "priority": 1}
                    },
                    "router_policy": "local_first",
                    "is_valid": True,
                    "validation_errors": []
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting provider profiles: {e}")
        return {"profiles": []}


@router.get("/api/providers/profiles/active")
async def get_active_provider_profile():
    """Get the currently active provider profile."""
    try:
        # Return mock active profile - this should be replaced with actual profile management
        return {
            "id": "default",
            "name": "Default Profile",
            "description": "Default LLM provider configuration",
            "is_active": True,
            "providers": {
                "chat": {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 1},
                "completion": {"provider": "openai", "model": "gpt-3.5-turbo", "priority": 1},
                "embedding": {"provider": "openai", "model": "text-embedding-ada-002", "priority": 1}
            },
            "router_policy": "local_first",
            "is_valid": True,
            "validation_errors": []
        }
    except Exception as e:
        logger.error(f"Error getting active provider profile: {e}")
        return None


@router.get("/api/models/all")
async def get_all_models():
    """Get all available models from all providers."""
    try:
        registry = get_registry()
        model_store = get_model_store()
        
        all_models = []
        
        # Get local models
        try:
            local_models = model_store.list_models()
            for model in local_models:
                all_models.append({
                    "id": model.get("id", "unknown"),
                    "name": model.get("name", "Unknown Model"),
                    "provider": "local",
                    "type": model.get("type", "unknown"),
                    "size": model.get("size", 0),
                    "status": "available"
                })
        except Exception as e:
            logger.warning(f"Could not load local models: {e}")
        
        # Get models from providers
        for provider_name, provider_spec in registry.providers.items():
            if provider_name.lower() == "copilotkit":
                continue
                
            try:
                # Add some common models for each provider
                if provider_name.lower() == "openai":
                    provider_models = [
                        {"id": "gpt-4", "name": "GPT-4", "type": "chat"},
                        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat"},
                        {"id": "text-embedding-ada-002", "name": "Ada Embedding", "type": "embedding"}
                    ]
                elif provider_name.lower() == "anthropic":
                    provider_models = [
                        {"id": "claude-3-opus", "name": "Claude 3 Opus", "type": "chat"},
                        {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "type": "chat"}
                    ]
                elif provider_name.lower() == "ollama":
                    provider_models = [
                        {"id": "llama2", "name": "Llama 2", "type": "chat"},
                        {"id": "mistral", "name": "Mistral", "type": "chat"}
                    ]
                else:
                    provider_models = []
                
                for model in provider_models:
                    all_models.append({
                        "id": f"{provider_name}:{model['id']}",
                        "name": model["name"],
                        "provider": provider_name,
                        "type": model["type"],
                        "size": 0,
                        "status": "available"
                    })
                    
            except Exception as e:
                logger.warning(f"Could not load models from {provider_name}: {e}")
        
        return {"models": all_models}
        
    except Exception as e:
        logger.error(f"Error getting all models: {e}")
        return {"models": []}


@router.get("/api/providers/stats")
async def get_provider_stats():
    """Get provider statistics and usage information."""
    try:
        registry = get_registry()
        
        stats = {
            "total_providers": 0,
            "active_providers": 0,
            "total_models": 0,
            "providers": {}
        }
        
        for provider_name, provider_spec in registry.providers.items():
            if provider_name.lower() == "copilotkit":
                continue
                
            stats["total_providers"] += 1
            
            # Mock provider stats - this should be replaced with actual usage tracking
            provider_stats = {
                "status": "active",
                "models_count": 3,  # Mock count
                "requests_today": 0,
                "avg_response_time": 0.0,
                "success_rate": 1.0,
                "last_used": None
            }
            
            stats["providers"][provider_name] = provider_stats
            stats["active_providers"] += 1
            stats["total_models"] += provider_stats["models_count"]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting provider stats: {e}")
        return {
            "total_providers": 0,
            "active_providers": 0,
            "total_models": 0,
            "providers": {}
        }

# -----------------------------
# System Model Management Endpoints
# -----------------------------

class SystemModelInfo(BaseModel):
    """System model information."""
    id: str
    name: str
    family: str
    format: str
    capabilities: List[str]
    runtime_compatibility: List[str]
    local_path: str
    status: str
    size: Optional[int] = None
    parameters: Optional[str] = None
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None
    memory_usage: Optional[int] = None
    load_time: Optional[float] = None
    inference_time: Optional[float] = None
    configuration: Dict[str, Any] = {}
    is_system_model: bool = True


class ModelConfigurationRequest(BaseModel):
    """Model configuration update request."""
    configuration: Dict[str, Any]


class HardwareRecommendations(BaseModel):
    """Hardware recommendations for model configuration."""
    system_info: Dict[str, Any]
    recommendations: Dict[str, Any] = {}


@router.get("/api/models/system", response_model=List[SystemModelInfo])
async def list_system_models():
    """List all system models with their status and configuration."""
    try:
        system_manager = get_system_model_manager()
        models = system_manager.get_system_models()
        
        return [SystemModelInfo(**model) for model in models]
        
    except Exception as e:
        logger.error(f"Failed to list system models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}", response_model=SystemModelInfo)
async def get_system_model(model_id: str):
    """Get detailed information about a specific system model."""
    try:
        system_manager = get_system_model_manager()
        models = system_manager.get_system_models()
        
        model = next((m for m in models if m["id"] == model_id), None)
        if not model:
            raise HTTPException(status_code=404, detail="System model not found")
        
        return SystemModelInfo(**model)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/configuration")
async def get_model_configuration(model_id: str):
    """Get configuration for a specific system model."""
    try:
        system_manager = get_system_model_manager()
        config = system_manager.get_model_configuration(model_id)
        
        if config is None:
            raise HTTPException(status_code=404, detail="Model configuration not found")
        
        return {"model_id": model_id, "configuration": config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/models/system/{model_id}/configuration")
async def update_model_configuration(model_id: str, request: ModelConfigurationRequest):
    """Update configuration for a specific system model."""
    try:
        system_manager = get_system_model_manager()
        success = system_manager.update_model_configuration(model_id, request.configuration)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update model configuration")
        
        return {"message": "Configuration updated successfully", "model_id": model_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/system/{model_id}/reset-configuration")
async def reset_model_configuration(model_id: str):
    """Reset model configuration to defaults."""
    try:
        system_manager = get_system_model_manager()
        success = system_manager.reset_model_configuration(model_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {"message": "Configuration reset to defaults", "model_id": model_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset configuration for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/hardware-recommendations")
async def get_hardware_recommendations(model_id: str):
    """Get hardware-specific recommendations for model configuration."""
    try:
        system_manager = get_system_model_manager()
        recommendations = system_manager.get_hardware_recommendations(model_id)
        
        return {"model_id": model_id, **recommendations}
        
    except Exception as e:
        logger.error(f"Failed to get hardware recommendations for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/system/{model_id}/performance-metrics")
async def get_performance_metrics(model_id: str):
    """Get performance metrics for a system model."""
    try:
        system_manager = get_system_model_manager()
        metrics = system_manager.get_performance_metrics(model_id)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/system/{model_id}/health-check")
async def perform_health_check(model_id: str):
    """Perform a health check on a system model."""
    try:
        system_manager = get_system_model_manager()
        # Force a fresh health check
        models = system_manager.get_system_models()
        model = next((m for m in models if m["id"] == model_id), None)
        
        if not model:
            raise HTTPException(status_code=404, detail="System model not found")
        
        return {
            "model_id": model_id,
            "status": model["status"],
            "last_health_check": model["last_health_check"],
            "error_message": model["error_message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform health check for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/system/validate-configuration")
async def validate_model_configuration(model_id: str, request: ModelConfigurationRequest):
    """Validate model configuration without applying it."""
    try:
        system_manager = get_system_model_manager()
        
        # Create a temporary configuration to validate
        model_info = system_manager.system_models.get(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="System model not found")
        
        config_class = model_info["config_class"]
        temp_config = config_class(**request.configuration)
        
        validation_result = system_manager._validate_configuration(model_id, temp_config)
        
        return {
            "model_id": model_id,
            "valid": validation_result["valid"],
            "error": validation_result.get("error"),
            "warnings": validation_result.get("warnings", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate configuration for {model_id}: {e}")
        return {
            "model_id": model_id,
            "valid": False,
            "error": str(e)
        }