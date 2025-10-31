"""
Model Library Cache Service

Optimizes model library caching for the ModelSelector component and API endpoints.
Provides intelligent caching with TTL, invalidation strategies, and performance monitoring.
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from production_cache_service import get_cache_service

logger = logging.getLogger(__name__)


@dataclass
class ModelCacheEntry:
    """Represents a cached model entry."""
    model_id: str
    name: str
    provider: str
    status: str
    size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    cached_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class ModelLibraryCacheService:
    """
    Service for caching model library data with intelligent invalidation.
    
    Features:
    - Quick model list caching for fast UI loading
    - Full model details caching with longer TTL
    - Provider-specific caching
    - Status-based cache invalidation
    - Performance metrics tracking
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        
        # Cache TTL configuration (in seconds)
        self.quick_list_ttl = 300  # 5 minutes for quick lists
        self.full_list_ttl = 1800  # 30 minutes for full lists
        self.model_details_ttl = 3600  # 1 hour for individual model details
        self.provider_list_ttl = 7200  # 2 hours for provider lists
        
        # Cache keys
        self.cache_namespace = 'model_library'
        
        logger.info("Model library cache service initialized")
    
    def _generate_cache_key(self, key_type: str, **params) -> str:
        """Generate a cache key for model library data."""
        if not params:
            return key_type
        
        # Sort parameters for consistent key generation
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        if param_str:
            return f"{key_type}?{param_str}"
        return key_type
    
    def _get_cache_tags(self, model_data: Optional[Dict] = None, **params) -> List[str]:
        """Generate cache tags for invalidation."""
        tags = ['model_library']
        
        if model_data:
            if 'provider' in model_data:
                tags.append(f"provider:{model_data['provider']}")
            if 'status' in model_data:
                tags.append(f"status:{model_data['status']}")
            if 'type' in model_data:
                tags.append(f"type:{model_data['type']}")
        
        # Add parameter-based tags
        if 'provider' in params:
            tags.append(f"provider:{params['provider']}")
        if 'status' in params:
            tags.append(f"status:{params['status']}")
        if 'task' in params:
            tags.append(f"task:{params['task']}")
        
        return tags
    
    async def get_quick_model_list(self, **filters) -> Optional[List[Dict[str, Any]]]:
        """
        Get a quick model list from cache.
        
        Args:
            **filters: Optional filters (provider, status, task, etc.)
            
        Returns:
            Cached model list or None if not found
        """
        cache_key = self._generate_cache_key('quick_list', **filters)
        
        try:
            cached_data = await self.cache_service.get(self.cache_namespace, cache_key)
            if cached_data:
                logger.debug(f"Cache hit for quick model list: {cache_key}")
                return cached_data.get('models', [])
            
            logger.debug(f"Cache miss for quick model list: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting quick model list from cache: {e}")
            return None
    
    async def set_quick_model_list(self, models: List[Dict[str, Any]], **filters) -> bool:
        """
        Cache a quick model list.
        
        Args:
            models: List of model data
            **filters: Filters used to generate the list
            
        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key('quick_list', **filters)
        
        try:
            cache_data = {
                'models': models,
                'count': len(models),
                'cached_at': datetime.now().isoformat(),
                'filters': filters
            }
            
            tags = self._get_cache_tags(**filters)
            
            success = await self.cache_service.set(
                self.cache_namespace,
                cache_key,
                cache_data,
                ttl=self.quick_list_ttl,
                tags=tags
            )
            
            if success:
                logger.debug(f"Cached quick model list: {cache_key} ({len(models)} models)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching quick model list: {e}")
            return False
    
    async def get_full_model_list(self, **filters) -> Optional[Dict[str, Any]]:
        """
        Get a full model list with metadata from cache.
        
        Args:
            **filters: Optional filters
            
        Returns:
            Cached model data or None if not found
        """
        cache_key = self._generate_cache_key('full_list', **filters)
        
        try:
            cached_data = await self.cache_service.get(self.cache_namespace, cache_key)
            if cached_data:
                logger.debug(f"Cache hit for full model list: {cache_key}")
                return cached_data
            
            logger.debug(f"Cache miss for full model list: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting full model list from cache: {e}")
            return None
    
    async def set_full_model_list(self, model_data: Dict[str, Any], **filters) -> bool:
        """
        Cache a full model list with metadata.
        
        Args:
            model_data: Complete model data including counts and metadata
            **filters: Filters used to generate the list
            
        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key('full_list', **filters)
        
        try:
            # Add caching metadata
            cache_data = {
                **model_data,
                'cached_at': datetime.now().isoformat(),
                'filters': filters
            }
            
            tags = self._get_cache_tags(**filters)
            
            success = await self.cache_service.set(
                self.cache_namespace,
                cache_key,
                cache_data,
                ttl=self.full_list_ttl,
                tags=tags
            )
            
            if success:
                model_count = len(model_data.get('models', []))
                logger.debug(f"Cached full model list: {cache_key} ({model_count} models)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching full model list: {e}")
            return False
    
    async def get_model_details(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get individual model details from cache.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Cached model details or None if not found
        """
        cache_key = f"model_details:{model_id}"
        
        try:
            cached_data = await self.cache_service.get(self.cache_namespace, cache_key)
            if cached_data:
                logger.debug(f"Cache hit for model details: {model_id}")
                return cached_data
            
            logger.debug(f"Cache miss for model details: {model_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting model details from cache: {e}")
            return None
    
    async def set_model_details(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """
        Cache individual model details.
        
        Args:
            model_id: Model identifier
            model_data: Model details
            
        Returns:
            True if cached successfully
        """
        cache_key = f"model_details:{model_id}"
        
        try:
            # Add caching metadata
            cache_data = {
                **model_data,
                'cached_at': datetime.now().isoformat()
            }
            
            tags = self._get_cache_tags(model_data)
            tags.append(f"model:{model_id}")
            
            success = await self.cache_service.set(
                self.cache_namespace,
                cache_key,
                cache_data,
                ttl=self.model_details_ttl,
                tags=tags
            )
            
            if success:
                logger.debug(f"Cached model details: {model_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching model details: {e}")
            return False
    
    async def get_provider_models(self, provider: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get models for a specific provider from cache.
        
        Args:
            provider: Provider name
            
        Returns:
            Cached provider models or None if not found
        """
        cache_key = f"provider_models:{provider}"
        
        try:
            cached_data = await self.cache_service.get(self.cache_namespace, cache_key)
            if cached_data:
                logger.debug(f"Cache hit for provider models: {provider}")
                return cached_data.get('models', [])
            
            logger.debug(f"Cache miss for provider models: {provider}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting provider models from cache: {e}")
            return None
    
    async def set_provider_models(self, provider: str, models: List[Dict[str, Any]]) -> bool:
        """
        Cache models for a specific provider.
        
        Args:
            provider: Provider name
            models: List of models for the provider
            
        Returns:
            True if cached successfully
        """
        cache_key = f"provider_models:{provider}"
        
        try:
            cache_data = {
                'provider': provider,
                'models': models,
                'count': len(models),
                'cached_at': datetime.now().isoformat()
            }
            
            tags = [f"provider:{provider}", 'model_library']
            
            success = await self.cache_service.set(
                self.cache_namespace,
                cache_key,
                cache_data,
                ttl=self.provider_list_ttl,
                tags=tags
            )
            
            if success:
                logger.debug(f"Cached provider models: {provider} ({len(models)} models)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching provider models: {e}")
            return False
    
    async def invalidate_model(self, model_id: str) -> int:
        """
        Invalidate cache entries for a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.invalidate_by_tags([f"model:{model_id}"])
    
    async def invalidate_provider(self, provider: str) -> int:
        """
        Invalidate cache entries for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.invalidate_by_tags([f"provider:{provider}"])
    
    async def invalidate_status(self, status: str) -> int:
        """
        Invalidate cache entries for models with a specific status.
        
        Args:
            status: Model status (local, available, downloading, etc.)
            
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.invalidate_by_tags([f"status:{status}"])
    
    async def invalidate_all_model_cache(self) -> int:
        """
        Invalidate all model library cache entries.
        
        Returns:
            Number of entries invalidated
        """
        return await self.cache_service.clear_namespace(self.cache_namespace)
    
    async def update_model_status(self, model_id: str, new_status: str, model_data: Optional[Dict] = None) -> bool:
        """
        Update a model's status and invalidate related cache entries.
        
        Args:
            model_id: Model identifier
            new_status: New status for the model
            model_data: Updated model data (optional)
            
        Returns:
            True if update was successful
        """
        try:
            # Invalidate model-specific cache
            await self.invalidate_model(model_id)
            
            # Invalidate status-based cache
            await self.invalidate_status(new_status)
            
            # Update model details cache if data provided
            if model_data:
                model_data['status'] = new_status
                await self.set_model_details(model_id, model_data)
            
            logger.info(f"Updated model status cache: {model_id} -> {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating model status cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for model library."""
        stats = self.cache_service.get_stats()
        stats['namespace'] = self.cache_namespace
        stats['ttl_config'] = {
            'quick_list_ttl': self.quick_list_ttl,
            'full_list_ttl': self.full_list_ttl,
            'model_details_ttl': self.model_details_ttl,
            'provider_list_ttl': self.provider_list_ttl
        }
        return stats


# Global model library cache service instance
_model_cache_service: Optional[ModelLibraryCacheService] = None


def get_model_cache_service() -> ModelLibraryCacheService:
    """Get the global model library cache service instance."""
    global _model_cache_service
    
    if _model_cache_service is None:
        _model_cache_service = ModelLibraryCacheService()
    
    return _model_cache_service


def reset_model_cache_service() -> None:
    """Reset the global model library cache service (for testing)."""
    global _model_cache_service
    _model_cache_service = None