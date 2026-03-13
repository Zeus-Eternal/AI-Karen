"""
Automatic Model Downloading and Caching System for Karen AI

This module provides comprehensive automatic model downloading and caching for offline use,
including intelligent download scheduling, robust caching mechanisms, and offline-first operation.

Features:
- Automatic model downloading with priority-based queuing
- Intelligent download scheduling based on network conditions
- Robust caching with compression and deduplication
- Offline-first operation with seamless fallback
- Comprehensive error handling and recovery
- Integration with existing monitoring systems
"""

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
import zlib
import gzip
import shutil
import tempfile
import weakref
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union, AsyncIterator
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import aiofiles
import os.path

from ..monitoring.network_connectivity import NetworkStatus, get_network_monitor
from .model_availability_cache import get_model_availability_cache, AvailabilityStatus

logger = logging.getLogger(__name__)


class DownloadStatus(Enum):
    """Download task status levels."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    VERIFYING = "verifying"


class DownloadPriority(Enum):
    """Download priority levels."""
    CRITICAL = 0    # Essential for offline operation
    HIGH = 1        # Frequently used models
    NORMAL = 2      # Regular downloads
    LOW = 3         # Less important models
    BACKGROUND = 4  # Background downloads only
    
    def __lt__(self, other) -> bool:
        if isinstance(other, DownloadPriority):
            return self.value < other.value
        return NotImplemented
    
    def __gt__(self, other) -> bool:
        if isinstance(other, DownloadPriority):
            return self.value > other.value
        return NotImplemented


@dataclass
class ModelMetadata:
    """Metadata for model downloads and caching."""
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
    compression_type: str = "gzip"  # gzip, zlib, none
    encryption_enabled: bool = False
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Generate cache key from model metadata."""
        key_data = f"{self.provider}:{self.name}:{self.version}"
        self.cache_key = hashlib.sha256(key_data.encode()).hexdigest()[:16]


@dataclass
class DownloadTask:
    """Individual download operation task."""
    metadata: ModelMetadata
    priority: DownloadPriority
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    bytes_downloaded: int = 0
    total_bytes: int = 0
    download_speed: float = 0.0  # bytes per second
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    last_activity: float = field(default_factory=time.time)
    timeout: float = 300.0  # 5 minutes default timeout
    resume_supported: bool = True
    chunk_size: int = 8192  # 8KB chunks
    temp_file_path: Optional[str] = None
    final_file_path: Optional[str] = None
    
    def __lt__(self, other) -> bool:
        """Compare tasks for priority queue (higher priority first)."""
        if not isinstance(other, DownloadTask):
            return NotImplemented
        # Lower priority value = higher priority
        if self.priority != other.priority:
            return self.priority < other.priority
        # If same priority, older tasks first
        return self.created_at < other.created_at
    
    def is_expired(self) -> bool:
        """Check if download task has expired."""
        return time.time() - self.last_activity > self.timeout
    
    def should_retry(self) -> bool:
        """Check if task should be retried."""
        return self.retry_count < self.max_retries and self.status == DownloadStatus.FAILED
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time to completion in seconds."""
        if self.download_speed <= 0 or self.total_bytes <= 0:
            return None
        remaining_bytes = self.total_bytes - self.bytes_downloaded
        return remaining_bytes / self.download_speed


@dataclass
class DownloadConfig:
    """Configuration for model download manager."""
    max_concurrent_downloads: int = field(default_factory=lambda: int(os.environ.get('KAREN_MAX_CONCURRENT_DOWNLOADS', '3')))
    max_download_speed: int = field(default_factory=lambda: int(os.environ.get('KAREN_MAX_DOWNLOAD_SPEED', '0')))  # 0 = unlimited
    retry_delay_base: float = field(default_factory=lambda: float(os.environ.get('KAREN_RETRY_DELAY_BASE', '30.0')))
    retry_delay_max: float = field(default_factory=lambda: float(os.environ.get('KAREN_RETRY_DELAY_MAX', '300.0')))
    chunk_size: int = field(default_factory=lambda: int(os.environ.get('KAREN_DOWNLOAD_CHUNK_SIZE', '8192')))
    timeout: float = field(default_factory=lambda: float(os.environ.get('KAREN_DOWNLOAD_TIMEOUT', '300.0')))
    verify_downloads: bool = field(default_factory=lambda: os.environ.get('KAREN_VERIFY_DOWNLOADS', 'true').lower() == 'true')
    enable_compression: bool = field(default_factory=lambda: os.environ.get('KAREN_ENABLE_COMPRESSION', 'true').lower() == 'true')
    enable_deduplication: bool = field(default_factory=lambda: os.environ.get('KAREN_ENABLE_DEDUPLICATION', 'true').lower() == 'true')
    cache_directory: str = field(default_factory=lambda: os.environ.get('KAREN_CACHE_DIRECTORY', './model_cache'))
    temp_directory: str = field(default_factory=lambda: os.environ.get('KAREN_TEMP_DIRECTORY', './temp'))
    max_cache_size: int = field(default_factory=lambda: int(os.environ.get('KAREN_MAX_CACHE_SIZE', str(50 * 1024 * 1024 * 1024))))  # 50GB
    cleanup_interval: float = field(default_factory=lambda: float(os.environ.get('KAREN_CLEANUP_INTERVAL', '3600.0')))
    network_aware_scheduling: bool = field(default_factory=lambda: os.environ.get('KAREN_NETWORK_AWARE_SCHEDULING', 'true').lower() == 'true')
    pause_on_metered: bool = field(default_factory=lambda: os.environ.get('KAREN_PAUSE_ON_METERED', 'true').lower() == 'true')
    background_download_window: Tuple[int, int] = field(default_factory=lambda: (22, 6) if os.environ.get('KAREN_BACKGROUND_WINDOW') is None else (int(os.environ.get('KAREN_BACKGROUND_WINDOW', '22-6').split('-')[0]), int(os.environ.get('KAREN_BACKGROUND_WINDOW', '22-6').split('-')[1])))
    critical_models: Set[str] = field(default_factory=lambda: set(os.environ.get('KAREN_CRITICAL_MODELS', '').split(',')) if os.environ.get('KAREN_CRITICAL_MODELS') else set())


class DownloadQueue:
    """Priority-based download queue with concurrent management."""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self._queue: List[DownloadTask] = []
        self._active_downloads: Set[str] = set()  # cache_keys
        self._lock = threading.RLock()
        self._not_empty = threading.Condition(self._lock)
        self._slot_available = threading.Condition(self._lock)
    
    def put(self, task: DownloadTask) -> None:
        """Add a download task to queue."""
        with self._lock:
            # Check if already queued
            cache_key = task.metadata.cache_key
            if cache_key in self._active_downloads:
                logger.debug(f"Task for {cache_key} already active")
                return
            
            # Check if already in queue
            for existing in self._queue:
                if existing.metadata.cache_key == cache_key:
                    # Update priority if higher
                    if task.priority < existing.priority:
                        existing.priority = task.priority
                        self._queue.sort()  # Re-sort queue
                    return
            
            self._queue.append(task)
            self._queue.sort()
            self._not_empty.notify()
            logger.debug(f"Added download task for {cache_key} with priority {task.priority.name}")
    
    def get(self, timeout: Optional[float] = None) -> Optional[DownloadTask]:
        """Get next download task, respecting concurrency limits."""
        with self._not_empty:
            while True:
                # Check if we can start a new download
                if len(self._active_downloads) < self.max_concurrent and self._queue:
                    task = self._queue.pop(0)
                    self._active_downloads.add(task.metadata.cache_key)
                    return task
                
                # Wait for slot or new task
                if timeout is None:
                    self._not_empty.wait()
                else:
                    if not self._not_empty.wait(timeout):
                        return None
    
    def task_done(self, cache_key: str) -> None:
        """Mark a task as completed (successful or failed)."""
        with self._lock:
            self._active_downloads.discard(cache_key)
            self._slot_available.notify()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self._lock:
            return {
                "queued_tasks": len(self._queue),
                "active_downloads": len(self._active_downloads),
                "max_concurrent": self.max_concurrent,
                "queue_by_priority": {
                    priority.name: sum(1 for t in self._queue if t.priority == priority)
                    for priority in DownloadPriority
                }
            }
    
    def get_task(self, cache_key: str) -> Optional[DownloadTask]:
        """Get a specific task by cache key."""
        with self._lock:
            # Check active downloads first
            for task in self._queue:
                if task.metadata.cache_key == cache_key:
                    return task
            return None
    
    def cancel_task(self, cache_key: str) -> bool:
        """Cancel a queued task."""
        with self._lock:
            for i, task in enumerate(self._queue):
                if task.metadata.cache_key == cache_key:
                    task.status = DownloadStatus.CANCELLED
                    self._queue.pop(i)
                    logger.info(f"Cancelled queued task for {cache_key}")
                    return True
            return False
    
    def pause_task(self, cache_key: str) -> bool:
        """Pause a queued task."""
        with self._lock:
            for task in self._queue:
                if task.metadata.cache_key == cache_key:
                    task.status = DownloadStatus.PAUSED
                    logger.info(f"Paused queued task for {cache_key}")
                    return True
            return False
    
    def resume_task(self, cache_key: str) -> bool:
        """Resume a paused task."""
        with self._lock:
            for task in self._queue:
                if task.metadata.cache_key == cache_key and task.status == DownloadStatus.PAUSED:
                    task.status = DownloadStatus.PENDING
                    self._queue.sort()  # Re-sort queue
                    logger.info(f"Resumed task for {cache_key}")
                    return True
            return False


class CacheManager:
    """Manages local model storage with compression and deduplication."""
    
    def __init__(self, cache_dir: str, max_size: int = 50 * 1024 * 1024 * 1024):
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size
        self._lock = threading.RLock()
        self._index: Dict[str, Dict[str, Any]] = {}  # cache_key -> metadata
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "models").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
        (self.cache_dir / "temp").mkdir(exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    def _load_index(self) -> None:
        """Load cache index from disk."""
        index_file = self.cache_dir / "metadata" / "index.json"
        try:
            if index_file.exists():
                with open(index_file, 'r') as f:
                    self._index = json.load(f)
                logger.info(f"Loaded cache index with {len(self._index)} entries")
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            self._index = {}
    
    def _save_index(self) -> None:
        """Save cache index to disk."""
        index_file = self.cache_dir / "metadata" / "index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def get_model_path(self, metadata: ModelMetadata) -> Path:
        """Get file path for a cached model."""
        return self.cache_dir / "models" / f"{metadata.cache_key}.model"
    
    def get_metadata_path(self, metadata: ModelMetadata) -> Path:
        """Get metadata file path for a cached model."""
        return self.cache_dir / "metadata" / f"{metadata.cache_key}.json"
    
    def get_temp_path(self, metadata: ModelMetadata) -> Path:
        """Get a temporary path for downloading."""
        return self.cache_dir / "temp" / f"{metadata.cache_key}.download"
    
    def is_cached(self, metadata: ModelMetadata) -> bool:
        """Check if a model is cached and valid."""
        cache_key = metadata.cache_key
        if cache_key not in self._index:
            return False
        
        model_path = self.get_model_path(metadata)
        if not model_path.exists():
            return False
        
        # Verify size matches
        cached_info = self._index[cache_key]
        actual_size = model_path.stat().st_size
        if cached_info.get('size_bytes', 0) != actual_size:
            logger.warning(f"Size mismatch for cached model {cache_key}")
            return False
        
        # Verify checksum if available
        if metadata.checksum and cached_info.get('checksum'):
            if not self._verify_checksum(model_path, metadata.checksum):
                logger.warning(f"Checksum mismatch for cached model {cache_key}")
                return False
        
        return True
    
    def store_model(self, metadata: ModelMetadata, source_path: Union[str, Path]) -> bool:
        """Store a model in the cache with compression and deduplication."""
        try:
            source_path = Path(source_path)
            cache_key = metadata.cache_key
            model_path = self.get_model_path(metadata)
            metadata_path = self.get_metadata_path(metadata)
            
            # Check for duplicates
            if self.is_cached(metadata):
                logger.debug(f"Model {cache_key} already cached")
                return True
            
            # Calculate source checksum for deduplication
            source_checksum = self._calculate_checksum(source_path)
            
            # Check for existing file with same content (deduplication)
            duplicate_key = None
            for existing_key, info in self._index.items():
                if info.get('content_checksum') == source_checksum:
                    duplicate_key = existing_key
                    break
            
            if duplicate_key:
                # Create hard link instead of copying
                duplicate_metadata = ModelMetadata(
                    name="", provider="", model_type="", version=""
                )
                duplicate_metadata.cache_key = duplicate_key
                duplicate_path = self.get_model_path(duplicate_metadata)
                try:
                    model_path.hardlink_to(duplicate_path)
                    logger.info(f"Created hard link for {cache_key} -> {duplicate_key}")
                except OSError:
                    # Fallback to copy if hard link fails
                    shutil.copy2(duplicate_path, model_path)
            else:
                # Compress and store
                if metadata.compression_type == "gzip":
                    self._compress_gzip(source_path, model_path)
                elif metadata.compression_type == "zlib":
                    self._compress_zlib(source_path, model_path)
                else:
                    shutil.copy2(source_path, model_path)
            
            # Store metadata
            metadata_dict = {
                'name': metadata.name,
                'provider': metadata.provider,
                'model_type': metadata.model_type,
                'capabilities': list(metadata.capabilities),
                'size_bytes': model_path.stat().st_size,
                'version': metadata.version,
                'checksum': metadata.checksum,
                'download_url': metadata.download_url,
                'compression_type': metadata.compression_type,
                'encryption_enabled': metadata.encryption_enabled,
                'tags': list(metadata.tags),
                'content_checksum': source_checksum,
                'cached_at': time.time(),
                'last_accessed': time.time(),
                'access_count': 0
            }
            
            self._index[cache_key] = metadata_dict
            
            # Save metadata file
            with open(metadata_path, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
            
            # Update main index
            self._save_index()
            
            # Check cache size and evict if necessary
            self._ensure_cache_size()
            
            logger.info(f"Cached model {cache_key} ({model_path.stat().st_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache model {metadata.cache_key}: {e}")
            return False
    
    def get_model(self, metadata: ModelMetadata) -> Optional[Path]:
        """Get a cached model, decompressing if necessary."""
        cache_key = metadata.cache_key
        
        if not self.is_cached(metadata):
            return None
        
        try:
            model_path = self.get_model_path(metadata)
            
            # Update access statistics
            if cache_key in self._index:
                self._index[cache_key]['last_accessed'] = time.time()
                self._index[cache_key]['access_count'] += 1
                self._save_index()
            
            # Decompress if needed
            if metadata.compression_type == "gzip":
                return self._decompress_gzip(model_path)
            elif metadata.compression_type == "zlib":
                return self._decompress_zlib(model_path)
            else:
                return model_path
                
        except Exception as e:
            logger.error(f"Failed to get cached model {cache_key}: {e}")
            return None
    
    def remove_model(self, metadata: ModelMetadata) -> bool:
        """Remove a model from cache."""
        cache_key = metadata.cache_key
        
        try:
            model_path = self.get_model_path(metadata)
            metadata_path = self.get_metadata_path(metadata)
            
            # Remove files
            if model_path.exists():
                model_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            # Remove from index
            if cache_key in self._index:
                del self._index[cache_key]
                self._save_index()
            
            logger.info(f"Removed cached model {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove cached model {cache_key}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size = sum(info['size_bytes'] for info in self._index.values())
            total_models = len(self._index)
            
            # Size by compression type
            compression_stats = defaultdict(int)
            for info in self._index.values():
                compression_stats[info.get('compression_type', 'none')] += info['size_bytes']
            
            # Most/least accessed models
            if self._index:
                most_accessed = max(self._index.items(), key=lambda x: x[1]['access_count'])
                least_accessed = min(self._index.items(), key=lambda x: x[1]['access_count'])
            else:
                most_accessed = least_accessed = None
            
            return {
                'total_models': total_models,
                'total_size_bytes': total_size,
                'total_size_gb': total_size / (1024**3),
                'max_size_gb': self.max_size / (1024**3),
                'utilization_percent': (total_size / self.max_size) * 100,
                'compression_stats': dict(compression_stats),
                'most_accessed': most_accessed[0] if most_accessed else None,
                'least_accessed': least_accessed[0] if least_accessed else None
            }
    
    def _ensure_cache_size(self) -> None:
        """Ensure cache doesn't exceed max size using LRU eviction."""
        current_size = sum(info['size_bytes'] for info in self._index.values())
        
        if current_size <= self.max_size:
            return
        
        # Sort by last accessed time (LRU)
        sorted_items = sorted(self._index.items(), key=lambda x: x[1]['last_accessed'])
        
        bytes_to_free = current_size - self.max_size
        freed_bytes = 0
        
        for cache_key, info in sorted_items:
            if freed_bytes >= bytes_to_free:
                break
            
            # Skip critical models
            model_key = f"{info['provider']}:{info['name']}"
            if model_key in DownloadConfig().critical_models:
                continue
            
            metadata = ModelMetadata(
                name=info['name'],
                provider=info['provider'],
                model_type=info['model_type'],
                version=""
            )
            metadata.cache_key = cache_key
            
            if self.remove_model(metadata):
                freed_bytes += info['size_bytes']
                logger.debug(f"Evicted {cache_key} to free space")
        
        logger.info(f"Freed {freed_bytes} bytes from cache")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file checksum matches expected."""
        return self._calculate_checksum(file_path) == expected_checksum
    
    def _compress_gzip(self, source: Path, target: Path) -> None:
        """Compress file using gzip."""
        with open(source, 'rb') as f_in:
            with gzip.open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _compress_zlib(self, source: Path, target: Path) -> None:
        """Compress file using zlib."""
        with open(source, 'rb') as f_in:
            with open(target, 'wb') as f_out:
                compressor = zlib.compressobj()
                while True:
                    chunk = f_in.read(8192)
                    if not chunk:
                        break
                    compressed = compressor.compress(chunk)
                    if compressed:
                        f_out.write(compressed)
                # Flush remaining data
                remaining = compressor.flush()
                if remaining:
                    f_out.write(remaining)
    
    def _decompress_gzip(self, compressed_path: Path) -> Path:
        """Decompress gzip file to temporary location."""
        temp_path = self.cache_dir / "temp" / f"{compressed_path.stem}_decompressed"
        
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(temp_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return temp_path
    
    def _decompress_zlib(self, compressed_path: Path) -> Path:
        """Decompress zlib file to temporary location."""
        temp_path = self.cache_dir / "temp" / f"{compressed_path.stem}_decompressed"
        
        with open(compressed_path, 'rb') as f_in:
            with open(temp_path, 'wb') as f_out:
                decompressor = zlib.decompressobj()
                while True:
                    chunk = f_in.read(8192)
                    if not chunk:
                        break
                    decompressed = decompressor.decompress(chunk)
                    if decompressed:
                        f_out.write(decompressed)
                # Flush remaining data
                remaining = decompressor.flush()
                if remaining:
                    f_out.write(remaining)
        
        return temp_path


class DownloadScheduler:
    """Intelligent download scheduling based on network conditions and user preferences."""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self._network_monitor = get_network_monitor()
        self._scheduler_active = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._download_callbacks: List[Callable[[DownloadTask], None]] = []
        self._lock = threading.RLock()
    
    async def start(self) -> None:
        """Start download scheduler."""
        if self._scheduler_active:
            return
        
        self._scheduler_active = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Download scheduler started")
    
    async def stop(self) -> None:
        """Stop download scheduler."""
        if not self._scheduler_active:
            return
        
        self._scheduler_active = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Download scheduler stopped")
    
    def register_callback(self, callback: Callable[[DownloadTask], None]) -> None:
        """Register callback for download events."""
        with self._lock:
            self._download_callbacks.append(callback)
    
    def should_download_now(self, task: DownloadTask) -> Tuple[bool, str]:
        """Determine if a task should download now based on conditions."""
        network_status = self._network_monitor.get_current_status()
        current_hour = datetime.now().hour
        
        # Check network status
        if network_status == NetworkStatus.OFFLINE:
            return False, "Network offline"
        
        if network_status == NetworkStatus.DEGRADED:
            # Only allow critical downloads on degraded network
            if task.priority != DownloadPriority.CRITICAL:
                return False, "Network degraded, only critical downloads allowed"
        
        # Check metered connection preference
        if self.config.pause_on_metered and self._is_metered_connection():
            if task.priority != DownloadPriority.CRITICAL:
                return False, "Metered connection, only critical downloads allowed"
        
        # Check background download window
        if task.priority == DownloadPriority.BACKGROUND:
            start_hour, end_hour = self.config.background_download_window
            if start_hour <= end_hour:
                # Same day window (e.g., 22:00 to 06:00)
                if not (start_hour <= current_hour < end_hour):
                    return False, f"Outside background window ({start_hour}:00-{end_hour}:00)"
            else:
                # Cross-midnight window (e.g., 22:00 to 06:00 next day)
                if not (current_hour >= start_hour or current_hour < end_hour):
                    return False, f"Outside background window ({start_hour}:00-{end_hour}:00)"
        
        # Check download speed limits
        if self.config.max_download_speed > 0:
            # This would be checked during actual download
            pass
        
        return True, "Download allowed"
    
    def _is_metered_connection(self) -> bool:
        """Check if current connection is metered."""
        # This is a placeholder - in a real implementation, you'd check
        # system network settings or use platform-specific APIs
        return False
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._scheduler_active:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                # The actual scheduling logic is handled by the ModelDownloadManager
                # This loop could be used for periodic maintenance tasks
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(30)


class ModelDownloadManager:
    """
    Main model download manager that coordinates downloading, caching, and scheduling.
    
    This class provides the primary interface for automatic model downloading and caching,
    integrating with network monitoring and model availability cache systems.
    """
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self._cache_manager = CacheManager(config.cache_directory, config.max_cache_size)
        self._download_queue = DownloadQueue(config.max_concurrent_downloads)
        self._scheduler = DownloadScheduler(config)
        self._network_monitor = get_network_monitor()
        self._model_cache = get_model_availability_cache()
        
        # Active downloads tracking
        self._active_downloads: Dict[str, DownloadTask] = {}
        self._download_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
        
        # Background tasks
        self._downloader_active = False
        self._downloader_tasks: List[asyncio.Task] = []
        
        # Statistics
        self._total_downloads = 0
        self._successful_downloads = 0
        self._failed_downloads = 0
        self._bytes_downloaded = 0
        
        logger.info(f"ModelDownloadManager initialized with cache at {config.cache_directory}")
    
    async def start(self) -> None:
        """Start download manager and background tasks."""
        if self._downloader_active:
            logger.warning("Download manager already active")
            return
        
        self._downloader_active = True
        
        # Start scheduler
        await self._scheduler.start()
        
        # Start download workers
        for i in range(self.config.max_concurrent_downloads):
            worker = asyncio.create_task(self._download_worker(f"worker-{i}"))
            self._downloader_tasks.append(worker)
        
        # Register network status callback
        self._network_monitor.register_status_callback(self._on_network_status_change)
        
        logger.info("Model download manager started")
    
    async def stop(self) -> None:
        """Stop download manager and cleanup resources."""
        if not self._downloader_active:
            return
        
        self._downloader_active = False
        
        # Stop scheduler
        await self._scheduler.stop()
        
        # Cancel download workers
        for task in self._downloader_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Cancel active downloads
        with self._lock:
            for task in self._active_downloads.values():
                task.status = DownloadStatus.CANCELLED
        
        logger.info("Model download manager stopped")
    
    async def download_model(
        self,
        metadata: ModelMetadata,
        priority: DownloadPriority = DownloadPriority.NORMAL,
        force: bool = False
    ) -> bool:
        """
        Queue a model for download.
        
        Args:
            metadata: Model metadata
            priority: Download priority
            force: Force download even if already cached
            
        Returns:
            True if download was queued successfully
        """
        cache_key = metadata.cache_key
        
        # Check if already cached
        if not force and self._cache_manager.is_cached(metadata):
            logger.debug(f"Model {cache_key} already cached")
            return True
        
        # Create download task
        task = DownloadTask(
            metadata=metadata,
            priority=priority,
            max_retries=3 if priority != DownloadPriority.CRITICAL else 5,
            timeout=self.config.timeout
        )
        
        # Add to queue
        self._download_queue.put(task)
        
        logger.info(f"Queued download for {cache_key} with priority {priority.name}")
        return True
    
    def get_download_status(self, cache_key: str) -> Optional[DownloadTask]:
        """Get status of a download task."""
        with self._lock:
            # Check active downloads
            if cache_key in self._active_downloads:
                return self._active_downloads[cache_key]
            
            # Check queue
            return self._download_queue.get_task(cache_key)
    
    def cancel_download(self, cache_key: str) -> bool:
        """Cancel a download task."""
        # Try to cancel in queue first
        if self._download_queue.cancel_task(cache_key):
            return True
        
        # Cancel active download
        with self._lock:
            if cache_key in self._active_downloads:
                task = self._active_downloads[cache_key]
                task.status = DownloadStatus.CANCELLED
                return True
        
        return False
    
    def pause_download(self, cache_key: str) -> bool:
        """Pause a download task."""
        # Try to pause in queue first
        if self._download_queue.pause_task(cache_key):
            return True
        
        # Pause active download
        with self._lock:
            if cache_key in self._active_downloads:
                task = self._active_downloads[cache_key]
                task.status = DownloadStatus.PAUSED
                return True
        
        return False
    
    def resume_download(self, cache_key: str) -> bool:
        """Resume a paused download task."""
        # Try to resume in queue first
        if self._download_queue.resume_task(cache_key):
            return True
        
        # Resume active download
        with self._lock:
            if cache_key in self._active_downloads:
                task = self._active_downloads[cache_key]
                if task.status == DownloadStatus.PAUSED:
                    task.status = DownloadStatus.DOWNLOADING
                    return True
        
        return False
    
    def get_cached_model(self, metadata: ModelMetadata) -> Optional[Path]:
        """Get a cached model, decompressing if necessary."""
        return self._cache_manager.get_model(metadata)
    
    def is_model_cached(self, metadata: ModelMetadata) -> bool:
        """Check if a model is cached and valid."""
        return self._cache_manager.is_cached(metadata)
    
    def remove_cached_model(self, metadata: ModelMetadata) -> bool:
        """Remove a model from cache."""
        return self._cache_manager.remove_model(metadata)
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get comprehensive download statistics."""
        with self._lock:
            queue_status = self._download_queue.get_queue_status()
            cache_stats = self._cache_manager.get_cache_stats()
            
            return {
                "total_downloads": self._total_downloads,
                "successful_downloads": self._successful_downloads,
                "failed_downloads": self._failed_downloads,
                "success_rate": self._successful_downloads / max(self._total_downloads, 1),
                "bytes_downloaded": self._bytes_downloaded,
                "active_downloads": len(self._active_downloads),
                "queue_status": queue_status,
                "cache_stats": cache_stats,
                "network_status": self._network_monitor.get_current_status().value
            }
    
    async def _download_worker(self, worker_id: str) -> None:
        """Worker process for handling downloads."""
        logger.info(f"Download worker {worker_id} started")
        
        while self._downloader_active:
            try:
                # Get next task from queue
                task = self._download_queue.get(timeout=1.0)
                if task is None:
                    continue
                
                cache_key = task.metadata.cache_key
                
                # Check if should download now
                should_download, reason = self._scheduler.should_download_now(task)
                if not should_download:
                    # Re-queue with lower priority if not critical
                    if task.priority != DownloadPriority.CRITICAL:
                        task.priority = DownloadPriority.BACKGROUND
                        self._download_queue.put(task)
                        logger.debug(f"Re-queued {cache_key}: {reason}")
                    continue
                
                # Check if already cached
                if self._cache_manager.is_cached(task.metadata):
                    task.status = DownloadStatus.COMPLETED
                    self._download_queue.task_done(cache_key)
                    continue
                
                # Start download
                with self._lock:
                    self._active_downloads[cache_key] = task
                    task.status = DownloadStatus.DOWNLOADING
                    task.started_at = time.time()
                
                try:
                    success = await self._perform_download(task)
                    
                    with self._lock:
                        if success:
                            task.status = DownloadStatus.COMPLETED
                            task.completed_at = time.time()
                            self._successful_downloads += 1
                        else:
                            task.status = DownloadStatus.FAILED
                            self._failed_downloads += 1
                            
                            # Retry if possible
                            if task.should_retry():
                                task.status = DownloadStatus.RETRYING
                                task.retry_count += 1
                                # Calculate backoff delay
                                delay = min(
                                    self.config.retry_delay_base * (2 ** task.retry_count),
                                    self.config.retry_delay_max
                                )
                                task.last_activity = time.time() + delay
                                self._download_queue.put(task)
                                logger.info(f"Scheduling retry for {cache_key} in {delay}s")
                        
                        self._total_downloads += 1
                        del self._active_downloads[cache_key]
                    
                    self._download_queue.task_done(cache_key)
                    
                except Exception as e:
                    logger.error(f"Download error for {cache_key}: {e}")
                    with self._lock:
                        task.status = DownloadStatus.FAILED
                        task.error_message = str(e)
                        self._failed_downloads += 1
                        if cache_key in self._active_downloads:
                            del self._active_downloads[cache_key]
                    self._download_queue.task_done(cache_key)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Download worker {worker_id} stopped")
    
    async def _perform_download(self, task: DownloadTask) -> bool:
        """Perform the actual download with progress tracking."""
        metadata = task.metadata
        cache_key = metadata.cache_key
        
        try:
            # Get temp path
            temp_path = self._cache_manager.get_temp_path(metadata)
            task.temp_file_path = str(temp_path)
            
            # Start download
            if not metadata.download_url:
                raise Exception("No download URL available")
            
            # Use aiohttp for async download
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Check for partial download (resume support)
                mode = 'wb'
                headers = {}
                
                if task.resume_supported and temp_path.exists():
                    # Get existing file size
                    existing_size = temp_path.stat().st_size
                    if existing_size > 0:
                        mode = 'ab'
                        headers['Range'] = f'bytes={existing_size}-'
                        task.bytes_downloaded = existing_size
                
                async with session.get(metadata.download_url, headers=headers) as response:
                    if response.status not in [200, 206]:  # 206 for partial content
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    # Get total size if available
                    if 'content-length' in response.headers:
                        task.total_bytes = int(response.headers['content-length'])
                        if mode == 'ab':  # Partial download
                            task.total_bytes += task.bytes_downloaded
                    
                    # Download with progress tracking
                    start_time = time.time()
                    last_update = start_time
                    
                    async with aiofiles.open(temp_path, mode) as f:
                        async for chunk in response.content.iter_chunked(task.chunk_size):
                            if not self._downloader_active or task.status == DownloadStatus.CANCELLED:
                                return False
                            
                            await f.write(chunk)
                            chunk_size = len(chunk)
                            task.bytes_downloaded += chunk_size
                            task.last_activity = time.time()
                            
                            # Update progress and speed
                            current_time = time.time()
                            if current_time - last_update >= 1.0:  # Update every second
                                elapsed = current_time - start_time
                                task.download_speed = task.bytes_downloaded / elapsed
                                task.progress = task.bytes_downloaded / max(task.total_bytes, 1)
                                last_update = current_time
                                
                                # Update model cache with progress
                                if hasattr(self._model_cache, "_update_download_progress"):
                                    pass
            # Verify download if configured
            if self.config.verify_downloads and metadata.checksum:
                task.status = DownloadStatus.VERIFYING
                if not self._cache_manager._verify_checksum(temp_path, metadata.checksum):
                    raise Exception("Download verification failed - checksum mismatch")
            
            # Store in cache
            task.final_file_path = str(self._cache_manager.get_model_path(metadata))
            success = self._cache_manager.store_model(metadata, temp_path)
            
            if success:
                # Update statistics
                self._bytes_downloaded += task.bytes_downloaded
                
                # Update model availability cache
                self._model_cache.record_model_usage(
                    metadata.provider, metadata.name, "download", True
                )
                
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
                
                logger.info(f"Successfully downloaded {cache_key}")
                return True
            else:
                raise Exception("Failed to store model in cache")
                
        except Exception as e:
            logger.error(f"Download failed for {cache_key}: {e}")
            task.error_message = str(e)
            
            # Clean up temp file on failure
            if task.temp_file_path and os.path.exists(task.temp_file_path):
                try:
                    os.unlink(task.temp_file_path)
                except:
                    pass
            
            return False
    
    async def _on_network_status_change(self, old_status: NetworkStatus, new_status: NetworkStatus) -> None:
        """Handle network status changes."""
        logger.info(f"Network status changed: {old_status.value} -> {new_status.value}")
        
        # If network is restored, retry failed downloads
        if new_status == NetworkStatus.ONLINE and old_status != NetworkStatus.ONLINE:
            await self._retry_failed_downloads()
        
        # If network goes offline, pause non-critical downloads
        elif new_status == NetworkStatus.OFFLINE:
            with self._lock:
                for task in self._active_downloads.values():
                    if task.priority != DownloadPriority.CRITICAL:
                        task.status = DownloadStatus.PAUSED
    
    async def _retry_failed_downloads(self) -> None:
        """Retry downloads that failed due to network issues."""
        with self._lock:
            failed_tasks = [
                task for task in self._active_downloads.values()
                if task.status == DownloadStatus.FAILED and task.should_retry()
            ]
        
        for task in failed_tasks:
            task.status = DownloadStatus.RETRYING
            task.retry_count += 1
            self._download_queue.put(task)
            logger.info(f"Retrying download for {task.metadata.cache_key}")


# Global instance
_model_download_manager: Optional[ModelDownloadManager] = None
_manager_lock = threading.RLock()


def get_model_download_manager(config: Optional[DownloadConfig] = None) -> ModelDownloadManager:
    """Get or create global model download manager instance."""
    global _model_download_manager
    if _model_download_manager is None:
        with _manager_lock:
            if _model_download_manager is None:
                _model_download_manager = ModelDownloadManager(config or DownloadConfig())
    return _model_download_manager


# Export main classes for easy import
__all__ = [
    "DownloadStatus",
    "DownloadPriority",
    "ModelMetadata",
    "DownloadTask",
    "DownloadConfig",
    "DownloadQueue",
    "CacheManager",
    "DownloadScheduler",
    "ModelDownloadManager",
    "get_model_download_manager",
]