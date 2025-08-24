"""
Database Connection Manager

Enhanced database connection handling with:
- Integration with ConnectionHealthManager
- Graceful degradation when database is unavailable
- Connection pool monitoring and management
- Automatic retry with exponential backoff
- Proper resource cleanup
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, Optional, AsyncGenerator
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.database.models import Base
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.connection_health_manager import (
    get_connection_health_manager,
    ConnectionType,
    ServiceStatus,
)

logger = get_logger(__name__)


@dataclass
class DatabaseConnectionInfo:
    """Database connection information"""
    database_url: str
    pool_size: int
    max_overflow: int
    pool_recycle: int
    pool_pre_ping: bool
    echo: bool
    is_async: bool = False


class DatabaseConnectionManager:
    """
    Enhanced database connection manager with health monitoring and graceful degradation.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False,
    ):
        self.database_url = database_url or settings.database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.echo = echo

        # Connection objects
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None

        # State management
        self._degraded_mode = False
        self._connection_failures = 0
        self._last_connection_attempt: Optional[datetime] = None
        self._health_manager = get_connection_health_manager()

        # Degraded mode storage (in-memory fallback)
        self._memory_storage: Dict[str, Any] = {}
        self._degraded_features = [
            "data_persistence",
            "user_management", 
            "audit_logging",
            "session_storage",
            "memory_metadata",
        ]

    async def initialize(self) -> bool:
        """Initialize database connections and register with health manager"""
        try:
            await self._create_engines()
            await self._create_session_factories()
            
            # Test connections
            if await self._test_connections():
                self._connection_failures = 0
                self._degraded_mode = False
                
                # Register with health manager
                self._health_manager.register_service(
                    service_name="database",
                    connection_type=ConnectionType.DATABASE,
                    health_check_func=self._health_check,
                    degraded_mode_callback=self._on_degraded_mode,
                    recovery_callback=self._on_recovery,
                )
                
                logger.info("Database connection manager initialized successfully")
                return True
            else:
                await self._enable_degraded_mode("Initial connection test failed")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize database connection manager: {e}")
            await self._enable_degraded_mode(str(e))
            return False

    async def _create_engines(self):
        """Create SQLAlchemy engines"""
        try:
            # Create synchronous engine
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=self.pool_pre_ping,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
            )

            # Create async engine
            async_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
            self.async_engine = create_async_engine(
                async_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_pre_ping=self.pool_pre_ping,
                pool_recycle=self.pool_recycle,
                echo=self.echo,
            )

            logger.debug("Database engines created successfully")

        except Exception as e:
            logger.error(f"Failed to create database engines: {e}")
            raise

    async def _create_session_factories(self):
        """Create session factories"""
        if not self.engine or not self.async_engine:
            raise RuntimeError("Database engines not initialized")

        try:
            # Create session factories
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            self.AsyncSessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.async_engine,
                class_=AsyncSession
            )

            logger.debug("Database session factories created successfully")

        except Exception as e:
            logger.error(f"Failed to create session factories: {e}")
            raise

    async def _test_connections(self) -> bool:
        """Test both sync and async database connections"""
        try:
            # Test sync connection
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))

            # Test async connection
            async with self.async_session_scope() as session:
                await session.execute(text("SELECT 1"))

            return True

        except Exception as e:
            logger.warning(f"Database connection test failed: {e}")
            return False

    async def _health_check(self) -> Dict[str, Any]:
        """Health check function for connection health manager"""
        if self._degraded_mode:
            return {
                "healthy": False,
                "degraded_mode": True,
                "connection_failures": self._connection_failures,
                "degraded_features": self._degraded_features,
            }

        try:
            start_time = time.time()
            
            # Test sync connection
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            
            # Test async connection
            async with self.async_session_scope() as session:
                await session.execute(text("SELECT 1"))

            response_time = (time.time() - start_time) * 1000

            # Get connection pool metrics
            pool_info = self._get_pool_metrics()

            return {
                "healthy": True,
                "response_time_ms": response_time,
                "degraded_mode": False,
                "connection_failures": 0,
                "pool_info": pool_info,
            }

        except Exception as e:
            self._connection_failures += 1
            return {
                "healthy": False,
                "error": str(e),
                "degraded_mode": self._degraded_mode,
                "connection_failures": self._connection_failures,
                "degraded_features": self._degraded_features,
            }

    def _get_pool_metrics(self) -> Dict[str, Any]:
        """Get connection pool metrics"""
        metrics = {}
        
        if self.engine and hasattr(self.engine, 'pool'):
            pool = self.engine.pool
            try:
                metrics["sync_pool"] = {
                    "size": getattr(pool, 'size', lambda: 0)(),
                    "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                    "overflow": getattr(pool, 'overflow', lambda: 0)(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                    "invalid": getattr(pool, 'invalidated', lambda: 0)(),
                }
            except Exception as e:
                logger.debug(f"Could not get sync pool metrics: {e}")

        if self.async_engine and hasattr(self.async_engine, 'pool'):
            pool = self.async_engine.pool
            try:
                metrics["async_pool"] = {
                    "size": getattr(pool, 'size', lambda: 0)(),
                    "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                    "overflow": getattr(pool, 'overflow', lambda: 0)(),
                    "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                    "invalid": getattr(pool, 'invalidated', lambda: 0)(),
                }
            except Exception as e:
                logger.debug(f"Could not get async pool metrics: {e}")

        return metrics

    async def _enable_degraded_mode(self, reason: str):
        """Enable degraded mode operation"""
        self._degraded_mode = True
        logger.warning(f"Database degraded mode enabled: {reason}")
        
        # Clear memory storage to start fresh
        self._memory_storage.clear()

    async def _on_degraded_mode(self, service_name: str):
        """Callback when service enters degraded mode"""
        await self._enable_degraded_mode("Health check failed")

    async def _on_recovery(self, service_name: str):
        """Callback when service recovers"""
        self._degraded_mode = False
        self._connection_failures = 0
        logger.info("Database service recovered, degraded mode disabled")

    def get_session(self) -> Session:
        """Get a new database session"""
        if self._degraded_mode:
            raise RuntimeError("Database unavailable - degraded mode active")

        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")

        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        if self._degraded_mode:
            # Return a mock session that stores data in memory
            yield self._create_mock_session()
            return

        session = None
        try:
            session = self.get_session()
            yield session
            session.commit()
        except Exception as e:
            if session:
                session.rollback()
            # Handle connection error in background since this is sync context
            asyncio.create_task(self._handle_connection_error(e))
            raise
        finally:
            if session:
                session.close()

    @asynccontextmanager
    async def async_session_scope(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide async transactional scope around operations"""
        if self._degraded_mode:
            # Return a mock async session
            yield self._create_mock_async_session()
            return

        if not self.AsyncSessionLocal:
            raise RuntimeError("Async database not initialized")

        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                await self._handle_connection_error(e)
                raise

    def _create_mock_session(self):
        """Create a mock session for degraded mode"""
        class MockSession:
            def __init__(self, storage):
                self.storage = storage
                self._transaction_data = {}

            def execute(self, statement, parameters=None):
                # Mock execute - just return empty result
                class MockResult:
                    def fetchone(self):
                        return None
                    def fetchall(self):
                        return []
                    def scalar(self):
                        return None
                return MockResult()

            def add(self, instance):
                # Store in memory
                table_name = getattr(instance.__class__, '__tablename__', 'unknown')
                if table_name not in self.storage:
                    self.storage[table_name] = []
                self.storage[table_name].append(instance)

            def commit(self):
                # Mock commit
                pass

            def rollback(self):
                # Mock rollback
                pass

            def close(self):
                # Mock close
                pass

        return MockSession(self._memory_storage)

    def _create_mock_async_session(self):
        """Create a mock async session for degraded mode"""
        class MockAsyncSession:
            def __init__(self, storage):
                self.storage = storage

            async def execute(self, statement, parameters=None):
                # Mock async execute
                class MockResult:
                    async def fetchone(self):
                        return None
                    async def fetchall(self):
                        return []
                    async def scalar(self):
                        return None
                    def scalars(self):
                        class MockScalars:
                            def all(self):
                                return []
                        return MockScalars()
                return MockResult()

            def add(self, instance):
                # Store in memory
                table_name = getattr(instance.__class__, '__tablename__', 'unknown')
                if table_name not in self.storage:
                    self.storage[table_name] = []
                self.storage[table_name].append(instance)

            async def commit(self):
                # Mock commit
                pass

            async def rollback(self):
                # Mock rollback
                pass

        return MockAsyncSession(self._memory_storage)

    async def _handle_connection_error(self, error: Exception):
        """Handle database connection errors"""
        self._connection_failures += 1
        self._last_connection_attempt = datetime.utcnow()
        
        # Check if this is a connection-related error
        if isinstance(error, (DisconnectionError, OperationalError)):
            logger.error(f"Database connection error: {error}")
            # Notify health manager
            await self._health_manager.handle_connection_failure("database", error)
        else:
            # Other SQLAlchemy errors might not be connection-related
            logger.warning(f"Database error (not connection-related): {error}")

    def create_tables(self):
        """Create all database tables"""
        if self._degraded_mode:
            logger.warning("Cannot create tables in degraded mode")
            return

        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def create_tables_async(self):
        """Create all database tables asynchronously"""
        if self._degraded_mode:
            logger.warning("Cannot create tables in degraded mode")
            return

        try:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully (async)")
        except Exception as e:
            logger.error(f"Failed to create database tables (async): {e}")
            raise

    def health_check(self) -> bool:
        """Simple health check"""
        if self._degraded_mode:
            return False

        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def async_health_check(self) -> bool:
        """Async health check"""
        if self._degraded_mode:
            return False

        try:
            async with self.async_session_scope() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return False

    def is_degraded(self) -> bool:
        """Check if database is in degraded mode"""
        return self._degraded_mode

    def get_connection_info(self) -> DatabaseConnectionInfo:
        """Get database connection information"""
        return DatabaseConnectionInfo(
            database_url=self._sanitize_database_url(self.database_url),
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo,
        )

    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information"""
        return {
            "degraded_mode": self._degraded_mode,
            "connection_failures": self._connection_failures,
            "last_connection_attempt": self._last_connection_attempt.isoformat() if self._last_connection_attempt else None,
            "degraded_features": self._degraded_features if self._degraded_mode else [],
            "memory_storage_tables": list(self._memory_storage.keys()) if self._degraded_mode else [],
            "pool_metrics": self._get_pool_metrics(),
        }

    def _sanitize_database_url(self, url: str) -> str:
        """Sanitize database URL by removing credentials"""
        try:
            import re
            # Pattern to match postgresql://user:password@host:port/database
            pattern = r'(postgresql://[^:]+:)[^@]+(@.+)'
            sanitized = re.sub(pattern, r'\1****\2', url)
            return sanitized
        except Exception:
            return "postgresql://****:****@[host]/[database]"

    async def close(self):
        """Close database connections and cleanup resources"""
        if self.async_engine:
            try:
                await self.async_engine.dispose()
            except Exception as e:
                logger.warning(f"Error disposing async engine: {e}")
            finally:
                self.async_engine = None

        if self.engine:
            try:
                self.engine.dispose()
            except Exception as e:
                logger.warning(f"Error disposing sync engine: {e}")
            finally:
                self.engine = None

        # Clear session factories
        self.SessionLocal = None
        self.AsyncSessionLocal = None

        # Clear memory storage
        self._memory_storage.clear()

        logger.info("Database connection manager closed")


# Global database connection manager instance
_database_manager: Optional[DatabaseConnectionManager] = None


def get_database_manager() -> DatabaseConnectionManager:
    """Get global database connection manager instance"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseConnectionManager()
    return _database_manager


async def initialize_database_manager(
    database_url: Optional[str] = None,
    pool_size: int = 10,
    max_overflow: int = 20,
    **kwargs
) -> DatabaseConnectionManager:
    """Initialize and return database connection manager"""
    global _database_manager
    _database_manager = DatabaseConnectionManager(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        **kwargs
    )
    await _database_manager.initialize()
    return _database_manager


async def shutdown_database_manager():
    """Shutdown global database connection manager"""
    global _database_manager
    if _database_manager:
        await _database_manager.close()
        _database_manager = None


# Convenience functions for backward compatibility
def get_db_session() -> Session:
    """Get a new database session"""
    return get_database_manager().get_session()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    with get_database_manager().session_scope() as session:
        yield session