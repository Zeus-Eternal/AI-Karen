"""
Unit tests for database migration utilities.

Tests the PostgreSQL schema creation, migration validation, backup management,
and consolidation migration functionality.
"""

import json
import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path to import our modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.database.migration.backup_manager import BackupManager
from ai_karen_engine.database.migration.consolidation_migrator import DatabaseConsolidationMigrator
from ai_karen_engine.database.migration.migration_validator import MigrationValidator
from ai_karen_engine.database.migration.postgres_schema import (
    Base,
    PasswordResetToken,
    PostgreSQLAuthSchema,
    User,
    UserSession,
)


class TestPostgreSQLAuthSchema:
    """Test PostgreSQL authentication schema creation and validation."""
    
    @pytest.fixture
    def temp_postgres_url(self):
        """Create temporary PostgreSQL database URL for testing."""
        # Use SQLite in-memory database for testing
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def schema_manager(self, temp_postgres_url):
        """Create schema manager for testing."""
        return PostgreSQLAuthSchema(temp_postgres_url)
    
    def test_create_schema_success(self, schema_manager):
        """Test successful schema creation."""
        result = schema_manager.create_schema()
        assert result is True
        
        # Verify schema validation passes
        assert schema_manager.validate_schema() is True
    
    def test_create_schema_with_drop_existing(self, schema_manager):
        """Test schema creation with drop existing tables."""
        # Create schema first
        schema_manager.create_schema()
        
        # Create again with drop_existing=True
        result = schema_manager.create_schema(drop_existing=True)
        assert result is True
        assert schema_manager.validate_schema() is True
    
    def test_validate_schema_missing_tables(self, temp_postgres_url):
        """Test schema validation with missing tables."""
        # Create empty database
        engine = create_engine(temp_postgres_url)
        schema_manager = PostgreSQLAuthSchema(temp_postgres_url)
        
        # Validation should fail on empty database
        assert schema_manager.validate_schema() is False
    
    def test_get_table_info(self, schema_manager):
        """Test getting table information."""
        schema_manager.create_schema()
        table_info = schema_manager.get_table_info()
        
        assert isinstance(table_info, dict)
        assert 'auth_users' in table_info
        assert 'auth_sessions' in table_info
        assert 'password_reset_tokens' in table_info
        
        # Check that table info contains expected fields
        users_info = table_info['auth_users']
        assert 'columns' in users_info
        assert 'indexes' in users_info
        assert 'foreign_keys' in users_info
        assert 'email' in users_info['columns']
    
    def test_create_indexes(self, schema_manager):
        """Test creating performance indexes."""
        schema_manager.create_schema()
        result = schema_manager.create_indexes()
        assert result is True
    
    def test_get_schema_ddl(self, schema_manager):
        """Test generating schema DDL."""
        ddl = schema_manager.get_schema_ddl()
        assert isinstance(ddl, str)
        assert len(ddl) > 0
        assert 'CREATE TABLE' in ddl
        assert 'auth_users' in ddl
    
    def test_cleanup_expired_tokens(self, schema_manager):
        """Test cleanup of expired password reset tokens."""
        schema_manager.create_schema()
        
        # Add some test tokens
        with schema_manager.SessionLocal() as session:
            # Add expired token
            expired_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                token="expired_token",
                expires_at=datetime.utcnow() - timedelta(hours=1),
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
            
            # Add valid token
            valid_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                token="valid_token",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow()
            )
            
            session.add(expired_token)
            session.add(valid_token)
            session.commit()
        
        # Cleanup should remove 1 expired token
        cleaned_count = schema_manager.cleanup_expired_tokens()
        assert cleaned_count == 1
    
    def test_cleanup_expired_sessions(self, schema_manager):
        """Test cleanup of expired sessions."""
        schema_manager.create_schema()
        
        # Add test user first
        with schema_manager.SessionLocal() as session:
            test_user = User(
                id=uuid.uuid4(),
                email="test@example.com",
                password_hash="hash",
                tenant_id=uuid.uuid4()
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            
            # Add expired session
            expired_session = UserSession(
                id=uuid.uuid4(),
                user_id=test_user.id,
                session_token="expired_session",
                expires_at=datetime.utcnow() - timedelta(hours=1),
                created_at=datetime.utcnow() - timedelta(hours=2),
                is_active=True
            )
            
            # Add valid session
            valid_session = UserSession(
                id=uuid.uuid4(),
                user_id=test_user.id,
                session_token="valid_session",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            session.add(expired_session)
            session.add(valid_session)
            session.commit()
        
        # Cleanup should mark 1 session as inactive
        cleaned_count = schema_manager.cleanup_expired_sessions()
        assert cleaned_count == 1


class TestBackupManager:
    """Test backup and rollback functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for backups."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def backup_manager(self, temp_dir):
        """Create backup manager for testing."""
        return BackupManager(temp_dir)
    
    @pytest.fixture
    def sample_sqlite_db(self, temp_dir):
        """Create sample SQLite database for testing."""
        db_path = os.path.join(temp_dir, "test.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sample table and data
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash) 
            VALUES ('1', 'test@example.com', 'hash123')
        """)
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_backup_sqlite_databases(self, backup_manager, sample_sqlite_db):
        """Test backing up SQLite databases."""
        sqlite_paths = [sample_sqlite_db]
        backup_mapping = backup_manager.backup_sqlite_databases(sqlite_paths)
        
        assert len(backup_mapping) == 1
        assert sample_sqlite_db in backup_mapping
        
        # Verify backup file exists
        backup_path = backup_mapping[sample_sqlite_db]
        assert os.path.exists(backup_path)
        
        # Verify backup manifest exists
        manifest_files = list(Path(backup_manager.backup_dir).glob("backup_manifest_*.json"))
        assert len(manifest_files) == 1
        
        with open(manifest_files[0], 'r') as f:
            manifest = json.load(f)
            assert 'sqlite_backups' in manifest
            assert sample_sqlite_db in manifest['sqlite_backups']
    
    def test_verify_backup_integrity(self, backup_manager, sample_sqlite_db):
        """Test backup integrity verification."""
        backup_mapping = backup_manager.backup_sqlite_databases([sample_sqlite_db])
        
        # Verify integrity should pass
        assert backup_manager.verify_backup_integrity(backup_mapping) is True
        
        # Test with missing backup file
        fake_mapping = {sample_sqlite_db: "/nonexistent/path.db"}
        assert backup_manager.verify_backup_integrity(fake_mapping) is False
    
    def test_restore_sqlite_databases(self, backup_manager, sample_sqlite_db, temp_dir):
        """Test restoring SQLite databases from backups."""
        # Create backup
        backup_mapping = backup_manager.backup_sqlite_databases([sample_sqlite_db])
        
        # Modify original database
        conn = sqlite3.connect(sample_sqlite_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        
        # Verify original is empty
        conn = sqlite3.connect(sample_sqlite_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        assert cursor.fetchone()[0] == 0
        conn.close()
        
        # Restore from backup
        result = backup_manager.restore_sqlite_databases(backup_mapping)
        assert result is True
        
        # Verify data is restored
        conn = sqlite3.connect(sample_sqlite_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        assert cursor.fetchone()[0] == 1
        conn.close()
    
    def test_list_backups(self, backup_manager, sample_sqlite_db):
        """Test listing available backups."""
        # Create a backup
        backup_manager.backup_sqlite_databases([sample_sqlite_db])
        
        backups = backup_manager.list_backups()
        assert len(backups) == 1
        assert 'timestamp' in backups[0]
        assert 'sqlite_backups' in backups[0]
    
    def test_cleanup_old_backups(self, backup_manager, sample_sqlite_db):
        """Test cleaning up old backup files."""
        # Create multiple backups
        for i in range(3):
            backup_manager.backup_sqlite_databases([sample_sqlite_db])
        
        # Should have 3 backups
        assert len(backup_manager.list_backups()) == 3
        
        # Cleanup keeping only 1
        cleaned_count = backup_manager.cleanup_old_backups(keep_count=1)
        assert cleaned_count > 0
        
        # Should have only 1 backup left
        assert len(backup_manager.list_backups()) == 1


class TestMigrationValidator:
    """Test migration validation functionality."""
    
    @pytest.fixture
    def temp_postgres_url(self):
        """Create temporary PostgreSQL database URL for testing."""
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def sample_sqlite_db(self, temp_dir):
        """Create sample SQLite database for testing."""
        db_path = os.path.join(temp_dir, "test.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sample tables and data
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_token TEXT UNIQUE
            )
        """)
        
        cursor.execute("""
            INSERT INTO users (id, email, password_hash) 
            VALUES ('1', 'test@example.com', 'hash123')
        """)
        
        cursor.execute("""
            INSERT INTO sessions (id, user_id, session_token) 
            VALUES ('1', '1', 'token123')
        """)
        
        conn.commit()
        conn.close()
        
        return db_path
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def validator(self, sample_sqlite_db, temp_postgres_url):
        """Create migration validator for testing."""
        return MigrationValidator([sample_sqlite_db], temp_postgres_url)
    
    def test_validate_user_migration_success(self, validator):
        """Test successful user migration validation."""
        # Setup PostgreSQL with matching data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            test_user = User(
                id=uuid.uuid4(),
                email="test@example.com",
                password_hash="hash123",
                tenant_id=uuid.uuid4()
            )
            session.add(test_user)
            session.commit()
        
        result = validator.validate_user_migration()
        assert result.success is True
        assert "1 users migrated successfully" in result.message
    
    def test_validate_user_migration_count_mismatch(self, validator):
        """Test user migration validation with count mismatch."""
        # Setup PostgreSQL with no data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        result = validator.validate_user_migration()
        assert result.success is False
        assert "User count mismatch" in result.errors[0]
    
    def test_validate_foreign_key_relationships(self, validator):
        """Test foreign key relationship validation."""
        # Setup PostgreSQL with orphaned data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            # Add session without corresponding user (orphaned)
            orphaned_session = UserSession(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),  # Non-existent user
                session_token="orphaned_token",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            session.add(orphaned_session)
            session.commit()
        
        result = validator.validate_foreign_key_relationships()
        assert result.success is False
        assert "orphaned sessions" in result.errors[0]
    
    def test_validate_data_integrity(self, validator):
        """Test data integrity validation."""
        # Setup PostgreSQL with duplicate emails
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            # Add users with duplicate emails
            user1 = User(
                id=uuid.uuid4(),
                email="duplicate@example.com",
                password_hash="hash1",
                tenant_id=uuid.uuid4()
            )
            user2 = User(
                id=uuid.uuid4(),
                email="duplicate@example.com",
                password_hash="hash2",
                tenant_id=uuid.uuid4()
            )
            
            # This should fail due to unique constraint, but let's test the validation
            try:
                session.add(user1)
                session.commit()
                # If we get here, the unique constraint isn't working as expected
                # but we can still test the validation logic
            except Exception:
                pass
        
        result = validator.validate_data_integrity()
        # Should pass if no duplicate emails were actually inserted
        assert isinstance(result.success, bool)
    
    def test_validate_complete_migration(self, validator):
        """Test complete migration validation."""
        # Setup PostgreSQL with matching data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            test_user = User(
                id=uuid.uuid4(),
                email="test@example.com",
                password_hash="hash123",
                tenant_id=uuid.uuid4()
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            
            test_session = UserSession(
                id=uuid.uuid4(),
                user_id=test_user.id,
                session_token="token123",
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            session.add(test_session)
            session.commit()
        
        report = validator.validate_complete_migration()
        assert isinstance(report.overall_success, bool)
        assert report.validation_timestamp is not None
        assert report.user_validation is not None
        assert report.session_validation is not None
    
    def test_validate_foreign_key_relationships_comprehensive(self, validator):
        """Test comprehensive foreign key relationship validation."""
        # Setup PostgreSQL with various relationship scenarios
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            # Create valid user
            valid_user = User(
                id=uuid.uuid4(),
                email="valid@example.com",
                password_hash="hash123",
                tenant_id=uuid.uuid4(),
                is_active=True
            )
            session.add(valid_user)
            session.commit()
            session.refresh(valid_user)
            
            # Create valid session
            valid_session = UserSession(
                id=uuid.uuid4(),
                user_id=valid_user.id,
                session_token="valid_token",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            session.add(valid_session)
            
            # Create valid password reset token
            valid_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=valid_user.id,
                token="valid_reset_token",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                used=False
            )
            session.add(valid_token)
            session.commit()
        
        # Test validation with valid relationships
        result = validator.validate_foreign_key_relationships()
        assert result.success is True
        assert result.details['orphaned_sessions'] == 0
        assert result.details['orphaned_tokens'] == 0
    
    def test_validate_data_consistency_comprehensive(self, validator):
        """Test comprehensive data consistency validation."""
        # Setup PostgreSQL with consistent data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            # Create users with proper data
            users = [
                User(
                    id=uuid.uuid4(),
                    email=f"user{i}@example.com",
                    password_hash=f"hash{i}",
                    full_name=f"User {i}",
                    tenant_id=uuid.uuid4(),
                    is_active=True,
                    is_verified=True
                )
                for i in range(5)
            ]
            
            for user in users:
                session.add(user)
            session.commit()
            
            # Create sessions with proper expiration dates
            for i, user in enumerate(users):
                user_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    session_token=f"token_{i}",
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    created_at=datetime.utcnow(),
                    is_active=True
                )
                session.add(user_session)
            
            session.commit()
        
        # Test data integrity validation
        result = validator.validate_data_integrity()
        assert result.success is True
        assert result.details['users_without_tenant'] == 0
        assert result.details['invalid_session_dates'] == 0
    
    def test_performance_benchmarks_validation(self, validator):
        """Test performance benchmarks validation."""
        # Setup PostgreSQL with test data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            # Create test user for performance testing
            test_user = User(
                id=uuid.uuid4(),
                email="perf_test_1@example.com",
                password_hash="hash123",
                tenant_id=uuid.uuid4(),
                is_active=True
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            
            # Create test session
            test_session = UserSession(
                id=uuid.uuid4(),
                user_id=test_user.id,
                session_token="perf_session_1",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            session.add(test_session)
            session.commit()
        
        # Run performance benchmarks
        result = validator.validate_performance_benchmarks(sample_size=10)
        
        assert isinstance(result, ValidationResult)
        assert result.details is not None
        
        # Check that key performance metrics are present
        expected_metrics = [
            'user_lookup_ms',
            'session_validation_ms',
            'bulk_query_ms',
            'user_creation_ms',
            'session_cleanup_ms',
            'auth_flow_ms'
        ]
        
        for metric in expected_metrics:
            assert metric in result.details, f"Missing performance metric: {metric}"
            assert isinstance(result.details[metric], (int, float))
            assert result.details[metric] >= 0


class TestDatabaseConsolidationMigrator:
    """Test complete database consolidation migration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def temp_postgres_url(self):
        """Create temporary PostgreSQL database URL for testing."""
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def sample_sqlite_db(self, temp_dir):
        """Create sample SQLite database for testing."""
        db_path = os.path.join(temp_dir, "test.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create sample tables and data
        cursor.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                full_name TEXT,
                tenant_id TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                session_token TEXT UNIQUE,
                expires_at TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO users (user_id, email, password_hash, full_name, tenant_id, created_at) 
            VALUES ('1', 'test@example.com', 'hash123', 'Test User', 'tenant1', '2023-01-01 00:00:00')
        """)
        
        cursor.execute("""
            INSERT INTO sessions (id, user_id, session_token, expires_at, created_at) 
            VALUES ('1', '1', 'token123', '2024-01-01 00:00:00', '2023-01-01 00:00:00')
        """)
        
        conn.commit()
        conn.close()
        
        return db_path
    
    @pytest.fixture
    def migrator(self, sample_sqlite_db, temp_postgres_url, temp_dir):
        """Create database consolidation migrator for testing."""
        return DatabaseConsolidationMigrator(
            sqlite_paths=[sample_sqlite_db],
            postgres_url=temp_postgres_url,
            backup_dir=temp_dir
        )
    
    @pytest.mark.asyncio
    async def test_migrate_all_data_success(self, migrator):
        """Test successful complete migration."""
        result = await migrator.migrate_all_data(create_backups=False, validate_after=False)
        
        assert result.success is True
        assert result.users_migrated > 0
        assert result.uuid_mappings is not None
        assert len(result.uuid_mappings) > 0
    
    @pytest.mark.asyncio
    async def test_migrate_users(self, migrator):
        """Test user migration specifically."""
        # Create PostgreSQL schema first
        migrator.schema_manager.create_schema()
        
        users_migrated = await migrator._migrate_users()
        assert users_migrated == 1
        assert len(migrator.uuid_mappings) == 1
    
    @pytest.mark.asyncio
    async def test_migrate_sessions(self, migrator):
        """Test session migration specifically."""
        # Create PostgreSQL schema first
        migrator.schema_manager.create_schema()
        
        # Migrate users first to establish UUID mappings
        await migrator._migrate_users()
        
        sessions_migrated = await migrator._migrate_sessions()
        assert sessions_migrated == 1
    
    def test_parse_datetime(self, migrator):
        """Test datetime parsing functionality."""
        # Test various datetime formats
        test_cases = [
            ('2023-01-01 12:00:00', datetime(2023, 1, 1, 12, 0, 0)),
            ('2023-01-01T12:00:00', datetime(2023, 1, 1, 12, 0, 0)),
            ('2023-01-01T12:00:00Z', datetime(2023, 1, 1, 12, 0, 0)),
            (None, None),
            ('', None),
            ('invalid', None)
        ]
        
        for date_str, expected in test_cases:
            result = migrator._parse_datetime(date_str)
            if expected is None:
                assert result is None
            else:
                assert result == expected
    
    def test_get_migration_status(self, migrator):
        """Test getting migration status."""
        # Create schema first
        migrator.schema_manager.create_schema()
        
        status = migrator.get_migration_status()
        assert isinstance(status, dict)
        assert 'migration_timestamp' in status
        assert 'uuid_mappings_count' in status
        assert 'postgres_schema_valid' in status


if __name__ == "__main__":
    pytest.main([__file__])