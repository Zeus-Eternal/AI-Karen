"""
Integration tests for WebSocket functionality.

This module tests the complete WebSocket integration including
the API routes, gateway, and stream processor working together.
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Import the modules to test
from ai_karen_engine.api_routes.websocket_routes import (
    get_websocket_gateway,
    get_stream_processor,
    websocket_health_check
)
from ai_karen_engine.chat.websocket_gateway import WebSocketGateway
from ai_karen_engine.chat.stream_processor import StreamProcessor


class TestWebSocketIntegration:
    """Test WebSocket integration functionality."""
    
    def test_websocket_gateway_initialization(self):
        """Test that WebSocket gateway can be initialized."""
        gateway = get_websocket_gateway()
        
        assert isinstance(gateway, WebSocketGateway)
        assert gateway.chat_orchestrator is not None
        assert gateway.typing_manager is not None
        assert gateway.presence_manager is not None
        assert gateway.message_queue is not None
    
    def test_stream_processor_initialization(self):
        """Test that stream processor can be initialized."""
        processor = get_stream_processor()
        
        assert isinstance(processor, StreamProcessor)
        assert processor.chat_orchestrator is not None
        assert processor.metrics is not None
    
    @pytest.mark.asyncio
    async def test_websocket_health_endpoint(self):
        """Test the WebSocket health endpoint."""
        health_response = await websocket_health_check()
        
        assert "status" in health_response
        assert "websocket_gateway" in health_response
        assert "stream_processor" in health_response
        assert "timestamp" in health_response
        
        # Check gateway status
        gateway_status = health_response["websocket_gateway"]
        assert "status" in gateway_status
        assert "connections" in gateway_status
        assert "authenticated_users" in gateway_status
        
        # Check processor status
        processor_status = health_response["stream_processor"]
        assert "status" in processor_status
        assert "active_streams" in processor_status
        assert "success_rate" in processor_status
    
    def test_websocket_gateway_stats(self):
        """Test WebSocket gateway statistics."""
        gateway = get_websocket_gateway()
        stats = gateway.get_connection_stats()
        
        assert "total_connections" in stats
        assert "authenticated_connections" in stats
        assert "unique_users" in stats
        assert "active_conversations" in stats
        assert "typing_users" in stats
        assert "online_users" in stats
        assert "queue_stats" in stats
        
        # All should be zero initially
        assert stats["total_connections"] == 0
        assert stats["authenticated_connections"] == 0
        assert stats["unique_users"] == 0
    
    def test_stream_processor_metrics(self):
        """Test stream processor metrics."""
        processor = get_stream_processor()
        metrics = processor.get_performance_metrics()
        
        assert "total_streams" in metrics
        assert "successful_streams" in metrics
        assert "failed_streams" in metrics
        assert "success_rate" in metrics
        assert "avg_stream_duration" in metrics
        assert "avg_processing_time" in metrics
        
        # All should be zero initially
        assert metrics["total_streams"] == 0
        assert metrics["successful_streams"] == 0
        assert metrics["failed_streams"] == 0
    
    def test_singleton_behavior(self):
        """Test that gateway and processor are singletons."""
        gateway1 = get_websocket_gateway()
        gateway2 = get_websocket_gateway()
        
        processor1 = get_stream_processor()
        processor2 = get_stream_processor()
        
        # Should be the same instances
        assert gateway1 is gateway2
        assert processor1 is processor2
    
    @pytest.mark.asyncio
    async def test_websocket_gateway_cleanup(self):
        """Test WebSocket gateway cleanup."""
        gateway = get_websocket_gateway()
        
        # Should not raise any exceptions
        await gateway.cleanup()
    
    @pytest.mark.asyncio
    async def test_stream_processor_cleanup(self):
        """Test stream processor cleanup."""
        processor = get_stream_processor()
        
        # Should not raise any exceptions
        await processor.cleanup()
    
    @pytest.mark.asyncio
    async def test_collaboration_presence_indicators(self):
        """Test collaboration presence indicators."""
        from ai_karen_engine.chat.websocket_gateway import PresenceManager
        
        presence_manager = PresenceManager()
        
        # Test presence update
        await presence_manager.update_presence(
            user_id="user123",
            status="online",
            conversation_id="conv456",
            metadata={"username": "testuser"}
        )
        
        # Verify presence data
        presence = presence_manager.get_presence("user123")
        assert presence is not None
        assert presence.status == "online"
        assert presence.user_id == "user123"
        
        # Test online users
        online_users = presence_manager.get_online_users("conv456")
        assert len(online_users) == 1
        assert online_users[0].user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_collaboration_typing_indicators(self):
        """Test collaboration typing indicators."""
        from ai_karen_engine.chat.websocket_gateway import TypingManager
        
        typing_manager = TypingManager()
        
        # Test typing start
        await typing_manager.set_typing(
            user_id="user123",
            conversation_id="conv456",
            is_typing=True,
            expires_in_seconds=5
        )
        
        # Verify typing users
        typing_users = typing_manager.get_typing_users("conv456")
        assert len(typing_users) == 1
        assert typing_users[0] == "user123"
        
        # Test typing stop
        await typing_manager.set_typing(
            user_id="user123",
            conversation_id="conv456",
            is_typing=False
        )
        
        typing_users = typing_manager.get_typing_users("conv456")
        assert len(typing_users) == 0
    
    @pytest.mark.asyncio
    async def test_collaboration_session_management(self):
        """Test collaboration session management."""
        from ai_karen_engine.chat.websocket_gateway import CollaborationManager
        
        collaboration_manager = CollaborationManager()
        
        # Test session creation
        session_id = await collaboration_manager.create_session(
            conversation_id="conv456",
            initiator_user_id="user123",
            session_type="chat",
            metadata={"initiator_username": "testuser"}
        )
        
        assert session_id is not None
        
        # Verify session exists
        session = collaboration_manager.get_session(session_id)
        assert session is not None
        assert session.conversation_id == "conv456"
        assert len(session.participants) == 1
        assert session.participants[0].user_id == "user123"
        
        # Test joining session
        success = await collaboration_manager.join_session(
            session_id=session_id,
            user_id="user456",
            username="testuser2"
        )
        
        assert success is True
        
        # Verify participant added
        session = collaboration_manager.get_session(session_id)
        assert len(session.participants) == 2
        
        # Test leaving session
        success = await collaboration_manager.leave_session(
            session_id=session_id,
            user_id="user456"
        )
        
        assert success is True
        
        # Verify participant removed
        session = collaboration_manager.get_session(session_id)
        assert len(session.participants) == 1
        
        # Test ending session
        success = await collaboration_manager.end_session(session_id)
        assert success is True
        
        # Verify session removed
        session = collaboration_manager.get_session(session_id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_collaboration_event_bus_integration(self):
        """Test collaboration features integration with EventBus."""
        from ai_karen_engine.event_bus import get_event_bus
        
        event_bus = get_event_bus()
        
        # Test presence update event
        event_id = event_bus.publish_presence_update(
            user_id="user123",
            status="online",
            conversation_id="conv456",
            metadata={"username": "testuser"}
        )
        
        assert event_id is not None
        
        # Test typing indicator event
        event_id = event_bus.publish_typing_indicator(
            user_id="user123",
            conversation_id="conv456",
            is_typing=True,
            expires_in_seconds=5
        )
        
        assert event_id is not None
        
        # Test collaboration session event
        event_id = event_bus.publish_collaboration_session(
            session_id="session123",
            action="start",
            participants=["user123", "user456"],
            conversation_id="conv456",
            session_type="chat"
        )
        
        assert event_id is not None
        
        # Verify presence tracking
        presence = event_bus.get_user_presence("user123")
        assert presence is not None
        assert presence["status"] == "online"
        
        # Verify online users
        online_users = event_bus.get_online_users("conv456")
        assert "user123" in online_users
        
        # Verify typing users
        typing_users = event_bus.get_typing_users("conv456")
        assert "user123" in typing_users
    
    @pytest.mark.asyncio
    async def test_collaboration_analytics_integration(self):
        """Test collaboration analytics integration."""
        from extensions_hub.analytics.dashboard.analytics_extension import AnalyticsDashboardExtension
        
        analytics = AnalyticsDashboardExtension()
        
        # Test collaboration session tracking
        result = await analytics._track_collaboration_session(
            context={
                'session': {
                    'session_id': 'session123',
                    'conversation_id': 'conv456',
                    'session_type': 'chat',
                    'participants': ['user123', 'user456']
                },
                'action': 'start'
            },
            user_context={'userId': 'user123'}
        )
        
        assert result['success'] is True
        assert result['collaboration_tracked'] is True
        
        # Test presence update tracking
        result = await analytics._track_presence_update(
            context={
                'presence': {
                    'status': 'online',
                    'user_id': 'user123'
                }
            },
            user_context={'user_type': 'regular'}
        )
        
        assert result['success'] is True
        assert result['presence_tracked'] is True
        
        # Test typing indicator tracking
        result = await analytics._track_typing_indicator(
            context={
                'typing': {
                    'is_typing': True,
                    'conversation_id': 'conv456'
                }
            },
            user_context={'userId': 'user123'}
        )
        
        assert result['success'] is True
        assert result['typing_tracked'] is True
        
        # Test collaborative edit tracking
        result = await analytics._track_collaborative_edit(
            context={
                'edit': {
                    'session_type': 'chat',
                    'edit_type': 'text'
                }
            },
            user_context={'userId': 'user123'}
        )
        
        assert result['success'] is True
        assert result['collaborative_edit_tracked'] is True
        
        # Test WebSocket connection tracking
        result = await analytics._track_websocket_connection(
            context={
                'connection': {
                    'authenticated': True,
                    'conversation_id': 'conv456'
                },
                'action': 'connect'
            },
            user_context={'userId': 'user123'}
        )
        
        assert result['success'] is True
        assert result['websocket_tracked'] is True
        
        # Test collaboration analytics data retrieval
        collaboration_data = await analytics.get_collaboration_analytics(
            timeframe='24h',
            conversation_id='conv456'
        )
        
        assert isinstance(collaboration_data, dict)
        assert 'active_sessions' in collaboration_data
        assert 'total_participants' in collaboration_data
        assert 'presence_status' in collaboration_data
        assert 'typing_activity' in collaboration_data


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])