"""
Integration tests for database operations in the consolidated authentication service.

This module provides comprehensive tests for database schema creation, migration,
connection pooling, and optimization utilities.
"""

import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ai_karen_engine.auth.config import DatabaseConfig
from src.ai_karen_engine.auth.connection_pool import ConnectionPool, QueryOptimizer
from src.ai_karen_engine.auth.database_schema import DatabaseSchemaManager
from src.ai_karen_engine.auth.exceptions import DatabaseConnectionError, DatabaseOperationError, MigrationError
from src.ai_karen_engine.auth.migration_utils import AuthDataMigrator
from src.ai_karen_engine.auth.models import UserData


class TestDatabaseSchemaManager:
    """Test suite for DatabaseSchemaManager."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_auth.db")
        return DatabaseConfig(
            database_url=f"sqlite:///{db_path}",
            connection_timeout_seconds=30
        )
    
    @pytest.fixture
    def schema_manager(self, temp_db_config):
        """Create schema manager instance for testing."""
        return DatabaseSchemaManager(temp_db_config)
    
    def test_schema_creation(self, schema_manager):
        """Test unified schema creation."""
        # Create schema
        schema_manager.create_unified_schema()
        
        # Verify tables were created
        cursor = schema_manager.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'auth_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            "auth_schema_version",
            "auth_users",
            "auth_password_hashes",
            "auth_sessions",
            "auth_password_reset_tokens",
            "auth_email_verification_tokens",
            "auth_events",
            "auth_rate_limits",
            "auth_user_roles",
            "auth_permissions",
            "auth_role_permissions",
            "auth_user_devices",
            "auth_security_alerts"
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"
    
    def test_schema_indexes_creation(self, schema_manager):
        """Test that indexes are created properly."""
        schema_manager.create_unified_schema()
        
        cursor = schema_manager.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_auth_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Should have multiple indexes
        assert len(indexes) > 10, "Not enough indexes were created"
        
        # Check for specific important indexes
        expected_indexes = [
            "idx_auth_users_email",
            "idx_auth_sessions_user",
            "idx_auth_events_timestamp"
        ]
        
        for index in expected_indexes:
            assert index in indexes, f"Index {index} was not created"
    
    def test_schema_triggers_creation(self, schema_manager):
        """Test that triggers are created properly."""
        schema_manager.create_unified_schema()
        
        cursor = schema_manager.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = [row[0] for row in cursor.fetchall()]
        
        expected_triggers = [
            "update_auth_users_updated_at",
            "update_auth_password_hashes_updated_at",
            "cleanup_expired_password_reset_tokens"
        ]
        
        for trigger in expected_triggers:
            assert trigger in triggers, f"Trigger {trigger} was not created"
    
    def test_default_data_insertion(self, schema_manager):
        """Test that default data is inserted properly."""
        schema_manager.create_unified_schema()
        
        cursor = schema_manager.connection.cursor()
        
        # Check default permissions
        cursor.execute("SELECT COUNT(*) FROM auth_permissions")
        permission_count = cursor.fetchone()[0]
        assert permission_count > 0, "No default permissions were inserted"
        
        # Check default role permissions
        cursor.execute("SELECT COUNT(*) FROM auth_role_permissions")
        role_permission_count = cursor.fetchone()[0]
        assert role_permission_count > 0, "No default role permissions were inserted"
    
    def test_schema_version_tracking(self, schema_manager):
        """Test schema version tracking."""
        schema_manager.create_unified_schema()
        
        version = schema_manager.get_schema_version()
        assert version == "1.0.0", f"Expected version 1.0.0, got {version}"
    
    def test_database_optimization(self, schema_manager):
        """Test database optimization operations."""
        schema_manager.create_unified_schema()
        
        # Should not raise any exceptions
        schema_manager.optimize_database()
    
    def test_table_statistics(self, schema_manager):
        """Test table statistics retrieval."""
        schema_manager.create_unified_schema()
        
        stats = schema_manager.get_table_statistics()
        
        assert isinstance(stats, dict), "Statistics should be a dictionary"
        assert len(stats) > 0, "Should have statistics for multiple tables"
        
        # Check structure of statistics
        for table_name, table_stats in stats.items():
            assert "row_count" in table_stats
            assert "column_count" in table_stats
            assert isinstance(table_stats["row_count"], int)
            assert isinstance(table_stats["column_count"], int)
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        # Invalid database URL
        invalid_config = DatabaseConfig(
            database_url="invalid://invalid",
            connection_timeout_seconds=30
        )
        
        with pytest.raises(DatabaseConnectionError):
            DatabaseSchemaManager(invalid_config)


class TestConnectionPool:
    """Test suite for ConnectionPool."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_pool.db")
        return DatabaseConfig(
            database_url=f"sqlite:///{db_path}",
            connection_timeout_seconds=30
        )
    
    @pytest.fixture
    def connection_pool(self, temp_db_config):
        """Create connection pool instance for testing."""
        pool = ConnectionPool(temp_db_config, pool_size=5)
        yield pool
        pool.close_all()
    
    def test_pool_initialization(self, connection_pool):
        """Test connection pool initialization."""
        stats = connection_pool.get_statistics()
        
        assert stats["pool_size"] == 5
        assert stats["created"] >= 3  # Should pre-create at least 3 connections
        assert stats["available_connections"] >= 0
    
    def test_connection_acquisition(self, connection_pool):
        """Test connection acquisition from pool."""
        with connection_pool.get_connection() as conn:
            assert conn is not None
            
            # Test connection works
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1
    
    def test_connection_reuse(self, connection_pool):
        """Test that connections are reused properly."""
        initial_stats = connection_pool.get_statistics()
        
        # Use multiple connections
        for _ in range(3):
            with connection_pool.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
        
        final_stats = connection_pool.get_statistics()
        
        # Should have reused connections
        assert final_stats["reused"] > initial_stats["reused"]
    
    def test_query_execution(self, connection_pool):
        """Test query execution through pool."""
        # Create a test table
        connection_pool.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        
        # Insert data
        connection_pool.execute_query(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test_name",)
        )
        
        # Fetch data
        result = connection_pool.execute_query(
            "SELECT name FROM test_table WHERE id = ?",
            (1,),
            fetch_one=True
        )
        
        assert result["name"] == "test_name"
    
    def test_transaction_execution(self, connection_pool):
        """Test transaction execution."""
        # Create test table
        connection_pool.execute_query("""
            CREATE TABLE test_transaction (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Execute transaction
        queries = [
            ("INSERT INTO test_transaction (value) VALUES (?)", ("value1",)),
            ("INSERT INTO test_transaction (value) VALUES (?)", ("value2",))
        ]
        
        connection_pool.execute_transaction(queries)
        
        # Verify data
        results = connection_pool.execute_query(
            "SELECT COUNT(*) as count FROM test_transaction",
            fetch_one=True
        )
        
        assert results["count"] == 2
    
    def test_health_check(self, connection_pool):
        """Test connection pool health check."""
        health = connection_pool.health_check()
        
        assert isinstance(health, dict)
        assert "healthy" in health
        assert "timestamp" in health
        assert "statistics" in health
        
        # Should be healthy initially
        assert health["healthy"] is True
    
    def test_statistics_tracking(self, connection_pool):
        """Test statistics tracking."""
        initial_stats = connection_pool.get_statistics()
        
        # Execute some queries
        for i in range(5):
            connection_pool.execute_query("SELECT ?", (i,), fetch_one=True)
        
        final_stats = connection_pool.get_statistics()
        
        # Should have updated statistics
        assert final_stats["total_queries"] > initial_stats["total_queries"]
        assert final_stats["avg_query_time"] >= 0


class TestQueryOptimizer:
    """Test suite for QueryOptimizer."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_optimizer.db")
        return DatabaseConfig(
            database_url=f"sqlite:///{db_path}",
            connection_timeout_seconds=30
        )
    
    @pytest.fixture
    def query_optimizer(self, temp_db_config):
        """Create query optimizer instance for testing."""
        pool = ConnectionPool(temp_db_config, pool_size=3)
        
        # Create schema for testing
        schema_manager = DatabaseSchemaManager(temp_db_config)
        schema_manager.create_unified_schema()
        
        optimizer = QueryOptimizer(pool)
        yield optimizer
        pool.close_all()
    
    def test_query_analysis(self, query_optimizer):
        """Test query performance analysis."""
        analysis = query_optimizer.analyze_query_performance(
            "SELECT * FROM auth_users WHERE email = ?",
            ("test@example.com",)
        )
        
        assert isinstance(analysis, dict)
        assert "query" in analysis
        assert "execution_time" in analysis
        assert "suggestions" in analysis
        assert analysis["execution_time"] >= 0
    
    def test_index_suggestions(self, query_optimizer):
        """Test index suggestions for tables."""
        suggestions = query_optimizer.suggest_indexes("auth_users")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should contain CREATE INDEX statements
        for suggestion in suggestions:
            assert "CREATE INDEX" in suggestion.upper()
            assert "auth_users" in suggestion
    
    def test_recommended_indexes_creation(self, query_optimizer):
        """Test creation of recommended indexes."""
        results = query_optimizer.create_recommended_indexes()
        
        assert isinstance(results, dict)
        assert "created" in results
        assert "errors" in results
        assert "timestamp" in results
        
        # Should have created some indexes
        assert len(results["created"]) > 0
    
    def test_table_statistics(self, query_optimizer):
        """Test table statistics retrieval."""
        stats = query_optimizer.get_table_statistics()
        
        assert isinstance(stats, dict)
        assert len(stats) > 0
        
        # Check auth_users table statistics
        if "auth_users" in stats:
            user_stats = stats["auth_users"]
            assert "row_count" in user_stats
            assert "column_count" in user_stats
            assert "index_count" in user_stats
            assert "columns" in user_stats
            assert "indexes" in user_stats


class TestAuthDataMigrator:
    """Test suite for AuthDataMigrator."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_migration_target.db")
        return DatabaseConfig(
            database_url=f"sqlite:///{db_path}",
            connection_timeout_seconds=30
        )
    
    @pytest.fixture
    def source_db_path(self):
        """Create a source database with test data."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "source_auth.db")
        
        # Create source database with test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create source tables
        cursor.execute("""
            CREATE TABLE auth_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                roles TEXT DEFAULT '["user"]',
                tenant_id TEXT DEFAULT 'default',
                preferences TEXT DEFAULT '{}',
                is_verified BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE auth_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_in INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                ip_address TEXT DEFAULT 'unknown',
                user_agent TEXT DEFAULT '',
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Insert test data
        test_user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO auth_users (
                user_id, email, full_name, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            test_user_id,
            "test@example.com",
            "Test User",
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        cursor.execute("""
            INSERT INTO auth_sessions (
                session_token, user_id, access_token, refresh_token, expires_in,
                created_at, last_accessed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            test_user_id,
            "access_token_123",
            "refresh_token_123",
            3600,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return db_path
    
    @pytest.fixture
    def migrator(self, temp_db_config):
        """Create migrator instance for testing."""
        return AuthDataMigrator(temp_db_config)
    
    def test_migration_dry_run(self, migrator, source_db_path):
        """Test migration dry run."""
        summary = migrator.migrate_from_existing_databases([source_db_path], dry_run=True)
        
        assert isinstance(summary, dict)
        assert summary["dry_run"] is True
        assert summary["migrated_users"] >= 0
        assert summary["migrated_sessions"] >= 0
        assert "started_at" in summary
        assert "completed_at" in summary
    
    def test_actual_migration(self, migrator, source_db_path):
        """Test actual data migration."""
        summary = migrator.migrate_from_existing_databases([source_db_path], dry_run=False)
        
        assert isinstance(summary, dict)
        assert summary["dry_run"] is False
        assert summary["migrated_users"] > 0
        assert summary["migrated_sessions"] > 0
        assert len(summary["errors"]) == 0
        
        # Verify data was migrated
        cursor = migrator.schema_manager.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM auth_users")
        user_count = cursor.fetchone()[0]
        assert user_count > 0
        
        cursor.execute("SELECT COUNT(*) FROM auth_sessions")
        session_count = cursor.fetchone()[0]
        assert session_count > 0
    
    def test_migration_with_nonexistent_source(self, migrator):
        """Test migration with non-existent source database."""
        summary = migrator.migrate_from_existing_databases(["/nonexistent/path.db"], dry_run=True)
        
        assert len(summary["warnings"]) > 0
        assert "not found" in summary["warnings"][0].lower()
    
    def test_cleanup_old_data(self, migrator, source_db_path):
        """Test cleanup of old data."""
        # First migrate data
        migrator.migrate_from_existing_databases([source_db_path], dry_run=False)
        
        # Add some old test data
        cursor = migrator.schema_manager.connection.cursor()
        old_date = (datetime.utcnow() - timedelta(days=100)).isoformat()
        
        cursor.execute("""
            INSERT INTO auth_events (
                event_id, event_type, timestamp, success, service_version
            ) VALUES (?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), "test_event", old_date, True, "test"))
        
        migrator.schema_manager.connection.commit()
        
        # Cleanup old data
        cleanup_summary = migrator.cleanup_old_data(older_than_days=30)
        
        assert isinstance(cleanup_summary, dict)
        assert "old_events" in cleanup_summary
        assert cleanup_summary["old_events"] >= 0
    
    def test_migration_validation(self, migrator, source_db_path):
        """Test migration validation."""
        # First migrate data
        migrator.migrate_from_existing_databases([source_db_path], dry_run=False)
        
        # Validate migration
        validation_report = migrator.validate_migration()
        
        assert isinstance(validation_report, dict)
        assert "timestamp" in validation_report
        assert "issues" in validation_report
        assert "warnings" in validation_report
        assert "statistics" in validation_report
        
        # Should have statistics
        stats = validation_report["statistics"]
        assert "total_users" in stats
        assert "active_sessions" in stats
        assert "total_events" in stats


class TestDatabaseIntegrationEnd2End:
    """End-to-end integration tests for database operations."""
    
    @pytest.fixture
    def temp_db_config(self):
        """Create temporary database configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_e2e.db")
        return DatabaseConfig(
            database_url=f"sqlite:///{db_path}",
            connection_timeout_seconds=30
        )
    
    def test_complete_database_workflow(self, temp_db_config):
        """Test complete database workflow from schema creation to optimization."""
        # 1. Create schema
        schema_manager = DatabaseSchemaManager(temp_db_config)
        schema_manager.create_unified_schema()
        
        # 2. Set up connection pool
        pool = ConnectionPool(temp_db_config, pool_size=3)
        
        try:
            # 3. Insert test data
            test_user_id = str(uuid.uuid4())
            pool.execute_query("""
                INSERT INTO auth_users (
                    user_id, email, full_name, roles, tenant_id, preferences,
                    is_verified, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_user_id,
                "integration@test.com",
                "Integration Test User",
                '["user"]',
                "default",
                '{}',
                True,
                True,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            # 4. Create session
            session_token = str(uuid.uuid4())
            pool.execute_query("""
                INSERT INTO auth_sessions (
                    session_token, user_id, access_token, refresh_token, expires_in,
                    created_at, last_accessed, ip_address, user_agent, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_token,
                test_user_id,
                "access_token_integration",
                "refresh_token_integration",
                3600,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat(),
                "127.0.0.1",
                "Integration Test Agent",
                True
            ))
            
            # 5. Query data
            user = pool.execute_query(
                "SELECT * FROM auth_users WHERE user_id = ?",
                (test_user_id,),
                fetch_one=True
            )
            assert user is not None
            assert user["email"] == "integration@test.com"
            
            session = pool.execute_query(
                "SELECT * FROM auth_sessions WHERE session_token = ?",
                (session_token,),
                fetch_one=True
            )
            assert session is not None
            assert session["user_id"] == test_user_id
            
            # 6. Test query optimization
            optimizer = QueryOptimizer(pool)
            
            # Analyze query performance
            analysis = optimizer.analyze_query_performance(
                "SELECT * FROM auth_users WHERE email = ?",
                ("integration@test.com",)
            )
            assert analysis["execution_time"] >= 0
            
            # Create recommended indexes
            index_results = optimizer.create_recommended_indexes()
            assert len(index_results["created"]) > 0
            
            # 7. Test health check
            health = pool.health_check()
            assert health["healthy"] is True
            
            # 8. Get statistics
            stats = pool.get_statistics()
            assert stats["total_queries"] > 0
            
            table_stats = optimizer.get_table_statistics()
            assert "auth_users" in table_stats
            assert table_stats["auth_users"]["row_count"] >= 1
            
            # 9. Optimize database
            schema_manager.optimize_database()
            
        finally:
            pool.close_all()
    
    def test_concurrent_operations(self, temp_db_config):
        """Test concurrent database operations."""
        import threading
        import time
        
        schema_manager = DatabaseSchemaManager(temp_db_config)
        schema_manager.create_unified_schema()
        
        pool = ConnectionPool(temp_db_config, pool_size=5)
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    user_id = f"user_{worker_id}_{i}"
                    pool.execute_query("""
                        INSERT INTO auth_users (
                            user_id, email, created_at, updated_at
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        user_id,
                        f"user_{worker_id}_{i}@test.com",
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat()
                    ))
                    
                    # Small delay to simulate real usage
                    time.sleep(0.01)
                
                results.append(f"Worker {worker_id} completed")
                
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        try:
            # Start multiple worker threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=30)
            
            # Check results
            assert len(errors) == 0, f"Errors occurred: {errors}"
            assert len(results) == 3, f"Expected 3 workers to complete, got {len(results)}"
            
            # Verify data was inserted
            total_users = pool.execute_query(
                "SELECT COUNT(*) as count FROM auth_users",
                fetch_one=True
            )
            assert total_users["count"] == 30  # 3 workers * 10 users each
            
        finally:
            pool.close_all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])