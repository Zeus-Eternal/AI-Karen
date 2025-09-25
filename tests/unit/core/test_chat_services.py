"""
Comprehensive unit tests for chat-related services in the web UI integration.
Tests the AI Orchestrator, Conversation Service, Memory Service, and dispatch functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

# Import the services we're testing
from ai_karen_engine.core.cortex.dispatch import dispatch
from ai_karen_engine.core.memory.manager import recall_context, update_memory


class TestChatDispatch:
    """Test the core chat dispatch functionality."""
    
    @pytest.fixture
    def user_context(self):
        """Standard user context for testing."""
        return {
            "user_id": "test-user-123",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    @pytest.mark.asyncio
    async def test_dispatch_basic_greeting(self, user_context):
        """Test basic greeting dispatch."""
        result = await dispatch(user_context, "hello")
        
        assert result is not None
        assert "intent" in result
        assert "result" in result
        assert result["intent"] in ["greet", "hf_generate"]
    
    @pytest.mark.asyncio
    async def test_dispatch_with_memory_enabled(self, user_context):
        """Test dispatch with memory context enabled."""
        result = await dispatch(
            user_context, 
            "What did we talk about before?",
            memory_enabled=True
        )
        
        assert result is not None
        assert "trace" in result
        # Check that memory recall was attempted
        memory_stages = [t for t in result["trace"] if t.get("stage") == "memory_recalled"]
        assert len(memory_stages) > 0
    
    @pytest.mark.asyncio
    async def test_dispatch_with_plugins_disabled(self, user_context):
        """Test dispatch with plugins disabled."""
        result = await dispatch(
            user_context,
            "get weather",
            plugin_enabled=False
        )
        
        assert result is not None
        # Should not execute plugins even if intent matches
        plugin_stages = [t for t in result.get("trace", []) if t.get("stage") == "plugin_executed"]
        assert len(plugin_stages) == 0
    
    @pytest.mark.asyncio
    async def test_dispatch_error_handling(self, user_context):
        """Test dispatch error handling."""
        with patch('ai_karen_engine.core.cortex.intent.resolve_intent') as mock_intent:
            mock_intent.side_effect = Exception("Intent resolution failed")
            
            with pytest.raises(Exception):
                await dispatch(user_context, "test query")
    
    @pytest.mark.asyncio
    async def test_dispatch_trace_logging(self, user_context):
        """Test that dispatch properly logs trace information."""
        trace = []
        result = await dispatch(
            user_context,
            "hello world",
            trace=trace
        )
        
        assert len(trace) > 0
        assert any(t.get("stage") == "intent_resolved" for t in trace)


class TestMemoryIntegration:
    """Test memory integration for chat functionality."""
    
    @pytest.fixture
    def user_context(self):
        return {
            "user_id": "test-user-123",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    def test_recall_context_basic(self, user_context):
        """Test basic context recall."""
        # Mock the memory recall to return some test data
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.return_value = [
                {"content": "Previous conversation about weather", "timestamp": datetime.now()},
                {"content": "User likes coffee", "timestamp": datetime.now()}
            ]
            
            context = recall_context(user_context, "tell me about weather", limit=5)
            
            assert context is not None
            assert len(context) == 2
            mock_recall.assert_called_once()
    
    def test_update_memory_success(self, user_context):
        """Test successful memory update."""
        with patch('ai_karen_engine.core.memory.manager.update_memory') as mock_update:
            mock_update.return_value = True
            
            result = update_memory(
                user_context,
                "I like pizza",
                {"response": "Noted that you like pizza"},
                tenant_id="test-tenant"
            )
            
            assert result is True
            mock_update.assert_called_once()
    
    def test_memory_with_tenant_isolation(self, user_context):
        """Test that memory operations respect tenant isolation."""
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.return_value = []
            
            recall_context(user_context, "test query", tenant_id="test-tenant")
            
            # Verify tenant_id was passed correctly
            call_args = mock_recall.call_args
            assert "test-tenant" in str(call_args)


class TestChatEndpoint:
    """Test the main chat endpoint functionality."""
    
    @pytest.fixture
    def mock_auth_context(self):
        """Mock authentication context."""
        return {
            "sub": "test-user-123",
            "roles": ["user"],
            "tenant_id": "test-tenant"
        }
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self, mock_auth_context):
        """Test successful chat endpoint call."""
        with patch('ai_karen_engine.core.cortex.dispatch.dispatch') as mock_dispatch:
            mock_dispatch.return_value = {
                "intent": "greet",
                "confidence": 0.9,
                "result": {"response": "Hello! How can I help you?"}
            }
            
            # Simulate the main chat endpoint logic
            user_ctx = {
                "user_id": mock_auth_context["sub"],
                "roles": mock_auth_context["roles"],
                "tenant_id": mock_auth_context["tenant_id"]
            }
            
            result = await dispatch(user_ctx, "hello", role="user")
            
            assert result["intent"] == "greet"
            assert result["confidence"] == 0.9
            mock_dispatch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_error_handling(self, mock_auth_context):
        """Test chat endpoint error handling."""
        with patch('ai_karen_engine.core.cortex.dispatch.dispatch') as mock_dispatch:
            mock_dispatch.side_effect = Exception("Service unavailable")
            
            user_ctx = {
                "user_id": mock_auth_context["sub"],
                "roles": mock_auth_context["roles"],
                "tenant_id": mock_auth_context["tenant_id"]
            }
            
            with pytest.raises(Exception):
                await dispatch(user_ctx, "hello", role="user")


class TestConversationFlow:
    """Test complete conversation flows."""
    
    @pytest.fixture
    def conversation_context(self):
        return {
            "user_id": "test-user-123",
            "session_id": "test-session-456",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, conversation_context):
        """Test multi-turn conversation handling."""
        # First message
        result1 = await dispatch(
            conversation_context,
            "Hello, I'm John",
            memory_enabled=True
        )
        
        assert result1 is not None
        
        # Second message referencing first
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.return_value = [
                {"content": "User said their name is John", "timestamp": datetime.now()}
            ]
            
            result2 = await dispatch(
                conversation_context,
                "What's my name?",
                memory_enabled=True
            )
            
            assert result2 is not None
            mock_recall.assert_called()
    
    @pytest.mark.asyncio
    async def test_conversation_with_context_building(self, conversation_context):
        """Test conversation with proper context building."""
        conversation_history = [
            {"role": "user", "content": "I like coffee"},
            {"role": "assistant", "content": "I'll remember that you like coffee"},
            {"role": "user", "content": "What do I like to drink?"}
        ]
        
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.return_value = [
                {"content": "User likes coffee", "timestamp": datetime.now()}
            ]
            
            result = await dispatch(
                conversation_context,
                "What do I like to drink?",
                context={"conversation_history": conversation_history},
                memory_enabled=True
            )
            
            assert result is not None
            assert "trace" in result


class TestPluginIntegration:
    """Test plugin integration in chat flows."""
    
    @pytest.fixture
    def user_context(self):
        return {
            "user_id": "test-user-123",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    @pytest.mark.asyncio
    async def test_plugin_execution_in_chat(self, user_context):
        """Test plugin execution within chat flow."""
        with patch('ai_karen_engine.plugins.manager.get_plugin_manager') as mock_manager:
            mock_plugin_manager = Mock()
            mock_plugin_manager.run_plugin = AsyncMock(return_value=(
                {"result": "Weather is sunny"}, "stdout", ""
            ))
            mock_manager.return_value = mock_plugin_manager
            
            with patch('ai_karen_engine.core.plugin_registry.plugin_registry') as mock_registry:
                mock_registry.__contains__ = Mock(return_value=True)
                mock_registry.get = Mock(return_value="weather_plugin")
                
                with patch('ai_karen_engine.core.cortex.intent.resolve_intent') as mock_intent:
                    mock_intent.return_value = ("weather", {"confidence": 0.9})
                    
                    result = await dispatch(
                        user_context,
                        "What's the weather?",
                        plugin_enabled=True
                    )
                    
                    assert result is not None
                    plugin_stages = [t for t in result.get("trace", []) if t.get("stage") == "plugin_executed"]
                    assert len(plugin_stages) > 0
    
    @pytest.mark.asyncio
    async def test_plugin_error_handling(self, user_context):
        """Test plugin error handling in chat."""
        with patch('ai_karen_engine.plugins.manager.get_plugin_manager') as mock_manager:
            mock_plugin_manager = Mock()
            mock_plugin_manager.run_plugin = AsyncMock(side_effect=Exception("Plugin failed"))
            mock_manager.return_value = mock_plugin_manager
            
            with patch('ai_karen_engine.core.plugin_registry.plugin_registry') as mock_registry:
                mock_registry.__contains__ = Mock(return_value=True)
                mock_registry.get = Mock(return_value="failing_plugin")
                
                with patch('ai_karen_engine.core.cortex.intent.resolve_intent') as mock_intent:
                    mock_intent.return_value = ("failing_plugin", {"confidence": 0.9})
                    
                    result = await dispatch(
                        user_context,
                        "Run failing plugin",
                        plugin_enabled=True
                    )
                    
                    # Should handle plugin errors gracefully
                    assert result is not None
                    error_stages = [t for t in result.get("trace", []) if t.get("stage") == "plugin_error"]
                    assert len(error_stages) > 0


class TestPerformanceAndScaling:
    """Test performance and scaling aspects of chat services."""
    
    @pytest.fixture
    def user_context(self):
        return {
            "user_id": "test-user-123",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    @pytest.mark.asyncio
    async def test_concurrent_chat_requests(self, user_context):
        """Test handling multiple concurrent chat requests."""
        async def single_request():
            return await dispatch(user_context, "hello")
        
        # Run 10 concurrent requests
        tasks = [single_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 10
    
    @pytest.mark.asyncio
    async def test_memory_performance_with_large_context(self, user_context):
        """Test memory performance with large conversation context."""
        # Simulate large conversation history
        large_context = [
            {"content": f"Message {i}", "timestamp": datetime.now()}
            for i in range(100)
        ]
        
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.return_value = large_context
            
            start_time = asyncio.get_event_loop().time()
            result = await dispatch(
                user_context,
                "What did we discuss?",
                memory_enabled=True
            )
            end_time = asyncio.get_event_loop().time()
            
            # Should complete within reasonable time (2 seconds)
            assert (end_time - start_time) < 2.0
            assert result is not None


class TestErrorRecovery:
    """Test error recovery and resilience in chat services."""
    
    @pytest.fixture
    def user_context(self):
        return {
            "user_id": "test-user-123",
            "tenant_id": "test-tenant",
            "roles": ["user"]
        }
    
    @pytest.mark.asyncio
    async def test_memory_service_failure_recovery(self, user_context):
        """Test recovery when memory service fails."""
        with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
            mock_recall.side_effect = Exception("Memory service unavailable")
            
            # Should still process the request without memory
            result = await dispatch(
                user_context,
                "hello",
                memory_enabled=True
            )
            
            assert result is not None
            # Should have error in trace but still return result
            error_stages = [t for t in result.get("trace", []) if "error" in t.get("stage", "")]
            assert len(error_stages) > 0
    
    @pytest.mark.asyncio
    async def test_intent_resolution_fallback(self, user_context):
        """Test fallback when intent resolution fails."""
        with patch('ai_karen_engine.core.cortex.intent.resolve_intent') as mock_intent:
            mock_intent.side_effect = Exception("Intent service down")
            
            # Should raise CortexDispatchError but handle gracefully
            with pytest.raises(Exception):
                await dispatch(user_context, "test query")
    
    @pytest.mark.asyncio
    async def test_partial_service_degradation(self, user_context):
        """Test behavior when some services are degraded."""
        # Memory works, plugins fail
        with patch('ai_karen_engine.plugins.manager.get_plugin_manager') as mock_manager:
            mock_plugin_manager = Mock()
            mock_plugin_manager.run_plugin = AsyncMock(side_effect=Exception("Plugin service down"))
            mock_manager.return_value = mock_plugin_manager
            
            with patch('ai_karen_engine.core.memory.manager.recall_context') as mock_recall:
                mock_recall.return_value = [{"content": "Previous context", "timestamp": datetime.now()}]
                
                result = await dispatch(
                    user_context,
                    "get weather",  # Would normally trigger plugin
                    memory_enabled=True,
                    plugin_enabled=True
                )
                
                # Should fall back to memory/predictor mode
                assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])