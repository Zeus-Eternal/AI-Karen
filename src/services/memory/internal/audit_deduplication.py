"""
Audit Log Deduplication Service

This service provides mechanisms to prevent duplicate audit log entries
by tracking events and ensuring single entries per unique event.
"""

import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.core.cache import MemoryCache

logger = get_logger(__name__)


class EventType(str, Enum):
    """Types of events that can be deduplicated"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT_SUCCESS = "logout_success"
    TOKEN_REFRESH = "token_refresh"
    SESSION_VALIDATION = "session_validation"
    TOKEN_CREATION = "token_creation"
    ERROR_RESPONSE = "error_response"


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
    logged_by: str  # Component that logged the event
    ttl_seconds: int = 300  # 5 minutes default TTL
    
    def is_expired(self) -> bool:
        """Check if this event record has expired"""
        return datetime.now(timezone.utc) > self.timestamp + timedelta(seconds=self.ttl_seconds)


class AuditDeduplicationService:
    """Service for preventing duplicate audit log entries"""
    
    def __init__(self):
        self._cache = MemoryCache(max_size=10000, default_ttl=300)  # Use memory cache for events
        self._local_events: Dict[str, EventRecord] = {}
        self._cleanup_interval = 300  # 5 minutes
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
            logger.debug(f"Cleaned up {len(expired_keys)} expired audit event records")
    
    def should_log_event(
        self,
        event_key: EventKey,
        logged_by: str,
        ttl_seconds: int = 300
    ) -> bool:
        """
        Check if an event should be logged (not a duplicate).
        
        Args:
            event_key: Unique key identifying the event
            logged_by: Component attempting to log the event
            ttl_seconds: Time-to-live for deduplication (default 5 minutes)
            
        Returns:
            True if event should be logged, False if it's a duplicate
        """
        self._cleanup_expired_events()
        
        event_hash = event_key.to_hash()
        
        # Check local cache first (fastest)
        if event_hash in self._local_events:
            existing_record = self._local_events[event_hash]
            if not existing_record.is_expired():
                logger.debug(
                    f"Duplicate event detected: {event_key.event_type.value} "
                    f"(originally logged by {existing_record.logged_by}, "
                    f"now attempted by {logged_by})"
                )
                return False
            else:
                # Remove expired record
                del self._local_events[event_hash]
        
        # Check memory cache if available
        if self._cache:
            try:
                cached_record = self._cache.get(f"audit_event:{event_hash}")
                if cached_record:
                    logger.debug(
                        f"Duplicate event detected in memory cache: "
                        f"{event_key.event_type.value} (attempted by {logged_by})"
                    )
                    return False
            except Exception as e:
                logger.warning(f"Failed to check memory cache for event deduplication: {e}")
        
        # Event is not a duplicate, record it
        record = EventRecord(
            event_key=event_key,
            timestamp=datetime.now(timezone.utc),
            logged_by=logged_by,
            ttl_seconds=ttl_seconds
        )
        
        # Store in local cache
        self._local_events[event_hash] = record
        
        # Store in memory cache if available
        if self._cache:
            try:
                self._cache.set(
                    f"audit_event:{event_hash}",
                    {
                        "logged_by": logged_by,
                        "timestamp": record.timestamp.isoformat(),
                        "event_type": event_key.event_type.value
                    },
                    ttl=ttl_seconds
                )
            except Exception as e:
                logger.warning(f"Failed to store event in memory cache: {e}")
        
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
        """
        Check if an authentication event should be logged.
        
        This is a convenience method for authentication-specific events.
        """
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
        ttl_seconds: int = 60  # Shorter TTL for session validations
    ) -> bool:
        """
        Check if a session validation event should be logged.
        
        Session validations have a shorter TTL since they happen frequently.
        """
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
        ttl_seconds: int = 30  # Short TTL for token operations
    ) -> bool:
        """
        Check if a token operation should be logged.
        
        Token operations have a short TTL since they can happen in quick succession.
        """
        event_key = EventKey(
            event_type=EventType.TOKEN_CREATION,
            user_id=user_id,
            additional_context={
                "operation": operation_name,
                "token_jti": token_jti
            }
        )
        
        return self.should_log_event(event_key, logged_by, ttl_seconds)
    
    def mark_event_logged(
        self,
        event_key: EventKey,
        logged_by: str,
        ttl_seconds: int = 300
    ) -> None:
        """
        Mark an event as logged without checking for duplicates.
        
        This is useful when you want to manually track an event.
        """
        event_hash = event_key.to_hash()
        
        record = EventRecord(
            event_key=event_key,
            timestamp=datetime.now(timezone.utc),
            logged_by=logged_by,
            ttl_seconds=ttl_seconds
        )
        
        # Store in local cache
        self._local_events[event_hash] = record
        
        # Store in memory cache if available
        if self._cache:
            try:
                self._cache.set(
                    f"audit_event:{event_hash}",
                    {
                        "logged_by": logged_by,
                        "timestamp": record.timestamp.isoformat(),
                        "event_type": event_key.event_type.value
                    },
                    ttl=ttl_seconds
                )
            except Exception as e:
                logger.warning(f"Failed to store event in memory cache: {e}")
    
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
        """Clear all tracked events (for testing/debugging)"""
        self._local_events.clear()
        logger.info("Cleared all tracked audit events")


# Global instance
_deduplication_service: Optional[AuditDeduplicationService] = None


def get_audit_deduplication_service() -> AuditDeduplicationService:
    """Get the global audit deduplication service instance"""
    global _deduplication_service
    if _deduplication_service is None:
        _deduplication_service = AuditDeduplicationService()
    return _deduplication_service


# Export main classes and functions
__all__ = [
    "AuditDeduplicationService",
    "EventType",
    "EventKey",
    "EventRecord",
    "get_audit_deduplication_service"
]