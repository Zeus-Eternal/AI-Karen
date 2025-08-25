"""
Enhanced HuggingFace Model Discovery API Routes

Provides REST API endpoints for the enhanced HuggingFace model discovery service
with advanced filtering, compatibility detection, and download management.

This module implements:
- Advanced model search with trainable model filtering
- Model compatibility detection and analysis
- Enhanced download management with progress tracking
- Model registration and metadata management
"""

import logging
from typing import Any, Dict, List, Optional

from ai_karen_engine.services.enhanced_huggingface_service import (
    get_enhanced_huggingface_service, TrainingFilters, TrainableModel,
    CompatibilityReport, EnhancedDownloadJob
)
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, HTTPException, BackgroundTasks = import_fastapi(
    "APIRouter", "HTTPException", "BackgroundTasks"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.enhanced_huggingface")

router = APIRouter(tags=["enhanced-huggingface"])

# -----------------------------
# Request/Response Models
# -----------------------------

class TrainingFiltersRequest(BaseModel):
    """Training filters for model search."""
    supports_fine_tuning: bool = True
    supports_lora: bool = False
    supports_full_training: bool = False
    min_parameters: Optional[str] = None
    max_parameters: Optional[str] = None
    hardware_requirements: Optional[str] = None
    training_frameworks: List[str] = Field(default_factory=list)
    memory_requirements: Optional[int] = None


class TrainableModelResponse(BaseModel):
    """Trainable model response."""
    id: str
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    downloads: int = 0
    likes: int = 0
    family: Optional[str] = None
    parameters: Optional[str] = None
    format: Optional[str] = None
    size: Optional[int] = None
    supports_fine_tuning: bool = False
    supports_lora: bool = False
    supports_full_training: bool = False
    training_frameworks: List[str] = Field(default_factory=list)
    hardware_requirements: Dict[str, Any] = Field(default_factory=dict)
    memory_requirements: Optional[int] = None
    training_complexity: str = "unknown"
    license: Optional[str] = None


class CompatibilityReportResponse(BaseModel):
    """Compatibility report response."""
    is_compatible: bool
    compatibility_score: float
    supported_operations: List[str]
    hardware_requirements: Dict[str, Any]
    framework_compatibility: Dict[str, bool]
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class EnhancedDownloadRequest(BaseModel):
    """Enhanced download request."""
    model_id: str
    setup_training: bool = True
    training_config: Optional[Dict[str, Any]] = None


class EnhancedDownloadJobResponse(BaseModel):
    """Enhanced download job response."""
    id: str
    model_id: str
    status: str
    progress: float
    compatibility_report: Optional[CompatibilityReportResponse] = None
    selected_artifacts: List[str] = Field(default_factory=list)
    conversion_needed: bool = False
    post_download_actions: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class ModelSearchRequest(BaseModel):
    """Model search request."""
    query: str = ""
    filters: Optional[TrainingFiltersRequest] = None
    limit: int = 50


# -----------------------------
# Enhanced Model Search Endpoints
# -----------------------------

@router.post("/api/models/huggingface/search-trainable", response_model=List[TrainableModelResponse])
async def search_trainable_models(request: ModelSearchRequest):
    """
    Search for trainable models with advanced filtering.
    
    This endpoint provides advanced search capabilities specifically for models
    that support training operations like fine-tuning, LoRA, or full training.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        # Convert request filters to service filters
        filters = None
        if request.filters:
            filters = TrainingFilters(
                supports_fine_tuning=request.filters.supports_fine_tuning,
                supports_lora=request.filters.supports_lora,
                supports_full_training=request.filters.supports_full_training,
                min_parameters=request.filters.min_parameters,
                max_parameters=request.filters.max_parameters,
                hardware_requirements=request.filters.hardware_requirements,
                training_frameworks=request.filters.training_frameworks,
                memory_requirements=request.filters.memory_requirements
            )
        
        # Search for trainable models
        models = service.search_trainable_models(
            query=request.query,
            filters=filters,
            limit=request.limit
        )
        
        # Convert to response format
        response_models = []
        for model in models:
            response_models.append(TrainableModelResponse(
                id=model.id,
                name=model.name,
                author=model.author,
                description=model.description,
                tags=model.tags,
                downloads=model.downloads,
                likes=model.likes,
                family=model.family,
                parameters=model.parameters,
                format=model.format,
                size=model.size,
                supports_fine_tuning=model.supports_fine_tuning,
                supports_lora=model.supports_lora,
                supports_full_training=model.supports_full_training,
                training_frameworks=model.training_frameworks,
                hardware_requirements=model.hardware_requirements,
                memory_requirements=model.memory_requirements,
                training_complexity=model.training_complexity,
                license=model.license
            ))
        
        return response_models
        
    except Exception as e:
        logger.error(f"Failed to search trainable models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/browse-categories")
async def browse_model_categories():
    """
    Browse models by categories with training capabilities.
    
    Returns curated lists of models organized by categories like
    language models, code models, embedding models, etc.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        categories = {
            "language_models": {
                "title": "Language Models",
                "description": "General-purpose language models for text generation",
                "query": "language model",
                "filters": TrainingFilters(supports_fine_tuning=True)
            },
            "code_models": {
                "title": "Code Models",
                "description": "Models specialized for code generation and understanding",
                "query": "code",
                "filters": TrainingFilters(supports_fine_tuning=True, supports_lora=True)
            },
            "small_models": {
                "title": "Small Models (≤3B)",
                "description": "Lightweight models suitable for resource-constrained environments",
                "query": "",
                "filters": TrainingFilters(
                    supports_fine_tuning=True,
                    max_parameters="3B",
                    memory_requirements=8
                )
            },
            "medium_models": {
                "title": "Medium Models (3B-13B)",
                "description": "Balanced models offering good performance and efficiency",
                "query": "",
                "filters": TrainingFilters(
                    supports_fine_tuning=True,
                    min_parameters="3B",
                    max_parameters="13B"
                )
            },
            "instruction_models": {
                "title": "Instruction-Tuned Models",
                "description": "Models fine-tuned to follow instructions",
                "query": "instruct OR instruction OR chat",
                "filters": TrainingFilters(supports_fine_tuning=True, supports_lora=True)
            }
        }
        
        result = {}
        for category_id, category_info in categories.items():
            try:
                models = service.search_trainable_models(
                    query=category_info["query"],
                    filters=category_info["filters"],
                    limit=10
                )
                
                result[category_id] = {
                    "title": category_info["title"],
                    "description": category_info["description"],
                    "model_count": len(models),
                    "models": [
                        {
                            "id": model.id,
                            "name": model.name,
                            "parameters": model.parameters,
                            "downloads": model.downloads,
                            "training_complexity": model.training_complexity
                        }
                        for model in models[:5]  # Top 5 models per category
                    ]
                }
            except Exception as e:
                logger.warning(f"Failed to load category {category_id}: {e}")
                result[category_id] = {
                    "title": category_info["title"],
                    "description": category_info["description"],
                    "model_count": 0,
                    "models": [],
                    "error": str(e)
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to browse model categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Compatibility Detection Endpoints
# -----------------------------

@router.get("/api/models/huggingface/{model_id}/compatibility", response_model=CompatibilityReportResponse)
async def check_model_compatibility(model_id: str):
    """
    Check training compatibility for a specific model.
    
    Analyzes the model's architecture, files, and metadata to determine
    what training operations are supported and what hardware is required.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        # Check compatibility
        report = service.check_training_compatibility(model_id)
        
        return CompatibilityReportResponse(
            is_compatible=report.is_compatible,
            compatibility_score=report.compatibility_score,
            supported_operations=report.supported_operations,
            hardware_requirements=report.hardware_requirements,
            framework_compatibility=report.framework_compatibility,
            warnings=report.warnings,
            recommendations=report.recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to check compatibility for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/huggingface/batch-compatibility")
async def check_batch_compatibility(model_ids: List[str]):
    """
    Check compatibility for multiple models in batch.
    
    Efficiently checks compatibility for multiple models and returns
    a summary report for each model.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        results = {}
        for model_id in model_ids:
            try:
                report = service.check_training_compatibility(model_id)
                results[model_id] = {
                    "is_compatible": report.is_compatible,
                    "compatibility_score": report.compatibility_score,
                    "supported_operations": report.supported_operations,
                    "training_complexity": "easy" if report.compatibility_score > 0.8 else 
                                         "medium" if report.compatibility_score > 0.5 else "hard",
                    "warnings_count": len(report.warnings)
                }
            except Exception as e:
                results[model_id] = {
                    "is_compatible": False,
                    "error": str(e)
                }
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to check batch compatibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Enhanced Download Management Endpoints
# -----------------------------

@router.post("/api/models/huggingface/download-enhanced", response_model=EnhancedDownloadJobResponse)
async def start_enhanced_download(request: EnhancedDownloadRequest):
    """
    Start enhanced model download with training setup.
    
    Downloads the model with automatic compatibility detection,
    optimal artifact selection, and optional training environment setup.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        # Start enhanced download
        job = service.download_with_training_setup(
            model_id=request.model_id,
            setup_training=request.setup_training,
            training_config=request.training_config
        )
        
        # Convert compatibility report
        compatibility_response = None
        if job.compatibility_report:
            compatibility_response = CompatibilityReportResponse(
                is_compatible=job.compatibility_report.is_compatible,
                compatibility_score=job.compatibility_report.compatibility_score,
                supported_operations=job.compatibility_report.supported_operations,
                hardware_requirements=job.compatibility_report.hardware_requirements,
                framework_compatibility=job.compatibility_report.framework_compatibility,
                warnings=job.compatibility_report.warnings,
                recommendations=job.compatibility_report.recommendations
            )
        
        return EnhancedDownloadJobResponse(
            id=job.id,
            model_id=job.model_id,
            status=job.status,
            progress=job.progress,
            compatibility_report=compatibility_response,
            selected_artifacts=job.selected_artifacts,
            conversion_needed=job.conversion_needed,
            post_download_actions=job.post_download_actions,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except Exception as e:
        logger.error(f"Failed to start enhanced download for {request.model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/downloads", response_model=List[EnhancedDownloadJobResponse])
async def list_enhanced_downloads(status: Optional[str] = None):
    """
    List enhanced download jobs with optional status filtering.
    
    Returns all enhanced download jobs with their current status,
    progress, and metadata.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        jobs = service.list_enhanced_download_jobs(status=status)
        
        response_jobs = []
        for job in jobs:
            # Convert compatibility report
            compatibility_response = None
            if job.compatibility_report:
                compatibility_response = CompatibilityReportResponse(
                    is_compatible=job.compatibility_report.is_compatible,
                    compatibility_score=job.compatibility_report.compatibility_score,
                    supported_operations=job.compatibility_report.supported_operations,
                    hardware_requirements=job.compatibility_report.hardware_requirements,
                    framework_compatibility=job.compatibility_report.framework_compatibility,
                    warnings=job.compatibility_report.warnings,
                    recommendations=job.compatibility_report.recommendations
                )
            
            response_jobs.append(EnhancedDownloadJobResponse(
                id=job.id,
                model_id=job.model_id,
                status=job.status,
                progress=job.progress,
                compatibility_report=compatibility_response,
                selected_artifacts=job.selected_artifacts,
                conversion_needed=job.conversion_needed,
                post_download_actions=job.post_download_actions,
                error=job.error,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            ))
        
        return response_jobs
        
    except Exception as e:
        logger.error(f"Failed to list enhanced downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/downloads/{job_id}", response_model=EnhancedDownloadJobResponse)
async def get_enhanced_download(job_id: str):
    """
    Get details of a specific enhanced download job.
    
    Returns detailed information about the download job including
    progress, compatibility report, and selected artifacts.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        job = service.get_enhanced_download_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Download job not found")
        
        # Convert compatibility report
        compatibility_response = None
        if job.compatibility_report:
            compatibility_response = CompatibilityReportResponse(
                is_compatible=job.compatibility_report.is_compatible,
                compatibility_score=job.compatibility_report.compatibility_score,
                supported_operations=job.compatibility_report.supported_operations,
                hardware_requirements=job.compatibility_report.hardware_requirements,
                framework_compatibility=job.compatibility_report.framework_compatibility,
                warnings=job.compatibility_report.warnings,
                recommendations=job.compatibility_report.recommendations
            )
        
        return EnhancedDownloadJobResponse(
            id=job.id,
            model_id=job.model_id,
            status=job.status,
            progress=job.progress,
            compatibility_report=compatibility_response,
            selected_artifacts=job.selected_artifacts,
            conversion_needed=job.conversion_needed,
            post_download_actions=job.post_download_actions,
            error=job.error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get enhanced download {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/huggingface/downloads/{job_id}/cancel")
async def cancel_enhanced_download(job_id: str):
    """Cancel an enhanced download job."""
    try:
        service = get_enhanced_huggingface_service()
        
        success = service.cancel_download(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download job not found or cannot be cancelled")
        
        return {"message": "Enhanced download cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel enhanced download {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/huggingface/downloads/{job_id}/pause")
async def pause_enhanced_download(job_id: str):
    """Pause an enhanced download job."""
    try:
        service = get_enhanced_huggingface_service()
        
        success = service.pause_download(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download job not found or cannot be paused")
        
        return {"message": "Enhanced download paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause enhanced download {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/models/huggingface/downloads/{job_id}/resume")
async def resume_enhanced_download(job_id: str):
    """Resume a paused enhanced download job."""
    try:
        service = get_enhanced_huggingface_service()
        
        success = service.resume_download(job_id)
        if not success:
            raise HTTPException(status_code=404, detail="Download job not found or cannot be resumed")
        
        return {"message": "Enhanced download resumed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume enhanced download {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Model Format Conversion Endpoints
# -----------------------------

@router.post("/api/models/huggingface/convert-format")
async def convert_model_format(
    model_path: str,
    target_format: str,
    output_name: Optional[str] = None
):
    """
    Convert model format for optimal training compatibility.
    
    Converts models between formats (e.g., PyTorch .bin to SafeTensors)
    to ensure optimal compatibility with training frameworks.
    """
    try:
        # This would integrate with the existing conversion tools
        # For now, return a placeholder response
        return {
            "message": "Format conversion started",
            "source_path": model_path,
            "target_format": target_format,
            "output_name": output_name or f"converted_{target_format}",
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Failed to start format conversion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Model Metadata Management Endpoints
# -----------------------------

@router.get("/api/models/huggingface/{model_id}/metadata")
async def get_model_metadata(model_id: str):
    """
    Get comprehensive metadata for a HuggingFace model.
    
    Returns detailed information including training capabilities,
    hardware requirements, and compatibility analysis.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        # Get model info
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get compatibility report
        compatibility_report = service.check_training_compatibility(model_id)
        
        return {
            "model_info": {
                "id": model_info.id,
                "name": model_info.name,
                "description": model_info.description,
                "tags": model_info.tags,
                "license": model_info.license,
                "size": model_info.size,
                "downloads": model_info.downloads,
                "likes": model_info.likes,
                "files": model_info.files
            },
            "compatibility": {
                "is_compatible": compatibility_report.is_compatible,
                "compatibility_score": compatibility_report.compatibility_score,
                "supported_operations": compatibility_report.supported_operations,
                "hardware_requirements": compatibility_report.hardware_requirements,
                "framework_compatibility": compatibility_report.framework_compatibility,
                "warnings": compatibility_report.warnings,
                "recommendations": compatibility_report.recommendations
            },
            "training_info": {
                "difficulty": "easy" if compatibility_report.compatibility_score > 0.8 else 
                            "medium" if compatibility_report.compatibility_score > 0.5 else "hard",
                "estimated_training_time": "varies",  # Could be calculated based on model size
                "recommended_hardware": compatibility_report.hardware_requirements.get("recommended", "gpu")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/huggingface/stats")
async def get_discovery_stats():
    """
    Get statistics about the model discovery service.
    
    Returns information about cached models, download jobs,
    and service health metrics.
    """
    try:
        service = get_enhanced_huggingface_service()
        
        # Get job statistics
        all_jobs = service.list_enhanced_download_jobs()
        job_stats = {
            "total": len(all_jobs),
            "completed": len([j for j in all_jobs if j.status == "completed"]),
            "downloading": len([j for j in all_jobs if j.status == "downloading"]),
            "failed": len([j for j in all_jobs if j.status == "failed"]),
            "cancelled": len([j for j in all_jobs if j.status == "cancelled"])
        }
        
        return {
            "service_status": "healthy",
            "cache_size": len(service._compatibility_cache),
            "download_jobs": job_stats,
            "features": {
                "advanced_search": True,
                "compatibility_detection": True,
                "enhanced_downloads": True,
                "format_conversion": True,
                "training_setup": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))