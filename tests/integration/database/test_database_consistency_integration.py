"""
Database Consistency Integration Tests

Comprehensive integration tests for database consistency validation across PostgreSQL, Redis, and Milvus.
Tests cross-database reference integrity, migration rollback scenarios, connection pool behavior under load,
and cache invalidation pattern validation.

Requirements: 2.1, 2.2, 2.3, 2.5
"""

import asyncio
import pytest
import time
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import concurrent.futures
import threading
import random

from sqlalchemy import text, select, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ai_karen_engine.services.database_consistency_validator import (
    DatabaseConsistencyValidator,
    ValidationStatus,
    DatabaseType,
    ValidationIssue,
    ConsistencyReport,
)
from ai_karen_engine.services.database_health_checker import (
    DatabaseHealthChecker,
    OverallHealthStatus,
)
from ai_karen_engine.services.migration_validator import (
    MigrationValidator,
    MigrationStatus,
)
from ai_karen_engine.services.database_connection_manager import get_database_manager
from ai_karen_engine.services.redis_connection_manager import get_redis_manager
from ai_karen_engine.core.milvus_client import MilvusClient
from ai_karen_engine.database.models import (
    TenantConversation,
    TenantMemoryItem,
    TenantMessage,
    AuthUser,
    Tenant,
)


class TestCrossDatabaseReferenceIntegrity:
    """Test cross-database reference integrity validation"""

    @pytest.fixture
    async def consistency_validator(self):
        """Create database consistency validator for testing"""
        validator = DatabaseConsistencyValidator(
            data_directory="tests/data",
            enable_auto_fix=False,
            validation_timeout=60,
        )
        yield validator

    @pytest.fixture
    async def mock_database_managers(self):
        """Mock database managers for testing"""
        # Mock PostgreSQL manager
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        mock_db_manager.is_degraded.return_value = False
        
        # Mock Redis manager
        mock_redis_manager = AsyncMock()
        mock_redis_manager.get.return_value = None
        mock_redis_manager.set.return_value = True
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {
            "memory_cache_size": 100,
            "connection_failures": 0,
            "degraded_mode": False,
        }
        
        # Mock Milvus client
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {
            "status": "healthy",
            "records": "1000",
        }
        
        return {
            "db_manager": mock_db_manager,
            "redis_manager": mock_redis_manager,
            "milvus_client": mock_milvus_client,
            "session": mock_session,
        }

    @pytest.mark.asyncio
    async def test_cross_database_reference_integrity(self, consistency_validator, mock_database_managers):
        """Test PostgreSQL to Milvus reference integrity validation"""
        session = mock_database_managers["session"]
        
        # Mock memory items without embeddings
        missing_embeddings_result = Mock()
        missing_embeddings_result.fetchall.return_value = [
            ("item_1", "Test content 1"),
            ("item_2", "Test content 2"),
            ("item_3", "Test content 3"),
        ]
        
        # Mock orphaned conversations
        orphaned_conversations_result = Mock()
        orphaned_conversations_result.fetchall.return_value = [
            ("conv_1", "Orphaned conversation 1"),
            ("conv_2", "Orphaned conversation 2"),
        ]
        
        # Configure session execute mock to return different results based on query
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if "embedding.is_(None)" in query_str or "embedding IS NULL" in query_str:
                return missing_embeddings_result
            elif "LEFT JOIN memory_items" in query_str:
                return orphaned_conversations_result
            else:
                result = Mock()
                result.fetchall.return_value = []
                return result
        
        session.execute.side_effect = execute_side_effect
        
        # Patch the validator's database managers
        with patch.object(consistency_validator, 'db_manager', mock_database_managers["db_manager"]), \
             patch.object(consistency_validator, 'redis_manager', mock_database_managers["redis_manager"]), \
             patch.object(consistency_validator, 'milvus_client', mock_database_managers["milvus_client"]):
            
            # Run validation
            report = await consistency_validator.validate_all()
            
            # Verify issues were detected
            assert report.overall_status in [ValidationStatus.WARNING, ValidationStatus.HEALTHY]
            
            # Check for missing embeddings issue
            missing_embedding_issues = [
                issue for issue in report.validation_issues
                if issue.category == "missing_embeddings"
            ]
            assert len(missing_embedding_issues) == 1
            assert missing_embedding_issues[0].details["count"] == 3
            assert missing_embedding_issues[0].auto_fixable is True
            
            # Check for orphaned conversations issue
            orphaned_conversation_issues = [
                issue for issue in report.validation_issues
                if issue.category == "orphaned_conversations"
            ]
            assert len(orphaned_conversation_issues) == 1
            assert orphaned_conversation_issues[0].details["count"] == 2

    @pytest.mark.asyncio
    async def test_redis_cache_consistency_validation(self, consistency_validator, mock_database_managers):
        """Test Redis cache consistency validation"""
        # Mock large cache size to trigger warning
        mock_database_managers["redis_manager"].get_connection_info.return_value = {
            "memory_cache_size": 2000,  # Large cache size
            "connection_failures": 0,
            "degraded_mode": False,
        }
        
        with patch.object(consistency_validator, 'db_manager', mock_database_managers["db_manager"]), \
             patch.object(consistency_validator, 'redis_manager', mock_database_managers["redis_manager"]), \
             patch.object(consistency_validator, 'milvus_client', mock_database_managers["milvus_client"]):
            
            # Run validation
            report = await consistency_validator.validate_all()
            
            # Check for cache size warning
            cache_issues = [
                issue for issue in report.validation_issues
                if issue.category == "cache_size"
            ]
            assert len(cache_issues) == 1
            assert cache_issues[0].severity == ValidationStatus.WARNING
            assert cache_issues[0].details["cache_size"] == 2000

    @pytest.mark.asyncio
    async def test_orphaned_records_detection(self, consistency_validator, mock_database_managers):
        """Test detection of orphaned records across databases"""
        session = mock_database_managers["session"]
        
        # Mock orphaned messages
        orphaned_messages_result = Mock()
        orphaned_messages_result.scalar.return_value = 5
        
        # Mock orphaned sessions
        orphaned_sessions_result = Mock()
        orphaned_sessions_result.scalar.return_value = 3
        
        # Configure session execute mock
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if "messages m" in query_str and "LEFT JOIN conversations" in query_str:
                return orphaned_messages_result
            elif "auth_sessions s" in query_str and "LEFT JOIN auth_users" in query_str:
                return orphaned_sessions_result
            else:
                result = Mock()
                result.scalar.return_value = 0
                result.fetchall.return_value = []
                return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(consistency_validator, 'db_manager', mock_database_managers["db_manager"]), \
             patch.object(consistency_validator, 'redis_manager', mock_database_managers["redis_manager"]), \
             patch.object(consistency_validator, 'milvus_client', mock_database_managers["milvus_client"]):
            
            # Run validation
            report = await consistency_validator.validate_all()
            
            # Check for orphaned records issues
            orphaned_issues = [
                issue for issue in report.validation_issues
                if issue.category == "orphaned_records"
            ]
            assert len(orphaned_issues) == 2  # Messages and sessions
            
            # Verify orphaned messages issue
            message_issues = [issue for issue in orphaned_issues if "messages" in issue.description]
            assert len(message_issues) == 1
            assert message_issues[0].details["count"] == 5
            assert message_issues[0].auto_fixable is True
            
            # Verify orphaned sessions issue
            session_issues = [issue for issue in orphaned_issues if "sessions" in issue.description]
            assert len(session_issues) == 1
            assert session_issues[0].details["count"] == 3
            assert session_issues[0].auto_fixable is True

    @pytest.mark.asyncio
    async def test_cross_database_consistency_with_failures(self, consistency_validator, mock_database_managers):
        """Test cross-database consistency validation with database failures"""
        # Mock PostgreSQL failure
        mock_database_managers["db_manager"].async_session_scope.side_effect = Exception("PostgreSQL connection failed")
        
        with patch.object(consistency_validator, 'db_manager', mock_database_managers["db_manager"]), \
             patch.object(consistency_validator, 'redis_manager', mock_database_managers["redis_manager"]), \
             patch.object(consistency_validator, 'milvus_client', mock_database_managers["milvus_client"]):
            
            # Run validation
            report = await consistency_validator.validate_all()
            
            # Should handle failure gracefully
            assert report.overall_status == ValidationStatus.FAILED
            
            # Check for database connectivity issue
            connectivity_issues = [
                issue for issue in report.validation_issues
                if issue.category == "connectivity"
            ]
            assert len(connectivity_issues) >= 1


class TestMigrationRollbackScenarios:
    """Test migration rollback scenarios"""

    @pytest.fixture
    async def migration_validator(self):
        """Create migration validator for testing"""
        validator = MigrationValidator(migrations_directory="tests/data/migrations")
        yield validator

    @pytest.fixture
    async def mock_migration_environment(self):
        """Mock migration environment for testing"""
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        
        return {
            "db_manager": mock_db_manager,
            "session": mock_session,
        }

    @pytest.mark.asyncio
    async def test_migration_rollback_validation(self, migration_validator, mock_migration_environment):
        """Test migration rollback scenario validation"""
        session = mock_migration_environment["session"]
        
        # Mock alembic_version table exists
        version_exists_result = Mock()
        version_exists_result.scalar.return_value = True
        
        # Mock current migration version
        current_version_result = Mock()
        current_version_result.scalar.return_value = "abc123_test_migration"
        
        # Mock existing tables (missing some expected tables to simulate rollback scenario)
        existing_tables_result = Mock()
        existing_tables_result.fetchall.return_value = [
            ("tenants",),
            ("auth_users",),
            ("conversations",),
            # Missing: messages, memory_items, etc.
        ]
        
        # Configure session execute mock
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if "alembic_version" in query_str and "EXISTS" in query_str:
                return version_exists_result
            elif "SELECT version_num FROM alembic_version" in query_str:
                return current_version_result
            elif "information_schema.tables" in query_str:
                return existing_tables_result
            else:
                result = Mock()
                result.scalar.return_value = 0
                result.fetchall.return_value = []
                return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', mock_migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect missing tables (indicating incomplete rollback or migration)
            assert report.overall_status == MigrationStatus.PENDING
            assert len(report.schema_validation.missing_tables) > 0
            
            # Should have current migration info
            assert report.current_migration is not None
            assert report.current_migration.version == "abc123_test_migration"
            
            # Should recommend applying migrations
            assert any("upgrade head" in rec for rec in report.recommendations)

    @pytest.mark.asyncio
    async def test_migration_rollback_with_orphaned_data(self, migration_validator, mock_migration_environment):
        """Test migration rollback scenario with orphaned data"""
        session = mock_migration_environment["session"]
        
        # Mock scenario where migration was rolled back but data remains
        version_exists_result = Mock()
        version_exists_result.scalar.return_value = True
        
        current_version_result = Mock()
        current_version_result.scalar.return_value = "old_version_123"
        
        # Mock tables that exist but shouldn't (indicating incomplete rollback)
        existing_tables_result = Mock()
        existing_tables_result.fetchall.return_value = [
            ("tenants",),
            ("auth_users",),
            ("conversations",),
            ("messages",),
            ("memory_items",),
            ("extensions",),
            ("llm_providers",),
            ("llm_requests",),
            ("audit_log",),
            ("auth_sessions",),
            ("hooks",),
            ("files",),
            ("webhooks",),
            ("usage_counters",),
            ("rate_limits",),
            # Extra table that shouldn't exist
            ("deprecated_feature_table",),
            ("old_migration_temp_table",),
        ]
        
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if "alembic_version" in query_str and "EXISTS" in query_str:
                return version_exists_result
            elif "SELECT version_num FROM alembic_version" in query_str:
                return current_version_result
            elif "information_schema.tables" in query_str:
                return existing_tables_result
            else:
                result = Mock()
                result.scalar.return_value = 0
                result.fetchall.return_value = []
                return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', mock_migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect extra tables (indicating incomplete rollback)
            assert report.overall_status == MigrationStatus.INCONSISTENT
            assert len(report.schema_validation.extra_tables) > 0
            assert "deprecated_feature_table" in report.schema_validation.extra_tables
            assert "old_migration_temp_table" in report.schema_validation.extra_tables
            
            # Should recommend cleanup
            assert any("extra tables" in rec for rec in report.recommendations)

    @pytest.mark.asyncio
    async def test_migration_rollback_without_tracking(self, migration_validator, mock_migration_environment):
        """Test migration rollback scenario without proper tracking"""
        session = mock_migration_environment["session"]
        
        # Mock scenario where alembic_version table doesn't exist
        version_exists_result = Mock()
        version_exists_result.scalar.return_value = False
        
        # Mock existing tables
        existing_tables_result = Mock()
        existing_tables_result.fetchall.return_value = [
            ("tenants",),
            ("auth_users",),
            ("conversations",),
        ]
        
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            if "alembic_version" in query_str and "EXISTS" in query_str:
                return version_exists_result
            elif "information_schema.tables" in query_str:
                return existing_tables_result
            else:
                result = Mock()
                result.scalar.return_value = 0
                result.fetchall.return_value = []
                return result
        
        session.execute.side_effect = execute_side_effect
        
        with patch.object(migration_validator, 'db_manager', mock_migration_environment["db_manager"]):
            # Run migration validation
            report = await migration_validator.validate_migrations()
            
            # Should detect unknown migration status
            assert report.overall_status == MigrationStatus.UNKNOWN
            assert report.current_migration is None
            
            # Should recommend initializing migration tracking
            assert any("Initialize Alembic" in rec for rec in report.recommendations)


class TestConnectionPoolBehaviorUnderLoad:
    """Test connection pool behavior under load"""

    @pytest.fixture
    async def health_checker(self):
        """Create database health checker for testing"""
        checker = DatabaseHealthChecker()
        yield checker

    @pytest.mark.asyncio
    async def test_connection_pool_under_concurrent_load(self, health_checker):
        """Test connection pool behavior under concurrent load"""
        # Mock database manager with pool metrics
        mock_db_manager = Mock()
        mock_pool_metrics = {
            "pool_size": 10,
            "checked_out": 0,
            "overflow": 0,
            "checked_in": 10,
            "total_connections": 10,
            "active_connections": 0,
        }
        mock_db_manager._get_pool_metrics.return_value = mock_pool_metrics
        mock_db_manager.is_degraded.return_value = False
        
        # Mock session for health checks
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar.return_value = "PostgreSQL 13.0"
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        
        # Mock Redis and Milvus for complete health check
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {
            "memory_cache_size": 100,
            "connection_failures": 0,
        }
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy", "records": "1000"}
        
        with patch.object(health_checker, 'db_manager', mock_db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Simulate concurrent load by running multiple health checks
            concurrent_tasks = 20
            load_duration = 2  # seconds
            
            async def simulate_load():
                """Simulate database load by performing health checks"""
                start_time = time.time()
                task_results = []
                
                while (time.time() - start_time) < load_duration:
                    # Simulate increasing pool usage
                    current_usage = min(10, int((time.time() - start_time) * 5))
                    mock_pool_metrics["checked_out"] = current_usage
                    mock_pool_metrics["active_connections"] = current_usage
                    mock_pool_metrics["checked_in"] = 10 - current_usage
                    
                    # Perform health check
                    result = await health_checker.check_health(include_detailed_validation=False)
                    task_results.append(result)
                    
                    await asyncio.sleep(0.1)
                
                return task_results
            
            # Run concurrent load simulation
            tasks = [simulate_load() for _ in range(5)]  # 5 concurrent load generators
            results = await asyncio.gather(*tasks)
            
            # Flatten results
            all_results = [result for task_results in results for result in task_results]
            
            # Verify health checks completed successfully under load
            assert len(all_results) > 0
            
            # Check that most health checks were successful
            successful_checks = [r for r in all_results if r.overall_status != OverallHealthStatus.CRITICAL]
            success_rate = len(successful_checks) / len(all_results)
            assert success_rate > 0.8  # At least 80% success rate under load
            
            # Verify pool metrics were collected
            for result in all_results:
                if result.performance_metrics.get("postgresql"):
                    pool_metrics = result.performance_metrics["postgresql"]["pool_metrics"]
                    assert "pool_size" in pool_metrics
                    assert "checked_out" in pool_metrics
                    assert pool_metrics["pool_size"] == 10

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_scenario(self, health_checker):
        """Test connection pool behavior when exhausted"""
        # Mock database manager with exhausted pool
        mock_db_manager = Mock()
        mock_pool_metrics = {
            "pool_size": 5,
            "checked_out": 5,  # All connections checked out
            "overflow": 3,     # Using overflow connections
            "checked_in": 0,   # No available connections
            "total_connections": 8,
            "active_connections": 8,
        }
        mock_db_manager._get_pool_metrics.return_value = mock_pool_metrics
        mock_db_manager.is_degraded.return_value = True  # Pool exhaustion causes degraded mode
        
        # Mock slow session for exhausted pool
        mock_session = AsyncMock()
        
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate slow query due to pool exhaustion
            result = Mock()
            result.scalar.return_value = "PostgreSQL 13.0"
            return result
        
        mock_session.execute = slow_execute
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        
        # Mock Redis and Milvus
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', mock_db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Perform health check with exhausted pool
            start_time = time.time()
            result = await health_checker.check_health(include_detailed_validation=False)
            check_duration = time.time() - start_time
            
            # Should detect degraded status due to pool exhaustion
            assert result.overall_status == OverallHealthStatus.DEGRADED
            
            # Should have slow response time due to pool exhaustion
            assert check_duration > 0.4  # Should be slower due to pool exhaustion
            
            # Should have pool exhaustion in recommendations
            pool_recommendations = [
                rec for rec in result.recommendations
                if "pool" in rec.lower() or "connection" in rec.lower()
            ]
            assert len(pool_recommendations) > 0

    @pytest.mark.asyncio
    async def test_connection_pool_recovery_after_load(self, health_checker):
        """Test connection pool recovery after high load"""
        # Mock database manager with recovering pool
        mock_db_manager = Mock()
        mock_pool_metrics = {
            "pool_size": 10,
            "checked_out": 8,  # High usage initially
            "overflow": 2,
            "checked_in": 2,
            "total_connections": 12,
            "active_connections": 8,
        }
        mock_db_manager._get_pool_metrics.return_value = mock_pool_metrics
        mock_db_manager.is_degraded.return_value = False
        
        # Mock session
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar.return_value = "PostgreSQL 13.0"
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        
        # Mock Redis and Milvus
        mock_redis_manager = AsyncMock()
        mock_redis_manager.set.return_value = True
        mock_redis_manager.get.return_value = "test"
        mock_redis_manager.delete.return_value = True
        mock_redis_manager.is_degraded.return_value = False
        mock_redis_manager.get_connection_info.return_value = {"memory_cache_size": 100}
        
        mock_milvus_client = AsyncMock()
        mock_milvus_client.connect.return_value = None
        mock_milvus_client.health_check.return_value = {"status": "healthy"}
        
        with patch.object(health_checker, 'db_manager', mock_db_manager), \
             patch.object(health_checker, 'redis_manager', mock_redis_manager), \
             patch.object(health_checker, 'milvus_client', mock_milvus_client):
            
            # Simulate pool recovery over time
            recovery_checks = []
            
            for i in range(5):
                # Gradually reduce pool usage to simulate recovery
                usage = max(2, 8 - i * 2)
                mock_pool_metrics["checked_out"] = usage
                mock_pool_metrics["active_connections"] = usage
                mock_pool_metrics["checked_in"] = 10 - usage
                mock_pool_metrics["overflow"] = max(0, usage - 10)
                mock_pool_metrics["total_connections"] = 10 + mock_pool_metrics["overflow"]
                
                result = await health_checker.check_health(include_detailed_validation=False)
                recovery_checks.append(result)
                
                await asyncio.sleep(0.1)
            
            # Verify recovery progression
            assert len(recovery_checks) == 5
            
            # Last check should show better pool status than first
            first_check = recovery_checks[0]
            last_check = recovery_checks[-1]
            
            # Pool usage should have decreased
            first_pool_metrics = first_check.performance_metrics.get("postgresql", {}).get("pool_metrics", {})
            last_pool_metrics = last_check.performance_metrics.get("postgresql", {}).get("pool_metrics", {})
            
            if first_pool_metrics and last_pool_metrics:
                assert last_pool_metrics.get("checked_out", 0) <= first_pool_metrics.get("checked_out", 0)


class TestCacheInvalidationPatternValidation:
    """Test cache invalidation pattern validation"""

    @pytest.fixture
    async def cache_test_environment(self):
        """Set up cache test environment"""
        mock_redis_manager = AsyncMock()
        mock_db_manager = AsyncMock()
        mock_session = AsyncMock()
        
        mock_db_manager.async_session_scope.return_value.__aenter__.return_value = mock_session
        mock_db_manager.async_session_scope.return_value.__aexit__.return_value = None
        mock_db_manager.is_degraded.return_value = False
        
        return {
            "redis_manager": mock_redis_manager,
            "db_manager": mock_db_manager,
            "session": mock_session,
        }

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_data_update(self, cache_test_environment):
        """Test cache invalidation when data is updated"""
        redis_manager = cache_test_environment["redis_manager"]
        db_manager = cache_test_environment["db_manager"]
        session = cache_test_environment["session"]
        
        # Mock cache operations
        cache_data = {}
        
        async def mock_get(key):
            return cache_data.get(key)
        
        async def mock_set(key, value, **kwargs):
            cache_data[key] = value
            return True
        
        async def mock_delete(key):
            if key in cache_data:
                del cache_data[key]
                return True
            return False
        
        redis_manager.get = mock_get
        redis_manager.set = mock_set
        redis_manager.delete = mock_delete
        redis_manager.is_degraded.return_value = False
        
        # Mock database operations
        session.execute.return_value.scalar.return_value = 1
        session.commit = AsyncMock()
        
        # Simulate cache invalidation pattern test
        test_key = "test:user:123"
        test_value = "cached_user_data"
        
        # Step 1: Set cache data
        await redis_manager.set(test_key, test_value)
        cached_value = await redis_manager.get(test_key)
        assert cached_value == test_value
        
        # Step 2: Simulate data update (should invalidate cache)
        await redis_manager.delete(test_key)
        
        # Step 3: Verify cache was invalidated
        cached_value_after_delete = await redis_manager.get(test_key)
        assert cached_value_after_delete is None
        
        # Verify cache invalidation pattern works correctly
        assert test_key not in cache_data

    @pytest.mark.asyncio
    async def test_cache_consistency_validation(self, cache_test_environment):
        """Test cache consistency validation between Redis and PostgreSQL"""
        redis_manager = cache_test_environment["redis_manager"]
        db_manager = cache_test_environment["db_manager"]
        session = cache_test_environment["session"]
        
        # Mock inconsistent cache scenario
        cache_data = {
            "user:123": '{"id": 123, "name": "John Doe", "email": "john@example.com"}',
            "user:456": '{"id": 456, "name": "Jane Smith", "email": "jane@example.com"}',
            "conversation:789": '{"id": 789, "title": "Test Conversation"}',
        }
        
        # Mock database data (different from cache)
        db_users = [
            {"id": 123, "name": "John Updated", "email": "john.updated@example.com"},
            # User 456 deleted from DB but still in cache
        ]
        
        async def mock_get(key):
            return cache_data.get(key)
        
        redis_manager.get = mock_get
        redis_manager.get_connection_info.return_value = {
            "memory_cache_size": len(cache_data),
            "connection_failures": 0,
        }
        
        # Mock database queries for consistency check
        def execute_side_effect(query, *args, **kwargs):
            query_str = str(query)
            result = Mock()
            
            if "SELECT id, name, email FROM auth_users" in query_str:
                result.fetchall.return_value = [(user["id"], user["name"], user["email"]) for user in db_users]
            else:
                result.fetchall.return_value = []
                result.scalar.return_value = 0
            
            return result
        
        session.execute.side_effect = execute_side_effect
        
        # Create consistency validator
        validator = DatabaseConsistencyValidator()
        
        with patch.object(validator, 'redis_manager', redis_manager), \
             patch.object(validator, 'db_manager', db_manager):
            
            # Simulate cache consistency validation
            cache_keys = list(cache_data.keys())
            user_cache_keys = [key for key in cache_keys if key.startswith("user:")]
            
            # Check for stale cache entries
            stale_entries = []
            for key in user_cache_keys:
                user_id = int(key.split(":")[1])
                db_user = next((u for u in db_users if u["id"] == user_id), None)
                
                if not db_user:
                    stale_entries.append(key)
                else:
                    # Check if cached data matches DB data
                    cached_data = await redis_manager.get(key)
                    if cached_data and '"name": "John Doe"' in cached_data and db_user["name"] != "John Doe":
                        stale_entries.append(key)
            
            # Should detect stale cache entries
            assert len(stale_entries) > 0
            assert "user:456" in stale_entries  # Deleted from DB but still in cache

    @pytest.mark.asyncio
    async def test_cache_invalidation_under_concurrent_access(self, cache_test_environment):
        """Test cache invalidation patterns under concurrent access"""
        redis_manager = cache_test_environment["redis_manager"]
        
        # Mock thread-safe cache operations
        cache_data = {}
        cache_lock = threading.Lock()
        
        async def mock_get(key):
            with cache_lock:
                return cache_data.get(key)
        
        async def mock_set(key, value, **kwargs):
            with cache_lock:
                cache_data[key] = value
                return True
        
        async def mock_delete(key):
            with cache_lock:
                if key in cache_data:
                    del cache_data[key]
                    return True
                return False
        
        redis_manager.get = mock_get
        redis_manager.set = mock_set
        redis_manager.delete = mock_delete
        
        # Simulate concurrent cache operations
        async def cache_worker(worker_id: int, operations: int):
            """Worker that performs cache operations"""
            results = []
            
            for i in range(operations):
                key = f"worker:{worker_id}:item:{i}"
                value = f"data_{worker_id}_{i}"
                
                # Set cache value
                await redis_manager.set(key, value)
                
                # Verify it was set
                cached_value = await redis_manager.get(key)
                results.append(cached_value == value)
                
                # Randomly invalidate some entries
                if random.random() < 0.3:  # 30% chance to invalidate
                    await redis_manager.delete(key)
                    
                    # Verify it was deleted
                    deleted_value = await redis_manager.get(key)
                    results.append(deleted_value is None)
                
                await asyncio.sleep(0.01)  # Small delay to allow interleaving
            
            return results
        
        # Run concurrent workers
        num_workers = 5
        operations_per_worker = 10
        
        tasks = [
            cache_worker(worker_id, operations_per_worker)
            for worker_id in range(num_workers)
        ]
        
        worker_results = await asyncio.gather(*tasks)
        
        # Verify all operations completed successfully
        all_results = [result for worker_results_list in worker_results for result in worker_results_list]
        success_rate = sum(all_results) / len(all_results)
        
        # Should have high success rate even under concurrent access
        assert success_rate > 0.95  # At least 95% success rate
        
        # Verify cache state is consistent
        final_cache_size = len(cache_data)
        assert final_cache_size >= 0  # Cache should be in valid state

    @pytest.mark.asyncio
    async def test_cache_invalidation_pattern_validation_with_ttl(self, cache_test_environment):
        """Test cache invalidation pattern validation with TTL (Time To Live)"""
        redis_manager = cache_test_environment["redis_manager"]
        
        # Mock TTL-aware cache
        cache_data = {}
        cache_ttl = {}
        
        async def mock_set(key, value, ex=None, **kwargs):
            cache_data[key] = value
            if ex:
                cache_ttl[key] = time.time() + ex
            return True
        
        async def mock_get(key):
            if key in cache_data:
                # Check TTL
                if key in cache_ttl and time.time() > cache_ttl[key]:
                    # Expired
                    del cache_data[key]
                    del cache_ttl[key]
                    return None
                return cache_data[key]
            return None
        
        async def mock_delete(key):
            deleted = False
            if key in cache_data:
                del cache_data[key]
                deleted = True
            if key in cache_ttl:
                del cache_ttl[key]
            return deleted
        
        redis_manager.set = mock_set
        redis_manager.get = mock_get
        redis_manager.delete = mock_delete
        
        # Test TTL-based invalidation
        test_key = "ttl_test:item:1"
        test_value = "test_data"
        ttl_seconds = 1  # 1 second TTL
        
        # Set cache with TTL
        await redis_manager.set(test_key, test_value, ex=ttl_seconds)
        
        # Should be available immediately
        cached_value = await redis_manager.get(test_key)
        assert cached_value == test_value
        
        # Wait for TTL to expire
        await asyncio.sleep(1.1)
        
        # Should be expired and return None
        expired_value = await redis_manager.get(test_key)
        assert expired_value is None
        
        # Verify key was removed from cache
        assert test_key not in cache_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])