"""
Migration validation utilities for database consolidation.

This module provides comprehensive validation tools to ensure data integrity
and consistency after migrating from SQLite to PostgreSQL.
"""

import asyncio
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@dataclass
class ValidationResult:
    """Result of a validation check."""
    success: bool
    message: str
    details: Optional[Dict] = None
    errors: Optional[List[str]] = None


@dataclass
class MigrationValidationReport:
    """Comprehensive migration validation report."""
    overall_success: bool
    validation_timestamp: datetime
    user_validation: ValidationResult
    session_validation: ValidationResult
    token_validation: ValidationResult
    foreign_key_validation: ValidationResult
    data_integrity_validation: ValidationResult
    performance_validation: Optional[ValidationResult] = None
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary."""
        return {
            'overall_success': self.overall_success,
            'validation_timestamp': self.validation_timestamp.isoformat(),
            'validations': {
                'users': {
                    'success': self.user_validation.success,
                    'message': self.user_validation.message,
                    'details': self.user_validation.details,
                    'errors': self.user_validation.errors
                },
                'sessions': {
                    'success': self.session_validation.success,
                    'message': self.session_validation.message,
                    'details': self.session_validation.details,
                    'errors': self.session_validation.errors
                },
                'tokens': {
                    'success': self.token_validation.success,
                    'message': self.token_validation.message,
                    'details': self.token_validation.details,
                    'errors': self.token_validation.errors
                },
                'foreign_keys': {
                    'success': self.foreign_key_validation.success,
                    'message': self.foreign_key_validation.message,
                    'details': self.foreign_key_validation.details,
                    'errors': self.foreign_key_validation.errors
                },
                'data_integrity': {
                    'success': self.data_integrity_validation.success,
                    'message': self.data_integrity_validation.message,
                    'details': self.data_integrity_validation.details,
                    'errors': self.data_integrity_validation.errors
                }
            }
        }


class MigrationValidator:
    """
    Comprehensive migration validator for database consolidation.
    
    Validates that data has been correctly migrated from SQLite to PostgreSQL
    with proper relationships and data integrity maintained.
    """
    
    def __init__(self, sqlite_paths: List[str], postgres_url: str):
        """
        Initialize migration validator.
        
        Args:
            sqlite_paths: List of SQLite database file paths
            postgres_url: PostgreSQL connection URL
        """
        self.sqlite_paths = sqlite_paths
        self.postgres_url = postgres_url
        self.postgres_engine = create_engine(postgres_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.postgres_engine)
        self.logger = logging.getLogger(__name__)
    
    def validate_complete_migration(self) -> MigrationValidationReport:
        """
        Perform comprehensive migration validation.
        
        Returns:
            Complete validation report
        """
        self.logger.info("Starting comprehensive migration validation")
        
        # Perform individual validations
        user_result = self.validate_user_migration()
        session_result = self.validate_session_migration()
        token_result = self.validate_token_migration()
        fk_result = self.validate_foreign_key_relationships()
        integrity_result = self.validate_data_integrity()
        
        # Determine overall success
        overall_success = all([
            user_result.success,
            session_result.success,
            token_result.success,
            fk_result.success,
            integrity_result.success
        ])
        
        report = MigrationValidationReport(
            overall_success=overall_success,
            validation_timestamp=datetime.utcnow(),
            user_validation=user_result,
            session_validation=session_result,
            token_validation=token_result,
            foreign_key_validation=fk_result,
            data_integrity_validation=integrity_result
        )
        
        if overall_success:
            self.logger.info("Migration validation completed successfully")
        else:
            self.logger.error("Migration validation failed - see report for details")
        
        return report
    
    def validate_user_migration(self) -> ValidationResult:
        """
        Validate user data migration.
        
        Returns:
            Validation result for user data
        """
        try:
            self.logger.info("Validating user migration")
            
            # Count users in SQLite databases
            sqlite_user_count = 0
            sqlite_users = {}
            
            for sqlite_path in self.sqlite_paths:
                try:
                    conn = sqlite3.connect(sqlite_path)
                    cursor = conn.cursor()
                    
                    # Check if users table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'")
                    user_tables = cursor.fetchall()
                    
                    for table_tuple in user_tables:
                        table_name = table_tuple[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        sqlite_user_count += count
                        
                        # Get sample user data for comparison
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        columns = [description[0] for description in cursor.description]
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            user_data = dict(zip(columns, row))
                            if 'email' in user_data:
                                sqlite_users[user_data['email']] = user_data
                    
                    conn.close()
                    
                except Exception as e:
                    self.logger.warning(f"Could not read SQLite database {sqlite_path}: {e}")
            
            # Count users in PostgreSQL
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users"))
                postgres_user_count = result.scalar()
                
                # Get sample PostgreSQL users for comparison
                result = conn.execute(text("SELECT * FROM auth_users LIMIT 5"))
                postgres_users = {}
                for row in result:
                    postgres_users[row.email] = dict(row._mapping)
            
            # Validate counts
            errors = []
            if sqlite_user_count != postgres_user_count:
                errors.append(f"User count mismatch: SQLite={sqlite_user_count}, PostgreSQL={postgres_user_count}")
            
            # Validate sample user data
            for email, sqlite_user in sqlite_users.items():
                if email in postgres_users:
                    postgres_user = postgres_users[email]
                    
                    # Check critical fields
                    if sqlite_user.get('email') != postgres_user.get('email'):
                        errors.append(f"Email mismatch for user {email}")
                    
                    if sqlite_user.get('password_hash') != postgres_user.get('password_hash'):
                        errors.append(f"Password hash mismatch for user {email}")
                else:
                    errors.append(f"User {email} found in SQLite but not in PostgreSQL")
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"User migration validation failed with {len(errors)} errors",
                    details={
                        'sqlite_count': sqlite_user_count,
                        'postgres_count': postgres_user_count,
                        'sample_users_checked': len(sqlite_users)
                    },
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message=f"User migration validation passed - {postgres_user_count} users migrated successfully",
                    details={
                        'sqlite_count': sqlite_user_count,
                        'postgres_count': postgres_user_count,
                        'sample_users_checked': len(sqlite_users)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"User migration validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"User migration validation error: {e}",
                errors=[str(e)]
            )
    
    def validate_session_migration(self) -> ValidationResult:
        """
        Validate session data migration.
        
        Returns:
            Validation result for session data
        """
        try:
            self.logger.info("Validating session migration")
            
            # Count sessions in SQLite databases
            sqlite_session_count = 0
            sqlite_sessions = {}
            
            for sqlite_path in self.sqlite_paths:
                try:
                    conn = sqlite3.connect(sqlite_path)
                    cursor = conn.cursor()
                    
                    # Check if sessions table exists
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%session%'")
                    session_tables = cursor.fetchall()
                    
                    for table_tuple in session_tables:
                        table_name = table_tuple[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        sqlite_session_count += count
                        
                        # Get sample session data
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        columns = [description[0] for description in cursor.description]
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            session_data = dict(zip(columns, row))
                            if 'session_token' in session_data:
                                sqlite_sessions[session_data['session_token']] = session_data
                    
                    conn.close()
                    
                except Exception as e:
                    self.logger.warning(f"Could not read SQLite database {sqlite_path}: {e}")
            
            # Count sessions in PostgreSQL
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM auth_sessions"))
                postgres_session_count = result.scalar()
                
                # Get sample PostgreSQL sessions
                result = conn.execute(text("SELECT * FROM auth_sessions LIMIT 5"))
                postgres_sessions = {}
                for row in result:
                    postgres_sessions[row.session_token] = dict(row._mapping)
            
            # Validate counts and data
            errors = []
            if sqlite_session_count != postgres_session_count:
                errors.append(f"Session count mismatch: SQLite={sqlite_session_count}, PostgreSQL={postgres_session_count}")
            
            # Validate sample session data
            for token, sqlite_session in sqlite_sessions.items():
                if token in postgres_sessions:
                    postgres_session = postgres_sessions[token]
                    
                    # Check critical fields
                    if sqlite_session.get('user_id') != str(postgres_session.get('user_id')):
                        errors.append(f"User ID mismatch for session {token}")
                else:
                    errors.append(f"Session {token} found in SQLite but not in PostgreSQL")
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"Session migration validation failed with {len(errors)} errors",
                    details={
                        'sqlite_count': sqlite_session_count,
                        'postgres_count': postgres_session_count,
                        'sample_sessions_checked': len(sqlite_sessions)
                    },
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message=f"Session migration validation passed - {postgres_session_count} sessions migrated successfully",
                    details={
                        'sqlite_count': sqlite_session_count,
                        'postgres_count': postgres_session_count,
                        'sample_sessions_checked': len(sqlite_sessions)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Session migration validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Session migration validation error: {e}",
                errors=[str(e)]
            )
    
    def validate_token_migration(self) -> ValidationResult:
        """
        Validate password reset token migration.
        
        Returns:
            Validation result for token data
        """
        try:
            self.logger.info("Validating token migration")
            
            # Count tokens in SQLite databases
            sqlite_token_count = 0
            sqlite_tokens = {}
            
            for sqlite_path in self.sqlite_paths:
                try:
                    conn = sqlite3.connect(sqlite_path)
                    cursor = conn.cursor()
                    
                    # Check if token tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%token%'")
                    token_tables = cursor.fetchall()
                    
                    for table_tuple in token_tables:
                        table_name = table_tuple[0]
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        sqlite_token_count += count
                        
                        # Get sample token data
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        columns = [description[0] for description in cursor.description]
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            token_data = dict(zip(columns, row))
                            if 'token' in token_data:
                                sqlite_tokens[token_data['token']] = token_data
                    
                    conn.close()
                    
                except Exception as e:
                    self.logger.warning(f"Could not read SQLite database {sqlite_path}: {e}")
            
            # Count tokens in PostgreSQL
            with self.postgres_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM password_reset_tokens"))
                postgres_token_count = result.scalar()
                
                # Get sample PostgreSQL tokens
                result = conn.execute(text("SELECT * FROM password_reset_tokens LIMIT 5"))
                postgres_tokens = {}
                for row in result:
                    postgres_tokens[row.token] = dict(row._mapping)
            
            # Validate counts and data
            errors = []
            if sqlite_token_count != postgres_token_count:
                errors.append(f"Token count mismatch: SQLite={sqlite_token_count}, PostgreSQL={postgres_token_count}")
            
            # Validate sample token data
            for token, sqlite_token in sqlite_tokens.items():
                if token in postgres_tokens:
                    postgres_token = postgres_tokens[token]
                    
                    # Check critical fields
                    if sqlite_token.get('user_id') != str(postgres_token.get('user_id')):
                        errors.append(f"User ID mismatch for token {token}")
                else:
                    errors.append(f"Token {token} found in SQLite but not in PostgreSQL")
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"Token migration validation failed with {len(errors)} errors",
                    details={
                        'sqlite_count': sqlite_token_count,
                        'postgres_count': postgres_token_count,
                        'sample_tokens_checked': len(sqlite_tokens)
                    },
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message=f"Token migration validation passed - {postgres_token_count} tokens migrated successfully",
                    details={
                        'sqlite_count': sqlite_token_count,
                        'postgres_count': postgres_token_count,
                        'sample_tokens_checked': len(sqlite_tokens)
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Token migration validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Token migration validation error: {e}",
                errors=[str(e)]
            )
    
    def validate_foreign_key_relationships(self) -> ValidationResult:
        """
        Validate foreign key relationships in PostgreSQL.
        
        Returns:
            Validation result for foreign key integrity
        """
        try:
            self.logger.info("Validating foreign key relationships")
            
            errors = []
            
            with self.postgres_engine.connect() as conn:
                # Check for orphaned sessions (sessions without valid users)
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM auth_sessions s 
                    LEFT JOIN auth_users u ON s.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_sessions = result.scalar()
                
                if orphaned_sessions > 0:
                    errors.append(f"Found {orphaned_sessions} orphaned sessions without valid users")
                
                # Check for orphaned password reset tokens
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM password_reset_tokens t 
                    LEFT JOIN auth_users u ON t.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_tokens = result.scalar()
                
                if orphaned_tokens > 0:
                    errors.append(f"Found {orphaned_tokens} orphaned password reset tokens without valid users")
                
                # Check for orphaned user identities
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM user_identities i 
                    LEFT JOIN auth_users u ON i.user_id = u.id 
                    WHERE u.id IS NULL
                """))
                orphaned_identities = result.scalar()
                
                if orphaned_identities > 0:
                    errors.append(f"Found {orphaned_identities} orphaned user identities without valid users")
                
                # Check for user identities without valid providers
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM user_identities i 
                    LEFT JOIN auth_providers p ON i.provider_id = p.id 
                    WHERE p.id IS NULL
                """))
                orphaned_provider_identities = result.scalar()
                
                if orphaned_provider_identities > 0:
                    errors.append(f"Found {orphaned_provider_identities} user identities without valid providers")
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"Foreign key validation failed with {len(errors)} errors",
                    details={
                        'orphaned_sessions': orphaned_sessions,
                        'orphaned_tokens': orphaned_tokens,
                        'orphaned_identities': orphaned_identities,
                        'orphaned_provider_identities': orphaned_provider_identities
                    },
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message="Foreign key validation passed - all relationships are valid",
                    details={
                        'orphaned_sessions': 0,
                        'orphaned_tokens': 0,
                        'orphaned_identities': 0,
                        'orphaned_provider_identities': 0
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Foreign key validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Foreign key validation error: {e}",
                errors=[str(e)]
            )
    
    def validate_data_integrity(self) -> ValidationResult:
        """
        Validate overall data integrity and consistency.
        
        Returns:
            Validation result for data integrity
        """
        try:
            self.logger.info("Validating data integrity")
            
            errors = []
            details = {}
            
            with self.postgres_engine.connect() as conn:
                # Check for duplicate emails
                result = conn.execute(text("""
                    SELECT email, COUNT(*) as count 
                    FROM auth_users 
                    GROUP BY email 
                    HAVING COUNT(*) > 1
                """))
                duplicate_emails = result.fetchall()
                
                if duplicate_emails:
                    errors.append(f"Found {len(duplicate_emails)} duplicate email addresses")
                    details['duplicate_emails'] = [dict(row._mapping) for row in duplicate_emails]
                
                # Check for users without tenant_id
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users WHERE tenant_id IS NULL"))
                users_without_tenant = result.scalar()
                
                if users_without_tenant > 0:
                    errors.append(f"Found {users_without_tenant} users without tenant_id")
                
                # Check for sessions with invalid expiration dates
                result = conn.execute(text("SELECT COUNT(*) FROM auth_sessions WHERE expires_at < created_at"))
                invalid_session_dates = result.scalar()
                
                if invalid_session_dates > 0:
                    errors.append(f"Found {invalid_session_dates} sessions with invalid expiration dates")
                
                # Check for password reset tokens with invalid expiration dates
                result = conn.execute(text("SELECT COUNT(*) FROM password_reset_tokens WHERE expires_at < created_at"))
                invalid_token_dates = result.scalar()
                
                if invalid_token_dates > 0:
                    errors.append(f"Found {invalid_token_dates} password reset tokens with invalid expiration dates")
                
                # Check for users with empty password hashes
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users WHERE password_hash IS NULL OR password_hash = ''"))
                users_without_password = result.scalar()
                
                details.update({
                    'users_without_tenant': users_without_tenant,
                    'invalid_session_dates': invalid_session_dates,
                    'invalid_token_dates': invalid_token_dates,
                    'users_without_password': users_without_password
                })
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"Data integrity validation failed with {len(errors)} errors",
                    details=details,
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message="Data integrity validation passed - all data is consistent",
                    details=details
                )
                
        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Data integrity validation error: {e}",
                errors=[str(e)]
            )
    
    def validate_performance_benchmarks(self, sample_size: int = 1000) -> ValidationResult:
        """
        Validate that PostgreSQL performance meets requirements.
        
        Args:
            sample_size: Number of sample records to create for testing
        
        Returns:
            Validation result for performance benchmarks
        """
        try:
            self.logger.info(f"Running performance benchmarks with {sample_size} sample records")
            
            performance_results = {}
            errors = []
            
            # Create sample data for performance testing
            self._create_performance_test_data(sample_size)
            
            with self.postgres_engine.connect() as conn:
                # Test user lookup by email performance (indexed query)
                start_time = datetime.utcnow()
                result = conn.execute(text("SELECT * FROM auth_users WHERE email = 'perf_test_1@example.com' LIMIT 1"))
                result.fetchone()
                user_lookup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['user_lookup_ms'] = user_lookup_time
                
                # Test session validation performance (join query)
                start_time = datetime.utcnow()
                result = conn.execute(text("""
                    SELECT u.* FROM auth_users u 
                    JOIN auth_sessions s ON u.id = s.user_id 
                    WHERE s.session_token = 'perf_session_1' AND s.is_active = true 
                    LIMIT 1
                """))
                result.fetchone()
                session_validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['session_validation_ms'] = session_validation_time
                
                # Test bulk user query performance
                start_time = datetime.utcnow()
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users WHERE is_active = true"))
                result.scalar()
                bulk_query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['bulk_query_ms'] = bulk_query_time
                
                # Test user creation performance
                start_time = datetime.utcnow()
                result = conn.execute(text("""
                    INSERT INTO auth_users (id, email, password_hash, tenant_id, is_active, created_at, updated_at)
                    VALUES (gen_random_uuid(), 'perf_create_test@example.com', 'hash123', gen_random_uuid(), true, NOW(), NOW())
                """))
                user_creation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['user_creation_ms'] = user_creation_time
                
                # Test session cleanup performance
                start_time = datetime.utcnow()
                result = conn.execute(text("""
                    UPDATE auth_sessions 
                    SET is_active = false 
                    WHERE expires_at < NOW() AND is_active = true
                """))
                session_cleanup_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['session_cleanup_ms'] = session_cleanup_time
                
                # Test complex authentication flow (realistic scenario)
                start_time = datetime.utcnow()
                result = conn.execute(text("""
                    SELECT u.id, u.email, u.full_name, u.roles, u.preferences,
                           s.session_token, s.expires_at, s.risk_score
                    FROM auth_users u
                    JOIN auth_sessions s ON u.id = s.user_id
                    WHERE u.email = 'perf_test_1@example.com' 
                    AND s.is_active = true 
                    AND s.expires_at > NOW()
                    ORDER BY s.created_at DESC
                    LIMIT 1
                """))
                result.fetchone()
                auth_flow_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                performance_results['auth_flow_ms'] = auth_flow_time
                
                # Test concurrent session validation (simulate load)
                from concurrent.futures import ThreadPoolExecutor
                import time
                
                def concurrent_session_check():
                    with self.postgres_engine.connect() as conn:
                        result = conn.execute(text("""
                            SELECT COUNT(*) FROM auth_sessions s
                            JOIN auth_users u ON s.user_id = u.id
                            WHERE s.is_active = true AND s.expires_at > NOW()
                        """))
                        return result.scalar()
                
                start_time = time.time()
                # Run 10 concurrent queries using ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(concurrent_session_check) for _ in range(10)]
                    results = [future.result() for future in futures]
                concurrent_time = (time.time() - start_time) * 1000
                performance_results['concurrent_validation_ms'] = concurrent_time
                performance_results['concurrent_results'] = results
            
            # Check performance thresholds
            thresholds = {
                'user_lookup_ms': 50,      # 50ms for indexed email lookup
                'session_validation_ms': 100,  # 100ms for join query
                'bulk_query_ms': 200,      # 200ms for count query
                'user_creation_ms': 100,   # 100ms for user creation
                'session_cleanup_ms': 500, # 500ms for cleanup operations
                'auth_flow_ms': 150,       # 150ms for complete auth flow
                'concurrent_validation_ms': 1000  # 1s for 10 concurrent queries
            }
            
            for metric, threshold in thresholds.items():
                if metric in performance_results and performance_results[metric] > threshold:
                    errors.append(f"{metric.replace('_', ' ').title()} too slow: {performance_results[metric]:.2f}ms (threshold: {threshold}ms)")
            
            # Clean up test data
            self._cleanup_performance_test_data()
            
            if errors:
                return ValidationResult(
                    success=False,
                    message=f"Performance validation failed - {len(errors)} benchmarks exceeded thresholds",
                    details=performance_results,
                    errors=errors
                )
            else:
                return ValidationResult(
                    success=True,
                    message="Performance validation passed - all benchmarks within acceptable limits",
                    details=performance_results
                )
                
        except Exception as e:
            self.logger.error(f"Performance validation failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Performance validation error: {e}",
                errors=[str(e)]
            )
    
    def _create_performance_test_data(self, sample_size: int):
        """Create sample data for performance testing."""
        try:
            with self.postgres_engine.connect() as conn:
                # Create sample users
                for i in range(min(sample_size, 100)):  # Limit to 100 for testing
                    conn.execute(text("""
                        INSERT INTO auth_users (id, email, password_hash, full_name, tenant_id, is_active, created_at, updated_at)
                        VALUES (gen_random_uuid(), :email, 'hash123', :name, gen_random_uuid(), true, NOW(), NOW())
                        ON CONFLICT (email) DO NOTHING
                    """), {
                        'email': f'perf_test_{i}@example.com',
                        'name': f'Performance Test User {i}'
                    })
                
                # Create sample sessions
                result = conn.execute(text("SELECT id FROM auth_users WHERE email LIKE 'perf_test_%@example.com' LIMIT 10"))
                user_ids = [row[0] for row in result]
                
                for i, user_id in enumerate(user_ids):
                    conn.execute(text("""
                        INSERT INTO auth_sessions (id, user_id, session_token, expires_at, created_at, is_active)
                        VALUES (gen_random_uuid(), :user_id, :token, NOW() + INTERVAL '1 day', NOW(), true)
                        ON CONFLICT (session_token) DO NOTHING
                    """), {
                        'user_id': user_id,
                        'token': f'perf_session_{i}'
                    })
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Could not create performance test data: {e}")
    
    def _cleanup_performance_test_data(self):
        """Clean up performance test data."""
        try:
            with self.postgres_engine.connect() as conn:
                # Clean up test sessions
                conn.execute(text("DELETE FROM auth_sessions WHERE session_token LIKE 'perf_session_%'"))
                
                # Clean up test users
                conn.execute(text("DELETE FROM auth_users WHERE email LIKE 'perf_test_%@example.com'"))
                conn.execute(text("DELETE FROM auth_users WHERE email = 'perf_create_test@example.com'"))
                
                conn.commit()
                
        except Exception as e:
            self.logger.warning(f"Could not clean up performance test data: {e}")
    
    def compare_pre_post_migration_performance(self, sqlite_paths: List[str]) -> ValidationResult:
        """
        Compare authentication performance before and after migration.
        
        Args:
            sqlite_paths: List of SQLite database paths for comparison
            
        Returns:
            Validation result comparing pre/post migration performance
        """
        try:
            self.logger.info("Comparing pre and post-migration authentication performance")
            
            # Measure SQLite performance
            sqlite_results = self._measure_sqlite_performance(sqlite_paths)
            
            # Measure PostgreSQL performance
            postgres_results = self._measure_postgres_performance()
            
            # Compare results
            comparison = {}
            improvements = []
            regressions = []
            
            for metric in sqlite_results:
                if metric in postgres_results:
                    sqlite_time = sqlite_results[metric]
                    postgres_time = postgres_results[metric]
                    
                    if postgres_time < sqlite_time:
                        improvement = ((sqlite_time - postgres_time) / sqlite_time) * 100
                        improvements.append(f"{metric}: {improvement:.1f}% faster")
                        comparison[metric] = {
                            'sqlite_ms': sqlite_time,
                            'postgres_ms': postgres_time,
                            'improvement_percent': improvement
                        }
                    else:
                        regression = ((postgres_time - sqlite_time) / sqlite_time) * 100
                        regressions.append(f"{metric}: {regression:.1f}% slower")
                        comparison[metric] = {
                            'sqlite_ms': sqlite_time,
                            'postgres_ms': postgres_time,
                            'regression_percent': regression
                        }
            
            # Determine overall success
            success = len(regressions) == 0 or all(
                comparison[metric].get('regression_percent', 0) < 50  # Allow up to 50% regression
                for metric in comparison
                if 'regression_percent' in comparison[metric]
            )
            
            message = f"Performance comparison completed. Improvements: {len(improvements)}, Regressions: {len(regressions)}"
            
            return ValidationResult(
                success=success,
                message=message,
                details={
                    'comparison': comparison,
                    'improvements': improvements,
                    'regressions': regressions,
                    'sqlite_results': sqlite_results,
                    'postgres_results': postgres_results
                }
            )
            
        except Exception as e:
            self.logger.error(f"Performance comparison failed: {e}")
            return ValidationResult(
                success=False,
                message=f"Performance comparison error: {e}",
                errors=[str(e)]
            )
    
    def _measure_sqlite_performance(self, sqlite_paths: List[str]) -> Dict[str, float]:
        """Measure SQLite authentication performance."""
        results = {}
        
        try:
            for sqlite_path in sqlite_paths:
                if not os.path.exists(sqlite_path):
                    continue
                    
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                
                # Test user lookup
                start_time = datetime.utcnow()
                cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", ('test@example.com',))
                cursor.fetchone()
                results['user_lookup_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Test session validation
                start_time = datetime.utcnow()
                cursor.execute("""
                    SELECT u.* FROM users u 
                    JOIN sessions s ON u.id = s.user_id 
                    WHERE s.session_token = ? LIMIT 1
                """, ('test_token',))
                cursor.fetchone()
                results['session_validation_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Test bulk query
                start_time = datetime.utcnow()
                cursor.execute("SELECT COUNT(*) FROM users")
                cursor.fetchone()
                results['bulk_query_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                conn.close()
                break  # Use first available database
                
        except Exception as e:
            self.logger.warning(f"Could not measure SQLite performance: {e}")
            
        return results
    
    def _measure_postgres_performance(self) -> Dict[str, float]:
        """Measure PostgreSQL authentication performance."""
        results = {}
        
        try:
            with self.postgres_engine.connect() as conn:
                # Test user lookup
                start_time = datetime.utcnow()
                result = conn.execute(text("SELECT * FROM auth_users WHERE email = 'test@example.com' LIMIT 1"))
                result.fetchone()
                results['user_lookup_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Test session validation
                start_time = datetime.utcnow()
                result = conn.execute(text("""
                    SELECT u.* FROM auth_users u 
                    JOIN auth_sessions s ON u.id = s.user_id 
                    WHERE s.session_token = 'test_token' LIMIT 1
                """))
                result.fetchone()
                results['session_validation_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Test bulk query
                start_time = datetime.utcnow()
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users"))
                result.scalar()
                results['bulk_query_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
        except Exception as e:
            self.logger.warning(f"Could not measure PostgreSQL performance: {e}")
            
        return results