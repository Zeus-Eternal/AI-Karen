"""
Tests for the DatabaseConsolidationMigrator class.

This module tests the complete SQLite to PostgreSQL migration process,
including user data migration, session migration, token migration,
and comprehensive validation logic.
"""

import asyncio
import json
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.ai_karen_engine.auth.database_consolidation_migrator import (
    DatabaseConsolidationMigrator,
    MigrationResult,
    MigrationValidator,
    UUIDMapping,
)
from src.ai_karen_engine.auth.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    MigrationError,
)


class TestDatabaseConsolidationMigrator:
    """Test cases for DatabaseConsolidationMigrator."""
    
    @pytest.fixture
    def temp_sqlite_db(self):
        """Create a temporary SQLite database with test data."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        
        conn = sqlite3.connect(temp_file.name)
        cursor = conn.cursor()
        
        # Create auth_users table
        cursor.execute("""
            CREATE TABLE auth_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                roles TEXT NOT NULL DEFAULT '["user"]',
                tenant_id TEXT NOT NULL DEFAULT 'default',
                preferences TEXT NOT NULL DEFAULT '{}',
                is_verified BOOLEAN NOT NULL DEFAULT 1,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login_at TEXT,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                two_factor_enabled BOOLEAN NOT NULL DEFAULT 0,
                two_factor_secret TEXT
            )
        """)
        
        # Create auth_password_hashes table
        cursor.execute("""
            CREATE TABLE auth_password_hashes (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
            )
        """)
        
        # Create auth_sessions table
        cursor.execute("""
            CREATE TABLE auth_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_in INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                ip_address TEXT NOT NULL DEFAULT 'unknown',
                user_agent TEXT NOT NULL DEFAULT '',
                device_fingerprint TEXT,
                geolocation TEXT,
                risk_score REAL NOT NULL DEFAULT 0.0,
                security_flags TEXT NOT NULL DEFAULT '[]',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
            )
        """)
        
        # Create token tables
        cursor.execute("""
            CREATE TABLE auth_password_reset_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                ip_address TEXT NOT NULL DEFAULT 'unknown',
                user_agent TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE auth_email_verification_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                ip_address TEXT NOT NULL DEFAULT 'unknown',
                user_agent TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES auth_users (user_id) ON DELETE CASCADE
            )
        """)
        
        # Insert test data
        test_user_id = str(uuid.uuid4())
        test_session_token = str(uuid.uuid4())
        test_reset_token_id = str(uuid.uuid4())
        test_verification_token_id = str(uuid.uuid4())
        
        now = datetime.utcnow().isoformat()
        future = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        # Insert test user
        cursor.execute("""
            INSERT INTO auth_users (
                user_id, email, full_name, roles, tenant_id, preferences,
                is_verified, is_active, created_at, updated_at, failed_login_attempts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_user_id, 'test@example.com', 'Test User', '["user", "admin"]',
            'test-tenant', '{"theme": "dark"}', True, True, now, now, 0
        ))
        
        # Insert password hash
        cursor.execute("""
            INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (test_user_id, '$2b$12$test.hash.value', now, now))
        
        # Insert test session
        cursor.execute("""
            INSERT INTO auth_sessions (
                session_token, user_id, access_token, refresh_token, expires_in,
                created_at, last_accessed, ip_address, user_agent, risk_score,
                security_flags, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_session_token, test_user_id, 'access_token_123', 'refresh_token_123',
            3600, now, now, '192.168.1.1', 'Test User Agent', 0.1, '["test_flag"]', True
        ))
        
        # Insert test reset token
        cursor.execute("""
            INSERT INTO auth_password_reset_tokens (
                token_id, user_id, token_hash, created_at, expires_at, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_reset_token_id, test_user_id, 'reset_token_hash_123',
            now, future, '192.168.1.1', 'Test User Agent'
        ))
        
        # Insert test verification token
        cursor.execute("""
            INSERT INTO auth_email_verification_tokens (
                token_id, user_id, token_hash, created_at, expires_at, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_verification_token_id, test_user_id, 'verification_token_hash_123',
            now, future, '192.168.1.1', 'Test User Agent'
        ))
        
        conn.commit()
        conn.close()
        
        yield temp_file.name, test_user_id, test_session_token, test_reset_token_id, test_verification_token_id
        
        # Cleanup
        Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def mock_postgres_url(self):
        """Mock PostgreSQL URL for testing."""
        return "postgresql+asyncpg://test:test@localhost:5432/test_db"
    
    @pytest.fixture
    def migrator(self, temp_sqlite_db, mock_postgres_url):
        """Create a DatabaseConsolidationMigrator instance for testing."""
        sqlite_path, _, _, _, _ = temp_sqlite_db
        return DatabaseConsolidationMigrator([sqlite_path], mock_postgres_url)
    
    def test_migrator_initialization(self, migrator, temp_sqlite_db, mock_postgres_url):
        """Test migrator initialization."""
        sqlite_path, _, _, _, _ = temp_sqlite_db
        
        assert migrator.sqlite_paths == [sqlite_path]
        assert migrator.postgres_url == mock_postgres_url
        assert migrator.uuid_mappings == {}
        assert migrator.sqlite_connections == []
        assert migrator.postgres_engine is None
        assert migrator.async_postgres_engine is None
    
    @pytest.mark.asyncio
    async def test_initialize_connections_success(self, migrator):
        """Test successful connection initialization."""
        with patch('sqlite3.connect') as mock_sqlite_connect, \
             patch('sqlalchemy.create_engine') as mock_create_engine, \
             patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_create_async_engine:
            
            # Mock SQLite connection
            mock_sqlite_conn = MagicMock()
            mock_sqlite_connect.return_value = mock_sqlite_conn
            
            # Mock PostgreSQL engines
            mock_postgres_engine = MagicMock()
            mock_async_postgres_engine = MagicMock()
            mock_create_engine.return_value = mock_postgres_engine
            mock_create_async_engine.return_value = mock_async_postgres_engine
            
            # Mock async engine connection test
            mock_conn = AsyncMock()
            mock_async_postgres_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            # Mock Path.exists to return True
            with patch('pathlib.Path.exists', return_value=True):
                await migrator._initialize_connections()
            
            assert len(migrator.sqlite_connections) == 1
            assert migrator.postgres_engine == mock_postgres_engine
            assert migrator.async_postgres_engine == mock_async_postgres_engine
    
    @pytest.mark.asyncio
    async def test_initialize_connections_no_sqlite_files(self, migrator):
        """Test connection initialization with no valid SQLite files."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(DatabaseConnectionError, match="No valid SQLite databases found"):
                await migrator._initialize_connections()
    
    @pytest.mark.asyncio
    async def test_ensure_postgres_schema(self, migrator):
        """Test PostgreSQL schema creation."""
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        await migrator._ensure_postgres_schema()
        
        # Verify that execute was called multiple times for table creation
        assert mock_conn.execute.call_count >= 4  # At least 4 tables should be created
    
    @pytest.mark.asyncio
    async def test_migrate_users_success(self, migrator, temp_sqlite_db):
        """Test successful user migration."""
        sqlite_path, test_user_id, _, _, _ = temp_sqlite_db
        
        # Mock connections
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        # Mock existing user check (return None = user doesn't exist)
        mock_conn.execute.return_value.fetchone.return_value = None
        
        # Initialize SQLite connections manually for test
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        migrator.sqlite_connections = [sqlite_conn]
        
        user_mapping = await migrator._migrate_users()
        
        assert test_user_id in user_mapping
        assert len(user_mapping) == 1
        assert migrator.migration_stats['users_processed'] == 1
        
        # Verify user was inserted into PostgreSQL
        mock_conn.execute.assert_called()
        
        sqlite_conn.close()
    
    @pytest.mark.asyncio
    async def test_migrate_sessions_success(self, migrator, temp_sqlite_db):
        """Test successful session migration."""
        sqlite_path, test_user_id, test_session_token, _, _ = temp_sqlite_db
        
        # Mock connections
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        # Mock session existence check (return None = session doesn't exist)
        mock_conn.execute.return_value.fetchone.return_value = None
        
        # Initialize SQLite connections manually for test
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        migrator.sqlite_connections = [sqlite_conn]
        
        # Create user mapping
        postgres_user_id = str(uuid.uuid4())
        user_mapping = {test_user_id: postgres_user_id}
        
        session_count = await migrator._migrate_sessions(user_mapping)
        
        assert session_count == 1
        assert migrator.migration_stats['sessions_processed'] == 1
        
        # Verify session was inserted into PostgreSQL
        mock_conn.execute.assert_called()
        
        sqlite_conn.close()
    
    @pytest.mark.asyncio
    async def test_migrate_tokens_success(self, migrator, temp_sqlite_db):
        """Test successful token migration."""
        sqlite_path, test_user_id, _, test_reset_token_id, test_verification_token_id = temp_sqlite_db
        
        # Mock connections
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        # Initialize SQLite connections manually for test
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        migrator.sqlite_connections = [sqlite_conn]
        
        # Create user mapping
        postgres_user_id = str(uuid.uuid4())
        user_mapping = {test_user_id: postgres_user_id}
        
        token_count = await migrator._migrate_tokens(user_mapping)
        
        assert token_count == 2  # 1 reset token + 1 verification token
        assert migrator.migration_stats['tokens_processed'] == 2
        
        # Verify tokens were inserted into PostgreSQL
        mock_conn.execute.assert_called()
        
        sqlite_conn.close()
    
    @pytest.mark.asyncio
    async def test_validate_migration_success(self, migrator):
        """Test successful migration validation."""
        # Mock connections and data
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        # Mock SQLite connections with test data
        mock_sqlite_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite_conn.cursor.return_value = mock_cursor
        
        # Mock SQLite counts
        mock_cursor.fetchone.side_effect = [
            [1],  # users count
            [1],  # sessions count
            [1],  # reset tokens count
            [1],  # verification tokens count
        ]
        
        migrator.sqlite_connections = [mock_sqlite_conn]
        
        # Mock PostgreSQL counts and integrity checks
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [
            1,  # postgres user count
            1,  # postgres session count
            1,  # postgres reset token count
            1,  # postgres verification token count
            0,  # orphaned sessions
            0,  # orphaned reset tokens
            0,  # orphaned verification tokens
            [],  # duplicate emails
            0,  # null tenant count
            0,  # expired active sessions
        ]
        mock_conn.execute.return_value = mock_result
        mock_conn.execute.return_value.fetchall.return_value = []
        
        validation_result = await migrator._validate_migration()
        
        assert validation_result['overall_success'] is True
        assert validation_result['user_count_match'] is True
        assert validation_result['session_count_match'] is True
        assert validation_result['foreign_key_integrity'] is True
        assert len(validation_result['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_migration_count_mismatch(self, migrator):
        """Test migration validation with count mismatch."""
        # Mock connections and data
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        # Mock SQLite connections with test data
        mock_sqlite_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite_conn.cursor.return_value = mock_cursor
        
        # Mock SQLite counts (higher than PostgreSQL)
        mock_cursor.fetchone.side_effect = [
            [2],  # users count
            [2],  # sessions count
            [0],  # reset tokens count
            [0],  # verification tokens count
        ]
        
        migrator.sqlite_connections = [mock_sqlite_conn]
        
        # Mock PostgreSQL counts (lower than SQLite)
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [
            1,  # postgres user count (mismatch)
            1,  # postgres session count (mismatch)
            0,  # postgres reset token count
            0,  # postgres verification token count
            0,  # orphaned sessions
            0,  # orphaned reset tokens
            0,  # orphaned verification tokens
            [],  # duplicate emails
            0,  # null tenant count
            0,  # expired active sessions
        ]
        mock_conn.execute.return_value = mock_result
        mock_conn.execute.return_value.fetchall.return_value = []
        
        validation_result = await migrator._validate_migration()
        
        assert validation_result['overall_success'] is False
        assert validation_result['user_count_match'] is False
        assert validation_result['session_count_match'] is False
        assert len(validation_result['errors']) >= 1
    
    @pytest.mark.asyncio
    async def test_rollback_migration(self, migrator):
        """Test migration rollback."""
        mock_conn = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
        migrator.async_postgres_engine = mock_async_engine
        
        await migrator._rollback_migration()
        
        # Verify that delete statements were executed
        assert mock_conn.execute.call_count >= 4  # Should delete from 4 tables
    
    @pytest.mark.asyncio
    async def test_cleanup_connections(self, migrator):
        """Test connection cleanup."""
        # Mock connections
        mock_sqlite_conn = MagicMock()
        mock_postgres_engine = MagicMock()
        mock_async_postgres_engine = AsyncMock()
        
        migrator.sqlite_connections = [mock_sqlite_conn]
        migrator.postgres_engine = mock_postgres_engine
        migrator.async_postgres_engine = mock_async_postgres_engine
        
        await migrator._cleanup_connections()
        
        mock_sqlite_conn.close.assert_called_once()
        mock_postgres_engine.dispose.assert_called_once()
        mock_async_postgres_engine.dispose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_migrate_all_data_success(self, migrator):
        """Test complete migration process success."""
        with patch.object(migrator, '_initialize_connections') as mock_init, \
             patch.object(migrator, '_ensure_postgres_schema') as mock_schema, \
             patch.object(migrator, '_migrate_users') as mock_users, \
             patch.object(migrator, '_migrate_sessions') as mock_sessions, \
             patch.object(migrator, '_migrate_tokens') as mock_tokens, \
             patch.object(migrator, '_validate_migration') as mock_validate, \
             patch.object(migrator, '_cleanup_connections') as mock_cleanup:
            
            # Mock successful operations
            mock_users.return_value = {'user1': 'postgres_user1'}
            mock_sessions.return_value = 1
            mock_tokens.return_value = 2
            mock_validate.return_value = {'overall_success': True}
            
            result = await migrator.migrate_all_data()
            
            assert result.success is True
            assert result.migrated_users == 1
            assert result.migrated_sessions == 1
            assert result.migrated_tokens == 2
            assert result.started_at is not None
            assert result.completed_at is not None
            
            # Verify all steps were called
            mock_init.assert_called_once()
            mock_schema.assert_called_once()
            mock_users.assert_called_once()
            mock_sessions.assert_called_once()
            mock_tokens.assert_called_once()
            mock_validate.assert_called_once()
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_migrate_all_data_failure_with_rollback(self, migrator):
        """Test migration failure with rollback."""
        with patch.object(migrator, '_initialize_connections') as mock_init, \
             patch.object(migrator, '_ensure_postgres_schema') as mock_schema, \
             patch.object(migrator, '_migrate_users') as mock_users, \
             patch.object(migrator, '_rollback_migration') as mock_rollback, \
             patch.object(migrator, '_cleanup_connections') as mock_cleanup:
            
            # Mock failure in user migration
            mock_users.side_effect = Exception("Migration failed")
            
            with pytest.raises(MigrationError, match="Migration failed"):
                await migrator.migrate_all_data()
            
            # Verify rollback was attempted
            mock_rollback.assert_called_once()
            mock_cleanup.assert_called_once()


class TestMigrationResult:
    """Test cases for MigrationResult."""
    
    def test_migration_result_initialization(self):
        """Test MigrationResult initialization."""
        result = MigrationResult(success=True)
        
        assert result.success is True
        assert result.migrated_users == 0
        assert result.migrated_sessions == 0
        assert result.migrated_tokens == 0
        assert result.validation_results == {}
        assert result.errors == []
        assert result.warnings == []
        assert result.started_at is None
        assert result.completed_at is None
    
    def test_add_error(self):
        """Test adding errors to migration result."""
        result = MigrationResult(success=True)
        
        result.add_error("Test error")
        
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
    
    def test_add_warning(self):
        """Test adding warnings to migration result."""
        result = MigrationResult(success=True)
        
        result.add_warning("Test warning")
        
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"


class TestUUIDMapping:
    """Test cases for UUIDMapping."""
    
    def test_uuid_mapping_initialization(self):
        """Test UUIDMapping initialization."""
        mapping = UUIDMapping(
            sqlite_id="sqlite_123",
            postgres_id="postgres_456",
            entity_type="user"
        )
        
        assert mapping.sqlite_id == "sqlite_123"
        assert mapping.postgres_id == "postgres_456"
        assert mapping.entity_type == "user"
        assert isinstance(mapping.created_at, datetime)


class TestMigrationValidator:
    """Test cases for MigrationValidator."""
    
    @pytest.fixture
    def mock_postgres_url(self):
        """Mock PostgreSQL URL for testing."""
        return "postgresql+asyncpg://test:test@localhost:5432/test_db"
    
    @pytest.fixture
    def validator(self, mock_postgres_url):
        """Create a MigrationValidator instance for testing."""
        return MigrationValidator(mock_postgres_url)
    
    def test_validator_initialization(self, validator, mock_postgres_url):
        """Test validator initialization."""
        assert validator.postgres_url == mock_postgres_url
        assert validator.async_engine is not None
    
    @pytest.mark.asyncio
    async def test_validate_complete_migration_success(self, validator):
        """Test successful complete migration validation."""
        with patch.object(validator, '_check_table_existence') as mock_tables, \
             patch.object(validator, '_check_data_consistency') as mock_consistency, \
             patch.object(validator, '_check_foreign_key_constraints') as mock_fk, \
             patch.object(validator, '_check_data_anomalies') as mock_anomalies:
            
            # Mock all checks as passing
            mock_tables.return_value = {'check_name': 'table_existence', 'passed': True}
            mock_consistency.return_value = {'check_name': 'data_consistency', 'passed': True}
            mock_fk.return_value = {'check_name': 'foreign_key_constraints', 'passed': True}
            mock_anomalies.return_value = {'check_name': 'data_anomalies', 'passed': True}
            
            # Mock async engine
            mock_conn = AsyncMock()
            mock_async_engine = AsyncMock()
            mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_async_engine.dispose = AsyncMock()
            validator.async_engine = mock_async_engine
            
            result = await validator.validate_complete_migration()
            
            assert result['overall_status'] == 'passed'
            assert len(result['checks_performed']) == 4
            assert len(result['issues_found']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_complete_migration_failure(self, validator):
        """Test complete migration validation with failures."""
        with patch.object(validator, '_check_table_existence') as mock_tables, \
             patch.object(validator, '_check_data_consistency') as mock_consistency, \
             patch.object(validator, '_check_foreign_key_constraints') as mock_fk, \
             patch.object(validator, '_check_data_anomalies') as mock_anomalies, \
             patch.object(validator, '_generate_recommendations') as mock_recommendations:
            
            # Mock some checks as failing
            mock_tables.return_value = {'check_name': 'table_existence', 'passed': False}
            mock_consistency.return_value = {'check_name': 'data_consistency', 'passed': True}
            mock_fk.return_value = {'check_name': 'foreign_key_constraints', 'passed': False}
            mock_anomalies.return_value = {'check_name': 'data_anomalies', 'passed': True}
            mock_recommendations.return_value = ['Fix table issues', 'Fix foreign key issues']
            
            # Mock async engine
            mock_conn = AsyncMock()
            mock_async_engine = AsyncMock()
            mock_async_engine.begin.return_value.__aenter__.return_value = mock_conn
            mock_async_engine.dispose = AsyncMock()
            validator.async_engine = mock_async_engine
            
            result = await validator.validate_complete_migration()
            
            assert result['overall_status'] == 'failed'
            assert len(result['checks_performed']) == 4
            assert len(result['recommendations']) == 2
    
    @pytest.mark.asyncio
    async def test_check_table_existence_all_present(self, validator):
        """Test table existence check with all tables present."""
        mock_conn = AsyncMock()
        
        # Mock all tables as existing
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_table_existence(mock_conn)
        
        assert result['check_name'] == 'table_existence'
        assert result['passed'] is True
        assert len(result['details']['missing_tables']) == 0
    
    @pytest.mark.asyncio
    async def test_check_table_existence_missing_tables(self, validator):
        """Test table existence check with missing tables."""
        mock_conn = AsyncMock()
        
        # Mock some tables as missing
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [True, False, True, False]  # 2 missing
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_table_existence(mock_conn)
        
        assert result['check_name'] == 'table_existence'
        assert result['passed'] is False
        assert len(result['details']['missing_tables']) == 2
    
    @pytest.mark.asyncio
    async def test_check_data_consistency_no_issues(self, validator):
        """Test data consistency check with no issues."""
        mock_conn = AsyncMock()
        
        # Mock no orphaned sessions
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [5, 0]  # 5 users without sessions (normal), 0 sessions without users
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_data_consistency(mock_conn)
        
        assert result['check_name'] == 'data_consistency'
        assert result['passed'] is True
        assert len(result['details']['issues']) == 0
    
    @pytest.mark.asyncio
    async def test_check_data_consistency_with_issues(self, validator):
        """Test data consistency check with issues."""
        mock_conn = AsyncMock()
        
        # Mock orphaned sessions
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [5, 3]  # 5 users without sessions, 3 sessions without users
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_data_consistency(mock_conn)
        
        assert result['check_name'] == 'data_consistency'
        assert result['passed'] is False
        assert len(result['details']['issues']) == 1
        assert "3 sessions without corresponding users" in result['details']['issues'][0]
    
    @pytest.mark.asyncio
    async def test_check_foreign_key_constraints_valid(self, validator):
        """Test foreign key constraints check with valid constraints."""
        mock_conn = AsyncMock()
        
        # Mock no constraint violations
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0, 0]  # No violations
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_foreign_key_constraints(mock_conn)
        
        assert result['check_name'] == 'foreign_key_constraints'
        assert result['passed'] is True
        assert len(result['details']['violations']) == 0
    
    @pytest.mark.asyncio
    async def test_check_foreign_key_constraints_violations(self, validator):
        """Test foreign key constraints check with violations."""
        mock_conn = AsyncMock()
        
        # Mock constraint violations
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [2, 1, 0]  # 2 session violations, 1 reset token violation, 0 verification token violations
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_foreign_key_constraints(mock_conn)
        
        assert result['check_name'] == 'foreign_key_constraints'
        assert result['passed'] is False
        assert len(result['details']['violations']) == 2
    
    @pytest.mark.asyncio
    async def test_check_data_anomalies_none_found(self, validator):
        """Test data anomalies check with no anomalies."""
        mock_conn = AsyncMock()
        
        # Mock no anomalies
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [0, 0]  # No null required fields, no invalid expiration sessions
        mock_result.fetchall.return_value = []  # No duplicate emails
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_data_anomalies(mock_conn)
        
        assert result['check_name'] == 'data_anomalies'
        assert result['passed'] is True
        assert len(result['details']['anomalies']) == 0
    
    @pytest.mark.asyncio
    async def test_check_data_anomalies_found(self, validator):
        """Test data anomalies check with anomalies found."""
        mock_conn = AsyncMock()
        
        # Mock anomalies
        mock_result = MagicMock()
        mock_result.scalar.side_effect = [2, 1]  # 2 users with null required fields, 1 invalid expiration session
        mock_result.fetchall.return_value = [('test@example.com', 2)]  # 1 duplicate email
        mock_conn.execute.return_value = mock_result
        
        result = await validator._check_data_anomalies(mock_conn)
        
        assert result['check_name'] == 'data_anomalies'
        assert result['passed'] is False
        assert len(result['details']['anomalies']) == 3
    
    def test_generate_recommendations(self, validator):
        """Test recommendation generation."""
        failed_checks = [
            {
                'check_name': 'table_existence',
                'passed': False,
                'details': {'missing_tables': ['users', 'sessions']}
            },
            {
                'check_name': 'foreign_key_constraints',
                'passed': False,
                'details': {'violations': ['2 sessions with invalid user_id']}
            }
        ]
        
        recommendations = validator._generate_recommendations(failed_checks)
        
        assert len(recommendations) == 2
        assert "Create missing tables: users, sessions" in recommendations[0]
        assert "Fix foreign key constraint violations" in recommendations[1]


if __name__ == "__main__":
    pytest.main([__file__])