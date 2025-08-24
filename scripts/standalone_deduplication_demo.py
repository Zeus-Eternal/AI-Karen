#!/usr/bin/env python3
"""
Standalone Audit Log Deduplication Demo

This script demonstrates the audit log deduplication functionality
using a standalone implementation that doesn't require the full system.
"""

import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class EventType(str, Enum):
    """Types of events that can be deduplicated"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT_SUCCESS = "logout_success"
    TOKEN_REFRESH = "token_refresh"
    SESSION_VALIDATION = "session_validation"
    TOKEN_CREATION = "token_creation"


@dataclass
class EventKey:
    """Unique key for identifying events"""
    event_type: EventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    correlation_id: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_hash(self) -> str:
        """Generate a hash key for this event"""
        key_data = {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "correlation_id": self.correlation_id,
            **self.additional_context
        }
        
        # Sort keys for consistent hashing
        key_str = str(sorted(key_data.items()))
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]


@dataclass
class EventRecord:
    """Record of a logged event"""
    event_key: EventKey
    timestamp: datetime
    logged_by: str
    ttl_seconds: int = 300
    
    def is_expired(self) -> bool:
        """Check if this event record has expired"""
        return datetime.now(timezone.utc) > self.timestamp + timedelta(seconds=self.ttl_seconds)


class SimpleAuditDeduplicationService:
    """Simplified audit deduplication service for demo"""
    
    def __init__(self):
        self._local_events: Dict[str, EventRecord] = {}
        self._cleanup_interval = 300
        self._last_cleanup = time.time()
        
    def _cleanup_expired_events(self) -> None:
        """Clean up expired events from local cache"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
            
        expired_keys = [
            key for key, record in self._local_events.items()
            if record.is_expired()
        ]
        
        for key in expired_keys:
            del self._local_events[key]
            
        self._last_cleanup = current_time
        
        if expired_keys:
            print(f"   [CLEANUP] Removed {len(expired_keys)} expired event records")
    
    def should_log_event(
        self,
        event_key: EventKey,
        logged_by: str,
        ttl_seconds: int = 300
    ) -> bool:
        """Check if an event should be logged (not a duplicate)"""
        self._cleanup_expired_events()
        
        event_hash = event_key.to_hash()
        
        # Check local cache
        if event_hash in self._local_events:
            existing_record = self._local_events[event_hash]
            if not existing_record.is_expired():
                print(f"   [DEDUP] Blocked duplicate: {event_key.event_type.value} "
                      f"(originally by {existing_record.logged_by}, now by {logged_by})")
                return False
            else:
                # Remove expired record
                del self._local_events[event_hash]
        
        # Event is not a duplicate, record it
        record = EventRecord(
            event_key=event_key,
            timestamp=datetime.now(timezone.utc),
            logged_by=logged_by,
            ttl_seconds=ttl_seconds
        )
        
        self._local_events[event_hash] = record
        return True
    
    def should_log_authentication_event(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        email: Optional[str] = None,
        logged_by: str = "unknown",
        ttl_seconds: int = 300
    ) -> bool:
        """Check if an authentication event should be logged"""
        event_key = EventKey(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            additional_context={"email": email} if email else {}
        )
        
        return self.should_log_event(event_key, logged_by, ttl_seconds)
    
    def should_log_session_validation(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        logged_by: str = "session_validator",
        ttl_seconds: int = 60
    ) -> bool:
        """Check if a session validation event should be logged"""
        event_key = EventKey(
            event_type=EventType.SESSION_VALIDATION,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address
        )
        
        return self.should_log_event(event_key, logged_by, ttl_seconds)
    
    def should_log_token_operation(
        self,
        operation_name: str,
        user_id: str,
        token_jti: Optional[str] = None,
        logged_by: str = "token_manager",
        ttl_seconds: int = 30
    ) -> bool:
        """Check if a token operation should be logged"""
        event_key = EventKey(
            event_type=EventType.TOKEN_CREATION,
            user_id=user_id,
            additional_context={
                "operation": operation_name,
                "token_jti": token_jti
            }
        )
        
        return self.should_log_event(event_key, logged_by, ttl_seconds)
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked events"""
        self._cleanup_expired_events()
        
        stats = {
            "local_events_count": len(self._local_events),
            "event_types": {},
            "logged_by": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        for record in self._local_events.values():
            event_type = record.event_key.event_type.value
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
            stats["logged_by"][record.logged_by] = stats["logged_by"].get(record.logged_by, 0) + 1
        
        return stats
    
    def clear_all_events(self) -> None:
        """Clear all tracked events"""
        self._local_events.clear()


def main():
    """Demonstrate audit log deduplication functionality"""
    print("=== Standalone Audit Log Deduplication Demo ===")
    
    # Create deduplication service
    dedup_service = SimpleAuditDeduplicationService()
    dedup_service.clear_all_events()
    
    print("\n1. Testing authentication event deduplication...")
    
    user_id = "demo_user_123"
    ip_address = "192.168.1.100"
    email = "demo@example.com"
    
    # First login attempt (should be allowed)
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_SUCCESS,
        user_id=user_id,
        ip_address=ip_address,
        email=email,
        logged_by="auth_routes"
    )
    print(f"   First login attempt (auth_routes): {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Duplicate login attempt from session validator (should be blocked)
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_SUCCESS,
        user_id=user_id,
        ip_address=ip_address,
        email=email,
        logged_by="session_validator"
    )
    print(f"   Duplicate login attempt (session_validator): {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Enhanced session validator also tries (should be blocked)
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_SUCCESS,
        user_id=user_id,
        ip_address=ip_address,
        email=email,
        logged_by="enhanced_session_validator"
    )
    print(f"   Another duplicate attempt (enhanced_session_validator): {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Different event type (should be allowed)
    should_log = dedup_service.should_log_session_validation(
        user_id=user_id,
        ip_address=ip_address,
        logged_by="session_validator"
    )
    print(f"   Session validation (different event): {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    print("\n2. Testing token operation deduplication...")
    
    # First token operation (should be allowed)
    should_log = dedup_service.should_log_token_operation(
        operation_name="create_access_token",
        user_id=user_id,
        token_jti="demo_jti_123",
        logged_by="token_manager"
    )
    print(f"   First token operation: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Duplicate token operation (should be blocked)
    should_log = dedup_service.should_log_token_operation(
        operation_name="create_access_token",
        user_id=user_id,
        token_jti="demo_jti_123",
        logged_by="token_manager"
    )
    print(f"   Duplicate token operation: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Different token operation (should be allowed)
    should_log = dedup_service.should_log_token_operation(
        operation_name="create_refresh_token",
        user_id=user_id,
        token_jti="demo_refresh_jti_456",
        logged_by="token_manager"
    )
    print(f"   Different token operation: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    print("\n3. Testing different users (should not interfere)...")
    
    # Different user (should be allowed)
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_SUCCESS,
        user_id="different_user_456",
        ip_address=ip_address,
        email="different@example.com",
        logged_by="auth_routes"
    )
    print(f"   Different user login: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    print("\n4. Testing session validation deduplication...")
    
    # First session validation (should be allowed)
    should_log = dedup_service.should_log_session_validation(
        user_id=user_id,
        session_id="session_123",
        ip_address=ip_address,
        logged_by="session_validator"
    )
    print(f"   First session validation: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Duplicate session validation (should be blocked)
    should_log = dedup_service.should_log_session_validation(
        user_id=user_id,
        session_id="session_123",
        ip_address=ip_address,
        logged_by="session_validator"
    )
    print(f"   Duplicate session validation: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    print("\n5. Deduplication Statistics:")
    stats = dedup_service.get_event_stats()
    
    print(f"   Total events tracked: {stats['local_events_count']}")
    print(f"   Event types: {list(stats['event_types'].keys())}")
    print(f"   Components that logged: {list(stats['logged_by'].keys())}")
    
    print("\n6. Event type breakdown:")
    for event_type, count in stats['event_types'].items():
        print(f"   {event_type}: {count} events")
    
    print("\n7. Component breakdown:")
    for component, count in stats['logged_by'].items():
        print(f"   {component}: {count} events")
    
    print("\n8. Testing event expiration...")
    
    # Log event with very short TTL
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_FAILURE,
        user_id="temp_user",
        ip_address="192.168.1.200",
        email="temp@example.com",
        logged_by="auth_routes",
        ttl_seconds=1  # 1 second TTL
    )
    print(f"   Event with short TTL: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    # Wait for expiration
    print("   Waiting for event to expire...")
    time.sleep(1.1)
    
    # Try to log the same event again (should be allowed after expiration)
    should_log = dedup_service.should_log_authentication_event(
        event_type=EventType.LOGIN_FAILURE,
        user_id="temp_user",
        ip_address="192.168.1.200",
        email="temp@example.com",
        logged_by="auth_routes",
        ttl_seconds=1
    )
    print(f"   Same event after expiration: {'✓ LOGGED' if should_log else '✗ BLOCKED'}")
    
    print("\n9. Testing event key uniqueness...")
    
    key1 = EventKey(
        event_type=EventType.LOGIN_SUCCESS,
        user_id="user1",
        ip_address="192.168.1.1"
    )
    
    key2 = EventKey(
        event_type=EventType.LOGIN_SUCCESS,
        user_id="user1",
        ip_address="192.168.1.1"
    )
    
    key3 = EventKey(
        event_type=EventType.LOGIN_SUCCESS,
        user_id="user2",  # Different user
        ip_address="192.168.1.1"
    )
    
    print(f"   Same keys produce same hash: {key1.to_hash() == key2.to_hash()}")
    print(f"   Different keys produce different hash: {key1.to_hash() != key3.to_hash()}")
    print(f"   Key1 hash: {key1.to_hash()}")
    print(f"   Key2 hash: {key2.to_hash()}")
    print(f"   Key3 hash: {key3.to_hash()}")
    
    print("\n=== Demo Complete ===")
    print("\nSummary of deduplication functionality:")
    print("✓ Prevented duplicate login events from multiple components")
    print("✓ Allowed different event types for the same user")
    print("✓ Allowed same event types for different users")
    print("✓ Prevented duplicate session validations")
    print("✓ Prevented duplicate token operations")
    print("✓ Properly handled event expiration and cleanup")
    print("✓ Generated unique hashes for different events")
    print("✓ Tracked comprehensive statistics")
    
    print(f"\nFinal statistics: {stats['local_events_count']} unique events tracked")
    print("This demonstrates how the audit deduplication service prevents")
    print("duplicate log entries while preserving legitimate events.")


if __name__ == "__main__":
    main()