"""
Model Availability Cache and Preloading System for Intelligent Fallback

This module provides comprehensive model availability caching and preloading strategies
for Karen AI intelligent fallback system, including:

- Model availability status tracking with intelligent caching
- Usage pattern analysis for predictive preloading
- Network-aware preloading decisions
- Storage management with intelligent eviction policies
- Integration with network monitoring and provider registry
- Comprehensive error handling and recovery mechanisms
"""

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union
from collections import defaultdict, deque
import weakref
import os
from functools import lru_cache

from ..monitoring.network_connectivity import NetworkStatus, get_network_monitor
from .intelligent_provider_registry import get_intelligent_provider_registry
from .capability_aware_selector import get_capability_selector

logger = logging.getLogger(__name__)


class AvailabilityStatus(Enum):
    """Model availability status levels."""
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    CACHED = "cached"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"
    CORRUPTED = "corrupted"
    EXPIRED = "expired"


class PreloadPriority(Enum):
    """Preloading priority levels."""
    CRITICAL = 0  # Essential for offline operation
    HIGH = 1      # Frequently used models
    MEDIUM = 2    # Occasionally used models
    LOW = 3       # Rarely used models
    LAZY = 4      # Only preload when explicitly requested
    
    def __lt__(self, other) -> bool:
        if isinstance(other, PreloadPriority):
            return self.value < other.value
        return NotImplemented
    
    def __gt__(self, other) -> bool:
        if isinstance(other, PreloadPriority):
            return self.value > other.value
        return NotImplemented
    
    def __le__(self, other) -> bool:
        if isinstance(other, PreloadPriority):
            return self.value <= other.value
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        if isinstance(other, PreloadPriority):
            return self.value >= other.value
        return NotImplemented


@dataclass
class ModelMetadata:
    """Metadata for cached models."""
    name: str
    provider: str
    model_type: str  # llm, embedding, vision, etc.
    capabilities: Set[str] = field(default_factory=set)
    size_bytes: int = 0
    version: str = ""
    checksum: str = ""
    download_url: Optional[str] = None
    local_path: Optional[str] = None
    cache_key: str = field(init=False)
    
    def __post_init__(self):
        """Generate cache key from model metadata."""
        key_data = f"{self.provider}:{self.name}:{self.version}"
        self.cache_key = hashlib.sha256(key_data.encode()).hexdigest()[:16]


@dataclass
class UsagePattern:
    """Usage pattern tracking for models."""
    model_key: str
    request_count: int = 0
    last_used: float = 0.0
    usage_frequency: float = 0.0  # Requests per hour
    peak_usage_times: List[float] = field(default_factory=list)
    contexts: Set[str] = field(default_factory=set)
    success_rate: float = 1.0
    average_response_time: float = 0.0
    
    def update_usage(self, context: str = "", success: bool = True, response_time: float = 0.0) -> None:
        """Update usage statistics."""
        current_time = time.time()
        self.request_count += 1
        self.last_used = current_time
        
        if context:
            self.contexts.add(context)
        
        # Update success rate with exponential moving average
        alpha = 0.1
        if success:
            self.success_rate = alpha * 1.0 + (1 - alpha) * self.success_rate
        else:
            self.success_rate = alpha * 0.0 + (1 - alpha) * self.success_rate
        
        # Update average response time
        if response_time > 0:
            if self.average_response_time == 0:
                self.average_response_time = response_time
            else:
                self.average_response_time = alpha * response_time + (1 - alpha) * self.average_response_time
        
        # Update usage frequency (requests per hour over last 24 hours)
        time_window = 24 * 3600  # 24 hours
        # This is a simplified calculation - in production, you'd track actual timestamps
        self.usage_frequency = self.request_count / (time_window / 3600)


@dataclass
class CacheEntry:
    """Cache entry for a model."""
    metadata: ModelMetadata
    status: AvailabilityStatus
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: float = 0.0  # Time-to-live in seconds
    size_bytes: int = 0
    download_progress: float = 0.0  # 0.0 to 1.0
    error_message: Optional[str] = None
    preload_priority: PreloadPriority = PreloadPriority.MEDIUM
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl <= 0:
            return False  # No TTL set
        return time.time() - self.created_at > self.ttl
    
    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class PreloadConfig:
    """Configuration for model preloading."""
    max_cache_size_bytes: int = field(default_factory=lambda: int(os.environ.get('KAREN_MAX_CACHE_SIZE_BYTES', str(10 * 1024 * 1024 * 1024))))
    max_concurrent_downloads: int = field(default_factory=lambda: int(os.environ.get('KAREN_MAX_CONCURRENT_DOWNLOADS', '3')))
    preload_threshold: float = field(default_factory=lambda: float(os.environ.get('KAREN_PRELOAD_THRESHOLD', '0.7')))
    critical_models: Set[str] = field(default_factory=lambda: set(os.environ.get('KAREN_CRITICAL_MODELS', '').split(',')) if os.environ.get('KAREN_CRITICAL_MODELS') else set())
    network_aware_preloading: bool = field(default_factory=lambda: os.environ.get('KAREN_NETWORK_AWARE_PRELOADING', 'true').lower() == 'true')
    offline_preload_only: bool = field(default_factory=lambda: os.environ.get('KAREN_OFFLINE_PRELOAD_ONLY', 'false').lower() == 'true')
    preload_on_startup: bool = field(default_factory=lambda: os.environ.get('KAREN_PRELOAD_ON_STARTUP', 'true').lower() == 'true')
    cleanup_interval: float = field(default_factory=lambda: float(os.environ.get('KAREN_CLEANUP_INTERVAL', '3600.0')))
    usage_history_size: int = field(default_factory=lambda: int(os.environ.get('KAREN_USAGE_HISTORY_SIZE', '1000')))
    preload_retry_attempts: int = field(default_factory=lambda: int(os.environ.get('KAREN_PRELOAD_RETRY_ATTEMPTS', '3')))
    preload_retry_delay: float = field(default_factory=lambda: float(os.environ.get('KAREN_PRELOAD_RETRY_DELAY', '300.0')))
    cache_directory: str = field(default_factory=lambda: os.environ.get('KAREN_CACHE_DIRECTORY', './model_cache'))
    enable_compression: bool = field(default_factory=lambda: os.environ.get('KAREN_ENABLE_COMPRESSION', 'true').lower() == 'true')
    verify_integrity: bool = field(default_factory=lambda: os.environ.get('KAREN_VERIFY_INTEGRITY', 'true').lower() == 'true')
    lru_eviction_threshold: float = field(default_factory=lambda: float(os.environ.get('KAREN_LRU_EVICTION_THRESHOLD', '0.8')))  # Evict when 80% full
    usage_based_priority_weight: float = field(default_factory=lambda: float(os.environ.get('KAREN_USAGE_PRIORITY_WEIGHT', '0.7')))  # Weight for usage in eviction


class ModelAvailabilityCache:
    """
    Comprehensive model availability caching and preloading system.
    
    Features:
    - Intelligent caching with TTL policies
    - Usage pattern analysis for predictive preloading
    - Network-aware preloading decisions
    - Storage management with intelligent eviction
    - Integration with existing monitoring systems
    - Comprehensive error handling and recovery
    """
    
    def __init__(self, config: Optional[PreloadConfig] = None):
        """Initialize model availability cache."""
        self.config = config or PreloadConfig()
        self._cache: Dict[str, CacheEntry] = {}
        self._usage_patterns: Dict[str, UsagePattern] = {}
        self._download_queue: asyncio.Queue = asyncio.Queue()
        self._active_downloads: Set[str] = set()
        self._lock = threading.RLock()
        
        # Network and provider integration
        self._network_monitor = get_network_monitor()
        self._provider_registry = get_intelligent_provider_registry()
        self._capability_selector = get_capability_selector()
        
        # Error recovery state
        self._error_recovery_state = defaultdict(dict)
        self._corruption_detected = set()
        
        # Background tasks
        self._preloading_active = False
        self._cleanup_task: Optional[asyncio.Task] = None
        self._preload_workers: List[asyncio.Task] = []
        
        # Statistics and monitoring
        self._cache_hits = 0
        self._cache_misses = 0
        self._preload_successes = 0
        self._preload_failures = 0
        self._eviction_count = 0
        
        # Ensure cache directory exists
        Path(self.config.cache_directory).mkdir(parents=True, exist_ok=True)
        
        # Load existing cache metadata
        self._load_cache_metadata()
        
        logger.info(f"Model availability cache initialized with {len(self._cache)} entries")
    
    async def start_preloading(self) -> None:
        """Start preloading system."""
        if self._preloading_active:
            logger.warning("Preloading already active")
            return
        
        self._preloading_active = True
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start preload workers
        for i in range(self.config.max_concurrent_downloads):
            worker = asyncio.create_task(self._preload_worker(f"worker-{i}"))
            self._preload_workers.append(worker)
        
        # Preload critical models if configured
        if self.config.preload_on_startup:
            await self._preload_critical_models()
        
        logger.info("Model preloading system started")
    
    async def stop_preloading(self) -> None:
        """Stop preloading system."""
        if not self._preloading_active:
            return
        
        self._preloading_active = False
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        for worker in self._preload_workers:
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass
        
        # Save cache metadata
        self._save_cache_metadata()
        
        logger.info("Model preloading system stopped")
    
    def get_model_status(self, provider: str, model_name: str) -> AvailabilityStatus:
        """
        Get current availability status of a model.
        
        Args:
            provider: Provider name
            model_name: Model name
            
        Returns:
            Current availability status
        """
        cache_key = self._get_cache_key(provider, model_name)
        
        with self._lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                entry.update_access()
                self._cache_hits += 1
                
                # Check if entry is expired
                if entry.is_expired():
                    self._invalidate_entry(cache_key)
                    return AvailabilityStatus.UNAVAILABLE
                
                return entry.status
            else:
                self._cache_misses += 1
                return AvailabilityStatus.UNAVAILABLE
    
    def get_model_metadata(self, provider: str, model_name: str) -> Optional[ModelMetadata]:
        """
        Get metadata for a cached model.
        
        Args:
            provider: Provider name
            model_name: Model name
            
        Returns:
            Model metadata if available, None otherwise
        """
        cache_key = self._get_cache_key(provider, model_name)
        
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key].metadata
            return None
    
    def is_model_cached(self, provider: str, model_name: str) -> bool:
        """Check if a model is cached and available."""
        status = self.get_model_status(provider, model_name)
        return status in [AvailabilityStatus.AVAILABLE, AvailabilityStatus.CACHED]
    
    def record_model_usage(self, provider: str, model_name: str, context: str = "",
                          success: bool = True, response_time: float = 0.0) -> None:
        """
        Record usage of a model for pattern analysis.
        
        Args:
            provider: Provider name
            model_name: Model name
            context: Usage context (e.g., 'chat', 'code', 'embedding')
            success: Whether request was successful
            response_time: Response time in seconds
        """
        model_key = f"{provider}:{model_name}"
        
        with self._lock:
            if model_key not in self._usage_patterns:
                self._usage_patterns[model_key] = UsagePattern(model_key=model_key)
            
            self._usage_patterns[model_key].update_usage(context, success, response_time)
            
            # Trigger preloading if usage pattern indicates high demand
            if self._should_preload_model(model_key):
                asyncio.create_task(self._queue_model_preload(provider, model_name))
            
            # Update capability selector with model availability information
            self._update_capability_selector(provider, model_name)
    
    async def preload_model(self, provider: str, model_name: str, 
                          priority: PreloadPriority = PreloadPriority.MEDIUM) -> bool:
        """
        Manually trigger preloading of a model.
        
        Args:
            provider: Provider name
            model_name: Model name
            priority: Preloading priority
            
        Returns:
            True if preloading was queued successfully
        """
        cache_key = self._get_cache_key(provider, model_name)
        
        with self._lock:
            if cache_key in self._cache and self._cache[cache_key].status == AvailabilityStatus.AVAILABLE:
                logger.debug(f"Model {provider}:{model_name} already available")
                return True
            
            # Update priority if already queued
            if cache_key in self._cache:
                self._cache[cache_key].preload_priority = min(
                    self._cache[cache_key].preload_priority, priority
                )
            else:
                # Create placeholder entry
                metadata = ModelMetadata(
                    name=model_name,
                    provider=provider,
                    model_type="unknown"
                )
                self._cache[cache_key] = CacheEntry(
                    metadata=metadata,
                    status=AvailabilityStatus.UNAVAILABLE,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    preload_priority=priority
                )
        
        return await self._queue_model_preload(provider, model_name)
    
    def get_preloading_candidates(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get list of models that should be preloaded based on usage patterns.
        
        Args:
            limit: Maximum number of candidates to return
            
        Returns:
            List of (model_key, priority_score) tuples
        """
        candidates = []
        network_status = self._network_monitor.get_current_status()
        
        with self._lock:
            for model_key, pattern in self._usage_patterns.items():
                # Skip if already cached
                provider, model_name = model_key.split(":", 1)
                if self.is_model_cached(provider, model_name):
                    continue
                
                # Calculate priority score
                score = self._calculate_preload_score(pattern, network_status)
                
                if score > 0:
                    candidates.append((model_key, score))
        
        # Sort by score (highest first) and limit
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            status_counts = defaultdict(int)
            
            for entry in self._cache.values():
                status_counts[entry.status.value] += 1
            
            return {
                "total_entries": len(self._cache),
                "total_size_bytes": total_size,
                "cache_hit_rate": self._cache_hits / max(self._cache_hits + self._cache_misses, 1),
                "preload_success_rate": self._preload_successes / max(
                    self._preload_successes + self._preload_failures, 1
                ),
                "eviction_count": self._eviction_count,
                "active_downloads": len(self._active_downloads),
                "usage_patterns_tracked": len(self._usage_patterns),
                "status_distribution": dict(status_counts),
                "cache_utilization": total_size / self.config.max_cache_size_bytes,
                "network_status": self._network_monitor.get_current_status().value
            }
    
    def clear_cache(self, provider: Optional[str] = None, model_name: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            provider: Specific provider to clear (None for all)
            model_name: Specific model to clear (None for all)
            
        Returns:
            Number of entries cleared
        """
        cleared_count = 0
        
        with self._lock:
            keys_to_remove = []
            
            for cache_key, entry in self._cache.items():
                should_remove = True
                
                if provider and entry.metadata.provider != provider:
                    should_remove = False
                
                if model_name and entry.metadata.name != model_name:
                    should_remove = False
                
                if should_remove:
                    keys_to_remove.append(cache_key)
            
            for cache_key in keys_to_remove:
                self._remove_cache_entry(cache_key)
                cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count
    
    def _get_cache_key(self, provider: str, model_name: str) -> str:
        """Generate cache key for a model."""
        return f"{provider}:{model_name}"
    
    def _should_preload_model(self, model_key: str) -> bool:
        """Determine if a model should be preloaded based on usage patterns."""
        if model_key not in self._usage_patterns:
            return False
        
        pattern = self._usage_patterns[model_key]
        network_status = self._network_monitor.get_current_status()
        
        # Check usage frequency threshold
        if pattern.usage_frequency < self.config.preload_threshold:
            return False
        
        # Check if already cached
        provider, model_name = model_key.split(":", 1)
        if self.is_model_cached(provider, model_name):
            return False
        
        # Network-aware decisions
        if self.config.network_aware_preloading:
            if network_status == NetworkStatus.OFFLINE:
                # Only preload critical models when offline
                return model_key in self.config.critical_models
            elif network_status == NetworkStatus.DEGRADED:
                # Be more selective when network is degraded
                return pattern.usage_frequency > self.config.preload_threshold * 2
        
        return True
    
    def _calculate_preload_score(self, pattern: UsagePattern, 
                               network_status: NetworkStatus) -> float:
        """Calculate preloading priority score for a model."""
        score = 0.0
        
        # Base score from usage frequency
        score += pattern.usage_frequency * 10.0
        
        # Success rate bonus
        score += pattern.success_rate * 5.0
        
        # Recency bonus
        time_since_last_use = time.time() - pattern.last_used
        recency_bonus = max(0, 1.0 - time_since_last_use / (24 * 3600))  # Decay over 24 hours
        score += recency_bonus * 3.0
        
        # Network status adjustments
        if network_status == NetworkStatus.ONLINE:
            score *= 1.0  # Normal priority
        elif network_status == NetworkStatus.DEGRADED:
            score *= 1.5  # Higher priority when degraded
        elif network_status == NetworkStatus.OFFLINE:
            # Only critical models get high priority when offline
            if pattern.model_key in self.config.critical_models:
                score *= 10.0
            else:
                score = 0.0
        
        # Context diversity bonus (models used in multiple contexts)
        context_diversity = len(pattern.contexts)
        score += context_diversity * 0.5
        
        return score
    
    async def _queue_model_preload(self, provider: str, model_name: str) -> bool:
        """Queue a model for preloading."""
        cache_key = self._get_cache_key(provider, model_name)
        
        if cache_key in self._active_downloads:
            logger.debug(f"Model {cache_key} already being downloaded")
            return False
        
        try:
            await self._download_queue.put((provider, model_name))
            logger.debug(f"Queued model {cache_key} for preloading")
            return True
        except Exception as e:
            logger.error(f"Failed to queue model {cache_key} for preloading: {e}")
            return False
    
    async def _preload_worker(self, worker_id: str) -> None:
        """Worker process for handling model preloading."""
        logger.info(f"Preload worker {worker_id} started")
        
        while self._preloading_active:
            try:
                # Get next model to preload
                try:
                    provider, model_name = await asyncio.wait_for(
                        self._download_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                cache_key = self._get_cache_key(provider, model_name)
                
                # Check if still needed
                if cache_key in self._active_downloads:
                    continue
                
                self._active_downloads.add(cache_key)
                
                try:
                    success = await self._download_model(provider, model_name)
                    
                    with self._lock:
                        if success:
                            self._preload_successes += 1
                            if cache_key in self._cache:
                                self._cache[cache_key].status = AvailabilityStatus.AVAILABLE
                        else:
                            self._preload_failures += 1
                            if cache_key in self._cache:
                                self._cache[cache_key].status = AvailabilityStatus.UNAVAILABLE
                
                finally:
                    self._active_downloads.discard(cache_key)
                    self._download_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in preload worker {worker_id}: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Preload worker {worker_id} stopped")
    
    async def _download_model(self, provider: str, model_name: str) -> bool:
        """
        Download and cache a model with comprehensive error handling and recovery.
        
        Args:
            provider: Provider name
            model_name: Model name
            
        Returns:
            True if download was successful
        """
        cache_key = self._get_cache_key(provider, model_name)
        
        logger.info(f"Starting download of model {cache_key}")
        
        # Initialize error recovery state if not present
        if cache_key not in self._error_recovery_state:
            self._error_recovery_state[cache_key] = {
                'retry_count': 0,
                'last_error': None,
                'backoff_until': 0,
                'corruption_detected': False
            }
        
        recovery_state = self._error_recovery_state[cache_key]
        
        # Check if we're in backoff period
        current_time = time.time()
        if current_time < recovery_state['backoff_until']:
            logger.info(f"Model {cache_key} in backoff period, skipping download")
            return False
        
        # Update status to downloading
        with self._lock:
            if cache_key in self._cache:
                self._cache[cache_key].status = AvailabilityStatus.DOWNLOADING
                self._cache[cache_key].download_progress = 0.0
        
        try:
            # Check for corruption first
            if cache_key in self._corruption_detected:
                logger.warning(f"Model {cache_key} previously detected as corrupted, performing clean download")
                self._cleanup_corrupted_model(cache_key)
                self._corruption_detected.discard(cache_key)
                recovery_state['corruption_detected'] = False
            
            # Get model metadata from provider
            metadata = await self._fetch_model_metadata(provider, model_name)
            if not metadata:
                raise Exception("Failed to fetch model metadata")
            
            # Check available space
            required_space = metadata.size_bytes
            if not self._ensure_space_available(required_space):
                raise Exception("Insufficient cache space")
            
            # Perform download with progress tracking
            local_path = await self._perform_model_download(provider, model_name, metadata)
            
            if not local_path:
                raise Exception("Download failed")
            
            # Verify integrity if configured
            if self.config.verify_integrity and metadata.checksum:
                if not self._verify_model_integrity(local_path, metadata.checksum):
                    # Mark as corrupted
                    self._corruption_detected.add(cache_key)
                    recovery_state['corruption_detected'] = True
                    raise Exception("Model integrity verification failed - file corrupted")
            
            # Update cache entry
            with self._lock:
                if cache_key in self._cache:
                    entry = self._cache[cache_key]
                    entry.metadata = metadata
                    entry.metadata.local_path = local_path
                    entry.status = AvailabilityStatus.CACHED
                    entry.size_bytes = metadata.size_bytes
                    entry.download_progress = 1.0
                    entry.error_message = None
            
            # Reset error recovery state on success
            recovery_state['retry_count'] = 0
            recovery_state['last_error'] = None
            recovery_state['backoff_until'] = 0
            
            logger.info(f"Successfully downloaded model {cache_key}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to download model {cache_key}: {e}"
            logger.error(error_msg)
            
            # Update error recovery state
            recovery_state['retry_count'] += 1
            recovery_state['last_error'] = str(e)
            
            # Implement exponential backoff
            if recovery_state['retry_count'] >= self.config.preload_retry_attempts:
                logger.error(f"Max retry attempts reached for {cache_key}, marking as failed")
                backoff_time = self.config.preload_retry_delay * (2 ** min(recovery_state['retry_count'], 5))
                recovery_state['backoff_until'] = current_time + backoff_time
            else:
                # Shorter backoff for initial retries
                backoff_time = 30 * recovery_state['retry_count']  # 30s, 60s, 90s...
                recovery_state['backoff_until'] = current_time + backoff_time
            
            with self._lock:
                if cache_key in self._cache:
                    self._cache[cache_key].status = AvailabilityStatus.UNAVAILABLE
                    self._cache[cache_key].error_message = str(e)
            
            return False
    
    async def _fetch_model_metadata(self, provider: str, model_name: str) -> Optional[ModelMetadata]:
        """Fetch metadata for a model from provider."""
        try:
            # Get provider registration
            provider_info = self._provider_registry.get_provider_info(provider)
            if not provider_info:
                return None
            
            # Look for model in provider's models
            for model in provider_info.base_registration.models:
                if model.name == model_name:
                    metadata = ModelMetadata(
                        name=model.name,
                        provider=provider,
                        model_type="llm",  # Default to LLM since ModelInfo doesn't have model_type
                        capabilities=set(model.capabilities),
                        size_bytes=getattr(model, 'size_bytes', 0),
                        version=getattr(model, 'version', ''),
                        checksum=getattr(model, 'checksum', ''),
                        download_url=getattr(model, 'download_url', None)
                    )
                    return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {provider}:{model_name}: {e}")
            return None
    
    async def _perform_model_download(self, provider: str, model_name: str, 
                                   metadata: ModelMetadata) -> Optional[str]:
        """
        Perform actual model download.
        
        This is a placeholder implementation - in a real system, this would
        integrate with specific provider's download mechanism.
        """
        # Simulate download progress
        cache_key = self._get_cache_key(provider, model_name)
        local_path = os.path.join(self.config.cache_directory, f"{cache_key}.model")
        
        try:
            # Simulate download with progress updates
            total_steps = 10
            for i in range(total_steps):
                if not self._preloading_active:
                    return None
                
                # Simulate download time
                await asyncio.sleep(0.5)
                
                # Update progress
                progress = (i + 1) / total_steps
                with self._lock:
                    if cache_key in self._cache:
                        self._cache[cache_key].download_progress = progress
                
                logger.debug(f"Download progress for {cache_key}: {progress:.1%}")
            
            # Create a dummy file to simulate successful download
            with open(local_path, 'w') as f:
                f.write(f"Simulated model data for {provider}:{model_name}")
            
            return local_path
            
        except Exception as e:
            logger.error(f"Download failed for {cache_key}: {e}")
            return None
    
    def _verify_model_integrity(self, local_path: str, expected_checksum: str) -> bool:
        """Verify integrity of a downloaded model."""
        try:
            # Calculate SHA256 checksum
            sha256_hash = hashlib.sha256()
            with open(local_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum == expected_checksum
            
        except Exception as e:
            logger.error(f"Failed to verify model integrity: {e}")
            return False
    
    def _ensure_space_available(self, required_bytes: int) -> bool:
        """Ensure enough cache space is available, evicting entries if necessary."""
        current_usage = sum(entry.size_bytes for entry in self._cache.values())
        available_space = self.config.max_cache_size_bytes - current_usage
        
        if available_space >= required_bytes:
            return True
        
        # Need to evict some entries
        return self._evict_entries(required_bytes - available_space)
    
    def _evict_entries(self, bytes_to_free: int) -> bool:
        """Evict cache entries to free up space using LRU with usage-based priorities."""
        if bytes_to_free <= 0:
            return True
        
        # Sort entries by eviction priority (enhanced LRU with usage-based priorities)
        entries_to_evict = []
        
        for cache_key, entry in self._cache.items():
            # Don't evict currently downloading or critical models
            if (entry.status == AvailabilityStatus.DOWNLOADING or
                cache_key in self.config.critical_models):
                continue
            
            # Get usage pattern for this model if available
            usage_score = 0.0
            if cache_key in self._usage_patterns:
                pattern = self._usage_patterns[cache_key]
                # Higher usage frequency and success rate increase priority (reduce eviction chance)
                usage_score = pattern.usage_frequency * pattern.success_rate * 10.0
                # Recent usage gets bonus
                time_since_last_use = time.time() - pattern.last_used
                recency_bonus = max(0, 1.0 - time_since_last_use / (24 * 3600))  # Decay over 24 hours
                usage_score += recency_bonus * 5.0
            
            # Calculate enhanced eviction score (lower score = higher eviction priority)
            # Base LRU score
            score = entry.last_accessed
            
            # Access count bonus (more accesses = higher priority = less likely to evict)
            score += entry.access_count * 3600
            
            # Preload priority bonus
            score += entry.preload_priority.value * 86400
            
            # Usage-based priority (weighted by configuration)
            score += usage_score * self.config.usage_based_priority_weight * 3600
            
            # Context diversity bonus (models used in multiple contexts get priority)
            if cache_key in self._usage_patterns:
                context_diversity = len(self._usage_patterns[cache_key].contexts)
                score += context_diversity * 1800  # 30 minutes per context
            
            # Response time bonus (faster models get priority)
            if cache_key in self._usage_patterns:
                avg_response = self._usage_patterns[cache_key].average_response_time
                if avg_response > 0:
                    # Lower response time = higher priority
                    response_bonus = max(0, (5.0 - avg_response) * 600)  # Up to 50 minutes bonus
                    score += response_bonus
            
            entries_to_evict.append((cache_key, entry, score))
        
        # Sort by eviction score (ascending - lowest score gets evicted first)
        entries_to_evict.sort(key=lambda x: x[2])
        
        # Evict entries until enough space is freed
        freed_bytes = 0
        evicted_count = 0
        for cache_key, entry, score in entries_to_evict:
            # Check if we've reached the LRU eviction threshold
            current_usage = sum(e.size_bytes for e in self._cache.values())
            if current_usage <= self.config.max_cache_size_bytes * self.config.lru_eviction_threshold:
                break
            
            self._remove_cache_entry(cache_key)
            freed_bytes += entry.size_bytes
            self._eviction_count += 1
            evicted_count += 1
            
            logger.debug(f"Evicted {cache_key} (score: {score:.0f}, size: {entry.size_bytes} bytes)")
            
            if freed_bytes >= bytes_to_free:
                break
        
        success = freed_bytes >= bytes_to_free
        if success:
            logger.info(f"Evicted {evicted_count} entries, freed {freed_bytes} bytes")
        else:
            logger.warning(f"Could not free enough space. Needed {bytes_to_free}, freed {freed_bytes}")
        
        return success
    
    def _cleanup_corrupted_model(self, cache_key: str) -> None:
        """Clean up a corrupted model and its associated files."""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        logger.warning(f"Cleaning up corrupted model: {cache_key}")
        
        # Remove local file if it exists
        if entry.metadata.local_path and os.path.exists(entry.metadata.local_path):
            try:
                os.remove(entry.metadata.local_path)
                logger.info(f"Removed corrupted file: {entry.metadata.local_path}")
            except Exception as e:
                logger.error(f"Failed to remove corrupted file {entry.metadata.local_path}: {e}")
        
        # Remove any partial downloads
        cache_dir = self.config.cache_directory
        for suffix in ['.part', '.tmp', '.download']:
            partial_path = os.path.join(cache_dir, f"{cache_key}{suffix}")
            if os.path.exists(partial_path):
                try:
                    os.remove(partial_path)
                    logger.info(f"Removed partial download: {partial_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove partial file {partial_path}: {e}")
        
        # Update status
        entry.status = AvailabilityStatus.UNAVAILABLE
        entry.error_message = "Model was corrupted and cleaned up"
        entry.download_progress = 0.0

    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove a cache entry and its associated files."""
        if cache_key not in self._cache:
            return
        
        entry = self._cache[cache_key]
        
        # Remove local file if it exists
        if entry.metadata.local_path and os.path.exists(entry.metadata.local_path):
            try:
                os.remove(entry.metadata.local_path)
                logger.debug(f"Removed local file: {entry.metadata.local_path}")
            except Exception as e:
                logger.warning(f"Failed to remove local file {entry.metadata.local_path}: {e}")
        
        # Remove from error tracking
        if cache_key in self._error_recovery_state:
            del self._error_recovery_state[cache_key]
        if cache_key in self._corruption_detected:
            self._corruption_detected.discard(cache_key)
        
        # Remove from cache
        del self._cache[cache_key]
    
    def _invalidate_entry(self, cache_key: str) -> None:
        """Invalidate a cache entry."""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            entry.status = AvailabilityStatus.EXPIRED
            entry.error_message = "Cache entry expired"
    
    async def _preload_critical_models(self) -> None:
        """Preload models marked as critical for offline operation."""
        logger.info("Starting preload of critical models")
        
        for model_key in self.config.critical_models:
            try:
                provider, model_name = model_key.split(":", 1)
                await self.preload_model(provider, model_name, PreloadPriority.CRITICAL)
            except Exception as e:
                logger.error(f"Failed to preload critical model {model_key}: {e}")
        
        logger.info("Critical models preload initiated")
    
    def _update_capability_selector(self, provider: str, model_name: str) -> None:
        """Update capability selector with model availability information."""
        try:
            # Get current model status
            status = self.get_model_status(provider, model_name)
            
            # Get model metadata
            metadata = self.get_model_metadata(provider, model_name)
            if not metadata:
                return
            
            # Create availability update for capability selector
            availability_update = {
                'provider': provider,
                'model': model_name,
                'status': status.value,
                'capabilities': list(metadata.capabilities),
                'model_type': metadata.model_type,
                'size_bytes': metadata.size_bytes,
                'local_path': metadata.local_path,
                'timestamp': time.time()
            }
            
            # Update capability selector if it has the method
            if hasattr(self._capability_selector, 'update_model_availability'):
                self._capability_selector.update_model_availability(availability_update)
                logger.debug(f"Updated capability selector with availability for {provider}:{model_name}")
            else:
                # Store availability update in selector's internal state if possible
                try:
                    if hasattr(self._capability_selector, '_model_availability_updates'):
                        self._capability_selector._model_availability_updates.append(availability_update)
                        logger.debug(f"Stored availability update for {provider}:{model_name}")
                    else:
                        logger.debug(f"Capability selector does not support availability updates")
                except Exception as e:
                    logger.warning(f"Failed to store availability update: {e}")
                
        except Exception as e:
            logger.error(f"Failed to update capability selector: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop for cache maintenance."""
        logger.info("Cache cleanup loop started")
        
        while self._preloading_active:
            try:
                await self._perform_cleanup()
                await asyncio.sleep(self.config.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
        
        logger.info("Cache cleanup loop stopped")
    
    async def _perform_cleanup(self) -> None:
        """Perform cache cleanup operations."""
        current_time = time.time()
        entries_to_remove = []
        
        with self._lock:
            for cache_key, entry in self._cache.items():
                # Remove expired entries
                if entry.is_expired():
                    entries_to_remove.append(cache_key)
                    continue
                
                # Remove corrupted entries
                if entry.status == AvailabilityStatus.CORRUPTED:
                    entries_to_remove.append(cache_key)
                    continue
                
                # Remove old unused entries (older than 7 days and not accessed in 3 days)
                if (current_time - entry.created_at > 7 * 24 * 3600 and
                    current_time - entry.last_accessed > 3 * 24 * 3600):
                    if cache_key not in self.config.critical_models:
                        entries_to_remove.append(cache_key)
        
        # Remove marked entries
        for cache_key in entries_to_remove:
            self._remove_cache_entry(cache_key)
        
        if entries_to_remove:
            logger.info(f"Cleaned up {len(entries_to_remove)} cache entries")
        
        # Save cache metadata
        self._save_cache_metadata()
    
    def _load_cache_metadata(self) -> None:
        """Load cache metadata from disk."""
        metadata_file = os.path.join(self.config.cache_directory, "cache_metadata.json")
        
        try:
            if not os.path.exists(metadata_file):
                return
            
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            current_time = time.time()
            
            for entry_data in data.get('entries', []):
                try:
                    # Recreate metadata
                    metadata_dict = entry_data['metadata']
                    metadata = ModelMetadata(
                        name=metadata_dict['name'],
                        provider=metadata_dict['provider'],
                        model_type=metadata_dict['model_type'],
                        capabilities=set(metadata_dict['capabilities']),
                        size_bytes=metadata_dict['size_bytes'],
                        version=metadata_dict['version'],
                        checksum=metadata_dict['checksum'],
                        download_url=metadata_dict.get('download_url'),
                        local_path=metadata_dict.get('local_path')
                    )
                    
                    # Recreate cache entry
                    entry = CacheEntry(
                        metadata=metadata,
                        status=AvailabilityStatus(entry_data['status']),
                        created_at=entry_data['created_at'],
                        last_accessed=entry_data['last_accessed'],
                        access_count=entry_data['access_count'],
                        ttl=entry_data['ttl'],
                        size_bytes=entry_data['size_bytes'],
                        preload_priority=PreloadPriority(entry_data.get('preload_priority', 2))
                    )
                    
                    # Verify local file exists
                    if metadata.local_path and not os.path.exists(metadata.local_path):
                        entry.status = AvailabilityStatus.UNAVAILABLE
                    elif entry.status == AvailabilityStatus.DOWNLOADING:
                        # Reset downloading status on restart
                        entry.status = AvailabilityStatus.UNAVAILABLE
                    
                    self._cache[metadata.cache_key] = entry
                    
                except Exception as e:
                    logger.warning(f"Failed to load cache entry: {e}")
            
            logger.info(f"Loaded {len(self._cache)} cache entries from disk")
            
        except Exception as e:
            logger.error(f"Failed to load cache metadata: {e}")
    
    def _save_cache_metadata(self) -> None:
        """Save cache metadata to disk."""
        metadata_file = os.path.join(self.config.cache_directory, "cache_metadata.json")
        
        try:
            entries_data = []
            
            for entry in self._cache.values():
                entry_data = {
                    'metadata': {
                        'name': entry.metadata.name,
                        'provider': entry.metadata.provider,
                        'model_type': entry.metadata.model_type,
                        'capabilities': list(entry.metadata.capabilities),
                        'size_bytes': entry.metadata.size_bytes,
                        'version': entry.metadata.version,
                        'checksum': entry.metadata.checksum,
                        'download_url': entry.metadata.download_url,
                        'local_path': entry.metadata.local_path
                    },
                    'status': entry.status.value,
                    'created_at': entry.created_at,
                    'last_accessed': entry.last_accessed,
                    'access_count': entry.access_count,
                    'ttl': entry.ttl,
                    'size_bytes': entry.size_bytes,
                    'preload_priority': entry.preload_priority.value
                }
                entries_data.append(entry_data)
            
            data = {
                'version': '1.0',
                'created_at': time.time(),
                'entries': entries_data
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")


# Global instance
_model_availability_cache: Optional[ModelAvailabilityCache] = None
_cache_lock = threading.RLock()


def get_model_availability_cache(config: Optional[PreloadConfig] = None) -> ModelAvailabilityCache:
    """Get or create global model availability cache instance."""
    global _model_availability_cache
    if _model_availability_cache is None:
        with _cache_lock:
            if _model_availability_cache is None:
                _model_availability_cache = ModelAvailabilityCache(config)
    return _model_availability_cache


async def initialize_model_availability_cache(config: Optional[PreloadConfig] = None) -> ModelAvailabilityCache:
    """Initialize model availability cache system."""
    cache = get_model_availability_cache(config)
    await cache.start_preloading()
    logger.info("Model availability cache system initialized")
    return cache


# Export main classes for easy import
__all__ = [
    "AvailabilityStatus",
    "PreloadPriority",
    "ModelMetadata",
    "UsagePattern",
    "CacheEntry",
    "PreloadConfig",
    "ModelAvailabilityCache",
    "get_model_availability_cache",
    "initialize_model_availability_cache",
]