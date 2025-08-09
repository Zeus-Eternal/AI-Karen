"""
Performance tests for PostgreSQL-optimized authentication operations.

This module tests the performance characteristics of the optimized authentication
system to ensure it meets the required performance benchmarks.
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import List, Dict, Any
from uuid import uuid4

from src.ai_karen_engine.auth.config import AuthConfig, DatabaseConfig, SecurityConfig
from src.ai_karen_engine.auth.optimized_core import OptimizedCoreAuthenticator
from src.ai_karen_engine.auth.optimized_database import OptimizedAuthDatabaseClient
from src.ai_karen_engine.auth.models import UserData


class PerformanceTestConfig:
    """Configuration for performance tests."""
    
    # Performance thresholds (in milliseconds)
    MAX_AUTH_TIME = 100.0  # Maximum time for authentication
    MAX_USER_CREATION_TIME = 50.0  # Maximum time for user creation
    MAX_SESSION_VALIDATION_TIME = 20.0  # Maximum time for session validation
    MAX_BATCH_OPERATION_TIME = 200.0  # Maximum time for batch operations
    
    # Load test parameters
    CONCURRENT_USERS = 50  # Number of concurrent operations
    OPERATIONS_PER_USER = 10  # Operations per concurrent user
    BATCH_SIZE = 100  # Size for batch operations


@pytest.fixture
async def optimized_auth_config():
    """Create optimized authentication configuration for testing."""
    return AuthConfig(
        database=DatabaseConfig(
            database_url="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_auth",
            connection_pool_size=20,
            connection_pool_max_overflow=40,
            connection_timeout_seconds=10,
            enable_query_logging=False,  # Disable for performance testing
        ),
        security=SecurityConfig(
            password_hash_rounds=10,  # Reduced for testing
            max_failed_attempts=5,
            lockout_duration_minutes=15,
        ),
    )


@pytest.fixture
async def optimized_authenticator(optimized_auth_config):
    """Create optimized authenticator for testing."""
    authenticator = OptimizedCoreAuthenticator(optimized_auth_config)
    await authenticator.initialize()
    yield authenticator
    await authenticator.close()


@pytest.fixture
async def test_users(optimized_authenticator) -> List[UserData]:
    """Create test users for performance testing."""
    users = []
    for i in range(100):
        user_data = await optimized_authenticator.create_user_optimized(
            email=f"test_user_{i}@example.com",
            password="TestPassword123!",
            full_name=f"Test User {i}",
            tenant_id="test_tenant",
        )
        users.append(user_data)
    return users


class TestAuthenticationPerformance:
    """Test authentication operation performance."""

    @pytest.mark.asyncio
    async def test_single_authentication_performance(self, optimized_authenticator):
        """Test single authentication operation performance."""
        # Create test user
        user_data = await optimized_authenticator.create_user_optimized(
            email="perf_test@example.com",
            password="TestPassword123!",
            full_name="Performance Test User",
        )

        # Measure authentication time
        start_time = time.perf_counter()
        authenticated_user = await optimized_authenticator.authenticate_user_optimized(
            email="perf_test@example.com",
            password="TestPassword123!",
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        end_time = time.perf_counter()

        auth_time_ms = (end_time - start_time) * 1000

        assert authenticated_user is not None
        assert authenticated_user.email == "perf_test@example.com"
        assert auth_time_ms < PerformanceTestConfig.MAX_AUTH_TIME, \
            f"Authentication took {auth_time_ms:.2f}ms, expected < {PerformanceTestConfig.MAX_AUTH_TIME}ms"

    @pytest.mark.asyncio
    async def test_concurrent_authentication_performance(self, optimized_authenticator, test_users):
        """Test concurrent authentication performance."""
        async def authenticate_user(user: UserData) -> float:
            """Authenticate a single user and return the time taken."""
            start_time = time.perf_counter()
            result = await optimized_authenticator.authenticate_user_optimized(
                email=user.email,
                password="TestPassword123!",
                ip_address="127.0.0.1",
                user_agent="concurrent-test",
            )
            end_time = time.perf_counter()
            assert result is not None
            return (end_time - start_time) * 1000

        # Run concurrent authentications
        concurrent_users = test_users[:PerformanceTestConfig.CONCURRENT_USERS]
        
        start_time = time.perf_counter()
        auth_times = await asyncio.gather(*[
            authenticate_user(user) for user in concurrent_users
        ])
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        avg_auth_time = sum(auth_times) / len(auth_times)
        max_auth_time = max(auth_times)

        print(f"Concurrent authentication stats:")
        print(f"  Total time: {total_time_ms:.2f}ms")
        print(f"  Average auth time: {avg_auth_time:.2f}ms")
        print(f"  Max auth time: {max_auth_time:.2f}ms")
        print(f"  Throughput: {len(concurrent_users) / (total_time_ms / 1000):.2f} auths/sec")

        assert avg_auth_time < PerformanceTestConfig.MAX_AUTH_TIME
        assert max_auth_time < PerformanceTestConfig.MAX_AUTH_TIME * 2  # Allow some variance

    @pytest.mark.asyncio
    async def test_user_creation_performance(self, optimized_authenticator):
        """Test user creation performance."""
        creation_times = []

        for i in range(20):
            start_time = time.perf_counter()
            user_data = await optimized_authenticator.create_user_optimized(
                email=f"creation_test_{i}@example.com",
                password="TestPassword123!",
                full_name=f"Creation Test User {i}",
            )
            end_time = time.perf_counter()

            creation_time_ms = (end_time - start_time) * 1000
            creation_times.append(creation_time_ms)

            assert user_data is not None
            assert creation_time_ms < PerformanceTestConfig.MAX_USER_CREATION_TIME

        avg_creation_time = sum(creation_times) / len(creation_times)
        print(f"User creation average time: {avg_creation_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_session_validation_performance(self, optimized_authenticator, test_users):
        """Test session validation performance."""
        # Create sessions for test users
        sessions = []
        for user in test_users[:20]:
            session_data = await optimized_authenticator.create_session_optimized(
                user_data=user,
                ip_address="127.0.0.1",
                user_agent="session-test",
            )
            sessions.append(session_data)

        # Test session validation performance
        validation_times = []
        for session in sessions:
            start_time = time.perf_counter()
            validated_user = await optimized_authenticator.validate_session_optimized(
                session.session_token
            )
            end_time = time.perf_counter()

            validation_time_ms = (end_time - start_time) * 1000
            validation_times.append(validation_time_ms)

            assert validated_user is not None
            assert validation_time_ms < PerformanceTestConfig.MAX_SESSION_VALIDATION_TIME

        avg_validation_time = sum(validation_times) / len(validation_times)
        print(f"Session validation average time: {avg_validation_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_batch_session_validation_performance(self, optimized_authenticator, test_users):
        """Test batch session validation performance."""
        # Create sessions for test users
        sessions = []
        for user in test_users[:PerformanceTestConfig.BATCH_SIZE]:
            session_data = await optimized_authenticator.create_session_optimized(
                user_data=user,
                ip_address="127.0.0.1",
                user_agent="batch-test",
            )
            sessions.append(session_data)

        session_tokens = [s.session_token for s in sessions]

        # Test batch validation performance
        start_time = time.perf_counter()
        results = await optimized_authenticator.batch_validate_sessions(session_tokens)
        end_time = time.perf_counter()

        batch_time_ms = (end_time - start_time) * 1000
        per_session_time = batch_time_ms / len(session_tokens)

        print(f"Batch validation stats:")
        print(f"  Total time: {batch_time_ms:.2f}ms")
        print(f"  Per session: {per_session_time:.2f}ms")
        print(f"  Throughput: {len(session_tokens) / (batch_time_ms / 1000):.2f} validations/sec")

        assert batch_time_ms < PerformanceTestConfig.MAX_BATCH_OPERATION_TIME
        assert len(results) == len(session_tokens)
        assert all(user is not None for user in results.values())

    @pytest.mark.asyncio
    async def test_role_based_lookup_performance(self, optimized_authenticator):
        """Test role-based user lookup performance using JSONB queries."""
        # Create users with different roles
        roles_to_test = [
            ["user"],
            ["user", "admin"],
            ["user", "moderator"],
            ["admin"],
            ["user", "admin", "super_admin"],
        ]

        users_created = []
        for i, roles in enumerate(roles_to_test * 10):  # Create 50 users
            user_data = await optimized_authenticator.create_user_optimized(
                email=f"role_test_{i}@example.com",
                password="TestPassword123!",
                full_name=f"Role Test User {i}",
                roles=roles,
            )
            users_created.append(user_data)

        # Test role-based lookups
        lookup_times = []
        test_roles = ["admin", "moderator", "super_admin"]

        for role in test_roles:
            start_time = time.perf_counter()
            user = await optimized_authenticator.get_user_by_email_with_roles(
                email=users_created[1].email,  # User with admin role
                required_roles=[role] if role == "admin" else ["user", role]
            )
            end_time = time.perf_counter()

            lookup_time_ms = (end_time - start_time) * 1000
            lookup_times.append(lookup_time_ms)

            if role == "admin":
                assert user is not None  # Should find admin user
            
            assert lookup_time_ms < 50.0  # Should be very fast with JSONB index

        avg_lookup_time = sum(lookup_times) / len(lookup_times)
        print(f"Role-based lookup average time: {avg_lookup_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_bulk_preferences_update_performance(self, optimized_authenticator, test_users):
        """Test bulk user preferences update performance."""
        # Prepare bulk updates
        updates = []
        for i, user in enumerate(test_users[:PerformanceTestConfig.BATCH_SIZE]):
            preferences = {
                "theme": "dark" if i % 2 == 0 else "light",
                "language": "en",
                "notifications": True,
                "test_setting": f"value_{i}",
            }
            updates.append((user.user_id, preferences))

        # Test bulk update performance
        start_time = time.perf_counter()
        updated_count = await optimized_authenticator.bulk_update_user_preferences(updates)
        end_time = time.perf_counter()

        bulk_update_time_ms = (end_time - start_time) * 1000
        per_user_time = bulk_update_time_ms / len(updates)

        print(f"Bulk preferences update stats:")
        print(f"  Total time: {bulk_update_time_ms:.2f}ms")
        print(f"  Per user: {per_user_time:.2f}ms")
        print(f"  Updated count: {updated_count}")

        assert bulk_update_time_ms < PerformanceTestConfig.MAX_BATCH_OPERATION_TIME
        assert updated_count == len(updates)

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, optimized_authenticator):
        """Test database connection pool performance under load."""
        async def perform_operations():
            """Perform multiple database operations."""
            operations = []
            
            # Mix of different operations
            for i in range(10):
                if i % 3 == 0:
                    # User creation
                    op = optimized_authenticator.create_user_optimized(
                        email=f"pool_test_{uuid4()}@example.com",
                        password="TestPassword123!",
                        full_name=f"Pool Test User {i}",
                    )
                elif i % 3 == 1:
                    # Authentication
                    op = optimized_authenticator.authenticate_user_optimized(
                        email="perf_test@example.com",
                        password="TestPassword123!",
                    )
                else:
                    # Session creation
                    user_data = UserData(
                        user_id=str(uuid4()),
                        email=f"session_test_{i}@example.com",
                        tenant_id="test",
                    )
                    op = optimized_authenticator.create_session_optimized(
                        user_data=user_data,
                        ip_address="127.0.0.1",
                    )
                
                operations.append(op)
            
            return await asyncio.gather(*operations, return_exceptions=True)

        # Create a test user for authentication operations
        await optimized_authenticator.create_user_optimized(
            email="perf_test@example.com",
            password="TestPassword123!",
            full_name="Performance Test User",
        )

        # Run concurrent operations to test connection pool
        start_time = time.perf_counter()
        results = await asyncio.gather(*[
            perform_operations() for _ in range(20)  # 20 concurrent batches
        ])
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000
        total_operations = sum(len(batch) for batch in results)
        
        print(f"Connection pool performance:")
        print(f"  Total time: {total_time_ms:.2f}ms")
        print(f"  Total operations: {total_operations}")
        print(f"  Operations per second: {total_operations / (total_time_ms / 1000):.2f}")

        # Check that most operations succeeded
        successful_operations = 0
        for batch in results:
            for result in batch:
                if not isinstance(result, Exception):
                    successful_operations += 1

        success_rate = successful_operations / total_operations
        print(f"  Success rate: {success_rate:.2%}")

        assert success_rate > 0.95  # At least 95% success rate
        assert total_time_ms < 5000  # Should complete within 5 seconds


class TestDatabaseOptimizations:
    """Test PostgreSQL-specific optimizations."""

    @pytest.mark.asyncio
    async def test_jsonb_query_performance(self, optimized_auth_config):
        """Test JSONB query performance with indexes."""
        db_client = OptimizedAuthDatabaseClient(optimized_auth_config.database)
        await db_client.initialize_optimized_schema()

        try:
            # Create users with complex JSONB data
            complex_preferences = {
                "ui": {
                    "theme": "dark",
                    "sidebar_collapsed": True,
                    "language": "en",
                },
                "notifications": {
                    "email": True,
                    "push": False,
                    "sms": True,
                },
                "features": {
                    "beta_features": True,
                    "analytics": False,
                },
                "custom_data": {
                    "tags": ["important", "vip", "beta_tester"],
                    "metadata": {"source": "api", "version": "2.1"},
                }
            }

            # Create test users with JSONB data
            for i in range(50):
                user_data = UserData(
                    user_id=str(uuid4()),
                    email=f"jsonb_test_{i}@example.com",
                    full_name=f"JSONB Test User {i}",
                    tenant_id="test_tenant",
                    roles=["user", "beta_tester"] if i % 2 == 0 else ["user"],
                    preferences=complex_preferences,
                )
                await db_client.upsert_user(user_data, "dummy_hash")

            # Test JSONB containment queries
            start_time = time.perf_counter()
            
            async with db_client.session_factory() as session:
                # Query users with specific role using JSONB containment
                result = await session.execute(text("""
                    SELECT COUNT(*) as user_count
                    FROM auth_users 
                    WHERE roles @> '["beta_tester"]'::jsonb
                    AND preferences @> '{"ui": {"theme": "dark"}}'::jsonb
                """))
                
                count = result.fetchone().user_count
            
            end_time = time.perf_counter()
            query_time_ms = (end_time - start_time) * 1000

            print(f"JSONB query performance:")
            print(f"  Query time: {query_time_ms:.2f}ms")
            print(f"  Results found: {count}")

            assert query_time_ms < 50.0  # Should be very fast with GIN index
            assert count > 0  # Should find matching users

        finally:
            await db_client.close()

    @pytest.mark.asyncio
    async def test_partial_index_performance(self, optimized_auth_config):
        """Test partial index performance for active users."""
        db_client = OptimizedAuthDatabaseClient(optimized_auth_config.database)
        await db_client.initialize_optimized_schema()

        try:
            # Create mix of active and inactive users
            for i in range(100):
                user_data = UserData(
                    user_id=str(uuid4()),
                    email=f"partial_index_test_{i}@example.com",
                    full_name=f"Partial Index Test User {i}",
                    tenant_id="test_tenant",
                    is_active=i % 10 != 0,  # 90% active, 10% inactive
                )
                await db_client.upsert_user(user_data, "dummy_hash")

            # Test query performance on active users (should use partial index)
            start_time = time.perf_counter()
            
            async with db_client.session_factory() as session:
                result = await session.execute(text("""
                    SELECT COUNT(*) as active_count
                    FROM auth_users 
                    WHERE is_active = true
                    AND tenant_id = 'test_tenant'
                """))
                
                active_count = result.fetchone().active_count
            
            end_time = time.perf_counter()
            query_time_ms = (end_time - start_time) * 1000

            print(f"Partial index query performance:")
            print(f"  Query time: {query_time_ms:.2f}ms")
            print(f"  Active users found: {active_count}")

            assert query_time_ms < 20.0  # Should be very fast with partial index
            assert active_count == 90  # Should find 90 active users

        finally:
            await db_client.close()


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-s"])