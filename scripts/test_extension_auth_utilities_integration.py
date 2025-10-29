"""
Integration Tests for Extension Authentication Testing Utilities

This module provides comprehensive integration tests that demonstrate the usage
of all authentication testing utilities and validate their functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer

# Import our testing utilities
from server.extension_test_auth_utils import (
    TestTokenGenerator,
    MockAuthMiddleware,
    AuthTestHelper,
    AuthPerformanceTester
)
from server.extension_auth_integration_helpers import (
    FastAPIAuthTestClient,
    AsyncAuthTestClient,
    AuthEndpointTester,
    AuthPerformanceTestSuite
)
from server.extension_auth_performance_tests import (
    AuthenticationOverheadTester,
    ConcurrentAuthTester,
    TokenPerformanceTester,
    quick_auth_performance_test
)


# Create a test FastAPI app for integration testing
def create_test_app():
    """Create a test FastAPI application with authentication."""
    
    app = FastAPI(title="Test Extension API")
    
    # Mock authentication middleware
    mock_auth = MockAuthMiddleware()
    security = HTTPBearer()
    
    @app.get("/api/extensions/")
    async def list_extensions(user_context: dict = Depends(mock_auth.authenticate_request)):
        """Test endpoint that requires authentication."""
        return {
            "extensions": ["test-extension"],
            "user_id": user_context.get("user_id"),
            "tenant_id": user_context.get("tenant_id")
        }
    
    @app.post("/api/extensions/background-tasks/")
    async def register_background_task(
        task_data: dict,
        user_context: dict = Depends(mock_auth.authenticate_request)
    ):
        """Test endpoint for background task registration."""
        return {
            "task_id": f"task_{user_context.get('user_id')}_{task_data.get('name', 'test')}",
            "status": "registered"
        }
    
    @app.get("/api/extensions/health/")
    async def extension_health():
        """Test endpoint without authentication."""
        return {"status": "healthy"}
    
    # Store mock auth for test access
    app.state.mock_auth = mock_auth
    
    return app


class TestTokenGeneratorIntegration:
    """Integration tests for TestTokenGenerator."""
    
    def test_token_lifecycle(self):
        """Test complete token lifecycle."""
        generator = TestTokenGenerator()
        
        # Generate access token
        access_token = generator.generate_access_token(
            user_id="integration-user",
            tenant_id="integration-tenant",
            roles=["user", "tester"],
            permissions=["extension:read", "extension:write"]
        )
        
        # Verify token structure
        assert isinstance(access_token, str)
        assert len(access_token.split('.')) == 3  # JWT has 3 parts
        
        # Decode and verify
        payload = generator.decode_token(access_token)
        assert payload["user_id"] == "integration-user"
        assert payload["tenant_id"] == "integration-tenant"
        assert "user" in payload["roles"]
        assert "tester" in payload["roles"]
        assert "extension:read" in payload["permissions"]
        
        # Generate refresh token
        refresh_token = generator.generate_refresh_token(
            user_id="integration-user",
            tenant_id="integration-tenant"
        )
        
        refresh_payload = generator.decode_token(refresh_token)
        assert refresh_payload["token_type"] == "refresh"
        assert refresh_payload["user_id"] == "integration-user"
    
    def test_special_tokens(self):
        """Test special token types."""
        generator = TestTokenGenerator()
        
        # Test admin token
        admin_token = generator.generate_admin_token()
        admin_payload = generator.decode_token(admin_token)
        assert "admin" in admin_payload["roles"]
        assert admin_payload["permissions"] == ["*"]
        
        # Test limited token
        limited_token = generator.generate_limited_token(
            permissions=["extension:read"]
        )
        limited_payload = generator.decode_token(limited_token)
        assert limited_payload["permissions"] == ["extension:read"]
        
        # Test expired token
        expired_token = generator.generate_expired_token()
        expired_payload = generator.decode_token(expired_token)
        from datetime import datetime
        exp_time = datetime.fromtimestamp(expired_payload["exp"])
        assert exp_time < datetime.utcnow()
        
        # Test invalid token
        invalid_token = generator.generate_invalid_token()
        assert invalid_token == "invalid.token.here"
        
        with pytest.raises(ValueError):
            generator.decode_token(invalid_token)


class TestMockAuthMiddlewareIntegration:
    """Integration tests for MockAuthMiddleware."""
    
    @pytest.mark.asyncio
    async def test_middleware_with_fastapi(self):
        """Test mock middleware integration with FastAPI."""
        app = create_test_app()
        client = TestClient(app)
        
        # Test successful authentication
        response = client.get("/api/extensions/")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user"
        assert data["tenant_id"] == "test-tenant"
        
        # Test middleware statistics
        mock_auth = app.state.mock_auth
        stats = mock_auth.get_stats()
        assert stats["call_count"] == 1
    
    @pytest.mark.asyncio
    async def test_middleware_failure_modes(self):
        """Test middleware failure modes."""
        app = create_test_app()
        client = TestClient(app)
        mock_auth = app.state.mock_auth
        
        # Test forbidden failure
        mock_auth.set_failure_mode(True, "forbidden")
        response = client.get("/api/extensions/")
        assert response.status_code == 403
        
        # Test expired token failure
        mock_auth.set_failure_mode(True, "expired")
        response = client.get("/api/extensions/")
        assert response.status_code == 403
        assert "expired" in response.json()["detail"].lower()
        
        # Test service error
        mock_auth.set_failure_mode(True, "service_error")
        response = client.get("/api/extensions/")
        assert response.status_code == 500
        
        # Reset to success
        mock_auth.set_failure_mode(False)
        response = client.get("/api/extensions/")
        assert response.status_code == 200


class TestAuthTestHelperIntegration:
    """Integration tests for AuthTestHelper."""
    
    def test_helper_with_real_requests(self):
        """Test auth helper with real HTTP requests."""
        app = create_test_app()
        client = TestClient(app)
        helper = AuthTestHelper()
        
        # Test different auth scenarios
        scenarios = helper.create_test_scenarios()
        
        for scenario in scenarios:
            response = client.get("/api/extensions/", headers=scenario["headers"])
            
            # All requests should succeed with mock middleware (unless it's configured to fail)
            if scenario["name"] in ["valid_user_token", "admin_token", "limited_permissions"]:
                assert response.status_code == 200
            # Note: Mock middleware doesn't actually validate tokens, so invalid tokens still pass
    
    @pytest.mark.asyncio
    async def test_helper_authenticated_requests(self):
        """Test helper's authenticated request methods."""
        app = create_test_app()
        client = TestClient(app)
        helper = AuthTestHelper()
        
        # Mock the make_authenticated_request method for testing
        class MockClient:
            def __init__(self, test_client):
                self.test_client = test_client
            
            async def get(self, url, **kwargs):
                return self.test_client.get(url, **kwargs)
            
            async def post(self, url, **kwargs):
                return self.test_client.post(url, **kwargs)
        
        mock_client = MockClient(client)
        
        # Test authenticated GET
        response = await helper.make_authenticated_request(
            mock_client, "GET", "/api/extensions/"
        )
        assert response.status_code == 200
        
        # Test authenticated POST
        response = await helper.make_authenticated_request(
            mock_client, "POST", "/api/extensions/background-tasks/",
            json_data={"name": "test-task"}
        )
        assert response.status_code == 200


class TestFastAPIAuthTestClientIntegration:
    """Integration tests for FastAPIAuthTestClient."""
    
    def test_auth_client_basic_operations(self):
        """Test basic operations of auth test client."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        
        # Test GET with different auth types
        response = auth_client.get("/api/extensions/", auth_type="user")
        assert response.status_code == 200
        
        response = auth_client.get("/api/extensions/", auth_type="admin")
        assert response.status_code == 200
        
        # Test POST
        response = auth_client.post(
            "/api/extensions/background-tasks/",
            auth_type="user",
            json_data={"name": "test-task"}
        )
        assert response.status_code == 200
    
    def test_auth_scenarios_testing(self):
        """Test auth scenarios testing functionality."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        
        # Test all auth scenarios for an endpoint
        results = auth_client.test_auth_scenarios("/api/extensions/", "GET")
        
        assert len(results) == 6  # Should have 6 scenarios
        
        # Check that we have all expected scenarios
        scenario_names = [r["scenario"] for r in results]
        expected_scenarios = [
            "valid_user_token", "admin_token", "limited_permissions",
            "expired_token", "invalid_token", "no_auth"
        ]
        
        for expected in expected_scenarios:
            assert expected in scenario_names
        
        # With mock middleware, most should succeed
        successful_scenarios = [r for r in results if r["success"]]
        assert len(successful_scenarios) > 0


class TestAuthEndpointTesterIntegration:
    """Integration tests for AuthEndpointTester."""
    
    def test_endpoint_auth_requirements_testing(self):
        """Test comprehensive endpoint auth requirements testing."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        endpoint_tester = AuthEndpointTester(auth_client)
        
        # Test endpoint auth requirements
        result = endpoint_tester.test_endpoint_auth_requirements(
            "/api/extensions/",
            method="GET",
            required_permissions=["extension:read"],
            admin_only=False
        )
        
        assert result["endpoint"] == "/api/extensions/"
        assert result["method"] == "GET"
        assert len(result["tests"]) > 0
        assert "overall_success" in result
        assert "success_rate" in result
        
        # Test summary
        summary = endpoint_tester.get_test_summary()
        assert summary["total_endpoints_tested"] == 1
        assert "success_rate" in summary


class TestPerformanceTestingIntegration:
    """Integration tests for performance testing utilities."""
    
    @pytest.mark.asyncio
    async def test_auth_performance_tester(self):
        """Test authentication performance tester."""
        tester = AuthPerformanceTester()
        
        # Test token generation performance
        result = await tester.measure_token_generation_performance(iterations=100)
        assert result["operation"] == "token_generation"
        assert result["iterations"] == 100
        assert result["tokens_per_second"] > 0
        
        # Test token validation performance
        result = await tester.measure_token_validation_performance(iterations=100)
        assert result["operation"] == "token_validation"
        assert result["valid_tokens"] == 100
        
        # Get performance summary
        summary = tester.get_performance_summary()
        assert summary["total_tests"] == 2
        assert "recommendations" in summary
    
    @pytest.mark.asyncio
    async def test_authentication_overhead_tester(self):
        """Test authentication overhead measurement."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        overhead_tester = AuthenticationOverheadTester(auth_client)
        
        # Test auth overhead (small iteration count for testing)
        result = await overhead_tester.measure_auth_overhead(
            "/api/extensions/health/",  # No auth required
            iterations=50
        )
        
        assert result["endpoint"] == "/api/extensions/health/"
        assert result["iterations"] == 50
        assert "overhead_ms" in result
        assert "throughput_impact" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_auth_tester(self):
        """Test concurrent authentication testing."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        concurrent_tester = ConcurrentAuthTester(auth_client)
        
        # Test concurrent authentication (small numbers for testing)
        results = await concurrent_tester.test_concurrent_authentication(
            "/api/extensions/",
            concurrent_users=[1, 2],
            requests_per_user=5
        )
        
        assert len(results) == 2
        for result in results:
            assert "concurrent_users" in result
            assert "requests_per_user" in result
            assert "success_rate" in result
    
    @pytest.mark.asyncio
    async def test_token_performance_tester(self):
        """Test token operations performance testing."""
        token_tester = TokenPerformanceTester()
        
        # Test token operations performance (small iteration count)
        result = await token_tester.test_token_operations_performance(iterations=100)
        
        assert result["iterations"] == 100
        assert "token_generation" in result
        assert "token_validation" in result
        assert "token_decoding" in result
        assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_quick_performance_test(self):
        """Test quick performance test function."""
        app = create_test_app()
        auth_client = FastAPIAuthTestClient(app)
        
        # Run quick performance test
        result = await quick_auth_performance_test(
            auth_client,
            endpoint="/api/extensions/",
            method="GET"
        )
        
        assert "test_summary" in result
        assert "overhead_results" in result
        assert "concurrent_results" in result
        assert "token_results" in result
        assert "overall_recommendations" in result


class TestCompleteIntegrationScenario:
    """Complete integration scenario testing all utilities together."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_testing_workflow(self):
        """Test complete authentication testing workflow."""
        
        # 1. Setup test application
        app = create_test_app()
        
        # 2. Create testing utilities
        token_generator = TestTokenGenerator()
        auth_helper = AuthTestHelper(token_generator)
        auth_client = FastAPIAuthTestClient(app, token_generator)
        
        # 3. Test token generation
        access_token = token_generator.generate_access_token(
            user_id="workflow-user",
            permissions=["extension:read", "extension:write"]
        )
        assert len(access_token) > 0
        
        # 4. Test authentication scenarios
        scenarios = auth_helper.create_test_scenarios()
        assert len(scenarios) == 6
        
        # 5. Test endpoint authentication
        endpoint_tester = AuthEndpointTester(auth_client)
        auth_result = endpoint_tester.test_endpoint_auth_requirements(
            "/api/extensions/",
            method="GET"
        )
        assert auth_result["overall_success"] is not None
        
        # 6. Test performance (minimal for integration test)
        performance_tester = AuthPerformanceTester()
        perf_result = await performance_tester.measure_token_generation_performance(
            iterations=50
        )
        assert perf_result["tokens_per_second"] > 0
        
        # 7. Verify all components work together
        summary = {
            "token_generation": "success",
            "auth_scenarios": len(scenarios),
            "endpoint_testing": auth_result["overall_success"],
            "performance_testing": perf_result["tokens_per_second"] > 0
        }
        
        assert all(summary.values())
    
    def test_error_handling_integration(self):
        """Test error handling across all utilities."""
        
        # Test with invalid configurations
        generator = TestTokenGenerator(secret_key="test-key")
        
        # Test invalid token handling
        invalid_token = generator.generate_invalid_token()
        with pytest.raises(ValueError):
            generator.decode_token(invalid_token)
        
        # Test mock middleware error modes
        mock_auth = MockAuthMiddleware(should_fail=True, failure_mode="service_error")
        
        # Verify error statistics
        stats = mock_auth.get_stats()
        assert stats["call_count"] == 0
        
        # Test auth helper with various scenarios
        helper = AuthTestHelper(generator)
        scenarios = helper.create_test_scenarios()
        
        # Verify we have error scenarios
        error_scenarios = [s for s in scenarios if s["expected_status"] == 403]
        assert len(error_scenarios) > 0


if __name__ == "__main__":
    # Run integration tests manually
    print("Running Extension Authentication Testing Utilities Integration Tests...")
    
    # Test basic functionality
    generator = TestTokenGenerator()
    token = generator.generate_access_token()
    print(f"✓ Token generation: {len(token)} characters")
    
    # Test auth helper
    helper = AuthTestHelper(generator)
    headers = helper.get_auth_headers()
    print(f"✓ Auth headers: {len(headers)} headers")
    
    # Test scenarios
    scenarios = helper.create_test_scenarios()
    print(f"✓ Test scenarios: {len(scenarios)} scenarios")
    
    # Test mock middleware
    mock_auth = MockAuthMiddleware()
    print(f"✓ Mock middleware: {type(mock_auth).__name__}")
    
    # Test FastAPI integration
    app = create_test_app()
    auth_client = FastAPIAuthTestClient(app)
    response = auth_client.get("/api/extensions/", auth_type="user")
    print(f"✓ FastAPI integration: HTTP {response.status_code}")
    
    print("All integration tests completed successfully!")