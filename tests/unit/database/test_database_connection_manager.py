"""
Tests for Database Connection Manager

Tests enhanced database connection handling with health monitoring,
graceful degradation, connection pool management, and proper cleanup.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy.exc import DisconnectionError, OperationalError

from src.ai_karen_engine.services.database_connection_manager import (
    DatabaseConnectionManager,
    DatabaseConnectionInfo,
    get_database_manager,
    initialize_database_manager,
    shutdown_database_manager,
    get_db_session,
    get_db_session_context,
)


class TestDatabaseConnectionManager:
    """Test DatabaseConnectionManager functionality"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings"""
        with patch('src.ai_karen_engine.services.database_connection_manager.settings') as mock:
            mock.database_url = "postgresql://test:test@localhost:5432/test_db"
            yield mock

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy engine"""
        engine = MagicMock()
        engine.pool = MagicMock()
        engine.pool.size = MagicMock(return_value=10)
        engine.pool.checkedout = MagicMock(return_value=2)
        engine.pool.overflow = MagicMock(return_value=0)
        engine.pool.checkedin = MagicMock(return_value=8)
        engine.pool.invalidated = MagicMock(return_value=0)
        engine.dispose = MagicMock()
        return engine

    @pytest.fixture
    def mock_async_engine(self):
        """Mock async SQLAlchemy engine"""
        engine = AsyncMock()
        engine.pool = MagicMock()
        engine.pool.size = MagicMock(return_value=10)
        engine.pool.checkedout = MagicMock(return_value=1)
        engine.pool.overflow = MagicMock(return_value=0)
        engine.pool.checkedin = MagicMock(return_value=9)
        engine.pool.invalidated = MagicMock(return_value=0)
        engine.dispose = AsyncMock()
        engine.begin = asynccontextmanager(lambda: AsyncMock())
        return engine

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = MagicMock()
        session.execute = MagicMock()
        session.commit = MagicMock()
        session.rollback = MagicMock()
        session.close = MagicMock()
        return session

    @pytest.fixture
    def mock_async_session(self):
        """Mock async database session"""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def db_manager(self, mock_settings):
        """Create database manager for testing"""
        return DatabaseConnectionManager(
            database_url="postgresql://test:test@localhost:5432/test_db",
            pool_size=5,
            max_overflow=10,
        )

    @pytest.mark.asyncio
    async def test_initialization_success(self, db_manager, mock_engine, mock_async_engine):
        """Test successful database initialization"""
        with patch.object(db_manager, '_create_engines') as mock_create_engines, \
             patch.object(db_manager, '_create_session_factories') as mock_create_factories, \
             patch.object(db_manager, '_test_connections', return_value=True) as mock_test:
            
            db_manager.engine = mock_engine
            db_manager.async_engine = mock_async_engine

            result = await db_manager.initialize()

            assert result is True
            assert db_manager._degraded_mode is False
            assert db_manager._connection_failures == 0
            mock_create_engines.assert_called_once()
            mock_create_factories.assert_called_once()
            mock_test.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_failure(self, db_manager):
        """Test database initialization failure"""
        with patch.object(db_manager, '_create_engines', side_effect=Exception("Engine creation failed")):
            result = await db_manager.initialize()

            assert result is False
            assert db_manager._degraded_mode is True

    @pytest.mark.asyncio
    async def test_create_engines(self, db_manager):
        """Test engine creation"""
        with patch('src.ai_karen_engine.services.database_connection_manager.create_engine') as mock_create, \
             patch('src.ai_karen_engine.services.database_connection_manager.create_async_engine') as mock_create_async:
            
            mock_engine = MagicMock()
            mock_async_engine = MagicMock()
            mock_create.return_value = mock_engine
            mock_create_async.return_value = mock_async_engine

            await db_manager._create_engines()

            assert db_manager.engine == mock_engine
            assert db_manager.async_engine == mock_async_engine
            mock_create.assert_called_once()
            mock_create_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_factories(self, db_manager, mock_engine, mock_async_engine):
        """Test session factory creation"""
        db_manager.engine = mock_engine
        db_manager.async_engine = mock_async_engine

        with patch('src.ai_karen_engine.services.database_connection_manager.sessionmaker') as mock_sessionmaker, \
             patch('src.ai_karen_engine.services.database_connection_manager.async_sessionmaker') as mock_async_sessionmaker:
            
            mock_session_factory = MagicMock()
            mock_async_session_factory = MagicMock()
            mock_sessionmaker.return_value = mock_session_factory
            mock_async_sessionmaker.return_value = mock_async_session_factory

            await db_manager._create_session_factories()

            assert db_manager.SessionLocal == mock_session_factory
            assert db_manager.AsyncSessionLocal == mock_async_session_factory

    @pytest.mark.asyncio
    async def test_test_connections_success(self, db_manager, mock_session, mock_async_session):
        """Test successful connection testing"""
        with patch.object(db_manager, 'session_scope') as mock_sync_scope, \
             patch.object(db_manager, 'async_session_scope') as mock_async_scope:
            
            # Mock context managers
            mock_sync_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_sync_scope.return_value.__exit__ = MagicMock(return_value=None)
            
            mock_async_scope.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_scope.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_manager._test_connections()

            assert result is True
            mock_session.execute.assert_called_once()
            mock_async_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connections_failure(self, db_manager):
        """Test connection testing failure"""
        with patch.object(db_manager, 'session_scope', side_effect=Exception("Connection failed")):
            result = await db_manager._test_connections()
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager, mock_session, mock_async_session):
        """Test successful health check"""
        db_manager._degraded_mode = False

        with patch.object(db_manager, 'session_scope') as mock_sync_scope, \
             patch.object(db_manager, 'async_session_scope') as mock_async_scope, \
             patch.object(db_manager, '_get_pool_metrics', return_value={"sync_pool": {"size": 10}}) as mock_metrics:
            
            # Mock context managers
            mock_sync_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_sync_scope.return_value.__exit__ = MagicMock(return_value=None)
            
            mock_async_scope.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_async_scope.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_manager._health_check()

            assert result["healthy"] is True
            assert "response_time_ms" in result
            assert result["degraded_mode"] is False
            assert "pool_info" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_manager):
        """Test failed health check"""
        db_manager._degraded_mode = False

        with patch.object(db_manager, 'session_scope', side_effect=Exception("Health check failed")):
            result = await db_manager._health_check()

            assert result["healthy"] is False
            assert "error" in result
            assert db_manager._connection_failures > 0

    @pytest.mark.asyncio
    async def test_health_check_degraded_mode(self, db_manager):
        """Test health check in degraded mode"""
        db_manager._degraded_mode = True

        result = await db_manager._health_check()

        assert result["healthy"] is False
        assert result["degraded_mode"] is True
        assert result["degraded_features"] == db_manager._degraded_features

    def test_get_pool_metrics(self, db_manager, mock_engine, mock_async_engine):
        """Test connection pool metrics retrieval"""
        db_manager.engine = mock_engine
        db_manager.async_engine = mock_async_engine

        metrics = db_manager._get_pool_metrics()

        assert "sync_pool" in metrics
        assert "async_pool" in metrics
        assert metrics["sync_pool"]["size"] == 10
        assert metrics["sync_pool"]["checked_out"] == 2

    def test_get_pool_metrics_no_engines(self, db_manager):
        """Test pool metrics when engines are not available"""
        db_manager.engine = None
        db_manager.async_engine = None

        metrics = db_manager._get_pool_metrics()

        assert metrics == {}

    @pytest.mark.asyncio
    async def test_enable_degraded_mode(self, db_manager):
        """Test enabling degraded mode"""
        await db_manager._enable_degraded_mode("Test reason")

        assert db_manager._degraded_mode is True
        assert len(db_manager._memory_storage) == 0

    @pytest.mark.asyncio
    async def test_degraded_mode_callbacks(self, db_manager):
        """Test degraded mode callbacks"""
        # Test degraded mode callback
        await db_manager._on_degraded_mode("database")
        assert db_manager._degraded_mode is True

        # Test recovery callback
        await db_manager._on_recovery("database")
        assert db_manager._degraded_mode is False
        assert db_manager._connection_failures == 0

    def test_get_session_success(self, db_manager):
        """Test successful session retrieval"""
        mock_session_factory = MagicMock()
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        db_manager.SessionLocal = mock_session_factory
        db_manager._degraded_mode = False

        session = db_manager.get_session()

        assert session == mock_session
        mock_session_factory.assert_called_once()

    def test_get_session_degraded_mode(self, db_manager):
        """Test session retrieval in degraded mode"""
        db_manager._degraded_mode = True

        with pytest.raises(RuntimeError, match="Database unavailable"):
            db_manager.get_session()

    def test_get_session_not_initialized(self, db_manager):
        """Test session retrieval when not initialized"""
        db_manager.SessionLocal = None
        db_manager._degraded_mode = False

        with pytest.raises(RuntimeError, match="Database not initialized"):
            db_manager.get_session()

    def test_session_scope_success(self, db_manager, mock_session):
        """Test successful session scope"""
        mock_session_factory = MagicMock()
        mock_session_factory.return_value = mock_session
        db_manager.SessionLocal = mock_session_factory
        db_manager._degraded_mode = False

        with db_manager.session_scope() as session:
            assert session == mock_session
            session.execute("SELECT 1")

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_session_scope_with_exception(self, db_manager, mock_session):
        """Test session scope with exception"""
        mock_session_factory = MagicMock()
        mock_session_factory.return_value = mock_session
        db_manager.SessionLocal = mock_session_factory
        db_manager._degraded_mode = False

        with patch.object(db_manager, '_handle_connection_error') as mock_handle:
            with pytest.raises(Exception):
                with db_manager.session_scope() as session:
                    raise Exception("Test error")

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    def test_session_scope_degraded_mode(self, db_manager):
        """Test session scope in degraded mode"""
        db_manager._degraded_mode = True

        with db_manager.session_scope() as session:
            # Should return mock session
            assert hasattr(session, 'execute')
            assert hasattr(session, 'commit')

    @pytest.mark.asyncio
    async def test_async_session_scope_success(self, db_manager, mock_async_session):
        """Test successful async session scope"""
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        db_manager.AsyncSessionLocal = mock_session_factory
        db_manager._degraded_mode = False

        async with db_manager.async_session_scope() as session:
            assert session == mock_async_session
            await session.execute("SELECT 1")

        mock_async_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_session_scope_with_exception(self, db_manager, mock_async_session):
        """Test async session scope with exception"""
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        db_manager.AsyncSessionLocal = mock_session_factory
        db_manager._degraded_mode = False

        with patch.object(db_manager, '_handle_connection_error') as mock_handle:
            with pytest.raises(Exception):
                async with db_manager.async_session_scope() as session:
                    raise Exception("Test error")

            mock_async_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_session_scope_degraded_mode(self, db_manager):
        """Test async session scope in degraded mode"""
        db_manager._degraded_mode = True

        async with db_manager.async_session_scope() as session:
            # Should return mock async session
            assert hasattr(session, 'execute')
            assert hasattr(session, 'commit')

    def test_create_mock_session(self, db_manager):
        """Test mock session creation for degraded mode"""
        mock_session = db_manager._create_mock_session()

        # Test basic operations
        result = mock_session.execute("SELECT 1")
        assert result is not None

        # Test add operation
        mock_instance = MagicMock()
        mock_instance.__class__.__tablename__ = "test_table"
        mock_session.add(mock_instance)

        # Test commit and rollback
        mock_session.commit()
        mock_session.rollback()
        mock_session.close()

    def test_create_mock_async_session(self, db_manager):
        """Test mock async session creation for degraded mode"""
        mock_session = db_manager._create_mock_async_session()

        # Test basic operations
        result = asyncio.run(mock_session.execute("SELECT 1"))
        assert result is not None

        # Test add operation
        mock_instance = MagicMock()
        mock_instance.__class__.__tablename__ = "test_table"
        mock_session.add(mock_instance)

        # Test commit and rollback
        asyncio.run(mock_session.commit())
        asyncio.run(mock_session.rollback())

    @pytest.mark.asyncio
    async def test_handle_connection_error_disconnection(self, db_manager):
        """Test handling disconnection errors"""
        error = DisconnectionError("Connection lost")
        
        with patch.object(db_manager._health_manager, 'handle_connection_failure') as mock_handle:
            await db_manager._handle_connection_error(error)

            assert db_manager._connection_failures > 0
            assert db_manager._last_connection_attempt is not None
            mock_handle.assert_called_once_with("database", error)

    @pytest.mark.asyncio
    async def test_handle_connection_error_operational(self, db_manager):
        """Test handling operational errors"""
        error = OperationalError("statement", "params", "orig")
        
        with patch.object(db_manager._health_manager, 'handle_connection_failure') as mock_handle:
            await db_manager._handle_connection_error(error)

            mock_handle.assert_called_once_with("database", error)

    @pytest.mark.asyncio
    async def test_handle_connection_error_other(self, db_manager):
        """Test handling other SQLAlchemy errors"""
        error = Exception("Other error")
        
        with patch.object(db_manager._health_manager, 'handle_connection_failure') as mock_handle:
            await db_manager._handle_connection_error(error)

            # Should not call health manager for non-connection errors
            mock_handle.assert_not_called()

    def test_create_tables_success(self, db_manager, mock_engine):
        """Test successful table creation"""
        db_manager.engine = mock_engine
        db_manager._degraded_mode = False

        with patch('src.ai_karen_engine.services.database_connection_manager.Base') as mock_base:
            db_manager.create_tables()
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    def test_create_tables_degraded_mode(self, db_manager):
        """Test table creation in degraded mode"""
        db_manager._degraded_mode = True

        # Should not raise exception, just log warning
        db_manager.create_tables()

    @pytest.mark.asyncio
    async def test_create_tables_async_success(self, db_manager, mock_async_engine):
        """Test successful async table creation"""
        db_manager.async_engine = mock_async_engine
        db_manager._degraded_mode = False

        with patch('src.ai_karen_engine.services.database_connection_manager.Base') as mock_base:
            await db_manager.create_tables_async()
            # Verify async engine begin was called
            mock_async_engine.begin.assert_called_once()

    def test_health_check_simple_success(self, db_manager, mock_session):
        """Test simple health check success"""
        db_manager._degraded_mode = False

        with patch.object(db_manager, 'session_scope') as mock_scope:
            mock_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=None)

            result = db_manager.health_check()

            assert result is True
            mock_session.execute.assert_called_once()

    def test_health_check_simple_failure(self, db_manager):
        """Test simple health check failure"""
        db_manager._degraded_mode = False

        with patch.object(db_manager, 'session_scope', side_effect=Exception("Health check failed")):
            result = db_manager.health_check()
            assert result is False

    def test_health_check_simple_degraded_mode(self, db_manager):
        """Test simple health check in degraded mode"""
        db_manager._degraded_mode = True

        result = db_manager.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_async_health_check_success(self, db_manager, mock_async_session):
        """Test async health check success"""
        db_manager._degraded_mode = False

        with patch.object(db_manager, 'async_session_scope') as mock_scope:
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_async_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await db_manager.async_health_check()

            assert result is True
            mock_async_session.execute.assert_called_once()

    def test_is_degraded(self, db_manager):
        """Test degraded mode check"""
        assert db_manager.is_degraded() is False

        db_manager._degraded_mode = True
        assert db_manager.is_degraded() is True

    def test_get_connection_info(self, db_manager):
        """Test getting connection information"""
        info = db_manager.get_connection_info()

        assert isinstance(info, DatabaseConnectionInfo)
        assert "postgresql://test:****@localhost:5432/test_db" in info.database_url
        assert info.pool_size == db_manager.pool_size
        assert info.max_overflow == db_manager.max_overflow

    def test_get_status_info(self, db_manager, mock_engine):
        """Test getting status information"""
        db_manager.engine = mock_engine
        db_manager._connection_failures = 2
        db_manager._last_connection_attempt = datetime.utcnow()
        db_manager._memory_storage = {"table1": []}

        info = db_manager.get_status_info()

        assert info["degraded_mode"] == db_manager._degraded_mode
        assert info["connection_failures"] == 2
        assert "last_connection_attempt" in info
        assert "pool_metrics" in info

    def test_sanitize_database_url(self, db_manager):
        """Test database URL sanitization"""
        url = "postgresql://user:password@localhost:5432/database"
        sanitized = db_manager._sanitize_database_url(url)
        
        assert "password" not in sanitized
        assert "****" in sanitized

    @pytest.mark.asyncio
    async def test_close_cleanup(self, db_manager, mock_engine, mock_async_engine):
        """Test proper cleanup on close"""
        db_manager.engine = mock_engine
        db_manager.async_engine = mock_async_engine
        db_manager.SessionLocal = MagicMock()
        db_manager.AsyncSessionLocal = MagicMock()
        db_manager._memory_storage = {"key": "value"}

        await db_manager.close()

        mock_async_engine.dispose.assert_called_once()
        mock_engine.dispose.assert_called_once()
        assert db_manager.engine is None
        assert db_manager.async_engine is None
        assert db_manager.SessionLocal is None
        assert db_manager.AsyncSessionLocal is None
        assert len(db_manager._memory_storage) == 0

    @pytest.mark.asyncio
    async def test_close_with_errors(self, db_manager, mock_engine, mock_async_engine):
        """Test close with errors during cleanup"""
        mock_engine.dispose.side_effect = Exception("Dispose error")
        mock_async_engine.dispose.side_effect = Exception("Async dispose error")
        
        db_manager.engine = mock_engine
        db_manager.async_engine = mock_async_engine

        # Should not raise exception
        await db_manager.close()

        assert db_manager.engine is None
        assert db_manager.async_engine is None

    @pytest.mark.asyncio
    async def test_global_manager_functions(self, mock_settings):
        """Test global manager functions"""
        # Test initialization
        with patch('src.ai_karen_engine.services.database_connection_manager.DatabaseConnectionManager') as MockManager:
            mock_instance = AsyncMock()
            mock_instance.initialize = AsyncMock(return_value=True)
            MockManager.return_value = mock_instance

            manager = await initialize_database_manager(
                database_url="postgresql://test:test@localhost:5432/test",
                pool_size=5,
            )
            
            assert manager is not None
            mock_instance.initialize.assert_called_once()

        # Test getting global instance
        global_manager = get_database_manager()
        assert global_manager is not None

        # Test shutdown
        with patch.object(global_manager, 'close') as mock_close:
            await shutdown_database_manager()
            mock_close.assert_called_once()

    def test_convenience_functions(self, mock_settings):
        """Test convenience functions"""
        with patch('src.ai_karen_engine.services.database_connection_manager.get_database_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_session = MagicMock()
            mock_manager.get_session.return_value = mock_session
            mock_manager.session_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_manager.session_scope.return_value.__exit__ = MagicMock(return_value=None)
            mock_get_manager.return_value = mock_manager

            # Test get_db_session
            session = get_db_session()
            assert session == mock_session
            mock_manager.get_session.assert_called_once()

            # Test get_db_session_context
            with get_db_session_context() as session:
                assert session == mock_session