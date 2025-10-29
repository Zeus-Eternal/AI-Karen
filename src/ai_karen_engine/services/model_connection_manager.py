"""
Model Connection Manager

Manages model connections with proper lifecycle management, connection pooling,
and automatic cleanup. Ensures that model switching maintains current reasoning flows
and preserves existing logic.

Requirements implemented: 7.3, 7.4, 8.4
"""

import asyncio
import logging
import time
import threading
import weakref
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Callable
from enum import Enum
from contextlib import asynccontextmanager
import gc

from ai_karen_engine.services.intelligent_model_router import (
    ModelConnection, ConnectionStatus, ModelRouter
)

logger = logging.getLogger("kari.model_connection_manager")

class ConnectionPoolStatus(Enum):
    """Connection pool status."""
    ACTIVE = "active"
    DRAINING = "draining"
    CLOSED = "closed"

@dataclass
class ConnectionPool:
    """Connection pool for a specific model."""
    model_id: str
    provider: str
    max_connections: int = 5
    active_connections: Set[ModelConnection] = field(default_factory=set)
    idle_connections: List[ModelConnection] = field(default_factory=list)
    status: ConnectionPoolStatus = ConnectionPoolStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    total_created: int = 0
    total_destroyed: int = 0

@dataclass
class ConnectionLease:
    """Represents a leased connection with automatic cleanup."""
    connection: ModelConnection
    pool: ConnectionPool
    lease_time: float = field(default_factory=time.time)
    auto_return: bool = True
    _returned: bool = False

class ModelConnectionManager:
    """
    Manages model connections with proper lifecycle management.
    
    Features:
    - Connection pooling for efficient resource usage
    - Automatic connection cleanup and lifecycle management
    - Graceful model switching without disrupting reasoning flows
    - Connection health monitoring and recovery
    - Memory management and garbage collection
    """
    
    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.active_leases: Set[ConnectionLease] = set()
        
        # Configuration
        self.max_idle_time = 300  # 5 minutes
        self.max_pool_size = 5
        self.connection_timeout = 30  # seconds
        self.cleanup_interval = 60  # 1 minute
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Reasoning flow preservation
        self.active_reasoning_sessions: Dict[str, Set[str]] = {}  # session_id -> model_ids
        self.reasoning_flow_callbacks: List[Callable] = []
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Model Connection Manager initialized")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                self._cleanup_task = loop.create_task(self._cleanup_loop())
                self._monitoring_task = loop.create_task(self._monitoring_loop())
        except RuntimeError:
            # No event loop running, tasks will be started when needed
            pass
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._cleanup_idle_connections()
                await self._cleanup_stale_pools()
                await self._cleanup_expired_leases()
                
                # Wait for next cleanup cycle
                await asyncio.wait_for(
                    self._shutdown_event.wait(), 
                    timeout=self.cleanup_interval
                )
            except asyncio.TimeoutError:
                continue  # Normal timeout, continue cleanup
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._monitor_connection_health()
                await self._update_pool_statistics()
                
                # Wait for next monitoring cycle
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=30  # Monitor every 30 seconds
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)
    
    async def get_connection(
        self, 
        model_id: str, 
        session_id: Optional[str] = None,
        preserve_reasoning: bool = True
    ) -> Optional[ConnectionLease]:
        """
        Get a connection to a model with proper lifecycle management.
        
        Args:
            model_id: ID of the model to connect to
            session_id: Optional session ID for reasoning flow preservation
            preserve_reasoning: Whether to preserve reasoning flows during switching
            
        Returns:
            ConnectionLease if successful, None otherwise
        """
        with self._lock:
            try:
                # Get or create connection pool
                pool = await self._get_or_create_pool(model_id)
                if not pool or pool.status != ConnectionPoolStatus.ACTIVE:
                    logger.error(f"Connection pool for {model_id} is not available")
                    return None
                
                # Try to get connection from pool
                connection = await self._get_pooled_connection(pool)
                if not connection:
                    logger.error(f"Failed to get connection for {model_id}")
                    return None
                
                # Create lease
                lease = ConnectionLease(
                    connection=connection,
                    pool=pool,
                    auto_return=True
                )
                
                self.active_leases.add(lease)
                pool.last_used = time.time()
                
                # Track reasoning session if provided
                if session_id and preserve_reasoning:
                    self._track_reasoning_session(session_id, model_id)
                
                logger.debug(f"Leased connection for {model_id}")
                return lease
                
            except Exception as e:
                logger.error(f"Failed to get connection for {model_id}: {e}")
                return None
    
    async def _get_or_create_pool(self, model_id: str) -> Optional[ConnectionPool]:
        """Get existing pool or create new one for model."""
        if model_id in self.connection_pools:
            return self.connection_pools[model_id]
        
        # Get model connection from router
        connection = await self.model_router.wire_model_connection(model_id)
        if not connection:
            return None
        
        # Create new pool
        pool = ConnectionPool(
            model_id=model_id,
            provider=connection.provider,
            max_connections=self.max_pool_size
        )
        
        self.connection_pools[model_id] = pool
        logger.info(f"Created connection pool for {model_id}")
        
        return pool
    
    async def _get_pooled_connection(self, pool: ConnectionPool) -> Optional[ModelConnection]:
        """Get a connection from the pool."""
        # Try to reuse idle connection
        if pool.idle_connections:
            connection = pool.idle_connections.pop(0)
            
            # Verify connection is still valid
            if await self._verify_connection_health(connection):
                pool.active_connections.add(connection)
                return connection
            else:
                # Connection is stale, destroy it
                await self._destroy_connection(connection, pool)
        
        # Create new connection if under limit
        if len(pool.active_connections) < pool.max_connections:
            connection = await self._create_new_connection(pool)
            if connection:
                pool.active_connections.add(connection)
                pool.total_created += 1
                return connection
        
        # Pool is at capacity
        logger.warning(f"Connection pool for {pool.model_id} is at capacity")
        return None
    
    async def _create_new_connection(self, pool: ConnectionPool) -> Optional[ModelConnection]:
        """Create a new connection for the pool."""
        try:
            connection = await self.model_router.wire_model_connection(pool.model_id)
            if connection and connection.status == ConnectionStatus.CONNECTED:
                logger.debug(f"Created new connection for {pool.model_id}")
                return connection
        except Exception as e:
            logger.error(f"Failed to create connection for {pool.model_id}: {e}")
        
        return None
    
    async def _verify_connection_health(self, connection: ModelConnection) -> bool:
        """Verify that a connection is still healthy."""
        try:
            # Check connection status
            if connection.status != ConnectionStatus.CONNECTED:
                return False
            
            # Check if connection is too old
            if connection.connection_time:
                age = time.time() - connection.connection_time
                if age > 3600:  # 1 hour max age
                    return False
            
            # Verify routing still works
            return await self.model_router.verify_model_routing(connection.model_id)
            
        except Exception as e:
            logger.error(f"Connection health check failed: {e}")
            return False
    
    async def return_connection(self, lease: ConnectionLease):
        """Return a connection to the pool."""
        if lease._returned:
            return  # Already returned
        
        with self._lock:
            try:
                lease._returned = True
                self.active_leases.discard(lease)
                
                pool = lease.pool
                connection = lease.connection
                
                # Remove from active connections
                pool.active_connections.discard(connection)
                
                # Check if connection is still healthy
                if await self._verify_connection_health(connection):
                    # Return to idle pool if there's space
                    if len(pool.idle_connections) < pool.max_connections // 2:
                        pool.idle_connections.append(connection)
                        logger.debug(f"Returned connection to idle pool for {pool.model_id}")
                    else:
                        # Pool is full, destroy connection
                        await self._destroy_connection(connection, pool)
                else:
                    # Connection is unhealthy, destroy it
                    await self._destroy_connection(connection, pool)
                
            except Exception as e:
                logger.error(f"Failed to return connection: {e}")
    
    async def _destroy_connection(self, connection: ModelConnection, pool: ConnectionPool):
        """Destroy a connection and clean up resources."""
        try:
            # Update connection status
            connection.status = ConnectionStatus.DISCONNECTED
            
            # Remove from all collections
            pool.active_connections.discard(connection)
            if connection in pool.idle_connections:
                pool.idle_connections.remove(connection)
            
            pool.total_destroyed += 1
            
            # Perform any provider-specific cleanup
            await self._cleanup_provider_connection(connection)
            
            logger.debug(f"Destroyed connection for {connection.model_id}")
            
        except Exception as e:
            logger.error(f"Failed to destroy connection: {e}")
    
    async def _cleanup_provider_connection(self, connection: ModelConnection):
        """Perform provider-specific connection cleanup."""
        try:
            # For local models, no special cleanup needed
            if connection.provider in ["local", "llamacpp"]:
                pass
            
            # For API providers, could implement connection cleanup
            else:
                pass
                
        except Exception as e:
            logger.error(f"Provider cleanup failed: {e}")
    
    @asynccontextmanager
    async def connection_context(
        self, 
        model_id: str, 
        session_id: Optional[str] = None,
        preserve_reasoning: bool = True
    ):
        """
        Context manager for automatic connection management.
        
        Usage:
            async with manager.connection_context("model_id") as connection:
                # Use connection
                pass
        """
        lease = await self.get_connection(model_id, session_id, preserve_reasoning)
        if not lease:
            raise RuntimeError(f"Failed to get connection for {model_id}")
        
        try:
            yield lease.connection
        finally:
            await self.return_connection(lease)
    
    async def switch_model(
        self,
        from_model_id: str,
        to_model_id: str,
        session_id: Optional[str] = None,
        preserve_reasoning: bool = True
    ) -> bool:
        """
        Switch from one model to another while preserving reasoning flows.
        
        Args:
            from_model_id: Current model ID
            to_model_id: Target model ID
            session_id: Session ID for reasoning preservation
            preserve_reasoning: Whether to preserve reasoning state
            
        Returns:
            True if switch was successful, False otherwise
        """
        try:
            logger.info(f"Switching from {from_model_id} to {to_model_id}")
            
            # Preserve reasoning flow if requested
            if preserve_reasoning and session_id:
                await self._preserve_reasoning_flow(session_id, from_model_id, to_model_id)
            
            # Get connection to new model
            new_lease = await self.get_connection(to_model_id, session_id, preserve_reasoning)
            if not new_lease:
                logger.error(f"Failed to get connection to {to_model_id}")
                return False
            
            # Verify new connection works
            if not await self._verify_connection_health(new_lease.connection):
                await self.return_connection(new_lease)
                logger.error(f"New connection to {to_model_id} is not healthy")
                return False
            
            # Update reasoning session tracking
            if session_id and preserve_reasoning:
                self._update_reasoning_session(session_id, from_model_id, to_model_id)
            
            # Return the new connection (it will be managed by the caller)
            await self.return_connection(new_lease)
            
            logger.info(f"Successfully switched to {to_model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Model switch failed: {e}")
            return False
    
    def _track_reasoning_session(self, session_id: str, model_id: str):
        """Track a reasoning session for flow preservation."""
        if session_id not in self.active_reasoning_sessions:
            self.active_reasoning_sessions[session_id] = set()
        
        self.active_reasoning_sessions[session_id].add(model_id)
        logger.debug(f"Tracking reasoning session {session_id} with model {model_id}")
    
    def _update_reasoning_session(self, session_id: str, old_model_id: str, new_model_id: str):
        """Update reasoning session tracking after model switch."""
        if session_id in self.active_reasoning_sessions:
            self.active_reasoning_sessions[session_id].discard(old_model_id)
            self.active_reasoning_sessions[session_id].add(new_model_id)
            logger.debug(f"Updated reasoning session {session_id}: {old_model_id} -> {new_model_id}")
    
    async def _preserve_reasoning_flow(self, session_id: str, from_model: str, to_model: str):
        """Preserve reasoning flow during model switch."""
        try:
            # Notify callbacks about model switch
            for callback in self.reasoning_flow_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(session_id, from_model, to_model)
                    else:
                        callback(session_id, from_model, to_model)
                except Exception as e:
                    logger.error(f"Reasoning flow callback failed: {e}")
            
            logger.debug(f"Preserved reasoning flow for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to preserve reasoning flow: {e}")
    
    def add_reasoning_flow_callback(self, callback: Callable):
        """Add a callback for reasoning flow preservation."""
        self.reasoning_flow_callbacks.append(callback)
        logger.debug("Added reasoning flow callback")
    
    async def _cleanup_idle_connections(self):
        """Clean up idle connections that have been unused for too long."""
        current_time = time.time()
        
        with self._lock:
            for pool in self.connection_pools.values():
                idle_to_remove = []
                
                for connection in pool.idle_connections:
                    if connection.last_used:
                        idle_time = current_time - connection.last_used
                        if idle_time > self.max_idle_time:
                            idle_to_remove.append(connection)
                
                # Remove and destroy idle connections
                for connection in idle_to_remove:
                    pool.idle_connections.remove(connection)
                    await self._destroy_connection(connection, pool)
                
                if idle_to_remove:
                    logger.debug(f"Cleaned up {len(idle_to_remove)} idle connections for {pool.model_id}")
    
    async def _cleanup_stale_pools(self):
        """Clean up connection pools that haven't been used recently."""
        current_time = time.time()
        stale_pools = []
        
        with self._lock:
            for model_id, pool in self.connection_pools.items():
                # Don't clean up pools with active reasoning sessions
                has_active_sessions = any(
                    model_id in models 
                    for models in self.active_reasoning_sessions.values()
                )
                
                if has_active_sessions:
                    continue
                
                # Check if pool is stale
                idle_time = current_time - pool.last_used
                if (idle_time > self.max_idle_time * 2 and 
                    not pool.active_connections and 
                    not pool.idle_connections):
                    stale_pools.append(model_id)
            
            # Remove stale pools
            for model_id in stale_pools:
                del self.connection_pools[model_id]
                logger.debug(f"Removed stale connection pool for {model_id}")
    
    async def _cleanup_expired_leases(self):
        """Clean up expired connection leases."""
        current_time = time.time()
        expired_leases = []
        
        with self._lock:
            for lease in self.active_leases:
                lease_age = current_time - lease.lease_time
                if lease_age > self.connection_timeout:
                    expired_leases.append(lease)
            
            # Return expired leases
            for lease in expired_leases:
                logger.warning(f"Returning expired lease for {lease.connection.model_id}")
                await self.return_connection(lease)
    
    async def _monitor_connection_health(self):
        """Monitor health of all active connections."""
        unhealthy_connections = []
        
        with self._lock:
            for pool in self.connection_pools.values():
                for connection in list(pool.active_connections):
                    if not await self._verify_connection_health(connection):
                        unhealthy_connections.append((connection, pool))
                
                for connection in list(pool.idle_connections):
                    if not await self._verify_connection_health(connection):
                        unhealthy_connections.append((connection, pool))
        
        # Clean up unhealthy connections
        for connection, pool in unhealthy_connections:
            await self._destroy_connection(connection, pool)
            logger.warning(f"Removed unhealthy connection for {connection.model_id}")
    
    async def _update_pool_statistics(self):
        """Update connection pool statistics."""
        with self._lock:
            for pool in self.connection_pools.values():
                # Update pool metrics
                pool.last_used = max(
                    pool.last_used,
                    max([c.last_used or 0 for c in pool.active_connections], default=0),
                    max([c.last_used or 0 for c in pool.idle_connections], default=0)
                )
    
    async def get_connection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics."""
        stats = {
            "total_pools": len(self.connection_pools),
            "active_leases": len(self.active_leases),
            "active_reasoning_sessions": len(self.active_reasoning_sessions),
            "pools": {},
            "memory_usage": {},
            "performance": {}
        }
        
        with self._lock:
            total_active = 0
            total_idle = 0
            
            for model_id, pool in self.connection_pools.items():
                active_count = len(pool.active_connections)
                idle_count = len(pool.idle_connections)
                
                total_active += active_count
                total_idle += idle_count
                
                stats["pools"][model_id] = {
                    "provider": pool.provider,
                    "status": pool.status.value,
                    "active_connections": active_count,
                    "idle_connections": idle_count,
                    "max_connections": pool.max_connections,
                    "total_created": pool.total_created,
                    "total_destroyed": pool.total_destroyed,
                    "created_at": pool.created_at,
                    "last_used": pool.last_used
                }
            
            stats["performance"] = {
                "total_active_connections": total_active,
                "total_idle_connections": total_idle,
                "connection_utilization": total_active / max(total_active + total_idle, 1),
                "average_pool_size": (total_active + total_idle) / max(len(self.connection_pools), 1)
            }
        
        # Memory usage statistics
        stats["memory_usage"] = {
            "connection_objects": len(self.connection_pools) + len(self.active_leases),
            "reasoning_sessions": len(self.active_reasoning_sessions),
            "callback_count": len(self.reasoning_flow_callbacks)
        }
        
        return stats
    
    async def drain_pool(self, model_id: str):
        """Drain a connection pool gracefully."""
        with self._lock:
            if model_id not in self.connection_pools:
                return
            
            pool = self.connection_pools[model_id]
            pool.status = ConnectionPoolStatus.DRAINING
            
            logger.info(f"Draining connection pool for {model_id}")
            
            # Close idle connections immediately
            idle_connections = list(pool.idle_connections)
            pool.idle_connections.clear()
            
            for connection in idle_connections:
                await self._destroy_connection(connection, pool)
            
            # Active connections will be closed when returned
            logger.info(f"Drained {len(idle_connections)} idle connections for {model_id}")
    
    async def close_pool(self, model_id: str):
        """Close a connection pool completely."""
        with self._lock:
            if model_id not in self.connection_pools:
                return
            
            pool = self.connection_pools[model_id]
            pool.status = ConnectionPoolStatus.CLOSED
            
            logger.info(f"Closing connection pool for {model_id}")
            
            # Close all connections
            all_connections = list(pool.active_connections) + list(pool.idle_connections)
            pool.active_connections.clear()
            pool.idle_connections.clear()
            
            for connection in all_connections:
                await self._destroy_connection(connection, pool)
            
            # Remove pool
            del self.connection_pools[model_id]
            
            logger.info(f"Closed connection pool for {model_id}")
    
    async def shutdown(self):
        """Shutdown the connection manager gracefully."""
        logger.info("Shutting down Model Connection Manager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for background tasks to complete
        if self._cleanup_task:
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._cleanup_task.cancel()
        
        if self._monitoring_task:
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
        
        # Close all pools
        pool_ids = list(self.connection_pools.keys())
        for model_id in pool_ids:
            await self.close_pool(model_id)
        
        # Clear reasoning sessions
        self.active_reasoning_sessions.clear()
        self.reasoning_flow_callbacks.clear()
        
        logger.info("Model Connection Manager shutdown complete")

# Global instance
_connection_manager: Optional[ModelConnectionManager] = None
_manager_lock = threading.RLock()

def get_connection_manager(model_router: Optional[ModelRouter] = None) -> ModelConnectionManager:
    """Get the global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        with _manager_lock:
            if _connection_manager is None:
                if model_router is None:
                    from ai_karen_engine.services.intelligent_model_router import get_model_router
                    model_router = get_model_router()
                _connection_manager = ModelConnectionManager(model_router)
    return _connection_manager