"""
Tests for MemoryProcessor task 3.2: Implement intelligent context building and retrieval.

Tests all requirements for task 3.2:
- Create context-aware memory retrieval with relevance scoring
- Build conversation context aggregation and summarization
- Implement memory conflict resolution and preference learning
- Add memory analytics and usage tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.ai_karen_engine.chat.memory_processor import (
    MemoryProcessor, MemoryType, ConfidenceLevel, RelevantMemory, MemoryContext
)
from src.ai_karen_engine.services.spacy_service import ParsedMessage, SpacyService
from src.ai_karen_engine.services.distilbert_service import DistilBertService
from src.ai_karen_engine.database.memory_manager import MemoryManager, MemoryEntry, MemoryQuery


class TestMemoryProcessorTask32:
    """Test suite for MemoryProcessor task 3.2 functionality."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        spacy_service = Mock(spec=SpacyService)
        distilbert_service = Mock(spec=DistilBertService)
        memory_manager = Mock(spec=MemoryManager)
        
        # Setup async methods
        spacy_service.parse_message = AsyncMock()
        distilbert_service.get_embeddings = AsyncMock()
        memory_manager.query_memories = AsyncMock()
        memory_manager.store_memory = AsyncMock()
        
        return spacy_service, distilbert_service, memory_manager
    
    @pytest.fixture
    def memory_processor(self, mock_services):
        """Create MemoryProcessor instance with mocked services."""
        spacy_service, distilbert_service, memory_manager = mock_services
        return MemoryProcessor(
            spacy_service=spacy_service,
            distilbert_service=distilbert_service,
            memory_manager=memory_manager,
            similarity_threshold=0.7,
            deduplication_threshold=0.95,
            max_context_memories=10,
            recency_weight=0.3
        )
    
    @pytest.fixture
    def sample_relevant_memories(self):
        """Create sample relevant memories for testing."""
        return [
            RelevantMemory(
                id="mem1",
                content="I like pizza",
                memory_type=MemoryType.PREFERENCE,
                similarity_score=0.9,
                recency_score=0.8,
                combined_score=0.87,
                created_at=datetime.utcnow(),
                metadata={
                    "preference_type": "positive_preference",
                    "preference_content": "pizza",
                    "confidence": "high"
                }
            ),
            RelevantMemory(
                id="mem2",
                content="I don't like vegetables",
                memory_type=MemoryType.PREFERENCE,
                similarity_score=0.8,
                recency_score=0.6,
                combined_score=0.74,
                created_at=datetime.utcnow() - timedelta(days=1),
                metadata={
                    "preference_type": "negative_preference",
                    "preference_content": "vegetables",
                    "confidence": "high"
                }
            ),
            RelevantMemory(
                id="mem3",
                content="PERSON: John",
                memory_type=MemoryType.ENTITY,
                similarity_score=0.85,
                recency_score=0.9,
                combined_score=0.86,
                created_at=datetime.utcnow(),
                metadata={
                    "entity_text": "John",
                    "entity_label": "PERSON",
                    "confidence": "high"
                }
            ),
            RelevantMemory(
                id="mem4",
                content="Python is a programming language",
                memory_type=MemoryType.FACT,
                similarity_score=0.75,
                recency_score=0.7,
                combined_score=0.74,
                created_at=datetime.utcnow(),
                metadata={
                    "fact_type": "is_relationship",
                    "subject": "Python",
                    "object": "programming language",
                    "confidence": "high"
                }
            )
        ]
    
    @pytest.mark.asyncio
    async def test_intelligent_context_building(self, memory_processor, sample_relevant_memories):
        """Test intelligent context building with conflict resolution and summarization."""
        # Test context building
        context = await memory_processor._build_memory_context(sample_relevant_memories)
        
        # Verify context structure
        assert isinstance(context, MemoryContext)
        assert len(context.memories) == 4
        assert len(context.entities) == 1
        assert len(context.preferences) == 2
        assert len(context.facts) == 1
        assert len(context.relationships) == 0
        
        # Verify context summary is intelligent
        assert "1 PERSON" in context.context_summary or "Entities" in context.context_summary
        assert "2 likes" in context.context_summary or "Preferences" in context.context_summary
        assert "1 is relationship" in context.context_summary or "Facts" in context.context_summary
        assert "high confidence" in context.context_summary
    
    @pytest.mark.asyncio
    async def test_preference_conflict_resolution(self, memory_processor):
        """Test memory conflict resolution for preferences."""
        # Create conflicting preferences
        conflicting_preferences = [
            {
                "content": "I like coffee",
                "similarity_score": 0.8,
                "recency_score": 0.9,
                "combined_score": 0.83,
                "metadata": {
                    "preference_type": "positive_preference",
                    "preference_content": "coffee"
                }
            },
            {
                "content": "I don't like coffee anymore",
                "similarity_score": 0.85,
                "recency_score": 0.95,  # More recent
                "combined_score": 0.88,
                "metadata": {
                    "preference_type": "negative_preference",
                    "preference_content": "coffee"
                }
            }
        ]
        
        # Test conflict resolution
        resolved = await memory_processor._resolve_preference_conflicts(conflicting_preferences)
        
        # Should keep the more recent negative preference
        assert len(resolved) == 1
        assert "don't like coffee" in resolved[0]["content"]
        assert memory_processor._conflict_resolution_count > 0
    
    @pytest.mark.asyncio
    async def test_fact_conflict_resolution(self, memory_processor):
        """Test memory conflict resolution for facts."""
        # Create conflicting facts
        conflicting_facts = [
            {
                "content": "Python was created in 1989",
                "similarity_score": 0.7,
                "recency_score": 0.5,
                "combined_score": 0.65,
                "metadata": {
                    "fact_type": "past_fact",
                    "subject": "Python",
                    "confidence": "medium"
                }
            },
            {
                "content": "Python was created in 1991",
                "similarity_score": 0.8,
                "recency_score": 0.9,
                "combined_score": 0.83,
                "metadata": {
                    "fact_type": "past_fact",
                    "subject": "Python",
                    "confidence": "high"
                }
            }
        ]
        
        # Test conflict resolution
        resolved = await memory_processor._resolve_fact_conflicts(conflicting_facts)
        
        # Should keep the more confident and recent fact
        assert len(resolved) == 1
        assert "1991" in resolved[0]["content"]
        assert memory_processor._conflict_resolution_count > 0
    
    @pytest.mark.asyncio
    async def test_context_summary_generation(self, memory_processor):
        """Test intelligent context summary generation."""
        entities = [
            {"metadata": {"entity_label": "PERSON"}},
            {"metadata": {"entity_label": "ORG"}},
            {"metadata": {"entity_label": "PERSON"}}
        ]
        
        preferences = [
            {"metadata": {"preference_type": "positive_preference"}, "content": "I like music"},
            {"metadata": {"preference_type": "negative_preference"}, "content": "I don't like noise"}
        ]
        
        facts = [
            {"metadata": {"fact_type": "is_relationship"}},
            {"metadata": {"fact_type": "capability"}}
        ]
        
        relationships = [{"content": "relationship1"}]
        
        # Test summary generation
        summary = await memory_processor._generate_context_summary(
            entities, preferences, facts, relationships
        )
        
        # Verify summary contains key information
        assert "2 person, 1 org" in summary.lower() or "entities" in summary.lower()
        assert "1 likes, 1 dislikes" in summary.lower() or "preferences" in summary.lower()
        assert "1 is relationship, 1 capability" in summary.lower() or "facts" in summary.lower()
        assert "1 connections" in summary.lower() or "relationships" in summary.lower()
        assert "confidence" in summary.lower()
    
    @pytest.mark.asyncio
    async def test_memory_analytics(self, memory_processor, mock_services):
        """Test comprehensive memory analytics and usage tracking."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Mock memory data for analytics
        mock_memories = [
            MemoryEntry(
                id="mem1",
                content="I like pizza",
                metadata={
                    "type": "preference",
                    "confidence": "high",
                    "extraction_method": "pattern_matching",
                    "preference_type": "positive_preference"
                },
                timestamp=time.time(),
                user_id="user1"
            ),
            MemoryEntry(
                id="mem2",
                content="PERSON: John",
                metadata={
                    "type": "entity",
                    "confidence": "high",
                    "extraction_method": "spacy_ner",
                    "entity_label": "PERSON",
                    "entity_text": "John"
                },
                timestamp=time.time() - 86400,  # 1 day ago
                user_id="user1"
            ),
            MemoryEntry(
                id="mem3",
                content="Python is powerful",
                metadata={
                    "type": "fact",
                    "confidence": "medium",
                    "extraction_method": "pattern_matching",
                    "fact_type": "is_relationship"
                },
                timestamp=time.time() - 2592000,  # 30 days ago
                user_id="user1"
            )
        ]
        
        memory_manager.query_memories.return_value = mock_memories
        
        # Test analytics generation
        analytics = await memory_processor.get_memory_analytics("user1")
        
        # Verify analytics structure
        assert analytics["total_memories"] == 3
        assert "preference" in analytics["memory_types"]
        assert "entity" in analytics["memory_types"]
        assert "fact" in analytics["memory_types"]
        
        assert analytics["confidence_distribution"]["high"] == 2
        assert analytics["confidence_distribution"]["medium"] == 1
        
        assert "pattern_matching" in analytics["extraction_methods"]
        assert "spacy_ner" in analytics["extraction_methods"]
        
        # Verify temporal distribution
        assert len(analytics["temporal_distribution"]) > 0
        
        # Verify entity analysis
        assert len(analytics["top_entities"]) > 0
        assert analytics["top_entities"][0]["entity"] == "John"
        assert analytics["top_entities"][0]["type"] == "PERSON"
        
        # Verify preference insights
        assert analytics["preference_insights"]["total_preferences"] == 1
        assert analytics["preference_insights"]["positive_ratio"] == 1.0
        
        # Verify fact categories
        assert "is_relationship" in analytics["fact_categories"]
    
    @pytest.mark.asyncio
    async def test_preference_learning(self, memory_processor, mock_services):
        """Test preference learning from conversation patterns."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Mock conversation history
        conversation_history = [
            "I really enjoy working with Python programming language",
            "Can you help me with machine learning?",
            "I prefer detailed explanations over brief ones",
            "What's the weather like today?",
            "I'm interested in artificial intelligence and neural networks"
        ]
        
        # Mock spaCy parsing results
        spacy_service.parse_message.return_value = ParsedMessage(
            tokens=["I", "enjoy", "Python"],
            lemmas=["I", "enjoy", "Python"],
            entities=[("Python", "PRODUCT"), ("machine learning", "WORK_OF_ART")],
            pos_tags=[("I", "PRON"), ("enjoy", "VERB")],
            noun_phrases=["Python programming"],
            sentences=["I enjoy Python"],
            dependencies=[],
            used_fallback=False
        )
        
        # Mock DistilBERT embeddings
        distilbert_service.get_embeddings.return_value = [0.1] * 768
        
        # Mock memory storage
        memory_manager.store_memory.return_value = "stored_memory_id"
        
        # Test preference learning
        learning_result = await memory_processor.learn_user_preferences(
            "user1", conversation_history
        )
        
        # Verify learning results
        assert "learned_patterns" in learning_result
        assert "communication_style" in learning_result["learned_patterns"]
        assert "topic_interests" in learning_result["learned_patterns"]
        assert "interaction_patterns" in learning_result["learned_patterns"]
        
        # Verify communication style detection
        comm_style = learning_result["learned_patterns"]["communication_style"]
        assert "verbose" in comm_style or "concise" in comm_style
        
        # Verify topic interest detection
        topics = learning_result["learned_patterns"]["topic_interests"]
        assert "python" in topics or "machine learning" in topics
        
        # Verify interaction patterns
        interactions = learning_result["learned_patterns"]["interaction_patterns"]
        assert "asks_questions" in interactions
        
        # Verify memories were stored
        assert memory_manager.store_memory.called
        
        # Verify learning metadata
        assert learning_result["total_patterns"] > 0
        assert learning_result["categories_analyzed"] > 0
        assert "learning_timestamp" in learning_result
    
    @pytest.mark.asyncio
    async def test_context_aware_retrieval_scoring(self, memory_processor, mock_services):
        """Test context-aware memory retrieval with enhanced relevance scoring."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Mock parsed query
        parsed_query = ParsedMessage(
            tokens=["What", "do", "I", "like"],
            lemmas=["what", "do", "I", "like"],
            entities=[],
            pos_tags=[],
            noun_phrases=[],
            sentences=["What do I like?"],
            dependencies=[],
            used_fallback=False
        )
        
        # Mock memory retrieval
        mock_memories = [
            MemoryEntry(
                id="mem1",
                content="I like pizza",
                embedding=[0.8] * 768,
                metadata={"type": "preference", "confidence": "high"},
                timestamp=time.time(),
                user_id="user1"
            ),
            MemoryEntry(
                id="mem2",
                content="I like music",
                embedding=[0.7] * 768,
                metadata={"type": "preference", "confidence": "medium"},
                timestamp=time.time() - 86400,
                user_id="user1"
            )
        ]
        
        memory_manager.query_memories.return_value = mock_memories
        
        # Test context retrieval
        context = await memory_processor.get_relevant_context(
            query_embedding=[0.9] * 768,
            parsed_query=parsed_query,
            user_id="user1",
            conversation_id="conv1"
        )
        
        # Verify context structure
        assert isinstance(context, MemoryContext)
        assert len(context.memories) > 0
        assert context.retrieval_time > 0
        assert context.total_memories_considered == 2
        
        # Verify relevance scoring
        for memory in context.memories:
            assert memory.similarity_score > 0
            assert memory.recency_score > 0
            assert memory.combined_score > 0
        
        # Verify memories are sorted by combined score
        scores = [m.combined_score for m in context.memories]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_conversation_context_aggregation(self, memory_processor, sample_relevant_memories):
        """Test conversation context aggregation and summarization."""
        # Test context aggregation
        context = await memory_processor._build_memory_context(sample_relevant_memories)
        
        # Verify aggregation by type
        assert len(context.entities) == 1
        assert len(context.preferences) == 2
        assert len(context.facts) == 1
        assert len(context.relationships) == 0
        
        # Verify each category contains proper data structure
        for entity in context.entities:
            assert "content" in entity
            assert "similarity_score" in entity
            assert "recency_score" in entity
            assert "combined_score" in entity
            assert "metadata" in entity
        
        for preference in context.preferences:
            assert "content" in preference
            assert "metadata" in preference
            assert preference["metadata"].get("preference_type") is not None
        
        # Verify context summary provides meaningful insights
        assert context.context_summary != ""
        assert "Retrieved" in context.context_summary
        
        # Test empty context handling
        empty_context = await memory_processor._build_memory_context([])
        assert empty_context.context_summary == "No relevant context found"
    
    def test_processing_stats_tracking(self, memory_processor):
        """Test that processing statistics are properly tracked."""
        # Get initial stats
        initial_stats = memory_processor.get_processing_stats()
        
        # Verify stats structure
        expected_keys = [
            "extraction_count", "retrieval_count", "deduplication_count",
            "conflict_resolution_count", "similarity_threshold",
            "deduplication_threshold", "max_context_memories", "recency_weight"
        ]
        
        for key in expected_keys:
            assert key in initial_stats
        
        # Verify initial values
        assert initial_stats["extraction_count"] == 0
        assert initial_stats["retrieval_count"] == 0
        assert initial_stats["deduplication_count"] == 0
        assert initial_stats["conflict_resolution_count"] == 0
        
        # Verify configuration values
        assert initial_stats["similarity_threshold"] == 0.7
        assert initial_stats["deduplication_threshold"] == 0.95
        assert initial_stats["max_context_memories"] == 10
        assert initial_stats["recency_weight"] == 0.3
    
    @pytest.mark.asyncio
    async def test_error_handling_in_analytics(self, memory_processor, mock_services):
        """Test error handling in memory analytics."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Mock memory manager to raise exception
        memory_manager.query_memories.side_effect = Exception("Database error")
        
        # Test analytics with error
        analytics = await memory_processor.get_memory_analytics("user1")
        
        # Verify error handling
        assert "error" in analytics
        assert "Database error" in analytics["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_in_preference_learning(self, memory_processor, mock_services):
        """Test error handling in preference learning."""
        spacy_service, distilbert_service, memory_manager = mock_services
        
        # Mock spaCy service to raise exception
        spacy_service.parse_message.side_effect = Exception("Parsing error")
        
        # Test preference learning with error
        result = await memory_processor.learn_user_preferences("user1", ["test message"])
        
        # Verify error handling
        assert "error" in result
        assert "Parsing error" in result["error"]


# Import time for timestamp testing
import time