"""
Integration test for chat hook functionality.

This test verifies that the hook system works correctly with the ChatOrchestrator
in a real integration scenario.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator, ChatRequest
from ai_karen_engine.hooks import get_hook_manager, HookTypes, HookContext


class TestChatHookIntegration:
    """Integration tests for chat hook functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_hook_integration(self):
        """Test basic hook integration with ChatOrchestrator."""
        # Get hook manager
        hook_manager = get_hook_manager()
        
        # Clear any existing hooks
        await hook_manager.clear_hooks_by_source("test")
        
        # Register a test hook
        hook_results = []
        
        async def test_pre_message_hook(context: HookContext):
            hook_results.append({
                "hook_type": context.hook_type,
                "message": context.data.get("message"),
                "user_id": context.data.get("user_id")
            })
            return {"status": "executed", "hook_type": context.hook_type}
        
        hook_id = await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=test_pre_message_hook,
            priority=100,
            source_type="test",
            source_name="integration_test"
        )
        
        try:
            # Create ChatOrchestrator
            chat_orchestrator = ChatOrchestrator()
            
            # Create test request
            request = ChatRequest(
                message="Hello, test message!",
                user_id="test_user_123",
                conversation_id="test_conv_456",
                session_id="test_session_789",
                stream=False,
                include_context=False,
                attachments=[],
                metadata={"test": True}
            )
            
            # Mock the processing pipeline to avoid dependencies
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Test response from ChatOrchestrator",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                from ai_karen_engine.chat.chat_orchestrator import ProcessingContext
                response = await chat_orchestrator._process_traditional(request, ProcessingContext())
                
                # Verify the response
                assert response.response == "Test response from ChatOrchestrator"
                assert response.used_fallback is False
                
                # Verify hook was executed
                assert len(hook_results) >= 1
                
                # Check hook execution details
                pre_message_result = next(
                    (r for r in hook_results if r["hook_type"] == HookTypes.PRE_MESSAGE), 
                    None
                )
                assert pre_message_result is not None
                assert pre_message_result["message"] == "Hello, test message!"
                assert pre_message_result["user_id"] == "test_user_123"
                
                # Verify hook execution metadata in response
                assert "pre_hooks_executed" in response.metadata
                assert response.metadata["pre_hooks_executed"] >= 1
                
        finally:
            # Clean up
            await hook_manager.unregister_hook(hook_id)
    
    @pytest.mark.asyncio
    async def test_multiple_hooks_execution_order(self):
        """Test that multiple hooks execute in priority order."""
        hook_manager = get_hook_manager()
        
        # Clear any existing hooks
        await hook_manager.clear_hooks_by_source("test")
        
        execution_order = []
        
        async def high_priority_hook(context: HookContext):
            execution_order.append("high_priority")
            return {"priority": "high"}
        
        async def low_priority_hook(context: HookContext):
            execution_order.append("low_priority")
            return {"priority": "low"}
        
        async def medium_priority_hook(context: HookContext):
            execution_order.append("medium_priority")
            return {"priority": "medium"}
        
        # Register hooks with different priorities (lower number = higher priority)
        hook_ids = []
        hook_ids.append(await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=low_priority_hook,
            priority=200,  # Low priority
            source_type="test"
        ))
        
        hook_ids.append(await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=high_priority_hook,
            priority=50,   # High priority
            source_type="test"
        ))
        
        hook_ids.append(await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=medium_priority_hook,
            priority=100,  # Medium priority
            source_type="test"
        ))
        
        try:
            # Create ChatOrchestrator
            chat_orchestrator = ChatOrchestrator()
            
            # Create test request
            request = ChatRequest(
                message="Priority test message",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=False
            )
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Priority test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                from ai_karen_engine.chat.chat_orchestrator import ProcessingContext
                response = await chat_orchestrator._process_traditional(request, ProcessingContext())
                
                # Verify hooks executed in priority order
                assert len(execution_order) == 3
                assert execution_order == ["high_priority", "medium_priority", "low_priority"]
                
                # Verify response metadata
                assert response.metadata["pre_hooks_executed"] == 3
                
        finally:
            # Clean up
            for hook_id in hook_ids:
                await hook_manager.unregister_hook(hook_id)
    
    @pytest.mark.asyncio
    async def test_hook_failure_resilience(self):
        """Test that hook failures don't break message processing."""
        hook_manager = get_hook_manager()
        
        # Clear any existing hooks
        await hook_manager.clear_hooks_by_source("test")
        
        async def failing_hook(context: HookContext):
            raise ValueError("Test hook failure")
        
        async def successful_hook(context: HookContext):
            return {"status": "success"}
        
        # Register both hooks
        hook_ids = []
        hook_ids.append(await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=failing_hook,
            priority=50,
            source_type="test"
        ))
        
        hook_ids.append(await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=successful_hook,
            priority=100,
            source_type="test"
        ))
        
        try:
            # Create ChatOrchestrator
            chat_orchestrator = ChatOrchestrator()
            
            # Create test request
            request = ChatRequest(
                message="Failure resilience test",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=False
            )
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Resilience test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message - should not raise exception
                from ai_karen_engine.chat.chat_orchestrator import ProcessingContext
                response = await chat_orchestrator._process_traditional(request, ProcessingContext())
                
                # Verify processing succeeded despite hook failure
                assert response.response == "Resilience test response"
                assert response.used_fallback is False
                
                # Verify that at least the successful hook executed
                # (The exact count depends on error handling implementation)
                assert "pre_hooks_executed" in response.metadata
                
        finally:
            # Clean up
            for hook_id in hook_ids:
                await hook_manager.unregister_hook(hook_id)
    
    @pytest.mark.asyncio
    async def test_hook_context_data_completeness(self):
        """Test that hook context contains all expected data."""
        hook_manager = get_hook_manager()
        
        # Clear any existing hooks
        await hook_manager.clear_hooks_by_source("test")
        
        captured_context = None
        
        async def context_capture_hook(context: HookContext):
            nonlocal captured_context
            captured_context = context
            return {"captured": True}
        
        hook_id = await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=context_capture_hook,
            source_type="test"
        )
        
        try:
            # Create ChatOrchestrator
            chat_orchestrator = ChatOrchestrator()
            
            # Create test request with comprehensive data
            request = ChatRequest(
                message="Context completeness test message",
                user_id="context_test_user",
                conversation_id="context_test_conv",
                session_id="context_test_session",
                stream=False,
                include_context=True,
                attachments=["file1.txt", "file2.pdf"],
                metadata={"test_key": "test_value", "priority": "high"}
            )
            
            # Mock the processing pipeline
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="Context test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process the message
                from ai_karen_engine.chat.chat_orchestrator import ProcessingContext
                response = await chat_orchestrator._process_traditional(request, ProcessingContext())
                
                # Verify context was captured
                assert captured_context is not None
                assert captured_context.hook_type == HookTypes.PRE_MESSAGE
                
                # Verify data completeness
                data = captured_context.data
                assert data["message"] == "Context completeness test message"
                assert data["user_id"] == "context_test_user"
                assert data["conversation_id"] == "context_test_conv"
                assert data["session_id"] == "context_test_session"
                assert "timestamp" in data
                assert "correlation_id" in data
                assert data["attachments"] == ["file1.txt", "file2.pdf"]
                assert data["metadata"]["test_key"] == "test_value"
                assert data["metadata"]["priority"] == "high"
                
                # Verify user context
                user_context = captured_context.user_context
                assert user_context["user_id"] == "context_test_user"
                assert user_context["conversation_id"] == "context_test_conv"
                assert user_context["session_id"] == "context_test_session"
                
        finally:
            # Clean up
            await hook_manager.unregister_hook(hook_id)
    
    @pytest.mark.asyncio
    async def test_hook_manager_state_management(self):
        """Test hook manager state management during chat processing."""
        hook_manager = get_hook_manager()
        
        # Verify initial state
        initial_summary = hook_manager.get_summary()
        initial_hook_count = initial_summary["total_hooks"]
        
        # Register a test hook
        async def state_test_hook(context: HookContext):
            return {"state": "managed"}
        
        hook_id = await hook_manager.register_hook(
            hook_type=HookTypes.PRE_MESSAGE,
            handler=state_test_hook,
            source_type="test"
        )
        
        try:
            # Verify hook was registered
            updated_summary = hook_manager.get_summary()
            assert updated_summary["total_hooks"] == initial_hook_count + 1
            
            # Verify hook can be retrieved
            hook_registration = hook_manager.get_hook_by_id(hook_id)
            assert hook_registration is not None
            assert hook_registration.hook_type == HookTypes.PRE_MESSAGE
            assert hook_registration.source_type == "test"
            
            # Test hook execution through ChatOrchestrator
            chat_orchestrator = ChatOrchestrator()
            request = ChatRequest(
                message="State management test",
                user_id="state_user",
                conversation_id="state_conv",
                stream=False,
                include_context=False
            )
            
            with patch.object(chat_orchestrator, '_process_with_retry') as mock_process:
                mock_process.return_value = MagicMock(
                    success=True,
                    response="State test response",
                    parsed_message=None,
                    embeddings=None,
                    context=None,
                    used_fallback=False
                )
                
                # Process message
                from ai_karen_engine.chat.chat_orchestrator import ProcessingContext
                response = await chat_orchestrator._process_traditional(request, ProcessingContext())
                
                # Verify hook executed
                assert response.metadata["pre_hooks_executed"] >= 1
            
            # Verify hook manager state is still consistent
            final_summary = hook_manager.get_summary()
            assert final_summary["total_hooks"] == initial_hook_count + 1
            
        finally:
            # Clean up and verify cleanup
            success = await hook_manager.unregister_hook(hook_id)
            assert success is True
            
            cleanup_summary = hook_manager.get_summary()
            assert cleanup_summary["total_hooks"] == initial_hook_count