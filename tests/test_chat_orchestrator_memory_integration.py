"""
Integration tests for ChatOrchestrator with MemoryProcessor.
Tests the integration of memory extraction and context retrieval in the chat orchestrator.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest,
    ChatResponse,
    RetryConfig
)
from ai_karen_engine.chat.memory_processor import (
    MemoryProcessor,
    ExtractedMemory,
    MemoryContext,
    RelevantMemory,
    MemoryType,
    ConfidenceLevel
)
from ai_karen_engine.services.spacy_service import ParsedMessage
from ai_karen_engine.database.memory_manager import MemoryEntry


class TestChatOrchestratorMemoryIntegration:
    """Test ChatOrchestrator integration with MemoryProcessor."""
    
    @pytest.fixture
    def mock_memory_processor(self):
        """Mock MemoryProcessor."""
        processor = Mock(spec=MemoryProcessor)
        processor.extract_memories = AsyncMock()
        processor.get_relevant_context = AsyncMock()
        processor.similarity_threshold = 0.7
        return processor
    
    @pytest.fixture
    def sample_parsed_message(self):
        """Sample parsed message."""
        return ParsedMessage(
            tokens=["I", "love", "pizza"],
            lemmas=["I", "love", "pizza"],
            entities=[("pizza", "FOOD")],
            pos_tags=[("I", "PRON"), ("love", "VERB"), ("pizza", "NOUN")],
            noun_phrases=["pizza"],
            sentences=["I love pizza."],
            dependencies=[],
            used_fallback=False
        )
    
    @pytest.fixture
    def sample_embeddings(self):
        """Sample embeddings."""
        return [0.1] * 768
    
    @pytest.fixture
    def chat_orchestrator(self, mock_memory_processor):
        """Create ChatOrchestrator with MemoryProcessor."""
        return ChatOrchestrator(
            memory_processor=mock_memory_processor,
            retry_config=RetryConfig(max_attempts=1),  # Reduce retries for testing
            timeout_seconds=10.0
        )
    
    @pytest.mark.asyncio
    async def test_memory_extraction_integration(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test that ChatOrchestrator calls MemoryProcessor for memory extraction."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Setup memory processor mocks
            extracted_memory = ExtractedMemory(
                content="I love pizza",
                memory_type=MemoryType.PREFERENCE,
                confidence=ConfidenceLevel.HIGH,
                source_message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                embedding=sample_embeddings,
                extraction_method="pattern_matching"
            )
            mock_memory_processor.extract_memories.return_value = [extracted_memory]
            
            # Setup context mock
            memory_context = MemoryContext(
                memories=[],
                entities=[],
                preferences=[{"content": "I love pizza", "similarity_score": 0.9}],
                facts=[],
                relationships=[],
                context_summary="Retrieved 1 user preferences",
                retrieval_time=0.1,
                total_memories_considered=5
            )
            mock_memory_processor.get_relevant_context.return_value = memory_context
            
            # Create request
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True
            )
            
            # Execute
            response = await chat_orchestrator.process_message(request)
            
            # Verify memory extraction was called
            mock_memory_processor.extract_memories.assert_called_once()
            call_args = mock_memory_processor.extract_memories.call_args
            assert call_args[0][0] == "I love pizza"  # message
            assert call_args[0][1] == sample_parsed_message  # parsed_data
            assert call_args[0][2] == sample_embeddings  # embeddings
            assert call_args[0][3] == "test_user"  # user_id
            assert call_args[0][4] == "test_conv"  # conversation_id
            
            # Verify context retrieval was called
            mock_memory_processor.get_relevant_context.assert_called_once()
            context_call_args = mock_memory_processor.get_relevant_context.call_args
            assert context_call_args[0][0] == sample_embeddings  # query_embedding
            assert context_call_args[0][1] == sample_parsed_message  # parsed_query
            assert context_call_args[0][2] == "test_user"  # user_id
            assert context_call_args[0][3] == "test_conv"  # conversation_id
            
            # Verify response
            assert isinstance(response, ChatResponse)
            assert response.context_used is True
            assert "context_summary" in response.metadata
    
    @pytest.mark.asyncio
    async def test_context_retrieval_integration(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test that ChatOrchestrator properly integrates retrieved context."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Setup memory processor mocks
            mock_memory_processor.extract_memories.return_value = []
            
            # Setup rich context
            relevant_memory = RelevantMemory(
                id="mem_1",
                content="I enjoy Italian cuisine",
                memory_type=MemoryType.PREFERENCE,
                similarity_score=0.85,
                recency_score=0.9,
                combined_score=0.87,
                created_at=datetime.utcnow(),
                metadata={"preference_type": "positive_preference"}
            )
            
            memory_context = MemoryContext(
                memories=[relevant_memory],
                entities=[{"content": "Italian cuisine", "similarity_score": 0.8}],
                preferences=[{"content": "I enjoy Italian cuisine", "similarity_score": 0.85}],
                facts=[],
                relationships=[],
                context_summary="Retrieved 1 relevant entities, 1 user preferences",
                retrieval_time=0.15,
                total_memories_considered=10
            )
            mock_memory_processor.get_relevant_context.return_value = memory_context
            
            # Create request
            request = ChatRequest(
                message="What do you know about my food preferences?",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True
            )
            
            # Execute
            response = await chat_orchestrator.process_message(request)
            
            # Verify response includes context information
            assert response.context_used is True
            assert "context_summary" in response.metadata
            assert "retrieval_time" in response.metadata
            assert "total_memories_considered" in response.metadata
            
            # Verify context structure in metadata
            assert response.metadata["context_summary"] == "Retrieved 1 relevant entities, 1 user preferences"
            assert response.metadata["retrieval_time"] == 0.15
            assert response.metadata["total_memories_considered"] == 10
    
    @pytest.mark.asyncio
    async def test_memory_processor_disabled(self, sample_parsed_message, sample_embeddings):
        """Test ChatOrchestrator behavior when MemoryProcessor is not provided."""
        # Create orchestrator without memory processor
        orchestrator = ChatOrchestrator(
            memory_processor=None,
            retry_config=RetryConfig(max_attempts=1),
            timeout_seconds=10.0
        )
        
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Create request
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True
            )
            
            # Execute
            response = await orchestrator.process_message(request)
            
            # Verify response
            assert isinstance(response, ChatResponse)
            # Context should still be available but with fallback behavior
            assert "context_summary" in response.metadata
            assert response.metadata["context_summary"] == "Memory processor not available"
    
    @pytest.mark.asyncio
    async def test_memory_extraction_error_handling(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test error handling when memory extraction fails."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Make memory extraction fail
            mock_memory_processor.extract_memories.side_effect = Exception("Memory extraction failed")
            
            # Setup context mock (should still work)
            memory_context = MemoryContext(
                memories=[],
                entities=[],
                preferences=[],
                facts=[],
                relationships=[],
                context_summary="No relevant memories found",
                retrieval_time=0.1,
                total_memories_considered=0
            )
            mock_memory_processor.get_relevant_context.return_value = memory_context
            
            # Create request
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True
            )
            
            # Execute - should not raise exception
            response = await chat_orchestrator.process_message(request)
            
            # Verify response is still successful
            assert isinstance(response, ChatResponse)
            assert response.response != ""  # Should have some response
    
    @pytest.mark.asyncio
    async def test_context_retrieval_error_handling(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test error handling when context retrieval fails."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Setup memory extraction (should work)
            mock_memory_processor.extract_memories.return_value = []
            
            # Make context retrieval fail
            mock_memory_processor.get_relevant_context.side_effect = Exception("Context retrieval failed")
            
            # Create request
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True
            )
            
            # Execute - should not raise exception
            response = await chat_orchestrator.process_message(request)
            
            # Verify response is still successful
            assert isinstance(response, ChatResponse)
            assert response.response != ""  # Should have some response
            
            # Context should indicate failure
            assert "context_summary" in response.metadata
            assert "failed" in response.metadata["context_summary"].lower()
    
    @pytest.mark.asyncio
    async def test_streaming_with_memory_integration(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test streaming response with memory integration."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Setup memory processor mocks
            mock_memory_processor.extract_memories.return_value = []
            
            memory_context = MemoryContext(
                memories=[],
                entities=[],
                preferences=[],
                facts=[],
                relationships=[],
                context_summary="No relevant memories found",
                retrieval_time=0.1,
                total_memories_considered=0
            )
            mock_memory_processor.get_relevant_context.return_value = memory_context
            
            # Create streaming request
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=True,
                include_context=True
            )
            
            # Execute
            stream_generator = await chat_orchestrator.process_message(request)
            
            # Collect streaming chunks
            chunks = []
            async for chunk in stream_generator:
                chunks.append(chunk)
            
            # Verify streaming worked
            assert len(chunks) > 0
            
            # Should have metadata chunk
            metadata_chunks = [c for c in chunks if c.type == "metadata"]
            assert len(metadata_chunks) > 0
            
            # Should have completion chunk with memory info
            complete_chunks = [c for c in chunks if c.type == "complete"]
            assert len(complete_chunks) > 0
            
            complete_chunk = complete_chunks[0]
            assert "context_used" in complete_chunk.metadata
            
            # Verify memory processor was called
            mock_memory_processor.extract_memories.assert_called_once()
            mock_memory_processor.get_relevant_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_disabled_request(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test request with context disabled."""
        # Setup mocks
        with patch('ai_karen_engine.chat.chat_orchestrator.nlp_service_manager') as mock_nlp:
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            
            # Setup memory processor mocks
            mock_memory_processor.extract_memories.return_value = []
            
            # Create request with context disabled
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=False  # Context disabled
            )
            
            # Execute
            response = await chat_orchestrator.process_message(request)
            
            # Verify memory extraction still happens (for learning)
            mock_memory_processor.extract_memories.assert_called_once()
            
            # Verify context retrieval was NOT called
            mock_memory_processor.get_relevant_context.assert_not_called()
            
            # Verify response
            assert isinstance(response, ChatResponse)
            assert response.context_used is False
    
    def test_orchestrator_stats_with_memory(self, chat_orchestrator, mock_memory_processor):
        """Test that orchestrator stats work with memory processor."""
        # Get stats
        stats = chat_orchestrator.get_processing_stats()
        
        # Verify stats structure
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "fallback_usage" in stats
        
        # Verify initial values
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])