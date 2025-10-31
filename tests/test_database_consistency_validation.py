"""
Tests for Database Consistency Validation System

Basic tests to verify the database consistency validation functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_karen_engine.services.database_consistency_validator import (
    DatabaseConsistencyValidator,
    ValidationStatus,
    DatabaseType,
    ValidationIssue,
    DatabaseHealthStatus,
)
from ai_karen_engine.services.data_cleanup_service import (
    DataCleanupService,
    CleanupAction,
)
from ai_karen_engine.services.migration_validator import (
    MigrationValidator,
    MigrationStatus,
    SchemaValidationStatus,
)
from ai_karen_engine.services.database_health_checker import (
    DatabaseHealthChecker,
    OverallHealthStatus,
)


class TestDatabaseConsistencyValidator:
    """Test database consistency validator"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return DatabaseConsistencyValidator(
            data_directory="test_data",
            enable_auto_fix=False,
        )
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager"""
        mock = Mock()
        mock.is_degraded.return_value = False
        mock.async_session_scope = AsyncMock()
        return mock
    
    def test_validator_initialization(self, validator):
        """Test validator initializes correctly"""
        assert validator.data_directory.name == "test_data"
        assert validator.enable_auto_fix is False
        assert validator.validation_timeout == 300
        assert len(validator.demo_patterns["emails"]) > 0
    
    @pytest.mark.asyncio
    async def test_postgresql_health_check_success(self, validator):
        """Test successful PostgreSQL health check"""
        with patch.object(validator, 'db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.return_value.scalar.side_effect = [
                "PostgreSQL 13.0",  # version
                5,  # connection count
                0,  # blocked queries
            ]
            mock_db.async_session_scope.return_value.__aenter__.return_value = mock_session
            mock_db.is_degraded.return_value = False
            
            await validator._check_postgresql_health()
            
            assert len(validator._database_health) == 1
            health = validator._database_health[0]
            assert health.database == DatabaseType.POSTGRESQL
            assert health.is_connected is True
            assert health.status == ValidationStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_postgresql_health_check_failure(self, validator):
        """Test PostgreSQL health check failure"""
        with patch.object(validator, 'db_manager') as mock_db:
            mock_db.async_session_scope.side_effect = Exception("Connection failed")
            
            await validator._check_postgresql_health()
            
            assert len(validator._database_health) == 1
            health = validator._database_health[0]
            assert health.database == DatabaseType.POSTGRESQL
            assert health.is_connected is False
            assert health.status == ValidationStatus.CRITICAL
            assert "Connection failed" in health.error_message
    
    @pytest.mark.asyncio
    async def test_redis_health_check_success(self, validator):
        """Test successful Redis health check"""
        with patch.object(validator, 'redis_manager') as mock_redis:
            mock_redis.set = AsyncMock()
            mock_redis.get = AsyncMock(return_value="test")
            mock_redis.delete = AsyncMock()
            mock_redis.is_degraded.return_value = False
            mock_redis.get_connection_info.return_value = {
                "memory_cache_size": 10,
                "connection_failures": 0,
            }
            
            await validator._check_redis_health()
            
            assert len(validator._database_health) == 1
            health = validator._database_health[0]
            assert health.database == DatabaseType.REDIS
            assert health.is_connected is True
            assert health.status == ValidationStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_milvus_health_check_success(self, validator):
        """Test successful Milvus health check"""
        with patch.object(validator, 'milvus_client') as mock_milvus:
            mock_milvus.connect = AsyncMock()
            mock_milvus.health_check = AsyncMock(return_value={
                "status": "healthy",
                "records": "100",
            })
            
            await validator._check_milvus_health()
            
            assert len(validator._database_health) == 1
            health = validator._database_health[0]
            assert health.database == DatabaseType.MILVUS
            assert health.is_connected is True
            assert health.status == ValidationStatus.HEALTHY
    
    def test_validation_issue_creation(self):
        """Test validation issue creation"""
        issue = ValidationIssue(
            database=DatabaseType.POSTGRESQL,
            severity=ValidationStatus.WARNING,
            category="test_category",
            description="Test issue",
            recommendation="Fix the test issue",
            auto_fixable=True,
        )
        
        assert issue.database == DatabaseType.POSTGRESQL
        assert issue.severity == ValidationStatus.WARNING
        assert issue.category == "test_category"
        assert issue.description == "Test issue"
        assert issue.recommendation == "Fix the test issue"
        assert issue.auto_fixable is True
        assert isinstance(issue.timestamp, datetime)


class TestDataCleanupService:
    """Test data cleanup service"""
    
    @pytest.fixture
    def cleanup_service(self, tmp_path):
        """Create cleanup service instance for testing"""
        return DataCleanupService(
            data_directory=str(tmp_path / "data"),
            backup_directory=str(tmp_path / "backups"),
        )
    
    def test_cleanup_service_initialization(self, cleanup_service):
        """Test cleanup service initializes correctly"""
        assert cleanup_service.data_directory.name == "data"
        assert cleanup_service.backup_directory.name == "backups"
        assert len(cleanup_service.demo_patterns["demo_emails"]) > 0
    
    def test_cleanup_action_creation(self):
        """Test cleanup action creation"""
        action = CleanupAction(
            action_type="remove_demo_user",
            target="test@example.com",
            description="Removed demo user",
            size_bytes=1024,
            count=1,
        )
        
        assert action.action_type == "remove_demo_user"
        assert action.target == "test@example.com"
        assert action.description == "Removed demo user"
        assert action.size_bytes == 1024
        assert action.count == 1
        assert isinstance(action.timestamp, datetime)
    
    def test_get_cleanup_recommendations(self, cleanup_service, tmp_path):
        """Test getting cleanup recommendations"""
        # Create test users.json with demo users
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        users_file = data_dir / "users.json"
        
        users_data = {
            "admin@example.com": {"user_id": "dev_admin", "full_name": "Development Admin"},
            "user@production.com": {"user_id": "prod_user", "full_name": "Production User"},
        }
        
        import json
        with open(users_file, 'w') as f:
            json.dump(users_data, f)
        
        recommendations = cleanup_service.get_cleanup_recommendations()
        
        # Should recommend removing demo user
        assert any("demo users" in rec for rec in recommendations)


class TestMigrationValidator:
    """Test migration validator"""
    
    @pytest.fixture
    def migration_validator(self):
        """Create migration validator instance for testing"""
        return MigrationValidator(migrations_directory="test_migrations")
    
    def test_migration_validator_initialization(self, migration_validator):
        """Test migration validator initializes correctly"""
        assert migration_validator.migrations_directory.name == "test_migrations"
        assert len(migration_validator.expected_tables) > 0
        assert "auth_users" in migration_validator.expected_tables
        assert "conversations" in migration_validator.expected_tables
    
    @pytest.mark.asyncio
    async def test_get_current_migration_no_table(self, migration_validator):
        """Test getting current migration when alembic_version table doesn't exist"""
        with patch.object(migration_validator, 'db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.return_value.scalar.return_value = False  # Table doesn't exist
            mock_db.async_session_scope.return_value.__aenter__.return_value = mock_session
            
            result = await migration_validator._get_current_migration()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_current_migration_with_version(self, migration_validator):
        """Test getting current migration with version"""
        with patch.object(migration_validator, 'db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_session.execute.return_value.scalar.side_effect = [
                True,  # Table exists
                "abc123",  # Version
            ]
            mock_db.async_session_scope.return_value.__aenter__.return_value = mock_session
            
            result = await migration_validator._get_current_migration()
            
            assert result is not None
            assert result.version == "abc123"
            assert result.is_current is True


class TestDatabaseHealthChecker:
    """Test database health checker"""
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker instance for testing"""
        return DatabaseHealthChecker()
    
    def test_health_checker_initialization(self, health_checker):
        """Test health checker initializes correctly"""
        assert health_checker.db_manager is not None
        assert health_checker.redis_manager is not None
        assert health_checker.milvus_client is not None
        assert health_checker.consistency_validator is not None
        assert health_checker.migration_validator is not None
    
    def test_determine_overall_status_healthy(self, health_checker):
        """Test determining overall status when all systems are healthy"""
        db_connections = [
            DatabaseConnectionStatus(
                database=DatabaseType.POSTGRESQL,
                is_connected=True,
                response_time_ms=100,
                status=ValidationStatus.HEALTHY,
            ),
            DatabaseConnectionStatus(
                database=DatabaseType.REDIS,
                is_connected=True,
                response_time_ms=50,
                status=ValidationStatus.HEALTHY,
            ),
        ]
        
        status = health_checker._determine_overall_status(
            db_connections=db_connections,
            migration_status=MigrationStatus.UP_TO_DATE,
            critical_issues=0,
        )
        
        assert status == OverallHealthStatus.HEALTHY
    
    def test_determine_overall_status_offline(self, health_checker):
        """Test determining overall status when database is offline"""
        db_connections = [
            DatabaseConnectionStatus(
                database=DatabaseType.POSTGRESQL,
                is_connected=False,
                response_time_ms=0,
                status=ValidationStatus.CRITICAL,
                error_message="Connection failed",
            ),
        ]
        
        status = health_checker._determine_overall_status(
            db_connections=db_connections,
            migration_status=MigrationStatus.UP_TO_DATE,
            critical_issues=0,
        )
        
        assert status == OverallHealthStatus.OFFLINE
    
    def test_determine_overall_status_critical(self, health_checker):
        """Test determining overall status with critical issues"""
        db_connections = [
            DatabaseConnectionStatus(
                database=DatabaseType.POSTGRESQL,
                is_connected=True,
                response_time_ms=100,
                status=ValidationStatus.HEALTHY,
            ),
        ]
        
        status = health_checker._determine_overall_status(
            db_connections=db_connections,
            migration_status=MigrationStatus.UP_TO_DATE,
            critical_issues=1,
        )
        
        assert status == OverallHealthStatus.CRITICAL
    
    def test_generate_health_recommendations(self, health_checker):
        """Test generating health recommendations"""
        db_connections = [
            DatabaseConnectionStatus(
                database=DatabaseType.POSTGRESQL,
                is_connected=False,
                response_time_ms=0,
                status=ValidationStatus.CRITICAL,
                error_message="Connection failed",
            ),
            DatabaseConnectionStatus(
                database=DatabaseType.REDIS,
                is_connected=True,
                response_time_ms=1500,  # High response time
                status=ValidationStatus.WARNING,
                degraded_mode=True,
            ),
        ]
        
        recommendations = health_checker._generate_health_recommendations(
            db_connections=db_connections,
            migration_status=MigrationStatus.PENDING,
            critical_issues=1,
            warning_issues=2,
        )
        
        # Should have recommendations for offline DB, degraded mode, pending migrations, etc.
        assert len(recommendations) > 0
        assert any("postgresql" in rec.lower() for rec in recommendations)
        assert any("redis" in rec.lower() for rec in recommendations)
        assert any("migration" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_get_quick_status(self, health_checker):
        """Test getting quick status"""
        with patch.object(health_checker, 'db_manager') as mock_db, \
             patch.object(health_checker, 'redis_manager') as mock_redis, \
             patch.object(health_checker, 'milvus_client') as mock_milvus:
            
            mock_db.is_degraded.return_value = False
            mock_redis.is_degraded.return_value = False
            mock_milvus.connect = AsyncMock()
            
            status = await health_checker.get_quick_status()
            
            assert "timestamp" in status
            assert "overall_status" in status
            assert "databases" in status
            assert "uptime_seconds" in status
            assert status["databases"]["postgresql"] == "connected"
            assert status["databases"]["redis"] == "connected"
            assert status["databases"]["milvus"] == "connected"


# Integration test
@pytest.mark.asyncio
async def test_full_validation_workflow():
    """Test the full validation workflow"""
    # This would be a more comprehensive integration test
    # For now, just test that the main functions can be imported and called
    from ai_karen_engine.services.database_consistency_validator import validate_database_consistency
    from ai_karen_engine.services.data_cleanup_service import cleanup_demo_data
    from ai_karen_engine.services.migration_validator import validate_database_migrations
    from ai_karen_engine.services.database_health_checker import check_database_health
    
    # These functions exist and can be imported
    assert validate_database_consistency is not None
    assert cleanup_demo_data is not None
    assert validate_database_migrations is not None
    assert check_database_health is not None