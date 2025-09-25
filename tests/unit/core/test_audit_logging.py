"""
Tests for comprehensive audit logging system.

This module tests all aspects of the audit logging system including
authentication events, intelligent response tracking, session lifecycle,
and performance metrics.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.audit_logging import (
    AuditLogger,
    AuditEvent,
    AuthenticationAuditEvent,
    IntelligentResponseAuditEvent,
    PerformanceAuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger
)
from ai_karen_engine.services.structured_logging import SecurityEventType


class TestAuditLogger:
    """Test cases for AuditLogger class"""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger instance for testing"""
        return AuditLogger()
    
    @pytest.fixture
    def mock_structured_logging(self):
        """Mock structured logging service"""
        with patch('ai_karen_engine.services.audit_logging.get_structured_logging_service') as mock:
            yield mock.return_value
    
    @pytest.fixture
    def mock_security_logger(self):
        """Mock security logger"""
        with patch('ai_karen_engine.services.audit_logging.get_security_logger') as mock:
            yield mock.return_value
    
    def test_audit_logger_initialization(self, audit_logger):
        """Test audit logger initializes correctly"""
        assert audit_logger is not None
        assert hasattr(audit_logger, 'structured_logging')
        assert hasattr(audit_logger, 'security_logger')
        assert hasattr(audit_logger, 'audit_logger')
        assert hasattr(audit_logger, 'performance_logger')
        assert hasattr(audit_logger, 'auth_logger')
        assert hasattr(audit_logger, 'response_logger')
        assert isinstance(audit_logger._event_counts, dict)
        assert isinstance(audit_logger._performance_metrics, dict)
    
    def test_log_audit_event_basic(self, audit_logger):
        """Test basic audit event logging"""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Test login success",
            user_id="test_user",
            ip_address="192.168.1.1"
        )
        
        # Should not raise exception
        audit_logger.log_audit_event(event)
        
        # Check event count tracking
        assert audit_logger._event_counts[AuditEventType.LOGIN_SUCCESS.value] == 1
    
    def test_log_audit_event_pii_redaction(self, audit_logger):
        """Test PII redaction in audit events"""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Test login success",
            user_id="test_user",
            session_id="sensitive_session_123",
            metadata={
                "email": "user@example.com",
                "password": "secret123",
                "api_key": "sk-1234567890abcdef"
            }
        )
        
        with patch.object(audit_logger.audit_logger, 'info') as mock_log:
            audit_logger.log_audit_event(event)
            
            # Verify logging was called
            mock_log.assert_called_once()
            
            # Check that session_id was hashed and removed
            call_args = mock_log.call_args
            extra = call_args[1]
            audit_event_data = extra['audit_event']
            
            assert 'session_id' not in audit_event_data
            assert 'session_id_hash' in audit_event_data
            assert audit_event_data['session_id_hash'] is not None
    
    def test_log_login_success(self, audit_logger):
        """Test successful login audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_login_success(
                user_id="user123",
                email="test@example.com",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123",
                session_id="session123",
                previous_login=datetime.now(timezone.utc) - timedelta(days=1),
                login_count=5,
                logged_by="test_component"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.LOGIN_SUCCESS
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.email == "test@example.com"
            assert event.ip_address == "192.168.1.1"
            assert event.login_count == 5
            assert event.metadata["logged_by"] == "test_component"
    
    def test_log_login_failure(self, audit_logger):
        """Test failed login audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_login_failure(
                email="test@example.com",
                ip_address="192.168.1.1",
                failure_reason="invalid_credentials",
                user_agent="Mozilla/5.0",
                correlation_id="corr123",
                attempt_count=3,
                logged_by="test_component"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.LOGIN_FAILURE
            assert event.severity == AuditSeverity.WARNING
            assert event.email == "test@example.com"
            assert event.failure_reason == "invalid_credentials"
            assert event.metadata["attempt_count"] == 3
            assert event.metadata["logged_by"] == "test_component"
    
    def test_log_login_failure_security_event(self, audit_logger):
        """Test that multiple login failures trigger security event"""
        with patch.object(audit_logger.security_logger, 'log_security_event') as mock_security_event:
            audit_logger.log_login_failure(
                email="test@example.com",
                ip_address="192.168.1.1",
                failure_reason="invalid_credentials",
                attempt_count=5  # Should trigger security event
            )
            
            # Verify security event was logged
            mock_security_event.assert_called_once()
            security_event = mock_security_event.call_args[0][0]
            assert security_event.event_type == SecurityEventType.AUTHENTICATION_FAILURE
            assert security_event.severity == "HIGH"
    
    def test_log_logout_success(self, audit_logger):
        """Test successful logout audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_logout_success(
                user_id="user123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123",
                session_id="session123",
                session_duration_minutes=45.5,
                logged_by="test_component"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.LOGOUT_SUCCESS
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.metadata["session_duration_minutes"] == 45.5
            assert event.metadata["logged_by"] == "test_component"
    
    def test_log_token_refresh_success(self, audit_logger):
        """Test successful token refresh audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_token_refresh_success(
                user_id="user123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123",
                old_token_jti="old_jti_123",
                new_token_jti="new_jti_456"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.REFRESH_SUCCESS
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.token_type == "refresh"
            assert "old_token_jti_hash" in event.metadata
            assert "new_token_jti_hash" in event.metadata
    
    def test_log_token_refresh_failure(self, audit_logger):
        """Test failed token refresh audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_token_refresh_failure(
                ip_address="192.168.1.1",
                failure_reason="token_expired",
                user_agent="Mozilla/5.0",
                correlation_id="corr123",
                token_jti="expired_jti_123"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.REFRESH_FAILURE
            assert event.severity == AuditSeverity.WARNING
            assert event.failure_reason == "token_expired"
            assert "token_jti_hash" in event.metadata
    
    def test_log_token_rotation(self, audit_logger):
        """Test token rotation audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_token_rotation(
                user_id="user123",
                ip_address="192.168.1.1",
                old_token_jti="old_jti_123",
                new_access_jti="new_access_456",
                new_refresh_jti="new_refresh_789",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.TOKEN_ROTATION
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert "old_token_jti_hash" in event.metadata
            assert "new_access_jti_hash" in event.metadata
            assert "new_refresh_jti_hash" in event.metadata
    
    def test_log_session_created(self, audit_logger):
        """Test session creation audit logging"""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_session_created(
                user_id="user123",
                session_id="session123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123",
                expires_at=expires_at
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.SESSION_CREATED
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.session_id == "session123"
            assert event.metadata["expires_at"] == expires_at.isoformat()
    
    def test_log_session_expired(self, audit_logger):
        """Test session expiration audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_session_expired(
                user_id="user123",
                session_id="session123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                correlation_id="corr123",
                session_duration_minutes=120.5
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.SESSION_EXPIRED
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.metadata["session_duration_minutes"] == 120.5
    
    def test_log_error_response_generated(self, audit_logger):
        """Test error response generation audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_error_response_generated(
                error_category="authentication",
                error_severity="medium",
                provider_name="openai",
                ai_analysis_used=True,
                response_cached=True,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                generation_time_ms=250.5
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.ERROR_RESPONSE_GENERATED
            assert event.severity == AuditSeverity.INFO
            assert event.error_category == "authentication"
            assert event.error_severity == "medium"
            assert event.provider_name == "openai"
            assert event.ai_analysis_used is True
            assert event.response_cached is True
            assert event.llm_provider == "openai"
            assert event.llm_model == "gpt-3.5-turbo"
            assert event.duration_ms == 250.5
    
    def test_log_ai_analysis_requested(self, audit_logger):
        """Test AI analysis request audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_ai_analysis_requested(
                error_message="Connection timeout",
                provider_name="openai",
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.AI_ANALYSIS_REQUESTED
            assert event.severity == AuditSeverity.INFO
            assert event.provider_name == "openai"
            assert event.ai_analysis_used is True
            assert "error_message_hash" in event.metadata
    
    def test_log_ai_analysis_completed_success(self, audit_logger):
        """Test successful AI analysis completion audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_ai_analysis_completed(
                success=True,
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                generation_time_ms=1250.0,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                response_quality_score=0.85
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.AI_ANALYSIS_COMPLETED
            assert event.severity == AuditSeverity.INFO
            assert event.llm_provider == "openai"
            assert event.llm_model == "gpt-3.5-turbo"
            assert event.duration_ms == 1250.0
            assert event.response_quality_score == 0.85
            assert event.metadata["success"] is True
    
    def test_log_ai_analysis_completed_failure(self, audit_logger):
        """Test failed AI analysis completion audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_ai_analysis_completed(
                success=False,
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                generation_time_ms=500.0,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                error_message="API rate limit exceeded"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.AI_ANALYSIS_COMPLETED
            assert event.severity == AuditSeverity.WARNING
            assert event.metadata["success"] is False
            assert event.metadata["error_message"] == "API rate limit exceeded"
    
    def test_log_response_cache_hit(self, audit_logger):
        """Test response cache hit audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_response_cache_event(
                cache_hit=True,
                error_category="authentication",
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.RESPONSE_SERVED_FROM_CACHE
            assert event.severity == AuditSeverity.INFO
            assert event.error_category == "authentication"
            assert event.cache_hit is True
            assert event.response_cached is False
    
    def test_log_response_cache_miss(self, audit_logger):
        """Test response cache miss audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_response_cache_event(
                cache_hit=False,
                error_category="api_key_missing",
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, IntelligentResponseAuditEvent)
            assert event.event_type == AuditEventType.RESPONSE_CACHED
            assert event.severity == AuditSeverity.INFO
            assert event.error_category == "api_key_missing"
            assert event.cache_hit is False
            assert event.response_cached is True
    
    def test_log_token_operation_performance(self, audit_logger):
        """Test token operation performance audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=15.5,
                success=True,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                cache_hit=False,
                token_jti="jti123",
                logged_by="token_manager"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, PerformanceAuditEvent)
            assert event.event_type == AuditEventType.TOKEN_OPERATION_PERFORMANCE
            assert event.severity == AuditSeverity.INFO
            assert event.operation_name == "create_access_token"
            assert event.operation_type == "token"
            assert event.duration_ms == 15.5
            assert event.success is True
            assert event.cache_hit is False
            assert event.metadata["token_jti"] == "jti123"
            assert event.metadata["logged_by"] == "token_manager"
            
            # Check performance metrics tracking
            assert "create_access_token" in audit_logger._performance_metrics
            assert audit_logger._performance_metrics["create_access_token"] == [15.5]
    
    def test_log_token_operation_performance_failure(self, audit_logger):
        """Test token operation performance audit logging for failures"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_token_operation_performance(
                operation_name="validate_refresh_token",
                duration_ms=5.0,
                success=False,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                error_message="Token expired"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, PerformanceAuditEvent)
            assert event.event_type == AuditEventType.TOKEN_OPERATION_PERFORMANCE
            assert event.severity == AuditSeverity.WARNING
            assert event.success is False
            assert event.error_message == "Token expired"
    
    def test_log_llm_response_performance(self, audit_logger):
        """Test LLM response performance audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_llm_response_performance(
                provider="openai",
                model="gpt-3.5-turbo",
                duration_ms=1250.0,
                success=True,
                user_id="user123",
                tenant_id="tenant1",
                correlation_id="corr123",
                token_count=150
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, PerformanceAuditEvent)
            assert event.event_type == AuditEventType.LLM_RESPONSE_PERFORMANCE
            assert event.severity == AuditSeverity.INFO
            assert event.operation_name == "openai_gpt-3.5-turbo"
            assert event.operation_type == "llm"
            assert event.duration_ms == 1250.0
            assert event.success is True
            assert event.metadata["provider"] == "openai"
            assert event.metadata["model"] == "gpt-3.5-turbo"
            assert event.metadata["token_count"] == 150
            
            # Check performance metrics tracking
            operation_key = "llm_openai_gpt-3.5-turbo"
            assert operation_key in audit_logger._performance_metrics
            assert audit_logger._performance_metrics[operation_key] == [1250.0]
    
    def test_log_suspicious_activity(self, audit_logger):
        """Test suspicious activity audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            with patch.object(audit_logger.security_logger, 'log_security_event') as mock_security_event:
                audit_logger.log_suspicious_activity(
                    description="Multiple failed login attempts from same IP",
                    user_id="user123",
                    ip_address="192.168.1.1",
                    user_agent="Mozilla/5.0",
                    correlation_id="corr123",
                    attempt_count=10
                )
                
                mock_log.assert_called_once()
                event = mock_log.call_args[0][0]
                
                assert isinstance(event, AuditEvent)
                assert event.event_type == AuditEventType.SUSPICIOUS_LOGIN_PATTERN
                assert event.severity == AuditSeverity.ERROR
                assert event.user_id == "user123"
                assert event.ip_address == "192.168.1.1"
                assert event.metadata["attempt_count"] == 10
                
                # Verify security event was also logged
                mock_security_event.assert_called_once()
    
    def test_log_rate_limit_exceeded(self, audit_logger):
        """Test rate limit exceeded audit logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            with patch.object(audit_logger.security_logger, 'log_rate_limit_violation') as mock_rate_limit:
                audit_logger.log_rate_limit_exceeded(
                    user_id="user123",
                    endpoint="/api/chat",
                    limit=100,
                    current_count=105,
                    ip_address="192.168.1.1",
                    correlation_id="corr123"
                )
                
                mock_log.assert_called_once()
                event = mock_log.call_args[0][0]
                
                assert isinstance(event, AuditEvent)
                assert event.event_type == AuditEventType.RATE_LIMIT_EXCEEDED
                assert event.severity == AuditSeverity.WARNING
                assert event.user_id == "user123"
                assert event.endpoint == "/api/chat"
                assert event.metadata["limit"] == 100
                assert event.metadata["current_count"] == 105
                
                # Verify security logger was called
                mock_rate_limit.assert_called_once()
    
    def test_get_audit_metrics(self, audit_logger):
        """Test audit metrics retrieval"""
        # Add some events and performance data
        audit_logger._event_counts = {
            "login_success": 10,
            "login_failure": 2,
            "token_refresh": 5
        }
        audit_logger._performance_metrics = {
            "create_access_token": [10.0, 15.0, 12.0],
            "llm_openai_gpt-3.5-turbo": [1000.0, 1200.0, 800.0]
        }
        
        metrics = audit_logger.get_audit_metrics()
        
        assert "event_counts" in metrics
        assert "performance_metrics" in metrics
        assert "timestamp" in metrics
        
        assert metrics["event_counts"]["login_success"] == 10
        assert metrics["event_counts"]["login_failure"] == 2
        assert metrics["event_counts"]["token_refresh"] == 5
        
        token_metrics = metrics["performance_metrics"]["create_access_token"]
        assert token_metrics["count"] == 3
        assert token_metrics["avg_ms"] == 12.333333333333334
        assert token_metrics["min_ms"] == 10.0
        assert token_metrics["max_ms"] == 15.0
        
        llm_metrics = metrics["performance_metrics"]["llm_openai_gpt-3.5-turbo"]
        assert llm_metrics["count"] == 3
        assert llm_metrics["avg_ms"] == 1000.0
        assert llm_metrics["min_ms"] == 800.0
        assert llm_metrics["max_ms"] == 1200.0
    
    def test_reset_metrics(self, audit_logger):
        """Test metrics reset functionality"""
        # Add some data
        audit_logger._event_counts = {"login_success": 5}
        audit_logger._performance_metrics = {"create_token": [10.0, 20.0]}
        
        # Reset metrics
        audit_logger.reset_metrics()
        
        assert len(audit_logger._event_counts) == 0
        assert len(audit_logger._performance_metrics) == 0
    
    def test_log_login_success_deduplication(self, audit_logger):
        """Test that duplicate login success events are prevented"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            # First login should be logged
            audit_logger.log_login_success(
                user_id="user123",
                email="test@example.com",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Second identical login should be blocked
            audit_logger.log_login_success(
                user_id="user123",
                email="test@example.com",
                ip_address="192.168.1.1",
                logged_by="session_validator"
            )
            
            # Should only be called once (first time)
            mock_log.assert_called_once()
    
    def test_log_session_validation(self, audit_logger):
        """Test session validation logging"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            audit_logger.log_session_validation(
                user_id="user123",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                tenant_id="tenant1",
                session_id="session123",
                validation_method="token",
                logged_by="session_validator"
            )
            
            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            
            assert isinstance(event, AuthenticationAuditEvent)
            assert event.event_type == AuditEventType.SESSION_CREATED
            assert event.severity == AuditSeverity.INFO
            assert event.user_id == "user123"
            assert event.session_id == "session123"
            assert event.metadata["validation_method"] == "token"
            assert event.metadata["logged_by"] == "session_validator"
            assert event.metadata["event_category"] == "session_validation"
    
    def test_log_session_validation_deduplication(self, audit_logger):
        """Test that duplicate session validation events are prevented"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            # First session validation should be logged
            audit_logger.log_session_validation(
                user_id="user123",
                ip_address="192.168.1.1",
                session_id="session123",
                logged_by="session_validator"
            )
            
            # Second identical session validation should be blocked
            audit_logger.log_session_validation(
                user_id="user123",
                ip_address="192.168.1.1",
                session_id="session123",
                logged_by="session_validator"
            )
            
            # Should only be called once (first time)
            mock_log.assert_called_once()
    
    def test_different_event_types_not_deduplicated(self, audit_logger):
        """Test that different event types are not deduplicated against each other"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log:
            # Login success
            audit_logger.log_login_success(
                user_id="user123",
                email="test@example.com",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Session validation for same user - should not be blocked
            audit_logger.log_session_validation(
                user_id="user123",
                ip_address="192.168.1.1",
                logged_by="session_validator"
            )
            
            # Logout for same user - should not be blocked
            audit_logger.log_logout_success(
                user_id="user123",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Should be called three times (different event types)
            assert mock_log.call_count == 3


class TestAuditEventModels:
    """Test cases for audit event data models"""
    
    def test_audit_event_creation(self):
        """Test basic audit event creation"""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Test event",
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        assert event.event_type == AuditEventType.LOGIN_SUCCESS
        assert event.severity == AuditSeverity.INFO
        assert event.message == "Test event"
        assert event.user_id == "user123"
        assert event.ip_address == "192.168.1.1"
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.metadata, dict)
    
    def test_authentication_audit_event_creation(self):
        """Test authentication audit event creation"""
        event = AuthenticationAuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Login successful",
            user_id="user123",
            email="test@example.com",
            failure_reason=None,
            token_type="access",
            login_count=5
        )
        
        assert isinstance(event, AuditEvent)
        assert event.email == "test@example.com"
        assert event.token_type == "access"
        assert event.login_count == 5
    
    def test_intelligent_response_audit_event_creation(self):
        """Test intelligent response audit event creation"""
        event = IntelligentResponseAuditEvent(
            event_type=AuditEventType.ERROR_RESPONSE_GENERATED,
            severity=AuditSeverity.INFO,
            message="Error response generated",
            error_category="authentication",
            error_severity="medium",
            provider_name="openai",
            ai_analysis_used=True,
            response_cached=True,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            response_quality_score=0.85
        )
        
        assert isinstance(event, AuditEvent)
        assert event.error_category == "authentication"
        assert event.error_severity == "medium"
        assert event.provider_name == "openai"
        assert event.ai_analysis_used is True
        assert event.response_cached is True
        assert event.llm_provider == "openai"
        assert event.llm_model == "gpt-3.5-turbo"
        assert event.response_quality_score == 0.85
    
    def test_performance_audit_event_creation(self):
        """Test performance audit event creation"""
        event = PerformanceAuditEvent(
            event_type=AuditEventType.TOKEN_OPERATION_PERFORMANCE,
            severity=AuditSeverity.INFO,
            message="Token operation completed",
            operation_name="create_access_token",
            operation_type="token",
            success=True,
            duration_ms=15.5,
            cache_hit=False,
            retry_count=0
        )
        
        assert isinstance(event, AuditEvent)
        assert event.operation_name == "create_access_token"
        assert event.operation_type == "token"
        assert event.success is True
        assert event.duration_ms == 15.5
        assert event.cache_hit is False
        assert event.retry_count == 0


class TestGlobalAuditLogger:
    """Test cases for global audit logger instance"""
    
    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns singleton instance"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
        assert isinstance(logger1, AuditLogger)
    
    @patch('ai_karen_engine.services.audit_logging._audit_logger', None)
    def test_get_audit_logger_initialization(self):
        """Test that get_audit_logger initializes new instance when needed"""
        logger = get_audit_logger()
        
        assert logger is not None
        assert isinstance(logger, AuditLogger)


class TestAuditEventTypes:
    """Test cases for audit event type enums"""
    
    def test_audit_event_type_values(self):
        """Test audit event type enum values"""
        assert AuditEventType.LOGIN_SUCCESS.value == "login_success"
        assert AuditEventType.LOGIN_FAILURE.value == "login_failure"
        assert AuditEventType.LOGOUT_SUCCESS.value == "logout_success"
        assert AuditEventType.REFRESH_SUCCESS.value == "refresh_success"
        assert AuditEventType.REFRESH_FAILURE.value == "refresh_failure"
        assert AuditEventType.TOKEN_ROTATION.value == "token_rotation"
        assert AuditEventType.ERROR_RESPONSE_GENERATED.value == "error_response_generated"
        assert AuditEventType.AI_ANALYSIS_REQUESTED.value == "ai_analysis_requested"
        assert AuditEventType.TOKEN_OPERATION_PERFORMANCE.value == "token_operation_performance"
        assert AuditEventType.LLM_RESPONSE_PERFORMANCE.value == "llm_response_performance"
    
    def test_audit_severity_values(self):
        """Test audit severity enum values"""
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"
        assert AuditSeverity.ERROR.value == "error"
        assert AuditSeverity.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__])