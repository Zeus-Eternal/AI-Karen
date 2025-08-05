"""
Tests for ChatOrchestrator hook integration.

This module tests the hook capabilities added to the ChatOrchestrator,
ensuring that hooks are properly triggered during message processing.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator, ChatRequest, ChatResponse, ProcessingContext
)
from ai_karen_engine.hooks import HookManager, HookTypes, HookContext, HookResult
from ai_karen_engine.hooks.models import HookExecutionSummary


class TestChatOrchestratorHooks:
    """Test hook integration in ChatOrchestrator."""
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create a mock hook manager."""
        hook_manager = MagicMock(spec=HookManager)
        hook_manager.trigger_hooks = AsyncMock()
        return hook_manager
    
    @pytest.fixture
    def chat_orchestrator(self):
        """Create a ChatOrchestrator instance for testing."""
        return ChatOrchestrator()
    
    @pytest.fixture
    def sample_chat_request(self):
        """Create a sample chat request."""
        return ChatRequest(
            message="Hello, how are you?",
            user_id="test_user_123",
            conversation_id="conv_456",
            session_id="session_789",
            stream=False,
            include_context=True,
            attachments=[],
            metadata={"test": "data"}
        )
    
    @pytest.fixture
    def mock_hook_summary(self):
        """Create a mock hook execution summary."""
        return HookExecutionSummary(
            hook_type=HookTypes.PRE_MESSAGE,
            total_hooks=2,
            successful_hooks=2,
            failed_hooks=0,
            total_execution_time_ms=50.0,
            results=[
                HookResult.success_result("hook_1", {"result": "success"}, 25.0),
                HookResult.success_result("hook_2", {"result": "success"}, 25.0)
            ]
        )
    
    @pytest.mark.asyncio
    async def test_pre_message_hooks_triggered(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that pre-message hooks are triggered during processing."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline to avoid dependencies
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify pre-message hooks were triggered
                assert mock_hook_manager.trigger_hooks.call_count >= 1
                
                # Check the first call (pre-message hooks)
                first_call = mock_hook_manager.trigger_hooks.call_args_list[0]
                hook_context = first_call[0][0]
                
                assert isinstance(hook_context, HookContext)
                assert hook_context.hook_type == HookTypes.PRE_MESSAGE
                assert hook_context.data["message"] == sample_chat_request.message
                assert hook_context.data["user_id"] == sample_chat_request.user_id
                assert hook_context.data["conversation_id"] == sample_chat_request.conversation_id
                assert hook_context.user_context["user_id"] == sample_chat_request.user_id
    
    @pytest.mark.asyncio
    async def test_post_message_hooks_triggered(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that post-message hooks are triggered after successful processing."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify multiple hook types were triggered
                assert mock_hook_manager.trigger_hooks.call_count >= 3
                
                # Check that POST_MESSAGE hooks were triggered
                hook_types_called = [
                    call[0][0].hook_type for call in mock_hook_manager.trigger_hooks.call_args_list
                ]
                assert HookTypes.PRE_MESSAGE in hook_types_called
                assert HookTypes.MESSAGE_PROCESSED in hook_types_called
                assert HookTypes.POST_MESSAGE in hook_types_called
    
    @pytest.mark.asyncio
    async def test_message_failed_hooks_triggered(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that message failed hooks are triggered on processing failure."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline to fail
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=False,
                    response=None,
                    error="Processing failed",
                    error_type=None,
                    used_fallback=True
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify hooks were triggered
                assert mock_hook_manager.trigger_hooks.call_count >= 2
                
                # Check that MESSAGE_FAILED hooks were triggered
                hook_types_called = [
                    call[0][0].hook_type for call in mock_hook_manager.trigger_hooks.call_args_list
                ]
                assert HookTypes.PRE_MESSAGE in hook_types_called
                assert HookTypes.MESSAGE_FAILED in hook_types_called
    
    @pytest.mark.asyncio
    async def test_streaming_hooks_triggered(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that hooks are triggered during streaming processing."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test streaming response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the streaming message
                stream_request = ChatRequest(**{
                    **sample_chat_request.dict(),
                    "stream": True
                })
                
                chunks = []
                async for chunk in chat_orchestrator._process_streaming(
                    stream_request,
                    ProcessingContext()
                ):
                    chunks.append(chunk)
                
                # Verify pre-message hooks were triggered for streaming
                assert mock_hook_manager.trigger_hooks.call_count >= 1
                
                # Check the first call includes streaming flag
                first_call = mock_hook_manager.trigger_hooks.call_args_list[0]
                hook_context = first_call[0][0]
                
                assert hook_context.hook_type == HookTypes.PRE_MESSAGE
                assert hook_context.data["streaming"] is True
                
                # Verify metadata chunk includes hook information
                metadata_chunks = [chunk for chunk in chunks if chunk.type == "metadata"]
                assert len(metadata_chunks) > 0
                assert "pre_hooks_executed" in metadata_chunks[0].metadata
    
    @pytest.mark.asyncio
    async def test_hook_context_data_structure(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that hook context contains the expected data structure."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=MagicMock(entities=[("test", "ENTITY")]),
                    embeddings=[0.1, 0.2, 0.3],
                    context={"memories": [], "context_summary": "Test context"},
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify hook context structure for pre-message hooks
                pre_message_call = mock_hook_manager.trigger_hooks.call_args_list[0]
                pre_context = pre_message_call[0][0]
                
                expected_data_keys = [
                    "message", "user_id", "conversation_id", "session_id",
                    "timestamp", "correlation_id", "attachments", "metadata"
                ]
                for key in expected_data_keys:
                    assert key in pre_context.data
                
                expected_user_context_keys = [
                    "user_id", "conversation_id", "session_id"
                ]
                for key in expected_user_context_keys:
                    assert key in pre_context.user_context
    
    @pytest.mark.asyncio
    async def test_hook_execution_metadata_in_response(self, chat_orchestrator, sample_chat_request, mock_hook_summary):
        """Test that hook execution information is included in the response metadata."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = mock_hook_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify hook execution metadata is in response
                assert isinstance(response, ChatResponse)
                assert "pre_hooks_executed" in response.metadata
                assert "processed_hooks_executed" in response.metadata
                assert "post_hooks_executed" in response.metadata
                assert "total_hooks_executed" in response.metadata
                
                # Verify the values are correct based on mock
                assert response.metadata["pre_hooks_executed"] == mock_hook_summary.successful_hooks
                assert response.metadata["processed_hooks_executed"] == mock_hook_summary.successful_hooks
                assert response.metadata["post_hooks_executed"] == mock_hook_summary.successful_hooks
    
    @pytest.mark.asyncio
    async def test_hook_failure_handling(self, chat_orchestrator, sample_chat_request):
        """Test that hook failures don't break message processing."""
        failed_summary = HookExecutionSummary(
            hook_type=HookTypes.PRE_MESSAGE,
            total_hooks=2,
            successful_hooks=1,
            failed_hooks=1,
            total_execution_time_ms=100.0,
            results=[
                HookResult.success_result("hook_1", {"result": "success"}, 50.0),
                HookResult.error_result("hook_2", "Hook failed", 50.0)
            ]
        )
        
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = failed_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify processing succeeded despite hook failures
                assert isinstance(response, ChatResponse)
                assert response.response == "Test response"
                
                # Verify hook failure information is recorded
                assert response.metadata["pre_hooks_executed"] == 1  # Only successful hooks
    
    @pytest.mark.asyncio
    async def test_hook_timeout_handling(self, chat_orchestrator, sample_chat_request):
        """Test that hook timeouts are handled gracefully."""
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            # Simulate timeout
            mock_hook_manager.trigger_hooks.side_effect = asyncio.TimeoutError("Hook timeout")
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message - should not raise exception
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify processing succeeded despite hook timeout
                assert isinstance(response, ChatResponse)
                assert response.response == "Test response"
    
    @pytest.mark.asyncio
    async def test_hook_disabled_scenario(self, chat_orchestrator, sample_chat_request):
        """Test behavior when hook manager is disabled."""
        disabled_summary = HookExecutionSummary(
            hook_type=HookTypes.PRE_MESSAGE,
            total_hooks=0,
            successful_hooks=0,
            failed_hooks=0,
            total_execution_time_ms=0.0,
            results=[]
        )
        
        with patch('ai_karen_engine.chat.chat_orchestrator.get_hook_manager') as mock_get_hook_manager:
            mock_hook_manager = AsyncMock()
            mock_hook_manager.trigger_hooks.return_value = disabled_summary
            mock_get_hook_manager.return_value = mock_hook_manager
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                response = await chat_orchestrator._process_traditional(
                    sample_chat_request,
                    ProcessingContext()
                )
                
                # Verify processing succeeded with no hooks executed
                assert isinstance(response, ChatResponse)
                assert response.response == "Test response"
                assert response.metadata["total_hooks_executed"] == 0