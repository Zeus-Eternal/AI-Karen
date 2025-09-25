"""
Integration tests for audit logging with authentication routes and error response service.

This module tests the integration of audit logging with the actual authentication
routes and error response service to ensure proper logging of events.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ai_karen_engine.services.audit_logging import (
    get_audit_logger,
    AuditEventType,
    AuditSeverity
)
from ai_karen_engine.auth.models import UserData
from ai_karen_engine.services.error_response_service import ErrorResponseService, ErrorCategory


class TestAuthenticationAuditIntegration:
    """Test audit logging integration with authentication routes"""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Mock audit logger for testing"""
        with patch('ai_karen_engine.services.audit_logging.get_audit_logger') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock auth service"""
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock:
            auth_service = AsyncMock()
            mock.return_value = auth_service
            yield auth_service
    
    @pytest.fixture
    def mock_token_manager(self):
        """Mock token manager"""
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_token_manager') as mock:
            token_manager = AsyncMock()
            mock.return_value = token_manager
            yield token_manager
    
    @pytest.fixture
    def mock_security_monitor(self):
        """Mock security monitor"""
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_security_monitor') as mock:
            security_monitor = AsyncMock()
            mock.return_value = security_monitor
            yield security_monitor
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return UserData(
            user_id="test_user_123",
            email="test@example.com",
            full_name="Test User",
            tenant_id="test_tenant",
            roles=["user"],
            is_verified=True,
            is_active=True,
            preferences={}
        )
    
    @pytest.fixture
    def app_with_routes(self):
        """FastAPI app with auth routes for testing"""
        app = FastAPI()
        
        # Import and include the auth routes
        from ai_karen_engine.api_routes.auth_session_routes import router
        app.include_router(router)
        
        return app
    
    def test_login_success_audit_logging(
        self, 
        app_with_routes, 
        mock_audit_logger, 
        mock_auth_service, 
        mock_token_manager,
        mock_security_monitor,
        sample_user_data
    ):
        """Test that successful login triggers audit logging"""
        # Setup mocks
        mock_auth_service.authenticate_user.return_value = sample_user_data
        mock_auth_service.create_session.return_value = Mock(session_token="session123")
        mock_token_manager.create_access_token.return_value = "access_token_123"
        mock_token_manager.create_refresh_token.return_value = "refresh_token_123"
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_mgr:
            mock_cookie_mgr.return_value = Mock()
            
            with patch('ai_karen_engine.api_routes.auth_session_routes.get_csrf_protection') as mock_csrf:
                mock_csrf.return_value = Mock()
                mock_csrf.return_value.validate_csrf_protection = AsyncMock()
                mock_csrf.return_value.generate_csrf_response.return_value = "csrf_token"
                
                client = TestClient(app_with_routes)
                
                response = client.post(
                    "/auth/login",
                    json={
                        "email": "test@example.com",
                        "password": "password123"
                    },
                    headers={"X-Forwarded-For": "192.168.1.1", "User-Agent": "TestClient/1.0"}
                )
                
                # Verify audit logging was called
                mock_audit_logger.log_login_success.assert_called_once()
                call_args = mock_audit_logger.log_login_success.call_args
                
                assert call_args[1]["user_id"] == "test_user_123"
                assert call_args[1]["email"] == "test@example.com"
                assert call_args[1]["ip_address"] == "192.168.1.1"
                assert call_args[1]["tenant_id"] == "test_tenant"
    
    def test_login_failure_audit_logging(
        self, 
        app_with_routes, 
        mock_audit_logger, 
        mock_auth_service,
        mock_security_monitor
    ):
        """Test that failed login triggers audit logging"""
        # Setup mocks for failure
        from ai_karen_engine.auth.exceptions import InvalidCredentialsError
        mock_auth_service.authenticate_user.side_effect = InvalidCredentialsError("Invalid credentials")
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_csrf_protection') as mock_csrf:
            mock_csrf.return_value = Mock()
            mock_csrf.return_value.validate_csrf_protection = AsyncMock()
            
            client = TestClient(app_with_routes)
            
            response = client.post(
                "/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrong_password"
                },
                headers={"X-Forwarded-For": "192.168.1.1", "User-Agent": "TestClient/1.0"}
            )
            
            # Verify audit logging was called
            mock_audit_logger.log_login_failure.assert_called_once()
            call_args = mock_audit_logger.log_login_failure.call_args
            
            assert call_args[1]["email"] == "test@example.com"
            assert call_args[1]["ip_address"] == "192.168.1.1"
            assert call_args[1]["failure_reason"] == "invalid_credentials"
    
    def test_token_refresh_success_audit_logging(
        self, 
        app_with_routes, 
        mock_audit_logger, 
        mock_token_manager,
        sample_user_data
    ):
        """Test that successful token refresh triggers audit logging"""
        # Setup mocks
        mock_token_manager.validate_refresh_token.return_value = {
            "sub": "test_user_123",
            "email": "test@example.com",
            "tenant_id": "test_tenant"
        }
        mock_token_manager.rotate_tokens.return_value = (
            "new_access_token",
            "new_refresh_token", 
            datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_mgr:
            mock_cookie_mgr.return_value = Mock()
            mock_cookie_mgr.return_value.get_refresh_token.return_value = "old_refresh_token"
            mock_cookie_mgr.return_value.set_refresh_token_cookie = Mock()
            
            client = TestClient(app_with_routes)
            
            response = client.post(
                "/auth/refresh",
                headers={"X-Forwarded-For": "192.168.1.1", "User-Agent": "TestClient/1.0"}
            )
            
            # Verify audit logging was called
            mock_audit_logger.log_token_refresh_success.assert_called_once()
            call_args = mock_audit_logger.log_token_refresh_success.call_args
            
            assert call_args[1]["user_id"] == "test_user_123"
            assert call_args[1]["ip_address"] == "192.168.1.1"
            assert call_args[1]["tenant_id"] == "test_tenant"
    
    def test_logout_success_audit_logging(
        self, 
        app_with_routes, 
        mock_audit_logger, 
        mock_token_manager
    ):
        """Test that successful logout triggers audit logging"""
        # Setup mocks
        mock_token_manager.validate_refresh_token.return_value = {
            "sub": "test_user_123"
        }
        mock_token_manager.revoke_token = AsyncMock()
        
        with patch('ai_karen_engine.api_routes.auth_session_routes.get_cookie_manager_instance') as mock_cookie_mgr:
            mock_cookie_mgr.return_value = Mock()
            mock_cookie_mgr.return_value.get_refresh_token.return_value = "refresh_token_123"
            mock_cookie_mgr.return_value.get_session_token.return_value = "session_token_123"
            mock_cookie_mgr.return_value.clear_all_auth_cookies = Mock()
            
            with patch('ai_karen_engine.api_routes.auth_session_routes.get_csrf_protection') as mock_csrf:
                mock_csrf.return_value = Mock()
                mock_csrf.return_value.validate_csrf_protection = AsyncMock()
                mock_csrf.return_value.clear_csrf_protection = Mock()
                
                with patch('ai_karen_engine.api_routes.auth_session_routes.get_auth_service_instance') as mock_auth:
                    mock_auth.return_value = Mock()
                    mock_auth.return_value.invalidate_session = AsyncMock()
                    
                    client = TestClient(app_with_routes)
                    
                    response = client.post(
                        "/auth/logout",
                        headers={"X-Forwarded-For": "192.168.1.1", "User-Agent": "TestClient/1.0"}
                    )
                    
                    # Verify audit logging was called
                    mock_audit_logger.log_logout_success.assert_called_once()
                    call_args = mock_audit_logger.log_logout_success.call_args
                    
                    assert call_args[1]["user_id"] == "test_user_123"
                    assert call_args[1]["ip_address"] == "192.168.1.1"


class TestTokenManagerAuditIntegration:
    """Test audit logging integration with token manager"""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Mock audit logger for testing"""
        with patch('ai_karen_engine.auth.tokens.get_audit_logger') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def token_manager(self, mock_audit_logger):
        """Token manager instance for testing"""
        from ai_karen_engine.auth.tokens import EnhancedTokenManager
        from ai_karen_engine.auth.config import JWTConfig
        
        config = JWTConfig(
            secret_key="test_secret_key_123",
            algorithm="HS256",
            access_token_expiry=timedelta(minutes=15),
            refresh_token_expiry=timedelta(days=7)
        )
        
        return EnhancedTokenManager(config)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return UserData(
            user_id="test_user_123",
            email="test@example.com",
            full_name="Test User",
            tenant_id="test_tenant",
            roles=["user"],
            is_verified=True,
            is_active=True,
            preferences={}
        )
    
    @pytest.mark.asyncio
    async def test_create_access_token_audit_logging(
        self, 
        token_manager, 
        mock_audit_logger, 
        sample_user_data
    ):
        """Test that access token creation triggers audit logging"""
        # Create access token
        token = await token_manager.create_access_token(sample_user_data)
        
        # Verify audit logging was called
        mock_audit_logger.log_token_operation_performance.assert_called_once()
        call_args = mock_audit_logger.log_token_operation_performance.call_args
        
        assert call_args[1]["operation_name"] == "create_access_token"
        assert call_args[1]["success"] is True
        assert call_args[1]["user_id"] == "test_user_123"
        assert call_args[1]["tenant_id"] == "test_tenant"
        assert "duration_ms" in call_args[1]
        assert call_args[1]["duration_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_create_refresh_token_audit_logging(
        self, 
        token_manager, 
        mock_audit_logger, 
        sample_user_data
    ):
        """Test that refresh token creation triggers audit logging"""
        # Create refresh token
        token = await token_manager.create_refresh_token(sample_user_data)
        
        # Verify audit logging was called
        mock_audit_logger.log_token_operation_performance.assert_called_once()
        call_args = mock_audit_logger.log_token_operation_performance.call_args
        
        assert call_args[1]["operation_name"] == "create_refresh_token"
        assert call_args[1]["success"] is True
        assert call_args[1]["user_id"] == "test_user_123"
        assert call_args[1]["tenant_id"] == "test_tenant"
        assert "duration_ms" in call_args[1]
        assert call_args[1]["duration_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_token_creation_failure_audit_logging(
        self, 
        mock_audit_logger, 
        sample_user_data
    ):
        """Test that token creation failures trigger audit logging"""
        from ai_karen_engine.auth.tokens import EnhancedTokenManager
        from ai_karen_engine.auth.config import JWTConfig
        
        # Create token manager with invalid config to trigger failure
        config = JWTConfig(
            secret_key="",  # Invalid empty secret key
            algorithm="HS256",
            access_token_expiry=timedelta(minutes=15),
            refresh_token_expiry=timedelta(days=7)
        )
        
        token_manager = EnhancedTokenManager(config)
        
        # Attempt to create token (should fail)
        with pytest.raises(Exception):
            await token_manager.create_access_token(sample_user_data)
        
        # Verify audit logging was called for failure
        mock_audit_logger.log_token_operation_performance.assert_called_once()
        call_args = mock_audit_logger.log_token_operation_performance.call_args
        
        assert call_args[1]["operation_name"] == "create_access_token"
        assert call_args[1]["success"] is False
        assert call_args[1]["user_id"] == "test_user_123"
        assert "error_message" in call_args[1]


class TestErrorResponseServiceAuditIntegration:
    """Test audit logging integration with error response service"""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Mock audit logger for testing"""
        with patch('ai_karen_engine.services.error_response_service.get_audit_logger') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def error_response_service(self, mock_audit_logger):
        """Error response service instance for testing"""
        return ErrorResponseService()
    
    @pytest.fixture
    def mock_response_cache(self):
        """Mock response cache"""
        with patch('ai_karen_engine.services.error_response_service.get_response_cache') as mock:
            cache = Mock()
            mock.return_value = cache
            yield cache
    
    def test_analyze_error_cache_hit_audit_logging(
        self, 
        error_response_service, 
        mock_audit_logger, 
        mock_response_cache
    ):
        """Test that cache hits trigger audit logging"""
        # Setup cache hit
        cached_response = {
            "title": "Cached Error",
            "summary": "This is a cached error response",
            "category": "authentication",
            "severity": "medium",
            "next_steps": ["Try again"],
            "contact_admin": False
        }
        mock_response_cache.get_cached_response.return_value = cached_response
        
        # Analyze error
        response = error_response_service.analyze_error(
            error_message="Authentication failed",
            error_type="AuthError",
            additional_context={"user_id": "user123", "correlation_id": "corr123"}
        )
        
        # Verify audit logging was called for cache hit
        mock_audit_logger.log_response_cache_event.assert_called_once()
        call_args = mock_audit_logger.log_response_cache_event.call_args
        
        assert call_args[1]["cache_hit"] is True
        assert call_args[1]["error_category"] == "authentication"
    
    def test_analyze_error_rule_based_response_audit_logging(
        self, 
        error_response_service, 
        mock_audit_logger, 
        mock_response_cache
    ):
        """Test that rule-based responses trigger audit logging"""
        # Setup cache miss
        mock_response_cache.get_cached_response.return_value = None
        
        # Analyze error that matches a rule
        response = error_response_service.analyze_error(
            error_message="Invalid credentials provided",
            error_type="AuthError",
            use_ai_analysis=False,
            additional_context={"user_id": "user123", "correlation_id": "corr123"}
        )
        
        # Verify audit logging was called for response generation
        mock_audit_logger.log_error_response_generated.assert_called_once()
        call_args = mock_audit_logger.log_error_response_generated.call_args
        
        assert call_args[1]["error_category"] == ErrorCategory.AUTHENTICATION.value
        assert call_args[1]["ai_analysis_used"] is False
        assert call_args[1]["response_cached"] is True
        assert call_args[1]["user_id"] == "user123"
        assert call_args[1]["correlation_id"] == "corr123"
    
    def test_analyze_error_ai_analysis_audit_logging(
        self, 
        error_response_service, 
        mock_audit_logger, 
        mock_response_cache
    ):
        """Test that AI analysis triggers audit logging"""
        # Setup cache miss
        mock_response_cache.get_cached_response.return_value = None
        
        # Mock LLM components
        with patch.object(error_response_service, '_get_llm_router') as mock_llm_router:
            with patch.object(error_response_service, '_get_llm_utils') as mock_llm_utils:
                mock_llm_router.return_value = Mock()
                mock_llm_utils.return_value = Mock()
                
                # Mock AI response
                mock_llm_router.return_value.invoke.return_value = """
                {
                    "title": "AI Generated Error",
                    "summary": "AI analysis of the error",
                    "category": "unknown",
                    "severity": "medium",
                    "next_steps": ["Contact support"]
                }
                """
                
                with patch.object(error_response_service, '_parse_ai_error_response') as mock_parse:
                    from ai_karen_engine.services.error_response_service import IntelligentErrorResponse
                    mock_parse.return_value = IntelligentErrorResponse(
                        title="AI Generated Error",
                        summary="AI analysis of the error",
                        category=ErrorCategory.UNKNOWN,
                        severity="medium",
                        next_steps=["Contact support"]
                    )
                    
                    # Analyze error with AI
                    response = error_response_service.analyze_error(
                        error_message="Unknown error occurred",
                        error_type="UnknownError",
                        use_ai_analysis=True,
                        additional_context={"user_id": "user123", "correlation_id": "corr123"}
                    )
                    
                    # Verify AI analysis request was logged
                    mock_audit_logger.log_ai_analysis_requested.assert_called_once()
                    request_call_args = mock_audit_logger.log_ai_analysis_requested.call_args
                    
                    assert request_call_args[1]["error_message"] == "Unknown error occurred"
                    assert request_call_args[1]["user_id"] == "user123"
                    assert request_call_args[1]["correlation_id"] == "corr123"
                    
                    # Verify AI analysis completion was logged
                    mock_audit_logger.log_ai_analysis_completed.assert_called_once()
                    completion_call_args = mock_audit_logger.log_ai_analysis_completed.call_args
                    
                    assert completion_call_args[1]["success"] is True
                    assert completion_call_args[1]["llm_provider"] == "openai"
                    assert completion_call_args[1]["llm_model"] == "gpt-3.5-turbo"
                    assert "generation_time_ms" in completion_call_args[1]
                    
                    # Verify response generation was logged
                    mock_audit_logger.log_error_response_generated.assert_called_once()
                    response_call_args = mock_audit_logger.log_error_response_generated.call_args
                    
                    assert response_call_args[1]["error_category"] == ErrorCategory.UNKNOWN.value
                    assert response_call_args[1]["ai_analysis_used"] is True
                    assert response_call_args[1]["user_id"] == "user123"
    
    def test_cache_response_audit_logging(
        self, 
        error_response_service, 
        mock_audit_logger, 
        mock_response_cache
    ):
        """Test that response caching triggers audit logging"""
        # Setup cache miss
        mock_response_cache.get_cached_response.return_value = None
        
        # Analyze error that will be cached
        response = error_response_service.analyze_error(
            error_message="OPENAI_API_KEY not found",
            error_type="ConfigError",
            use_ai_analysis=False
        )
        
        # Verify cache event was logged
        mock_audit_logger.log_response_cache_event.assert_called_once()
        call_args = mock_audit_logger.log_response_cache_event.call_args
        
        assert call_args[1]["cache_hit"] is False
        assert call_args[1]["error_category"] == ErrorCategory.API_KEY_MISSING.value


class TestAuditLoggingMetrics:
    """Test audit logging metrics and analytics"""
    
    @pytest.fixture
    def audit_logger(self):
        """Real audit logger instance for metrics testing"""
        return get_audit_logger()
    
    def test_event_count_tracking(self, audit_logger):
        """Test that event counts are tracked correctly"""
        # Clear existing metrics
        audit_logger.reset_metrics()
        
        # Log some events
        audit_logger.log_login_success(
            user_id="user1",
            email="user1@example.com",
            ip_address="192.168.1.1"
        )
        
        audit_logger.log_login_success(
            user_id="user2",
            email="user2@example.com",
            ip_address="192.168.1.2"
        )
        
        audit_logger.log_login_failure(
            email="user3@example.com",
            ip_address="192.168.1.3",
            failure_reason="invalid_credentials"
        )
        
        # Check metrics
        metrics = audit_logger.get_audit_metrics()
        
        assert metrics["event_counts"]["login_success"] == 2
        assert metrics["event_counts"]["login_failure"] == 1
    
    def test_performance_metrics_tracking(self, audit_logger):
        """Test that performance metrics are tracked correctly"""
        # Clear existing metrics
        audit_logger.reset_metrics()
        
        # Log some performance events
        audit_logger.log_token_operation_performance(
            operation_name="create_access_token",
            duration_ms=10.5,
            success=True,
            user_id="user1"
        )
        
        audit_logger.log_token_operation_performance(
            operation_name="create_access_token",
            duration_ms=15.2,
            success=True,
            user_id="user2"
        )
        
        audit_logger.log_llm_response_performance(
            provider="openai",
            model="gpt-3.5-turbo",
            duration_ms=1250.0,
            success=True,
            user_id="user1"
        )
        
        # Check metrics
        metrics = audit_logger.get_audit_metrics()
        
        token_metrics = metrics["performance_metrics"]["create_access_token"]
        assert token_metrics["count"] == 2
        assert token_metrics["avg_ms"] == 12.85
        assert token_metrics["min_ms"] == 10.5
        assert token_metrics["max_ms"] == 15.2
        
        llm_metrics = metrics["performance_metrics"]["llm_openai_gpt-3.5-turbo"]
        assert llm_metrics["count"] == 1
        assert llm_metrics["avg_ms"] == 1250.0
        assert llm_metrics["min_ms"] == 1250.0
        assert llm_metrics["max_ms"] == 1250.0


if __name__ == "__main__":
    pytest.main([__file__])