"""
Load Testing for Authentication Endpoints and Session Management

Tests the performance and reliability of authentication endpoints under load:
- Login endpoint performance
- Token refresh performance
- Session validation performance
- Concurrent user scenarios
- Memory and resource usage
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, AsyncMock, MagicMock
import threading
import psutil
import gc

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_karen_engine.api_routes.auth_session_routes import router as auth_router
from ai_karen_engine.middleware.session_persistence import SessionPersistenceMiddleware
from ai_karen_engine.auth.models import UserData, SessionData
from ai_karen_engine.auth.config import AuthConfig


@pytest.fixture
def app():
    """Create FastAPI app for load testing."""
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(SessionPersistenceMiddleware, enable_intelligent_errors=True)
    
    # Include auth routes
    app.include_router(auth_router)
    
    # Add test endpoints
    @app.get("/api/test/protected")
    async def protected_endpoint():
        return {"message": "success", "timestamp": datetime.now().isoformat()}
    
    @app.get("/api/test/heavy")
    async def heavy_endpoint():
        # Simulate some processing
        await asyncio.sleep(0.01)
        return {"message": "heavy processing complete"}
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_users():
    """Create multiple sample users for load testing."""
    users = []
    for i in range(100):
        user = UserData(
            user_id=f"load-user-{i}",
            email=f"load{i}@example.com",
            full_name=f"Load User {i}",
            tenant_id="default",
            roles=["user"],
            is_verified=True,
            is_active=True,
            preferences={"theme": "dark"}
        )
        users.append(user)
    return users


class LoadTestMetrics:
    """Class to collect and analyze load test metrics."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []
        self.start_time = None
        self.end_time = None
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.memory_usage.clear()
        self.cpu_usage.clear()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.end_time = time.time()
    
    def record_response(self, response_time: float, success: bool, error: str = None):
        """Record a response result."""
        with self._lock:
            self.response_times.append(response_time)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error:
                    self.errors.append(error)
    
    def record_system_metrics(self):
        """Record current system metrics."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        with self._lock:
            self.memory_usage.append(memory_mb)
            self.cpu_usage.append(cpu_percent)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.response_times:
            return {"error": "No data collected"}
        
        total_time = self.end_time - self.start_time if self.end_time else 0
        
        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / len(self.response_times) if self.response_times else 0,
            "total_time": total_time,
            "requests_per_second": len(self.response_times) / total_time if total_time > 0 else 0,
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
            },
            "memory_usage": {
                "min": min(self.memory_usage) if self.memory_usage else 0,
                "max": max(self.memory_usage) if self.memory_usage else 0,
                "mean": statistics.mean(self.memory_usage) if self.memory_usage else 0
            },
            "cpu_usage": {
                "min": min(self.cpu_usage) if self.cpu_usage else 0,
                "max": max(self.cpu_usage) if self.cpu_usage else 0,
                "mean": statistics.mean(self.cpu_usage) if self.cpu_usage else 0
            },
            "errors": list(set(self.errors))  # Unique errors
        }


class TestLoginEndpointLoad:
    """Test login endpoint under load."""

    def test_concurrent_login_requests(self, client, sample_users):
        """Test concurrent login requests."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            auth_service_mock = AsyncMock()
            token_manager_mock = AsyncMock()
            cookie_manager_mock = MagicMock()
            
            mock_auth_service.return_value = auth_service_mock
            mock_token_manager.return_value = token_manager_mock
            mock_cookie_manager.return_value = cookie_manager_mock
            
            metrics = LoadTestMetrics()
            
            def login_request(user_index: int) -> Tuple[bool, float, str]:
                """Perform a single login request."""
                user = sample_users[user_index % len(sample_users)]
                
                # Mock user authentication
                auth_service_mock.authenticate_user.return_value = user
                auth_service_mock.create_session.return_value = SessionData(
                    session_token=f"session-{user_index}",
                    access_token=f"access-{user_index}",
                    refresh_token=f"refresh-{user_index}",
                    expires_in=900,
                    user_data=user,
                    ip_address="127.0.0.1",
                    user_agent="load-test",
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
                )
                
                token_manager_mock.create_access_token.return_value = f"access-{user_index}"
                token_manager_mock.create_refresh_token.return_value = f"refresh-{user_index}"
                
                start_time = time.time()
                try:
                    response = client.post("/auth/login", json={
                        "email": user.email,
                        "password": "password123"
                    })
                    end_time = time.time()
                    
                    success = response.status_code == 200
                    error = None if success else f"Status {response.status_code}: {response.text}"
                    
                    return success, end_time - start_time, error
                    
                except Exception as e:
                    end_time = time.time()
                    return False, end_time - start_time, str(e)
            
            # Run concurrent login requests
            num_requests = 50
            max_workers = 10
            
            metrics.start_monitoring()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all requests
                futures = [executor.submit(login_request, i) for i in range(num_requests)]
                
                # Collect results
                for future in as_completed(futures):
                    success, response_time, error = future.result()
                    metrics.record_response(response_time, success, error)
                    metrics.record_system_metrics()
            
            metrics.stop_monitoring()
            
            # Analyze results
            summary = metrics.get_summary()
            
            print(f"\n=== Login Load Test Results ===")
            print(f"Total requests: {summary['total_requests']}")
            print(f"Success rate: {summary['success_rate']:.2%}")
            print(f"Requests per second: {summary['requests_per_second']:.2f}")
            print(f"Response time - Mean: {summary['response_times']['mean']:.3f}s")
            print(f"Response time - P95: {summary['response_times']['p95']:.3f}s")
            print(f"Memory usage - Mean: {summary['memory_usage']['mean']:.1f}MB")
            
            # Performance assertions
            assert summary['success_rate'] >= 0.95  # 95% success rate
            assert summary['response_times']['mean'] < 0.5  # Mean response time under 500ms
            assert summary['response_times']['p95'] < 1.0  # P95 under 1 second
            assert summary['requests_per_second'] > 20  # At least 20 RPS

    def test_login_endpoint_sustained_load(self, client, sample_users):
        """Test login endpoint under sustained load."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            auth_service_mock = AsyncMock()
            token_manager_mock = AsyncMock()
            cookie_manager_mock = MagicMock()
            
            mock_auth_service.return_value = auth_service_mock
            mock_token_manager.return_value = token_manager_mock
            mock_cookie_manager.return_value = cookie_manager_mock
            
            metrics = LoadTestMetrics()
            stop_flag = threading.Event()
            
            def sustained_login_worker(worker_id: int):
                """Worker that continuously makes login requests."""
                request_count = 0
                while not stop_flag.is_set():
                    user = sample_users[request_count % len(sample_users)]
                    
                    # Mock responses
                    auth_service_mock.authenticate_user.return_value = user
                    auth_service_mock.create_session.return_value = SessionData(
                        session_token=f"session-{worker_id}-{request_count}",
                        access_token=f"access-{worker_id}-{request_count}",
                        refresh_token=f"refresh-{worker_id}-{request_count}",
                        expires_in=900,
                        user_data=user,
                        ip_address="127.0.0.1",
                        user_agent="sustained-test",
                        created_at=datetime.now(timezone.utc),
                        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
                    )
                    
                    token_manager_mock.create_access_token.return_value = f"access-{worker_id}-{request_count}"
                    token_manager_mock.create_refresh_token.return_value = f"refresh-{worker_id}-{request_count}"
                    
                    start_time = time.time()
                    try:
                        response = client.post("/auth/login", json={
                            "email": user.email,
                            "password": "password123"
                        })
                        end_time = time.time()
                        
                        success = response.status_code == 200
                        error = None if success else f"Status {response.status_code}"
                        
                        metrics.record_response(end_time - start_time, success, error)
                        
                        if request_count % 10 == 0:  # Record system metrics every 10 requests
                            metrics.record_system_metrics()
                        
                        request_count += 1
                        
                        # Small delay to prevent overwhelming
                        time.sleep(0.01)
                        
                    except Exception as e:
                        end_time = time.time()
                        metrics.record_response(end_time - start_time, False, str(e))
            
            # Run sustained load test
            num_workers = 5
            test_duration = 10  # seconds
            
            metrics.start_monitoring()
            
            # Start workers
            threads = []
            for i in range(num_workers):
                thread = threading.Thread(target=sustained_login_worker, args=(i,))
                thread.start()
                threads.append(thread)
            
            # Run for specified duration
            time.sleep(test_duration)
            
            # Stop workers
            stop_flag.set()
            for thread in threads:
                thread.join(timeout=2)
            
            metrics.stop_monitoring()
            
            # Analyze results
            summary = metrics.get_summary()
            
            print(f"\n=== Sustained Login Load Test Results ===")
            print(f"Test duration: {test_duration}s")
            print(f"Total requests: {summary['total_requests']}")
            print(f"Success rate: {summary['success_rate']:.2%}")
            print(f"Requests per second: {summary['requests_per_second']:.2f}")
            print(f"Response time - Mean: {summary['response_times']['mean']:.3f}s")
            print(f"Memory usage - Max: {summary['memory_usage']['max']:.1f}MB")
            
            # Performance assertions
            assert summary['success_rate'] >= 0.90  # 90% success rate under sustained load
            assert summary['response_times']['mean'] < 1.0  # Mean response time under 1 second
            assert summary['requests_per_second'] > 10  # At least 10 RPS sustained


class TestTokenRefreshLoad:
    """Test token refresh endpoint under load."""

    def test_concurrent_token_refresh(self, client):
        """Test concurrent token refresh requests."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            cookie_manager_mock = MagicMock()
            
            mock_token_manager.return_value = token_manager_mock
            mock_cookie_manager.return_value = cookie_manager_mock
            
            metrics = LoadTestMetrics()
            
            def refresh_request(request_id: int) -> Tuple[bool, float, str]:
                """Perform a single token refresh request."""
                
                # Mock refresh token validation
                cookie_manager_mock.get_refresh_token.return_value = f"refresh-token-{request_id}"
                token_manager_mock.validate_refresh_token.return_value = {
                    "sub": f"user-{request_id}",
                    "email": f"user{request_id}@example.com",
                    "tenant_id": "default",
                    "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                    "jti": f"refresh-jti-{request_id}"
                }
                
                # Mock token rotation
                new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                token_manager_mock.rotate_tokens.return_value = (
                    f"new-access-{request_id}",
                    f"new-refresh-{request_id}",
                    new_expires_at
                )
                
                start_time = time.time()
                try:
                    response = client.post("/auth/refresh")
                    end_time = time.time()
                    
                    success = response.status_code == 200
                    error = None if success else f"Status {response.status_code}: {response.text}"
                    
                    return success, end_time - start_time, error
                    
                except Exception as e:
                    end_time = time.time()
                    return False, end_time - start_time, str(e)
            
            # Run concurrent refresh requests
            num_requests = 100
            max_workers = 20
            
            metrics.start_monitoring()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(refresh_request, i) for i in range(num_requests)]
                
                for future in as_completed(futures):
                    success, response_time, error = future.result()
                    metrics.record_response(response_time, success, error)
                    metrics.record_system_metrics()
            
            metrics.stop_monitoring()
            
            # Analyze results
            summary = metrics.get_summary()
            
            print(f"\n=== Token Refresh Load Test Results ===")
            print(f"Total requests: {summary['total_requests']}")
            print(f"Success rate: {summary['success_rate']:.2%}")
            print(f"Requests per second: {summary['requests_per_second']:.2f}")
            print(f"Response time - Mean: {summary['response_times']['mean']:.3f}s")
            print(f"Response time - P95: {summary['response_times']['p95']:.3f}s")
            
            # Performance assertions
            assert summary['success_rate'] >= 0.95  # 95% success rate
            assert summary['response_times']['mean'] < 0.2  # Mean response time under 200ms
            assert summary['response_times']['p95'] < 0.5  # P95 under 500ms
            assert summary['requests_per_second'] > 50  # At least 50 RPS (refresh should be fast)

    def test_token_refresh_memory_usage(self, client):
        """Test memory usage during token refresh operations."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager:
            
            # Setup mocks
            token_manager_mock = AsyncMock()
            cookie_manager_mock = MagicMock()
            
            mock_token_manager.return_value = token_manager_mock
            mock_cookie_manager.return_value = cookie_manager_mock
            
            # Record initial memory
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # Perform many refresh operations
            num_operations = 1000
            
            for i in range(num_operations):
                cookie_manager_mock.get_refresh_token.return_value = f"refresh-token-{i}"
                token_manager_mock.validate_refresh_token.return_value = {
                    "sub": f"user-{i}",
                    "email": f"user{i}@example.com",
                    "tenant_id": "default",
                    "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                    "jti": f"refresh-jti-{i}"
                }
                
                new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                token_manager_mock.rotate_tokens.return_value = (
                    f"new-access-{i}",
                    f"new-refresh-{i}",
                    new_expires_at
                )
                
                response = client.post("/auth/refresh")
                assert response.status_code == 200
                
                # Force garbage collection every 100 operations
                if i % 100 == 0:
                    gc.collect()
            
            # Record final memory
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            print(f"\n=== Token Refresh Memory Test Results ===")
            print(f"Operations: {num_operations}")
            print(f"Initial memory: {initial_memory:.1f}MB")
            print(f"Final memory: {final_memory:.1f}MB")
            print(f"Memory increase: {memory_increase:.1f}MB")
            print(f"Memory per operation: {memory_increase/num_operations*1024:.1f}KB")
            
            # Memory usage should not grow excessively
            assert memory_increase < 50  # Less than 50MB increase
            assert memory_increase / num_operations < 0.05  # Less than 50KB per operation


class TestSessionValidationLoad:
    """Test session validation under load."""

    def test_concurrent_protected_requests(self, client):
        """Test concurrent requests to protected endpoints."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class:
            
            # Setup token manager
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            metrics = LoadTestMetrics()
            
            def protected_request(request_id: int) -> Tuple[bool, float, str]:
                """Make a request to protected endpoint."""
                
                # Mock valid token validation
                token_manager_mock.validate_access_token.return_value = {
                    "sub": f"user-{request_id}",
                    "email": f"user{request_id}@example.com",
                    "full_name": f"User {request_id}",
                    "roles": ["user"],
                    "tenant_id": "default",
                    "is_verified": True
                }
                
                start_time = time.time()
                try:
                    response = client.get("/api/test/protected", headers={
                        "Authorization": f"Bearer token-{request_id}"
                    })
                    end_time = time.time()
                    
                    success = response.status_code == 200
                    error = None if success else f"Status {response.status_code}: {response.text}"
                    
                    return success, end_time - start_time, error
                    
                except Exception as e:
                    end_time = time.time()
                    return False, end_time - start_time, str(e)
            
            # Run concurrent protected requests
            num_requests = 200
            max_workers = 30
            
            metrics.start_monitoring()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(protected_request, i) for i in range(num_requests)]
                
                for future in as_completed(futures):
                    success, response_time, error = future.result()
                    metrics.record_response(response_time, success, error)
                    metrics.record_system_metrics()
            
            metrics.stop_monitoring()
            
            # Analyze results
            summary = metrics.get_summary()
            
            print(f"\n=== Protected Endpoint Load Test Results ===")
            print(f"Total requests: {summary['total_requests']}")
            print(f"Success rate: {summary['success_rate']:.2%}")
            print(f"Requests per second: {summary['requests_per_second']:.2f}")
            print(f"Response time - Mean: {summary['response_times']['mean']:.3f}s")
            print(f"Response time - P95: {summary['response_times']['p95']:.3f}s")
            
            # Performance assertions
            assert summary['success_rate'] >= 0.98  # 98% success rate
            assert summary['response_times']['mean'] < 0.1  # Mean response time under 100ms
            assert summary['response_times']['p95'] < 0.3  # P95 under 300ms
            assert summary['requests_per_second'] > 100  # At least 100 RPS

    def test_mixed_workload_performance(self, client, sample_users):
        """Test performance with mixed authentication workload."""
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth_service, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock_token_manager, \
             patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_manager, \
             patch('ai_karen_engine.middleware.session_persistence.AuthConfig'):
            
            # Setup mocks
            auth_service_mock = AsyncMock()
            token_manager_mock = AsyncMock()
            cookie_manager_mock = MagicMock()
            
            mock_auth_service.return_value = auth_service_mock
            mock_token_manager.return_value = token_manager_mock
            mock_cookie_manager.return_value = cookie_manager_mock
            
            metrics = LoadTestMetrics()
            
            def mixed_request(request_id: int) -> Tuple[bool, float, str]:
                """Perform mixed authentication operations."""
                operation = request_id % 4  # 4 different operations
                
                start_time = time.time()
                try:
                    if operation == 0:  # Login
                        user = sample_users[request_id % len(sample_users)]
                        auth_service_mock.authenticate_user.return_value = user
                        auth_service_mock.create_session.return_value = SessionData(
                            session_token=f"session-{request_id}",
                            access_token=f"access-{request_id}",
                            refresh_token=f"refresh-{request_id}",
                            expires_in=900,
                            user_data=user,
                            ip_address="127.0.0.1",
                            user_agent="mixed-test",
                            created_at=datetime.now(timezone.utc),
                            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
                        )
                        token_manager_mock.create_access_token.return_value = f"access-{request_id}"
                        token_manager_mock.create_refresh_token.return_value = f"refresh-{request_id}"
                        
                        response = client.post("/auth/login", json={
                            "email": user.email,
                            "password": "password123"
                        })
                        
                    elif operation == 1:  # Token refresh
                        cookie_manager_mock.get_refresh_token.return_value = f"refresh-token-{request_id}"
                        token_manager_mock.validate_refresh_token.return_value = {
                            "sub": f"user-{request_id}",
                            "email": f"user{request_id}@example.com",
                            "tenant_id": "default",
                            "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp(),
                            "jti": f"refresh-jti-{request_id}"
                        }
                        new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
                        token_manager_mock.rotate_tokens.return_value = (
                            f"new-access-{request_id}",
                            f"new-refresh-{request_id}",
                            new_expires_at
                        )
                        
                        response = client.post("/auth/refresh")
                        
                    elif operation == 2:  # Protected request
                        token_manager_mock.validate_access_token.return_value = {
                            "sub": f"user-{request_id}",
                            "email": f"user{request_id}@example.com",
                            "full_name": f"User {request_id}",
                            "roles": ["user"],
                            "tenant_id": "default",
                            "is_verified": True
                        }
                        
                        response = client.get("/api/test/protected", headers={
                            "Authorization": f"Bearer token-{request_id}"
                        })
                        
                    else:  # Logout
                        cookie_manager_mock.get_refresh_token.return_value = f"refresh-token-{request_id}"
                        cookie_manager_mock.get_session_token.return_value = f"session-token-{request_id}"
                        token_manager_mock.revoke_token.return_value = True
                        auth_service_mock.invalidate_session.return_value = True
                        
                        response = client.post("/auth/logout")
                    
                    end_time = time.time()
                    success = response.status_code in [200, 201]
                    error = None if success else f"Status {response.status_code}"
                    
                    return success, end_time - start_time, error
                    
                except Exception as e:
                    end_time = time.time()
                    return False, end_time - start_time, str(e)
            
            # Run mixed workload
            num_requests = 200
            max_workers = 20
            
            metrics.start_monitoring()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(mixed_request, i) for i in range(num_requests)]
                
                for future in as_completed(futures):
                    success, response_time, error = future.result()
                    metrics.record_response(response_time, success, error)
                    metrics.record_system_metrics()
            
            metrics.stop_monitoring()
            
            # Analyze results
            summary = metrics.get_summary()
            
            print(f"\n=== Mixed Workload Load Test Results ===")
            print(f"Total requests: {summary['total_requests']}")
            print(f"Success rate: {summary['success_rate']:.2%}")
            print(f"Requests per second: {summary['requests_per_second']:.2f}")
            print(f"Response time - Mean: {summary['response_times']['mean']:.3f}s")
            print(f"Response time - P95: {summary['response_times']['p95']:.3f}s")
            print(f"Memory usage - Max: {summary['memory_usage']['max']:.1f}MB")
            
            # Performance assertions for mixed workload
            assert summary['success_rate'] >= 0.90  # 90% success rate for mixed operations
            assert summary['response_times']['mean'] < 0.5  # Mean response time under 500ms
            assert summary['response_times']['p95'] < 1.0  # P95 under 1 second
            assert summary['requests_per_second'] > 20  # At least 20 RPS for mixed operations


class TestResourceUsage:
    """Test resource usage and memory leaks."""

    def test_memory_leak_detection(self, client):
        """Test for memory leaks during extended operation."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class:
            
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            # Record memory usage over time
            memory_samples = []
            process = psutil.Process()
            
            # Baseline memory
            gc.collect()
            baseline_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(baseline_memory)
            
            # Perform operations in batches
            batch_size = 100
            num_batches = 5
            
            for batch in range(num_batches):
                # Perform batch of operations
                for i in range(batch_size):
                    request_id = batch * batch_size + i
                    
                    token_manager_mock.validate_access_token.return_value = {
                        "sub": f"user-{request_id}",
                        "email": f"user{request_id}@example.com",
                        "full_name": f"User {request_id}",
                        "roles": ["user"],
                        "tenant_id": "default",
                        "is_verified": True
                    }
                    
                    response = client.get("/api/test/protected", headers={
                        "Authorization": f"Bearer token-{request_id}"
                    })
                    assert response.status_code == 200
                
                # Force garbage collection and record memory
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                print(f"Batch {batch + 1}: {current_memory:.1f}MB")
            
            # Analyze memory growth
            memory_growth = memory_samples[-1] - memory_samples[0]
            max_memory = max(memory_samples)
            
            print(f"\n=== Memory Leak Test Results ===")
            print(f"Baseline memory: {baseline_memory:.1f}MB")
            print(f"Final memory: {memory_samples[-1]:.1f}MB")
            print(f"Total growth: {memory_growth:.1f}MB")
            print(f"Max memory: {max_memory:.1f}MB")
            print(f"Operations: {num_batches * batch_size}")
            
            # Memory growth should be minimal
            assert memory_growth < 20  # Less than 20MB growth
            assert max_memory < baseline_memory + 30  # Peak usage reasonable

    def test_cpu_usage_under_load(self, client):
        """Test CPU usage during high load."""
        
        with patch('ai_karen_engine.middleware.session_persistence.AuthConfig'), \
             patch('ai_karen_engine.middleware.session_persistence.EnhancedTokenManager') as mock_token_manager_class:
            
            token_manager_mock = AsyncMock()
            mock_token_manager_class.return_value = token_manager_mock
            
            process = psutil.Process()
            cpu_samples = []
            
            # Monitor CPU during load
            def cpu_monitor():
                for _ in range(20):  # Monitor for 10 seconds
                    cpu_percent = process.cpu_percent(interval=0.5)
                    cpu_samples.append(cpu_percent)
            
            # Start CPU monitoring in background
            import threading
            monitor_thread = threading.Thread(target=cpu_monitor)
            monitor_thread.start()
            
            # Generate load
            num_requests = 500
            
            for i in range(num_requests):
                token_manager_mock.validate_access_token.return_value = {
                    "sub": f"user-{i}",
                    "email": f"user{i}@example.com",
                    "full_name": f"User {i}",
                    "roles": ["user"],
                    "tenant_id": "default",
                    "is_verified": True
                }
                
                response = client.get("/api/test/protected", headers={
                    "Authorization": f"Bearer token-{i}"
                })
                assert response.status_code == 200
            
            # Wait for monitoring to complete
            monitor_thread.join()
            
            # Analyze CPU usage
            if cpu_samples:
                avg_cpu = statistics.mean(cpu_samples)
                max_cpu = max(cpu_samples)
                
                print(f"\n=== CPU Usage Test Results ===")
                print(f"Requests processed: {num_requests}")
                print(f"Average CPU: {avg_cpu:.1f}%")
                print(f"Max CPU: {max_cpu:.1f}%")
                
                # CPU usage should be reasonable
                assert avg_cpu < 80  # Average CPU under 80%
                assert max_cpu < 95  # Peak CPU under 95%


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print output