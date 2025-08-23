"""
Enhanced Caching Utilities for Performance Optimization

This module provides caching utilities for token validation, error responses,
provider health status, and request deduplication to improve system performance.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set, Tuple, Callable, Awaitable
from dataclasses import dataclass, asdict
from threading import Lock
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Access the cached data and update access metadata"""
        self.access_count += 1
        self.last_access = time.time()
        return self.data


class MemoryCache:
    """Thread-safe in-memory cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired_removals": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["expired_removals"] += 1
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            # Use default TTL if not specified
            cache_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                ttl=cache_ttl
            )
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "expired_removals": 0
            }
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_access or self._cache[k].timestamp
        )
        
        del self._cache[lru_key]
        self._stats["evictions"] += 1
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            self._stats["expired_removals"] += len(expired_keys)
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                **self._stats
            }


class TokenValidationCache:
    """Specialized cache for token validation results"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache = MemoryCache(max_size=5000, default_ttl=ttl)
        self.ttl = ttl
    
    def _generate_token_key(self, token: str) -> str:
        """Generate cache key for token (using hash for security)"""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def get_validation_result(self, token: str) -> Optional[Dict[str, Any]]:
        """Get cached token validation result"""
        key = self._generate_token_key(token)
        return self.cache.get(key)
    
    def cache_validation_result(
        self, 
        token: str, 
        validation_result: Dict[str, Any],
        custom_ttl: Optional[int] = None
    ) -> None:
        """Cache token validation result"""
        key = self._generate_token_key(token)
        
        # Don't cache failed validations for as long
        ttl = custom_ttl or (60 if validation_result.get("valid") else 30)
        
        self.cache.set(key, validation_result, ttl)
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate cached token validation"""
        key = self._generate_token_key(token)
        return self.cache.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get token cache statistics"""
        return self.cache.get_stats()


class RequestDeduplicator:
    """Deduplicates simultaneous identical requests"""
    
    def __init__(self, ttl: int = 30):  # 30 seconds default
        self.ttl = ttl
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "deduplicated_requests": 0,
            "unique_requests": 0
        }
    
    def _generate_request_key(self, *args, **kwargs) -> str:
        """Generate unique key for request parameters"""
        key_data = json.dumps({
            "args": args,
            "kwargs": sorted(kwargs.items())
        }, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def deduplicate(
        self, 
        func: Callable[..., Awaitable[Any]], 
        *args, 
        **kwargs
    ) -> Any:
        """
        Deduplicate identical function calls
        
        If the same function is called with identical parameters while
        a previous call is still pending, return the result of the first call.
        """
        request_key = self._generate_request_key(*args, **kwargs)
        
        async with self._lock:
            # Check if request is already pending
            if request_key in self._pending_requests:
                logger.debug(f"Deduplicating request: {request_key}")
                self._stats["deduplicated_requests"] += 1
                # Wait for the existing request to complete
                return await self._pending_requests[request_key]
            
            # Create new future for this request
            future = asyncio.create_task(func(*args, **kwargs))
            self._pending_requests[request_key] = future
            self._stats["unique_requests"] += 1
        
        try:
            # Execute the function
            result = await future
            return result
        finally:
            # Clean up the pending request
            async with self._lock:
                self._pending_requests.pop(request_key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        total_requests = self._stats["deduplicated_requests"] + self._stats["unique_requests"]
        dedup_rate = (
            self._stats["deduplicated_requests"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            "pending_requests": len(self._pending_requests),
            "deduplication_rate": dedup_rate,
            **self._stats
        }


class IntelligentResponseCache:
    """Enhanced cache for intelligent error responses"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache = MemoryCache(max_size=2000, default_ttl=ttl)
        self.ttl = ttl
    
    def _generate_response_key(
        self, 
        error_message: str, 
        error_type: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> str:
        """Generate cache key for error response"""
        key_data = f"{error_message}:{error_type}:{provider_name}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_response(
        self, 
        error_message: str, 
        error_type: Optional[str] = None,
        provider_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached intelligent response"""
        key = self._generate_response_key(error_message, error_type, provider_name)
        return self.cache.get(key)
    
    def cache_response(
        self, 
        error_message: str, 
        response: Dict[str, Any],
        error_type: Optional[str] = None,
        provider_name: Optional[str] = None,
        custom_ttl: Optional[int] = None
    ) -> None:
        """Cache intelligent response"""
        key = self._generate_response_key(error_message, error_type, provider_name)
        
        # Cache longer for common error types
        ttl = custom_ttl or self.ttl
        if response.get("category") in ["api_key_missing", "api_key_invalid", "authentication"]:
            ttl = 600  # 10 minutes for stable errors
        
        self.cache.set(key, response, ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get response cache statistics"""
        return self.cache.get_stats()


class ProviderHealthCache:
    """Enhanced cache for provider health status"""
    
    def __init__(self, ttl: int = 180):  # 3 minutes default
        self.cache = MemoryCache(max_size=100, default_ttl=ttl)
        self.ttl = ttl
    
    def get_provider_health(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get cached provider health status"""
        return self.cache.get(provider_name.lower())
    
    def cache_provider_health(
        self, 
        provider_name: str, 
        health_data: Dict[str, Any],
        custom_ttl: Optional[int] = None
    ) -> None:
        """Cache provider health status"""
        ttl = custom_ttl or self.ttl
        
        # Cache unhealthy providers for shorter time
        if health_data.get("status") == "unhealthy":
            ttl = 60  # 1 minute for unhealthy providers
        
        self.cache.set(provider_name.lower(), health_data, ttl)
    
    def invalidate_provider(self, provider_name: str) -> bool:
        """Invalidate cached provider health"""
        return self.cache.delete(provider_name.lower())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get provider health cache statistics"""
        return self.cache.get_stats()


# Global cache instances
_token_cache: Optional[TokenValidationCache] = None
_response_cache: Optional[IntelligentResponseCache] = None
_provider_cache: Optional[ProviderHealthCache] = None
_request_deduplicator: Optional[RequestDeduplicator] = None


def get_token_cache() -> TokenValidationCache:
    """Get global token validation cache instance"""
    global _token_cache
    if _token_cache is None:
        _token_cache = TokenValidationCache()
    return _token_cache


def get_response_cache() -> IntelligentResponseCache:
    """Get global intelligent response cache instance"""
    global _response_cache
    if _response_cache is None:
        _response_cache = IntelligentResponseCache()
    return _response_cache


def get_provider_cache() -> ProviderHealthCache:
    """Get global provider health cache instance"""
    global _provider_cache
    if _provider_cache is None:
        _provider_cache = ProviderHealthCache()
    return _provider_cache


def get_request_deduplicator() -> RequestDeduplicator:
    """Get global request deduplicator instance"""
    global _request_deduplicator
    if _request_deduplicator is None:
        _request_deduplicator = RequestDeduplicator()
    return _request_deduplicator


async def cleanup_all_caches() -> Dict[str, int]:
    """Cleanup expired entries from all caches"""
    results = {}
    
    if _token_cache:
        results["token_cache"] = _token_cache.cache.cleanup_expired()
    
    if _response_cache:
        results["response_cache"] = _response_cache.cache.cleanup_expired()
    
    if _provider_cache:
        results["provider_cache"] = _provider_cache.cache.cleanup_expired()
    
    return results


def get_all_cache_stats() -> Dict[str, Dict[str, Any]]:
    """Get statistics for all caches"""
    stats = {}
    
    if _token_cache:
        stats["token_cache"] = _token_cache.get_stats()
    
    if _response_cache:
        stats["response_cache"] = _response_cache.get_stats()
    
    if _provider_cache:
        stats["provider_cache"] = _provider_cache.get_stats()
    
    if _request_deduplicator:
        stats["request_deduplicator"] = _request_deduplicator.get_stats()
    
    return stats