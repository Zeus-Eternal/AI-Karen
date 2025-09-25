"""
Integration tests for ChatOrchestrator with MemoryProcessor.
Tests the integration of memory extraction and context retrieval in the chat orchestrator.
"""

import asyncio
import pytest
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
from ai_karen_engine.hooks import HookTypes
from ai_karen_engine.hooks.models import HookExecutionSummary


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
        with (
            patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp,
            patch("ai_karen_engine.chat.chat_orchestrator.get_hook_manager") as get_hook,
            patch.object(chat_orchestrator, "_generate_ai_response", AsyncMock(return_value="response")),
        ):
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            hook_manager = AsyncMock()
            summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )
            hook_manager.trigger_hooks.return_value = summary
            get_hook.return_value = hook_manager

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
            
            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=False,
                include_context=True,
                metadata={},
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
    async def test_streaming_with_memory_integration(self, chat_orchestrator, mock_memory_processor, sample_parsed_message, sample_embeddings):
        """Test streaming response with memory integration."""
        with (
            patch("ai_karen_engine.chat.chat_orchestrator.nlp_service_manager") as mock_nlp,
            patch("ai_karen_engine.chat.chat_orchestrator.get_hook_manager") as get_hook,
            patch.object(chat_orchestrator, "_generate_ai_response", AsyncMock(return_value="stream resp")),
        ):
            mock_nlp.parse_message = AsyncMock(return_value=sample_parsed_message)
            mock_nlp.get_embeddings = AsyncMock(return_value=sample_embeddings)
            mock_memory_processor.extract_memories.return_value = []
            memory_context = MemoryContext(
                memories=[],
                entities=[],
                preferences=[],
                facts=[],
                relationships=[],
                context_summary="No relevant memories found",
                retrieval_time=0.1,
                total_memories_considered=0,
            )
            mock_memory_processor.get_relevant_context.return_value = memory_context
            hook_manager = AsyncMock()
            summary = HookExecutionSummary(
                hook_type=HookTypes.PRE_MESSAGE,
                total_hooks=0,
                successful_hooks=0,
                failed_hooks=0,
                total_execution_time_ms=0.0,
                results=[],
            )
            hook_manager.trigger_hooks.return_value = summary
            get_hook.return_value = hook_manager

            request = ChatRequest(
                message="I love pizza",
                user_id="test_user",
                conversation_id="test_conv",
                stream=True,
                include_context=True,
                metadata={},
            )

            stream_generator = await chat_orchestrator.process_message(request)
            chunks = [chunk async for chunk in stream_generator]
            assert len(chunks) > 0
            metadata_chunks = [c for c in chunks if c.type == "metadata"]
            assert len(metadata_chunks) > 0
            complete_chunks = [c for c in chunks if c.type == "complete"]
            assert len(complete_chunks) > 0
            mock_memory_processor.extract_memories.assert_called_once()
            mock_memory_processor.get_relevant_context.assert_called_once()

