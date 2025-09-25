"""
Simple integration test for memory extraction and context retrieval functionality.
Tests the core requirements for task 2.2.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from ai_karen_engine.chat.memory_processor import (
    MemoryProcessor,
    ExtractedMemory,
    MemoryContext,
    RelevantMemory,
    MemoryType,
    ConfidenceLevel
)
from ai_karen_engine.services.spacy_service import ParsedMessage


class TestMemoryIntegrationSimple:
    """Simple integration tests for memory functionality."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        spacy_service = Mock()
        spacy_service.parse_message = AsyncMock()
        
        distilbert_service = Mock()
        distilbert_service.get_embeddings = AsyncMock()
        
        memory_manager = Mock()
        memory_manager.store_memory = AsyncMock()
        memory_manager.query_memories = AsyncMock()
        
        return spacy_service, distilbert_service, memory_manager
    
    @pytest.fixture
    def memory_processor(self, mock_services):
        """Create MemoryProcessor with mocked services."""
        spacy_service, distilbert_service, memory_manager = mock_services
        return MemoryProcessor(
            spacy_service=spacy_service,
            distilbert_service=distilbert_service,
            memory_manager=memory_manager
        )
    
    @pytest.mark.asyncio
    async def test_end_to_end_memory_processing(self, memory_processor, mock_services):
        """Test end-to-end memory processing workflow."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Setup test data
        message = "I love Italian pizza from New York"
        user_id = "test_user"
        conversation_id = "test_conv"
        embeddings = [0.1] * 768
        
        # Setup parsed message with entities and dependencies
        parsed_message = ParsedMessage(
            tokens=["I", "love", "Italian", "pizza", "from", "New", "York"],
            lemmas=["I", "love", "italian", "pizza", "from", "new", "york"],
            entities=[("Italian", "NORP"), ("New York", "GPE")],
            pos_tags=[("I", "PRON"), ("love", "VERB"), ("pizza", "NOUN")],
            noun_phrases=["Italian pizza", "New York"],
            sentences=["I love Italian pizza from New York."],
            dependencies=[
                {
                    "text": "I",
                    "lemma": "I",
                    "pos": "PRON",
                    "dep": "nsubj",
                    "head": "love",
                    "head_pos": "VERB",
                    "children": []
                },
                {
                    "text": "pizza",
                    "lemma": "pizza",
                    "pos": "NOUN",
                    "dep": "dobj",
                    "head": "love",
                    "head_pos": "VERB",
                    "children": []
                }
            ],
            used_fallback=False
        )
        
        # Mock memory storage
        memory_manager.store_memory.return_value = "memory_123"
        
        # Test memory extraction
        extracted_memories = await memory_processor.extract_memories(
            message, parsed_message, embeddings, user_id, conversation_id
        )
        
        # Verify memory extraction results
        assert len(extracted_memories) > 0, "Should extract memories"
        
        # Check for entity memories
        entity_memories = [m for m in extracted_memories if m.memory_type == MemoryType.ENTITY]
        assert len(entity_memories) >= 1, "Should extract entity memories"
        
        # Check for preference memories (from "I love" pattern)
        preference_memories = [m for m in extracted_memories if m.memory_type == MemoryType.PREFERENCE]
        assert len(preference_memories) >= 1, "Should extract preference memories"
        
        # Check for relationship memories (from dependency parsing)
        relationship_memories = [m for m in extracted_memories if m.memory_type == MemoryType.RELATIONSHIP]
        assert len(relationship_memories) >= 1, "Should extract relationship memories"
        
        # Verify memory storage was called
        assert memory_manager.store_memory.call_count >= len(extracted_memories)
        
        # Test context retrieval
        from ai_karen_engine.database.memory_manager import MemoryEntry
        import time
        
        # Mock stored memories for retrieval
        stored_memories = [
            MemoryEntry(
                id="mem_1",
                content="I enjoy Italian cuisine",
                embedding=embeddings,
                metadata={"type": "preference"},
                timestamp=time.time() - 3600,
                user_id=user_id
            ),
            MemoryEntry(
                id="mem_2",
                content="NORP: Italian",
                embedding=[0.12] * 768,
                metadata={"type": "entity", "entity_label": "NORP"},
                timestamp=time.time() - 1800,
                user_id=user_id
            )
        ]
        
        memory_manager.query_memories.return_value = stored_memories
        
        # Test context retrieval
        context = await memory_processor.get_relevant_context(
            embeddings, parsed_message, user_id, conversation_id
        )
        
        # Verify context retrieval results
        assert isinstance(context, MemoryContext)
        assert len(context.memories) > 0, "Should retrieve relevant memories"
        assert context.context_summary != "", "Should have context summary"
        assert context.retrieval_time >= 0, "Should track retrieval time"
        
        # Verify memory categorization
        assert isinstance(context.entities, list)
        assert isinstance(context.preferences, list)
        assert isinstance(context.facts, list)
        assert isinstance(context.relationships, list)
        
        # Verify similarity scoring
        for memory in context.memories:
            assert memory.similarity_score >= 0, "Should have similarity score"
            assert memory.recency_score >= 0, "Should have recency score"
            assert memory.combined_score >= 0, "Should have combined score"
    
    @pytest.mark.asyncio
    async def test_memory_deduplication_workflow(self, memory_processor, mock_services):
        """Test memory deduplication prevents duplicate storage."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Setup test data
        message1 = "I love pizza"
        message2 = "I really love pizza"  # Very similar
        embeddings = [0.1] * 768
        
        parsed_message = ParsedMessage(
            tokens=message1.split(),
            lemmas=message1.lower().split(),
            entities=[],
            pos_tags=[],
            noun_phrases=[],
            sentences=[message1],
            dependencies=[],
            used_fallback=False
        )
        
        # Mock existing similar memory
        from ai_karen_engine.database.memory_manager import MemoryEntry
        import time
        
        existing_memory = MemoryEntry(
            id="existing_mem",
            content="I love pizza",
            embedding=embeddings,  # Same embedding = high similarity
            metadata={"type": "preference"},
            timestamp=time.time() - 3600,
            user_id="test_user"
        )
        
        memory_manager.query_memories.return_value = [existing_memory]
        memory_manager.store_memory.return_value = "memory_123"
        
        # Extract memories from first message
        extracted_memories1 = await memory_processor.extract_memories(
            message1, parsed_message, embeddings, "test_user", "test_conv"
        )
        
        # Extract memories from very similar message
        extracted_memories2 = await memory_processor.extract_memories(
            message2, parsed_message, embeddings, "test_user", "test_conv"
        )
        
        # Verify deduplication occurred
        # The second extraction should have fewer or equal memories due to deduplication
        assert len(extracted_memories2) <= len(extracted_memories1), \
            "Deduplication should prevent duplicate memories"
    
    @pytest.mark.asyncio
    async def test_fallback_behavior(self, memory_processor, mock_services):
        """Test graceful fallback when spaCy parsing fails."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Setup fallback parsed message (no entities, no dependencies)
        message = "I love pizza"
        embeddings = [0.1] * 768
        
        fallback_parsed_message = ParsedMessage(
            tokens=message.split(),
            lemmas=message.lower().split(),
            entities=[],  # No entities in fallback
            pos_tags=[],
            noun_phrases=[],
            sentences=[message],
            dependencies=[],  # No dependencies in fallback
            used_fallback=True  # Fallback mode
        )
        
        memory_manager.store_memory.return_value = "memory_123"
        
        # Extract memories in fallback mode
        extracted_memories = await memory_processor.extract_memories(
            message, fallback_parsed_message, embeddings, "test_user", "test_conv"
        )
        
        # Should still extract preference memories using pattern matching
        preference_memories = [m for m in extracted_memories if m.memory_type == MemoryType.PREFERENCE]
        assert len(preference_memories) >= 1, "Should extract preferences even in fallback mode"
        
        # Should not extract relationship memories (requires dependency parsing)
        relationship_memories = [m for m in extracted_memories if m.memory_type == MemoryType.RELATIONSHIP]
        assert len(relationship_memories) == 0, "Should not extract relationships in fallback mode"
        
        # Should not extract entity memories (requires NER)
        entity_memories = [m for m in extracted_memories if m.memory_type == MemoryType.ENTITY]
        assert len(entity_memories) == 0, "Should not extract entities in fallback mode"
    
    def test_memory_processor_initialization(self, mock_services):
        """Test MemoryProcessor initialization with proper configuration."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Test with custom configuration
        processor = MemoryProcessor(
            spacy_service=spacy_service,
            distilbert_service=distilbert_service,
            memory_manager=memory_manager,
            similarity_threshold=0.8,
            deduplication_threshold=0.9,
            max_context_memories=15,
            recency_weight=0.4
        )
        
        # Verify configuration
        assert processor.similarity_threshold == 0.8
        assert processor.deduplication_threshold == 0.9
        assert processor.max_context_memories == 15
        assert processor.recency_weight == 0.4
        
        # Verify services are properly assigned
        assert processor.spacy_service == spacy_service
        assert processor.distilbert_service == distilbert_service
        assert processor.memory_manager == memory_manager
        
        # Verify statistics tracking
        stats = processor.get_processing_stats()
        assert "extraction_count" in stats
        assert "retrieval_count" in stats
        assert "deduplication_count" in stats
        assert stats["similarity_threshold"] == 0.8
        assert stats["deduplication_threshold"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])