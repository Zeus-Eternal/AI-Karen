"""
Unified Zvec Orchestration Manager

Phase3: Production-ready orchestration of all Zvec systems.
- Integrates Sync Protocol
- Integrates Concurrency Manager  
- Integrates Offline Mode
- Provides unified API for frontend
- Handles errors & recovery

Architecture:
    ┌──────────────────────────────────────────────┐
    │  Unified Orchestration Manager (This File) │
    ├───────────────────────────────────────────────┤
    │  Frontend Layer (API)                  │
    │  ┌────────────────────────────────────────┐  │
    │  │ Unified API (single entry point)      │  │
    │  │ - sync()                           │  │
    │  │ - get_status()                      │  │
    │  │ - get_stats()                       │  │
    │  └──────────────┬───────────────────────┘  │
    │                 │                            │
    │  ┌──────────────▼───────────────────────┐  │
    │  │ Orchestration Layer                 │  │
    │  │ - Error handling                    │  │
    │  │ - Monitoring                       │  │
    │  │ - Logging                          │  │
    │  └───┬────────────┬────────┬──────┘  │
    │      │            │        │           │
    │  ┌───▼────┐  ┌───▼────┐ ┌───▼────┐│
    │  │   Sync  │  │ Offline │ │Currency││
    │  │ Manager │  │  Mode   │ │Manager  ││
    │  └─────────┘  └─────────┘ └─────────┘│
    └──────────────────────────────────────────────┘

Features:
1. Unified API: Single entry point for all Zvec operations
2. Error Recovery: Automatic retry with backoff
3. Monitoring: Comprehensive metrics & logging
4. Health Checks: System status & diagnostics
5. Frontend Integration: Easy-to-consume API
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

# Import Zvec components
try:
    from ai_karen_engine.core.memory.sync_protocol import (
        get_sync_manager,
        SyncDirection,
        ConflictResolution,
    )
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False

try:
    from ai_karen_engine.core.memory.concurrency_manager import (
        get_concurrency_manager,
    )
    CONCURRENCY_AVAILABLE = True
except ImportError:
    CONCURRENCY_AVAILABLE = False

try:
    from ai_karen_engine.core.memory.offline_mode import (
        get_offline_mode,
    )
    OFFLINE_AVAILABLE = True
except ImportError:
    OFFLINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ZvecOrchestrationManager:
    """
    Unified orchestration manager for all Zvec systems.
    
    Integrates:
    - Sync Protocol (Edge ↔ Server)
    - Concurrency Manager (Multi-user)
    - Offline Mode (Connectivity detection)
    
    Provides:
    - Unified API for frontend
    - Error handling & recovery
    - Monitoring & observability
    - Health checks & diagnostics
    """
    
    def __init__(
        self,
        zvec_base_path: str = "./zvec_data",
        sync_interval: int = 60,
        conflict_resolution: str = ConflictResolution.LAST_WRITE_WINS,
        enable_pooling: bool = True,
        max_queue_size: int = 1000,
    ):
        """
        Initialize orchestration manager.
        
        Args:
            zvec_base_path: Base path for user Zvec DBs
            sync_interval: Auto-sync interval (seconds)
            conflict_resolution: Conflict resolution strategy
            enable_pooling: Enable connection pooling
            max_queue_size: Maximum offline sync queue size
        """
        self.zvec_base_path = zvec_base_path
        self.sync_interval = sync_interval
        self.conflict_resolution = conflict_resolution
        
        # Initialize components
        self.sync_manager = None
        self.concurrency_manager = None
        self.offline_mode = None
        
        # State
        self._running = False
        self._initialized = False
        
        # Statistics (unified)
        self.stats = {
            "uptime": 0,
            "sync_count": 0,
            "conflicts": 0,
            "errors": 0,
            "active_users": 0,
            "offline_seconds": 0,
        }
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        logger.info("[Orchestration] Initialized Zvec orchestration manager")
    
    async def initialize(self) -> None:
        """Initialize all components."""
        if self._initialized:
            logger.warning("[Orchestration] Already initialized")
            return
        
        try:
            # 1. Concurrency Manager
            if CONCURRENCY_AVAILABLE:
                self.concurrency_manager = get_concurrency_manager(
                    base_path=self.zvec_base_path,
                    max_connections=10,
                    enable_pooling=True,
                )
                logger.info("[Orchestration] Concurrency manager initialized")
            
            # 2. Offline Mode
            if OFFLINE_AVAILABLE:
                self.offline_mode = get_offline_mode(
                    check_interval=30,
                    check_timeout=3,
                )
                logger.info("[Orchestration] Offline mode initialized")
            
            # 3. Sync Manager
            if SYNC_AVAILABLE and self.concurrency_manager:
                # Get Zvec client (for sync manager)
                # This would be created via concurrency manager
                zvec_client = None  # Will be fetched when needed
                
                self.sync_manager = get_sync_manager(
                    zvec_client=zvec_client,
                    conflict_resolution=self.conflict_resolution,
                    sync_interval=self.sync_interval,
                    max_queue_size=max_queue_size,
                )
                logger.info("[Orchestration] Sync manager initialized")
            
            self._initialized = True
            logger.info("[Orchestration] All components initialized")
        
        except Exception as ex:
            logger.error(f"[Orchestration] Initialization failed: {ex}")
            raise
    
    async def start(self) -> None:
        """Start all components."""
        if not self._initialized:
            await self.initialize()
        
        if self._running:
            logger.warning("[Orchestration] Already running")
            return
        
        self._running = True
        start_time = time.time()
        
        try:
            # Start offline mode monitoring
            if self.offline_mode:
                await self.offline_mode.start()
            
            # Start sync manager
            if self.sync_manager:
                await self.sync_manager.start()
            
            logger.info("[Orchestration] All components started")
        
        except Exception as ex:
            logger.error(f"[Orchestration] Start failed: {ex}")
            self.stats["errors"] += 1
    
    async def stop(self) -> None:
        """Stop all components."""
        if not self._running:
            return
        
        self._running = False
        
        try:
            # Stop sync manager
            if self.sync_manager:
                await self.sync_manager.stop()
            
            # Stop offline mode
            if self.offline_mode:
                await self.offline_mode.stop()
            
            # Close concurrency manager
            if self.concurrency_manager:
                await self.concurrency_manager.close()
            
            logger.info("[Orchestration] All components stopped")
        
        except Exception as ex:
            logger.error(f"[Orchestration] Stop failed: {ex}")
            self.stats["errors"] += 1
    
    async def sync(
        self,
        direction: Optional[str] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Trigger sync (with retry logic).
        
        Args:
            direction: Override sync direction
            force: Force sync even if offline
            
        Returns:
            Sync result with retry information
        """
        if not self.sync_manager:
            return {"status": "sync_not_available"}
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await self.sync_manager.sync(
                    direction=direction,
                    force=force,
                )
                
                if result.get("status") == "success":
                    # Update stats
                    self.stats["sync_count"] += 1
                    return result
                
                last_error = result.get("error")
            
            except Exception as ex:
                last_error = str(ex)
                logger.warning(
                    f"[Orchestration] Sync attempt {attempt + 1} failed: {ex}"
                )
                
                # Wait before retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        self.stats["errors"] += 1
        return {
            "status": "error",
            "error": last_error,
            "attempts": self.max_retries,
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get unified status for frontend.
        
        Returns:
            Comprehensive status dictionary
            {
                "running": bool,
                "initialized": bool,
                "offline": bool,
                "syncing": bool,
                "active_users": int,
                "queue_size": int,
                "last_sync": ISO timestamp,
                "capabilities": List[str],
                "stats": Dict[str, int],
            }
        """
        status = {
            "running": self._running,
            "initialized": self._initialized,
            "offline": False,
            "syncing": False,
            "active_users": 0,
            "queue_size": 0,
            "last_sync": None,
            "capabilities": [],
            "stats": self.get_stats(),
        }
        
        # Offline mode status
        if self.offline_mode:
            offline_status = self.offline_mode.get_status()
            status["offline"] = offline_status.get("is_offline", False)
            status["capabilities"] = offline_status.get("capabilities", [])
        
        # Sync manager status
        if self.sync_manager:
            sync_stats = self.sync_manager.get_stats()
            status["syncing"] = sync_stats.get("sync_in_progress", False)
            status["queue_size"] = sync_stats.get("queue_size", 0)
            status["last_sync"] = sync_stats.get("last_sync")
        
        # Concurrency manager status
        if self.concurrency_manager:
            concurrency_stats = self.concurrency_manager.get_stats()
            status["active_users"] = concurrency_stats.get("active_users", 0)
        
        return status
    
    def get_stats(self) -> Dict[str, int]:
        """Get unified statistics."""
        stats = dict(self.stats)
        
        # Add component stats
        if self.sync_manager:
            sync_stats = self.sync_manager.get_stats()
            stats["sync_count"] = sync_stats.get("sync_count", 0)
            stats["conflicts"] = sync_stats.get("conflicts", 0)
        
        if self.concurrency_manager:
            concurrency_stats = self.concurrency_manager.get_stats()
            stats["active_users"] = concurrency_stats.get("active_users", 0)
            stats["total_operations"] = concurrency_stats.get("total_operations", 0)
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "uptime": 0,
            "sync_count": 0,
            "conflicts": 0,
            "errors": 0,
            "active_users": 0,
            "offline_seconds": 0,
        }
        
        if self.sync_manager:
            self.sync_manager.reset_stats()
        
        if self.concurrency_manager:
            self.concurrency_manager.reset_stats()
        
        logger.info("[Orchestration] Statistics reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for all components.
        
        Returns:
            Health status dictionary
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "components": {
                    "sync": "healthy" | "unavailable",
                    "concurrency": "healthy" | "unavailable",
                    "offline_mode": "healthy" | "unavailable",
                },
                "checks": List of check results,
            }
        """
        health = {
            "status": "healthy",
            "components": {},
            "checks": [],
        }
        
        # Check sync manager
        if self.sync_manager:
            sync_health = await self._check_sync_health()
            health["components"]["sync"] = sync_health
            health["checks"].append({
                "component": "sync",
                "status": sync_health,
            })
        else:
            health["components"]["sync"] = "unavailable"
        
        # Check concurrency manager
        if self.concurrency_manager:
            concurrency_health = await self._check_concurrency_health()
            health["components"]["concurrency"] = concurrency_health
            health["checks"].append({
                "component": "concurrency",
                "status": concurrency_health,
            })
        else:
            health["components"]["concurrency"] = "unavailable"
        
        # Check offline mode
        if self.offline_mode:
            offline_health = await self._check_offline_health()
            health["components"]["offline_mode"] = offline_health
            health["checks"].append({
                "component": "offline_mode",
                "status": offline_health,
            })
        else:
            health["components"]["offline_mode"] = "unavailable"
        
        # Overall status
        component_statuses = [
            s for s in health["components"].values()
            if s != "unavailable"
        ]
        
        if "unhealthy" in component_statuses:
            health["status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health["status"] = "degraded"
        
        return health
    
    async def _check_sync_health(self) -> str:
        """Check sync manager health."""
        if not self.sync_manager:
            return "unavailable"
        
        try:
            stats = self.sync_manager.get_stats()
            errors = stats.get("errors", 0)
            last_sync = stats.get("last_sync")
            
            # Check if last sync was recent (within 10 minutes)
            if last_sync:
                time_since_sync = (time.time() - last_sync.timestamp()) / 60
                if time_since_sync > 10:
                    return "degraded"
            
            # Check error rate
            if errors > 10:
                return "degraded"
            
            return "healthy"
        
        except Exception as ex:
            logger.warning(f"[Orchestration] Sync health check failed: {ex}")
            return "unhealthy"
    
    async def _check_concurrency_health(self) -> str:
        """Check concurrency manager health."""
        if not self.concurrency_manager:
            return "unavailable"
        
        try:
            stats = self.concurrency_manager.get_stats()
            active_users = stats.get("active_users", 0)
            max_concurrent = stats.get("max_concurrent", 0)
            
            # Check if too many users
            if active_users > 100:
                return "degraded"
            
            # Check if too many concurrent operations
            if max_concurrent > 50:
                return "degraded"
            
            return "healthy"
        
        except Exception as ex:
            logger.warning(f"[Orchestration] Concurrency health check failed: {ex}")
            return "unhealthy"
    
    async def _check_offline_health(self) -> str:
        """Check offline mode health."""
        if not self.offline_mode:
            return "unavailable"
        
        try:
            status = self.offline_mode.get_status()
            
            # Check if last check was recent (within 5 minutes)
            if status.get("last_check"):
                time_since_check = (time.time() - status["last_check"].timestamp()) / 60
                if time_since_check > 5:
                    return "degraded"
            
            return "healthy"
        
        except Exception as ex:
            logger.warning(f"[Orchestration] Offline mode health check failed: {ex}")
            return "unhealthy"


# Singleton instance
_orchestration_manager: Optional[ZvecOrchestrationManager] = None


def get_orchestration_manager(
    zvec_base_path: str = "./zvec_data",
    sync_interval: int = 60,
    conflict_resolution: str = ConflictResolution.LAST_WRITE_WINS,
    enable_pooling: bool = True,
    max_queue_size: int = 1000,
) -> Optional[ZvecOrchestrationManager]:
    """
    Get or create global orchestration manager instance.
    
    Args:
        zvec_base_path: Base path for user Zvec DBs
        sync_interval: Auto-sync interval (seconds)
        conflict_resolution: Conflict resolution strategy
        enable_pooling: Enable connection pooling
        max_queue_size: Maximum offline sync queue size
        
    Returns:
        ZvecOrchestrationManager instance or None
    """
    global _orchestration_manager
    
    if _orchestration_manager is None:
        _orchestration_manager = ZvecOrchestrationManager(
            zvec_base_path=zvec_base_path,
            sync_interval=sync_interval,
            conflict_resolution=conflict_resolution,
            enable_pooling=enable_pooling,
            max_queue_size=max_queue_size,
        )
        logger.info("[Orchestration] Created global orchestration manager instance")
    
    return _orchestration_manager


__all__ = [
    "ZvecOrchestrationManager",
    "get_orchestration_manager",
]
