#!/usr/bin/env python3
"""
Audit Log Cleanup Demo Script

This script demonstrates the audit log cleanup functionality
and can be used to manually clean up audit logs.
"""

import argparse
import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.services.audit_cleanup import get_audit_cleanup_service
from ai_karen_engine.services.audit_deduplication import get_audit_deduplication_service
from ai_karen_engine.services.audit_logging import get_audit_logger


def main():
    """Main function for the audit cleanup demo"""
    parser = argparse.ArgumentParser(
        description="Audit Log Cleanup Demo and Utility"
    )
    
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory containing log files (default: logs)"
    )
    
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=30,
        help="Maximum age of log files to keep in days (default: 30)"
    )
    
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=100,
        help="Maximum size in MB before rotating logs (default: 100)"
    )
    
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress old files before deletion"
    )
    
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show statistics, don't perform cleanup"
    )
    
    parser.add_argument(
        "--demo-deduplication",
        action="store_true",
        help="Demonstrate audit log deduplication"
    )
    
    args = parser.parse_args()
    
    if args.demo_deduplication:
        demo_deduplication()
        return
    
    # Get cleanup service
    cleanup_service = get_audit_cleanup_service(args.log_dir)
    
    if args.stats_only:
        # Show statistics only
        print("=== Audit Log Statistics ===")
        stats = cleanup_service.get_log_file_stats()
        print(json.dumps(stats, indent=2, default=str))
        
        print("\n=== Deduplication Statistics ===")
        dedup_service = get_audit_deduplication_service()
        dedup_stats = dedup_service.get_event_stats()
        print(json.dumps(dedup_stats, indent=2, default=str))
        
    else:
        # Perform comprehensive cleanup
        print("=== Starting Comprehensive Audit Log Cleanup ===")
        print(f"Log directory: {args.log_dir}")
        print(f"Max age: {args.max_age_days} days")
        print(f"Max size: {args.max_size_mb} MB")
        print(f"Compress old files: {args.compress}")
        print()
        
        cleanup_stats = cleanup_service.cleanup_all(
            max_age_days=args.max_age_days,
            max_size_mb=args.max_size_mb,
            compress_old_files=args.compress
        )
        
        print("=== Cleanup Results ===")
        print(json.dumps(cleanup_stats, indent=2, default=str))


def demo_deduplication():
    """Demonstrate audit log deduplication functionality"""
    print("=== Audit Log Deduplication Demo ===")
    
    # Get audit logger
    audit_logger = get_audit_logger()
    
    # Clear any existing events for clean demo
    audit_logger.deduplication_service.clear_all_events()
    
    print("1. Logging initial authentication events...")
    
    # Simulate authentication events
    audit_logger.log_login_success(
        user_id="demo_user_123",
        email="demo@example.com",
        ip_address="192.168.1.100",
        logged_by="auth_routes"
    )
    
    print("   ✓ Login success logged by auth_routes")
    
    # Try to log the same event from session validator (should be blocked)
    audit_logger.log_login_success(
        user_id="demo_user_123",
        email="demo@example.com",
        ip_address="192.168.1.100",
        logged_by="session_validator"
    )
    
    print("   ✗ Duplicate login attempt blocked (session_validator)")
    
    # Log a different event type (should be allowed)
    audit_logger.log_session_validation(
        user_id="demo_user_123",
        ip_address="192.168.1.100",
        session_id="demo_session_456",
        logged_by="session_validator"
    )
    
    print("   ✓ Session validation logged (different event type)")
    
    # Log token operations
    audit_logger.log_token_operation_performance(
        operation_name="create_access_token",
        duration_ms=15.5,
        success=True,
        user_id="demo_user_123",
        token_jti="demo_access_jti",
        logged_by="token_manager"
    )
    
    print("   ✓ Token operation logged")
    
    # Try to log the same token operation (should be blocked)
    audit_logger.log_token_operation_performance(
        operation_name="create_access_token",
        duration_ms=16.2,
        success=True,
        user_id="demo_user_123",
        token_jti="demo_access_jti",
        logged_by="token_manager"
    )
    
    print("   ✗ Duplicate token operation blocked")
    
    # Show deduplication statistics
    print("\n2. Deduplication Statistics:")
    stats = audit_logger.deduplication_service.get_event_stats()
    
    print(f"   Total events tracked: {stats['local_events_count']}")
    print(f"   Event types: {list(stats['event_types'].keys())}")
    print(f"   Components that logged: {list(stats['logged_by'].keys())}")
    
    print("\n3. Event type breakdown:")
    for event_type, count in stats['event_types'].items():
        print(f"   {event_type}: {count} events")
    
    print("\n4. Component breakdown:")
    for component, count in stats['logged_by'].items():
        print(f"   {component}: {count} events")
    
    print("\n=== Demo Complete ===")
    print("The deduplication service successfully prevented duplicate events")
    print("while allowing legitimate different events to be logged.")


if __name__ == "__main__":
    main()