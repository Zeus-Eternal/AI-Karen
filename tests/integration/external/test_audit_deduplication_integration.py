"""
Integration tests for audit log deduplication with actual audit logging service.

This module tests the complete integration between the audit logging service
and the deduplication service to ensure duplicate events are properly prevented.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from ai_karen_engine.services.audit_logging import (
    AuditLogger,
    get_audit_logger
)
from ai_karen_engine.services.audit_deduplication import (
    get_audit_deduplication_service
)


class TestAuditDeduplicationIntegration:
    """Test complete integration of audit logging with deduplication"""
    
    @pytest.fixture
    def audit_logger(self):
        """Create audit logger with real deduplication service"""
        # Clear any existing global instances
        import ai_karen_engine.services.audit_logging
        import ai_karen_engine.services.audit_deduplication
        ai_karen_engine.services.audit_logging._audit_logger = None
        ai_karen_engine.services.audit_deduplication._deduplication_service = None
        
        # Create fresh instances
        logger = get_audit_logger()
        logger.deduplication_service.clear_all_events()  # Start clean
        return logger
    
    def test_login_success_deduplication_integration(self, audit_logger):
        """Test that duplicate login success events are actually prevented"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            with patch.object(audit_logger.auth_logger, 'info') as mock_auth_log:
                # First login should be logged
                audit_logger.log_login_success(
                    user_id="user123",
                    email="test@example.com",
                    ip_address="192.168.1.1",
                    logged_by="auth_routes"
                )
                
                # Second identical login should be blocked by deduplication
                audit_logger.log_login_success(
                    user_id="user123",
                    email="test@example.com",
                    ip_address="192.168.1.1",
                    logged_by="session_validator"
                )
                
                # Should only be called once due to deduplication
                assert mock_log_event.call_count == 1
                assert mock_auth_log.call_count == 1
                
                # Verify the logged event has correct metadata
                logged_event = mock_log_event.call_args[0][0]
                assert logged_event.user_id == "user123"
                assert logged_event.email == "test@example.com"
                assert logged_event.metadata["logged_by"] == "auth_routes"
    
    def test_different_components_same_event_deduplication(self, audit_logger):
        """Test that the same event from different components is deduplicated"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            # Auth routes logs login
            audit_logger.log_login_success(
                user_id="user456",
                email="user456@example.com",
                ip_address="192.168.1.2",
                logged_by="auth_routes"
            )
            
            # Session validator tries to log the same login
            audit_logger.log_login_success(
                user_id="user456",
                email="user456@example.com",
                ip_address="192.168.1.2",
                logged_by="session_validator"
            )
            
            # Enhanced session validator also tries to log
            audit_logger.log_login_success(
                user_id="user456",
                email="user456@example.com",
                ip_address="192.168.1.2",
                logged_by="enhanced_session_validator"
            )
            
            # Should only be logged once despite multiple components trying
            assert mock_log_event.call_count == 1
    
    def test_session_validation_separate_from_login(self, audit_logger):
        """Test that session validation events are separate from login events"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            # Login event
            audit_logger.log_login_success(
                user_id="user789",
                email="user789@example.com",
                ip_address="192.168.1.3",
                logged_by="auth_routes"
            )
            
            # Session validation event (different event type)
            audit_logger.log_session_validation(
                user_id="user789",
                ip_address="192.168.1.3",
                session_id="session123",
                logged_by="session_validator"
            )
            
            # Both should be logged as they are different event types
            assert mock_log_event.call_count == 2
            
            # Verify event types are different
            login_event = mock_log_event.call_args_list[0][0][0]
            session_event = mock_log_event.call_args_list[1][0][0]
            
            assert login_event.event_type.value == "login_success"
            assert session_event.event_type.value == "session_created"
            assert session_event.metadata["event_category"] == "session_validation"
    
    def test_token_operation_deduplication(self, audit_logger):
        """Test that duplicate token operations are prevented"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            # First token operation
            audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=15.5,
                success=True,
                user_id="user123",
                token_jti="jti456",
                logged_by="token_manager"
            )
            
            # Duplicate token operation (same user, same JTI)
            audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=16.2,  # Different duration but same operation
                success=True,
                user_id="user123",
                token_jti="jti456",
                logged_by="token_manager"
            )
            
            # Should only be logged once
            assert mock_log_event.call_count == 1
    
    def test_different_users_not_deduplicated(self, audit_logger):
        """Test that events for different users are not deduplicated"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            # Login for user1
            audit_logger.log_login_success(
                user_id="user1",
                email="user1@example.com",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Login for user2 (different user, same IP)
            audit_logger.log_login_success(
                user_id="user2",
                email="user2@example.com",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Both should be logged as they are for different users
            assert mock_log_event.call_count == 2
    
    def test_deduplication_stats_tracking(self, audit_logger):
        """Test that deduplication statistics are properly tracked"""
        # Log some events
        audit_logger.log_login_success(
            user_id="user1",
            email="user1@example.com",
            ip_address="192.168.1.1",
            logged_by="auth_routes"
        )
        
        # Try to log duplicate (should be blocked)
        audit_logger.log_login_success(
            user_id="user1",
            email="user1@example.com",
            ip_address="192.168.1.1",
            logged_by="session_validator"
        )
        
        # Log different event type
        audit_logger.log_session_validation(
            user_id="user1",
            ip_address="192.168.1.1",
            logged_by="session_validator"
        )
        
        # Check deduplication stats
        stats = audit_logger.deduplication_service.get_event_stats()
        
        assert stats["local_events_count"] == 2  # Login + session validation
        assert "login_success" in stats["event_types"]
        assert "session_validation" in stats["event_types"]
        assert stats["logged_by"]["auth_routes"] == 1
        assert stats["logged_by"]["session_validator"] == 1
    
    def test_cleanup_expired_events_integration(self, audit_logger):
        """Test that expired events are cleaned up properly"""
        import time
        
        # Log event with very short TTL
        audit_logger.log_login_success(
            user_id="user_short_ttl",
            email="user@example.com",
            ip_address="192.168.1.1",
            logged_by="auth_routes"
        )
        
        # Manually set short TTL for testing
        dedup_service = audit_logger.deduplication_service
        for record in dedup_service._local_events.values():
            record.ttl_seconds = 1  # 1 second TTL
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Force cleanup
        dedup_service._cleanup_expired_events()
        
        # Now the same event should be allowed again
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            audit_logger.log_login_success(
                user_id="user_short_ttl",
                email="user@example.com",
                ip_address="192.168.1.1",
                logged_by="auth_routes"
            )
            
            # Should be logged since previous event expired
            assert mock_log_event.call_count == 1
    
    def test_real_world_authentication_flow(self, audit_logger):
        """Test a realistic authentication flow with deduplication"""
        with patch.object(audit_logger, 'log_audit_event') as mock_log_event:
            user_id = "real_user_123"
            email = "real@example.com"
            ip_address = "192.168.1.100"
            session_id = "session_abc123"
            
            # 1. User logs in (auth routes)
            audit_logger.log_login_success(
                user_id=user_id,
                email=email,
                ip_address=ip_address,
                session_id=session_id,
                logged_by="auth_routes"
            )
            
            # 2. Session validator validates the session (should not duplicate login)
            audit_logger.log_session_validation(
                user_id=user_id,
                ip_address=ip_address,
                session_id=session_id,
                logged_by="session_validator"
            )
            
            # 3. Token manager creates tokens
            audit_logger.log_token_operation_performance(
                operation_name="create_access_token",
                duration_ms=12.5,
                success=True,
                user_id=user_id,
                token_jti="access_jti_123",
                logged_by="token_manager"
            )
            
            audit_logger.log_token_operation_performance(
                operation_name="create_refresh_token",
                duration_ms=8.3,
                success=True,
                user_id=user_id,
                token_jti="refresh_jti_456",
                logged_by="token_manager"
            )
            
            # 4. User makes API calls (session validations - should be deduplicated)
            for _ in range(3):
                audit_logger.log_session_validation(
                    user_id=user_id,
                    ip_address=ip_address,
                    session_id=session_id,
                    logged_by="session_validator"
                )
            
            # 5. User logs out
            audit_logger.log_logout_success(
                user_id=user_id,
                ip_address=ip_address,
                session_id=session_id,
                logged_by="auth_routes"
            )
            
            # Verify expected number of events were logged
            # 1 login + 1 session validation + 2 token operations + 1 logout = 5 events
            assert mock_log_event.call_count == 5
            
            # Verify event types
            event_types = [call[0][0].event_type.value for call in mock_log_event.call_args_list]
            assert "login_success" in event_types
            assert "session_created" in event_types  # Session validation
            assert "token_operation_performance" in event_types
            assert "logout_success" in event_types


if __name__ == "__main__":
    pytest.main([__file__])