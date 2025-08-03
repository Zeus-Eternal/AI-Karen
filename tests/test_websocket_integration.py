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


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])