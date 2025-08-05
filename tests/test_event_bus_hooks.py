"""
Unit tests for EventBus hook integration.
Extends existing event bus tests with hook functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
import types

from ai_karen_engine.event_bus import EventBus, RedisEventBus, Event, get_event_bus
from ai_karen_engine.config import config_manager


class TestEventBusHooks:
    """Test EventBus hook integration."""
    
    @pytest.fixture
    def event_bus(self):
        """Create a fresh EventBus instance."""
        return EventBus()
    
    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return Event(
            id="test_id",
            capsule="test_capsule",
            event_type="test_event",
            payload={"key": "value"},
            risk=0.0,
            roles=["admin"],
            tenant_id="test_tenant"
        )
    
    def test_event_bus_hook_initialization(self, event_bus):
        """Test that EventBus initializes with hook capabilities."""
        assert hasattr(event_bus, '_hook_handlers')
        assert hasattr(event_bus, '_hook_enabled')
        assert event_bus._hook_enabled is True
        assert len(event_bus._hook_handlers) == 0
    
    def test_register_hook_handler(self, event_bus):
        """Test registering hook handlers."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Register handler
        event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Verify handler is registered
        assert len(event_bus._hook_handlers["test_capsule.test_event"]) == 1
        assert event_bus._hook_handlers["test_capsule.test_event"][0] == test_handler
    
    def test_unregister_hook_handler(self, event_bus):
        """Test unregistering hook handlers."""
        def test_handler(event):
            pass
        
        # Register and then unregister
        event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        assert len(event_bus._hook_handlers["test_capsule.test_event"]) == 1
        
        success = event_bus.unregister_hook_handler("test_capsule.test_event", test_handler)
        assert success
        assert len(event_bus._hook_handlers["test_capsule.test_event"]) == 0
        
        # Try to unregister non-existent handler
        success = event_bus.unregister_hook_handler("test_capsule.test_event", test_handler)
        assert not success
    
    def test_enable_disable_hooks(self, event_bus):
        """Test enabling and disabling hooks."""
        assert event_bus._hook_enabled is True
        
        event_bus.disable_hooks()
        assert event_bus._hook_enabled is False
        
        event_bus.enable_hooks()
        assert event_bus._hook_enabled is True
    
    def test_hook_handler_triggered_on_publish(self, event_bus, sample_event):
        """Test that hook handlers are triggered when events are published."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Register handler for specific event type
        event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Publish event
        event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Verify handler was called
        assert len(handler_calls) == 1
        assert handler_calls[0].capsule == "test_capsule"
        assert handler_calls[0].event_type == "test_event"
        assert handler_calls[0].payload == {"key": "value"}
    
    def test_wildcard_hook_handler(self, event_bus):
        """Test wildcard hook handlers that catch all events."""
        handler_calls = []
        
        def wildcard_handler(event):
            handler_calls.append(event)
        
        # Register wildcard handler
        event_bus.register_hook_handler("*", wildcard_handler)
        
        # Publish different events
        event_bus.publish("capsule1", "event1", {"data": 1}, roles=["admin"])
        event_bus.publish("capsule2", "event2", {"data": 2}, roles=["admin"])
        
        # Verify wildcard handler caught both events
        assert len(handler_calls) == 2
        assert handler_calls[0].capsule == "capsule1"
        assert handler_calls[1].capsule == "capsule2"
    
    def test_hook_handler_error_handling(self, event_bus):
        """Test that hook handler errors don't break event publishing."""
        def failing_handler(event):
            raise ValueError("Handler failed")
        
        def working_handler(event):
            working_handler.called = True
        working_handler.called = False
        
        # Register both handlers
        event_bus.register_hook_handler("test_capsule.test_event", failing_handler)
        event_bus.register_hook_handler("test_capsule.test_event", working_handler)
        
        # Publish event - should not raise exception
        event_id = event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Event should still be published successfully
        assert event_id is not None
        
        # Working handler should still be called
        assert working_handler.called
    
    def test_hooks_disabled_no_handler_execution(self, event_bus):
        """Test that disabled hooks prevent handler execution."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Register handler and disable hooks
        event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        event_bus.disable_hooks()
        
        # Publish event
        event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Handler should not be called
        assert len(handler_calls) == 0
    
    def test_multiple_handlers_same_event(self, event_bus):
        """Test multiple handlers for the same event type."""
        handler1_calls = []
        handler2_calls = []
        
        def handler1(event):
            handler1_calls.append(event)
        
        def handler2(event):
            handler2_calls.append(event)
        
        # Register multiple handlers
        event_bus.register_hook_handler("test_capsule.test_event", handler1)
        event_bus.register_hook_handler("test_capsule.test_event", handler2)
        
        # Publish event
        event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Both handlers should be called
        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1
    
    def test_hook_integration_with_existing_functionality(self, event_bus):
        """Test that hooks don't interfere with existing event bus functionality."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Register handler
        event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Publish event
        event_id = event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Consume events (existing functionality)
        events = event_bus.consume(roles=["admin"])
        
        # Verify both hook and consume work
        assert len(handler_calls) == 1  # Hook handler called
        assert len(events) == 1  # Event consumed normally
        assert events[0].id == event_id
        assert handler_calls[0].id == event_id


class TestRedisEventBusHooks:
    """Test RedisEventBus hook integration."""
    
    @pytest.fixture
    def fake_redis_client(self):
        """Create a fake Redis client."""
        class FakeRedisClient:
            def __init__(self):
                self.storage = []
            
            def rpush(self, key, val):
                self.storage.append(val)
            
            def lrange(self, key, start, end):
                if end == -1:
                    end = len(self.storage) - 1
                return self.storage[start:end+1]
            
            def delete(self, key):
                self.storage.clear()
        
        return FakeRedisClient()
    
    @pytest.fixture
    def redis_event_bus(self, fake_redis_client):
        """Create a RedisEventBus with fake Redis client."""
        return RedisEventBus(redis_client=fake_redis_client)
    
    def test_redis_event_bus_hook_functionality(self, redis_event_bus):
        """Test that RedisEventBus inherits hook functionality."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Register handler
        redis_event_bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Publish event
        redis_event_bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Verify handler was called
        assert len(handler_calls) == 1
        assert handler_calls[0].capsule == "test_capsule"


class TestEventBusHookIntegration:
    """Integration tests for EventBus hooks with existing functionality."""
    
    def test_hook_integration_with_role_filtering(self):
        """Test that hooks work with existing role filtering."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Create event bus and register handler
        bus = EventBus()
        bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Publish event with admin role
        bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value"},
            roles=["admin"]
        )
        
        # Consume with admin role
        events = bus.consume(roles=["admin"])
        
        # Both hook and consume should work
        assert len(handler_calls) == 1
        assert len(events) == 1
        
        # Clear and test with different roles
        handler_calls.clear()
        
        # Publish with user role
        bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value2"},
            roles=["user"]
        )
        
        # Consume with admin role (should not get user event)
        events = bus.consume(roles=["admin"])
        
        # Hook should still be called (hooks don't filter by consumer roles)
        assert len(handler_calls) == 1
        assert len(events) == 0  # But consume should filter
    
    def test_hook_integration_with_tenant_filtering(self):
        """Test that hooks work with tenant filtering."""
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        # Create event bus and register handler
        bus = EventBus()
        bus.register_hook_handler("test_capsule.test_event", test_handler)
        
        # Publish events with different tenants
        bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value1"},
            roles=["admin"],
            tenant_id="tenant1"
        )
        
        bus.publish(
            "test_capsule",
            "test_event",
            {"key": "value2"},
            roles=["admin"],
            tenant_id="tenant2"
        )
        
        # Hook should catch both events
        assert len(handler_calls) == 2
        
        # Consume with tenant filtering
        tenant1_events = bus.consume(roles=["admin"], tenant_id="tenant1")
        tenant2_events = bus.consume(roles=["admin"], tenant_id="tenant2")
        
        # Consume should respect tenant filtering
        assert len(tenant1_events) == 1
        assert len(tenant2_events) == 1
        assert tenant1_events[0].tenant_id == "tenant1"
        assert tenant2_events[0].tenant_id == "tenant2"
    
    def test_get_event_bus_with_hooks(self, monkeypatch):
        """Test that get_event_bus returns bus with hook capabilities."""
        # Reset global bus
        import ai_karen_engine.event_bus as eb
        eb._global_bus = None
        
        # Force memory backend
        monkeypatch.setattr(config_manager, "get_config_value", lambda section, key, default=None: "memory")
        
        bus = get_event_bus()
        
        # Verify it has hook capabilities
        assert hasattr(bus, 'register_hook_handler')
        assert hasattr(bus, 'unregister_hook_handler')
        assert hasattr(bus, 'enable_hooks')
        assert hasattr(bus, 'disable_hooks')
        
        # Test hook functionality
        handler_calls = []
        
        def test_handler(event):
            handler_calls.append(event)
        
        bus.register_hook_handler("test.event", test_handler)
        bus.publish("test", "event", {"data": "test"}, roles=["admin"])
        
        assert len(handler_calls) == 1