"""
Implementation plan for fixing LLM runtime caching issues affecting extension authentication.

This module provides the concrete implementation to resolve database connection pool
contention and query caching conflicts that cause HTTP 403 errors in extension APIs.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, AsyncGenerator
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """Service types for connection pool isolation"""
    EXTENSION = "extension"
    LLM = "llm"
    AUTHENTICATION = "authentication"
    USAGE_TRACKING = "usage_tracking"
    BACKGROUND_TASKS = "background_tasks"


class ServiceIsolatedDatabaseManager:
    """
    Database manager with service-specific connection pools to prevent
    LLM runtime caching from interfering with extension authentication.
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engines: Dict[ServiceType, Any] = {}
        self.session_factories: Dict[ServiceType, Any] = {}
        self.async_engines: Dict[ServiceType, Any] = {}
        self.async_session_factories: Dict[ServiceType, Any] = {}
        
        # Service-specific pool configurations
        self.pool_configs = {
            ServiceType.AUTHENTICATION: {
                "pool_size": 3,
                "max_overflow": 5,
                "pool_recycle": 900,  # 15 minutes - fastest recycle for auth
                "pool_pre_ping": True,
                "pool_timeout": 5,  # Fast timeout for auth
            },
            ServiceType.EXTENSION: {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 1800,  # 30 minutes
                "pool_pre_ping": True,
                "pool_timeout": 10,
            },
            ServiceType.LLM: {
                "pool_size": 8,
                "max_overflow": 15,
                "pool_recycle": 3600,  # 1 hour - can handle longer operations
                "pool_pre_ping": True,
                "pool_timeout": 30,  # Longer timeout for LLM operations
            },
            ServiceType.USAGE_TRACKING: {
                "pool_size": 2,
                "max_overflow": 4,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
                "pool_timeout": 15,
            },
            ServiceType.BACKGROUND_TASKS: {
                "pool_size": 3,
                "max_overflow": 6,
                "pool_recycle": 2400,  # 40 minutes
                "pool_pre_ping": True,
                "pool_timeout": 20,
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize all service-specific connection pools"""
        try:
            for service_type in ServiceType:
                await self._create_service_engines(service_type)
                await self._create_service_session_factories(service_type)
            
            # Test all connections
            for service_type in ServiceType:
                if not await self._test_service_connection(service_type):
                    logger.error(f"Failed to test {service_type.value} connection")
                    return False
            
            logger.info("Service-isolated database manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize service-isolated database manager: {e}")
            return False
    
    async def _create_service_engines(self, service_type: ServiceType):
        """Create engines for a specific service type"""
        config = self.pool_configs[service_type]
        
        # Create synchronous engine
        self.engines[service_type] = create_engine(
            self.database_url,
            poolclass=QueuePool,
            **config,
            echo=False,  # Disable echo to reduce noise
        )
        
        # Create async engine
        async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        self.async_engines[service_type] = create_async_engine(
            async_url,
            **config,
            echo=False,
        )
        
        logger.debug(f"Created engines for {service_type.value} service")
    
    async def _create_service_session_factories(self, service_type: ServiceType):
        """Create session factories for a specific service type"""
        # Sync session factory
        self.session_factories[service_type] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engines[service_type],
            # Disable query caching for authentication service
            query_cache_size=0 if service_type == ServiceType.AUTHENTICATION else 100
        )
        
        # Async session factory
        self.async_session_factories[service_type] = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.async_engines[service_type],
            class_=AsyncSession
        )
        
        logger.debug(f"Created session factories for {service_type.value} service")
    
    async def _test_service_connection(self, service_type: ServiceType) -> bool:
        """Test connection for a specific service"""
        try:
            # Test sync connection
            with self.get_session_scope(service_type) as session:
                session.execute(text("SELECT 1"))
            
            # Test async connection
            async with self.get_async_session_scope(service_type) as session:
                await session.execute(text("SELECT 1"))
            
            logger.debug(f"{service_type.value} service connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"{service_type.value} service connection test failed: {e}")
            return False
    
    @asynccontextmanager
    def get_session_scope(self, service_type: ServiceType):
        """Get session scope for specific service type"""
        if service_type not in self.session_factories:
            raise ValueError(f"Service type {service_type.value} not initialized")
        
        session = self.session_factories[service_type]()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error for {service_type.value}: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session_scope(self, service_type: ServiceType) -> AsyncGenerator[AsyncSession, None]:
        """Get async session scope for specific service type"""
        if service_type not in self.async_session_factories:
            raise ValueError(f"Service type {service_type.value} not initialized")
        
        async with self.async_session_factories[service_type]() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async session error for {service_type.value}: {e}")
                raise
    
    def get_pool_metrics(self, service_type: ServiceType) -> Dict[str, Any]:
        """Get connection pool metrics for a specific service"""
        if service_type not in self.engines:
            return {"error": f"Service {service_type.value} not initialized"}
        
        engine = self.engines[service_type]
        pool = engine.pool
        
        try:
            return {
                "service_type": service_type.value,
                "pool_size": getattr(pool, 'size', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "invalidated": getattr(pool, 'invalidated', lambda: 0)(),
                "pool_config": self.pool_configs[service_type]
            }
        except Exception as e:
            return {"error": f"Failed to get metrics for {service_type.value}: {e}"}
    
    def get_all_pool_metrics(self) -> Dict[str, Any]:
        """Get metrics for all service pools"""
        metrics = {}
        for service_type in ServiceType:
            metrics[service_type.value] = self.get_pool_metrics(service_type)
        return metrics
    
    async def health_check(self, service_type: ServiceType) -> Dict[str, Any]:
        """Perform health check for specific service"""
        try:
            start_time = datetime.utcnow()
            
            # Test connection
            async with self.get_async_session_scope(service_type) as session:
                await session.execute(text("SELECT 1"))
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "service_type": service_type.value,
                "healthy": True,
                "response_time_ms": response_time,
                "pool_metrics": self.get_pool_metrics(service_type),
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            return {
                "service_type": service_type.value,
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check for all services"""
        results = {}
        for service_type in ServiceType:
            results[service_type.value] = await self.health_check(service_type)
        
        # Calculate overall health
        healthy_services = sum(1 for result in results.values() if result.get("healthy", False))
        total_services = len(results)
        
        return {
            "overall_health": "healthy" if healthy_services == total_services else "degraded",
            "healthy_services": healthy_services,
            "total_services": total_services,
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Close all database connections"""
        for service_type in ServiceType:
            # Close async engines
            if service_type in self.async_engines:
                try:
                    await self.async_engines[service_type].dispose()
                except Exception as e:
                    logger.warning(f"Error disposing async engine for {service_type.value}: {e}")
            
            # Close sync engines
            if service_type in self.engines:
                try:
                    self.engines[service_type].dispose()
                except Exception as e:
                    logger.warning(f"Error disposing sync engine for {service_type.value}: {e}")
        
        logger.info("Service-isolated database manager closed")


class OptimizedUsageService:
    """
    Optimized usage service that batches updates to reduce database load
    and uses dedicated connection pool to prevent interference with extensions.
    """
    
    def __init__(self, db_manager: ServiceIsolatedDatabaseManager):
        self.db_manager = db_manager
        self.batch_buffer: Dict[str, int] = {}
        self.batch_size = 50
        self.flush_interval = 30  # seconds
        self.last_flush = datetime.utcnow()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_batch_processor(self):
        """Start the batch processing task"""
        self._running = True
        self._flush_task = asyncio.create_task(self._batch_flush_loop())
        logger.info("Usage service batch processor started")
    
    async def stop_batch_processor(self):
        """Stop the batch processing task"""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining batched data
        await self.flush_batch()
        logger.info("Usage service batch processor stopped")
    
    async def increment(self, metric: str, tenant_id: Optional[str] = None, 
                       user_id: Optional[str] = None, amount: int = 1):
        """Increment usage counter with batching to reduce database load"""
        try:
            # Create batch key
            key = f"{tenant_id or 'none'}:{user_id or 'none'}:{metric}"
            
            # Add to batch buffer
            self.batch_buffer[key] = self.batch_buffer.get(key, 0) + amount
            
            # Flush if batch is full
            if len(self.batch_buffer) >= self.batch_size:
                await self.flush_batch()
                
        except Exception as e:
            # Don't let usage tracking failures break the main request
            logger.warning(f"Usage tracking failed: {e}")
    
    async def flush_batch(self):
        """Flush batched usage increments to database"""
        if not self.batch_buffer:
            return
        
        try:
            # Use dedicated usage tracking connection pool
            async with self.db_manager.get_async_session_scope(ServiceType.USAGE_TRACKING) as session:
                current_batch = self.batch_buffer.copy()
                self.batch_buffer.clear()
                
                for key, total_increment in current_batch.items():
                    tenant_id, user_id, metric = key.split(':', 2)
                    tenant_id = None if tenant_id == 'none' else tenant_id
                    user_id = None if user_id == 'none' else user_id
                    
                    # Calculate current window
                    now = datetime.utcnow()
                    window_start = now.replace(minute=0, second=0, microsecond=0)
                    window_end = window_start + timedelta(hours=1)
                    
                    # Use upsert to handle concurrent updates
                    await session.execute(
                        text("""
                            INSERT INTO usage_counters (tenant_id, user_id, metric, value, window_start, window_end)
                            VALUES (:tenant_id, :user_id, :metric, :value, :window_start, :window_end)
                            ON CONFLICT (tenant_id, user_id, metric, window_start, window_end)
                            DO UPDATE SET value = usage_counters.value + EXCLUDED.value
                        """),
                        {
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "metric": metric,
                            "value": total_increment,
                            "window_start": window_start,
                            "window_end": window_end
                        }
                    )
                
                await session.commit()
                self.last_flush = datetime.utcnow()
                logger.debug(f"Flushed {len(current_batch)} usage counter updates")
                
        except Exception as e:
            logger.error(f"Failed to flush usage counter batch: {e}")
            # Don't re-add to buffer to avoid infinite loops
    
    async def _batch_flush_loop(self):
        """Background task to flush batches periodically"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                
                # Check if it's time to flush
                if (datetime.utcnow() - self.last_flush).total_seconds() >= self.flush_interval:
                    await self.flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch flush loop: {e}")


class ExtensionAuthenticationService:
    """
    Authentication service for extensions that uses dedicated connection pool
    and bypasses query caching to prevent stale authentication data.
    """
    
    def __init__(self, db_manager: ServiceIsolatedDatabaseManager):
        self.db_manager = db_manager
    
    async def authenticate_extension_request(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate extension request using dedicated auth connection pool.
        Bypasses all caching to ensure fresh authentication data.
        """
        try:
            # Use dedicated authentication connection pool
            async with self.db_manager.get_async_session_scope(ServiceType.AUTHENTICATION) as session:
                # Direct query with no caching
                result = await session.execute(
                    text("""
                        SELECT u.id, u.username, u.email, u.tenant_id, u.roles, u.permissions,
                               s.expires_at, s.created_at
                        FROM users u
                        JOIN auth_sessions s ON u.id = s.user_id
                        WHERE s.token = :token
                        AND s.expires_at > NOW()
                        AND u.active = true
                    """),
                    {"token": token}
                )
                
                row = result.fetchone()
                if not row:
                    return None
                
                return {
                    "user_id": row.id,
                    "username": row.username,
                    "email": row.email,
                    "tenant_id": row.tenant_id,
                    "roles": row.roles or [],
                    "permissions": row.permissions or [],
                    "session_expires_at": row.expires_at,
                    "session_created_at": row.created_at
                }
                
        except Exception as e:
            logger.error(f"Extension authentication failed: {e}")
            return None
    
    async def validate_extension_permission(self, user_context: Dict[str, Any], 
                                          permission: str) -> bool:
        """Validate if user has required extension permission"""
        try:
            user_permissions = user_context.get("permissions", [])
            user_roles = user_context.get("roles", [])
            
            # Admin users have all permissions
            if "admin" in user_roles or "*" in user_permissions:
                return True
            
            # Check specific permission
            extension_permissions = [
                f"extension:{permission}",
                f"extensions:{permission}",
                permission
            ]
            
            return any(perm in user_permissions for perm in extension_permissions)
            
        except Exception as e:
            logger.error(f"Permission validation failed: {e}")
            return False


# Global instance
_service_isolated_db_manager: Optional[ServiceIsolatedDatabaseManager] = None
_optimized_usage_service: Optional[OptimizedUsageService] = None
_extension_auth_service: Optional[ExtensionAuthenticationService] = None


async def initialize_service_isolated_database(database_url: str) -> bool:
    """Initialize the service-isolated database manager"""
    global _service_isolated_db_manager, _optimized_usage_service, _extension_auth_service
    
    try:
        # Initialize database manager
        _service_isolated_db_manager = ServiceIsolatedDatabaseManager(database_url)
        if not await _service_isolated_db_manager.initialize():
            return False
        
        # Initialize optimized usage service
        _optimized_usage_service = OptimizedUsageService(_service_isolated_db_manager)
        await _optimized_usage_service.start_batch_processor()
        
        # Initialize extension authentication service
        _extension_auth_service = ExtensionAuthenticationService(_service_isolated_db_manager)
        
        logger.info("Service-isolated database system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize service-isolated database: {e}")
        return False


def get_service_isolated_db_manager() -> Optional[ServiceIsolatedDatabaseManager]:
    """Get the global service-isolated database manager"""
    return _service_isolated_db_manager


def get_optimized_usage_service() -> Optional[OptimizedUsageService]:
    """Get the global optimized usage service"""
    return _optimized_usage_service


def get_extension_auth_service() -> Optional[ExtensionAuthenticationService]:
    """Get the global extension authentication service"""
    return _extension_auth_service


async def shutdown_service_isolated_database():
    """Shutdown the service-isolated database system"""
    global _service_isolated_db_manager, _optimized_usage_service, _extension_auth_service
    
    try:
        if _optimized_usage_service:
            await _optimized_usage_service.stop_batch_processor()
            _optimized_usage_service = None
        
        if _service_isolated_db_manager:
            await _service_isolated_db_manager.close()
            _service_isolated_db_manager = None
        
        _extension_auth_service = None
        
        logger.info("Service-isolated database system shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during service-isolated database shutdown: {e}")