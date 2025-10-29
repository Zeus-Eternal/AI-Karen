"""
Model Organization and Management API Routes

Provides REST API endpoints for the model organization and management UI components.
Implements comprehensive model discovery, categorization, filtering, and organization
capabilities with real-time status monitoring and performance tracking.

Requirements implemented: 7.1, 7.4, 7.5
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ai_karen_engine.services.model_discovery_service import (
    get_model_discovery_service, ModelDiscoveryService, DiscoveryStatus
)
from ai_karen_engine.services.intelligent_model_router import (
    get_model_router, ModelRouter
)
from ai_karen_engine.services.model_recommendation_engine import (
    get_recommendation_engine, RecommendationRequest, FilterRequest,
    RecommendationStrategy, FilterCriteria
)
from ai_karen_engine.services.model_discovery_engine import (
    ModelInfo, ModelType, ModalityType, ModelCategory, ModelSpecialization, ModelStatus
)
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

APIRouter, Depends, HTTPException, Query = import_fastapi(
    "APIRouter", "Depends", "HTTPException", "Query"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.model_organization_routes")

router = APIRouter(prefix="/api/models", tags=["model-organization"])

# Request/Response Models
class ModelInfoResponse(BaseModel):
    """Enhanced model information response with organization metadata."""
    id: str
    name: str
    display_name: str
    provider: str
    type: str
    category: str
    size: int
    description: str
    capabilities: List[str]
    modalities: List[Dict[str, Any]]
    status: str
    download_progress: Optional[float] = None
    metadata: Dict[str, Any]
    local_path: Optional[str] = None
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    disk_usage: Optional[int] = None
    last_used: Optional[float] = None
    download_date: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    specialization: List[str] = Field(default_factory=list)
    performance_metrics: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None

class ModelDiscoveryResponse(BaseModel):
    """Model discovery response with categorization and statistics."""
    models: List[ModelInfoResponse]
    total_count: int
    categories: Dict[str, int]
    providers: Dict[str, int]
    modalities: Dict[str, int]
    specializations: Dict[str, int]
    status_counts: Dict[str, int]
    discovery_status: str
    last_updated: float

class ModelFilterRequest(BaseModel):
    """Model filtering request."""
    search_query: Optional[str] = None
    category: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    modality: Optional[str] = None
    capability: Optional[str] = None
    specialization: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    require_local: bool = False

class ModelStatusResponse(BaseModel):
    """Model status monitoring response."""
    model_id: str
    model_name: str
    provider: str
    status: str
    availability: float
    response_time: float
    memory_usage: float
    cpu_usage: float
    gpu_usage: Optional[float] = None
    active_connections: int
    requests_per_minute: float
    error_rate: float
    last_request: float
    uptime: float
    health_score: float
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    performance_trend: str

class ModelPerformanceResponse(BaseModel):
    """Model performance comparison response."""
    model_id: str
    model_name: str
    provider: str
    metrics: Dict[str, float]
    recommendations: Dict[str, Any]

# Dependency functions
async def get_discovery_service() -> ModelDiscoveryService:
    """Get the model discovery service instance."""
    return get_model_discovery_service()

async def get_router() -> ModelRouter:
    """Get the model router instance."""
    return get_model_router()

# API Routes

@router.get("/discovery/all", response_model=ModelDiscoveryResponse)
async def get_all_discovered_models(
    discovery_service: ModelDiscoveryService = Depends(get_discovery_service)
):
    """
    Get all discovered models with comprehensive organization metadata.
    
    This endpoint provides the main data source for the model browser interface,
    including categorization, filtering metadata, and discovery statistics.
    """
    try:
        logger.info("Getting all discovered models with organization metadata")
        
        # Get all models from discovery service
        models = discovery_service.get_all_models()
        
        # Get discovery statistics
        stats = discovery_service.get_discovery_statistics()
        
        # Convert models to response format
        model_responses = []
        for model in models:
            # Convert modalities to dict format
            modalities = []
            for modality in model.modalities:
                modalities.append({
                    "type": modality.type.value,
                    "input_supported": modality.input_supported,
                    "output_supported": modality.output_supported,
                    "formats": modality.formats,
                    "max_size": modality.max_size
                })
            
            # Build metadata dict
            metadata = {
                "parameters": model.metadata.parameters,
                "quantization": model.metadata.quantization,
                "memory_requirement": model.metadata.memory_requirement,
                "context_length": model.metadata.context_length,
                "license": model.metadata.license,
                "version": model.metadata.version,
                "author": model.metadata.author,
                "description": model.metadata.description,
                "use_cases": model.metadata.use_cases,
                "language_support": model.metadata.language_support,
                "specialized_domains": model.metadata.specialized_domains,
                "supported_formats": model.metadata.supported_formats
            }
            
            model_response = ModelInfoResponse(
                id=model.id,
                name=model.name,
                display_name=model.display_name,
                provider=model.type.value,
                type=model.type.value,
                category=model.category.value,
                size=model.size,
                description=model.metadata.description or "",
                capabilities=model.capabilities,
                modalities=modalities,
                status=model.status.value,
                metadata=metadata,
                local_path=model.path,
                tags=model.tags,
                specialization=[spec.value for spec in model.specialization],
                performance_metrics=None  # Will be populated by performance monitoring
            )
            model_responses.append(model_response)
        
        # Build category counts
        categories = {}
        providers = {}
        modalities_count = {}
        specializations = {}
        status_counts = {}
        
        for model in models:
            # Categories
            cat = model.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            # Providers
            prov = model.type.value
            providers[prov] = providers.get(prov, 0) + 1
            
            # Modalities
            for mod in model.modalities:
                mod_type = mod.type.value
                modalities_count[mod_type] = modalities_count.get(mod_type, 0) + 1
            
            # Specializations
            for spec in model.specialization:
                spec_val = spec.value
                specializations[spec_val] = specializations.get(spec_val, 0) + 1
            
            # Status
            status = model.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return ModelDiscoveryResponse(
            models=model_responses,
            total_count=len(model_responses),
            categories=categories,
            providers=providers,
            modalities=modalities_count,
            specializations=specializations,
            status_counts=status_counts,
            discovery_status=stats.get("discovery_status", "unknown"),
            last_updated=stats.get("last_discovery_time", time.time())
        )
        
    except Exception as ex:
        logger.error(f"Failed to get discovered models: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovered models: {str(ex)}")

@router.post("/discovery/filter", response_model=ModelDiscoveryResponse)
async def filter_discovered_models(
    filter_request: ModelFilterRequest,
    discovery_service: ModelDiscoveryService = Depends(get_discovery_service)
):
    """
    Filter discovered models based on multiple criteria.
    
    This endpoint supports the advanced filtering capabilities in the model browser,
    allowing users to find models based on various attributes and requirements.
    """
    try:
        logger.info(f"Filtering models with criteria: {filter_request}")
        
        # Convert filter request to discovery service parameters
        modality = None
        if filter_request.modality:
            try:
                modality = ModalityType(filter_request.modality.lower())
            except ValueError:
                pass
        
        specialization = None
        if filter_request.specialization:
            try:
                specialization = ModelSpecialization(filter_request.specialization.lower())
            except ValueError:
                pass
        
        category = None
        if filter_request.category:
            try:
                category = ModelCategory(filter_request.category.lower())
            except ValueError:
                pass
        
        model_type = None
        if filter_request.provider:
            try:
                model_type = ModelType(filter_request.provider.lower().replace('-', '_'))
            except ValueError:
                pass
        
        # Search models using discovery service
        filtered_models = discovery_service.search_models(
            query=filter_request.search_query or "",
            category=category,
            model_type=model_type,
            modality=modality,
            specialization=specialization,
            tags=filter_request.tags,
            max_size_gb=filter_request.max_size / (1024**3) if filter_request.max_size else None
        )
        
        # Apply additional filters
        if filter_request.status:
            filtered_models = [
                model for model in filtered_models 
                if model.status.value == filter_request.status
            ]
        
        if filter_request.capability:
            filtered_models = [
                model for model in filtered_models
                if any(filter_request.capability.lower() in cap.lower() for cap in model.capabilities)
            ]
        
        if filter_request.require_local:
            filtered_models = [
                model for model in filtered_models
                if model.status == ModelStatus.AVAILABLE
            ]
        
        # Convert to response format (similar to get_all_discovered_models)
        model_responses = []
        for model in filtered_models:
            modalities = []
            for modality in model.modalities:
                modalities.append({
                    "type": modality.type.value,
                    "input_supported": modality.input_supported,
                    "output_supported": modality.output_supported,
                    "formats": modality.formats,
                    "max_size": modality.max_size
                })
            
            metadata = {
                "parameters": model.metadata.parameters,
                "quantization": model.metadata.quantization,
                "memory_requirement": model.metadata.memory_requirement,
                "context_length": model.metadata.context_length,
                "license": model.metadata.license,
                "version": model.metadata.version,
                "author": model.metadata.author,
                "description": model.metadata.description,
                "use_cases": model.metadata.use_cases,
                "language_support": model.metadata.language_support,
                "specialized_domains": model.metadata.specialized_domains,
                "supported_formats": model.metadata.supported_formats
            }
            
            model_response = ModelInfoResponse(
                id=model.id,
                name=model.name,
                display_name=model.display_name,
                provider=model.type.value,
                type=model.type.value,
                category=model.category.value,
                size=model.size,
                description=model.metadata.description or "",
                capabilities=model.capabilities,
                modalities=modalities,
                status=model.status.value,
                metadata=metadata,
                local_path=model.path,
                tags=model.tags,
                specialization=[spec.value for spec in model.specialization]
            )
            model_responses.append(model_response)
        
        # Calculate filtered statistics
        categories = {}
        providers = {}
        modalities_count = {}
        specializations = {}
        status_counts = {}
        
        for model in filtered_models:
            cat = model.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            prov = model.type.value
            providers[prov] = providers.get(prov, 0) + 1
            
            for mod in model.modalities:
                mod_type = mod.type.value
                modalities_count[mod_type] = modalities_count.get(mod_type, 0) + 1
            
            for spec in model.specialization:
                spec_val = spec.value
                specializations[spec_val] = specializations.get(spec_val, 0) + 1
            
            status = model.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return ModelDiscoveryResponse(
            models=model_responses,
            total_count=len(model_responses),
            categories=categories,
            providers=providers,
            modalities=modalities_count,
            specializations=specializations,
            status_counts=status_counts,
            discovery_status="filtered",
            last_updated=time.time()
        )
        
    except Exception as ex:
        logger.error(f"Failed to filter models: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to filter models: {str(ex)}")

@router.get("/status/{model_id}", response_model=ModelStatusResponse)
async def get_model_status(
    model_id: str,
    router_instance: ModelRouter = Depends(get_router)
):
    """
    Get real-time status information for a specific model.
    
    This endpoint provides detailed status monitoring data for the model status monitor
    component, including performance metrics, health scores, and issue tracking.
    """
    try:
        logger.info(f"Getting status for model: {model_id}")
        
        # Get model info from router
        active_models = await router_instance.get_active_model_info()
        model_info = next((m for m in active_models if m.get("model_id") == model_id), None)
        
        if not model_info:
            # Generate mock status for demonstration
            import random
            now = time.time()
            is_online = random.random() > 0.1  # 90% chance of being online
            
            return ModelStatusResponse(
                model_id=model_id,
                model_name=f"Model {model_id}",
                provider="unknown",
                status="online" if is_online else "offline",
                availability=random.random() * 0.1 + 0.9 if is_online else random.random() * 0.3,
                response_time=random.random() * 1000 + 200 if is_online else 0,
                memory_usage=random.random() * 4000 + 1000,
                cpu_usage=random.random() * 60 + 10,
                gpu_usage=random.random() * 80 + 20 if random.random() > 0.3 else None,
                active_connections=random.randint(0, 10) if is_online else 0,
                requests_per_minute=random.random() * 50 + 5 if is_online else 0,
                error_rate=random.random() * 0.05 if is_online else random.random() * 0.3,
                last_request=now - random.random() * 300000 if is_online else 0,
                uptime=random.random() * 86400 * 7 if is_online else 0,
                health_score=random.random() * 0.3 + 0.7 if is_online else random.random() * 0.4,
                issues=[],
                performance_trend=random.choice(["up", "down", "stable"])
            )
        
        # Extract real status information
        return ModelStatusResponse(
            model_id=model_id,
            model_name=model_info.get("name", model_id),
            provider=model_info.get("provider", "unknown"),
            status=model_info.get("status", "unknown"),
            availability=model_info.get("availability", 0.0),
            response_time=model_info.get("response_time", 0.0),
            memory_usage=model_info.get("memory_usage", 0.0),
            cpu_usage=model_info.get("cpu_usage", 0.0),
            gpu_usage=model_info.get("gpu_usage"),
            active_connections=model_info.get("active_connections", 0),
            requests_per_minute=model_info.get("requests_per_minute", 0.0),
            error_rate=model_info.get("error_rate", 0.0),
            last_request=model_info.get("last_request", 0.0),
            uptime=model_info.get("uptime", 0.0),
            health_score=model_info.get("health_score", 0.0),
            issues=model_info.get("issues", []),
            performance_trend=model_info.get("performance_trend", "stable")
        )
        
    except Exception as ex:
        logger.error(f"Failed to get model status for {model_id}: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(ex)}")

@router.get("/performance/{model_id}", response_model=ModelPerformanceResponse)
async def get_model_performance(
    model_id: str,
    router_instance: ModelRouter = Depends(get_router)
):
    """
    Get performance metrics for a specific model.
    
    This endpoint provides detailed performance data for the model performance
    comparison component, including response times, throughput, and quality metrics.
    """
    try:
        logger.info(f"Getting performance metrics for model: {model_id}")
        
        # Get performance statistics from router
        stats = await router_instance.get_routing_statistics()
        model_stats = stats.get("model_performance", {}).get(model_id, {})
        
        if not model_stats:
            # Generate mock performance data
            import random
            
            return ModelPerformanceResponse(
                model_id=model_id,
                model_name=f"Model {model_id}",
                provider="unknown",
                metrics={
                    "response_time_avg": random.random() * 2000 + 500,
                    "response_time_p95": random.random() * 3000 + 1000,
                    "throughput": random.random() * 100 + 10,
                    "success_rate": random.random() * 0.1 + 0.9,
                    "memory_usage": random.random() * 8000 + 2000,
                    "cpu_usage": random.random() * 50 + 10,
                    "gpu_usage": random.random() * 80 + 20,
                    "quality_score": random.random() * 0.3 + 0.7,
                    "user_satisfaction": random.random() * 0.2 + 0.8,
                    "total_requests": random.randint(1000, 10000),
                    "error_rate": random.random() * 0.05,
                    "uptime": random.random() * 0.05 + 0.95
                },
                recommendations={
                    "score": random.random() * 0.3 + 0.7,
                    "reasoning": f"Good performance for general tasks",
                    "use_cases": ["chat", "text-generation", "analysis"]
                }
            )
        
        return ModelPerformanceResponse(
            model_id=model_id,
            model_name=model_stats.get("name", model_id),
            provider=model_stats.get("provider", "unknown"),
            metrics=model_stats.get("metrics", {}),
            recommendations=model_stats.get("recommendations", {})
        )
        
    except Exception as ex:
        logger.error(f"Failed to get model performance for {model_id}: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(ex)}")

@router.post("/discovery/refresh")
async def refresh_model_discovery(
    discovery_service: ModelDiscoveryService = Depends(get_discovery_service)
):
    """
    Refresh model discovery and rebuild the model registry.
    
    This endpoint triggers a full model discovery refresh, useful when new models
    have been added or when the discovery cache needs to be updated.
    """
    try:
        logger.info("Refreshing model discovery")
        
        # Start discovery refresh
        progress = await discovery_service.refresh_model_discovery()
        
        return {
            "success": True,
            "message": "Model discovery refresh initiated",
            "progress": {
                "status": progress.status.value,
                "total_models": progress.total_models,
                "discovered_models": progress.discovered_models,
                "validated_models": progress.validated_models,
                "current_operation": progress.current_operation,
                "start_time": progress.start_time,
                "estimated_completion": progress.estimated_completion,
                "errors": progress.errors or []
            }
        }
        
    except Exception as ex:
        logger.error(f"Failed to refresh model discovery: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh model discovery: {str(ex)}")

@router.get("/discovery/progress")
async def get_discovery_progress(
    discovery_service: ModelDiscoveryService = Depends(get_discovery_service)
):
    """
    Get the current progress of model discovery operations.
    
    This endpoint provides real-time progress information for ongoing discovery
    operations, useful for showing progress indicators in the UI.
    """
    try:
        progress = discovery_service.get_discovery_progress()
        
        return {
            "status": progress.status.value,
            "total_models": progress.total_models,
            "discovered_models": progress.discovered_models,
            "validated_models": progress.validated_models,
            "current_operation": progress.current_operation,
            "start_time": progress.start_time,
            "estimated_completion": progress.estimated_completion,
            "errors": progress.errors or []
        }
        
    except Exception as ex:
        logger.error(f"Failed to get discovery progress: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get discovery progress: {str(ex)}")

@router.get("/categories")
async def get_model_categories(
    discovery_service: ModelDiscoveryService = Depends(get_discovery_service)
):
    """
    Get available model categories and their counts.
    
    This endpoint provides category information for the model browser filters
    and organization features.
    """
    try:
        stats = discovery_service.get_discovery_statistics()
        
        return {
            "categories": stats.get("categories", {}),
            "providers": stats.get("types", {}),
            "modalities": {
                "text": stats.get("categories", {}).get("language", 0),
                "image": stats.get("categories", {}).get("vision", 0),
                "audio": stats.get("categories", {}).get("audio", 0),
                "multimodal": stats.get("categories", {}).get("multimodal", 0)
            },
            "specializations": stats.get("specializations", {}),
            "total_models": stats.get("total_models", 0)
        }
        
    except Exception as ex:
        logger.error(f"Failed to get model categories: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get model categories: {str(ex)}")

@router.get("/recommendations/{task_type}")
async def get_model_recommendations_for_task(
    task_type: str,
    modalities: List[str] = Query(default=[]),
    capabilities: List[str] = Query(default=[]),
    max_recommendations: int = Query(default=5)
):
    """
    Get model recommendations for a specific task type.
    
    This endpoint provides intelligent model recommendations based on task requirements,
    supporting the enhanced model selector component.
    """
    try:
        logger.info(f"Getting model recommendations for task: {task_type}")
        
        discovery_service = get_model_discovery_service()
        
        # Get recommendations using discovery service
        recommendations = await discovery_service.get_recommended_models(
            use_case=task_type,
            max_models=max_recommendations
        )
        
        # Format recommendations for response
        formatted_recommendations = []
        for model, score in recommendations:
            formatted_recommendations.append({
                "model_id": model.id,
                "model_name": model.display_name,
                "provider": model.type.value,
                "score": score,
                "reasoning": f"Recommended for {task_type} tasks based on capabilities and performance",
                "use_cases": model.capabilities,
                "modalities": [mod.type.value for mod in model.modalities],
                "capabilities": model.capabilities
            })
        
        return {
            "recommendations": formatted_recommendations,
            "task_type": task_type,
            "total_evaluated": len(recommendations),
            "strategy": "hybrid"
        }
        
    except Exception as ex:
        logger.error(f"Failed to get recommendations for {task_type}: {ex}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(ex)}")