"""
Model Storage Monitoring for Resource Usage Tracking.

This module provides storage monitoring capabilities for model orchestrator,
integrating with existing resource monitoring patterns.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import asyncio

from ai_karen_engine.monitoring.model_orchestrator_metrics import (
    get_model_orchestrator_metrics,
    ModelOperationStatus
)

logger = logging.getLogger(__name__)


@dataclass
class StorageInfo:
    """Storage information for a path."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


@dataclass
class ModelStorageStats:
    """Storage statistics for models."""
    library: str
    model_count: int
    total_size_bytes: int
    pinned_count: int
    pinned_size_bytes: int
    last_accessed: Optional[datetime] = None
    oldest_model: Optional[str] = None


class ModelStorageMonitor:
    """
    Monitor storage usage for model orchestrator operations.
    
    Tracks disk usage, model sizes, and provides data for
    garbage collection and quota enforcement.
    """
    
    def __init__(self, models_root: Path = None):
        self.models_root = models_root or Path("models")
        self.metrics = get_model_orchestrator_metrics()
        self.cache_duration = timedelta(minutes=5)
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        logger.debug(f"Storage monitor initialized for {self.models_root}")
    
    def get_disk_usage(self, path: Path = None) -> StorageInfo:
        """Get disk usage information for a path."""
        path = path or self.models_root
        
        try:
            # Ensure path exists
            path.mkdir(parents=True, exist_ok=True)
            
            # Get disk usage
            total, used, free = shutil.disk_usage(path)
            usage_percent = (used / total) * 100 if total > 0 else 0
            
            return StorageInfo(
                total_bytes=total,
                used_bytes=used,
                free_bytes=free,
                usage_percent=usage_percent
            )
            
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return StorageInfo(0, 0, 0, 0.0)
    
    def get_directory_size(self, path: Path) -> int:
        """Get the total size of a directory and its contents."""
        if not path.exists():
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    try:
                        total_size += filepath.stat().st_size
                    except (OSError, FileNotFoundError):
                        # Skip files that can't be accessed
                        continue
        except Exception as e:
            logger.warning(f"Error calculating directory size for {path}: {e}")
        
        return total_size
    
    def get_model_storage_stats(self, use_cache: bool = True) -> Dict[str, ModelStorageStats]:
        """Get storage statistics by library."""
        cache_key = "model_storage_stats"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data
        
        stats = {}
        
        try:
            # Load registry to get model information
            registry_path = self.models_root / "llm_registry.json"
            registry_data = {}
            
            if registry_path.exists():
                try:
                    with open(registry_path, 'r') as f:
                        registry_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Error loading registry: {e}")
            
            # Scan model directories
            for library_dir in self.models_root.iterdir():
                if not library_dir.is_dir():
                    continue
                
                library_name = library_dir.name
                model_count = 0
                total_size = 0
                pinned_count = 0
                pinned_size = 0
                last_accessed = None
                oldest_model = None
                oldest_time = None
                
                # Scan models in library directory
                for model_dir in library_dir.iterdir():
                    if not model_dir.is_dir():
                        continue
                    
                    model_count += 1
                    model_size = self.get_directory_size(model_dir)
                    total_size += model_size
                    
                    # Check if model is pinned (from registry)
                    model_id = f"{library_name}/{model_dir.name}"
                    model_info = registry_data.get(model_id, {})
                    is_pinned = model_info.get("pinned", False)
                    
                    if is_pinned:
                        pinned_count += 1
                        pinned_size += model_size
                    
                    # Track access times
                    try:
                        access_time = datetime.fromtimestamp(model_dir.stat().st_atime)
                        if last_accessed is None or access_time > last_accessed:
                            last_accessed = access_time
                        
                        if oldest_time is None or access_time < oldest_time:
                            oldest_time = access_time
                            oldest_model = model_dir.name
                    except Exception:
                        pass
                
                if model_count > 0:
                    stats[library_name] = ModelStorageStats(
                        library=library_name,
                        model_count=model_count,
                        total_size_bytes=total_size,
                        pinned_count=pinned_count,
                        pinned_size_bytes=pinned_size,
                        last_accessed=last_accessed,
                        oldest_model=oldest_model
                    )
            
            # Cache results
            self._cache[cache_key] = (datetime.now(), stats)
            
            # Update metrics
            self._update_storage_metrics(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting model storage stats: {e}")
            return {}
    
    def _update_storage_metrics(self, stats: Dict[str, ModelStorageStats]):
        """Update Prometheus metrics with storage data."""
        try:
            # Update storage usage metrics
            storage_by_library = {
                library: stat.total_size_bytes 
                for library, stat in stats.items()
            }
            self.metrics.update_storage_metrics(storage_by_library)
            
            # Update model count metrics
            counts_by_library = {}
            for library, stat in stats.items():
                counts_by_library[library] = {
                    "true": stat.pinned_count,
                    "false": stat.model_count - stat.pinned_count
                }
            self.metrics.update_model_count_metrics(counts_by_library)
            
        except Exception as e:
            logger.error(f"Error updating storage metrics: {e}")
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """Get a comprehensive storage summary."""
        try:
            disk_info = self.get_disk_usage()
            model_stats = self.get_model_storage_stats()
            
            total_models = sum(stat.model_count for stat in model_stats.values())
            total_model_size = sum(stat.total_size_bytes for stat in model_stats.values())
            total_pinned = sum(stat.pinned_count for stat in model_stats.values())
            
            return {
                "disk_usage": {
                    "total_bytes": disk_info.total_bytes,
                    "used_bytes": disk_info.used_bytes,
                    "free_bytes": disk_info.free_bytes,
                    "usage_percent": disk_info.usage_percent
                },
                "model_storage": {
                    "total_models": total_models,
                    "total_size_bytes": total_model_size,
                    "total_pinned": total_pinned,
                    "libraries": len(model_stats),
                    "by_library": {
                        library: {
                            "model_count": stat.model_count,
                            "total_size_bytes": stat.total_size_bytes,
                            "pinned_count": stat.pinned_count,
                            "pinned_size_bytes": stat.pinned_size_bytes,
                            "last_accessed": stat.last_accessed.isoformat() if stat.last_accessed else None,
                            "oldest_model": stat.oldest_model
                        }
                        for library, stat in model_stats.items()
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting storage summary: {e}")
            return {"error": str(e)}
    
    def check_storage_quota(self, quota_bytes: Optional[int] = None) -> Dict[str, Any]:
        """Check if storage usage is within quota limits."""
        if quota_bytes is None:
            return {"quota_enabled": False}
        
        try:
            model_stats = self.get_model_storage_stats()
            total_used = sum(stat.total_size_bytes for stat in model_stats.values())
            
            quota_percent = (total_used / quota_bytes) * 100 if quota_bytes > 0 else 0
            over_quota = total_used > quota_bytes
            
            return {
                "quota_enabled": True,
                "quota_bytes": quota_bytes,
                "used_bytes": total_used,
                "quota_percent": quota_percent,
                "over_quota": over_quota,
                "available_bytes": max(0, quota_bytes - total_used)
            }
            
        except Exception as e:
            logger.error(f"Error checking storage quota: {e}")
            return {"error": str(e)}
    
    def identify_gc_candidates(
        self,
        target_free_bytes: int,
        exclude_pinned: bool = True
    ) -> List[Dict[str, Any]]:
        """Identify models that are candidates for garbage collection."""
        candidates = []
        
        try:
            registry_path = self.models_root / "llm_registry.json"
            registry_data = {}
            
            if registry_path.exists():
                try:
                    with open(registry_path, 'r') as f:
                        registry_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Error loading registry for GC: {e}")
            
            # Collect model information
            for library_dir in self.models_root.iterdir():
                if not library_dir.is_dir():
                    continue
                
                library_name = library_dir.name
                
                for model_dir in library_dir.iterdir():
                    if not model_dir.is_dir():
                        continue
                    
                    model_id = f"{library_name}/{model_dir.name}"
                    model_info = registry_data.get(model_id, {})
                    
                    # Skip pinned models if requested
                    if exclude_pinned and model_info.get("pinned", False):
                        continue
                    
                    try:
                        stat = model_dir.stat()
                        size_bytes = self.get_directory_size(model_dir)
                        
                        candidates.append({
                            "model_id": model_id,
                            "library": library_name,
                            "path": str(model_dir),
                            "size_bytes": size_bytes,
                            "last_accessed": datetime.fromtimestamp(stat.st_atime),
                            "last_modified": datetime.fromtimestamp(stat.st_mtime),
                            "pinned": model_info.get("pinned", False)
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error processing model {model_id}: {e}")
            
            # Sort by last accessed time (oldest first)
            candidates.sort(key=lambda x: x["last_accessed"])
            
            # Select candidates until we have enough space
            selected = []
            total_freed = 0
            
            for candidate in candidates:
                selected.append(candidate)
                total_freed += candidate["size_bytes"]
                
                if total_freed >= target_free_bytes:
                    break
            
            return selected
            
        except Exception as e:
            logger.error(f"Error identifying GC candidates: {e}")
            return []
    
    def monitor_storage_health(self) -> Dict[str, Any]:
        """Monitor storage health and return status."""
        try:
            disk_info = self.get_disk_usage()
            model_stats = self.get_model_storage_stats()
            
            # Determine health status
            health_status = "healthy"
            warnings = []
            
            # Check disk usage
            if disk_info.usage_percent > 90:
                health_status = "critical"
                warnings.append("Disk usage above 90%")
            elif disk_info.usage_percent > 80:
                health_status = "warning"
                warnings.append("Disk usage above 80%")
            
            # Check for very old models
            now = datetime.now()
            for library, stat in model_stats.items():
                if stat.last_accessed and (now - stat.last_accessed).days > 90:
                    warnings.append(f"Library {library} has models not accessed in 90+ days")
            
            return {
                "status": health_status,
                "warnings": warnings,
                "disk_usage_percent": disk_info.usage_percent,
                "free_bytes": disk_info.free_bytes,
                "total_models": sum(stat.model_count for stat in model_stats.values()),
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error monitoring storage health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_periodic_monitoring(self, interval_seconds: int = 300):
        """Start periodic storage monitoring."""
        logger.info(f"Starting periodic storage monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Update storage metrics
                self.get_model_storage_stats(use_cache=False)
                
                # Check storage health
                health = self.monitor_storage_health()
                if health["status"] != "healthy":
                    logger.warning(f"Storage health check: {health}")
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Periodic storage monitoring cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic storage monitoring: {e}")
                await asyncio.sleep(interval_seconds)
    
    def clear_cache(self):
        """Clear the monitoring cache."""
        self._cache.clear()
        logger.debug("Storage monitoring cache cleared")


# Global storage monitor instance
_storage_monitor: Optional[ModelStorageMonitor] = None


def get_model_storage_monitor(models_root: Path = None) -> ModelStorageMonitor:
    """Get the global model storage monitor instance."""
    global _storage_monitor
    if _storage_monitor is None:
        _storage_monitor = ModelStorageMonitor(models_root)
    return _storage_monitor