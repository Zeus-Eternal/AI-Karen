"""
Model Library API Routes

Provides REST API endpoints for the Model Library feature including:
- Model discovery and listing
- Model download management with progress tracking
- Model metadata retrieval
- Local model management operations

This module implements the backend API for the Model Library UI component
with comprehensive error handling and user feedback.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from ai_karen_engine.services.model_library_service import (
    ModelLibraryService,
    ModelInfo,
    DownloadTask,
    ModelMetadata
)
from ai_karen_engine.utils.dependency_checks import import_fastapi, import_pydantic

# Import comprehensive error handling
from ai_karen_engine.utils.error_handling import (
    ErrorHandler, ModelLibraryError, NetworkError, DiskSpaceError, 
    PermissionError, ValidationError, SecurityError,
    handle_network_error, handle_disk_space_error, handle_permission_error,
    handle_validation_error, handle_download_error
)

APIRouter, HTTPException, BackgroundTasks, Depends = import_fastapi(
    "APIRouter", "HTTPException", "BackgroundTasks", "Depends"
)
BaseModel, Field = import_pydantic("BaseModel", "Field")

logger = logging.getLogger("kari.model_library_routes")

router = APIRouter(prefix="/api/models", tags=["model-library"])
# Public, read-only router for unauthenticated UI access to library listing
public_router = APIRouter(prefix="/api/models/public", tags=["model-library-public"])

# Global service instance
_model_library_service: Optional[ModelLibraryService] = None

def get_model_library_service() -> ModelLibraryService:
    """Get or create the model library service instance."""
    global _model_library_service
    if _model_library_service is None:
        try:
            logger.info("Initializing ModelLibraryService...")
            _model_library_service = ModelLibraryService()
            logger.info("ModelLibraryService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ModelLibraryService: {e}")
            # Create a minimal fallback service
            _model_library_service = ModelLibraryService()
    return _model_library_service

# -----------------------------
# Request/Response Models
# -----------------------------

class ModelInfoResponse(BaseModel):
    """Model information response."""
    id: str
    name: str
    provider: str
    size: int
    description: str
    capabilities: List[str]
    status: str
    download_progress: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None
    download_url: Optional[str] = None
    checksum: Optional[str] = None
    disk_usage: Optional[int] = None
    last_used: Optional[float] = None
    download_date: Optional[float] = None

class DownloadRequest(BaseModel):
    """Model download request."""
    model_id: str

class DownloadTaskResponse(BaseModel):
    """Download task response."""
    task_id: str
    model_id: str
    url: str
    filename: str
    total_size: int
    downloaded_size: int
    progress: float
    status: str
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    estimated_time_remaining: Optional[float] = None

class ModelLibraryResponse(BaseModel):
    """Model library listing response."""
    models: List[ModelInfoResponse]
    total_count: int
    local_count: int
    available_count: int

class ModelMetadataResponse(BaseModel):
    """Model metadata response."""
    parameters: str
    quantization: str
    memory_requirement: str
    context_length: int
    license: str
    tags: List[str]
    architecture: Optional[str] = None
    training_data: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

# -----------------------------
# Model Library API Routes (Task 4.1)
# -----------------------------

@router.get("/stats")
async def get_model_library_stats():
    """
    Get model library statistics and overview information.
    
    Returns summary statistics about available models, local models,
    disk usage, and provider information.
    """
    try:
        service = get_model_library_service()
        models = service.get_available_models()
        
        # Calculate statistics
        total_models = len(models)
        local_models = len([m for m in models if m.status == 'local'])
        available_models = len([m for m in models if m.status == 'available'])
        downloading_models = len([m for m in models if m.status == 'downloading'])
        
        # Provider statistics
        providers = {}
        for model in models:
            if model.provider not in providers:
                providers[model.provider] = {
                    'total': 0,
                    'local': 0,
                    'available': 0
                }
            providers[model.provider]['total'] += 1
            if model.status == 'local':
                providers[model.provider]['local'] += 1
            elif model.status == 'available':
                providers[model.provider]['available'] += 1
        
        # Disk usage
        total_disk_usage = sum(m.disk_usage or 0 for m in models if m.disk_usage)
        
        return {
            "total_models": total_models,
            "local_models": local_models,
            "available_models": available_models,
            "downloading_models": downloading_models,
            "providers": providers,
            "total_providers": len(providers),
            "total_disk_usage_bytes": total_disk_usage,
            "total_disk_usage_gb": round(total_disk_usage / (1024**3), 2),
            "last_updated": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get model library stats: {e}")
        # Return basic fallback stats instead of raising an exception
        return {
            "total_models": 0,
            "local_models": 0,
            "available_models": 0,
            "downloading_models": 0,
            "providers": {},
            "total_providers": 0,
            "total_disk_usage_bytes": 0,
            "total_disk_usage_gb": 0,
            "last_updated": time.time(),
            "error": "Service temporarily unavailable"
        }

_MODEL_LIST_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/health")
async def model_library_health():
    """Lightweight health check for the Model Library service.

    Returns minimal, fast-to-compute information without scanning the filesystem
    or contacting remote repositories. Useful for isolating 500s.
    """
    try:
        service = get_model_library_service()
        registry_path = service.registry_path
        predefined = service.metadata_service.get_predefined_models()

        # Avoid heavy operations: do not scan models directory or compute sizes
        # Only report simple counts from already-loaded structures
        if isinstance(service.registry, dict):
            registry_models = len(service.registry.get("models", []))
        elif isinstance(service.registry, list):
            registry_models = len(service.registry)
        else:
            registry_models = 0

        return {
            "status": "ok",
            "service_initialized": True,
            "registry_path": str(registry_path),
            "registry_exists": registry_path.exists(),
            "registry_models": registry_models,
            "predefined_models": len(predefined or {}),
            "cache_keys": list(_MODEL_LIST_CACHE.keys()),
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Model library health check error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": time.time(),
        }


@router.post("/refresh")
async def refresh_model_cache():
    """
    Force refresh the model cache.
    
    Clears the current cache and rebuilds it by scanning for new models.
    Use this when you've added new models manually or want to ensure
    the latest model state is reflected.
    """
    try:
        service = get_model_library_service()
        cache_info = service.refresh_model_cache()
        
        # Also clear the API-level cache
        global _MODEL_LIST_CACHE
        _MODEL_LIST_CACHE.clear()
        
        return {
            "message": "Model cache refreshed successfully",
            "cache_info": cache_info,
            "api_cache_cleared": True
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh model cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")


@router.get("/cache-info")
async def get_cache_info():
    """
    Get information about the current cache state.
    
    Returns cache validity, age, and statistics for debugging and monitoring.
    """
    try:
        service = get_model_library_service()
        service_cache_info = service.get_cache_info()
        
        # Add API-level cache info
        api_cache_info = {
            "api_cache_keys": list(_MODEL_LIST_CACHE.keys()),
            "api_cache_entries": len(_MODEL_LIST_CACHE)
        }
        
        return {
            "service_cache": service_cache_info,
            "api_cache": api_cache_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {str(e)}")


class CacheConfigRequest(BaseModel):
    """Cache configuration request."""
    ttl_seconds: int = Field(ge=30, le=3600, description="Cache TTL in seconds (30-3600)")


@router.post("/cache-config")
async def configure_cache(request: CacheConfigRequest):
    """
    Configure cache settings.
    
    Allows setting the cache time-to-live (TTL) in seconds.
    Minimum TTL is 30 seconds, maximum is 3600 seconds (1 hour).
    """
    try:
        service = get_model_library_service()
        service.set_cache_ttl(request.ttl_seconds)
        
        return {
            "message": f"Cache TTL set to {request.ttl_seconds} seconds",
            "ttl_seconds": request.ttl_seconds
        }
        
    except Exception as e:
        logger.error(f"Failed to configure cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure cache: {str(e)}")


@router.get("/library", response_model=ModelLibraryResponse)
async def get_available_models(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    capability: Optional[str] = None,
    quick: bool = False,
    ttl: int = 30,
    force_refresh: bool = False,
):
    """
    Get all available models from the model library.
    
    Supports filtering by:
    - provider: Filter by model provider (e.g., 'llama-cpp', 'huggingface')
    - status: Filter by model status ('local', 'available', 'downloading', 'error')
    - capability: Filter by model capability (e.g., 'chat', 'text-generation')
    
    Requirements: 1.1, 1.2, 4.1, 4.2
    """
    import asyncio
    
    try:
        service = get_model_library_service()

        # Cache key includes filters and quick mode
        cache_key = f"quick={quick}|provider={provider}|status={status}|capability={capability}"
        now = time.time()
        cached = _MODEL_LIST_CACHE.get(cache_key)
        if not force_refresh and cached and (now - cached.get("ts", 0) <= max(5, ttl)):
            return cached["payload"]

        # Set timeout for the operation (30 seconds max)
        timeout_seconds = 30
        
        async def get_models_with_timeout():
            if quick:
                # Lightweight listing: avoid recursive disk scans and size calculations
                raw = service.registry.get("models", []) if isinstance(service.registry, dict) else []
                predefined = service.metadata_service.get_predefined_models()
                seen_ids = set()
                model_responses: List[ModelInfoResponse] = []
                
                # Also try to get models from discovery cache directly
                discovered_models = []
                try:
                    import json
                    from pathlib import Path
                    discovery_cache_path = Path("models/.discovery_cache/discovery_cache.json")
                    if discovery_cache_path.exists():
                        with open(discovery_cache_path, 'r') as f:
                            discovery_data = json.load(f)
                        logger.debug(f"Found {len(discovery_data)} models in discovery cache")
                        
                        # Convert discovery cache entries to model objects
                        for model_id, model_data in discovery_data.items():
                            try:
                                # Create a simple model object from discovery data
                                class DiscoveredModel:
                                    def __init__(self, data):
                                        self.id = data.get('id', model_id)
                                        self.name = data.get('name', model_id)
                                        self.type = data.get('type', 'unknown')
                                        self.size = data.get('size', 0)
                                        self.status = data.get('status', 'available')
                                        self.capabilities = data.get('capabilities', [])
                                        self.path = data.get('path', '')
                                        self.checksum = data.get('checksum', '')
                                        self.metadata = data.get('metadata', {})
                                
                                discovered_models.append(DiscoveredModel(model_data))
                            except Exception as e:
                                logger.debug(f"Failed to parse discovery model {model_id}: {e}")
                                continue
                    else:
                        logger.debug("Discovery cache file not found")
                except Exception as e:
                    logger.debug(f"Could not load discovery cache: {e}")
                    discovered_models = []

                # Map registry entries (local) - only include models with valid IDs
                for entry in raw:
                    try:
                        mid = str(entry.get("id") or entry.get("name") or "").strip()
                        # Skip empty names, directory entries, or cache directories
                        if (not mid or mid in seen_ids or 
                            mid in ["", "metadata_cache", "downloads", "llama-cpp", "transformers", "TinyLlama"] or
                            mid.startswith("./models/")):
                            continue
                        seen_ids.add(mid)
                        prov = str(entry.get("provider") or entry.get("type") or "local")
                        # Infer capabilities based on model type and name if not explicitly set
                        capabilities = list(entry.get("capabilities") or [])
                        if not capabilities:
                            # Add default capabilities based on provider/type and name
                            if prov in ["llama-cpp", "llama-gguf"] or mid.endswith(".gguf"):
                                capabilities = ["text-generation", "chat", "local-inference"]
                            elif prov == "transformers":
                                capabilities = ["text-generation", "feature-extraction"]
                                if "chat" in mid.lower() or "dialog" in mid.lower():
                                    capabilities.append("chat")
                                if "bert" in mid.lower():
                                    capabilities.extend(["text-classification", "token-classification"])
                            elif prov == "hf_hub":
                                capabilities = ["text-generation", "feature-extraction"]
                        
                        model_responses.append(ModelInfoResponse(
                            id=mid,
                            name=str(entry.get("name") or mid),
                            provider=prov,
                            size=0,
                            description=(entry.get("metadata") or {}).get("description", f"Local model: {mid}"),
                            capabilities=capabilities,
                            status="local",
                            download_progress=None,
                            metadata=entry.get("metadata") or {},
                            local_path=str(entry.get("path") or ""),
                            download_url=None,
                            checksum=None,
                            disk_usage=None,
                            last_used=entry.get("last_used"),
                            download_date=(entry.get("downloadInfo") or {}).get("downloadDate"),
                        ))
                    except Exception as map_err:
                        logger.debug(f"Quick map registry entry failed: {map_err}")
                        continue

                # Add discovered models from discovery engine
                for discovered_model in discovered_models:
                    try:
                        mid = discovered_model.id
                        if mid in seen_ids:
                            continue
                        seen_ids.add(mid)
                        
                        # Map discovery engine model to API response
                        model_responses.append(ModelInfoResponse(
                            id=mid,
                            name=discovered_model.name,
                            provider=discovered_model.type,  # discovery engine uses 'type' field
                            size=int(discovered_model.size or 0),
                            description=discovered_model.metadata.description if discovered_model.metadata else f"Discovered model: {discovered_model.name}",
                            capabilities=list(discovered_model.capabilities or []),
                            status=discovered_model.status,
                            download_progress=None,
                            metadata={
                                "category": discovered_model.category.value if hasattr(discovered_model.category, 'value') else str(discovered_model.category),
                                "specialization": [s.value if hasattr(s, 'value') else str(s) for s in (discovered_model.specialization or [])],
                                "tags": discovered_model.tags or [],
                                "requirements": discovered_model.requirements.__dict__ if discovered_model.requirements else {},
                                "modalities": [m.__dict__ if hasattr(m, '__dict__') else m for m in (discovered_model.modalities or [])]
                            } if discovered_model.metadata else {},
                            local_path=discovered_model.path,
                            download_url=None,
                            checksum=discovered_model.checksum,
                            disk_usage=None,
                            last_used=None,
                            download_date=None,
                        ))
                    except Exception as map_err:
                        logger.debug(f"Quick map discovered model failed: {map_err}")
                        continue
                
                # Add predefined available models not already local
                for mid, pdata in predefined.items():
                    if mid in seen_ids:
                        continue
                    try:
                        # Safely convert metadata dataclass to dict when present
                        _meta = None
                        try:
                            from dataclasses import asdict as _asdict
                            if pdata.get("metadata") is not None:
                                _meta = _asdict(pdata.get("metadata"))
                        except Exception:
                            _meta = None
                        model_responses.append(ModelInfoResponse(
                            id=mid,
                            name=pdata.get("name", mid),
                            provider=pdata.get("provider", "llama-cpp"),
                            size=int(pdata.get("size") or 0),
                            description=pdata.get("description"),
                            capabilities=list(pdata.get("capabilities") or []),
                            status="available",
                            download_progress=None,
                            metadata=_meta,
                            local_path=None,
                            download_url=pdata.get("download_url"),
                            checksum=pdata.get("checksum"),
                            disk_usage=None,
                            last_used=None,
                            download_date=None,
                        ))
                    except Exception as map_err:
                        logger.debug(f"Quick map predefined entry failed: {map_err}")
                        continue
                
                return model_responses
            else:
                # Full listing with timeout protection
                try:
                    models = await asyncio.wait_for(
                        asyncio.to_thread(service.get_available_models_fast, force_refresh), 
                        timeout=25  # 25 second timeout for the service call
                    )
                    logger.info(f"Retrieved {len(models)} models from service")
                    return models
                except asyncio.TimeoutError:
                    logger.warning("Model library service timed out, falling back to quick mode")
                    # Fall back to quick mode
                    return await get_models_with_timeout()
                except Exception as e:
                    logger.error(f"Failed to get models from service: {e}")
                    return []

        try:
            # Execute with overall timeout
            models_data = await asyncio.wait_for(get_models_with_timeout(), timeout=timeout_seconds)
            
            if isinstance(models_data, list) and len(models_data) > 0 and hasattr(models_data[0], 'id'):
                # Full model objects from service
                filtered_models = models_data
            else:
                # Model response objects from quick mode
                filtered_models = models_data
                
        except asyncio.TimeoutError:
            logger.warning("Model library service timed out, returning empty response")
            return ModelLibraryResponse(
                models=[],
                total_count=0,
                local_count=0,
                available_count=0
            )
        
        # Apply filters
        if isinstance(filtered_models, list) and len(filtered_models) > 0:
            if hasattr(filtered_models[0], 'id'):
                # Full model objects from service
                if provider:
                    filtered_models = [m for m in filtered_models if m.provider == provider]
                if status:
                    filtered_models = [m for m in filtered_models if m.status == status]
                if capability:
                    filtered_models = [m for m in filtered_models if capability in m.capabilities]
                
                # Convert to response format
                model_responses = []
                for model in filtered_models:
                    try:
                        # Coerce/guard against bad entries from registry
                        provider_name = (model.provider or "unknown").strip()
                        capabilities = list(model.capabilities or [])
                        model_responses.append(ModelInfoResponse(
                            id=str(model.id or model.name or provider_name),
                            name=str(model.name or provider_name),
                            provider=provider_name,
                            size=int(model.size or 0),
                            description=model.description,
                            capabilities=capabilities,
                            status=model.status,
                            download_progress=model.download_progress,
                            metadata=model.metadata,
                            local_path=model.local_path,
                            download_url=model.download_url,
                            checksum=model.checksum,
                            disk_usage=model.disk_usage,
                            last_used=model.last_used,
                            download_date=model.download_date
                        ))
                    except Exception as map_err:
                        logger.warning(f"Skipping malformed model entry: {getattr(model,'name',None)} ({map_err})")
                        continue
            else:
                # Already in response format from quick mode
                model_responses = filtered_models
                if provider:
                    model_responses = [m for m in model_responses if m.provider == provider]
                if status:
                    model_responses = [m for m in model_responses if m.status == status]
                if capability:
                    model_responses = [m for m in model_responses if capability in (m.capabilities or [])]
        else:
            model_responses = []
        
        # Calculate counts
        local_count = len([m for m in model_responses if m.status == 'local'])
        available_count = len([m for m in model_responses if m.status == 'available'])
        
        payload = ModelLibraryResponse(
            models=model_responses,
            total_count=len(model_responses),
            local_count=local_count,
            available_count=available_count
        )
        
        # Cache the result
        _MODEL_LIST_CACHE[cache_key] = {"ts": now, "payload": payload}
        return payload


 
        
        # Apply filters
        filtered_models = []
        if quick:
            # Convert ModelInfoResponse list to filtering domain as dicts
            tmp = model_responses
            # Apply filters
            if provider:
                tmp = [m for m in tmp if m.provider == provider]
            if status:
                tmp = [m for m in tmp if m.status == status]
            if capability:
                tmp = [m for m in tmp if capability in (m.capabilities or [])]
            # Already in response format
            result_payload = ModelLibraryResponse(
                models=tmp,
                total_count=len(tmp),
                local_count=len([m for m in tmp if m.status == 'local']),
                available_count=len([m for m in tmp if m.status == 'available'])
            )
            _MODEL_LIST_CACHE[cache_key] = {"ts": now, "payload": result_payload}
            return result_payload
        else:
            filtered_models = models
        
        if provider:
            filtered_models = [m for m in filtered_models if m.provider == provider]
        
        if status:
            filtered_models = [m for m in filtered_models if m.status == status]
        
        if capability:
            filtered_models = [m for m in filtered_models if capability in m.capabilities]
        
        # Convert to response format
        model_responses = []
        for model in filtered_models:
            try:
                # Coerce/guard against bad entries from registry
                provider = (model.provider or "unknown").strip()
                capabilities = list(model.capabilities or [])
                model_responses.append(ModelInfoResponse(
                    id=str(model.id or model.name or provider),
                    name=str(model.name or provider),
                    provider=provider,
                    size=int(model.size or 0),
                    description=model.description,
                    capabilities=capabilities,
                    status=model.status,
                    download_progress=model.download_progress,
                    metadata=model.metadata,
                    local_path=model.local_path,
                    download_url=model.download_url,
                    checksum=model.checksum,
                    disk_usage=model.disk_usage,
                    last_used=model.last_used,
                    download_date=model.download_date
                ))
            except Exception as map_err:
                logger.warning(f"Skipping malformed model entry: {getattr(model,'name',None)} ({map_err})")
                continue
        
        # Calculate counts
        local_count = len([m for m in models if m.status == 'local'])
        available_count = len([m for m in models if m.status == 'available'])
        
        payload = ModelLibraryResponse(
            models=model_responses,
            total_count=len(model_responses),
            local_count=local_count,
            available_count=available_count
        )
        _MODEL_LIST_CACHE[cache_key] = {"ts": now, "payload": payload}
        return payload
        
    except ModelLibraryError as e:
        # Graceful fallback: don't break the UI on library errors
        logger.error(f"Model library error getting available models: {e.error_info.message}")
        # Return an empty, well-formed payload so the UI can render with zero models
        return ModelLibraryResponse(
            models=[],
            total_count=0,
            local_count=0,
            available_count=0,
        )
        
    except Exception as e:
        # Graceful fallback on unexpected errors
        logger.error(f"Unexpected error getting available models: {e}")
        return ModelLibraryResponse(
            models=[],
            total_count=0,
            local_count=0,
            available_count=0,
        )

@router.post("/download", response_model=DownloadTaskResponse)
async def initiate_model_download(request: DownloadRequest):
    """
    Initiate download of a model from the library.
    
    Creates a download task and returns task information for progress tracking.
    The download runs in the background and can be monitored using the task_id.
    
    Requirements: 1.1, 1.2, 4.1, 4.2
    """
    try:
        service = get_model_library_service()
        
        # Validate model exists and is available for download
        model_info = service.get_model_info(request.model_id)
        if not model_info:
            error_info = handle_validation_error(
                "model_id", 
                f"Model {request.model_id} not found",
                {"model_id": request.model_id, "operation": "download"}
            )
            error_handler = ErrorHandler()
            error_response = error_handler.create_error_response(error_info)
            raise HTTPException(status_code=404, detail=error_response)
        
        if model_info.status == 'local':
            error_info = handle_validation_error(
                "model_status", 
                f"Model {request.model_id} is already downloaded locally",
                {"model_id": request.model_id, "current_status": model_info.status}
            )
            error_handler = ErrorHandler()
            error_response = error_handler.create_error_response(error_info)
            raise HTTPException(status_code=400, detail=error_response)
        
        if model_info.status != 'available':
            error_info = handle_validation_error(
                "model_status", 
                f"Model {request.model_id} is not available for download (status: {model_info.status})",
                {"model_id": request.model_id, "current_status": model_info.status}
            )
            error_handler = ErrorHandler()
            error_response = error_handler.create_error_response(error_info)
            raise HTTPException(status_code=400, detail=error_response)
        
        # Start download with comprehensive error handling
        download_task = service.download_model(request.model_id)
        if not download_task:
            error_info = handle_download_error(
                "initiation_failed", 
                "Failed to create download task",
                {"model_id": request.model_id}
            )
            error_handler = ErrorHandler()
            error_response = error_handler.create_error_response(error_info)
            raise HTTPException(status_code=500, detail=error_response)
        
        # Clear API cache since a download was initiated
        global _MODEL_LIST_CACHE
        _MODEL_LIST_CACHE.clear()
        
        return DownloadTaskResponse(
            task_id=download_task.task_id,
            model_id=download_task.model_id,
            url=download_task.url,
            filename=download_task.filename,
            total_size=download_task.total_size,
            downloaded_size=download_task.downloaded_size,
            progress=download_task.progress,
            status=download_task.status,
            error_message=download_task.error_message,
            start_time=download_task.start_time,
            estimated_time_remaining=download_task.estimated_time_remaining
        )
        
    except HTTPException:
        raise
    except DiskSpaceError as e:
        logger.error(f"Disk space error initiating download for {request.model_id}: {e.error_info.message}")
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(e.error_info)
        raise HTTPException(status_code=507, detail=error_response)  # 507 Insufficient Storage
        
    except PermissionError as e:
        logger.error(f"Permission error initiating download for {request.model_id}: {e.error_info.message}")
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(e.error_info)
        raise HTTPException(status_code=403, detail=error_response)
        
    except ValidationError as e:
        logger.error(f"Validation error initiating download for {request.model_id}: {e.error_info.message}")
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(e.error_info)
        raise HTTPException(status_code=400, detail=error_response)
        
    except NetworkError as e:
        logger.error(f"Network error initiating download for {request.model_id}: {e.error_info.message}")
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(e.error_info)
        raise HTTPException(status_code=502, detail=error_response)  # 502 Bad Gateway
        
    except ModelLibraryError as e:
        logger.error(f"Model library error initiating download for {request.model_id}: {e.error_info.message}")
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(e.error_info)
        raise HTTPException(status_code=500, detail=error_response)
        
    except Exception as e:
        logger.error(f"Unexpected error initiating download for {request.model_id}: {e}")
        error_info = handle_download_error(
            "unexpected", 
            f"Unexpected error during download initiation: {str(e)}",
            {"model_id": request.model_id}
        )
        error_handler = ErrorHandler()
        error_response = error_handler.create_error_response(error_info)
        raise HTTPException(status_code=500, detail=error_response)

@router.get("/download/{task_id}", response_model=DownloadTaskResponse)
async def get_download_progress(task_id: str):
    """
    Get download progress for a specific download task.
    
    Returns current progress, status, and estimated time remaining for the download.
    Use this endpoint to track download progress in real-time.
    
    Requirements: 1.1, 1.2, 4.1, 4.2
    """
    try:
        service = get_model_library_service()
        download_task = service.get_download_status(task_id)
        
        if not download_task:
            raise HTTPException(status_code=404, detail=f"Download task {task_id} not found")
        
        return DownloadTaskResponse(
            task_id=download_task.task_id,
            model_id=download_task.model_id,
            url=download_task.url,
            filename=download_task.filename,
            total_size=download_task.total_size,
            downloaded_size=download_task.downloaded_size,
            progress=download_task.progress,
            status=download_task.status,
            error_message=download_task.error_message,
            start_time=download_task.start_time,
            estimated_time_remaining=download_task.estimated_time_remaining
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download progress for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Model Management API Routes (Task 4.2)
# -----------------------------

@router.delete("/{model_id}")
async def delete_local_model(model_id: str):
    """
    Delete a local model and its files.
    
    Removes the model from the local registry and deletes associated files.
    This operation cannot be undone.
    
    Requirements: 5.1, 5.2, 3.3, 3.4
    """
    try:
        service = get_model_library_service()
        
        # Validate model exists and is local
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        if model_info.status != 'local':
            raise HTTPException(status_code=400, detail=f"Model {model_id} is not a local model")
        
        # Delete model
        success = service.delete_model(model_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete model")
        
        # Clear API cache since a model was deleted
        global _MODEL_LIST_CACHE
        _MODEL_LIST_CACHE.clear()
        
        return {
            "message": f"Model {model_id} deleted successfully",
            "model_id": model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/download/{task_id}")
async def cancel_download(task_id: str):
    """
    Cancel an active download task.
    
    Stops the download process and cleans up any partial files.
    Only active downloads can be cancelled.
    
    Requirements: 5.1, 5.2, 3.3, 3.4
    """
    try:
        service = get_model_library_service()
        
        # Check if task exists
        download_task = service.get_download_status(task_id)
        if not download_task:
            raise HTTPException(status_code=404, detail=f"Download task {task_id} not found")
        
        if download_task.status not in ['pending', 'downloading']:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel download task in status: {download_task.status}"
            )
        
        # Cancel download
        success = service.cancel_download(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel download")
        
        return {
            "message": f"Download task {task_id} cancelled successfully",
            "task_id": task_id,
            "model_id": download_task.model_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel download task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{model_id}", response_model=ModelMetadataResponse)
async def get_model_metadata(model_id: str):
    """
    Get detailed metadata for a specific model.
    
    Returns comprehensive information about the model including technical
    specifications, capabilities, and performance metrics.
    
    Requirements: 5.1, 5.2, 3.3, 3.4
    """
    try:
        service = get_model_library_service()
        
        # Get model info first to validate it exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Get detailed metadata
        metadata = service.metadata_service.get_model_metadata(model_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Metadata not found for model {model_id}")
        
        return ModelMetadataResponse(
            parameters=metadata.parameters,
            quantization=metadata.quantization,
            memory_requirement=metadata.memory_requirement,
            context_length=metadata.context_length,
            license=metadata.license,
            tags=metadata.tags,
            architecture=metadata.architecture,
            training_data=metadata.training_data,
            performance_metrics=metadata.performance_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# Additional Utility Endpoints
# -----------------------------

@router.get("/providers")
async def list_model_providers():
    """Get list of available model providers."""
    try:
        service = get_model_library_service()
        models = service.get_available_models()
        
        # Extract unique providers with counts
        provider_counts = {}
        for model in models:
            provider = model.provider
            if provider not in provider_counts:
                provider_counts[provider] = {
                    "name": provider,
                    "total_models": 0,
                    "local_models": 0,
                    "available_models": 0
                }
            
            provider_counts[provider]["total_models"] += 1
            if model.status == "local":
                provider_counts[provider]["local_models"] += 1
            elif model.status == "available":
                provider_counts[provider]["available_models"] += 1
        
        return {
            "providers": list(provider_counts.values()),
            "total_providers": len(provider_counts)
        }
        
    except Exception as e:
        logger.error(f"Failed to list model providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def list_model_capabilities():
    """Get list of available model capabilities."""
    try:
        service = get_model_library_service()
        models = service.get_available_models()
        
        # Extract unique capabilities with counts
        capability_counts = {}
        for model in models:
            for capability in model.capabilities:
                if capability not in capability_counts:
                    capability_counts[capability] = {
                        "name": capability,
                        "model_count": 0,
                        "local_count": 0
                    }
                
                capability_counts[capability]["model_count"] += 1
                if model.status == "local":
                    capability_counts[capability]["local_count"] += 1
        
        return {
            "capabilities": list(capability_counts.values()),
            "total_capabilities": len(capability_counts)
        }
        
    except Exception as e:
        logger.error(f"Failed to list model capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disk-usage")
async def get_disk_usage_info():
    """Get disk usage information for models and available space."""
    try:
        service = get_model_library_service()
        
        available_space = service.get_available_disk_space()
        total_models_usage = service.get_total_models_disk_usage()
        
        return {
            "available_space_bytes": available_space,
            "total_models_usage_bytes": total_models_usage,
            "available_space_gb": round(available_space / (1024**3), 2),
            "total_models_usage_gb": round(total_models_usage / (1024**3), 2),
            "models_directory": str(service.models_dir)
        }
        
    except Exception as e:
        logger.error(f"Failed to get disk usage info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/usage-stats")
async def get_model_usage_stats(model_id: str):
    """Get usage statistics for a specific model."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        stats = service.get_model_usage_stats(model_id)
        
        # Format response with human-readable values
        response = {
            "model_id": model_id,
            "disk_usage_bytes": stats.get("disk_usage"),
            "disk_usage_mb": round(stats.get("disk_usage", 0) / (1024**2), 2) if stats.get("disk_usage") else None,
            "last_used": stats.get("last_used"),
            "download_date": stats.get("download_date"),
            "status": stats.get("status"),
            "usage_frequency": stats.get("usage_frequency")
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get usage stats for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/validate")
async def validate_model_integrity(model_id: str):
    """Validate model file integrity and return validation results."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        validation_result = service.validate_model_integrity(model_id)
        
        return {
            "model_id": model_id,
            "validation_result": validation_result,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/mark-used")
async def mark_model_used(model_id: str):
    """Mark a model as recently used (updates last_used timestamp)."""
    try:
        service = get_model_library_service()
        
        # Validate model exists and is local
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        if model_info.status != 'local':
            raise HTTPException(status_code=400, detail=f"Model {model_id} is not a local model")
        
        success = service.mark_model_used(model_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update model usage")
        
        return {
            "message": f"Model {model_id} marked as used",
            "model_id": model_id,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark model {model_id} as used: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/disk-usage")
async def get_model_disk_usage(model_id: str):
    """Get detailed disk usage information for a specific model."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        disk_usage = service.get_detailed_disk_usage(model_id)
        
        if "error" in disk_usage:
            raise HTTPException(status_code=500, detail=disk_usage["error"])
        
        return disk_usage
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get disk usage for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/status-history")
async def get_model_status_history(model_id: str):
    """Get status change history for a specific model."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        history = service.get_model_status_history(model_id)
        
        return {
            "model_id": model_id,
            "history": history,
            "total_events": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status history for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/validate-before-use")
async def validate_model_before_use(model_id: str):
    """Validate model before use and update status accordingly."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        if model_info.status != 'local':
            raise HTTPException(status_code=400, detail=f"Model {model_id} is not a local model")
        
        validation_result = service.validate_model_before_use(model_id)
        
        return {
            "model_id": model_id,
            "validation_result": validation_result,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate model before use {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/local/summary")
async def get_local_models_summary():
    """Get summary information about all local models."""
    try:
        service = get_model_library_service()
        summary = service.get_local_models_summary()
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get local models summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup/orphaned-files")
async def cleanup_orphaned_files():
    """Clean up orphaned model files that are not in the registry."""
    try:
        service = get_model_library_service()
        cleanup_result = service.cleanup_orphaned_files()
        
        if "error" in cleanup_result:
            raise HTTPException(status_code=500, detail=cleanup_result["error"])
        
        return {
            "message": "Orphaned files cleanup completed",
            "result": cleanup_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/security-scan")
async def perform_security_scan(model_id: str):
    """Perform comprehensive security scan on a model."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        if model_info.status != 'local':
            raise HTTPException(status_code=400, detail=f"Model {model_id} is not a local model")
        
        scan_result = service.scan_model_security(model_id)
        
        if "error" in scan_result:
            raise HTTPException(status_code=500, detail=scan_result["error"])
        
        return {
            "message": f"Security scan completed for {model_id}",
            "scan_result": scan_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform security scan for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/quarantine")
async def quarantine_model(model_id: str, reason: str = "Security concern"):
    """Quarantine a model due to security concerns."""
    try:
        service = get_model_library_service()
        
        # Validate model exists
        model_info = service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        if model_info.status != 'local':
            raise HTTPException(status_code=400, detail=f"Model {model_id} is not a local model")
        
        success = service.quarantine_model(model_id, reason)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to quarantine model")
        
        return {
            "message": f"Model {model_id} has been quarantined",
            "model_id": model_id,
            "reason": reason,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to quarantine model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/validate-download")
async def validate_model_download(model_id: str):
    """Validate model before download for security and safety."""
    try:
        service = get_model_library_service()
        
        # Get predefined model data
        predefined = service.metadata_service.get_predefined_models()
        if model_id not in predefined:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found in predefined models")
        
        model_data = predefined[model_id]
        download_url = model_data.get("download_url")
        
        if not download_url:
            raise HTTPException(status_code=400, detail=f"No download URL available for model {model_id}")
        
        validation_result = service.validate_model_before_download(model_id, download_url)
        
        if "error" in validation_result:
            raise HTTPException(status_code=500, detail=validation_result["error"])
        
        return {
            "message": f"Download validation completed for {model_id}",
            "validation_result": validation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate download for model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security/quarantined")
async def list_quarantined_models():
    """List all quarantined models."""
    try:
        service = get_model_library_service()
        models = service.get_available_models()
        
        quarantined_models = []
        for model in models:
            if model.status == 'quarantined':
                # Get additional quarantine info from registry
                model_data = None
                for registry_model in service.registry["models"]:
                    if registry_model.get("id") == model.id:
                        model_data = registry_model
                        break
                
                quarantine_info = model_data.get("quarantine_info", {}) if model_data else {}
                
                quarantined_models.append({
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider,
                    "quarantine_reason": quarantine_info.get("reason", "Unknown"),
                    "quarantine_timestamp": quarantine_info.get("timestamp"),
                    "original_path": quarantine_info.get("original_path"),
                    "quarantine_path": quarantine_info.get("quarantine_path")
                })
        
        return {
            "quarantined_models": quarantined_models,
            "total_count": len(quarantined_models)
        }
        
    except Exception as e:
        logger.error(f"Failed to list quarantined models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/security/scan-summary")
async def get_security_scan_summary():
    """Get summary of security scan results for all local models."""
    try:
        service = get_model_library_service()
        local_models = service.get_models_by_status("local")
        
        summary = {
            "total_local_models": len(local_models),
            "scanned_models": 0,
            "passed_scans": 0,
            "warning_scans": 0,
            "failed_scans": 0,
            "never_scanned": 0,
            "last_scan_times": []
        }
        
        for model in local_models:
            # Get model data from registry to check scan status
            model_data = None
            for registry_model in service.registry["models"]:
                if registry_model.get("id") == model.id:
                    model_data = registry_model
                    break
            
            if model_data:
                last_scan = model_data.get("last_security_scan")
                scan_status = model_data.get("security_scan_status")
                
                if last_scan:
                    summary["scanned_models"] += 1
                    summary["last_scan_times"].append({
                        "model_id": model.id,
                        "last_scan": last_scan
                    })
                    
                    if scan_status == "passed":
                        summary["passed_scans"] += 1
                    elif scan_status == "warning":
                        summary["warning_scans"] += 1
                    elif scan_status == "failed":
                        summary["failed_scans"] += 1
                else:
                    summary["never_scanned"] += 1
        
        # Sort by most recent scan
        summary["last_scan_times"].sort(key=lambda x: x["last_scan"], reverse=True)
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get security scan summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_downloads():
    """Clean up completed download tasks."""
    try:
        service = get_model_library_service()
        service.cleanup()
        
        return {"message": "Download cleanup completed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Public, read-only endpoint mirrors the library listing without requiring auth
# Uses quick mode by default to ensure fast responses for the UI without heavy scanning
@public_router.get("/library", response_model=ModelLibraryResponse)
async def get_available_models_public(
    provider: Optional[str] = None,
    status: Optional[str] = None,
    capability: Optional[str] = None,
    quick: bool = True,  # default to quick on public path
    ttl: int = 60,
):
    try:
        return await get_available_models(
            provider=provider,
            status=status,
            capability=capability,
            quick=quick,
            ttl=ttl,
            force_refresh=False,
        )
    except Exception:
        # Never error on public endpoint; provide empty result
        return ModelLibraryResponse(models=[], total_count=0, local_count=0, available_count=0)
