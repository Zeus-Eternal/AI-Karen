"""
Extension Authentication Integration Test Helpers

This module provides specialized helpers for integration testing of extension
authentication with FastAPI applications and real HTTP clients.
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
import pytest
import logging

from server.extension_test_auth_utils import (
    TestTokenGenerator,
    MockAuthMiddleware,
    AuthTestHelper
)

logger = logging.getLogger(__name__)


class FastAPIAuthTestClient:
    """Enhanced test client for FastAPI applications with authentication support."""
    
    def __init__(self, app: FastAPI, token_generator: TestTokenGenerator = None):
        self.app = app
        self.client = TestClient(app)
        self.token_generator = token_generator or TestTokenGenerator()
        self.auth_helper = AuthTestHelper(self.token_generator)
    
    def get(self, url: str, auth_type: str = "user", **kwargs) -> httpx.Response:
        """Make authenticated GET request."""
        headers = self._get_headers_for_auth_type(auth_type)
        return self.client.get(url, headers=headers, **kwargs)
    
    def post(self, url: str, auth_type: str = "user", json_data: Dict = None, **kwargs) -> httpx.Response:
        """Make authenticated POST request."""
        headers = self._get_headers_for_auth_type(auth_type)
        return self.client.post(url, headers=headers, json=json_data, **kwargs)
    
    def put(self, url: str, auth_type: str = "user", json_data: Dict = None, **kwargs) -> httpx.Response:
        """Make authenticated PUT request."""
        headers = self._get_headers_for_auth_type(auth_type)
        return self.client.put(url, headers=headers, json=json_data, **kwargs)
    
    def delete(self, url: str, auth_type: str = "user", **kwargs) -> httpx.Response:
        """Make authenticated DELETE request."""
        headers = self._get_headers_for_auth_type(auth_type)
        return self.client.delete(url, headers=headers, **kwargs)
    
    def _get_headers_for_auth_type(self, auth_type: str) -> Dict[str, str]:
        """Get headers for specific auth type."""
        if auth_type == "admin":
            return self.auth_helper.get_admin_headers()
        elif auth_type == "limited":
            return self.auth_helper.get_limited_headers()
        elif auth_type == "expired":
            return self.auth_helper.get_expired_headers()
        elif auth_type == "invalid":
            return self.auth_helper.get_invalid_headers()
        elif auth_type == "none":
            return self.auth_helper.get_no_auth_headers()
        else:  # "user" or default
            return self.auth_helper.get_auth_headers()
    
    def test_auth_scenarios(self, url: str, method: str = "GET") -> List[Dict[str, Any]]:
        """Test all authentication scenarios for an endpoint."""
        scenarios = self.auth_helper.create_test_scenarios()
        results = []
        
        for scenario in scenarios:
            try:
                if method.upper() == "GET":
                    response = self.client.get(url, headers=scenario["headers"])
                elif method.upper() == "POST":
                    response = self.client.post(url, headers=scenario["headers"], json={})
                elif method.upper() == "PUT":
                    response = self.client.put(url, headers=scenario["headers"], json={})
                elif method.upper() == "DELETE":
                    response = self.client.delete(url, headers=scenario["headers"])
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                results.append({
                    "scenario": scenario["name"],
                    "expected_status": scenario["expected_status"],
                    "actual_status": response.status_code,
                    "success": response.status_code == scenario["expected_status"],
                    "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                    "description": scenario["description"]
                })
                
            except Exception as e:
                results.append({
                    "scenario": scenario["name"],
                    "expected_status": scenario["expected_status"],
                    "actual_status": None,
                    "success": False,
                    "error": str(e),
                    "description": scenario["description"]
                })
        
        return results


class AsyncAuthTestClient:
    """Async test client for testing with real HTTP requests."""
    
    def __init__(self, base_url: str, token_generator: TestTokenGenerator = None):
        self.base_url = base_url.rstrip('/')
        self.token_generator = token_generator or TestTokenGenerator()
        self.auth_helper = AuthTestHelper(self.token_generator)
    
    @asynccontextmanager
    async def client_session(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """Create async HTTP client session."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    async def get(self, endpoint: str, auth_type: str = "user", **kwargs) -> httpx.Response:
        """Make authenticated async GET request."""
        headers = self._get_headers_for_auth_type(auth_type)
        url = f"{self.base_url}{endpoint}"
        
        async with self.client_session() as client:
            return await client.get(url, headers=headers, **kwargs)
    
    async def post(self, endpoint: str, auth_type: str = "user", json_data: Dict = None, **kwargs) -> httpx.Response:
        """Make authenticated async POST request."""
        headers = self._get_headers_for_auth_type(auth_type)
        url = f"{self.base_url}{endpoint}"
        
        async with self.client_session() as client:
            return await client.post(url, headers=headers, json=json_data, **kwargs)
    
    async def put(self, endpoint: str, auth_type: str = "user", json_data: Dict = None, **kwargs) -> httpx.Response:
        """Make authenticated async PUT request."""
        headers = self._get_headers_for_auth_type(auth_type)
        url = f"{self.base_url}{endpoint}"
        
        async with self.client_session() as client:
            return await client.put(url, headers=headers, json=json_data, **kwargs)
    
    async def delete(self, endpoint: str, auth_type: str = "user", **kwargs) -> httpx.Response:
        """Make authenticated async DELETE request."""
        headers = self._get_headers_for_auth_type(auth_type)
        url = f"{self.base_url}{endpoint}"
        
        async with self.client_session() as client:
            return await client.delete(url, headers=headers, **kwargs)
    
    def _get_headers_for_auth_type(self, auth_type: str) -> Dict[str, str]:
        """Get headers for specific auth type."""
        if auth_type == "admin":
            return self.auth_helper.get_admin_headers()
        elif auth_type == "limited":
            return self.auth_helper.get_limited_headers()
        elif auth_type == "expired":
            return self.auth_helper.get_expired_headers()
        elif auth_type == "invalid":
            return self.auth_helper.get_invalid_headers()
        elif auth_type == "none":
            return self.auth_helper.get_no_auth_headers()
        else:  # "user" or default
            return self.auth_helper.get_auth_headers()
    
    async def test_auth_scenarios_async(self, endpoint: str, method: str = "GET") -> List[Dict[str, Any]]:
        """Test all authentication scenarios asynchronously."""
        scenarios = self.auth_helper.create_test_scenarios()
        results = []
        
        async with self.client_session() as client:
            for scenario in scenarios:
                try:
                    url = f"{self.base_url}{endpoint}"
                    
                    if method.upper() == "GET":
                        response = await client.get(url, headers=scenario["headers"])
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=scenario["headers"], json={})
                    elif method.upper() == "PUT":
                        response = await client.put(url, headers=scenario["headers"], json={})
                    elif method.upper() == "DELETE":
                        response = await client.delete(url, headers=scenario["headers"])
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    results.append({
                        "scenario": scenario["name"],
                        "expected_status": scenario["expected_status"],
                        "actual_status": response.status_code,
                        "success": response.status_code == scenario["expected_status"],
                        "response_data": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                        "description": scenario["description"]
                    })
                    
                except Exception as e:
                    results.append({
                        "scenario": scenario["name"],
                        "expected_status": scenario["expected_status"],
                        "actual_status": None,
                        "success": False,
                        "error": str(e),
                        "description": scenario["description"]
                    })
        
        return results


class AuthTestFixtures:
    """Pytest fixtures for authentication testing."""
    
    @staticmethod
    @pytest.fixture
    def token_generator():
        """Fixture providing test token generator."""
        return TestTokenGenerator()
    
    @staticmethod
    @pytest.fixture
    def auth_helper(token_generator):
        """Fixture providing auth test helper."""
        return AuthTestHelper(token_generator)
    
    @staticmethod
    @pytest.fixture
    def mock_auth_middleware():
        """Fixture providing mock auth middleware."""
        return MockAuthMiddleware()
    
    @staticmethod
    @pytest.fixture
    def failing_auth_middleware():
        """Fixture providing failing auth middleware."""
        return MockAuthMiddleware(should_fail=True)
    
    @staticmethod
    @pytest.fixture
    def admin_auth_middleware():
        """Fixture providing admin auth middleware."""
        return MockAuthMiddleware(default_user_context={
            'user_id': 'admin-user',
            'tenant_id': 'test-tenant',
            'roles': ['admin'],
            'permissions': ['*'],
            'token_type': 'access'
        })


class AuthEndpointTester:
    """Utility for comprehensive endpoint authentication testing."""
    
    def __init__(self, client: FastAPIAuthTestClient):
        self.client = client
        self.test_results = []
    
    def test_endpoint_auth_requirements(
        self,
        endpoint: str,
        method: str = "GET",
        required_permissions: List[str] = None,
        admin_only: bool = False
    ) -> Dict[str, Any]:
        """Test endpoint authentication requirements comprehensively."""
        
        results = {
            "endpoint": endpoint,
            "method": method,
            "required_permissions": required_permissions,
            "admin_only": admin_only,
            "tests": []
        }
        
        # Test no authentication
        response = self._make_request(endpoint, method, "none")
        results["tests"].append({
            "test": "no_auth",
            "expected": 403,
            "actual": response.status_code,
            "passed": response.status_code == 403
        })
        
        # Test invalid token
        response = self._make_request(endpoint, method, "invalid")
        results["tests"].append({
            "test": "invalid_token",
            "expected": 403,
            "actual": response.status_code,
            "passed": response.status_code == 403
        })
        
        # Test expired token
        response = self._make_request(endpoint, method, "expired")
        results["tests"].append({
            "test": "expired_token",
            "expected": 403,
            "actual": response.status_code,
            "passed": response.status_code == 403
        })
        
        # Test valid user token
        response = self._make_request(endpoint, method, "user")
        expected_status = 403 if admin_only else 200
        results["tests"].append({
            "test": "valid_user_token",
            "expected": expected_status,
            "actual": response.status_code,
            "passed": response.status_code == expected_status
        })
        
        # Test admin token
        response = self._make_request(endpoint, method, "admin")
        results["tests"].append({
            "test": "admin_token",
            "expected": 200,
            "actual": response.status_code,
            "passed": response.status_code == 200
        })
        
        # Test limited permissions if specified
        if required_permissions:
            response = self._make_request(endpoint, method, "limited")
            expected_status = 403 if any(perm not in ["extension:read"] for perm in required_permissions) else 200
            results["tests"].append({
                "test": "limited_permissions",
                "expected": expected_status,
                "actual": response.status_code,
                "passed": response.status_code == expected_status
            })
        
        # Calculate overall success
        results["overall_success"] = all(test["passed"] for test in results["tests"])
        results["success_rate"] = sum(1 for test in results["tests"] if test["passed"]) / len(results["tests"])
        
        self.test_results.append(results)
        return results
    
    def _make_request(self, endpoint: str, method: str, auth_type: str) -> httpx.Response:
        """Make request with specified auth type."""
        if method.upper() == "GET":
            return self.client.get(endpoint, auth_type=auth_type)
        elif method.upper() == "POST":
            return self.client.post(endpoint, auth_type=auth_type, json_data={})
        elif method.upper() == "PUT":
            return self.client.put(endpoint, auth_type=auth_type, json_data={})
        elif method.upper() == "DELETE":
            return self.client.delete(endpoint, auth_type=auth_type)
        else:
            raise ValueError(f"Unsupported method: {method}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all endpoint tests."""
        if not self.test_results:
            return {"message": "No tests run"}
        
        total_tests = len(self.test_results)
        successful_endpoints = sum(1 for result in self.test_results if result["overall_success"])
        
        return {
            "total_endpoints_tested": total_tests,
            "successful_endpoints": successful_endpoints,
            "success_rate": successful_endpoints / total_tests,
            "failed_endpoints": [
                result["endpoint"] for result in self.test_results 
                if not result["overall_success"]
            ],
            "detailed_results": self.test_results
        }


class AuthPerformanceTestSuite:
    """Performance testing suite for authentication systems."""
    
    def __init__(self, client: FastAPIAuthTestClient):
        self.client = client
        self.performance_results = []
    
    async def run_auth_performance_test(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_requests: int = 10,
        total_requests: int = 100
    ) -> Dict[str, Any]:
        """Run performance test with authentication."""
        
        import time
        
        start_time = time.time()
        successful_requests = 0
        failed_requests = 0
        response_times = []
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def make_single_request():
            nonlocal successful_requests, failed_requests
            
            async with semaphore:
                request_start = time.time()
                try:
                    if method.upper() == "GET":
                        response = self.client.get(endpoint, auth_type="user")
                    elif method.upper() == "POST":
                        response = self.client.post(endpoint, auth_type="user", json_data={})
                    else:
                        raise ValueError(f"Unsupported method: {method}")
                    
                    request_time = time.time() - request_start
                    response_times.append(request_time)
                    
                    if response.status_code < 400:
                        successful_requests += 1
                    else:
                        failed_requests += 1
                        
                except Exception as e:
                    failed_requests += 1
                    logger.error(f"Request failed: {e}")
        
        # Run concurrent requests
        tasks = [make_single_request() for _ in range(total_requests)]
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        result = {
            "endpoint": endpoint,
            "method": method,
            "total_requests": total_requests,
            "concurrent_requests": concurrent_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time_seconds": total_time,
            "requests_per_second": total_requests / total_time,
            "average_response_time_ms": (sum(response_times) / len(response_times)) * 1000 if response_times else 0,
            "min_response_time_ms": min(response_times) * 1000 if response_times else 0,
            "max_response_time_ms": max(response_times) * 1000 if response_times else 0,
            "success_rate": successful_requests / total_requests
        }
        
        self.performance_results.append(result)
        return result
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance test summary."""
        if not self.performance_results:
            return {"message": "No performance tests run"}
        
        total_requests = sum(r["total_requests"] for r in self.performance_results)
        total_successful = sum(r["successful_requests"] for r in self.performance_results)
        avg_rps = sum(r["requests_per_second"] for r in self.performance_results) / len(self.performance_results)
        avg_response_time = sum(r["average_response_time_ms"] for r in self.performance_results) / len(self.performance_results)
        
        return {
            "total_tests": len(self.performance_results),
            "total_requests": total_requests,
            "total_successful_requests": total_successful,
            "overall_success_rate": total_successful / total_requests,
            "average_requests_per_second": avg_rps,
            "average_response_time_ms": avg_response_time,
            "detailed_results": self.performance_results,
            "recommendations": self._generate_performance_recommendations()
        }
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on results."""
        recommendations = []
        
        for result in self.performance_results:
            if result["success_rate"] < 0.95:
                recommendations.append(
                    f"Endpoint {result['endpoint']} has low success rate ({result['success_rate']:.2%})"
                )
            
            if result["average_response_time_ms"] > 1000:
                recommendations.append(
                    f"Endpoint {result['endpoint']} has slow response time ({result['average_response_time_ms']:.1f}ms)"
                )
            
            if result["requests_per_second"] < 10:
                recommendations.append(
                    f"Endpoint {result['endpoint']} has low throughput ({result['requests_per_second']:.1f} RPS)"
                )
        
        return recommendations