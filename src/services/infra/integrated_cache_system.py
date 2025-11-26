"""
Integrated Cache System

This service provides a unified interface to different cache types.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import json

from .internal.cache_backends import CacheBackend, RedisBackend, MemoryBackend, DiskBackend


class CacheType(Enum):
    """Types of cache backends."""
    REDIS = "redis"
    MEMORY = "memory"
    DISK = "disk"


@dataclass
class CacheEntry:
    """A cache entry with metadata."""
    key: str
    value: Any
    ttl: Optional[int] = None
    created_at: float = 0
    access_count: int = 0
    metadata: Dict[str, Any] = None


class IntegratedCacheSystem:
    """
    Integrated Cache System provides a unified interface to different cache types.
    
    This service abstracts Redis, in-memory, and disk caches
    with a consistent API and automatic backend selection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Integrated Cache System.
        
        Args:
            config: Configuration for the cache system
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache backends
        self.backends: Dict[CacheType, CacheBackend] = {}
        
        # Default backend
        self.default_backend = CacheType(config.get("default_backend", "memory"))
        
        # Initialize backends
        self._initialize_backends()
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def _initialize_backends(self):
        """Initialize cache backends."""
        # Redis backend
        if "redis" in self.config:
            self.backends[CacheType.REDIS] = RedisBackend(
                self.config["redis"]
            )
        
        # Memory backend
        if "memory" in self.config:
            self.backends[CacheType.MEMORY] = MemoryBackend(
                self.config["memory"]
            )
        
        # Disk backend
        if "disk" in self.config:
            self.backends[CacheType.DISK] = DiskBackend(
                self.config["disk"]
            )
        
        self.logger.info(f"Initialized cache backends: {list(self.backends.keys())}")
    
    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_expired(self):
        """Clean up expired entries in all backends."""
        for backend_type, backend in self.backends.items():
            try:
                await backend.cleanup_expired()
            except Exception as e:
                self.logger.error(f"Error cleaning up {backend_type.value}: {e}")
    
    def _get_backend(self, backend_type: Optional[CacheType] = None) -> CacheBackend:
        """Get a cache backend."""
        if backend_type is None:
            backend_type = self.default_backend
        
        backend = self.backends.get(backend_type)
        if not backend:
            raise ValueError(f"Cache backend not available: {backend_type}")
        
        return backend
    
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
        backend = self._get_backend(backend_type)
        entry = await backend.get(key)
        
        if entry:
            # Update access count
            entry.access_count += 1
            return entry.value
        
        return None
    
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
        backend = self._get_backend(backend_type)
        
        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl,
            created_at=time.time(),
            metadata=metadata
        )
        
        return await backend.set(entry)
    
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
        backend = self._get_backend(backend_type)
        return await backend.delete(key)
    
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
        backend = self._get_backend(backend_type)
        return await backend.exists(key)
    
    async def clear(self, backend_type: Optional[CacheType] = None):
        """
        Clear all values from a cache backend.
        
        Args:
            backend_type: Optional cache backend type
        """
        backend = self._get_backend(backend_type)
        await backend.clear()
        self.logger.info(f"Cleared cache: {backend_type.value}")
    
    async def get_stats(self, backend_type: Optional[CacheType] = None) -> Dict[str, Any]:
        """
        Get statistics for a cache backend.
        
        Args:
            backend_type: Optional cache backend type
            
        Returns:
            Cache statistics
        """
        backend = self._get_backend(backend_type)
        return await backend.get_stats()
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all cache backends.
        
        Returns:
            Dictionary of all cache statistics
        """
        stats = {}
        for backend_type, backend in self.backends.items():
            stats[backend_type.value] = await backend.get_stats()
        
        return stats
    
    async def migrate(
        self,
        key: str,
        from_backend: CacheType,
        to_backend: CacheType
    ) -> bool:
        """
        Migrate a cache entry from one backend to another.
        
        Args:
            key: The cache key
            from_backend: Source backend type
            to_backend: Destination backend type
            
        Returns:
            True if migrated successfully, False otherwise
        """
        # Get value from source
        value = await self.get(key, from_backend)
        if value is None:
            return False
        
        # Get entry metadata
        from_backend_obj = self._get_backend(from_backend)
        entry = await from_backend_obj.get(key)
        
        # Set in destination
        return await self.set(
            key,
            value,
            ttl=entry.ttl if entry else None,
            backend_type=to_backend,
            metadata=entry.metadata if entry else None
        )
    
    async def close(self):
        """Close all cache backends."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        for backend_type, backend in self.backends.items():
            await backend.close()
            self.logger.info(f"Closed cache backend: {backend_type.value}")
