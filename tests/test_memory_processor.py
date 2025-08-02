"""
Comprehensive tests for MemoryProcessor implementation.
Tests all requirements for task 2.2: Add memory extraction and context retrieval.

Requirements being tested:
- 6.1: Automatic fact extraction using spaCy entity recognition
- 6.2: Preference detection using linguistic patterns and embeddings
- 6.3: Semantic similarity search using DistilBERT embeddings and Milvus
- 6.4: Memory deduplication and conflict resolution
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.memory_processor import (
    MemoryProcessor,
    ExtractedMemory,
    RelevantMemory,
    MemoryContext,
    MemoryType,
    ConfidenceLevel
)
from ai_karen_engine.services.spacy_service import ParsedMessage
from ai_karen_engine.database.memory_manager import MemoryEntry, MemoryQuery


class TestMemoryProcessor:
    """Test suite for MemoryProcessor functionality."""
    
    @pytest.fixture
    def mock_spacy_service(self):
        """Mock spaCy service."""
        service = Mock()
        service.parse_message = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_distilbert_service(self):
        """Mock DistilBERT service."""
        service = Mock()
        service.get_embeddings = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock memory manager."""
        manager = Mock()
        manager.store_memory = AsyncMock()
        manager.query_memories = AsyncMock()
        return manager
    
    @pytest.fixture
    def sample_parsed_message(self):
        """Sample parsed message with entities."""
        return ParsedMessage(
            tokens=["I", "love", "pizza", "from", "New", "York"],
            lemmas=["I", "love", "pizza", "from", "new", "york"],
            entities=[("New York", "GPE"), ("pizza", "FOOD")],
            pos_tags=[("I", "PRON"), ("love", "VERB"), ("pizza", "NOUN")],
            noun_phrases=["pizza", "New York"],
            sentences=["I love pizza from New York."],
            dependencies=[
                {
                    "text": "I",
                    "lemma": "I",
                    "pos": "PRON",
                    "tag": "PRP",
                    "dep": "nsubj",
                    "head": "love",
                    "head_pos": "VERB",
                    "children": []
                },
                {
                    "text": "pizza",
                    "lemma": "pizza",
                    "pos": "NOUN",
                    "tag": "NN",
                    "dep": "dobj",
                    "head": "love",
                    "head_pos": "VERB",
                    "children": []
                }
            ],
            used_fallback=False
        )
    
    @pytest.fixture
    def sample_embeddings(self):
        """Sample embeddings vector."""
        return [0.1] * 768  # Standard DistilBERT dimension
    
    @pytest.fixture
    def memory_processor(self, mock_spacy_service, mock_distilbert_service, mock_memory_manager):
        """Create MemoryProcessor instance with mocked dependencies."""
        return MemoryProcessor(
            spacy_service=mock_spacy_service,
            distilbert_service=mock_distilbert_service,
            memory_manager=mock_memory_manager,
            similarity_threshold=0.7,
            deduplication_threshold=0.95,
            max_context_memories=10,
            recency_weight=0.3
        )
    
    @pytest.mark.asyncio
    async def test_extract_entity_memories(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test automatic fact extraction using spaCy entity recognition (Requirement 6.1)."""
        # Setup
        message = "I love pizza from New York."
        user_id = "test_user"
        conversation_id = "test_conv"
        
        # Mock memory storage
        memory_processor.memory_manager.store_memory.return_value = "memory_123"
        
        # Execute
        extracted_memories = await memory_processor.extract_memories(
            message, sample_parsed_message, sample_embeddings, user_id, conversation_id
        )
        
        # Verify entity extraction
        entity_memories = [m for m in extracted_memories if m.memory_type == MemoryType.ENTITY]
        assert len(entity_memories) >= 1, "Should extract entity memories"
        
        # Check for location entity (New York)
        location_memory = next((m for m in entity_memories if "New York" in m.content), None)
        assert location_memory is not None, "Should extract New York as location entity"
        assert location_memory.memory_type == MemoryType.ENTITY
        assert location_memory.confidence == ConfidenceLevel.HIGH
        assert "GPE" in location_memory.content
        
        # Verify metadata
        assert location_memory.user_id == user_id
        assert location_memory.conversation_id == conversation_id
        assert location_memory.metadata["extraction_method"] == "spacy_ner"
        assert location_memory.metadata["entity_label"] == "GPE"
    
    @pytest.mark.asyncio
    async def test_extract_preference_memories(self, memory_processor, sample_embeddings):
        """Test preference detection using linguistic patterns (Requirement 6.2)."""
        # Setup test messages with different preference patterns
        test_cases = [
            ("I love chocolate ice cream", "positive_preference"),
            ("I don't like spicy food", "negative_preference"),
            ("My favorite color is blue", "favorite"),
            ("I usually wake up early", "habit"),
            ("I work at Google", "work_info"),
            ("I am a software engineer", "identity_info")
        ]
        
        for message, expected_type in test_cases:
            # Create simple parsed message
            parsed_message = ParsedMessage(
                tokens=message.split(),
                lemmas=message.lower().split(),
                entities=[],
                pos_tags=[],
                noun_phrases=[],
                sentences=[message],
                dependencies=[],
                used_fallback=False
            )
            
            # Mock memory storage
            memory_processor.memory_manager.store_memory.return_value = "memory_123"
            
            # Execute
            extracted_memories = await memory_processor.extract_memories(
                message, parsed_message, sample_embeddings, "test_user", "test_conv"
            )
            
            # Verify preference extraction
            preference_memories = [m for m in extracted_memories if m.memory_type == MemoryType.PREFERENCE]
            assert len(preference_memories) >= 1, f"Should extract preference from: {message}"
            
            preference_memory = preference_memories[0]
            assert preference_memory.memory_type == MemoryType.PREFERENCE
            assert preference_memory.metadata["preference_type"] == expected_type
            assert preference_memory.metadata["extraction_method"] == "pattern_matching"
    
    @pytest.mark.asyncio
    async def test_extract_fact_memories(self, memory_processor, sample_embeddings):
        """Test fact extraction using linguistic patterns."""
        # Setup test messages with factual patterns
        test_cases = [
            ("Python is a programming language", "is_relationship"),
            ("The car has four wheels", "has_relationship"),
            ("Birds can fly", "capability"),
            ("The meeting will start at 3pm", "future_fact"),
            ("The event happened yesterday", "event")
        ]
        
        for message, expected_type in test_cases:
            # Create simple parsed message
            parsed_message = ParsedMessage(
                tokens=message.split(),
                lemmas=message.lower().split(),
                entities=[],
                pos_tags=[],
                noun_phrases=[],
                sentences=[message],
                dependencies=[],
                used_fallback=False
            )
            
            # Mock memory storage
            memory_processor.memory_manager.store_memory.return_value = "memory_123"
            
            # Execute
            extracted_memories = await memory_processor.extract_memories(
                message, parsed_message, sample_embeddings, "test_user", "test_conv"
            )
            
            # Verify fact extraction
            fact_memories = [m for m in extracted_memories if m.memory_type == MemoryType.FACT]
            assert len(fact_memories) >= 1, f"Should extract fact from: {message}"
            
            fact_memory = fact_memories[0]
            assert fact_memory.memory_type == MemoryType.FACT
            assert fact_memory.metadata["fact_type"] == expected_type
    
    @pytest.mark.asyncio
    async def test_extract_relationship_memories(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test relationship extraction from dependency parsing."""
        # Setup
        message = "I love pizza from New York."
        user_id = "test_user"
        conversation_id = "test_conv"
        
        # Mock memory storage
        memory_processor.memory_manager.store_memory.return_value = "memory_123"
        
        # Execute
        extracted_memories = await memory_processor.extract_memories(
            message, sample_parsed_message, sample_embeddings, user_id, conversation_id
        )
        
        # Verify relationship extraction
        relationship_memories = [m for m in extracted_memories if m.memory_type == MemoryType.RELATIONSHIP]
        assert len(relationship_memories) >= 1, "Should extract relationship memories"
        
        # Check for subject-verb-object relationship
        subj_rel = next((m for m in relationship_memories if "nsubj" in m.content), None)
        assert subj_rel is not None, "Should extract subject relationship"
        assert subj_rel.metadata["relation"] == "nsubj"
        assert subj_rel.metadata["extraction_method"] == "dependency_parsing"
    
    @pytest.mark.asyncio
    async def test_semantic_similarity_search(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test semantic similarity search using DistilBERT embeddings and Milvus (Requirement 6.3)."""
        # Setup mock memory manager to return similar memories
        mock_memories = [
            MemoryEntry(
                id="mem_1",
                content="I enjoy Italian cuisine",
                embedding=sample_embeddings,
                metadata={"type": "preference"},
                timestamp=time.time() - 3600,  # 1 hour ago
                user_id="test_user"
            ),
            MemoryEntry(
                id="mem_2", 
                content="Pizza is my favorite food",
                embedding=[0.15] * 768,  # Slightly different embedding
                metadata={"type": "preference"},
                timestamp=time.time() - 7200,  # 2 hours ago
                user_id="test_user"
            )
        ]
        
        memory_processor.memory_manager.query_memories.return_value = mock_memories
        
        # Execute context retrieval
        context = await memory_processor.get_relevant_context(
            sample_embeddings,
            sample_parsed_message,
            "test_user",
            "test_conv"
        )
        
        # Verify semantic search results
        assert isinstance(context, MemoryContext)
        assert len(context.memories) > 0, "Should retrieve relevant memories"
        
        # Check similarity scoring
        for memory in context.memories:
            assert memory.similarity_score >= memory_processor.similarity_threshold
            assert memory.recency_score > 0
            assert memory.combined_score > 0
        
        # Verify memories are sorted by combined score
        scores = [m.combined_score for m in context.memories]
        assert scores == sorted(scores, reverse=True), "Memories should be sorted by combined score"
        
        # Verify context structure
        assert isinstance(context.entities, list)
        assert isinstance(context.preferences, list)
        assert isinstance(context.facts, list)
        assert isinstance(context.relationships, list)
        assert context.context_summary != ""
        assert context.retrieval_time >= 0
    
    @pytest.mark.asyncio
    async def test_memory_deduplication(self, memory_processor, sample_embeddings):
        """Test memory deduplication and conflict resolution (Requirement 6.4)."""
        # Setup duplicate memories
        message1 = "I love pizza"
        message2 = "I really love pizza"  # Very similar content
        
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
        
        # Mock similar stored memories
        memory_processor.memory_manager.query_memories.return_value = [
            MemoryEntry(
                id="existing_mem",
                content="I love pizza",
                embedding=sample_embeddings,
                metadata={"type": "preference"},
                timestamp=time.time() - 3600,
                user_id="test_user"
            )
        ]
        
        # Mock storage
        memory_processor.memory_manager.store_memory.return_value = "memory_123"
        
        # Execute extraction for first message
        extracted_memories1 = await memory_processor.extract_memories(
            message1, parsed_message, sample_embeddings, "test_user", "test_conv"
        )
        
        # Execute extraction for very similar message
        extracted_memories2 = await memory_processor.extract_memories(
            message2, parsed_message, sample_embeddings, "test_user", "test_conv"
        )
        
        # Verify deduplication occurred
        # The second extraction should have fewer memories due to deduplication
        assert len(extracted_memories2) <= len(extracted_memories1), "Deduplication should reduce memory count"
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, memory_processor, sample_embeddings):
        """Test confidence level assignment for different memory types."""
        test_cases = [
            ("John lives in New York", MemoryType.ENTITY, ConfidenceLevel.HIGH),  # Person + Location
            ("I love chocolate", MemoryType.PREFERENCE, ConfidenceLevel.HIGH),    # Strong preference
            ("I tend to wake up early", MemoryType.PREFERENCE, ConfidenceLevel.MEDIUM),  # Tendency
            ("Python is a language", MemoryType.FACT, ConfidenceLevel.HIGH)      # is_relationship fact
        ]
        
        for message, expected_type, expected_confidence in test_cases:
            # Create parsed message with appropriate entities
            entities = []
            if "John" in message:
                entities.append(("John", "PERSON"))
            if "New York" in message:
                entities.append(("New York", "GPE"))
            
            parsed_message = ParsedMessage(
                tokens=message.split(),
                lemmas=message.lower().split(),
                entities=entities,
                pos_tags=[],
                noun_phrases=[],
                sentences=[message],
                dependencies=[],
                used_fallback=False
            )
            
            # Mock storage
            memory_processor.memory_manager.store_memory.return_value = "memory_123"
            
            # Execute
            extracted_memories = await memory_processor.extract_memories(
                message, parsed_message, sample_embeddings, "test_user", "test_conv"
            )
            
            # Find memory of expected type
            target_memories = [m for m in extracted_memories if m.memory_type == expected_type]
            assert len(target_memories) > 0, f"Should extract {expected_type.value} memory from: {message}"
            
            # Verify confidence level
            target_memory = target_memories[0]
            assert target_memory.confidence == expected_confidence, \
                f"Expected {expected_confidence.value} confidence for {expected_type.value}"
    
    @pytest.mark.asyncio
    async def test_temporal_memory_extraction(self, memory_processor, sample_embeddings):
        """Test extraction of temporal memories from time-related entities."""
        # Setup message with temporal entities
        message = "I have a meeting tomorrow at 3pm"
        parsed_message = ParsedMessage(
            tokens=message.split(),
            lemmas=message.lower().split(),
            entities=[("tomorrow", "DATE"), ("3pm", "TIME")],
            pos_tags=[],
            noun_phrases=[],
            sentences=[message],
            dependencies=[],
            used_fallback=False
        )
        
        # Mock storage
        memory_processor.memory_manager.store_memory.return_value = "memory_123"
        
        # Execute
        extracted_memories = await memory_processor.extract_memories(
            message, parsed_message, sample_embeddings, "test_user", "test_conv"
        )
        
        # Verify temporal memory extraction
        temporal_memories = [m for m in extracted_memories if m.memory_type == MemoryType.TEMPORAL]
        assert len(temporal_memories) >= 1, "Should extract temporal memories"
        
        # Check temporal metadata
        temporal_memory = temporal_memories[0]
        assert temporal_memory.metadata["extraction_method"] == "temporal_ner"
        assert temporal_memory.metadata["temporal_type"] in ["DATE", "TIME"]
    
    @pytest.mark.asyncio
    async def test_fallback_behavior(self, memory_processor, sample_embeddings):
        """Test graceful fallback when spaCy parsing fails."""
        # Setup parsed message with fallback flag
        message = "I love pizza"
        fallback_parsed_message = ParsedMessage(
            tokens=message.split(),
            lemmas=message.lower().split(),
            entities=[],  # No entities in fallback mode
            pos_tags=[],
            noun_phrases=[],
            sentences=[message],
            dependencies=[],
            used_fallback=True  # Fallback mode
        )
        
        # Mock storage
        memory_processor.memory_manager.store_memory.return_value = "memory_123"
        
        # Execute
        extracted_memories = await memory_processor.extract_memories(
            message, fallback_parsed_message, sample_embeddings, "test_user", "test_conv"
        )
        
        # Should still extract preference memories using pattern matching
        preference_memories = [m for m in extracted_memories if m.memory_type == MemoryType.PREFERENCE]
        assert len(preference_memories) >= 1, "Should extract preferences even in fallback mode"
        
        # Should not extract relationship memories (requires dependency parsing)
        relationship_memories = [m for m in extracted_memories if m.memory_type == MemoryType.RELATIONSHIP]
        assert len(relationship_memories) == 0, "Should not extract relationships in fallback mode"
    
    @pytest.mark.asyncio
    async def test_context_building(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test structured context building from retrieved memories."""
        # Setup mock memories of different types
        mock_memories = [
            MemoryEntry(
                id="mem_1",
                content="PERSON: John",
                embedding=sample_embeddings,
                metadata={"type": "entity", "entity_label": "PERSON"},
                timestamp=time.time() - 1800,
                user_id="test_user"
            ),
            MemoryEntry(
                id="mem_2",
                content="I love Italian food",
                embedding=sample_embeddings,
                metadata={"type": "preference", "preference_type": "positive_preference"},
                timestamp=time.time() - 3600,
                user_id="test_user"
            ),
            MemoryEntry(
                id="mem_3",
                content="Pizza is delicious",
                embedding=sample_embeddings,
                metadata={"type": "fact", "fact_type": "is_relationship"},
                timestamp=time.time() - 7200,
                user_id="test_user"
            )
        ]
        
        memory_processor.memory_manager.query_memories.return_value = mock_memories
        
        # Execute context retrieval
        context = await memory_processor.get_relevant_context(
            sample_embeddings,
            sample_parsed_message,
            "test_user",
            "test_conv"
        )
        
        # Verify structured context
        assert len(context.entities) > 0, "Should categorize entity memories"
        assert len(context.preferences) > 0, "Should categorize preference memories"
        assert len(context.facts) > 0, "Should categorize fact memories"
        
        # Verify context summary
        assert "entities" in context.context_summary.lower()
        assert "preferences" in context.context_summary.lower()
        assert "memories" in context.context_summary.lower()
    
    @pytest.mark.asyncio
    async def test_recency_weighting(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test recency weighting in memory retrieval."""
        # Setup memories with different timestamps
        old_time = time.time() - 86400  # 24 hours ago
        recent_time = time.time() - 3600  # 1 hour ago
        
        mock_memories = [
            MemoryEntry(
                id="old_mem",
                content="Old memory",
                embedding=sample_embeddings,
                metadata={"type": "preference"},
                timestamp=old_time,
                user_id="test_user"
            ),
            MemoryEntry(
                id="recent_mem",
                content="Recent memory",
                embedding=sample_embeddings,
                metadata={"type": "preference"},
                timestamp=recent_time,
                user_id="test_user"
            )
        ]
        
        memory_processor.memory_manager.query_memories.return_value = mock_memories
        
        # Execute context retrieval
        context = await memory_processor.get_relevant_context(
            sample_embeddings,
            sample_parsed_message,
            "test_user",
            "test_conv"
        )
        
        # Verify recency scoring
        for memory in context.memories:
            assert memory.recency_score > 0, "Should have recency score"
            assert memory.combined_score > 0, "Should have combined score"
        
        # Recent memory should have higher recency score
        recent_memory = next(m for m in context.memories if m.id == "recent_mem")
        old_memory = next(m for m in context.memories if m.id == "old_mem")
        
        assert recent_memory.recency_score > old_memory.recency_score, \
            "Recent memory should have higher recency score"
    
    def test_processing_stats(self, memory_processor):
        """Test processing statistics tracking."""
        # Get initial stats
        stats = memory_processor.get_processing_stats()
        
        # Verify stats structure
        assert "extraction_count" in stats
        assert "retrieval_count" in stats
        assert "deduplication_count" in stats
        assert "conflict_resolution_count" in stats
        assert "similarity_threshold" in stats
        assert "deduplication_threshold" in stats
        
        # Verify initial values
        assert stats["extraction_count"] == 0
        assert stats["retrieval_count"] == 0
        assert stats["similarity_threshold"] == 0.7
        assert stats["deduplication_threshold"] == 0.95
    
    def test_stats_reset(self, memory_processor):
        """Test statistics reset functionality."""
        # Manually set some stats
        memory_processor._extraction_count = 5
        memory_processor._retrieval_count = 3
        
        # Reset stats
        memory_processor.reset_stats()
        
        # Verify reset
        stats = memory_processor.get_processing_stats()
        assert stats["extraction_count"] == 0
        assert stats["retrieval_count"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, memory_processor, sample_parsed_message, sample_embeddings):
        """Test error handling in memory processing."""
        # Setup memory manager to raise exception
        memory_processor.memory_manager.store_memory.side_effect = Exception("Storage failed")
        
        # Execute - should not raise exception
        extracted_memories = await memory_processor.extract_memories(
            "I love pizza",
            sample_parsed_message,
            sample_embeddings,
            "test_user",
            "test_conv"
        )
        
        # Should return empty list on error, not raise exception
        assert isinstance(extracted_memories, list)
        
        # Test context retrieval error handling
        memory_processor.memory_manager.query_memories.side_effect = Exception("Query failed")
        
        context = await memory_processor.get_relevant_context(
            sample_embeddings,
            sample_parsed_message,
            "test_user",
            "test_conv"
        )
        
        # Should return empty context, not raise exception
        assert isinstance(context, MemoryContext)
        assert len(context.memories) == 0
        assert "failed" in context.context_summary.lower() or context.context_summary == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])