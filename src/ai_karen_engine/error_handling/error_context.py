"""
Error Context Management System

This module provides comprehensive error context preservation and restoration
with intelligent context capture, storage, and retrieval capabilities.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from threading import Lock

import asyncio
import traceback
from .error_classifier import ErrorClassification


class ContextScope(Enum):
    """Scope levels for error context."""
    
    REQUEST = "request"           # Context for single request
    SESSION = "session"           # Context for user session
    COMPONENT = "component"        # Context for component
    SYSTEM = "system"             # Context for entire system
    GLOBAL = "global"             # Global context


class ContextType(Enum):
    """Types of context data."""
    
    USER_DATA = "user_data"           # User-related data
    REQUEST_DATA = "request_data"       # Request-related data
    SYSTEM_STATE = "system_state"       # System state information
    COMPONENT_STATE = "component_state"   # Component state
    BUSINESS_DATA = "business_data"       # Business logic data
    TEMPORARY = "temporary"           # Temporary data
    PERSISTENT = "persistent"         # Persistent data


@dataclass
class ContextEntry:
    """Single context entry with metadata."""
    
    key: str
    value: Any
    context_type: ContextType
    scope: ContextScope
    timestamp: datetime
    ttl: Optional[float] = None  # Time to live in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if context entry has expired."""
        if self.ttl is None:
            return False
        
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "context_type": self.context_type.value,
            "scope": self.scope.value,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextEntry':
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            context_type=ContextType(data["context_type"]),
            scope=ContextScope(data["scope"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl=data.get("ttl"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ErrorContext:
    """Comprehensive error context with multiple data points."""
    
    context_id: str
    error_id: str
    timestamp: datetime
    classification: Optional[ErrorClassification] = None
    
    # Core context data
    entries: Dict[str, ContextEntry] = field(default_factory=dict)
    
    # Hierarchical context
    parent_context_id: Optional[str] = None
    child_context_ids: List[str] = field(default_factory=list)
    
    # Metadata
    scope: ContextScope = ContextScope.REQUEST
    component: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # System information
    system_info: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_entry(
        self,
        key: str,
        value: Any,
        context_type: ContextType,
        scope: ContextScope = ContextScope.REQUEST,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add context entry."""
        entry = ContextEntry(
            key=key,
            value=value,
            context_type=context_type,
            scope=scope,
            timestamp=datetime.utcnow(),
            ttl=ttl,
            metadata=metadata or {}
        )
        self.entries[key] = entry
    
    def get_entry(self, key: str) -> Optional[ContextEntry]:
        """Get context entry by key."""
        entry = self.entries.get(key)
        if entry and entry.is_expired():
            del self.entries[key]
            return None
        return entry
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value from context entry."""
        entry = self.get_entry(key)
        return entry.value if entry else default
    
    def remove_entry(self, key: str) -> bool:
        """Remove context entry."""
        if key in self.entries:
            del self.entries[key]
            return True
        return False
    
    def get_entries_by_type(self, context_type: ContextType) -> List[ContextEntry]:
        """Get all entries of specific type."""
        return [entry for entry in self.entries.values() 
                if entry.context_type == context_type and not entry.is_expired()]
    
    def get_entries_by_scope(self, scope: ContextScope) -> List[ContextEntry]:
        """Get all entries of specific scope."""
        return [entry for entry in self.entries.values() 
                if entry.scope == scope and not entry.is_expired()]
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        expired_keys = [
            key for key, entry in self.entries.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.entries[key]
        
        return len(expired_keys)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "context_id": self.context_id,
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "classification": asdict(self.classification) if self.classification else None,
            "entries": {k: v.to_dict() for k, v in self.entries.items()},
            "parent_context_id": self.parent_context_id,
            "child_context_ids": self.child_context_ids,
            "scope": self.scope.value,
            "component": self.component,
            "operation": self.operation,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "system_info": self.system_info,
            "environment_info": self.environment_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorContext':
        """Create from dictionary."""
        context = cls(
            context_id=data["context_id"],
            error_id=data["error_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            classification=ErrorClassification(**data["classification"]) if data.get("classification") else None,
            parent_context_id=data.get("parent_context_id"),
            child_context_ids=data.get("child_context_ids", []),
            scope=ContextScope(data.get("scope", ContextScope.REQUEST.value)),
            component=data.get("component"),
            operation=data.get("operation"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            system_info=data.get("system_info", {}),
            environment_info=data.get("environment_info", {})
        )
        
        # Restore entries
        entries_data = data.get("entries", {})
        context.entries = {
            key: ContextEntry.from_dict(entry_data)
            for key, entry_data in entries_data.items()
        }
        
        return context


class ContextManager:
    """
    Comprehensive context manager for error handling.
    
    Features:
    - Hierarchical context management
    - Context preservation and restoration
    - TTL-based expiration
    - Scope-based isolation
    - Automatic cleanup
    - Serialization support
    """
    
    def __init__(self):
        self.contexts: Dict[str, ErrorContext] = {}
        self.active_contexts: Dict[str, str] = {}  # scope -> context_id mapping
        self.lock = Lock()
        
        # Context storage backends
        self.storage_backends = {}
        
        # Cleanup task
        self.cleanup_interval = 300  # 5 minutes
        self._schedule_cleanup()
    
    def create_context(
        self,
        error_id: str,
        scope: ContextScope = ContextScope.REQUEST,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        parent_context_id: Optional[str] = None
    ) -> ErrorContext:
        """Create new error context."""
        context_id = str(uuid.uuid4())
        
        context = ErrorContext(
            context_id=context_id,
            error_id=error_id,
            timestamp=datetime.utcnow(),
            scope=scope,
            component=component,
            operation=operation,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            parent_context_id=parent_context_id
        )
        
        with self.lock:
            self.contexts[context_id] = context
            self.active_contexts[scope.value] = context_id
            
            # Update parent context
            if parent_context_id and parent_context_id in self.contexts:
                parent = self.contexts[parent_context_id]
                parent.child_context_ids.append(context_id)
        
        return context
    
    def get_context(self, context_id: str) -> Optional[ErrorContext]:
        """Get context by ID."""
        with self.lock:
            return self.contexts.get(context_id)
    
    def get_active_context(self, scope: ContextScope) -> Optional[ErrorContext]:
        """Get active context for scope."""
        with self.lock:
            context_id = self.active_contexts.get(scope.value)
            return self.contexts.get(context_id) if context_id else None
    
    def update_context(self, context_id: str, **updates) -> bool:
        """Update context with new values."""
        with self.lock:
            if context_id not in self.contexts:
                return False
            
            context = self.contexts[context_id]
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
            
            return True
    
    def add_context_data(
        self,
        context_id: str,
        key: str,
        value: Any,
        context_type: ContextType,
        scope: ContextScope = ContextScope.REQUEST,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add data to context."""
        with self.lock:
            if context_id not in self.contexts:
                return False
            
            context = self.contexts[context_id]
            context.add_entry(key, value, context_type, scope, ttl, metadata)
            return True
    
    def get_context_data(self, context_id: str, key: str) -> Optional[Any]:
        """Get data from context."""
        with self.lock:
            context = self.contexts.get(context_id)
            if not context:
                return None
            
            entry = context.get_entry(key)
            return entry.value if entry else None
    
    def remove_context_data(self, context_id: str, key: str) -> bool:
        """Remove data from context."""
        with self.lock:
            context = self.contexts.get(context_id)
            if not context:
                return False
            
            return context.remove_entry(key)
    
    def preserve_context(self, context_id: str, backend: str = "memory") -> bool:
        """Preserve context to storage backend."""
        context = self.get_context(context_id)
        if not context:
            return False
        
        if backend not in self.storage_backends:
            return False
        
        try:
            storage = self.storage_backends[backend]
            storage.store(context_id, context.to_dict())
            return True
        except Exception:
            return False
    
    def restore_context(self, context_id: str, backend: str = "memory") -> Optional[ErrorContext]:
        """Restore context from storage backend."""
        if backend not in self.storage_backends:
            return None
        
        try:
            storage = self.storage_backends[backend]
            data = storage.retrieve(context_id)
            if data:
                context = ErrorContext.from_dict(data)
                
                with self.lock:
                    self.contexts[context_id] = context
                
                return context
        except Exception:
            pass
        
        return None
    
    def delete_context(self, context_id: str) -> bool:
        """Delete context."""
        with self.lock:
            if context_id not in self.contexts:
                return False
            
            context = self.contexts[context_id]
            
            # Remove from active contexts
            for scope, active_id in list(self.active_contexts.items()):
                if active_id == context_id:
                    del self.active_contexts[scope]
            
            # Remove from parent context
            if context.parent_context_id and context.parent_context_id in self.contexts:
                parent = self.contexts[context.parent_context_id]
                if context_id in parent.child_context_ids:
                    parent.child_context_ids.remove(context_id)
            
            # Delete context
            del self.contexts[context_id]
            
            # Delete from storage backends
            for backend in self.storage_backends.values():
                try:
                    backend.delete(context_id)
                except Exception:
                    pass
            
            return True
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries across all contexts."""
        total_cleaned = 0
        
        with self.lock:
            for context in self.contexts.values():
                total_cleaned += context.cleanup_expired()
        
        return total_cleaned
    
    def get_context_hierarchy(self, context_id: str) -> List[ErrorContext]:
        """Get full hierarchy of contexts."""
        hierarchy = []
        current_id = context_id
        
        with self.lock:
            while current_id:
                context = self.contexts.get(current_id)
                if not context:
                    break
                
                hierarchy.append(context)
                current_id = context.parent_context_id
        
        return hierarchy
    
    def get_context_children(self, context_id: str) -> List[ErrorContext]:
        """Get all child contexts."""
        children = []
        
        with self.lock:
            context = self.contexts.get(context_id)
            if not context:
                return children
            
            for child_id in context.child_context_ids:
                child = self.contexts.get(child_id)
                if child:
                    children.append(child)
        
        return children
    
    def register_storage_backend(self, name: str, backend) -> None:
        """Register storage backend."""
        self.storage_backends[name] = backend
    
    def unregister_storage_backend(self, name: str) -> bool:
        """Unregister storage backend."""
        if name in self.storage_backends:
            del self.storage_backends[name]
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        with self.lock:
            total_contexts = len(self.contexts)
            active_contexts = len(self.active_contexts)
            
            # Count by scope
            scope_counts = {}
            for context in self.contexts.values():
                scope = context.scope.value
                scope_counts[scope] = scope_counts.get(scope, 0) + 1
            
            # Count total entries
            total_entries = sum(len(context.entries) for context in self.contexts.values())
            
            return {
                "total_contexts": total_contexts,
                "active_contexts": active_contexts,
                "contexts_by_scope": scope_counts,
                "total_entries": total_entries,
                "storage_backends": list(self.storage_backends.keys())
            }
    
    def _schedule_cleanup(self) -> None:
        """Schedule periodic cleanup."""
        import threading
        
        def cleanup_task():
            while True:
                try:
                    self.cleanup_expired()
                except Exception:
                    pass
                
                # Sleep for cleanup interval
                threading.Event().wait(self.cleanup_interval)
        
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()


class MemoryStorageBackend:
    """In-memory storage backend for contexts."""
    
    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()
    
    def store(self, key: str, data: Dict[str, Any]) -> None:
        """Store data."""
        with self.lock:
            self.storage[key] = data
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data."""
        with self.lock:
            return self.storage.get(key)
    
    def delete(self, key: str) -> bool:
        """Delete data."""
        with self.lock:
            if key in self.storage:
                del self.storage[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all data."""
        with self.lock:
            self.storage.clear()


# Global context manager instance
context_manager = ContextManager()

# Register default memory backend
context_manager.register_storage_backend("memory", MemoryStorageBackend())


def with_error_context(
    scope: ContextScope = ContextScope.REQUEST,
    component: Optional[str] = None,
    operation: Optional[str] = None
):
    """Decorator for automatic error context management."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate error ID
            error_id = str(uuid.uuid4())
            
            # Extract context information
            user_id = kwargs.get("user_id")
            session_id = kwargs.get("session_id")
            request_id = kwargs.get("request_id")
            
            # Create context
            context = context_manager.create_context(
                error_id=error_id,
                scope=scope,
                component=component,
                operation=operation,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id
            )
            
            # Add function arguments to context
            context.add_entry(
                "function_args",
                {"args": args, "kwargs": kwargs},
                ContextType.REQUEST_DATA
            )
            
            # Add system information
            context.add_entry(
                "function_name",
                func.__name__,
                ContextType.SYSTEM_STATE
            )
            
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func, *args, **kwargs)
                
                # Add success to context
                context.add_entry(
                    "execution_success",
                    True,
                    ContextType.SYSTEM_STATE
                )
                
                return result
                
            except Exception as e:
                # Add error to context
                context.add_entry(
                    "execution_error",
                    {
                        "type": type(e).__name__,
                        "message": str(e),
                        "traceback": traceback.format_exc() if 'traceback' in globals() else None
                    },
                    ContextType.SYSTEM_STATE
                )
                
                # Preserve context on error
                context_manager.preserve_context(context.context_id)
                
                raise
        
        return wrapper
    return decorator