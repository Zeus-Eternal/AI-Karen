"""
Extension Cache Manager

Implements caching strategies for extension loading and data to improve performance.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

from ..models import ExtensionManifest, ExtensionRecord
from ..registry import ExtensionRegistry


@dataclass
class CacheEntry:
    """Represents a cached extension entry."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    size_bytes: int
    ttl: Optional[float] = None


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class ExtensionCacheManager:
    """
    Manages caching for extension loading and data to improve performance.
    
    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Size-based limits
    - Cache warming
    - Performance metrics
    """
    
    def __init__(
        self,
        max_size_mb: int = 256,
        max_entries: int = 1000,
        default_ttl: Optional[float] = 3600,  # 1 hour
        cleanup_interval: float = 300  # 5 minutes
    ):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(__name__)
        
    async def start(self) -> None:
        """Start the cache manager and cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info("Extension cache manager started")
    
    async def stop(self) -> None:
        """Stop the cache manager and cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            self.logger.info("Extension cache manager stopped")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats.misses += 1
                return None
            
            # Check TTL expiration
            if entry.ttl and time.time() > entry.created_at + entry.ttl:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                return None
            
            # Update access statistics
            entry.last_accessed = time.time()
            entry.access_count += 1
            self._stats.hits += 1
            
            return entry.value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[float] = None
    ) -> None:
        """Set a value in the cache."""
        async with self._lock:
            # Calculate size estimate
            size_bytes = self._estimate_size(value)
            
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                size_bytes=size_bytes,
                ttl=ttl
            )
            
            # Remove existing entry if present
            if key in self._cache:
                old_entry = self._cache[key]
                self._stats.total_size -= old_entry.size_bytes
                self._stats.entry_count -= 1
            
            # Add new entry
            self._cache[key] = entry
            self._stats.total_size += size_bytes
            self._stats.entry_count += 1
            
            # Enforce size and count limits
            await self._enforce_limits()
    
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        async with self._lock:
            entry = self._cache.pop(key, None)
            if entry:
                self._stats.total_size -= entry.size_bytes
                self._stats.entry_count -= 1
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
    
    async def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        async with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                total_size=self._stats.total_size,
                entry_count=self._stats.entry_count
            )
    
    async def warm_cache(
        self, 
        extension_registry: ExtensionRegistry,
        extension_names: Optional[List[str]] = None
    ) -> None:
        """Warm the cache with frequently used extensions."""
        try:
            if extension_names is None:
                # Get all active extensions
                extensions = await extension_registry.list_extensions(status="active")
                extension_names = [ext.name for ext in extensions]
            
            self.logger.info(f"Warming cache for {len(extension_names)} extensions")
            
            for name in extension_names:
                try:
                    # Cache extension manifest
                    manifest = await extension_registry.get_manifest(name)
                    if manifest:
                        await self.set(f"manifest:{name}", manifest)
                    
                    # Cache extension record
                    record = await extension_registry.get_extension(name)
                    if record:
                        await self.set(f"record:{name}", record)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to warm cache for extension {name}: {e}")
            
            self.logger.info("Cache warming completed")
            
        except Exception as e:
            self.logger.error(f"Cache warming failed: {e}")
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate the size of a value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode('utf-8') if isinstance(value, str) else value)
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, dict):
                return len(json.dumps(value, default=str).encode('utf-8'))
            elif hasattr(value, '__dict__'):
                return len(json.dumps(value.__dict__, default=str).encode('utf-8'))
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate
    
    async def _enforce_limits(self) -> None:
        """Enforce cache size and entry count limits using LRU eviction."""
        # Enforce entry count limit
        while len(self._cache) > self.max_entries:
            await self._evict_lru()
        
        # Enforce size limit
        while self._stats.total_size > self.max_size_bytes:
            await self._evict_lru()
    
    async def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        
        # Remove LRU entry
        entry = self._cache.pop(lru_key)
        self._stats.total_size -= entry.size_bytes
        self._stats.entry_count -= 1
        self._stats.evictions += 1
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries from the cache."""
        async with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry.ttl and current_time > entry.created_at + entry.ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                entry = self._cache.pop(key)
                self._stats.total_size -= entry.size_bytes
                self._stats.entry_count -= 1
                self._stats.evictions += 1
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class ExtensionManifestCache:
    """Specialized cache for extension manifests with file watching."""
    
    def __init__(self, cache_manager: ExtensionCacheManager):
        self.cache_manager = cache_manager
        self._file_hashes: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    async def get_manifest(self, extension_path: Path) -> Optional[ExtensionManifest]:
        """Get cached manifest or load from file if changed."""
        manifest_file = extension_path / "extension.json"
        if not manifest_file.exists():
            return None
        
        # Calculate file hash
        file_hash = self._calculate_file_hash(manifest_file)
        cache_key = f"manifest:{extension_path.name}"
        
        # Check if file has changed
        if self._file_hashes.get(cache_key) == file_hash:
            cached_manifest = await self.cache_manager.get(cache_key)
            if cached_manifest:
                return cached_manifest
        
        # Load manifest from file
        try:
            with open(manifest_file, 'r') as f:
                manifest_data = json.load(f)
            
            manifest = ExtensionManifest(**manifest_data)
            
            # Cache the manifest
            await self.cache_manager.set(cache_key, manifest)
            self._file_hashes[cache_key] = file_hash
            
            return manifest
            
        except Exception as e:
            self.logger.error(f"Failed to load manifest from {manifest_file}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()