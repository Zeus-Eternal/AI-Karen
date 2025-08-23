"""
Cache Management API Routes

This module provides API endpoints for monitoring and managing the various
caches used throughout the system for performance optimization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.cache import (
    get_token_cache,
    get_response_cache,
    get_provider_cache,
    get_request_deduplicator,
    cleanup_all_caches,
    get_all_cache_stats
)

logger = get_logger(__name__)
router = APIRouter(tags=["cache-management"], prefix="/cache")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    cache_name: str = Field(..., description="Name of the cache")
    size: int = Field(..., description="Current number of entries")
    max_size: int = Field(..., description="Maximum cache size")
    hit_rate: float = Field(..., description="Cache hit rate (0.0 to 1.0)")
    total_requests: int = Field(..., description="Total number of requests")
    hits: int = Field(..., description="Number of cache hits")
    misses: int = Field(..., description="Number of cache misses")
    evictions: int = Field(..., description="Number of evicted entries")
    expired_removals: int = Field(..., description="Number of expired entries removed")


class AllCacheStatsResponse(BaseModel):
    """Response model for all cache statistics"""
    timestamp: str = Field(..., description="Timestamp when stats were collected")
    caches: Dict[str, Dict[str, Any]] = Field(..., description="Statistics for all caches")
    total_memory_usage: Optional[int] = Field(None, description="Estimated total memory usage in bytes")


class CacheCleanupResponse(BaseModel):
    """Response model for cache cleanup operations"""
    timestamp: str = Field(..., description="Timestamp when cleanup was performed")
    cleaned_caches: Dict[str, int] = Field(..., description="Number of entries cleaned per cache")
    total_cleaned: int = Field(..., description="Total number of entries cleaned")


class CacheClearResponse(BaseModel):
    """Response model for cache clear operations"""
    timestamp: str = Field(..., description="Timestamp when clear was performed")
    cache_name: str = Field(..., description="Name of the cleared cache")
    entries_cleared: int = Field(..., description="Number of entries that were cleared")
    success: bool = Field(..., description="Whether the operation was successful")


@router.get("/stats", response_model=AllCacheStatsResponse)
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute per IP
async def get_cache_statistics(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> AllCacheStatsResponse:
    """
    Get comprehensive statistics for all caches
    
    This endpoint returns detailed statistics for all caching systems
    including hit rates, sizes, and performance metrics.
    
    **Rate Limiting**: 60 requests per minute per IP address
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        AllCacheStatsResponse with statistics for all caches
    """
    try:
        all_stats = get_all_cache_stats()
        
        # Calculate estimated memory usage (rough approximation)
        total_memory_usage = 0
        for cache_name, stats in all_stats.items():
            if "size" in stats:
                # Rough estimate: 1KB per cache entry
                total_memory_usage += stats["size"] * 1024
        
        return AllCacheStatsResponse(
            timestamp=datetime.utcnow().isoformat(),
            caches=all_stats,
            total_memory_usage=total_memory_usage
        )
        
    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )


@router.get("/stats/{cache_name}")
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute per IP
async def get_specific_cache_stats(
    cache_name: str,
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Get statistics for a specific cache
    
    **Available caches**: token_cache, response_cache, provider_cache, request_deduplicator
    
    Args:
        cache_name: Name of the cache to get statistics for
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with cache statistics
    """
    try:
        cache_instances = {
            "token_cache": get_token_cache(),
            "response_cache": get_response_cache(),
            "provider_cache": get_provider_cache(),
            "request_deduplicator": get_request_deduplicator()
        }
        
        if cache_name not in cache_instances:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cache '{cache_name}' not found. Available caches: {list(cache_instances.keys())}"
            )
        
        cache_instance = cache_instances[cache_name]
        stats = cache_instance.get_stats()
        
        return {
            "cache_name": cache_name,
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics for cache '{cache_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics for cache '{cache_name}'"
        )


@router.post("/cleanup", response_model=CacheCleanupResponse)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def cleanup_expired_entries(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> CacheCleanupResponse:
    """
    Clean up expired entries from all caches
    
    This endpoint removes expired entries from all caches to free up memory
    and improve performance. This operation is safe and non-destructive.
    
    **Rate Limiting**: 10 requests per minute per IP address
    **Authentication**: Requires valid user session
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        CacheCleanupResponse with cleanup results
    """
    try:
        cleaned_caches = await cleanup_all_caches()
        total_cleaned = sum(cleaned_caches.values())
        
        logger.info(
            f"Cache cleanup completed by user: {user_context.get('user_id', 'unknown')}. "
            f"Total entries cleaned: {total_cleaned}"
        )
        
        return CacheCleanupResponse(
            timestamp=datetime.utcnow().isoformat(),
            cleaned_caches=cleaned_caches,
            total_cleaned=total_cleaned
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup caches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired cache entries"
        )


@router.post("/clear/{cache_name}", response_model=CacheClearResponse)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute per IP
async def clear_specific_cache(
    cache_name: str,
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> CacheClearResponse:
    """
    Clear all entries from a specific cache
    
    **Warning**: This operation will clear ALL entries from the specified cache,
    which may temporarily impact performance until the cache is repopulated.
    
    **Available caches**: token_cache, response_cache, provider_cache
    
    **Rate Limiting**: 5 requests per minute per IP address
    **Authentication**: Requires valid user session
    
    Args:
        cache_name: Name of the cache to clear
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        CacheClearResponse with clear operation results
    """
    try:
        cache_instances = {
            "token_cache": get_token_cache(),
            "response_cache": get_response_cache(),
            "provider_cache": get_provider_cache()
        }
        
        if cache_name not in cache_instances:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cache '{cache_name}' not found or not clearable. Available caches: {list(cache_instances.keys())}"
            )
        
        cache_instance = cache_instances[cache_name]
        
        # Get current size before clearing
        current_stats = cache_instance.get_stats()
        entries_before = current_stats.get("size", 0)
        
        # Clear the cache
        cache_instance.cache.clear()
        
        logger.warning(
            f"Cache '{cache_name}' cleared by user: {user_context.get('user_id', 'unknown')}. "
            f"Entries cleared: {entries_before}"
        )
        
        return CacheClearResponse(
            timestamp=datetime.utcnow().isoformat(),
            cache_name=cache_name,
            entries_cleared=entries_before,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache '{cache_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache '{cache_name}'"
        )


@router.post("/clear-all")
@limiter.limit("2/minute")  # Rate limit: 2 requests per minute per IP
async def clear_all_caches(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Clear all cache entries from all caches
    
    **Warning**: This operation will clear ALL entries from ALL caches,
    which will significantly impact performance until caches are repopulated.
    Use this operation with caution and only when necessary.
    
    **Rate Limiting**: 2 requests per minute per IP address
    **Authentication**: Requires valid user session
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with clear operation results for all caches
    """
    try:
        cache_instances = {
            "token_cache": get_token_cache(),
            "response_cache": get_response_cache(),
            "provider_cache": get_provider_cache()
        }
        
        clear_results = {}
        total_cleared = 0
        
        for cache_name, cache_instance in cache_instances.items():
            # Get current size before clearing
            current_stats = cache_instance.get_stats()
            entries_before = current_stats.get("size", 0)
            
            # Clear the cache
            cache_instance.cache.clear()
            
            clear_results[cache_name] = {
                "entries_cleared": entries_before,
                "success": True
            }
            total_cleared += entries_before
        
        logger.critical(
            f"ALL CACHES cleared by user: {user_context.get('user_id', 'unknown')}. "
            f"Total entries cleared: {total_cleared}"
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "All caches cleared successfully",
            "total_entries_cleared": total_cleared,
            "cache_results": clear_results,
            "warning": "Performance may be temporarily impacted until caches are repopulated"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear all caches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear all caches"
        )


@router.get("/health")
@limiter.limit("120/minute")  # Rate limit: 120 requests per minute per IP
async def get_cache_health(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Get health status of all caches
    
    This endpoint provides a quick health check for all caching systems,
    including hit rates, memory usage, and performance indicators.
    
    **Rate Limiting**: 120 requests per minute per IP address
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with health status for all caches
    """
    try:
        all_stats = get_all_cache_stats()
        
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "cache_health": {}
        }
        
        for cache_name, stats in all_stats.items():
            cache_health = {
                "status": "healthy",
                "issues": []
            }
            
            # Check for potential issues
            if "hit_rate" in stats:
                hit_rate = stats["hit_rate"]
                if hit_rate < 0.3:  # Less than 30% hit rate
                    cache_health["status"] = "degraded"
                    cache_health["issues"].append(f"Low hit rate: {hit_rate:.2%}")
                elif hit_rate < 0.1:  # Less than 10% hit rate
                    cache_health["status"] = "unhealthy"
            
            if "size" in stats and "max_size" in stats:
                utilization = stats["size"] / stats["max_size"]
                if utilization > 0.9:  # More than 90% full
                    cache_health["status"] = "degraded"
                    cache_health["issues"].append(f"High utilization: {utilization:.1%}")
            
            if "evictions" in stats and stats["evictions"] > 100:
                cache_health["issues"].append(f"High eviction count: {stats['evictions']}")
            
            # Update overall status
            if cache_health["status"] == "unhealthy":
                health_status["overall_status"] = "unhealthy"
            elif cache_health["status"] == "degraded" and health_status["overall_status"] == "healthy":
                health_status["overall_status"] = "degraded"
            
            health_status["cache_health"][cache_name] = cache_health
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get cache health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache health status"
        )


@router.get("/performance-metrics")
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute per IP
async def get_performance_metrics(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Get performance metrics for all caches
    
    This endpoint provides detailed performance metrics including
    hit rates, response times, and efficiency indicators.
    
    **Rate Limiting**: 30 requests per minute per IP address
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with performance metrics for all caches
    """
    try:
        all_stats = get_all_cache_stats()
        
        performance_metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {}
        }
        
        for cache_name, stats in all_stats.items():
            metrics = {
                "cache_name": cache_name,
                "efficiency_score": 0.0,
                "performance_indicators": {}
            }
            
            # Calculate efficiency score
            if "hit_rate" in stats:
                hit_rate = stats["hit_rate"]
                metrics["performance_indicators"]["hit_rate"] = hit_rate
                metrics["efficiency_score"] += hit_rate * 0.6  # 60% weight for hit rate
            
            if "size" in stats and "max_size" in stats:
                utilization = stats["size"] / stats["max_size"]
                metrics["performance_indicators"]["utilization"] = utilization
                # Optimal utilization is around 70-80%
                utilization_score = 1.0 - abs(utilization - 0.75) / 0.75
                metrics["efficiency_score"] += max(0, utilization_score) * 0.2  # 20% weight
            
            if "evictions" in stats and "total_requests" in stats:
                eviction_rate = stats["evictions"] / max(stats["total_requests"], 1)
                metrics["performance_indicators"]["eviction_rate"] = eviction_rate
                # Lower eviction rate is better
                eviction_score = max(0, 1.0 - eviction_rate * 10)
                metrics["efficiency_score"] += eviction_score * 0.2  # 20% weight
            
            # Add deduplication metrics for request deduplicator
            if cache_name == "request_deduplicator" and "deduplication_rate" in stats:
                dedup_rate = stats["deduplication_rate"]
                metrics["performance_indicators"]["deduplication_rate"] = dedup_rate
                metrics["efficiency_score"] = dedup_rate  # Simple score for deduplicator
            
            performance_metrics["metrics"][cache_name] = metrics
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )