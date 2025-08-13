"""
Tests for the ContextIntegrator module.

This module tests the enhanced context integration capabilities including
relevance scoring, context summarization, and token-aware context building.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from ai_karen_engine.chat.context_integrator import (
    ContextIntegrator,
    ContextItem,
    ContextType,
    RelevanceScore,
    IntegratedContext
)


class TestContextIntegrator:
    """Test the ContextIntegrator class."""
    
    @pytest.fixture
    def integrator(self):
        """Create a ContextIntegrator instance for testing."""
        return ContextIntegrator(
            max_context_tokens=1000,
            relevance_threshold=0.3
        )
    
    @pytest.fixture
    def sample_raw_context(self):
        """Create sample raw context data."""
        return {
            "memories": [
                {
                    "id": "memory_1",
                    "content": "User prefers detailed explanations with examples",
                    "similarity_score": 0.8,
                    "recency_score": 0.7,
                    "combined_score": 0.75,
                    "type": "preference",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {"importance": "high"}
                },
                {
                    "id": "memory_2",
                    "content": "Previous discussion about machine learning algorithms",
                    "similarity_score": 0.6,
                    "recency_score": 0.5,
                    "combined_score": 0.55,
                    "type": "conversation",
                    "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "metadata": {"topic": "ml"}
                }
            ],
            "entities": [
                {"text": "Python", "label": "LANGUAGE"},
                {"text": "machine learning", "label": "TOPIC"}
            ],
            "preferences": [
                {"content": "Use simple language", "type": "communication"}
            ],
            "facts": [
                {"content": "User is a beginner programmer", "confidence": 0.8, "importance": 0.7}
            ],
            "relationships": [
                {"description": "Python is used for machine learning"}
            ],
            "attachments": {
                "total_files": 2,
                "extracted_content": [
                    {"file_id": "file_1", "content": "Sample code for data analysis"}
                ],
                "multimedia_analysis": [
                    {"file_id": "file_2", "media_type": "image", "basic_analysis": "Chart showing data trends"}
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_extract_context_items(self, integrator, sample_raw_context):
        """Test extraction of context items from raw context."""
        current_message = "Explain Python machine learning libraries"
        
        items = await integrator._extract_context_items(sample_raw_context, current_message)
        
        assert len(items) > 0
        
        # Check that different types of context items are extracted
        item_types = {item.type for item in items}
        assert ContextType.MEMORY in item_types
        assert ContextType.ENTITIES in item_types
        assert ContextType.USER_PREFERENCES in item_types
        assert ContextType.FACTS in item_types
        assert ContextType.RELATIONSHIPS in item_types
        assert ContextType.ATTACHMENTS in item_types
        
        # Check memory items
        memory_items = [item for item in items if item.type == ContextType.MEMORY]
        assert len(memory_items) == 2
        
        # Check that relevance scores are preserved
        memory_1 = next(item for item in memory_items if item.id == "memory_1")
        assert memory_1.relevance_score == 0.8
        assert memory_1.recency_score == 0.7
    
    @pytest.mark.asyncio
    async def test_score_context_items(self, integrator, sample_raw_context):
        """Test scoring of context items for relevance."""
        current_message = "Explain Python machine learning libraries"
        
        items = await integrator._extract_context_items(sample_raw_context, current_message)
        scored_items = await integrator._score_context_items(items, current_message)
        
        # Check that combined scores are calculated
        for item in scored_items:
            assert 0.0 <= item.combined_score <= 1.0
        
        # Items with keywords matching the message should have higher relevance
        python_related_items = [
            item for item in scored_items 
            if "python" in item.content.lower()
        ]
        
        if python_related_items:
            # Should have boosted relevance due to keyword matching
            python_item = python_related_items[0]
            assert python_item.relevance_score > 0.5
    
    @pytest.mark.asyncio
    async def test_integrate_context_full_flow(self, integrator, sample_raw_context):
        """Test the complete context integration flow."""
        current_message = "Explain Python machine learning libraries"
        user_id = "test_user"
        conversation_id = "test_conversation"
        
        integrated_context = await integrator.integrate_context(
            sample_raw_context, current_message, user_id, conversation_id
        )
        
        assert isinstance(integrated_context, IntegratedContext)
        assert integrated_context.primary_context is not None
        assert integrated_context.context_summary is not None
        assert integrated_context.token_count > 0
        assert len(integrated_context.items_included) > 0
        
        # Check that high-relevance items are included
        high_relevance_included = [
            item for item in integrated_context.items_included
            if item.get_relevance_category() in [RelevanceScore.VERY_HIGH, RelevanceScore.HIGH]
        ]
        assert len(high_relevance_included) > 0
    
    @pytest.mark.asyncio
    async def test_token_limit_enforcement(self, integrator):
        """Test that context integration respects token limits."""
        # Create a large amount of context that exceeds token limit
        large_context = {
            "memories": [
                {
                    "id": f"memory_{i}",
                    "content": "This is a very long memory item that contains a lot of text " * 20,
                    "similarity_score": 0.8,
                    "recency_score": 0.7,
                    "combined_score": 0.75,
                    "type": "conversation",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {}
                }
                for i in range(20)  # Create many large memory items
            ]
        }
        
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            large_context, current_message, "user", "conversation"
        )
        
        # Should respect token limit
        assert integrated_context.token_count <= integrator.max_context_tokens
        
        # Should have excluded some items due to token limit
        assert len(integrated_context.items_excluded) > 0
    
    @pytest.mark.asyncio
    async def test_relevance_threshold_filtering(self, integrator):
        """Test that items below relevance threshold are excluded."""
        # Create context with items of varying relevance
        mixed_relevance_context = {
            "memories": [
                {
                    "id": "high_relevance",
                    "content": "Highly relevant content",
                    "similarity_score": 0.9,
                    "recency_score": 0.8,
                    "combined_score": 0.85,
                    "type": "preference",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {}
                },
                {
                    "id": "low_relevance",
                    "content": "Not very relevant content",
                    "similarity_score": 0.05,
                    "recency_score": 0.05,
                    "combined_score": 0.05,
                    "type": "conversation",
                    "created_at": datetime.utcnow().isoformat(),
                    "metadata": {}
                }
            ]
        }
        
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            mixed_relevance_context, current_message, "user", "conversation"
        )
        
        # High relevance item should be included
        included_ids = {item.id for item in integrated_context.items_included}
        assert "high_relevance" in included_ids
        
        # Low relevance item should be excluded
        excluded_ids = {item.id for item in integrated_context.items_excluded}
        assert "low_relevance" in excluded_ids
    
    @pytest.mark.asyncio
    async def test_context_prioritization(self, integrator, sample_raw_context):
        """Test that context items are prioritized correctly."""
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            sample_raw_context, current_message, "user", "conversation"
        )
        
        # Attachments should have high priority and be included
        attachment_items = [
            item for item in integrated_context.items_included
            if item.type == ContextType.ATTACHMENTS
        ]
        assert len(attachment_items) > 0
        
        # Entities should also be prioritized
        entity_items = [
            item for item in integrated_context.items_included
            if item.type == ContextType.ENTITIES
        ]
        assert len(entity_items) > 0
    
    def test_context_item_relevance_categories(self):
        """Test relevance category classification."""
        # Test different relevance scores
        very_high_item = ContextItem(
            id="very_high",
            type=ContextType.MEMORY,
            content="test",
            relevance_score=0.9,
            recency_score=0.8,
            importance_score=0.7,
            combined_score=0.85
        )
        assert very_high_item.get_relevance_category() == RelevanceScore.VERY_HIGH
        
        high_item = ContextItem(
            id="high",
            type=ContextType.MEMORY,
            content="test",
            relevance_score=0.7,
            recency_score=0.6,
            importance_score=0.5,
            combined_score=0.65
        )
        assert high_item.get_relevance_category() == RelevanceScore.HIGH
        
        medium_item = ContextItem(
            id="medium",
            type=ContextType.MEMORY,
            content="test",
            relevance_score=0.5,
            recency_score=0.4,
            importance_score=0.3,
            combined_score=0.45
        )
        assert medium_item.get_relevance_category() == RelevanceScore.MEDIUM
        
        low_item = ContextItem(
            id="low",
            type=ContextType.MEMORY,
            content="test",
            relevance_score=0.3,
            recency_score=0.2,
            importance_score=0.1,
            combined_score=0.25
        )
        assert low_item.get_relevance_category() == RelevanceScore.LOW
        
        very_low_item = ContextItem(
            id="very_low",
            type=ContextType.MEMORY,
            content="test",
            relevance_score=0.1,
            recency_score=0.1,
            importance_score=0.1,
            combined_score=0.1
        )
        assert very_low_item.get_relevance_category() == RelevanceScore.VERY_LOW
    
    @pytest.mark.asyncio
    async def test_primary_context_building(self, integrator, sample_raw_context):
        """Test building of primary context string."""
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            sample_raw_context, current_message, "user", "conversation"
        )
        
        primary_context = integrated_context.primary_context
        
        # Should contain structured sections
        if "CURRENT FILES:" in primary_context:
            assert "file" in primary_context.lower()
        
        if "KEY ENTITIES:" in primary_context:
            assert any(entity in primary_context.lower() for entity in ["python", "machine learning"])
        
        if "RELEVANT CONTEXT:" in primary_context:
            assert len(primary_context) > 0
    
    @pytest.mark.asyncio
    async def test_supporting_context_building(self, integrator, sample_raw_context):
        """Test building of supporting context string."""
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            sample_raw_context, current_message, "user", "conversation"
        )
        
        supporting_context = integrated_context.supporting_context
        
        # Should contain user preferences and facts if they have medium relevance
        if supporting_context:
            # Check for structured sections
            assert isinstance(supporting_context, str)
    
    @pytest.mark.asyncio
    async def test_context_summary_generation(self, integrator, sample_raw_context):
        """Test generation of context summary."""
        current_message = "Test message"
        
        integrated_context = await integrator.integrate_context(
            sample_raw_context, current_message, "user", "conversation"
        )
        
        summary = integrated_context.context_summary
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        # Should mention what types of context are included
        if integrated_context.items_included:
            assert "Context includes:" in summary or "No additional context" in summary
    
    def test_token_estimation(self, integrator):
        """Test token count estimation."""
        short_text = "Hello world"
        long_text = "This is a much longer text that should have more tokens " * 10
        
        short_tokens = integrator._estimate_tokens(short_text)
        long_tokens = integrator._estimate_tokens(long_text)
        
        assert short_tokens > 0
        assert long_tokens > short_tokens
        assert integrator._estimate_tokens("") == 0
    
    @pytest.mark.asyncio
    async def test_empty_context_handling(self, integrator):
        """Test handling of empty or minimal context."""
        empty_context = {}
        minimal_context = {"memories": []}
        
        current_message = "Test message"
        
        # Test empty context
        empty_integrated = await integrator.integrate_context(
            empty_context, current_message, "user", "conversation"
        )
        assert isinstance(empty_integrated, IntegratedContext)
        assert len(empty_integrated.items_included) == 0
        
        # Test minimal context
        minimal_integrated = await integrator.integrate_context(
            minimal_context, current_message, "user", "conversation"
        )
        assert isinstance(minimal_integrated, IntegratedContext)
        assert len(minimal_integrated.items_included) == 0
    
    def test_integrated_context_serialization(self, integrator):
        """Test IntegratedContext serialization."""
        # Create sample context items
        items_included = [
            ContextItem(
                id="item_1",
                type=ContextType.MEMORY,
                content="test content",
                relevance_score=0.8,
                recency_score=0.7,
                importance_score=0.6,
                combined_score=0.7
            )
        ]
        
        items_excluded = [
            ContextItem(
                id="item_2",
                type=ContextType.FACTS,
                content="excluded content",
                relevance_score=0.2,
                recency_score=0.1,
                importance_score=0.1,
                combined_score=0.15
            )
        ]
        
        integrated_context = IntegratedContext(
            primary_context="Primary context text",
            supporting_context="Supporting context text",
            context_summary="Context summary",
            token_count=100,
            items_included=items_included,
            items_excluded=items_excluded,
            relevance_threshold=0.3,
            metadata={"test": "value"}
        )
        
        # Test serialization
        data = integrated_context.to_dict()
        
        assert data["primary_context"] == "Primary context text"
        assert data["supporting_context"] == "Supporting context text"
        assert data["context_summary"] == "Context summary"
        assert data["token_count"] == 100
        assert data["items_included_count"] == 1
        assert data["items_excluded_count"] == 1
        assert data["relevance_threshold"] == 0.3
        assert data["included_by_type"]["memory"] == 1
        assert data["excluded_by_type"]["facts"] == 1
        assert data["metadata"]["test"] == "value"
    
    def test_integration_stats(self, integrator):
        """Test getting integration statistics."""
        stats = integrator.get_integration_stats()
        
        assert "max_context_tokens" in stats
        assert "relevance_threshold" in stats
        assert "scoring_weights" in stats
        
        assert stats["max_context_tokens"] == integrator.max_context_tokens
        assert stats["relevance_threshold"] == integrator.relevance_threshold
        
        weights = stats["scoring_weights"]
        assert "recency" in weights
        assert "relevance" in weights
        assert "importance" in weights
    
    @pytest.mark.asyncio
    async def test_format_entities(self, integrator):
        """Test entity formatting."""
        entities = [
            {"text": "Python", "label": "LANGUAGE"},
            ("machine learning", "TOPIC"),
            {"text": "TensorFlow", "label": "LIBRARY"}
        ]
        
        formatted = integrator._format_entities(entities)
        
        assert "LANGUAGE: Python" in formatted
        assert "TOPIC: machine learning" in formatted
        assert "LIBRARY: TensorFlow" in formatted
        
        # Test empty entities
        empty_formatted = integrator._format_entities([])
        assert empty_formatted == ""
    
    @pytest.mark.asyncio
    async def test_format_attachments(self, integrator):
        """Test attachment formatting."""
        attachments = {
            "total_files": 3,
            "extracted_content": [
                {"file_id": "file_1", "content": "Sample text content for analysis"},
                {"file_id": "file_2", "content": "Another document with important information"}
            ],
            "multimedia_analysis": [
                {"file_id": "file_3", "media_type": "image", "basic_analysis": "Chart data"}
            ]
        }
        
        formatted = integrator._format_attachments(attachments)
        
        assert "3 file(s) attached" in formatted
        assert "File content:" in formatted
        assert "Media files: image" in formatted
        
        # Test empty attachments
        empty_formatted = integrator._format_attachments({})
        assert empty_formatted == ""