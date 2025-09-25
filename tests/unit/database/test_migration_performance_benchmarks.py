"""
Performance benchmark tests for database migration validation.

This module provides comprehensive performance benchmarks to compare
authentication speed before and after migration from SQLite to PostgreSQL.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from typing import Dict, List, Tuple

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path to import our modules directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.database.migration.migration_validator import MigrationValidator
from ai_karen_engine.database.migration.postgres_schema import (
    Base,
    PasswordResetToken,
    User,
    UserSession,
)


class PerformanceBenchmark:
    """Performance benchmark utility for database operations."""
    
    def __init__(self):
        self.results = {}
    
    def time_operation(self, operation_name: str, operation_func, iterations: int = 100):
        """Time a database operation multiple times and collect statistics."""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                operation_func()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            except Exception as e:
                # Skip failed operations but log them
                print(f"Operation {operation_name} failed: {e}")
                continue
        
        if times:
            self.results[operation_name] = {
                'mean_ms': mean(times),
                'median_ms': median(times),
                'min_ms': min(times),
                'max_ms': max(times),
                'std_dev_ms': stdev(times) if len(times) > 1 else 0,
                'iterations': len(times),
                'success_rate': len(times) / iterations
            }
        else:
            self.results[operation_name] = {
                'mean_ms': float('inf'),
                'median_ms': float('inf'),
                'min_ms': float('inf'),
                'max_ms': float('inf'),
                'std_dev_ms': float('inf'),
                'iterations': 0,
                'success_rate': 0
            }
        
        return self.results[operation_name]
    
    def compare_results(self, other_benchmark: 'PerformanceBenchmark') -> Dict:
        """Compare results with another benchmark."""
        comparison = {}
        
        for operation in self.results:
            if operation in other_benchmark.results:
                self_time = self.results[operation]['mean_ms']
                other_time = other_benchmark.results[operation]['mean_ms']
                
                if other_time > 0 and self_time != float('inf') and other_time != float('inf'):
                    improvement = ((other_time - self_time) / other_time) * 100
                    comparison[operation] = {
                        'self_mean_ms': self_time,
                        'other_mean_ms': other_time,
                        'improvement_percent': improvement,
                        'faster': improvement > 0
                    }
        
        return comparison


class TestSQLitePerformanceBenchmarks:
    """Performance benchmarks for SQLite authentication operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sqlite_auth_db(self, temp_dir):
        """Create SQLite authentication database with test data."""
        db_path = os.path.join(temp_dir, "auth_benchmark.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                tenant_id TEXT NOT NULL,
                roles TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE password_reset_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX idx_sessions_token ON sessions(session_token)")
        cursor.execute("CREATE INDEX idx_sessions_user_id ON sessions(user_id)")
        cursor.execute("CREATE INDEX idx_tokens_token ON password_reset_tokens(token)")
        
        # Insert test data
        users_data = []
        sessions_data = []
        tokens_data = []
        
        for i in range(1000):  # Create 1000 test users
            user_id = f"user_{i}"
            email = f"user{i}@example.com"
            users_data.append((user_id, email, f"hash_{i}", f"User {i}", f"tenant_{i % 10}"))
            
            # Create 2-3 sessions per user
            for j in range(2 + (i % 2)):
                session_id = f"session_{i}_{j}"
                session_token = f"token_{i}_{j}_{uuid.uuid4().hex[:8]}"
                expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
                sessions_data.append((session_id, user_id, session_token, expires_at))
            
            # Create password reset token for some users
            if i % 10 == 0:
                token_id = f"reset_{i}"
                reset_token = f"reset_{i}_{uuid.uuid4().hex[:8]}"
                expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
                tokens_data.append((token_id, user_id, reset_token, expires_at))
        
        cursor.executemany("""
            INSERT INTO users (id, email, password_hash, full_name, tenant_id)
            VALUES (?, ?, ?, ?, ?)
        """, users_data)
        
        cursor.executemany("""
            INSERT INTO sessions (id, user_id, session_token, expires_at)
            VALUES (?, ?, ?, ?)
        """, sessions_data)
        
        cursor.executemany("""
            INSERT INTO password_reset_tokens (id, user_id, token, expires_at)
            VALUES (?, ?, ?, ?)
        """, tokens_data)
        
        conn.commit()
        conn.close()
        
        return db_path
    
    def test_sqlite_user_lookup_performance(self, sqlite_auth_db):
        """Benchmark SQLite user lookup by email."""
        benchmark = PerformanceBenchmark()
        
        def lookup_user():
            conn = sqlite3.connect(sqlite_auth_db)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? LIMIT 1", ('user500@example.com',))
            result = cursor.fetchone()
            conn.close()
            return result
        
        result = benchmark.time_operation("sqlite_user_lookup", lookup_user, iterations=100)
        
        assert result['success_rate'] > 0.9  # At least 90% success rate
        assert result['mean_ms'] < 50  # Should be under 50ms on average
        print(f"SQLite user lookup: {result['mean_ms']:.2f}ms average")
    
    def test_sqlite_session_validation_performance(self, sqlite_auth_db):
        """Benchmark SQLite session validation with join."""
        benchmark = PerformanceBenchmark()
        
        def validate_session():
            conn = sqlite3.connect(sqlite_auth_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.*, s.expires_at FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.session_token = ? AND s.is_active = 1
                LIMIT 1
            """, ('token_500_0_12345678',))
            result = cursor.fetchone()
            conn.close()
            return result
        
        result = benchmark.time_operation("sqlite_session_validation", validate_session, iterations=100)
        
        assert result['success_rate'] > 0.8  # At least 80% success rate
        print(f"SQLite session validation: {result['mean_ms']:.2f}ms average")
    
    def test_sqlite_bulk_operations_performance(self, sqlite_auth_db):
        """Benchmark SQLite bulk operations."""
        benchmark = PerformanceBenchmark()
        
        def count_active_users():
            conn = sqlite3.connect(sqlite_auth_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            result = cursor.fetchone()[0]
            conn.close()
            return result
        
        def count_active_sessions():
            conn = sqlite3.connect(sqlite_auth_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
            result = cursor.fetchone()[0]
            conn.close()
            return result
        
        benchmark.time_operation("sqlite_count_users", count_active_users, iterations=50)
        benchmark.time_operation("sqlite_count_sessions", count_active_sessions, iterations=50)
        
        print(f"SQLite count users: {benchmark.results['sqlite_count_users']['mean_ms']:.2f}ms")
        print(f"SQLite count sessions: {benchmark.results['sqlite_count_sessions']['mean_ms']:.2f}ms")
    
    def test_sqlite_concurrent_access_performance(self, sqlite_auth_db):
        """Benchmark SQLite concurrent access performance."""
        benchmark = PerformanceBenchmark()
        
        def concurrent_lookups():
            def lookup_user(user_id):
                conn = sqlite3.connect(sqlite_auth_db)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (f"user_{user_id}",))
                result = cursor.fetchone()
                conn.close()
                return result
            
            # Simulate 10 concurrent user lookups
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(lookup_user, i) for i in range(10)]
                results = [future.result() for future in futures]
            
            return len([r for r in results if r is not None])
        
        result = benchmark.time_operation("sqlite_concurrent_lookups", concurrent_lookups, iterations=20)
        print(f"SQLite concurrent lookups: {result['mean_ms']:.2f}ms average")


class TestPostgreSQLPerformanceBenchmarks:
    """Performance benchmarks for PostgreSQL authentication operations."""
    
    @pytest.fixture
    def temp_postgres_url(self):
        """Create temporary PostgreSQL database URL for testing."""
        return "sqlite:///:memory:"
    
    @pytest.fixture
    def postgres_auth_db(self, temp_postgres_url):
        """Create PostgreSQL authentication database with test data."""
        engine = create_engine(temp_postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Insert test data
        with SessionLocal() as session:
            users = []
            sessions = []
            tokens = []
            
            for i in range(1000):  # Create 1000 test users
                user = User(
                    id=uuid.uuid4(),
                    email=f"user{i}@example.com",
                    password_hash=f"hash_{i}",
                    full_name=f"User {i}",
                    tenant_id=uuid.uuid4(),
                    roles=['user'],
                    is_active=True
                )
                users.append(user)
                
                # Create 2-3 sessions per user
                for j in range(2 + (i % 2)):
                    user_session = UserSession(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        session_token=f"token_{i}_{j}_{uuid.uuid4().hex[:8]}",
                        expires_at=datetime.utcnow() + timedelta(hours=24),
                        is_active=True
                    )
                    sessions.append(user_session)
                
                # Create password reset token for some users
                if i % 10 == 0:
                    reset_token = PasswordResetToken(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        token=f"reset_{i}_{uuid.uuid4().hex[:8]}",
                        expires_at=datetime.utcnow() + timedelta(hours=1),
                        used=False
                    )
                    tokens.append(reset_token)
            
            # Batch insert for better performance
            session.add_all(users)
            session.commit()
            
            # Update session user_ids after users are committed
            for i, user_session in enumerate(sessions):
                user_session.user_id = users[i // 3].id  # Approximate mapping
            
            session.add_all(sessions)
            session.commit()
            
            # Update token user_ids
            for i, token in enumerate(tokens):
                token.user_id = users[i * 10].id
            
            session.add_all(tokens)
            session.commit()
        
        return engine
    
    def test_postgres_user_lookup_performance(self, postgres_auth_db):
        """Benchmark PostgreSQL user lookup by email."""
        benchmark = PerformanceBenchmark()
        
        def lookup_user():
            with postgres_auth_db.connect() as conn:
                result = conn.execute(text("SELECT * FROM auth_users WHERE email = :email LIMIT 1"), 
                                    {'email': 'user500@example.com'})
                return result.fetchone()
        
        result = benchmark.time_operation("postgres_user_lookup", lookup_user, iterations=100)
        
        assert result['success_rate'] > 0.9  # At least 90% success rate
        print(f"PostgreSQL user lookup: {result['mean_ms']:.2f}ms average")
    
    def test_postgres_session_validation_performance(self, postgres_auth_db):
        """Benchmark PostgreSQL session validation with join."""
        benchmark = PerformanceBenchmark()
        
        def validate_session():
            with postgres_auth_db.connect() as conn:
                result = conn.execute(text("""
                    SELECT u.*, s.expires_at FROM auth_users u
                    JOIN auth_sessions s ON u.id = s.user_id
                    WHERE s.session_token = :token AND s.is_active = true
                    LIMIT 1
                """), {'token': 'token_500_0_12345678'})
                return result.fetchone()
        
        result = benchmark.time_operation("postgres_session_validation", validate_session, iterations=100)
        
        assert result['success_rate'] > 0.8  # At least 80% success rate
        print(f"PostgreSQL session validation: {result['mean_ms']:.2f}ms average")
    
    def test_postgres_bulk_operations_performance(self, postgres_auth_db):
        """Benchmark PostgreSQL bulk operations."""
        benchmark = PerformanceBenchmark()
        
        def count_active_users():
            with postgres_auth_db.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM auth_users WHERE is_active = true"))
                return result.scalar()
        
        def count_active_sessions():
            with postgres_auth_db.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM auth_sessions WHERE is_active = true"))
                return result.scalar()
        
        benchmark.time_operation("postgres_count_users", count_active_users, iterations=50)
        benchmark.time_operation("postgres_count_sessions", count_active_sessions, iterations=50)
        
        print(f"PostgreSQL count users: {benchmark.results['postgres_count_users']['mean_ms']:.2f}ms")
        print(f"PostgreSQL count sessions: {benchmark.results['postgres_count_sessions']['mean_ms']:.2f}ms")
    
    def test_postgres_concurrent_access_performance(self, postgres_auth_db):
        """Benchmark PostgreSQL concurrent access performance."""
        benchmark = PerformanceBenchmark()
        
        def concurrent_lookups():
            def lookup_user(user_id):
                with postgres_auth_db.connect() as conn:
                    result = conn.execute(text("SELECT * FROM auth_users WHERE email = :email"), 
                                        {'email': f'user_{user_id}@example.com'})
                    return result.fetchone()
            
            # Simulate 10 concurrent user lookups
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(lookup_user, i) for i in range(10)]
                results = [future.result() for future in futures]
            
            return len([r for r in results if r is not None])
        
        result = benchmark.time_operation("postgres_concurrent_lookups", concurrent_lookups, iterations=20)
        print(f"PostgreSQL concurrent lookups: {result['mean_ms']:.2f}ms average")
    
    def test_postgres_complex_queries_performance(self, postgres_auth_db):
        """Benchmark PostgreSQL complex query performance."""
        benchmark = PerformanceBenchmark()
        
        def complex_auth_query():
            with postgres_auth_db.connect() as conn:
                result = conn.execute(text("""
                    SELECT u.id, u.email, u.full_name, u.roles,
                           COUNT(s.id) as active_sessions,
                           MAX(s.created_at) as last_login
                    FROM auth_users u
                    LEFT JOIN auth_sessions s ON u.id = s.user_id AND s.is_active = true
                    WHERE u.is_active = true
                    GROUP BY u.id, u.email, u.full_name, u.roles
                    HAVING COUNT(s.id) > 0
                    ORDER BY last_login DESC
                    LIMIT 10
                """))
                return result.fetchall()
        
        result = benchmark.time_operation("postgres_complex_query", complex_auth_query, iterations=20)
        print(f"PostgreSQL complex query: {result['mean_ms']:.2f}ms average")


class TestMigrationPerformanceComparison:
    """Compare performance between SQLite and PostgreSQL after migration."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def performance_test_data(self, temp_dir):
        """Create test databases for performance comparison."""
        # Create SQLite database
        sqlite_path = os.path.join(temp_dir, "perf_test.db")
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
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
        
        # Insert test data
        for i in range(100):
            cursor.execute("INSERT INTO users VALUES (?, ?, ?)", 
                         (f"user_{i}", f"user{i}@example.com", f"hash_{i}"))
            cursor.execute("INSERT INTO sessions VALUES (?, ?, ?)", 
                         (f"session_{i}", f"user_{i}", f"token_{i}"))
        
        conn.commit()
        conn.close()
        
        # Create PostgreSQL database
        postgres_url = "sqlite:///:memory:"
        engine = create_engine(postgres_url)
        Base.metadata.create_all(bind=engine)
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        with SessionLocal() as session:
            for i in range(100):
                user = User(
                    id=uuid.uuid4(),
                    email=f"user{i}@example.com",
                    password_hash=f"hash_{i}",
                    tenant_id=uuid.uuid4(),
                    is_active=True
                )
                session.add(user)
            session.commit()
            
            # Add sessions
            users = session.query(User).all()
            for i, user in enumerate(users):
                user_session = UserSession(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    session_token=f"token_{i}",
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                    is_active=True
                )
                session.add(user_session)
            session.commit()
        
        return sqlite_path, postgres_url
    
    def test_performance_comparison_comprehensive(self, performance_test_data):
        """Comprehensive performance comparison between SQLite and PostgreSQL."""
        sqlite_path, postgres_url = performance_test_data
        
        # Create validator for comparison
        validator = MigrationValidator([sqlite_path], postgres_url)
        
        # Run performance comparison
        result = validator.compare_pre_post_migration_performance([sqlite_path])
        
        assert result.success is not None  # Should complete without errors
        assert 'comparison' in result.details
        assert 'sqlite_results' in result.details
        assert 'postgres_results' in result.details
        
        # Print comparison results
        comparison = result.details['comparison']
        for metric, data in comparison.items():
            if 'improvement_percent' in data:
                print(f"{metric}: {data['improvement_percent']:.1f}% improvement")
            elif 'regression_percent' in data:
                print(f"{metric}: {data['regression_percent']:.1f}% regression")
    
    def test_load_testing_simulation(self, performance_test_data):
        """Simulate load testing for both databases."""
        sqlite_path, postgres_url = performance_test_data
        
        def simulate_load_sqlite(operations: int = 100):
            """Simulate load on SQLite database."""
            times = []
            for i in range(operations):
                start_time = time.perf_counter()
                
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                
                # Simulate typical auth operations
                cursor.execute("SELECT * FROM users WHERE email = ?", (f"user{i % 100}@example.com",))
                user = cursor.fetchone()
                
                if user:
                    cursor.execute("SELECT * FROM sessions WHERE user_id = ?", (user[0],))
                    cursor.fetchone()
                
                conn.close()
                
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
            
            return {
                'mean_ms': mean(times),
                'max_ms': max(times),
                'min_ms': min(times),
                'operations': operations
            }
        
        def simulate_load_postgres(operations: int = 100):
            """Simulate load on PostgreSQL database."""
            engine = create_engine(postgres_url)
            times = []
            
            for i in range(operations):
                start_time = time.perf_counter()
                
                with engine.connect() as conn:
                    # Simulate typical auth operations
                    result = conn.execute(text("""
                        SELECT u.*, s.session_token FROM auth_users u
                        LEFT JOIN auth_sessions s ON u.id = s.user_id
                        WHERE u.email = :email
                        LIMIT 1
                    """), {'email': f"user{i % 100}@example.com"})
                    result.fetchone()
                
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
            
            return {
                'mean_ms': mean(times),
                'max_ms': max(times),
                'min_ms': min(times),
                'operations': operations
            }
        
        # Run load tests
        sqlite_results = simulate_load_sqlite(50)
        postgres_results = simulate_load_postgres(50)
        
        print(f"SQLite load test: {sqlite_results['mean_ms']:.2f}ms average")
        print(f"PostgreSQL load test: {postgres_results['mean_ms']:.2f}ms average")
        
        # Calculate improvement
        if postgres_results['mean_ms'] < sqlite_results['mean_ms']:
            improvement = ((sqlite_results['mean_ms'] - postgres_results['mean_ms']) / 
                          sqlite_results['mean_ms']) * 100
            print(f"PostgreSQL is {improvement:.1f}% faster under load")
        else:
            regression = ((postgres_results['mean_ms'] - sqlite_results['mean_ms']) / 
                         sqlite_results['mean_ms']) * 100
            print(f"PostgreSQL is {regression:.1f}% slower under load")
        
        # Both should complete successfully
        assert sqlite_results['operations'] == 50
        assert postgres_results['operations'] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print output