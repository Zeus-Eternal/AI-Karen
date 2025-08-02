"""
Comprehensive tests for ChatOrchestrator implementation.
Tests all requirements for task 2.1: Create ChatOrchestrator class with spaCy and DistilBERT integration.

Requirements being tested:
- Build message processing pipeline with spaCy parsing and DistilBERT embeddings
- Implement retry logic with exponential backoff for failed processing
- Add comprehensive error handling with graceful degradation
- Create request correlation and context management
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    RetryConfig,
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
    ErrorType
)
from ai_karen_engine.services.spacy_service import ParsedMessage


class TestChatOrchestrator:
    """Comprehensive tests for ChatOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create ChatOrchestrator instance with test configuration."""
        retry_config = RetryConfig(
            max_attempts=3,
            backoff_factor=2.0,
            initial_delay=0.1,  # Faster for tests
            max_delay=1.0,
            exponential_backoff=True
        )
        return ChatOrchestrator(
            retry_config=retry_config,
            timeout_seconds=5.0,
            enable_monitoring=True
        )

    @pytest.fixture
    def sample_request(self):
        """Create sample chat request."""
        return ChatRequest(
            message="Hello, how are you?",
            user_id="test_user_123",
            conversation_id="conv_456",
            session_id="session_789",
            stream=False,
            include_context=True,
            metadata={"test": "data"}
        )

    @pytest.fixture
    def mock_parsed_message(self):
        """Create mock parsed message from spaCy."""
        return ParsedMessage(
            tokens=["Hello", ",", "how", "are", "you", "?"],
            lemmas=["hello", ",", "how", "be", "you", "?"],
            entities=[("you", "PERSON")],
            pos_tags=[("Hello", "INTJ"), ("how", "ADV"), ("are", "AUX"), ("you", "PRON")],
            noun_phrases=["you"],
            sentences=["Hello, how are you?"],
            dependencies=[],
            language="en",
            processing_time=0.05,
            used_fallback=False
        )

    @pytest.mark.asyncio
    async def test_message_processing_pipeline_success(self, orchestrator, sample_request, mock_parsed_message):
        """Test successful message processing pipeline with spaCy and DistilBERT integration."""
        
        # Mock NLP service manager
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            # Setup mocks
            mock_nlp.parse_message = AsyncMock(return_value=mock_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3] * 256)  # 768-dim embedding
            
            # Mock AI response generation
            with patch.object(orchestrator, '_generate_ai_response', new_callable=AsyncMock) as mock_ai:
                mock_ai.return_value = "I'm doing well, thank you for asking!"
                
                # Process message
                response = await orchestrator.process_message(sample_request)
                
                # Verify response
                assert isinstance(response, ChatResponse)
                assert response.response == "I'm doing well, thank you for asking!"
                assert response.used_fallback is False
                assert response.context_used is True
                assert response.processing_time > 0
                assert len(response.correlation_id) > 0
                
                # Verify NLP services were called
                mock_nlp.parse_message.assert_called_once_with(sample_request.message)
                mock_nlp.get_embeddings.assert_called_once_with(sample_request.message)
                
                # Verify metadata includes NLP processing info
                assert "parsed_entities" in response.metadata
                assert "embedding_dimension" in response.metadata
                assert response.metadata["parsed_entities"] == 1
                assert response.metadata["embedding_dimension"] == 768

    @pytest.mark.asyncio
    async def test_retry_logic_with_exponential_backoff(self, orchestrator, sample_request):
        """Test retry logic with exponential backoff for failed processing."""
        
        retry_attempts = []
        
        async def failing_process(*args, **kwargs):
            retry_attempts.append(time.time())
            if len(retry_attempts) < 3:
                raise Exception("Temporary failure")
            return ProcessingResult(
                success=True,
                response="Success after retries",
                correlation_id="test_id"
            )
        
        with patch.object(orchestrator, '_process_message_internal', side_effect=failing_process):
            start_time = time.time()
            response = await orchestrator.process_message(sample_request)
            total_time = time.time() - start_time
            
            # Verify retries occurred
            assert len(retry_attempts) == 3
            assert response.response == "Success after retries"
            
            # Verify exponential backoff timing
            # First attempt: immediate
            # Second attempt: ~0.1s delay
            # Third attempt: ~0.2s delay
            # Total should be > 0.3s
            assert total_time > 0.3
            
            # Verify retry count in metadata
            assert response.metadata["retry_count"] == 2  # 0-indexed

    @pytest.mark.asyncio
    async def test_comprehensive_error_handling(self, orchestrator, sample_request):
        """Test comprehensive error handling with graceful degradation."""
        
        # Test different error types
        error_scenarios = [
            (Exception("spaCy parsing failed"), ErrorType.NLP_PARSING_ERROR),
            (Exception("Embedding generation failed"), ErrorType.EMBEDDING_ERROR),
            (asyncio.TimeoutError(), ErrorType.TIMEOUT_ERROR),
        ]
        
        for error, expected_error_type in error_scenarios:
            with patch.object(orchestrator, '_process_message_internal', side_effect=error):
                response = await orchestrator.process_message(sample_request)
                
                # Verify error response
                assert isinstance(response, ChatResponse)
                assert "error" in response.response.lower()
                assert response.used_fallback is True
                assert response.context_used is False
                
                # Verify error metadata
                if expected_error_type != ErrorType.TIMEOUT_ERROR:
                    assert "error" in response.metadata
                    assert "error_type" in response.metadata

    @pytest.mark.asyncio
    async def test_request_correlation_and_context_management(self, orchestrator, sample_request):
        """Test request correlation and context management."""
        
        # Track processing contexts
        contexts_created = []
        
        original_process = orchestrator._process_traditional
        
        async def track_context(request, context):
            contexts_created.append(context)
            return await original_process(request, context)
        
        with patch.object(orchestrator, '_process_traditional', side_effect=track_context):
            with patch.object(orchestrator, '_process_message_internal', new_callable=AsyncMock) as mock_internal:
                mock_internal.return_value = ProcessingResult(
                    success=True,
                    response="Test response",
                    correlation_id="test_correlation_id"
                )
                
                response = await orchestrator.process_message(sample_request)
                
                # Verify context was created and managed
                assert len(contexts_created) == 1
                context = contexts_created[0]
                
                assert isinstance(context, ProcessingContext)
                assert context.user_id == sample_request.user_id
                assert context.conversation_id == sample_request.conversation_id
                assert context.session_id == sample_request.session_id
                assert context.metadata == sample_request.metadata
                assert len(context.correlation_id) > 0
                assert isinstance(context.request_timestamp, datetime)
                
                # Verify correlation ID is consistent
                assert response.correlation_id == context.correlation_id

    @pytest.mark.asyncio
    async def test_streaming_response_processing(self, orchestrator, sample_request, mock_parsed_message):
        """Test streaming response processing."""
        
        # Enable streaming
        sample_request.stream = True
        
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=mock_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=[0.1] * 768)
            
            with patch.object(orchestrator, '_generate_ai_response', new_callable=AsyncMock) as mock_ai:
                mock_ai.return_value = "This is a streaming response"
                
                # Process streaming message
                stream_generator = await orchestrator.process_message(sample_request)
                
                # Collect all chunks
                chunks = []
                async for chunk in stream_generator:
                    chunks.append(chunk)
                
                # Verify streaming chunks
                assert len(chunks) > 0
                
                # First chunk should be metadata
                assert chunks[0].type == "metadata"
                assert chunks[0].metadata["status"] == "processing"
                
                # Content chunks
                content_chunks = [c for c in chunks if c.type == "content"]
                assert len(content_chunks) > 0
                
                # Last chunk should be completion
                assert chunks[-1].type == "complete"
                assert "processing_time" in chunks[-1].metadata
                
                # All chunks should have same correlation ID
                correlation_ids = {chunk.correlation_id for chunk in chunks}
                assert len(correlation_ids) == 1

    @pytest.mark.asyncio
    async def test_fallback_processing_when_nlp_fails(self, orchestrator, sample_request):
        """Test fallback processing when NLP services fail."""
        
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            # Mock spaCy to use fallback
            fallback_parsed = ParsedMessage(
                tokens=["Hello", "how", "are", "you"],
                lemmas=["Hello", "how", "are", "you"],  # No lemmatization in fallback
                entities=[],  # No entities in fallback
                pos_tags=[],  # No POS tags in fallback
                noun_phrases=[],  # No noun phrases in fallback
                sentences=["Hello how are you"],
                dependencies=[],
                language="en",
                processing_time=0.01,
                used_fallback=True
            )
            
            mock_nlp.parse_message = AsyncMock(return_value=fallback_parsed)
            mock_nlp.get_embeddings = AsyncMock(return_value=[0.1] * 768)
            
            with patch.object(orchestrator, '_generate_ai_response', new_callable=AsyncMock) as mock_ai:
                mock_ai.return_value = "Fallback response"
                
                response = await orchestrator.process_message(sample_request)
                
                # Verify fallback was used
                assert response.used_fallback is True
                assert response.metadata["parsed_entities"] == 0  # No entities in fallback

    @pytest.mark.asyncio
    async def test_timeout_handling(self, orchestrator, sample_request):
        """Test timeout handling in message processing."""
        
        # Set very short timeout
        orchestrator.timeout_seconds = 0.1
        
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(0.2)  # Longer than timeout
            return ProcessingResult(success=True, response="Should not reach here")
        
        with patch.object(orchestrator, '_process_message_internal', side_effect=slow_process):
            response = await orchestrator.process_message(sample_request)
            
            # Verify timeout error response
            assert "error" in response.response.lower()
            assert response.used_fallback is True
            assert "timeout" in response.metadata.get("error", "").lower()

    def test_processing_statistics(self, orchestrator):
        """Test processing statistics collection."""
        
        # Initial stats
        stats = orchestrator.get_processing_stats()
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 0
        assert stats["success_rate"] == 0.0
        
        # Simulate some processing
        orchestrator._total_requests = 10
        orchestrator._successful_requests = 8
        orchestrator._failed_requests = 2
        orchestrator._processing_times = [0.1, 0.2, 0.15, 0.3, 0.25]
        
        stats = orchestrator.get_processing_stats()
        assert stats["total_requests"] == 10
        assert stats["successful_requests"] == 8
        assert stats["failed_requests"] == 2
        assert stats["success_rate"] == 0.8
        assert stats["avg_processing_time"] == 0.2

    def test_active_contexts_tracking(self, orchestrator):
        """Test active processing contexts tracking."""
        
        # Create test contexts
        context1 = ProcessingContext(
            user_id="user1",
            conversation_id="conv1",
            status=ProcessingStatus.PROCESSING
        )
        context2 = ProcessingContext(
            user_id="user2", 
            conversation_id="conv2",
            status=ProcessingStatus.RETRYING,
            retry_count=1
        )
        
        orchestrator._active_contexts[context1.correlation_id] = context1
        orchestrator._active_contexts[context2.correlation_id] = context2
        
        # Get active contexts
        active = orchestrator.get_active_contexts()
        
        assert len(active) == 2
        assert context1.correlation_id in active
        assert context2.correlation_id in active
        
        # Verify context information
        ctx1_info = active[context1.correlation_id]
        assert ctx1_info["user_id"] == "user1"
        assert ctx1_info["conversation_id"] == "conv1"
        assert ctx1_info["status"] == "processing"
        assert ctx1_info["retry_count"] == 0
        
        ctx2_info = active[context2.correlation_id]
        assert ctx2_info["retry_count"] == 1
        assert ctx2_info["status"] == "retrying"

    @pytest.mark.asyncio
    async def test_context_cleanup(self, orchestrator, sample_request):
        """Test that processing contexts are properly cleaned up."""
        
        with patch.object(orchestrator, '_process_message_internal', new_callable=AsyncMock) as mock_internal:
            mock_internal.return_value = ProcessingResult(
                success=True,
                response="Test response",
                correlation_id="test_id"
            )
            
            # Verify no active contexts initially
            assert len(orchestrator._active_contexts) == 0
            
            # Process message
            await orchestrator.process_message(sample_request)
            
            # Verify context was cleaned up after processing
            assert len(orchestrator._active_contexts) == 0

    def test_reset_statistics(self, orchestrator):
        """Test statistics reset functionality."""
        
        # Set some statistics
        orchestrator._total_requests = 10
        orchestrator._successful_requests = 8
        orchestrator._failed_requests = 2
        orchestrator._retry_attempts = 5
        orchestrator._fallback_usage = 3
        orchestrator._processing_times = [0.1, 0.2, 0.3]
        
        # Reset statistics
        orchestrator.reset_stats()
        
        # Verify all stats are reset
        stats = orchestrator.get_processing_stats()
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0
        assert stats["failed_requests"] == 0
        assert stats["retry_attempts"] == 0
        assert stats["fallback_usage"] == 0
        assert stats["avg_processing_time"] == 0.0
        assert len(stats["recent_processing_times"]) == 0