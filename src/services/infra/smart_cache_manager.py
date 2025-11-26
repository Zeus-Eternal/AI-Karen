"""
Smart Cache Manager

This service provides intelligent caching with automatic policies.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import json

from .integrated_cache_system import IntegratedCacheSystem, CacheType


class CachePolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    max_size: int = 1000
    default_ttl: int = 3600
    eviction_policy: CachePolicy = CachePolicy.LRU
    compression_enabled: bool = False
    serialization_format: str = "json"


class SmartCacheManager:
    """
    Smart Cache Manager provides intelligent caching with automatic policies.
    
    This service extends the basic cache system with intelligent
    eviction policies, compression, and serialization.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Smart Cache Manager.
        
        Args:
            config: Configuration for the cache manager
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache configuration
        self.cache_config = CacheConfig(**config.get("cache", {}))
        
        # Integrated cache system
        self.cache_system = IntegratedCacheSystem(config.get("backends", {}))
        
        # Access tracking for eviction policies
        self.access_times: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = {}
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background task to enforce cache policies."""
        while True:
            try:
                await self._enforce_policies()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _enforce_policies(self):
        """Enforce cache eviction policies."""
        # Check size limits
        await self._enforce_size_limit()
        
        # Check TTL expiration
        await self._cleanup_expired()
    
    async def _enforce_size_limit(self):
        """Enforce maximum cache size."""
        stats = await self.cache_system.get_stats()
        current_size = stats.get("entry_count", 0)
        
        if current_size <= self.cache_config.max_size:
            return
        
        # Calculate how many entries to remove
        to_remove = current_size - self.cache_config.max_size
        
        # Get keys to evict based on policy
        keys_to_evict = await self._get_keys_to_evict(to_remove)
        
        # Evict keys
        for key in keys_to_evict:
            await self.cache_system.delete(key)
            self._remove_tracking(key)
    
    async def _get_keys_to_evict(self, count: int) -> List[str]:
        """Get keys to evict based on eviction policy."""
        if self.cache_config.eviction_policy == CachePolicy.LRU:
            return self._get_lru_keys(count)
        elif self.cache_config.eviction_policy == CachePolicy.LFU:
            return self._get_lfu_keys(count)
        elif self.cache_config.eviction_policy == CachePolicy.FIFO:
            return self._get_fifo_keys(count)
        elif self.cache_config.eviction_policy == CachePolicy.TTL:
            return await self._get_ttl_keys(count)
        else:
            return self._get_lru_keys(count)  # Default to LRU
    
    def _get_lru_keys(self, count: int) -> List[str]:
        """Get least recently used keys."""
        # Sort by access time
        sorted_keys = sorted(
            self.access_times.items(),
            key=lambda x: x[1]
        )
        return [key for key, _ in sorted_keys[:count]]
    
    def _get_lfu_keys(self, count: int) -> List[str]:
        """Get least frequently used keys."""
        # Sort by access count
        sorted_keys = sorted(
            self.access_counts.items(),
            key=lambda x: x[1]
        )
        return [key for key, _ in sorted_keys[:count]]
    
    def _get_fifo_keys(self, count: int) -> List[str]:
        """Get first-in-first-out keys."""
        # Implementation would track insertion order
        # For now, return random keys
        import random
        keys = list(self.access_times.keys())
        return random.sample(keys, min(count, len(keys)))
    
    async def _get_ttl_keys(self, count: int) -> List[str]:
        """Get keys with shortest TTL."""
        # Implementation would check actual TTL
        # For now, return random keys
        import random
        keys = list(self.access_times.keys())
        return random.sample(keys, min(count, len(keys)))
    
    async def _cleanup_expired(self):
        """Clean up expired entries."""
        # This is handled by the integrated cache system
        pass
    
    def _update_tracking(self, key: str):
        """Update access tracking for a key."""
        self.access_times[key] = time.time()
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
    
    def _remove_tracking(self, key: str):
        """Remove access tracking for a key."""
        self.access_times.pop(key, None)
        self.access_counts.pop(key, None)
    
    async def get(
        self,
        key: str,
        backend_type: Optional[CacheType] = None
    ) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            backend_type: Optional cache backend type
            
        Returns:
            The cached value if found, None otherwise
        """
        value = await self.cache_system.get(key, backend_type)
        if value is not None:
            self._update_tracking(key)
        
        return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        backend_type: Optional[CacheType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            backend_type: Optional cache backend type
            metadata: Optional metadata for the entry
            
        Returns:
            True if set successfully, False otherwise
        """
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.cache_config.default_ttl
        
        # Apply compression if enabled
        if self.cache_config.compression_enabled:
            value = self._compress_value(value)
        
        # Serialize if needed
        if self.cache_config.serialization_format == "json":
            value = self._serialize_json(value)
        
        success = await self.cache_system.set(
            key, value, ttl, backend_type, metadata
        )
        
        if success:
            self._update_tracking(key)
        
        return success
    
    def _compress_value(self, value: Any) -> Any:
        """Compress a value if possible."""
        # Implementation would compress value
        return value
    
    def _serialize_json(self, value: Any) -> str:
        """Serialize a value to JSON."""
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            self.logger.warning(f"Failed to serialize value to JSON: {type(value)}")
            return str(value)
    
    async def delete(
        self,
        key: str,
        backend_type: Optional[CacheType] = None
    ) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            backend_type: Optional cache backend type
            
        Returns:
            True if deleted successfully, False otherwise
        """
        success = await self.cache_system.delete(key, backend_type)
        if success:
            self._remove_tracking(key)
        
        return success
    
    async def exists(
        self,
        key: str,
        backend_type: Optional[CacheType] = None
    ) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key
            backend_type: Optional cache backend type
            
        Returns:
            True if the key exists, False otherwise
        """
        return await self.cache_system.exists(key, backend_type)
    
    async def clear(self, backend_type: Optional[CacheType] = None):
        """
        Clear all values from a cache backend.
        
        Args:
            backend_type: Optional cache backend type
        """
        await self.cache_system.clear(backend_type)
        
        # Clear tracking
        if backend_type is None:
            self.access_times.clear()
            self.access_counts.clear()
    
    async def get_stats(self, backend_type: Optional[CacheType] = None) -> Dict[str, Any]:
        """
        Get statistics for a cache backend.
        
        Args:
            backend_type: Optional cache backend type
            
        Returns:
            Cache statistics
        """
        base_stats = await self.cache_system.get_stats(backend_type)
        
        # Add policy-specific stats
        if backend_type is None:
            base_stats["policy"] = {
                "eviction_policy": self.cache_config.eviction_policy.value,
                "max_size": self.cache_config.max_size,
                "default_ttl": self.cache_config.default_ttl,
                "compression_enabled": self.cache_config.compression_enabled,
                "tracked_keys": len(self.access_times)
            }
        
        return base_stats
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all cache backends.
        
        Returns:
            Dictionary of all cache statistics
        """
        return await self.cache_system.get_all_stats()
    
    async def close(self):
        """Close the cache manager."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.cache_system.close()
