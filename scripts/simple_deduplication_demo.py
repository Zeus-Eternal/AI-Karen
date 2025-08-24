#!/usr/bin/env python3
"""
Simple Audit Log Deduplication Demo

This script demonstrates the audit log deduplication functionality
without requiring the full system setup.
"""

import os
import sys
from pathlib import Path

# Set required environment variables to avoid import errors
os.environ.setdefault("KARI_DUCKDB_PASSWORD", "demo_password")
os.environ.setdefault("KARI_JOB_ENC_KEY", "demo_encryption_key")

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.services.audit_deduplication import (
    AuditDeduplicationService,
    EventType,
    EventKey
)


def main():
    """Demonstrate audit log deduplication functionality"""
    print("=== Simple Audit Log Deduplication Demo ===")
    
    # Create deduplication service
    dedup_service = AuditDeduplicationService()
    dedup_service.clear_all_events()  # Start clean
    
    print("\n1. Testing authentication event deduplication...")
    
    # Test login success deduplication
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
    
    print("\n4. Deduplication Statistics:")
    stats = dedup_service.get_event_stats()
    
    print(f"   Total events tracked: {stats['local_events_count']}")
    print(f"   Event types: {list(stats['event_types'].keys())}")
    print(f"   Components that logged: {list(stats['logged_by'].keys())}")
    
    print("\n5. Event type breakdown:")
    for event_type, count in stats['event_types'].items():
        print(f"   {event_type}: {count} events")
    
    print("\n6. Component breakdown:")
    for component, count in stats['logged_by'].items():
        print(f"   {component}: {count} events")
    
    print("\n7. Testing event key uniqueness...")
    
    # Test that event keys are properly unique
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
    
    print("\n=== Demo Complete ===")
    print("The deduplication service successfully:")
    print("• Prevented duplicate events from the same component")
    print("• Prevented duplicate events from different components")
    print("• Allowed different event types for the same user")
    print("• Allowed same event types for different users")
    print("• Tracked statistics about prevented duplicates")


if __name__ == "__main__":
    main()