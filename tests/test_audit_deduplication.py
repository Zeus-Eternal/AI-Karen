"""
Tests for audit log deduplication service.

This module tests the audit deduplication service to ensure it properly
prevents duplicate audit log entries while allowing legitimate events.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from ai_karen_engine.services.audit_deduplication import (
    AuditDeduplicationService,
    EventType,
    EventKey,
    EventRecord,
    get_audit_deduplication_service
)


class TestEventKey:
    """Test cases for EventKey class"""
    
    def test_event_key_creation(self):
        """Test basic event key creation"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            correlation_id="corr789"
        )
        
        assert key.event_type == EventType.LOGIN_SUCCESS
        assert key.user_id == "user123"
        assert key.session_id == "session456"
        assert key.ip_address == "192.168.1.1"
        assert key.correlation_id == "corr789"
        assert isinstance(key.additional_context, dict)
    
    def test_event_key_hash_consistency(self):
        """Test that event key hashes are consistent"""
        key1 = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        key2 = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # Same keys should produce same hash
        assert key1.to_hash() == key2.to_hash()
    
    def test_event_key_hash_uniqueness(self):
        """Test that different event keys produce different hashes"""
        key1 = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        key2 = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user456",  # Different user
            ip_address="192.168.1.1"
        )
        
        # Different keys should produce different hashes
        assert key1.to_hash() != key2.to_hash()
    
    def test_event_key_with_additional_context(self):
        """Test event key with additional context"""
        key = EventKey(
            event_type=EventType.LOGIN_FAILURE,
            ip_address="192.168.1.1",
            additional_context={"email": "test@example.com", "attempt": 1}
        )
        
        hash1 = key.to_hash()
        
        # Same key with same context should produce same hash
        key2 = EventKey(
            event_type=EventType.LOGIN_FAILURE,
            ip_address="192.168.1.1",
            additional_context={"email": "test@example.com", "attempt": 1}
        )
        
        assert key.to_hash() == key2.to_hash()
        
        # Different context should produce different hash
        key3 = EventKey(
            event_type=EventType.LOGIN_FAILURE,
            ip_address="192.168.1.1",
            additional_context={"email": "test@example.com", "attempt": 2}
        )
        
        assert key.to_hash() != key3.to_hash()


class TestEventRecord:
    """Test cases for EventRecord class"""
    
    def test_event_record_creation(self):
        """Test basic event record creation"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123"
        )
        
        record = EventRecord(
            event_key=key,
            timestamp=datetime.now(timezone.utc),
            logged_by="test_component",
            ttl_seconds=300
        )
        
        assert record.event_key == key
        assert isinstance(record.timestamp, datetime)
        assert record.logged_by == "test_component"
        assert record.ttl_seconds == 300
    
    def test_event_record_expiration(self):
        """Test event record expiration logic"""
        key = EventKey(event_type=EventType.LOGIN_SUCCESS, user_id="user123")
        
        # Create record that should be expired
        old_timestamp = datetime.now(timezone.utc) - timedelta(seconds=400)
        expired_record = EventRecord(
            event_key=key,
            timestamp=old_timestamp,
            logged_by="test",
            ttl_seconds=300  # 5 minutes
        )
        
        assert expired_record.is_expired()
        
        # Create record that should not be expired
        recent_timestamp = datetime.now(timezone.utc) - timedelta(seconds=100)
        active_record = EventRecord(
            event_key=key,
            timestamp=recent_timestamp,
            logged_by="test",
            ttl_seconds=300
        )
        
        assert not active_record.is_expired()


class TestAuditDeduplicationService:
    """Test cases for AuditDeduplicationService class"""
    
    @pytest.fixture
    def dedup_service(self):
        """Create deduplication service for testing"""
        with patch('ai_karen_engine.services.audit_deduplication.MemoryCache') as mock_cache_class:
            mock_cache = Mock()
            mock_cache.get.return_value = None  # No cache hits for testing
            mock_cache_class.return_value = mock_cache
            service = AuditDeduplicationService()
            service._local_events.clear()  # Start with clean state
            return service
    
    @pytest.fixture
    def mock_cache_client(self):
        """Mock cache client"""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = True
        return cache
    
    def test_should_log_event_first_time(self, dedup_service):
        """Test that first occurrence of an event should be logged"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # First time should return True
        assert dedup_service.should_log_event(key, "test_component")
        
        # Event should be recorded
        event_hash = key.to_hash()
        assert event_hash in dedup_service._local_events
        assert dedup_service._local_events[event_hash].logged_by == "test_component"
    
    def test_should_log_event_duplicate_prevention(self, dedup_service):
        """Test that duplicate events are prevented"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # First time should return True
        assert dedup_service.should_log_event(key, "component1")
        
        # Second time should return False (duplicate)
        assert not dedup_service.should_log_event(key, "component2")
    
    def test_should_log_event_after_expiration(self, dedup_service):
        """Test that events can be logged again after expiration"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1"
        )
        
        # Log event with very short TTL
        assert dedup_service.should_log_event(key, "test_component", ttl_seconds=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be able to log again after expiration
        assert dedup_service.should_log_event(key, "test_component", ttl_seconds=1)
    
    def test_should_log_authentication_event(self, dedup_service):
        """Test authentication event deduplication"""
        # First login success should be logged
        assert dedup_service.should_log_authentication_event(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1",
            email="test@example.com",
            logged_by="auth_routes"
        )
        
        # Duplicate login success should not be logged
        assert not dedup_service.should_log_authentication_event(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1",
            email="test@example.com",
            logged_by="session_validator"
        )
        
        # Different event type should be logged
        assert dedup_service.should_log_authentication_event(
            event_type=EventType.LOGOUT_SUCCESS,
            user_id="user123",
            ip_address="192.168.1.1",
            logged_by="auth_routes"
        )
    
    def test_should_log_session_validation(self, dedup_service):
        """Test session validation deduplication"""
        # First session validation should be logged
        assert dedup_service.should_log_session_validation(
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            logged_by="session_validator"
        )
        
        # Duplicate session validation should not be logged
        assert not dedup_service.should_log_session_validation(
            user_id="user123",
            session_id="session456",
            ip_address="192.168.1.1",
            logged_by="session_validator"
        )
        
        # Different session should be logged
        assert dedup_service.should_log_session_validation(
            user_id="user123",
            session_id="session789",  # Different session
            ip_address="192.168.1.1",
            logged_by="session_validator"
        )
    
    def test_should_log_token_operation(self, dedup_service):
        """Test token operation deduplication"""
        # First token operation should be logged
        assert dedup_service.should_log_token_operation(
            operation_name="create_access_token",
            user_id="user123",
            token_jti="jti456",
            logged_by="token_manager"
        )
        
        # Duplicate token operation should not be logged
        assert not dedup_service.should_log_token_operation(
            operation_name="create_access_token",
            user_id="user123",
            token_jti="jti456",
            logged_by="token_manager"
        )
        
        # Different operation should be logged
        assert dedup_service.should_log_token_operation(
            operation_name="create_refresh_token",  # Different operation
            user_id="user123",
            token_jti="jti789",
            logged_by="token_manager"
        )
    
    def test_cleanup_expired_events(self, dedup_service):
        """Test cleanup of expired events"""
        # Add some events with different TTLs
        key1 = EventKey(event_type=EventType.LOGIN_SUCCESS, user_id="user1")
        key2 = EventKey(event_type=EventType.LOGIN_SUCCESS, user_id="user2")
        
        # Add event that should expire quickly
        dedup_service.should_log_event(key1, "test", ttl_seconds=1)
        
        # Add event that should not expire
        dedup_service.should_log_event(key2, "test", ttl_seconds=300)
        
        assert len(dedup_service._local_events) == 2
        
        # Wait for first event to expire
        time.sleep(1.1)
        
        # Force cleanup
        dedup_service._cleanup_expired_events()
        
        # Only the non-expired event should remain
        assert len(dedup_service._local_events) == 1
        assert key2.to_hash() in dedup_service._local_events
        assert key1.to_hash() not in dedup_service._local_events
    
    def test_mark_event_logged(self, dedup_service):
        """Test manually marking an event as logged"""
        key = EventKey(
            event_type=EventType.LOGIN_SUCCESS,
            user_id="user123"
        )
        
        # Mark event as logged
        dedup_service.mark_event_logged(key, "manual_component")
        
        # Event should be recorded
        event_hash = key.to_hash()
        assert event_hash in dedup_service._local_events
        assert dedup_service._local_events[event_hash].logged_by == "manual_component"
        
        # Subsequent attempts to log should be blocked
        assert not dedup_service.should_log_event(key, "other_component")
    
    def test_get_event_stats(self, dedup_service):
        """Test getting event statistics"""
        # Add some events
        dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS, user_id="user1", logged_by="auth_routes"
        )
        dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS, user_id="user2", logged_by="auth_routes"
        )
        dedup_service.should_log_authentication_event(
            EventType.LOGIN_FAILURE, user_id="user3", logged_by="auth_routes"
        )
        dedup_service.should_log_session_validation(
            user_id="user1", logged_by="session_validator"
        )
        
        stats = dedup_service.get_event_stats()
        
        assert "local_events_count" in stats
        assert "event_types" in stats
        assert "logged_by" in stats
        assert "timestamp" in stats
        
        assert stats["local_events_count"] == 4
        assert stats["event_types"]["login_success"] == 2
        assert stats["event_types"]["login_failure"] == 1
        assert stats["event_types"]["session_validation"] == 1
        assert stats["logged_by"]["auth_routes"] == 3
        assert stats["logged_by"]["session_validator"] == 1
    
    def test_clear_all_events(self, dedup_service):
        """Test clearing all tracked events"""
        # Add some events
        dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS, user_id="user1", logged_by="test"
        )
        dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS, user_id="user2", logged_by="test"
        )
        
        assert len(dedup_service._local_events) == 2
        
        # Clear all events
        dedup_service.clear_all_events()
        
        assert len(dedup_service._local_events) == 0
    
    def test_memory_cache_integration(self):
        """Test integration with memory cache"""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        with patch('ai_karen_engine.services.audit_deduplication.MemoryCache') as mock_cache_class:
            mock_cache_class.return_value = mock_cache
            
            service = AuditDeduplicationService()
            key = EventKey(event_type=EventType.LOGIN_SUCCESS, user_id="user123")
            
            # First time should check cache and store event
            assert service.should_log_event(key, "test_component")
            
            # Verify cache was checked and event was stored
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()
    
    def test_memory_cache_hit(self):
        """Test behavior when memory cache has the event"""
        mock_cache = Mock()
        mock_cache.get.return_value = {
            "logged_by": "other_component",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "login_success"
        }
        
        with patch('ai_karen_engine.services.audit_deduplication.MemoryCache') as mock_cache_class:
            mock_cache_class.return_value = mock_cache
            
            service = AuditDeduplicationService()
            key = EventKey(event_type=EventType.LOGIN_SUCCESS, user_id="user123")
            
            # Should return False due to cache hit
            assert not service.should_log_event(key, "test_component")
            
            # Verify cache was checked but not set
            mock_cache.get.assert_called_once()
            mock_cache.set.assert_not_called()


class TestGlobalInstance:
    """Test cases for global instance management"""
    
    def test_get_audit_deduplication_service(self):
        """Test getting global deduplication service instance"""
        service1 = get_audit_deduplication_service()
        service2 = get_audit_deduplication_service()
        
        # Should return the same instance
        assert service1 is service2
        assert isinstance(service1, AuditDeduplicationService)


class TestIntegrationScenarios:
    """Test cases for real-world integration scenarios"""
    
    @pytest.fixture
    def dedup_service(self):
        """Create fresh deduplication service for integration tests"""
        with patch('ai_karen_engine.services.audit_deduplication.MemoryCache') as mock_cache_class:
            mock_cache = Mock()
            mock_cache.get.return_value = None
            mock_cache_class.return_value = mock_cache
            service = AuditDeduplicationService()
            service._local_events.clear()
            return service
    
    def test_login_and_session_validation_scenario(self, dedup_service):
        """Test scenario where user logs in and then session is validated"""
        user_id = "user123"
        ip_address = "192.168.1.1"
        email = "test@example.com"
        
        # 1. User logs in - should be logged
        assert dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            email=email,
            logged_by="auth_routes"
        )
        
        # 2. Session validator tries to log the same login - should be blocked
        assert not dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            email=email,
            logged_by="session_validator"
        )
        
        # 3. Session validation event - should be logged (different event type)
        assert dedup_service.should_log_session_validation(
            user_id=user_id,
            ip_address=ip_address,
            logged_by="session_validator"
        )
        
        # 4. Another session validation - should be blocked
        assert not dedup_service.should_log_session_validation(
            user_id=user_id,
            ip_address=ip_address,
            logged_by="session_validator"
        )
    
    def test_token_operations_scenario(self, dedup_service):
        """Test scenario with multiple token operations"""
        user_id = "user123"
        
        # 1. Create access token - should be logged
        assert dedup_service.should_log_token_operation(
            operation_name="create_access_token",
            user_id=user_id,
            token_jti="access_jti_123",
            logged_by="token_manager"
        )
        
        # 2. Same token operation - should be blocked
        assert not dedup_service.should_log_token_operation(
            operation_name="create_access_token",
            user_id=user_id,
            token_jti="access_jti_123",
            logged_by="token_manager"
        )
        
        # 3. Create refresh token - should be logged (different operation)
        assert dedup_service.should_log_token_operation(
            operation_name="create_refresh_token",
            user_id=user_id,
            token_jti="refresh_jti_456",
            logged_by="token_manager"
        )
        
        # 4. Create access token with different JTI - should be logged
        assert dedup_service.should_log_token_operation(
            operation_name="create_access_token",
            user_id=user_id,
            token_jti="access_jti_789",  # Different JTI
            logged_by="token_manager"
        )
    
    def test_multiple_users_scenario(self, dedup_service):
        """Test scenario with multiple users performing similar actions"""
        ip_address = "192.168.1.1"
        
        # Different users should not interfere with each other
        assert dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS,
            user_id="user1",
            ip_address=ip_address,
            email="user1@example.com",
            logged_by="auth_routes"
        )
        
        assert dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS,
            user_id="user2",  # Different user
            ip_address=ip_address,
            email="user2@example.com",
            logged_by="auth_routes"
        )
        
        # Same user duplicate should be blocked
        assert not dedup_service.should_log_authentication_event(
            EventType.LOGIN_SUCCESS,
            user_id="user1",  # Same user as first
            ip_address=ip_address,
            email="user1@example.com",
            logged_by="session_validator"
        )


if __name__ == "__main__":
    pytest.main([__file__])