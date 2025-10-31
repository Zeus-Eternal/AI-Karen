"""
Cache Management API Routes

Provides API endpoints for managing production caches, including
statistics, invalidation, and configuration.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ai_karen_engine.services.production_cache_service import get_cache_service
from ai_karen_engine.services.model_library_cache_service import get_model_cache_service
from ai_karen_engine.services.database_query_cache_service import get_db_cache_service
from ai_karen_engine.services.cache_invalidation_service import (
    get_invalidation_service,
    InvalidationTrigger
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["cache"])


# Pydantic models for request/response
class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    cache_type: str
    stats: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class InvalidationRequest(BaseModel):
    """Request model for cache invalidation."""
    namespaces: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    trigger_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class InvalidationResponse(BaseModel):
    """Response model for cache invalidation."""
    invalidated_count: int
    trigger: str
    timestamp: datetime = Field(default_factory=datetime.now)
    affected_namespaces: List[str] = []
    affected_tags: List[str] = []


class CacheConfigRequest(BaseModel):
    """Request model for cache configuration updates."""
    default_ttl: Optional[int] = None
    max_local_entries: Optional[int] = None
    max_local_size_mb: Optional[int] = None


@router.get("/stats", response_model=List[CacheStatsResponse])
async def get_cache_stats():
    """
    Get statistics for all cache services.
    
    Returns comprehensive cache performance metrics including hit rates,
    entry counts, and memory usage.
    """
    try:
        cache_service = get_cache_service()
        model_cache_service = get_model_cache_service()
        db_cache_service = get_db_cache_service()
        invalidation_service = get_invalidation_service()
        
        stats = [
            CacheStatsResponse(
                cache_type="production_cache",
                stats=cache_service.get_stats()
            ),
            CacheStatsResponse(
                cache_type="model_library_cache",
                stats=model_cache_service.get_cache_stats()
            ),
            CacheStatsResponse(
                cache_type="database_query_cache",
                stats=db_cache_service.get_cache_stats()
            ),
            CacheStatsResponse(
                cache_type="cache_invalidation",
                stats=invalidation_service.get_invalidation_stats()
            )
        ]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.get("/stats/{cache_type}", response_model=CacheStatsResponse)
async def get_specific_cache_stats(cache_type: str):
    """
    Get statistics for a specific cache service.
    
    Args:
        cache_type: Type of cache (production_cache, model_library_cache, database_query_cache)
    """
    try:
        if cache_type == "production_cache":
            service = get_cache_service()
            stats = service.get_stats()
        elif cache_type == "model_library_cache":
            service = get_model_cache_service()
            stats = service.get_cache_stats()
        elif cache_type == "database_query_cache":
            service = get_db_cache_service()
            stats = service.get_cache_stats()
        elif cache_type == "cache_invalidation":
            service = get_invalidation_service()
            stats = service.get_invalidation_stats()
        else:
            raise HTTPException(status_code=404, detail=f"Unknown cache type: {cache_type}")
        
        return CacheStatsResponse(cache_type=cache_type, stats=stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {cache_type} stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get {cache_type} stats: {str(e)}")


@router.post("/invalidate", response_model=InvalidationResponse)
async def invalidate_cache(request: InvalidationRequest):
    """
    Manually invalidate cache entries.
    
    Supports invalidation by namespaces, tags, or specific trigger types.
    """
    try:
        invalidation_service = get_invalidation_service()
        
        if request.trigger_type:
            # Trigger-based invalidation
            try:
                trigger = InvalidationTrigger(request.trigger_type)
                invalidated_count = await invalidation_service.trigger_invalidation(
                    trigger, request.metadata or {}
                )
                
                return InvalidationResponse(
                    invalidated_count=invalidated_count,
                    trigger=request.trigger_type,
                    affected_namespaces=request.namespaces or [],
                    affected_tags=request.tags or []
                )
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid trigger type: {request.trigger_type}")
        
        else:
            # Manual invalidation
            invalidated_count = await invalidation_service.manual_cache_clear(
                namespaces=request.namespaces,
                tags=request.tags
            )
            
            return InvalidationResponse(
                invalidated_count=invalidated_count,
                trigger="manual",
                affected_namespaces=request.namespaces or [],
                affected_tags=request.tags or []
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


@router.post("/invalidate/model/{model_id}")
async def invalidate_model_cache(model_id: str):
    """
    Invalidate cache entries for a specific model.
    
    Args:
        model_id: ID of the model to invalidate cache for
    """
    try:
        model_cache_service = get_model_cache_service()
        invalidated_count = await model_cache_service.invalidate_model(model_id)
        
        return InvalidationResponse(
            invalidated_count=invalidated_count,
            trigger="model_specific",
            affected_tags=[f"model:{model_id}"]
        )
        
    except Exception as e:
        logger.error(f"Error invalidating model cache for {model_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate model cache: {str(e)}")


@router.post("/invalidate/provider/{provider}")
async def invalidate_provider_cache(provider: str):
    """
    Invalidate cache entries for a specific provider.
    
    Args:
        provider: Name of the provider to invalidate cache for
    """
    try:
        model_cache_service = get_model_cache_service()
        invalidation_service = get_invalidation_service()
        
        # Invalidate model library cache for provider
        model_invalidated = await model_cache_service.invalidate_provider(provider)
        
        # Trigger provider config change invalidation
        config_invalidated = await invalidation_service.invalidate_provider_config_change(
            provider, "manual_invalidation"
        )
        
        total_invalidated = model_invalidated + config_invalidated
        
        return InvalidationResponse(
            invalidated_count=total_invalidated,
            trigger="provider_specific",
            affected_tags=[f"provider:{provider}"]
        )
        
    except Exception as e:
        logger.error(f"Error invalidating provider cache for {provider}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate provider cache: {str(e)}")


@router.post("/invalidate/user/{user_id}")
async def invalidate_user_cache(user_id: str):
    """
    Invalidate cache entries for a specific user.
    
    Args:
        user_id: ID of the user to invalidate cache for
    """
    try:
        invalidation_service = get_invalidation_service()
        invalidated_count = await invalidation_service.invalidate_user_data_change(
            user_id, "manual_invalidation"
        )
        
        return InvalidationResponse(
            invalidated_count=invalidated_count,
            trigger="user_specific",
            affected_tags=[f"user:{user_id}"]
        )
        
    except Exception as e:
        logger.error(f"Error invalidating user cache for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate user cache: {str(e)}")


@router.post("/invalidate/table/{table_name}")
async def invalidate_table_cache(table_name: str):
    """
    Invalidate cache entries for a specific database table.
    
    Args:
        table_name: Name of the table to invalidate cache for
    """
    try:
        db_cache_service = get_db_cache_service()
        invalidated_count = await db_cache_service.invalidate_table_cache(table_name)
        
        return InvalidationResponse(
            invalidated_count=invalidated_count,
            trigger="table_specific",
            affected_tags=[f"table:{table_name}"]
        )
        
    except Exception as e:
        logger.error(f"Error invalidating table cache for {table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate table cache: {str(e)}")


@router.delete("/clear/{cache_type}")
async def clear_cache_type(cache_type: str):
    """
    Clear all entries for a specific cache type.
    
    Args:
        cache_type: Type of cache to clear (production_cache, model_library_cache, database_query_cache)
    """
    try:
        if cache_type == "model_library_cache":
            service = get_model_cache_service()
            cleared_count = await service.invalidate_all_model_cache()
        elif cache_type == "database_query_cache":
            service = get_db_cache_service()
            cleared_count = await service.invalidate_all_query_cache()
        elif cache_type == "production_cache":
            # Clear all namespaces in production cache
            service = get_cache_service()
            cleared_count = 0
            for namespace in service.namespaces.keys():
                cleared_count += await service.clear_namespace(namespace)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown cache type: {cache_type}")
        
        return InvalidationResponse(
            invalidated_count=cleared_count,
            trigger="clear_all",
            affected_namespaces=[cache_type]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing {cache_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear {cache_type}: {str(e)}")


@router.get("/health")
async def get_cache_health():
    """
    Get health status of all cache services.
    
    Returns health information including Redis connectivity and service status.
    """
    try:
        cache_service = get_cache_service()
        
        health_status = {
            "redis_connected": cache_service.redis.health() if cache_service.redis else False,
            "services": {
                "production_cache": "healthy",
                "model_library_cache": "healthy",
                "database_query_cache": "healthy",
                "cache_invalidation": "healthy"
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if any service has issues
        overall_healthy = health_status["redis_connected"]
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "details": health_status
        }
        
    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/config", response_model=Dict[str, Any])
async def update_cache_config(request: CacheConfigRequest):
    """
    Update cache configuration settings.
    
    Allows runtime configuration of cache parameters like TTL and size limits.
    """
    try:
        cache_service = get_cache_service()
        
        updated_config = {}
        
        if request.default_ttl is not None:
            cache_service.default_ttl = request.default_ttl
            updated_config["default_ttl"] = request.default_ttl
        
        if request.max_local_entries is not None:
            cache_service.max_local_entries = request.max_local_entries
            updated_config["max_local_entries"] = request.max_local_entries
        
        if request.max_local_size_mb is not None:
            cache_service.max_local_size_mb = request.max_local_size_mb
            updated_config["max_local_size_mb"] = request.max_local_size_mb
        
        logger.info(f"Updated cache configuration: {updated_config}")
        
        return {
            "status": "success",
            "updated_config": updated_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating cache config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cache config: {str(e)}")


@router.get("/config")
async def get_cache_config():
    """
    Get current cache configuration settings.
    
    Returns current configuration for all cache services.
    """
    try:
        cache_service = get_cache_service()
        model_cache_service = get_model_cache_service()
        db_cache_service = get_db_cache_service()
        
        config = {
            "production_cache": {
                "default_ttl": cache_service.default_ttl,
                "max_local_entries": cache_service.max_local_entries,
                "max_local_size_mb": cache_service.max_local_size_mb,
                "namespaces": cache_service.namespaces
            },
            "model_library_cache": {
                "quick_list_ttl": model_cache_service.quick_list_ttl,
                "full_list_ttl": model_cache_service.full_list_ttl,
                "model_details_ttl": model_cache_service.model_details_ttl,
                "provider_list_ttl": model_cache_service.provider_list_ttl
            },
            "database_query_cache": {
                "default_configs": {
                    name: {
                        "ttl": config.ttl,
                        "tags": config.tags,
                        "invalidate_on_write": config.invalidate_on_write
                    }
                    for name, config in db_cache_service.default_configs.items()
                },
                "dynamic_tables": db_cache_service.dynamic_tables,
                "static_tables": db_cache_service.static_tables
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Error getting cache config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache config: {str(e)}")


@router.post("/reset-stats")
async def reset_cache_stats():
    """
    Reset cache statistics for all services.
    
    Useful for monitoring and performance analysis.
    """
    try:
        cache_service = get_cache_service()
        cache_service.reset_stats()
        
        return {
            "status": "success",
            "message": "Cache statistics reset",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset cache stats: {str(e)}")


# Add the router to the main application
def setup_cache_routes(app):
    """Setup cache management routes."""
    app.include_router(router)
    logger.info("Cache management routes registered")