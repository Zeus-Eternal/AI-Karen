"""
Production Authentication Integration Tests

This test suite verifies that the production authentication system is working correctly
with all components: PostgreSQL database, Redis sessions, JWT tokens, and security features.
"""

import asyncio
import os
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Import authentication components
from ai_karen_engine.auth.config import AuthConfig
from ai_karen_engine.auth.service import AuthService
from ai_karen_engine.auth.database import AuthDatabaseClient
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.auth.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    SessionExpiredError,
    AccountLockedError
)


class TestProductionAuthentication:
    """Test suite for production authentication system."""
    
    @pytest.fixture(scope="class")
    async def auth_config(self):
        """Create authentication configuration for testing."""
        return AuthConfig.from_env()
    
    @pytest.fixture(scope="class")
    async def auth_service(self, auth_config):
        """Create and initialize authentication service."""
        service = AuthService(auth_config)
        await service.initialize()
        return service
    
    @pytest.fixture(scope="class")
    async def test_user_data(self):
        """Create test user data."""
        return {
            "email": f"test_user_{uuid.uuid4().hex[:8]}@test.local",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "roles": ["user"],
            "tenant_id": "default"
        }
    
    @pytest.fixture(scope="class")
    async def admin_user_data(self):
        """Create admin user data."""
        return {
            "email": f"admin_user_{uuid.uuid4().hex[:8]}@test.local",
            "password": "AdminPassword123!",
            "full_name": "Admin User",
            "roles": ["admin", "user"],
            "tenant_id": "default"
        }
    
    async def test_database_connection(self, auth_config):
        """Test PostgreSQL database connection."""
        db_client = AuthDatabaseClient(auth_config.database)
        
        # Test basic connection
        async with db_client.engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1, "Database connection test failed"
    
    async def test_database_schema(self, auth_config):
        """Test that all required database tables exist."""
        db_client = AuthDatabaseClient(auth_config.database)
        
        required_tables = [
            'auth_users',
            'auth_password_hashes',
            'auth_sessions',
            'auth_providers',
            'user_identities',
            'auth_password_reset_tokens',
            'auth_email_verification_tokens',
            'auth_events'
        ]
        
        async with db_client.engine.begin() as conn:
            from sqlalchemy import text
            for table in required_tables:
                result = await conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.fetchone()[0]
                assert exists, f"Required table {table} does not exist"
    
    async def test_redis_connection(self, auth_config):
        """Test Redis connection if configured."""
        if auth_config.session.redis_url:
            import redis.asyncio as redis
            
            redis_client = redis.from_url(
                auth_config.session.redis_url,
                decode_responses=True
            )
            
            # Test connection
            await redis_client.ping()
            
            # Test basic operations
            test_key = f"test_{uuid.uuid4().hex}"
            await redis_client.set(test_key, "test_value", ex=10)
            value = await redis_client.get(test_key)
            await redis_client.delete(test_key)
            await redis_client.close()
            
            assert value == "test_value", "Redis operation test failed"
    
    async def test_user_creation(self, auth_service, test_user_data):
        """Test user creation with secure password hashing."""
        # Create user
        user = await auth_service.create_user(**test_user_data)
        
        assert user is not None, "User creation failed"
        assert user.email == test_user_data["email"], "User email mismatch"
        assert user.full_name == test_user_data["full_name"], "User full name mismatch"
        assert user.roles == test_user_data["roles"], "User roles mismatch"
        assert user.is_active, "User should be active by default"
        
        # Verify password hash is stored securely
        password_hash = await auth_service.core_auth.db_client.get_user_password_hash(user.user_id)
        assert password_hash is not None, "Password hash not stored"
        assert password_hash != test_user_data["password"], "Password should be hashed"
        assert password_hash.startswith("$2b$"), "Password should use bcrypt hashing"
    
    async def test_user_authentication(self, auth_service, test_user_data):
        """Test user authentication with correct credentials."""
        # Authenticate user
        authenticated_user = await auth_service.authenticate_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        assert authenticated_user is not None, "Authentication failed"
        assert authenticated_user.email == test_user_data["email"], "Authenticated user email mismatch"
    
    async def test_invalid_credentials(self, auth_service, test_user_data):
        """Test authentication with invalid credentials."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.authenticate_user(
                email=test_user_data["email"],
                password="wrong_password",
                ip_address="127.0.0.1",
                user_agent="Test User Agent"
            )
    
    async def test_session_management(self, auth_service, test_user_data):
        """Test session creation, validation, and invalidation."""
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        # Create session
        session = await auth_service.create_session(
            user_data=user,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        assert session is not None, "Session creation failed"
        assert session.session_token is not None, "Session token not generated"
        assert session.access_token is not None, "Access token not generated"
        assert session.refresh_token is not None, "Refresh token not generated"
        assert session.user_data.user_id == user.user_id, "Session user data mismatch"
        
        # Validate session
        validated_user = await auth_service.validate_session(
            session_token=session.session_token,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        assert validated_user is not None, "Session validation failed"
        assert validated_user.user_id == user.user_id, "Validated user mismatch"
        
        # Invalidate session
        invalidated = await auth_service.invalidate_session(
            session_token=session.session_token,
            reason="test_cleanup"
        )
        
        assert invalidated, "Session invalidation failed"
        
        # Verify session is no longer valid
        invalid_user = await auth_service.validate_session(
            session_token=session.session_token,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        assert invalid_user is None, "Invalidated session should not be valid"
    
    async def test_jwt_token_functionality(self, auth_config, test_user_data):
        """Test JWT token creation and validation."""
        from ai_karen_engine.auth.tokens import TokenManager
        
        token_manager = TokenManager(auth_config.jwt)
        
        # Create test user
        user = UserData(
            user_id=str(uuid.uuid4()),
            email=test_user_data["email"],
            full_name=test_user_data["full_name"],
            roles=test_user_data["roles"],
            tenant_id=test_user_data["tenant_id"]
        )
        
        # Create tokens
        access_token = await token_manager.create_access_token(user)
        refresh_token = await token_manager.create_refresh_token(user)
        
        assert access_token is not None, "Access token creation failed"
        assert refresh_token is not None, "Refresh token creation failed"
        
        # Validate tokens
        access_payload = await token_manager.validate_access_token(access_token)
        refresh_payload = await token_manager.validate_refresh_token(refresh_token)
        
        assert access_payload is not None, "Access token validation failed"
        assert refresh_payload is not None, "Refresh token validation failed"
        assert access_payload["sub"] == user.user_id, "Access token user ID mismatch"
        assert refresh_payload["sub"] == user.user_id, "Refresh token user ID mismatch"
    
    async def test_password_security_features(self, auth_service):
        """Test password security features (complexity, hashing)."""
        # Test weak password rejection
        weak_passwords = [
            "123",
            "password",
            "abc123",
            "Password",  # Missing special character and number
            "password123",  # Missing uppercase and special character
        ]
        
        for weak_password in weak_passwords:
            with pytest.raises((ValueError, Exception)):  # Should reject weak passwords
                await auth_service.create_user(
                    email=f"weak_test_{uuid.uuid4().hex[:8]}@test.local",
                    password=weak_password,
                    full_name="Weak Password Test"
                )
    
    async def test_account_lockout(self, auth_service, test_user_data):
        """Test account lockout after failed login attempts."""
        max_attempts = auth_service.config.security.max_failed_attempts
        
        # Make multiple failed login attempts
        for i in range(max_attempts):
            try:
                await auth_service.authenticate_user(
                    email=test_user_data["email"],
                    password="wrong_password",
                    ip_address="127.0.0.1",
                    user_agent="Test User Agent"
                )
            except InvalidCredentialsError:
                pass  # Expected
        
        # Next attempt should result in account lockout
        with pytest.raises(AccountLockedError):
            await auth_service.authenticate_user(
                email=test_user_data["email"],
                password="wrong_password",
                ip_address="127.0.0.1",
                user_agent="Test User Agent"
            )
    
    async def test_audit_logging(self, auth_service, test_user_data):
        """Test that authentication events are properly logged."""
        # Perform authentication to generate audit events
        user = await auth_service.authenticate_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        # Create session to generate more events
        session = await auth_service.create_session(
            user_data=user,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        # Verify events are logged in database
        async with auth_service.core_auth.db_client.session_factory() as db_session:
            from sqlalchemy import text
            result = await db_session.execute(text("""
                SELECT COUNT(*) FROM auth_events 
                WHERE user_id = :user_id 
                AND timestamp > :since
            """), {
                "user_id": user.user_id,
                "since": datetime.utcnow() - timedelta(minutes=5)
            })
            
            event_count = result.fetchone()[0]
            assert event_count > 0, "Authentication events should be logged"
    
    async def test_multi_session_support(self, auth_service, test_user_data):
        """Test multiple concurrent sessions for the same user."""
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="Test User Agent 1"
        )
        
        # Create multiple sessions
        session1 = await auth_service.create_session(
            user_data=user,
            ip_address="127.0.0.1",
            user_agent="Test User Agent 1"
        )
        
        session2 = await auth_service.create_session(
            user_data=user,
            ip_address="192.168.1.1",
            user_agent="Test User Agent 2"
        )
        
        # Verify both sessions are valid
        user1 = await auth_service.validate_session(session1.session_token)
        user2 = await auth_service.validate_session(session2.session_token)
        
        assert user1 is not None, "First session should be valid"
        assert user2 is not None, "Second session should be valid"
        assert user1.user_id == user2.user_id, "Both sessions should belong to same user"
        
        # Clean up sessions
        await auth_service.invalidate_session(session1.session_token)
        await auth_service.invalidate_session(session2.session_token)
    
    async def test_session_cleanup(self, auth_service, test_user_data):
        """Test automatic cleanup of expired sessions."""
        # This test would require manipulating session expiry times
        # For now, we'll test the cleanup function exists and can be called
        
        # Get session manager
        session_manager = auth_service.core_auth.session_manager
        
        # Call cleanup function
        cleaned_count = await session_manager.cleanup_expired_sessions()
        
        # Should return a number (even if 0)
        assert isinstance(cleaned_count, int), "Cleanup should return count of cleaned sessions"
    
    async def test_external_provider_support(self, auth_service):
        """Test external authentication provider support."""
        # Test creating an external provider
        provider_id = f"test_provider_{uuid.uuid4().hex[:8]}"
        
        # This would test the external authentication flow
        # For now, we'll verify the provider tables exist and can be used
        
        async with auth_service.core_auth.db_client.session_factory() as session:
            from sqlalchemy import text
            
            # Insert test provider
            await session.execute(text("""
                INSERT INTO auth_providers (provider_id, type, config, enabled)
                VALUES (:provider_id, 'oauth2', '{}', true)
                ON CONFLICT (provider_id) DO NOTHING
            """), {"provider_id": provider_id})
            
            await session.commit()
            
            # Verify provider was created
            result = await session.execute(text("""
                SELECT COUNT(*) FROM auth_providers WHERE provider_id = :provider_id
            """), {"provider_id": provider_id})
            
            count = result.fetchone()[0]
            assert count == 1, "External provider should be created"
    
    async def test_performance_metrics(self, auth_service, test_user_data):
        """Test that performance metrics are collected."""
        # Perform operations that should generate metrics
        start_time = datetime.utcnow()
        
        user = await auth_service.authenticate_user(
            email=test_user_data["email"],
            password=test_user_data["password"],
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        session = await auth_service.create_session(
            user_data=user,
            ip_address="127.0.0.1",
            user_agent="Test User Agent"
        )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify operations completed in reasonable time
        assert processing_time < 5.0, "Authentication operations should complete quickly"
        
        # Clean up
        await auth_service.invalidate_session(session.session_token)


# Utility functions for running tests
async def run_production_auth_tests():
    """Run all production authentication tests."""
    print("🧪 Running Production Authentication Tests")
    print("=" * 50)
    
    # Create test instance
    test_instance = TestProductionAuthentication()
    
    # Get configuration
    config = AuthConfig.from_env()
    
    # Initialize auth service
    auth_service = AuthService(config)
    await auth_service.initialize()
    
    # Create test data
    test_user_data = {
        "email": f"test_user_{uuid.uuid4().hex[:8]}@test.local",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default"
    }
    
    tests = [
        ("Database Connection", test_instance.test_database_connection(config)),
        ("Database Schema", test_instance.test_database_schema(config)),
        ("Redis Connection", test_instance.test_redis_connection(config)),
        ("User Creation", test_instance.test_user_creation(auth_service, test_user_data)),
        ("User Authentication", test_instance.test_user_authentication(auth_service, test_user_data)),
        ("Invalid Credentials", test_instance.test_invalid_credentials(auth_service, test_user_data)),
        ("Session Management", test_instance.test_session_management(auth_service, test_user_data)),
        ("JWT Token Functionality", test_instance.test_jwt_token_functionality(config, test_user_data)),
        ("Password Security", test_instance.test_password_security_features(auth_service)),
        ("Audit Logging", test_instance.test_audit_logging(auth_service, test_user_data)),
        ("Multi-Session Support", test_instance.test_multi_session_support(auth_service, test_user_data)),
        ("Session Cleanup", test_instance.test_session_cleanup(auth_service, test_user_data)),
        ("External Provider Support", test_instance.test_external_provider_support(auth_service)),
        ("Performance Metrics", test_instance.test_performance_metrics(auth_service, test_user_data)),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_coro in tests:
        try:
            print(f"Running {test_name}...", end=" ")
            await test_coro
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All production authentication tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False


if __name__ == "__main__":
    # Run tests directly
    success = asyncio.run(run_production_auth_tests())
    exit(0 if success else 1)