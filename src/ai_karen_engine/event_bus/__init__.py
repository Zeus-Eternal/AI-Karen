"""
Simple in-memory and Redis-backed event bus with tenant & role filtering.
Enhanced with hook-specific event types and routing.
"""

from __future__ import annotations

import collections
import json
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, List, Optional, Union, Callable

from ai_karen_engine.config.config_manager import config_manager

# Optional Redis dependency
try:
    import redis  # type: ignore
except ImportError:
    redis = None

# Default configuration
REDIS_URL = config_manager.get_config_value("redis", "url", default=os.getenv("REDIS_URL"))
EVENT_LIST_KEY = config_manager.get_config_value("event_bus", "key", default="kari:events")
ALLOWED_PUBLISH_ROLES = set(config_manager.get_config_value("event_bus", "allowed_roles", default=["admin", "user"]))

@dataclass
class Event:
    id: str
    capsule: str
    event_type: str
    payload: Dict[str, Any]
    risk: float
    roles: List[str]
    tenant_id: Optional[str] = None

class EventBus:
    """In-memory FIFO event bus with optional Redis fallback and hook routing."""

    def __init__(self) -> None:
        self._queue: Deque[Event] = collections.deque()
        self._redis: Optional["redis.Redis"] = None
        self._hook_handlers: Dict[str, List[Callable]] = collections.defaultdict(list)
        self._hook_enabled = True
        
        # Collaboration-specific event tracking
        self._presence_events: Dict[str, Dict[str, Any]] = {}
        self._typing_events: Dict[str, Dict[str, Any]] = {}
        self._collaboration_sessions: Dict[str, Dict[str, Any]] = {}

        if redis and REDIS_URL:
            try:
                self._redis = redis.from_url(REDIS_URL)
            except Exception:
                self._redis = None

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        # enforce allowed roles
        if not roles or not ALLOWED_PUBLISH_ROLES.intersection(roles):
            raise PermissionError("Publish denied: insufficient roles")
        eid = str(uuid.uuid4())
        event = Event(eid, capsule, event_type, payload, risk, roles, tenant_id)

        # trigger hook handlers if enabled
        if self._hook_enabled:
            self._trigger_hook_handlers(event)

        # try Redis first
        if self._redis:
            try:
                self._redis.rpush(EVENT_LIST_KEY, json.dumps(asdict(event)))
                return eid
            except Exception:
                self._redis = None  # disable Redis on failure

        # fallback to in-memory queue
        self._queue.append(event)
        return eid

    def consume(
        self,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Event]:
        results: List[Event] = []

        # drain Redis list if available
        if self._redis:
            try:
                raw = self._redis.lrange(EVENT_LIST_KEY, 0, -1)
                self._redis.delete(EVENT_LIST_KEY)
                for item in raw:
                    text = item.decode() if isinstance(item, (bytes, bytearray)) else item
                    data = json.loads(text)
                    results.append(Event(**data))
            except Exception:
                self._redis = None  # disable Redis on error

        # drain in-memory queue
        results.extend(self._queue)
        self._queue.clear()

        # apply tenant & role filtering
        def allowed(e: Event) -> bool:
            if tenant_id is not None and e.tenant_id != tenant_id:
                return False
            if roles and not set(roles).intersection(e.roles):
                return False
            return True

        return [e for e in results if allowed(e)]
    
    def register_hook_handler(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register a hook handler for specific event types."""
        self._hook_handlers[event_type].append(handler)
    
    def unregister_hook_handler(self, event_type: str, handler: Callable[[Event], None]) -> bool:
        """Unregister a hook handler."""
        if event_type in self._hook_handlers:
            try:
                self._hook_handlers[event_type].remove(handler)
                return True
            except ValueError:
                pass
        return False
    
    def enable_hooks(self) -> None:
        """Enable hook processing."""
        self._hook_enabled = True
    
    def disable_hooks(self) -> None:
        """Disable hook processing."""
        self._hook_enabled = False
    
    def _trigger_hook_handlers(self, event: Event) -> None:
        """Trigger registered hook handlers for an event."""
        if not self._hook_enabled:
            return
        
        # Handle collaboration-specific events
        self._handle_collaboration_events(event)
        
        # Trigger handlers for specific event type
        event_key = f"{event.capsule}.{event.event_type}"
        for handler in self._hook_handlers.get(event_key, []):
            try:
                handler(event)
            except Exception:
                # Silently ignore hook handler errors to prevent disrupting event flow
                pass
        
        # Trigger handlers for wildcard patterns
        for handler in self._hook_handlers.get("*", []):
            try:
                handler(event)
            except Exception:
                pass
    
    def _handle_collaboration_events(self, event: Event) -> None:
        """Handle collaboration-specific events for presence and typing indicators."""
        try:
            if event.event_type == "user_presence_update":
                user_id = event.payload.get("user_id")
                if user_id:
                    self._presence_events[user_id] = {
                        "status": event.payload.get("status", "online"),
                        "last_seen": event.payload.get("timestamp"),
                        "conversation_id": event.payload.get("conversation_id"),
                        "metadata": event.payload.get("metadata", {})
                    }
            
            elif event.event_type == "typing_indicator":
                user_id = event.payload.get("user_id")
                conversation_id = event.payload.get("conversation_id")
                if user_id and conversation_id:
                    key = f"{conversation_id}:{user_id}"
                    if event.payload.get("is_typing", False):
                        self._typing_events[key] = {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "started_at": event.payload.get("timestamp"),
                            "expires_at": event.payload.get("expires_at")
                        }
                    else:
                        self._typing_events.pop(key, None)
            
            elif event.event_type == "collaboration_session_start":
                session_id = event.payload.get("session_id")
                if session_id:
                    self._collaboration_sessions[session_id] = {
                        "participants": event.payload.get("participants", []),
                        "conversation_id": event.payload.get("conversation_id"),
                        "started_at": event.payload.get("timestamp"),
                        "type": event.payload.get("session_type", "chat"),
                        "metadata": event.payload.get("metadata", {})
                    }
            
            elif event.event_type == "collaboration_session_end":
                session_id = event.payload.get("session_id")
                if session_id:
                    self._collaboration_sessions.pop(session_id, None)
                    
        except Exception:
            # Silently ignore collaboration event handling errors
            pass
    
    def get_user_presence(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current presence status for a user."""
        return self._presence_events.get(user_id)
    
    def get_online_users(self, conversation_id: Optional[str] = None) -> List[str]:
        """Get list of online users, optionally filtered by conversation."""
        online_users = []
        for user_id, presence in self._presence_events.items():
            if presence.get("status") == "online":
                if not conversation_id or presence.get("conversation_id") == conversation_id:
                    online_users.append(user_id)
        return online_users
    
    def get_typing_users(self, conversation_id: str) -> List[str]:
        """Get list of users currently typing in a conversation."""
        typing_users = []
        for key, typing_info in self._typing_events.items():
            if typing_info.get("conversation_id") == conversation_id:
                typing_users.append(typing_info.get("user_id"))
        return typing_users
    
    def get_collaboration_sessions(self, conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active collaboration sessions, optionally filtered by conversation."""
        sessions = []
        for session_id, session_info in self._collaboration_sessions.items():
            if not conversation_id or session_info.get("conversation_id") == conversation_id:
                sessions.append({
                    "session_id": session_id,
                    **session_info
                })
        return sessions
    
    def publish_presence_update(
        self,
        user_id: str,
        status: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None
    ) -> str:
        """Publish a user presence update event."""
        import time
        return self.publish(
            capsule="collaboration",
            event_type="user_presence_update",
            payload={
                "user_id": user_id,
                "status": status,
                "conversation_id": conversation_id,
                "timestamp": time.time(),
                "metadata": metadata or {}
            },
            roles=roles or ["user", "admin"]
        )
    
    def publish_typing_indicator(
        self,
        user_id: str,
        conversation_id: str,
        is_typing: bool,
        expires_in_seconds: int = 5,
        roles: Optional[List[str]] = None
    ) -> str:
        """Publish a typing indicator event."""
        import time
        current_time = time.time()
        return self.publish(
            capsule="collaboration",
            event_type="typing_indicator",
            payload={
                "user_id": user_id,
                "conversation_id": conversation_id,
                "is_typing": is_typing,
                "timestamp": current_time,
                "expires_at": current_time + expires_in_seconds if is_typing else None
            },
            roles=roles or ["user", "admin"]
        )
    
    def publish_collaboration_session(
        self,
        session_id: str,
        action: str,  # "start" or "end"
        participants: List[str],
        conversation_id: str,
        session_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
        roles: Optional[List[str]] = None
    ) -> str:
        """Publish a collaboration session event."""
        import time
        return self.publish(
            capsule="collaboration",
            event_type=f"collaboration_session_{action}",
            payload={
                "session_id": session_id,
                "participants": participants,
                "conversation_id": conversation_id,
                "session_type": session_type,
                "timestamp": time.time(),
                "metadata": metadata or {}
            },
            roles=roles or ["user", "admin"]
        )

class RedisEventBus(EventBus):
    """Explicit Redis-only event bus (list semantics)."""

    def __init__(
        self,
        redis_client: Optional["redis.Redis"] = None,
        list_key: Optional[str] = None,
    ) -> None:
        # Initialize parent EventBus (which includes hook functionality)
        EventBus.__init__(self)
        if redis_client:
            self._redis = redis_client
        elif redis is None:
            raise ImportError("redis package is required for RedisEventBus")
        elif REDIS_URL:
            self._redis = redis.from_url(REDIS_URL)
        else:
            self._redis = redis.Redis()
        self._list_key = list_key or EVENT_LIST_KEY

    def publish(
        self,
        capsule: str,
        event_type: str,
        payload: Dict[str, Any],
        risk: float = 0.0,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> str:
        if not roles or not ALLOWED_PUBLISH_ROLES.intersection(roles):
            raise PermissionError("Publish denied: insufficient roles")
        eid = str(uuid.uuid4())
        ev = Event(eid, capsule, event_type, payload, risk, roles or [], tenant_id)
        
        # trigger hook handlers if enabled
        if self._hook_enabled:
            self._trigger_hook_handlers(ev)
        
        self._redis.rpush(self._list_key, json.dumps(asdict(ev)))
        return eid

    def consume(
        self,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> List[Event]:
        raw = self._redis.lrange(self._list_key, 0, -1)
        if raw:
            self._redis.delete(self._list_key)
        events: List[Event] = []
        for item in raw:
            text = item.decode() if isinstance(item, (bytes, bytearray)) else item
            data = json.loads(text)
            events.append(Event(**data))
        # apply same filtering as base
        return super().consume(roles=roles, tenant_id=tenant_id)

# Singleton accessor
_global_bus: Union[EventBus, RedisEventBus, None] = None

def get_event_bus() -> Union[EventBus, RedisEventBus]:
    """Return a singleton EventBus, preferring Redis if configured."""
    global _global_bus
    if _global_bus is not None:
        return _global_bus

    backend = config_manager.get_config_value("event_bus", "backend", default="memory").lower()
    if backend == "redis" and redis:
        try:
            _global_bus = RedisEventBus()
        except Exception as e:
            # Log the exception for debugging
            import logging
            logging.getLogger(__name__).debug(f"Failed to create RedisEventBus: {e}")
            _global_bus = EventBus()
    else:
        _global_bus = EventBus()

    return _global_bus

__all__ = ["Event", "EventBus", "RedisEventBus", "get_event_bus"]
