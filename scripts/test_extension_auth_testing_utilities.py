"""
Test cases for Extension Authentication Testing Utilities

This module tests the authentication testing utilities to ensure they work correctly
and provide reliable testing infrastructure for extension authentication.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from fastapi import Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from server.extension_test_auth_utils import (
    TestTokenGenerator,
    MockAuthMiddleware,
    AuthTestHelper,
    AuthPerformanceTester,
    default_token_generator,
    default_auth_helper,
    default_performance_tester
)


class TestTokenGeneratorTests:
    """Test cases for TestTokenGenerator."""
    
    def test_generate_access_token_default(self):
        """Test generating access token with default parameters."""
        generator = TestTokenGenerator()
        token = generator.generate_access_token()
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = generator.decode_token(token)
        assert payload['user_id'] == 'test-user'
        assert payload['tenant_id'] == 'test-tenant'
        assert 'user' in payload['roles']
        assert 'extension:read' in payload['permissions']
        assert payload['token_type'] == 'access'
    
    def test_generate_access_token_custom(self):
        """Test generating access token with custom parameters."""
        generator = TestTokenGenerator()
        token = generator.generate_access_token(
            user_id='custom-user',
            tenant_id='custom-tenant',
            roles=['admin'],
            permissions=['*'],
            expires_in_minutes=60
        )
        
        payload = generator.decode_token(token)
        assert payload['user_id'] == 'custom-user'
        assert payload['tenant_id'] == 'custom-tenant'
        assert payload['roles'] == ['admin']
        assert payload['permissions'] == ['*']
    
    def test_generate_refresh_token(self):
        """Test generating refresh token."""
        generator = TestTokenGenerator()
        token = generator.generate_refresh_token()
        
        payload = generator.decode_token(token)
        assert payload['token_type'] == 'refresh'
        assert payload['user_id'] == 'test-user'
    
    def test_generate_expired_token(self):
        """Test generating expired token."""
        generator = TestTokenGenerator()
        token = generator.generate_expired_token()
        
        # Should be able to decode but will be expired
        payload = generator.decode_token(token)
        assert payload['user_id'] == 'test-user'
        
        # Verify it's actually expired
        import jwt
        from datetime import datetime
        exp_time = datetime.fromtimestamp(payload['exp'])
        assert exp_time < datetime.utcnow()
    
    def test_generate_invalid_token(self):
        """Test generating invalid token."""
        generator = TestTokenGenerator()
        token = generator.generate_invalid_token()
        
        assert token == "invalid.token.here"
        
        with pytest.raises(ValueError):
            generator.decode_token(token)
    
    def test_generate_admin_token(self):
        """Test generating admin token."""
        generator = TestTokenGenerator()
        token = generator.generate_admin_token()
        
        payload = generator.decode_token(token)
        assert 'admin' in payload['roles']
        assert payload['permissions'] == ['*']
    
    def test_generate_limited_token(self):
        """Test generating limited permission token."""
        generator = TestTokenGenerator()
        token = generator.generate_limited_token(
            permissions=['extension:read']
        )
        
        payload = generator.decode_token(token)
        assert payload['permissions'] == ['extension:read']
        assert payload['roles'] == ['user']


class TestMockAuthMiddleware:
    """Test cases for MockAuthMiddleware."""
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self):
        """Test successful authentication."""
        middleware = MockAuthMiddleware()
        
        mock_request = Mock()
        mock_credentials = Mock()
        
        user_context = await middleware.authenticate_request(mock_request, mock_credentials)
        
        assert user_context['user_id'] == 'test-user'
        assert user_context['tenant_id'] == 'test-tenant'
        assert middleware.call_count == 1
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure."""
        middleware = MockAuthMiddleware(should_fail=True, failure_mode="forbidden")
        
        mock_request = Mock()
        mock_credentials = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate_request(mock_request, mock_credentials)
        
        assert exc_info.value.status_code == 403
        assert "Authentication failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_different_failure_modes(self):
        """Test different failure modes."""
        middleware = MockAuthMiddleware(should_fail=True)
        mock_request = Mock()
        mock_credentials = Mock()
        
        # Test expired token failure
        middleware.set_failure_mode(True, "expired")
        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate_request(mock_request, mock_credentials)
        assert "Token expired" in str(exc_info.value.detail)
        
        # Test invalid token failure
        middleware.set_failure_mode(True, "invalid")
        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate_request(mock_request, mock_credentials)
        assert "Invalid token" in str(exc_info.value.detail)
        
        # Test service error
        middleware.set_failure_mode(True, "service_error")
        with pytest.raises(HTTPException) as exc_info:
            await middleware.authenticate_request(mock_request, mock_credentials)
        assert exc_info.value.status_code == 500
    
    @pytest.mark.asyncio
    async def test_custom_user_context(self):
        """Test setting custom user context."""
        custom_context = {
            'user_id': 'custom-user',
            'tenant_id': 'custom-tenant',
            'roles': ['admin'],
            'permissions': ['*']
        }
        
        middleware = MockAuthMiddleware(default_user_context=custom_context)
        
        mock_request = Mock()
        mock_credentials = Mock()
        
        user_context = await middleware.authenticate_request(mock_request, mock_credentials)
        
        assert user_context['user_id'] == 'custom-user'
        assert user_context['roles'] == ['admin']
    
    def test_statistics_tracking(self):
        """Test call statistics tracking."""
        middleware = MockAuthMiddleware()
        
        # Initial stats
        stats = middleware.get_stats()
        assert stats['call_count'] == 0
        
        # Reset stats
        middleware.reset_stats()
        assert middleware.call_count == 0


class TestAuthTestHelper:
    """Test cases for AuthTestHelper."""
    
    def test_get_auth_headers_default(self):
        """Test getting default auth headers."""
        helper = AuthTestHelper()
        headers = helper.get_auth_headers()
        
        assert 'Authorization' in headers
        assert headers['Authorization'].startswith('Bearer ')
        assert headers['Content-Type'] == 'application/json'
        assert headers['X-Client-Type'] == 'test-client'
    
    def test_get_auth_headers_custom_token(self):
        """Test getting auth headers with custom token."""
        helper = AuthTestHelper()
        custom_token = "custom.test.token"
        headers = helper.get_auth_headers(token=custom_token)
        
        assert headers['Authorization'] == f'Bearer {custom_token}'
    
    def test_get_admin_headers(self):
        """Test getting admin headers."""
        helper = AuthTestHelper()
        headers = helper.get_admin_headers()
        
        assert 'Authorization' in headers
        
        # Decode token to verify it's admin
        token = headers['Authorization'].replace('Bearer ', '')
        payload = helper.token_generator.decode_token(token)
        assert 'admin' in payload['roles']
        assert payload['permissions'] == ['*']
    
    def test_get_limited_headers(self):
        """Test getting limited permission headers."""
        helper = AuthTestHelper()
        headers = helper.get_limited_headers(permissions=['extension:read'])
        
        token = headers['Authorization'].replace('Bearer ', '')
        payload = helper.token_generator.decode_token(token)
        assert payload['permissions'] == ['extension:read']
    
    def test_get_expired_headers(self):
        """Test getting expired token headers."""
        helper = AuthTestHelper()
        headers = helper.get_expired_headers()
        
        token = headers['Authorization'].replace('Bearer ', '')
        payload = helper.token_generator.decode_token(token)
        
        # Verify token is expired
        from datetime import datetime
        exp_time = datetime.fromtimestamp(payload['exp'])
        assert exp_time < datetime.utcnow()
    
    def test_get_invalid_headers(self):
        """Test getting invalid token headers."""
        helper = AuthTestHelper()
        headers = helper.get_invalid_headers()
        
        assert headers['Authorization'] == 'Bearer invalid.token.here'
    
    def test_get_no_auth_headers(self):
        """Test getting headers without authentication."""
        helper = AuthTestHelper()
        headers = helper.get_no_auth_headers()
        
        assert 'Authorization' not in headers
        assert headers['Content-Type'] == 'application/json'
    
    def test_create_test_scenarios(self):
        """Test creating test scenarios."""
        helper = AuthTestHelper()
        scenarios = helper.create_test_scenarios()
        
        assert len(scenarios) == 6
        
        scenario_names = [s['name'] for s in scenarios]
        expected_names = [
            'valid_user_token', 'admin_token', 'limited_permissions',
            'expired_token', 'invalid_token', 'no_auth'
        ]
        
        for name in expected_names:
            assert name in scenario_names
        
        # Check that each scenario has required fields
        for scenario in scenarios:
            assert 'name' in scenario
            assert 'headers' in scenario
            assert 'expected_status' in scenario
            assert 'description' in scenario


class TestAuthPerformanceTester:
    """Test cases for AuthPerformanceTester."""
    
    @pytest.mark.asyncio
    async def test_measure_token_generation_performance(self):
        """Test measuring token generation performance."""
        tester = AuthPerformanceTester()
        result = await tester.measure_token_generation_performance(iterations=100)
        
        assert result['operation'] == 'token_generation'
        assert result['iterations'] == 100
        assert result['total_time_seconds'] > 0
        assert result['average_time_ms'] > 0
        assert result['tokens_per_second'] > 0
        assert result['sample_token_length'] > 0
        
        # Should be reasonably fast
        assert result['average_time_ms'] < 100  # Less than 100ms per token
    
    @pytest.mark.asyncio
    async def test_measure_token_validation_performance(self):
        """Test measuring token validation performance."""
        tester = AuthPerformanceTester()
        result = await tester.measure_token_validation_performance(iterations=100)
        
        assert result['operation'] == 'token_validation'
        assert result['iterations'] == 100
        assert result['valid_tokens'] == 100  # All should be valid
        assert result['total_time_seconds'] > 0
        assert result['average_time_ms'] > 0
        assert result['validations_per_second'] > 0
    
    @pytest.mark.asyncio
    async def test_measure_auth_middleware_performance(self):
        """Test measuring auth middleware performance."""
        tester = AuthPerformanceTester()
        
        # Create mock middleware
        mock_middleware = AsyncMock()
        mock_middleware.authenticate_request.return_value = {'user_id': 'test-user'}
        
        result = await tester.measure_auth_middleware_performance(
            mock_middleware, iterations=50
        )
        
        assert result['operation'] == 'auth_middleware'
        assert result['iterations'] == 50
        assert result['successful_auths'] == 50
        assert result['total_time_seconds'] > 0
        assert result['average_time_ms'] > 0
        assert result['auths_per_second'] > 0
    
    def test_get_performance_summary(self):
        """Test getting performance summary."""
        tester = AuthPerformanceTester()
        
        # Initially no results
        summary = tester.get_performance_summary()
        assert "No performance tests run" in summary['message']
        
        # Add some mock results
        tester.results = [
            {
                'operation': 'token_generation',
                'average_time_ms': 15,  # Slow
                'iterations': 100
            },
            {
                'operation': 'token_validation',
                'average_time_ms': 2,   # Fast
                'iterations': 100
            }
        ]
        
        summary = tester.get_performance_summary()
        assert summary['total_tests'] == 2
        assert len(summary['recommendations']) > 0
        assert any('slow' in rec.lower() for rec in summary['recommendations'])
    
    def test_reset_results(self):
        """Test resetting performance results."""
        tester = AuthPerformanceTester()
        
        # Add some results
        tester.results = [{'test': 'data'}]
        assert len(tester.results) == 1
        
        # Reset
        tester.reset_results()
        assert len(tester.results) == 0


class TestDefaultInstances:
    """Test the default instances provided for convenience."""
    
    def test_default_token_generator(self):
        """Test default token generator instance."""
        token = default_token_generator.generate_access_token()
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_default_auth_helper(self):
        """Test default auth helper instance."""
        headers = default_auth_helper.get_auth_headers()
        assert 'Authorization' in headers
    
    def test_default_performance_tester(self):
        """Test default performance tester instance."""
        summary = default_performance_tester.get_performance_summary()
        assert isinstance(summary, dict)


class TestIntegrationScenarios:
    """Integration test scenarios using the testing utilities."""
    
    @pytest.mark.asyncio
    async def test_complete_auth_flow_simulation(self):
        """Test complete authentication flow simulation."""
        # Setup
        token_generator = TestTokenGenerator()
        auth_helper = AuthTestHelper(token_generator)
        mock_middleware = MockAuthMiddleware()
        
        # Generate token
        token = token_generator.generate_access_token(
            user_id='integration-user',
            permissions=['extension:read', 'extension:write']
        )
        
        # Get headers
        headers = auth_helper.get_auth_headers(token)
        
        # Simulate middleware authentication
        mock_request = Mock()
        mock_request.url.path = '/api/extensions/'
        mock_request.method = 'GET'
        mock_request.headers = headers
        
        mock_credentials = Mock()
        mock_credentials.credentials = token
        
        user_context = await mock_middleware.authenticate_request(
            mock_request, mock_credentials
        )
        
        # Verify complete flow
        assert user_context['user_id'] == 'test-user'  # Mock returns default
        assert mock_middleware.call_count == 1
        assert headers['Authorization'] == f'Bearer {token}'
    
    @pytest.mark.asyncio
    async def test_error_scenarios_simulation(self):
        """Test error scenarios simulation."""
        auth_helper = AuthTestHelper()
        mock_middleware = MockAuthMiddleware()
        
        # Test scenarios
        scenarios = [
            ('expired_token', auth_helper.get_expired_headers(), True),
            ('invalid_token', auth_helper.get_invalid_headers(), True),
            ('no_auth', auth_helper.get_no_auth_headers(), True),
            ('valid_token', auth_helper.get_auth_headers(), False)
        ]
        
        for scenario_name, headers, should_fail in scenarios:
            mock_middleware.set_failure_mode(should_fail, 'forbidden')
            
            mock_request = Mock()
            mock_credentials = Mock() if 'Authorization' in headers else None
            
            if should_fail:
                with pytest.raises(HTTPException):
                    await mock_middleware.authenticate_request(mock_request, mock_credentials)
            else:
                user_context = await mock_middleware.authenticate_request(mock_request, mock_credentials)
                assert user_context['user_id'] == 'test-user'


if __name__ == "__main__":
    # Run basic functionality tests
    print("Testing Extension Authentication Testing Utilities...")
    
    # Test token generation
    generator = TestTokenGenerator()
    token = generator.generate_access_token()
    print(f"✓ Generated test token: {token[:50]}...")
    
    # Test auth helper
    helper = AuthTestHelper()
    headers = helper.get_auth_headers()
    print(f"✓ Generated auth headers: {len(headers)} headers")
    
    # Test scenarios
    scenarios = helper.create_test_scenarios()
    print(f"✓ Created {len(scenarios)} test scenarios")
    
    print("All basic tests passed!")