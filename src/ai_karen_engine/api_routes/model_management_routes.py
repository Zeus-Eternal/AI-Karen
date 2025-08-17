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
from ai_karen_engine.integrations.dynamic_provider_system import get_dynamic_provider_system
from ai_karen_engine.integrations.registry import get_registry
from ai_karen_engine.services.job_manager import get_job_manager
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
# ---
--------------------------
# Provider Management Endpoints
# -----------------------------

@router.get("/api/providers", response_model=List[ProviderInfo])
async def list_providers():
    """List all available LLM providers (excluding CopilotKit)."""
    try:
        registry = get_registry()
        dynamic_system = get_dynamic_provider_system()
        
        providers = []
        
        # Get providers from registry
        for provider_name, provider_spec in registry.providers.items():
            # Exclude CopilotKit as it's not an LLM provider
            if provider_name.lower() == "copilotkit":
                continue
            
            try:
                # Get provider status and models
                status = "unknown"
                models = []
                error_message = None
                
                # Try to get models from dynamic system
                try:
                    provider_models = dynamic_system.get_provider_models(provider_name)
                    models = [{"id": m.id, "name": m.name} for m in provider_models]
                    status = "healthy"
                except Exception as e:
                    error_message = str(e)
                    status = "unhealthy"
                
                providers.append(ProviderInfo(
                    id=provider_name,
                    name=provider_spec.name,
                    type=getattr(provider_spec, 'type', 'llm'),
                    requires_api_key=provider_spec.requires_api_key,
                    status=status,
                    models=models,
                    capabilities={
                        "streaming": getattr(provider_spec, 'supports_streaming', False),
                        "embeddings": getattr(provider_spec, 'supports_embeddings', False),
                        "function_calling": getattr(provider_spec, 'supports_function_calling', False),
                        "vision": getattr(provider_spec, 'supports_vision', False)
                    },
                    error_message=error_message
                ))
                
            except Exception as e:
                logger.warning(f"Failed to get info for provider {provider_name}: {e}")
                continue
        
        return providers
        
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        dynamic_system = get_dynamic_provider_system()
        
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
        
        dynamic_system = get_dynamic_provider_system()
        
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
        dynamic_system = get_dynamic_provider_system()
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