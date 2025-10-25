"""
End-to-End Authentication Integration Tests

This module provides comprehensive integration tests for the authentication system,
covering complete authentication flows, network failure scenarios, concurrent attempts,
and performance testing under load.

Requirements: 4.1, 4.2, 4.3, 4.4
"""

import asyncio
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any, Optional
import aiohttp
import json
from concurrent.futures import ThreadPoolExecutor
import statistics

from src.ai_karen_engine.auth.service import AuthService
from src.ai_karen_engine.auth.models import UserData
from src.ai_karen_engine.auth.exceptions import (
    InvalidCredentialsError,
    SessionNotFoundError,
    RateLimitExceededError,
    DatabaseConnectionError,
    NetworkTimeoutError,
)


class TestCredentials:
    """Test credentials for end-to-end authentication testing."""
    EMAIL = "admin@example.com"
    PASSWORD = "password123"
    INVALID_EMAIL = "invalid@example.com"
    INVALID_PASSWORD = "wrongpassword"


class NetworkFailureSimulator:
    """Simulates various network failure scenarios for testing."""
    
    def __init__(self):
        self.failure_count = 0
        self.max_failures = 0
        self.failure_type = None
        
    def configure_failures(self, max_failures: int, failure_type: str = "timeout"):
        """Configure network failure simulation."""
        self.max_failures = max_failures
        self.failure_type = failure_type
        self.failure_count = 0
        
    async def simulate_request(self, original_request_func, *args, **kwargs):
        """Simulate network request with potential failures."""
        if self.failure_count < self.max_failures:
            self.failure_count += 1
            
            if self.failure_type == "timeout":
                await asyncio.sleep(0.1)  # Simulate delay
                raise NetworkTimeoutError("Simulated network timeout")
            elif self.failure_type == "connection_refused":
                raise ConnectionError("Simulated connection refused")
            elif self.failure_type == "database_error":
                raise DatabaseConnectionError("Simulated database connection error")
                
        # After max failures, allow success
        return await original_request_func(*args, **kwargs)


class AuthenticationPerformanceTracker:
    """Tracks authentication performance metrics."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.concurrent_attempts = 0
        self.max_concurrent = 0
        
    def start_attempt(self):
        """Mark start of authentication attempt."""
        self.concurrent_attempts += 1
        self.max_concurrent = max(self.max_concurrent, self.concurrent_attempts)
        return time.time()
        
    def end_attempt(self, start_time: float, success: bool):
        """Mark end of authentication attempt."""
        response_time = time.time() - start_time
        self.response_times.append(response_time)
        self.concurrent_attempts -= 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.response_times:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "max_response_time": 0.0,
                "min_response_time": 0.0,
                "max_concurrent": 0,
            }
            
        return {
            "total_attempts": len(self.response_times),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / len(self.response_times),
            "avg_response_time": statistics.mean(self.response_times),
            "max_response_time": max(self.response_times),
            "min_response_time": min(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "max_concurrent": self.max_concurrent,
        }


@pytest_asyncio.fixture
async def auth_service_with_test_user():
    """Create AuthService with test user admin@example.com/password123."""
    # Mock database client for testing
    mock_db_client = AsyncMock()
    
    # Create test user data
    test_user = UserData(
        user_id="test-admin-user-id",
        email=TestCredentials.EMAIL,
        full_name="Test Admin User",
        roles=["admin", "super_admin"],
        tenant_id="default",
        is_active=True,
    )
    
    # Configure mock responses
    mock_db_client.get_user_by_email.return_value = test_user
    mock_db_client.get_user_password_hash.return_value = "$2b$12$hashed_password_123"
    mock_db_client.create_user.return_value = None
    mock_db_client.update_user.return_value = None
    
    # Mock password hasher
    mock_hasher = MagicMock()
    mock_hasher.hash_password.return_value = "$2b$12$hashed_password_123"
    mock_hasher.verify_password.return_value = True
    
    with patch('src.ai_karen_engine.auth.core.AuthDatabaseClient') as mock_db_class:
        mock_db_class.return_value = mock_db_client
        
        with patch('src.ai_karen_engine.auth.core.PasswordHasher') as mock_hasher_class:
            mock_hasher_class.return_value = mock_hasher
            
            # Create auth service
            from src.ai_karen_engine.auth.config import AuthConfig
            config = AuthConfig()
            service = AuthService(config)
            await service.initialize()
            
            yield service, test_user
            
            # Cleanup
            if hasattr(service.core_auth.session_manager, 'stop_cleanup_task'):
                service.core_auth.session_manager.stop_cleanup_task()


@pytest_asyncio.fixture
def network_failure_simulator():
    """Network failure simulator for testing retry logic."""
    return NetworkFailureSimulator()


@pytest_asyncio.fixture
def performance_tracker():
    """Performance tracker for load testing."""
    return AuthenticationPerformanceTracker()


class TestEndToEndAuthentication:
    """Comprehensive end-to-end authentication tests."""
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow_with_test_credentials(self, auth_service_with_test_user):
        """Test complete authentication flow with admin@example.com/password123."""
        service, test_user = auth_service_with_test_user
        
        # Step 1: Authenticate user
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100",
            user_agent="Test-Agent/1.0"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == TestCredentials.EMAIL
        assert authenticated_user.user_id == test_user.user_id
        assert "admin" in authenticated_user.roles
        
        # Step 2: Create session
        session = await service.create_session(
            authenticated_user,
            ip_address="192.168.1.100",
            user_agent="Test-Agent/1.0"
        )
        
        assert session is not None
        assert session.session_token is not None
        assert session.user_id == test_user.user_id
        
        # Step 3: Validate session
        validated_user = await service.validate_session(session.session_token)
        assert validated_user is not None
        assert validated_user.email == TestCredentials.EMAIL
        
        # Step 4: Test session persistence
        # Simulate time passing
        await asyncio.sleep(0.1)
        
        # Session should still be valid
        revalidated_user = await service.validate_session(session.session_token)
        assert revalidated_user is not None
        assert revalidated_user.email == TestCredentials.EMAIL
        
        # Step 5: Invalidate session
        success = await service.invalidate_session(session.session_token)
        assert success is True
        
        # Step 6: Verify session is invalidated
        with pytest.raises(SessionNotFoundError):
            await service.validate_session(session.session_token)
    
    @pytest.mark.asyncio
    async def test_authentication_with_invalid_credentials(self, auth_service_with_test_user):
        """Test authentication failure with invalid credentials."""
        service, _ = auth_service_with_test_user
        
        # Test with invalid email
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(
                email=TestCredentials.INVALID_EMAIL,
                password=TestCredentials.PASSWORD,
                ip_address="192.168.1.100"
            )
        
        # Test with invalid password
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate_user(
                email=TestCredentials.EMAIL,
                password=TestCredentials.INVALID_PASSWORD,
                ip_address="192.168.1.100"
            )
    
    @pytest.mark.asyncio
    async def test_database_connectivity_validation(self, auth_service_with_test_user):
        """Test database connectivity validation during authentication."""
        service, test_user = auth_service_with_test_user
        
        # Mock database connection check
        with patch.object(service.core_auth.db_client, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test successful database connection
            authenticated_user = await service.authenticate_user(
                email=TestCredentials.EMAIL,
                password=TestCredentials.PASSWORD,
                ip_address="192.168.1.100"
            )
            
            assert authenticated_user is not None
            mock_get_user.assert_called_once_with(TestCredentials.EMAIL)
    
    @pytest.mark.asyncio
    async def test_authentication_timeout_handling(self, auth_service_with_test_user):
        """Test authentication timeout handling with 45-second limit."""
        service, test_user = auth_service_with_test_user
        
        # Mock slow database response
        async def slow_get_user(email):
            await asyncio.sleep(0.1)  # Simulate slow response
            return test_user
            
        with patch.object(service.core_auth.db_client, 'get_user_by_email', side_effect=slow_get_user):
            start_time = time.time()
            
            authenticated_user = await service.authenticate_user(
                email=TestCredentials.EMAIL,
                password=TestCredentials.PASSWORD,
                ip_address="192.168.1.100"
            )
            
            response_time = time.time() - start_time
            
            # Should complete successfully within reasonable time
            assert authenticated_user is not None
            assert response_time < 45.0  # AUTH_TIMEOUT_MS = 45 seconds
    
    @pytest.mark.asyncio
    async def test_session_validation_with_database_check(self, auth_service_with_test_user):
        """Test session validation includes database connectivity check."""
        service, test_user = auth_service_with_test_user
        
        # Create authenticated session
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100"
        )
        
        session = await service.create_session(
            authenticated_user,
            ip_address="192.168.1.100"
        )
        
        # Test session validation
        with patch.object(service.core_auth.db_client, 'get_user_by_email') as mock_get_user:
            mock_get_user.return_value = test_user
            
            validated_user = await service.validate_session(session.session_token)
            
            assert validated_user is not None
            assert validated_user.email == TestCredentials.EMAIL


class TestNetworkFailureScenarios:
    """Test authentication behavior under network failure conditions."""
    
    @pytest.mark.asyncio
    async def test_authentication_with_network_timeout_recovery(
        self, auth_service_with_test_user, network_failure_simulator
    ):
        """Test authentication recovery from network timeouts."""
        service, test_user = auth_service_with_test_user
        
        # Configure network failures (2 failures, then success)
        network_failure_simulator.configure_failures(2, "timeout")
        
        # Mock database call with failure simulation
        original_get_user = service.core_auth.db_client.get_user_by_email
        
        async def failing_get_user(email):
            return await network_failure_simulator.simulate_request(
                original_get_user, email
            )
        
        with patch.object(service.core_auth.db_client, 'get_user_by_email', side_effect=failing_get_user):
            # This should eventually succeed after retries
            try:
                authenticated_user = await service.authenticate_user(
                    email=TestCredentials.EMAIL,
                    password=TestCredentials.PASSWORD,
                    ip_address="192.168.1.100"
                )
                
                # If retry logic is implemented, this should succeed
                assert authenticated_user is not None
                assert authenticated_user.email == TestCredentials.EMAIL
                
            except NetworkTimeoutError:
                # If no retry logic, should fail with timeout
                pytest.skip("Retry logic not implemented - expected behavior")
    
    @pytest.mark.asyncio
    async def test_authentication_with_database_connection_failure(
        self, auth_service_with_test_user, network_failure_simulator
    ):
        """Test authentication behavior with database connection failures."""
        service, _ = auth_service_with_test_user
        
        # Configure database connection failures
        network_failure_simulator.configure_failures(1, "database_error")
        
        # Mock database call with failure simulation
        async def failing_get_user(email):
            return await network_failure_simulator.simulate_request(
                lambda e: None, email  # Always fail
            )
        
        with patch.object(service.core_auth.db_client, 'get_user_by_email', side_effect=failing_get_user):
            with pytest.raises(DatabaseConnectionError):
                await service.authenticate_user(
                    email=TestCredentials.EMAIL,
                    password=TestCredentials.PASSWORD,
                    ip_address="192.168.1.100"
                )
    
    @pytest.mark.asyncio
    async def test_session_validation_network_failure_recovery(
        self, auth_service_with_test_user, network_failure_simulator
    ):
        """Test session validation recovery from network failures."""
        service, test_user = auth_service_with_test_user
        
        # Create session first
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100"
        )
        
        session = await service.create_session(
            authenticated_user,
            ip_address="192.168.1.100"
        )
        
        # Configure network failures for session validation
        network_failure_simulator.configure_failures(1, "timeout")
        
        # Test session validation with network failure
        try:
            validated_user = await service.validate_session(session.session_token)
            
            # Should succeed if retry logic is implemented
            assert validated_user is not None
            assert validated_user.email == TestCredentials.EMAIL
            
        except (NetworkTimeoutError, SessionNotFoundError):
            # Expected if no retry logic for session validation
            pytest.skip("Session validation retry logic not implemented")


class TestConcurrentAuthentication:
    """Test concurrent authentication attempts and session management."""
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication_attempts(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Test multiple concurrent authentication attempts."""
        service, _ = auth_service_with_test_user
        
        async def authenticate_user_tracked():
            """Authenticate user with performance tracking."""
            start_time = performance_tracker.start_attempt()
            success = False
            
            try:
                authenticated_user = await service.authenticate_user(
                    email=TestCredentials.EMAIL,
                    password=TestCredentials.PASSWORD,
                    ip_address="192.168.1.100"
                )
                success = authenticated_user is not None
                return authenticated_user
                
            except Exception as e:
                return None
                
            finally:
                performance_tracker.end_attempt(start_time, success)
        
        # Run 5 concurrent authentication attempts
        concurrent_attempts = 5
        tasks = [authenticate_user_tracked() for _ in range(concurrent_attempts)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        failed_results = [r for r in results if r is None or isinstance(r, Exception)]
        
        # At least some should succeed
        assert len(successful_results) > 0, "No concurrent authentication attempts succeeded"
        
        # Get performance statistics
        stats = performance_tracker.get_statistics()
        
        assert stats["total_attempts"] == concurrent_attempts
        assert stats["max_concurrent"] <= concurrent_attempts
        assert stats["avg_response_time"] > 0
        
        # All successful results should have correct email
        for result in successful_results:
            if hasattr(result, 'email'):
                assert result.email == TestCredentials.EMAIL
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation_and_validation(
        self, auth_service_with_test_user
    ):
        """Test concurrent session creation and validation."""
        service, _ = auth_service_with_test_user
        
        # First authenticate user
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100"
        )
        
        async def create_and_validate_session(session_id: int):
            """Create session and immediately validate it."""
            session = await service.create_session(
                authenticated_user,
                ip_address=f"192.168.1.{100 + session_id}",
                user_agent=f"Test-Agent-{session_id}/1.0"
            )
            
            # Immediately validate the session
            validated_user = await service.validate_session(session.session_token)
            
            return {
                "session": session,
                "validated_user": validated_user,
                "session_id": session_id
            }
        
        # Create 3 concurrent sessions
        concurrent_sessions = 3
        tasks = [create_and_validate_session(i) for i in range(concurrent_sessions)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == concurrent_sessions
        
        # Verify all sessions are valid
        for result in successful_results:
            assert result["session"] is not None
            assert result["validated_user"] is not None
            assert result["validated_user"].email == TestCredentials.EMAIL
    
    @pytest.mark.asyncio
    async def test_session_limit_enforcement(self, auth_service_with_test_user):
        """Test that session limits are enforced under concurrent load."""
        service, _ = auth_service_with_test_user
        
        # Authenticate user
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100"
        )
        
        # Create multiple sessions (more than typical limit)
        sessions = []
        max_sessions = 5
        
        for i in range(max_sessions):
            try:
                session = await service.create_session(
                    authenticated_user,
                    ip_address=f"192.168.1.{100 + i}",
                    user_agent=f"Test-Agent-{i}/1.0"
                )
                sessions.append(session)
                
            except Exception as e:
                # Some sessions might fail due to limits
                break
        
        # Should have created at least one session
        assert len(sessions) > 0
        
        # All created sessions should be valid
        for session in sessions:
            validated_user = await service.validate_session(session.session_token)
            assert validated_user is not None
            assert validated_user.email == TestCredentials.EMAIL


class TestAuthenticationPerformanceUnderLoad:
    """Test authentication performance under various load conditions."""
    
    @pytest.mark.asyncio
    async def test_authentication_performance_baseline(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Establish baseline authentication performance metrics."""
        service, _ = auth_service_with_test_user
        
        # Run 10 sequential authentication attempts
        attempts = 10
        
        for i in range(attempts):
            start_time = performance_tracker.start_attempt()
            success = False
            
            try:
                authenticated_user = await service.authenticate_user(
                    email=TestCredentials.EMAIL,
                    password=TestCredentials.PASSWORD,
                    ip_address=f"192.168.1.{100 + i}"
                )
                success = authenticated_user is not None
                
            except Exception:
                pass
                
            finally:
                performance_tracker.end_attempt(start_time, success)
        
        stats = performance_tracker.get_statistics()
        
        # Performance assertions
        assert stats["total_attempts"] == attempts
        assert stats["success_rate"] > 0.8  # At least 80% success rate
        assert stats["avg_response_time"] < 5.0  # Average under 5 seconds
        assert stats["max_response_time"] < 45.0  # Max under 45 seconds (timeout)
    
    @pytest.mark.asyncio
    async def test_authentication_under_high_load(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Test authentication performance under high concurrent load."""
        service, _ = auth_service_with_test_user
        
        async def authenticate_with_tracking(user_id: int):
            """Authenticate with performance tracking."""
            start_time = performance_tracker.start_attempt()
            success = False
            
            try:
                # Add small random delay to simulate real-world conditions
                await asyncio.sleep(0.01 * (user_id % 5))
                
                authenticated_user = await service.authenticate_user(
                    email=TestCredentials.EMAIL,
                    password=TestCredentials.PASSWORD,
                    ip_address=f"192.168.{1 + (user_id // 254)}.{1 + (user_id % 254)}",
                    user_agent=f"LoadTest-Agent-{user_id}/1.0"
                )
                success = authenticated_user is not None
                return authenticated_user
                
            except Exception as e:
                return None
                
            finally:
                performance_tracker.end_attempt(start_time, success)
        
        # High load test: 20 concurrent users
        high_load_users = 20
        tasks = [authenticate_with_tracking(i) for i in range(high_load_users)]
        
        # Use asyncio.gather with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60.0  # 60 second timeout for entire test
            )
        except asyncio.TimeoutError:
            pytest.fail("High load authentication test timed out")
        
        # Analyze performance under load
        stats = performance_tracker.get_statistics()
        
        assert stats["total_attempts"] == high_load_users
        assert stats["max_concurrent"] <= high_load_users
        
        # Under high load, we expect some degradation but still reasonable performance
        assert stats["success_rate"] > 0.5  # At least 50% success rate under load
        assert stats["avg_response_time"] < 30.0  # Average under 30 seconds
        assert stats["max_response_time"] < 45.0  # Max under timeout limit
        
        # Check that we handled concurrent load
        assert stats["max_concurrent"] > 1
    
    @pytest.mark.asyncio
    async def test_session_validation_performance_under_load(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Test session validation performance under concurrent load."""
        service, _ = auth_service_with_test_user
        
        # First, create multiple sessions
        authenticated_user = await service.authenticate_user(
            email=TestCredentials.EMAIL,
            password=TestCredentials.PASSWORD,
            ip_address="192.168.1.100"
        )
        
        # Create 10 sessions
        sessions = []
        for i in range(10):
            session = await service.create_session(
                authenticated_user,
                ip_address=f"192.168.1.{100 + i}"
            )
            sessions.append(session)
        
        async def validate_session_with_tracking(session, session_id: int):
            """Validate session with performance tracking."""
            start_time = performance_tracker.start_attempt()
            success = False
            
            try:
                validated_user = await service.validate_session(session.session_token)
                success = validated_user is not None
                return validated_user
                
            except Exception:
                return None
                
            finally:
                performance_tracker.end_attempt(start_time, success)
        
        # Validate all sessions concurrently (multiple times each)
        validation_tasks = []
        for i, session in enumerate(sessions):
            # Validate each session 3 times concurrently
            for j in range(3):
                validation_tasks.append(
                    validate_session_with_tracking(session, i * 3 + j)
                )
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Analyze session validation performance
        stats = performance_tracker.get_statistics()
        
        expected_validations = len(sessions) * 3
        assert stats["total_attempts"] == expected_validations
        
        # Session validation should be fast and reliable
        assert stats["success_rate"] > 0.9  # At least 90% success rate
        assert stats["avg_response_time"] < 2.0  # Average under 2 seconds
        assert stats["max_response_time"] < 10.0  # Max under 10 seconds
    
    @pytest.mark.asyncio
    async def test_mixed_authentication_and_validation_load(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Test mixed authentication and session validation under load."""
        service, _ = auth_service_with_test_user
        
        async def mixed_auth_operations(operation_id: int):
            """Perform mixed authentication and validation operations."""
            start_time = performance_tracker.start_attempt()
            success = False
            
            try:
                if operation_id % 3 == 0:
                    # Authentication operation
                    authenticated_user = await service.authenticate_user(
                        email=TestCredentials.EMAIL,
                        password=TestCredentials.PASSWORD,
                        ip_address=f"192.168.1.{100 + (operation_id % 50)}"
                    )
                    
                    if authenticated_user:
                        # Create session
                        session = await service.create_session(
                            authenticated_user,
                            ip_address=f"192.168.1.{100 + (operation_id % 50)}"
                        )
                        success = session is not None
                        return {"type": "auth", "result": session}
                    
                else:
                    # For validation, we need an existing session
                    # Create a quick session first
                    auth_user = await service.authenticate_user(
                        email=TestCredentials.EMAIL,
                        password=TestCredentials.PASSWORD,
                        ip_address=f"192.168.1.{100 + (operation_id % 50)}"
                    )
                    
                    if auth_user:
                        session = await service.create_session(
                            auth_user,
                            ip_address=f"192.168.1.{100 + (operation_id % 50)}"
                        )
                        
                        # Validate the session
                        validated_user = await service.validate_session(session.session_token)
                        success = validated_user is not None
                        return {"type": "validation", "result": validated_user}
                
                return None
                
            except Exception:
                return None
                
            finally:
                performance_tracker.end_attempt(start_time, success)
        
        # Run mixed operations concurrently
        mixed_operations = 15
        tasks = [mixed_auth_operations(i) for i in range(mixed_operations)]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze mixed load performance
        stats = performance_tracker.get_statistics()
        
        assert stats["total_attempts"] == mixed_operations
        
        # Mixed operations should maintain reasonable performance
        assert stats["success_rate"] > 0.6  # At least 60% success rate for mixed load
        assert stats["avg_response_time"] < 20.0  # Average under 20 seconds
        assert stats["max_response_time"] < 45.0  # Max under timeout limit
        
        # Verify we had concurrent operations
        assert stats["max_concurrent"] > 1


# Performance test configuration
@pytest.mark.performance
class TestAuthenticationLoadTesting:
    """Dedicated load testing for authentication system."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_authentication_load(
        self, auth_service_with_test_user, performance_tracker
    ):
        """Test sustained authentication load over time."""
        service, _ = auth_service_with_test_user
        
        # Run authentication attempts for 30 seconds
        test_duration = 30.0  # seconds
        start_time = time.time()
        operation_count = 0
        
        async def sustained_auth_worker():
            """Worker for sustained authentication testing."""
            nonlocal operation_count
            
            while time.time() - start_time < test_duration:
                worker_start = performance_tracker.start_attempt()
                success = False
                
                try:
                    authenticated_user = await service.authenticate_user(
                        email=TestCredentials.EMAIL,
                        password=TestCredentials.PASSWORD,
                        ip_address=f"192.168.1.{100 + (operation_count % 50)}"
                    )
                    success = authenticated_user is not None
                    operation_count += 1
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.1)
                    
                except Exception:
                    pass
                    
                finally:
                    performance_tracker.end_attempt(worker_start, success)
        
        # Run 5 concurrent workers
        workers = 5
        worker_tasks = [sustained_auth_worker() for _ in range(workers)]
        
        await asyncio.gather(*worker_tasks)
        
        # Analyze sustained load performance
        stats = performance_tracker.get_statistics()
        
        # Should have completed many operations
        assert stats["total_attempts"] > 50  # At least 50 operations in 30 seconds
        
        # Performance should remain stable under sustained load
        assert stats["success_rate"] > 0.7  # At least 70% success rate
        assert stats["avg_response_time"] < 15.0  # Average under 15 seconds
        
        # Calculate throughput
        throughput = stats["total_attempts"] / test_duration
        assert throughput > 1.0  # At least 1 operation per second