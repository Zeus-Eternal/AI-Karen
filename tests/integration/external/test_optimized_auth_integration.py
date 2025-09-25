"""
Integration tests for PostgreSQL-optimized authentication operations.

This module tests the integration of all optimized authentication components
to ensure they work together correctly and efficiently.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import uuid4

from src.ai_karen_engine.auth.config import AuthConfig, DatabaseConfig, SecurityConfig, SessionConfig
from src.ai_karen_engine.auth.optimized_core import OptimizedCoreAuthenticator
from src.ai_karen_engine.auth.optimized_database import OptimizedAuthDatabaseClient
from src.ai_karen_engine.auth.optimized_session import OptimizedSessionManager
from src.ai_karen_engine.auth.models import UserData, SessionData
from src.ai_karen_engine.auth.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    SessionExpiredError,
    UserAlreadyExistsError,
)


@pytest.fixture
async def optimized_config():
    """Create optimized configuration for integration testing."""
    return AuthConfig(
        database=DatabaseConfig(
            database_url="postgresql+asyncpg://test_user:test_pass@localhost:5432/test_auth_integration",
            connection_pool_size=10,
            connection_pool_max_overflow=20,
            enable_query_logging=True,
        ),
        security=SecurityConfig(
            password_hash_rounds=10,
            max_failed_attempts=3,
            lockout_duration_minutes=5,
        ),
        session=SessionConfig(
            session_timeout_hours=1,
            max_sessions_per_user=3,
        ),
    )


@pytest.fixture
async def optimized_authenticator(optimized_config):
    """Create and initialize optimized authenticator."""
    authenticator = OptimizedCoreAuthenticator(optimized_config)
    await authenticator.initialize()
    yield authenticator
    await authenticator.close()


class TestOptimizedAuthenticationIntegration:
    """Test complete authentication flow with optimizations."""

    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, optimized_authenticator):
        """Test complete authentication flow from user creation to session validation."""
        # Step 1: Create user with optimized operations
        user_data = await optimized_authenticator.create_user_optimized(
            email="integration_test@example.com",
            password="SecurePassword123!",
            full_name="Integration Test User",
            tenant_id="integration_tenant",
            roles=["user", "tester"],
        )

        assert user_data is not None
        assert user_data.email == "integration_test@example.com"
        assert user_data.tenant_id == "integration_tenant"
        assert "user" in user_data.roles
        assert "tester" in user_data.roles

        # Step 2: Authenticate user with optimized authentication
        authenticated_user = await optimized_authenticator.authenticate_user_optimized(
            email="integration_test@example.com",
            password="SecurePassword123!",
            ip_address="192.168.1.100",
            user_agent="Integration-Test-Agent/1.0",
        )

        assert authenticated_user is not None
        assert authenticated_user.user_id == user_data.user_id
        assert authenticated_user.last_login_at is not None

        # Step 3: Create session with optimized session management
        session_data = await optimized_authenticator.create_session_optimized(
            user_data=authenticated_user,
            ip_address="192.168.1.100",
            user_agent="Integration-Test-Agent/1.0",
            device_fingerprint="test_device_123",
            geolocation={"country": "US", "city": "San Francisco"},
        )

        assert session_data is not None
        assert session_data.session_token is not None
        assert session_data.access_token is not None
        assert session_data.refresh_token is not None
        assert session_data.ip_address == "192.168.1.100"
        assert session_data.geolocation["country"] == "US"

        # Step 4: Validate session with optimized validation
        validated_user = await optimized_authenticator.validate_session_optimized(
            session_data.session_token
        )

        assert validated_user is not None
        assert validated_user.user_id == user_data.user_id
        assert validated_user.email == "integration_test@example.com"

        # Step 5: Test role-based lookup with JSONB optimization
        role_filtered_user = await optimized_authenticator.get_user_by_email_with_roles(
            email="integration_test@example.com",
            required_roles=["tester"]
        )

        assert role_filtered_user is not None
        assert role_filtered_user.user_id == user_data.user_id

        # Step 6: Test bulk preferences update
        preferences_updates = [(user_data.user_id, {
            "theme": "dark",
            "language": "en",
            "notifications": {"email": True, "push": False},
            "advanced_features": True,
        })]

        updated_count = await optimized_authenticator.bulk_update_user_preferences(
            preferences_updates
        )

        assert updated_count == 1

    @pytest.mark.asyncio
    async def test_session_management_with_limits(self, optimized_authenticator):
        """Test session management with user session limits."""
        # Create test user
        user_data = await optimized_authenticator.create_user_optimized(
            email="session_limit_test@example.com",
            password="TestPassword123!",
            full_name="Session Limit Test User",
        )

        # Create maximum allowed sessions
        sessions = []
        for i in range(3):  # max_sessions_per_user = 3
            session = await optimized_authenticator.create_session_optimized(
                user_data=user_data,
                ip_address=f"192.168.1.{100 + i}",
                user_agent=f"Test-Agent-{i}/1.0",
                device_fingerprint=f"device_{i}",
            )
            sessions.append(session)

        # Verify all sessions are valid
        for session in sessions:
            validated_user = await optimized_authenticator.validate_session_optimized(
                session.session_token
            )
            assert validated_user is not None

        # Create one more session (should trigger cleanup of oldest)
        new_session = await optimized_authenticator.create_session_optimized(
            user_data=user_data,
            ip_address="192.168.1.200",
            user_agent="Test-Agent-New/1.0",
            device_fingerprint="device_new",
        )

        # New session should be valid
        validated_user = await optimized_authenticator.validate_session_optimized(
            new_session.session_token
        )
        assert validated_user is not None

        # Get user sessions to verify cleanup
        user_sessions = await optimized_authenticator.session_manager.get_user_sessions(
            user_data.user_id, active_only=True
        )
        assert len(user_sessions) <= 3  # Should not exceed limit

    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, optimized_authenticator):
        """Test batch operations for improved performance."""
        # Create multiple users for batch testing
        users = []
        for i in range(20):
            user_data = await optimized_authenticator.create_user_optimized(
                email=f"batch_test_{i}@example.com",
                password="BatchTestPassword123!",
                full_name=f"Batch Test User {i}",
                roles=["user", "batch_tester"],
            )
            users.append(user_data)

        # Create sessions for all users
        sessions = []
        for user in users:
            session = await optimized_authenticator.create_session_optimized(
                user_data=user,
                ip_address="192.168.1.50",
                user_agent="Batch-Test-Agent/1.0",
            )
            sessions.append(session)

        # Test batch session validation
        session_tokens = [s.session_token for s in sessions]
        batch_results = await optimized_authenticator.batch_validate_sessions(session_tokens)

        assert len(batch_results) == len(session_tokens)
        assert all(user is not None for user in batch_results.values())

        # Test bulk preferences update
        preferences_updates = []
        for user in users:
            preferences = {
                "batch_test": True,
                "user_index": users.index(user),
                "settings": {"theme": "light", "lang": "en"},
            }
            preferences_updates.append((user.user_id, preferences))

        updated_count = await optimized_authenticator.bulk_update_user_preferences(
            preferences_updates
        )

        assert updated_count == len(users)

    @pytest.mark.asyncio
    async def test_failed_authentication_handling(self, optimized_authenticator):
        """Test optimized handling of failed authentication attempts."""
        # Create test user
        user_data = await optimized_authenticator.create_user_optimized(
            email="failed_auth_test@example.com",
            password="CorrectPassword123!",
            full_name="Failed Auth Test User",
        )

        # Test multiple failed attempts
        for i in range(2):  # max_failed_attempts = 3, so 2 should not lock
            with pytest.raises(InvalidCredentialsError):
                await optimized_authenticator.authenticate_user_optimized(
                    email="failed_auth_test@example.com",
                    password="WrongPassword123!",
                    ip_address="192.168.1.100",
                )

        # User should still be able to authenticate with correct password
        authenticated_user = await optimized_authenticator.authenticate_user_optimized(
            email="failed_auth_test@example.com",
            password="CorrectPassword123!",
            ip_address="192.168.1.100",
        )
        assert authenticated_user is not None

        # Test account lockout after max failed attempts
        for i in range(3):  # This should lock the account
            with pytest.raises(InvalidCredentialsError):
                await optimized_authenticator.authenticate_user_optimized(
                    email="failed_auth_test@example.com",
                    password="WrongPassword123!",
                    ip_address="192.168.1.100",
                )

        # Now even correct password should fail due to lockout
        with pytest.raises(AccountLockedError):
            await optimized_authenticator.authenticate_user_optimized(
                email="failed_auth_test@example.com",
                password="CorrectPassword123!",
                ip_address="192.168.1.100",
            )

    @pytest.mark.asyncio
    async def test_jsonb_query_optimizations(self, optimized_authenticator):
        """Test JSONB query optimizations for roles and preferences."""
        # Create users with different role combinations
        test_cases = [
            (["user"], {"theme": "light", "lang": "en"}),
            (["user", "admin"], {"theme": "dark", "lang": "es"}),
            (["user", "moderator"], {"theme": "auto", "lang": "fr"}),
            (["admin", "super_admin"], {"theme": "dark", "lang": "en"}),
        ]

        created_users = []
        for i, (roles, preferences) in enumerate(test_cases):
            user_data = await optimized_authenticator.create_user_optimized(
                email=f"jsonb_test_{i}@example.com",
                password="JsonbTestPassword123!",
                full_name=f"JSONB Test User {i}",
                roles=roles,
            )
            
            # Update preferences using bulk operation
            await optimized_authenticator.bulk_update_user_preferences([
                (user_data.user_id, preferences)
            ])
            
            created_users.append(user_data)

        # Test role-based queries
        admin_user = await optimized_authenticator.get_user_by_email_with_roles(
            email="jsonb_test_1@example.com",  # User with admin role
            required_roles=["admin"]
        )
        assert admin_user is not None

        # Test query for non-existent role combination
        no_user = await optimized_authenticator.get_user_by_email_with_roles(
            email="jsonb_test_0@example.com",  # User without admin role
            required_roles=["admin"]
        )
        assert no_user is None

    @pytest.mark.asyncio
    async def test_session_cleanup_and_expiration(self, optimized_authenticator):
        """Test automatic session cleanup and expiration handling."""
        # Create test user
        user_data = await optimized_authenticator.create_user_optimized(
            email="cleanup_test@example.com",
            password="CleanupTestPassword123!",
            full_name="Cleanup Test User",
        )

        # Create session with short expiration for testing
        session_data = await optimized_authenticator.create_session_optimized(
            user_data=user_data,
            ip_address="192.168.1.100",
            user_agent="Cleanup-Test-Agent/1.0",
        )

        # Session should be valid initially
        validated_user = await optimized_authenticator.validate_session_optimized(
            session_data.session_token
        )
        assert validated_user is not None

        # Manually expire the session by updating the database
        async with optimized_authenticator.db_client.session_factory() as db_session:
            await db_session.execute(text("""
                UPDATE auth_sessions 
                SET expires_in = 1,
                    created_at = NOW() - INTERVAL '2 seconds'
                WHERE session_token = :token
            """), {"token": session_data.session_token})
            await db_session.commit()

        # Session should now be expired
        with pytest.raises(SessionExpiredError):
            await optimized_authenticator.validate_session_optimized(
                session_data.session_token
            )

        # Test cleanup of expired sessions
        cleanup_count = await optimized_authenticator.session_manager.cleanup_expired_sessions()
        assert cleanup_count >= 1  # Should clean up at least our expired session

    @pytest.mark.asyncio
    async def test_concurrent_operations_stability(self, optimized_authenticator):
        """Test stability under concurrent operations."""
        async def create_and_authenticate_user(index: int):
            """Create user and perform authentication operations."""
            try:
                # Create user
                user_data = await optimized_authenticator.create_user_optimized(
                    email=f"concurrent_test_{index}@example.com",
                    password="ConcurrentTestPassword123!",
                    full_name=f"Concurrent Test User {index}",
                )

                # Authenticate user
                authenticated_user = await optimized_authenticator.authenticate_user_optimized(
                    email=f"concurrent_test_{index}@example.com",
                    password="ConcurrentTestPassword123!",
                    ip_address=f"192.168.1.{100 + (index % 50)}",
                )

                # Create session
                session_data = await optimized_authenticator.create_session_optimized(
                    user_data=authenticated_user,
                    ip_address=f"192.168.1.{100 + (index % 50)}",
                    user_agent=f"Concurrent-Test-Agent-{index}/1.0",
                )

                # Validate session
                validated_user = await optimized_authenticator.validate_session_optimized(
                    session_data.session_token
                )

                return {
                    "success": True,
                    "user_id": user_data.user_id,
                    "session_token": session_data.session_token,
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        # Run concurrent operations
        concurrent_count = 30
        results = await asyncio.gather(*[
            create_and_authenticate_user(i) for i in range(concurrent_count)
        ])

        # Analyze results
        successful_operations = [r for r in results if r["success"]]
        failed_operations = [r for r in results if not r["success"]]

        success_rate = len(successful_operations) / len(results)
        
        print(f"Concurrent operations results:")
        print(f"  Total operations: {len(results)}")
        print(f"  Successful: {len(successful_operations)}")
        print(f"  Failed: {len(failed_operations)}")
        print(f"  Success rate: {success_rate:.2%}")

        if failed_operations:
            print("Failed operation errors:")
            for i, failure in enumerate(failed_operations[:5]):  # Show first 5 errors
                print(f"  {i+1}: {failure['error']}")

        # Should have high success rate
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} is below 95%"

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, optimized_authenticator):
        """Test performance metrics collection and reporting."""
        # Perform various operations to generate metrics
        user_data = await optimized_authenticator.create_user_optimized(
            email="metrics_test@example.com",
            password="MetricsTestPassword123!",
            full_name="Metrics Test User",
        )

        # Perform multiple operations
        for i in range(10):
            authenticated_user = await optimized_authenticator.authenticate_user_optimized(
                email="metrics_test@example.com",
                password="MetricsTestPassword123!",
                ip_address="192.168.1.100",
            )

            session_data = await optimized_authenticator.create_session_optimized(
                user_data=authenticated_user,
                ip_address="192.168.1.100",
            )

            await optimized_authenticator.validate_session_optimized(
                session_data.session_token
            )

        # Get performance metrics
        metrics = await optimized_authenticator.get_performance_metrics()

        assert "authenticate_user_optimized" in metrics
        assert "create_user_optimized" in metrics
        assert "create_session_optimized" in metrics
        assert "validate_session_optimized" in metrics

        # Check metric structure
        auth_metrics = metrics["authenticate_user_optimized"]
        assert "count" in auth_metrics
        assert "avg_ms" in auth_metrics
        assert "min_ms" in auth_metrics
        assert "max_ms" in auth_metrics
        assert auth_metrics["count"] >= 10

        # Check database stats
        assert "database_stats" in metrics
        db_stats = metrics["database_stats"]
        assert "users" in db_stats
        assert "sessions" in db_stats

        print(f"Performance metrics summary:")
        for operation, stats in metrics.items():
            if isinstance(stats, dict) and "avg_ms" in stats:
                print(f"  {operation}: {stats['avg_ms']:.2f}ms avg ({stats['count']} ops)")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])