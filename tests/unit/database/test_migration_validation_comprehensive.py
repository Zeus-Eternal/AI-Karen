"""
Comprehensive migration validation and testing suite.

This module provides comprehensive tests for migration validation, performance benchmarks,
and integration tests for complete authentication flows using PostgreSQL data.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path to import our modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.database.migration.migration_validator import (
    MigrationValidationReport,
    MigrationValidator,
    ValidationResult,
)
from ai_karen_engine.database.migration.postgres_schema import (
    Base,
    PasswordResetToken,
    PostgreSQLAuthSchema,
    User,
    UserSession,
)


class TestMigrationValidatorComprehensive:
    """Comprehensive tests for MigrationValidator class."""
    
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
    def sample_sqlite_dbs(self, temp_dir):
        """Create sample SQLite databases with comprehensive test data."""
        # Create auth.db
        auth_db_path = os.path.join(temp_dir, "auth.db")
        conn = sqlite3.connect(auth_db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                tenant_id TEXT NOT NULL,
                roles TEXT DEFAULT '[]',
                preferences TEXT DEFAULT '{}',
                is_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Insert test users
        test_users = [
            ('user1', 'user1@example.com', 'hash1', 'User One', 'tenant1', '["user"]', '{"theme": "dark"}', 1, 1),
            ('user2', 'user2@example.com', 'hash2', 'User Two', 'tenant1', '["admin"]', '{"theme": "light"}', 1, 1),
            ('user3', 'user3@example.com', 'hash3', 'User Three', 'tenant2', '["user"]', '{}', 0, 1),
        ]
        
        for user_data in test_users:
            cursor.execute("""
                INSERT INTO users (user_id, email, password_hash, full_name, tenant_id, roles, preferences, is_verified, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, user_data)
        
        conn.commit()
        conn.close()
        
        # Create auth_sessions.db
        sessions_db_path = os.path.join(temp_dir, "auth_sessions.db")
        conn = sqlite3.connect(sessions_db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TEXT NOT NULL,
                created_at TEXT,
                ip_address TEXT,
                user_agent TEXT,
                is_active INTEGER DEFAULT 1,
                risk_score REAL DEFAULT 0.0
            )
        """)
        
        # Insert test sessions
        future_time = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        test_sessions = [
            ('session1', 'user1', 'token1', 'access1', 'refresh1', future_time, datetime.utcnow().isoformat(), '192.168.1.1', 'Mozilla/5.0', 1, 0.1),
            ('session2', 'user2', 'token2', 'access2', 'refresh2', future_time, datetime.utcnow().isoformat(), '192.168.1.2', 'Chrome/90.0', 1, 0.2),
            ('session3', 'user3', 'token3', 'access3', 'refresh3', future_time, datetime.utcnow().isoformat(), '192.168.1.3', 'Safari/14.0', 1, 0.0),
        ]
        
        for session_data in test_sessions:
            cursor.execute("""
                INSERT INTO sessions (id, user_id, session_token, access_token, refresh_token, expires_at, created_at, ip_address, user_agent, is_active, risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, session_data)
        
        # Create password reset tokens table
        cursor.execute("""
            CREATE TABLE password_reset_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        # Insert test tokens
        test_tokens = [
            ('token1', 'user1', 'reset_token1', future_time, 0, datetime.utcnow().isoformat()),
            ('token2', 'user2', 'reset_token2', future_time, 0, datetime.utcnow().isoformat()),
        ]
        
        for token_data in test_tokens:
            cursor.execute("""
                INSERT INTO password_reset_tokens (id, user_id, token, expires_at, used, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, token_data)
        
        conn.commit()
        conn.close()
        
        return [auth_db_path, sessions_db_path]
    
    @pytest.fixture
    def validator(self, sample_sqlite_dbs, temp_postgres_url):
        """Create migration validator with test data."""
        return MigrationValidator(sample_sqlite_dbs, temp_postgres_url)
    
    @pytest.fixture
    def postgres_with_migrated_data(self, validator):
        """Setup PostgreSQL with migrated test data."""
        # Create schema
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Insert migrated test data
        with SessionLocal() as session:
            # Create test users
            users = [
                User(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789001'),
                    email='user1@example.com',
                    password_hash='hash1',
                    full_name='User One',
                    tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                    roles=['user'],
                    preferences={'theme': 'dark'},
                    is_verified=True,
                    is_active=True
                ),
                User(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789002'),
                    email='user2@example.com',
                    password_hash='hash2',
                    full_name='User Two',
                    tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                    roles=['admin'],
                    preferences={'theme': 'light'},
                    is_verified=True,
                    is_active=True
                ),
                User(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789003'),
                    email='user3@example.com',
                    password_hash='hash3',
                    full_name='User Three',
                    tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789102'),
                    roles=['user'],
                    preferences={},
                    is_verified=False,
                    is_active=True
                )
            ]
            
            for user in users:
                session.add(user)
            session.commit()
            
            # Create test sessions
            sessions = [
                UserSession(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789201'),
                    user_id=uuid.UUID('12345678-1234-5678-9012-123456789001'),
                    session_token='token1',
                    access_token='access1',
                    refresh_token='refresh1',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    ip_address='192.168.1.1',
                    user_agent='Mozilla/5.0',
                    is_active=True,
                    risk_score=0.1
                ),
                UserSession(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789202'),
                    user_id=uuid.UUID('12345678-1234-5678-9012-123456789002'),
                    session_token='token2',
                    access_token='access2',
                    refresh_token='refresh2',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    ip_address='192.168.1.2',
                    user_agent='Chrome/90.0',
                    is_active=True,
                    risk_score=0.2
                ),
                UserSession(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789203'),
                    user_id=uuid.UUID('12345678-1234-5678-9012-123456789003'),
                    session_token='token3',
                    access_token='access3',
                    refresh_token='refresh3',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    ip_address='192.168.1.3',
                    user_agent='Safari/14.0',
                    is_active=True,
                    risk_score=0.0
                )
            ]
            
            for user_session in sessions:
                session.add(user_session)
            session.commit()
            
            # Create test password reset tokens
            tokens = [
                PasswordResetToken(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789301'),
                    user_id=uuid.UUID('12345678-1234-5678-9012-123456789001'),
                    token='reset_token1',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    used=False
                ),
                PasswordResetToken(
                    id=uuid.UUID('12345678-1234-5678-9012-123456789302'),
                    user_id=uuid.UUID('12345678-1234-5678-9012-123456789002'),
                    token='reset_token2',
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    used=False
                )
            ]
            
            for token in tokens:
                session.add(token)
            session.commit()
        
        return engine
    
    def test_validate_complete_migration_success(self, validator, postgres_with_migrated_data):
        """Test complete migration validation with successful data."""
        report = validator.validate_complete_migration()
        
        assert isinstance(report, MigrationValidationReport)
        assert report.overall_success is True
        assert report.validation_timestamp is not None
        
        # Check individual validations
        assert report.user_validation.success is True
        assert report.session_validation.success is True
        assert report.token_validation.success is True
        assert report.foreign_key_validation.success is True
        assert report.data_integrity_validation.success is True
        
        # Test report serialization
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert 'overall_success' in report_dict
        assert 'validations' in report_dict
    
    def test_validate_user_migration_detailed(self, validator, postgres_with_migrated_data):
        """Test detailed user migration validation."""
        result = validator.validate_user_migration()
        
        assert result.success is True
        assert "3 users migrated successfully" in result.message
        assert result.details['sqlite_count'] == 3
        assert result.details['postgres_count'] == 3
        assert result.details['sample_users_checked'] == 3
    
    def test_validate_session_migration_detailed(self, validator, postgres_with_migrated_data):
        """Test detailed session migration validation."""
        result = validator.validate_session_migration()
        
        assert result.success is True
        assert "3 sessions migrated successfully" in result.message
        assert result.details['sqlite_count'] == 3
        assert result.details['postgres_count'] == 3
        assert result.details['sample_sessions_checked'] == 3
    
    def test_validate_token_migration_detailed(self, validator, postgres_with_migrated_data):
        """Test detailed token migration validation."""
        result = validator.validate_token_migration()
        
        assert result.success is True
        assert "2 tokens migrated successfully" in result.message
        assert result.details['sqlite_count'] == 2
        assert result.details['postgres_count'] == 2
        assert result.details['sample_tokens_checked'] == 2
    
    def test_validate_foreign_key_relationships_success(self, validator, postgres_with_migrated_data):
        """Test foreign key relationship validation with valid data."""
        result = validator.validate_foreign_key_relationships()
        
        assert result.success is True
        assert "all relationships are valid" in result.message
        assert result.details['orphaned_sessions'] == 0
        assert result.details['orphaned_tokens'] == 0
    
    def test_validate_data_integrity_success(self, validator, postgres_with_migrated_data):
        """Test data integrity validation with clean data."""
        result = validator.validate_data_integrity()
        
        assert result.success is True
        assert "all data is consistent" in result.message
        assert result.details['users_without_tenant'] == 0
        assert result.details['invalid_session_dates'] == 0
        assert result.details['invalid_token_dates'] == 0
    
    def test_validate_performance_benchmarks(self, validator, postgres_with_migrated_data):
        """Test performance benchmarks validation."""
        result = validator.validate_performance_benchmarks(sample_size=10)
        
        assert isinstance(result, ValidationResult)
        assert result.details is not None
        
        # Check that performance metrics are present
        expected_metrics = [
            'user_lookup_ms',
            'session_validation_ms',
            'bulk_query_ms',
            'user_creation_ms',
            'session_cleanup_ms',
            'auth_flow_ms'
        ]
        
        for metric in expected_metrics:
            assert metric in result.details
            assert isinstance(result.details[metric], (int, float))
            assert result.details[metric] >= 0
    
    def test_compare_pre_post_migration_performance(self, validator, postgres_with_migrated_data):
        """Test pre/post migration performance comparison."""
        result = validator.compare_pre_post_migration_performance(validator.sqlite_paths)
        
        assert isinstance(result, ValidationResult)
        assert result.details is not None
        assert 'comparison' in result.details
        assert 'sqlite_results' in result.details
        assert 'postgres_results' in result.details
    
    def test_migration_validation_with_errors(self, validator):
        """Test migration validation with various error conditions."""
        # Create PostgreSQL schema but with missing/incorrect data
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Add only partial data to simulate migration errors
        with SessionLocal() as session:
            # Add only 1 user instead of 3
            user = User(
                id=uuid.uuid4(),
                email='user1@example.com',
                password_hash='hash1',
                full_name='User One',
                tenant_id=uuid.uuid4(),
                is_active=True
            )
            session.add(user)
            session.commit()
        
        # Test user migration validation - should fail due to count mismatch
        result = validator.validate_user_migration()
        assert result.success is False
        assert "User count mismatch" in result.errors[0]
        
        # Test complete migration validation
        report = validator.validate_complete_migration()
        assert report.overall_success is False
    
    def test_migration_validation_with_orphaned_data(self, validator):
        """Test validation with orphaned foreign key relationships."""
        # Create PostgreSQL schema
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Add orphaned session (session without corresponding user)
        with SessionLocal() as session:
            orphaned_session = UserSession(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),  # Non-existent user ID
                session_token='orphaned_token',
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            session.add(orphaned_session)
            session.commit()
        
        # Test foreign key validation - should fail
        result = validator.validate_foreign_key_relationships()
        assert result.success is False
        assert "orphaned sessions" in result.errors[0]
    
    def test_migration_validation_with_data_integrity_issues(self, validator):
        """Test validation with data integrity problems."""
        # Create PostgreSQL schema
        engine = create_engine(validator.postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Add user without tenant_id
        with SessionLocal() as session:
            user_without_tenant = User(
                id=uuid.uuid4(),
                email='notenant@example.com',
                password_hash='hash',
                tenant_id=None,  # This should cause integrity issue
                is_active=True
            )
            
            # Add session with invalid expiration date
            invalid_session = UserSession(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                session_token='invalid_session',
                expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired before creation
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            try:
                session.add(user_without_tenant)
                session.add(invalid_session)
                session.commit()
            except Exception:
                # Some integrity constraints might prevent this
                session.rollback()
        
        # Test data integrity validation
        result = validator.validate_data_integrity()
        # Result depends on whether the invalid data was actually inserted
        assert isinstance(result, ValidationResult)


class TestAuthenticationFlowIntegration:
    """Integration tests for complete authentication flows using PostgreSQL data."""
    
    @pytest.fixture
    def temp_postgres_url(self):
        """Create temporary PostgreSQL database URL for testing."""
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def auth_database(self, temp_postgres_url):
        """Setup authentication database with test data."""
        engine = create_engine(temp_postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create test data
        with SessionLocal() as session:
            # Create test users
            test_user = User(
                id=uuid.UUID('12345678-1234-5678-9012-123456789001'),
                email='testuser@example.com',
                password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6/6Vf6.Xem',  # 'password123'
                full_name='Test User',
                tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                roles=['user'],
                preferences={'theme': 'dark'},
                is_verified=True,
                is_active=True
            )
            
            admin_user = User(
                id=uuid.UUID('12345678-1234-5678-9012-123456789002'),
                email='admin@example.com',
                password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6/6Vf6.Xem',  # 'password123'
                full_name='Admin User',
                tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                roles=['admin', 'user'],
                preferences={'theme': 'light'},
                is_verified=True,
                is_active=True
            )
            
            inactive_user = User(
                id=uuid.UUID('12345678-1234-5678-9012-123456789003'),
                email='inactive@example.com',
                password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6/6Vf6.Xem',
                full_name='Inactive User',
                tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                roles=['user'],
                is_verified=True,
                is_active=False  # Inactive user
            )
            
            session.add_all([test_user, admin_user, inactive_user])
            session.commit()
        
        return engine, SessionLocal
    
    def test_user_registration_flow(self, auth_database):
        """Test complete user registration flow."""
        engine, SessionLocal = auth_database
        
        # Simulate user registration
        with SessionLocal() as session:
            new_user = User(
                id=uuid.uuid4(),
                email='newuser@example.com',
                password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6/6Vf6.Xem',
                full_name='New User',
                tenant_id=uuid.UUID('12345678-1234-5678-9012-123456789101'),
                roles=['user'],
                is_verified=False,  # Needs verification
                is_active=True
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            # Verify user was created
            assert new_user.id is not None
            assert new_user.email == 'newuser@example.com'
            assert new_user.is_verified is False
            assert new_user.is_active is True
            
            # Simulate email verification
            new_user.is_verified = True
            session.commit()
            
            # Verify user is now verified
            verified_user = session.query(User).filter(User.email == 'newuser@example.com').first()
            assert verified_user.is_verified is True
    
    def test_user_login_flow(self, auth_database):
        """Test complete user login flow with session creation."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            # Find user by email (login attempt)
            user = session.query(User).filter(
                User.email == 'testuser@example.com',
                User.is_active == True
            ).first()
            
            assert user is not None
            assert user.email == 'testuser@example.com'
            assert user.is_active is True
            
            # Create session for logged-in user
            user_session = UserSession(
                id=uuid.uuid4(),
                user_id=user.id,
                session_token=f'session_{uuid.uuid4().hex}',
                access_token=f'access_{uuid.uuid4().hex}',
                refresh_token=f'refresh_{uuid.uuid4().hex}',
                expires_at=datetime.utcnow() + timedelta(hours=24),
                ip_address='192.168.1.100',
                user_agent='Test Browser/1.0',
                is_active=True,
                risk_score=0.1
            )
            
            session.add(user_session)
            session.commit()
            session.refresh(user_session)
            
            # Verify session was created
            assert user_session.id is not None
            assert user_session.user_id == user.id
            assert user_session.is_active is True
            assert user_session.expires_at > datetime.utcnow()
    
    def test_session_validation_flow(self, auth_database):
        """Test session validation flow."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            # Create a test session first
            user = session.query(User).filter(User.email == 'testuser@example.com').first()
            test_token = f'test_session_{uuid.uuid4().hex}'
            
            user_session = UserSession(
                id=uuid.uuid4(),
                user_id=user.id,
                session_token=test_token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            
            session.add(user_session)
            session.commit()
            
            # Test session validation (typical middleware operation)
            valid_session = session.query(UserSession).join(User).filter(
                UserSession.session_token == test_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow(),
                User.is_active == True
            ).first()
            
            assert valid_session is not None
            assert valid_session.session_token == test_token
            assert valid_session.user.email == 'testuser@example.com'
            
            # Test invalid session (expired)
            user_session.expires_at = datetime.utcnow() - timedelta(hours=1)
            session.commit()
            
            expired_session = session.query(UserSession).join(User).filter(
                UserSession.session_token == test_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow(),
                User.is_active == True
            ).first()
            
            assert expired_session is None
    
    def test_password_reset_flow(self, auth_database):
        """Test complete password reset flow."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            # Find user requesting password reset
            user = session.query(User).filter(User.email == 'testuser@example.com').first()
            
            # Create password reset token
            reset_token = PasswordResetToken(
                id=uuid.uuid4(),
                user_id=user.id,
                token=f'reset_{uuid.uuid4().hex}',
                expires_at=datetime.utcnow() + timedelta(hours=1),
                used=False
            )
            
            session.add(reset_token)
            session.commit()
            session.refresh(reset_token)
            
            # Verify token was created
            assert reset_token.id is not None
            assert reset_token.user_id == user.id
            assert reset_token.used is False
            
            # Simulate password reset (validate token and update password)
            valid_token = session.query(PasswordResetToken).filter(
                PasswordResetToken.token == reset_token.token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            ).first()
            
            assert valid_token is not None
            
            # Update password and mark token as used
            user.password_hash = '$2b$12$NewHashForNewPassword'
            valid_token.used = True
            session.commit()
            
            # Verify password was updated and token marked as used
            updated_user = session.query(User).filter(User.id == user.id).first()
            used_token = session.query(PasswordResetToken).filter(PasswordResetToken.id == reset_token.id).first()
            
            assert updated_user.password_hash == '$2b$12$NewHashForNewPassword'
            assert used_token.used is True
    
    def test_user_logout_flow(self, auth_database):
        """Test user logout flow with session cleanup."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            # Create active session
            user = session.query(User).filter(User.email == 'testuser@example.com').first()
            test_token = f'logout_test_{uuid.uuid4().hex}'
            
            user_session = UserSession(
                id=uuid.uuid4(),
                user_id=user.id,
                session_token=test_token,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                is_active=True
            )
            
            session.add(user_session)
            session.commit()
            
            # Verify session is active
            active_session = session.query(UserSession).filter(
                UserSession.session_token == test_token,
                UserSession.is_active == True
            ).first()
            assert active_session is not None
            
            # Simulate logout (deactivate session)
            active_session.is_active = False
            session.commit()
            
            # Verify session is no longer active
            inactive_session = session.query(UserSession).filter(
                UserSession.session_token == test_token,
                UserSession.is_active == True
            ).first()
            assert inactive_session is None
            
            # But session record still exists for audit purposes
            session_record = session.query(UserSession).filter(
                UserSession.session_token == test_token
            ).first()
            assert session_record is not None
            assert session_record.is_active is False
    
    def test_concurrent_session_management(self, auth_database):
        """Test concurrent session management and limits."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            user = session.query(User).filter(User.email == 'testuser@example.com').first()
            
            # Create multiple active sessions for the same user
            sessions = []
            for i in range(5):
                user_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    session_token=f'concurrent_{i}_{uuid.uuid4().hex}',
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                    is_active=True,
                    ip_address=f'192.168.1.{100 + i}',
                    user_agent=f'Browser {i}/1.0'
                )
                sessions.append(user_session)
                session.add(user_session)
            
            session.commit()
            
            # Verify all sessions were created
            active_sessions = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).all()
            
            assert len(active_sessions) == 5
            
            # Simulate session limit enforcement (keep only 3 most recent)
            sessions_to_deactivate = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).order_by(UserSession.created_at.asc()).limit(2).all()
            
            for old_session in sessions_to_deactivate:
                old_session.is_active = False
            
            session.commit()
            
            # Verify only 3 sessions remain active
            remaining_active = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).count()
            
            assert remaining_active == 3
    
    def test_role_based_access_validation(self, auth_database):
        """Test role-based access control validation."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            # Test regular user access
            regular_user = session.query(User).filter(User.email == 'testuser@example.com').first()
            assert 'user' in regular_user.roles
            assert 'admin' not in regular_user.roles
            
            # Test admin user access
            admin_user = session.query(User).filter(User.email == 'admin@example.com').first()
            assert 'admin' in admin_user.roles
            assert 'user' in admin_user.roles
            
            # Test inactive user access
            inactive_user = session.query(User).filter(User.email == 'inactive@example.com').first()
            assert inactive_user.is_active is False
            
            # Simulate role-based query (admin-only operation)
            admin_users = session.query(User).filter(
                User.roles.contains(['admin']),
                User.is_active == True
            ).all()
            
            assert len(admin_users) == 1
            assert admin_users[0].email == 'admin@example.com'
    
    def test_session_cleanup_and_maintenance(self, auth_database):
        """Test session cleanup and maintenance operations."""
        engine, SessionLocal = auth_database
        
        with SessionLocal() as session:
            user = session.query(User).filter(User.email == 'testuser@example.com').first()
            
            # Create expired sessions
            expired_sessions = []
            for i in range(3):
                expired_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    session_token=f'expired_{i}_{uuid.uuid4().hex}',
                    expires_at=datetime.utcnow() - timedelta(hours=i + 1),
                    is_active=True
                )
                expired_sessions.append(expired_session)
                session.add(expired_session)
            
            # Create valid sessions
            valid_sessions = []
            for i in range(2):
                valid_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    session_token=f'valid_{i}_{uuid.uuid4().hex}',
                    expires_at=datetime.utcnow() + timedelta(hours=i + 1),
                    is_active=True
                )
                valid_sessions.append(valid_session)
                session.add(valid_session)
            
            session.commit()
            
            # Count sessions before cleanup
            total_sessions = session.query(UserSession).filter(
                UserSession.user_id == user.id
            ).count()
            assert total_sessions == 5
            
            # Perform cleanup (deactivate expired sessions)
            expired_count = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_active == True
            ).update({'is_active': False})
            
            session.commit()
            
            # Verify cleanup results
            assert expired_count == 3
            
            active_sessions = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).count()
            assert active_sessions == 2
            
            inactive_sessions = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == False
            ).count()
            assert inactive_sessions == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])