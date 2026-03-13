"""
Unit tests for content type detection service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base import ContentType, ResponseContext
from content_detector import (
    ContentTypeDetector,
    ContentDetectionResult
)


class TestContentTypeDetector:
    """Test the content type detector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ContentTypeDetector()
    
    @pytest.mark.asyncio
    async def test_detect_movie_content(self):
        """Test detecting movie content."""
        query = "Tell me about the movie Inception"
        response = "Inception is a 2010 sci-fi film directed by Christopher Nolan, starring Leonardo DiCaprio. The movie has an IMDB rating of 8.8/10."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert isinstance(result, ContentDetectionResult)
        assert result.content_type == ContentType.MOVIE
        assert result.confidence > 0.3
        assert "movie" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_recipe_content(self):
        """Test detecting recipe content."""
        query = "How do I make pasta?"
        response = "Here's a simple pasta recipe: Ingredients: 1 cup pasta, 2 tbsp olive oil, salt. Cook pasta for 10 minutes in boiling water."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.RECIPE
        assert result.confidence > 0.3
        assert "recipe" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_weather_content(self):
        """Test detecting weather content."""
        query = "What's the weather like today?"
        response = "Today's weather: 75°F, sunny with light winds. Humidity is 45%. Tomorrow's forecast shows rain with temperatures dropping to 65°F."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.WEATHER
        assert result.confidence > 0.3
        assert "weather" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_news_content(self):
        """Test detecting news content."""
        query = "What's the latest news?"
        response = "Breaking news: According to sources, the latest report published today shows significant developments in technology sector."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.NEWS
        assert result.confidence > 0.3
        assert "news" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_product_content(self):
        """Test detecting product content."""
        query = "Show me laptops under $1000"
        response = "Here are some laptops under $1000: MacBook Air - $999, Dell XPS - $899. Both have excellent reviews and ratings. You can buy them from Amazon."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.PRODUCT
        assert result.confidence > 0.3
        assert "product" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_travel_content(self):
        """Test detecting travel content."""
        query = "Plan a trip to Paris"
        response = "Here's your Paris travel itinerary: Visit the Eiffel Tower, book a hotel near the Louvre, check flight prices. Don't forget your passport!"
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.TRAVEL
        assert result.confidence > 0.3
        assert "travel" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_code_content(self):
        """Test detecting code content."""
        query = "How do I write a Python function?"
        response = "Here's a Python function example:\n```python\ndef hello_world():\n    return 'Hello, World!'\n```\nThis function returns a string."
        
        result = await self.detector.detect_content_type(query, response)
        
        assert result.content_type == ContentType.CODE
        assert result.confidence > 0.3
        assert "code" in result.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_detect_default_content(self):
        """Test detecting default content type."""
        query = "What is the meaning of life?"
        response = "The meaning of life is a philosophical question that has been pondered for centuries."
        
        result = await self.detector.detect_content_type(query, response)
        
        # Should fall back to default for ambiguous content
        assert result.content_type == ContentType.DEFAULT
        assert result.confidence <= 0.3
    
    @pytest.mark.asyncio
    async def test_detect_with_nlp_analysis(self):
        """Test detection with NLP analysis available."""
        
        # Mock NLP service
        mock_nlp_manager = Mock()
        mock_spacy_service = Mock()
        mock_parsed_message = Mock()
        mock_parsed_message.entities = [Mock(label_="WORK_OF_ART")]
        
        mock_spacy_service.parse_message = AsyncMock(return_value=mock_parsed_message)
        mock_spacy_service.get_linguistic_features = AsyncMock(return_value={
            'keywords': ['movie', 'film', 'director']
        })
        
        mock_nlp_manager.spacy_service = mock_spacy_service
        
        with patch('content_detector.nlp_service_manager', mock_nlp_manager):
            query = "Tell me about Inception"
            response = "Inception is a movie directed by Christopher Nolan"
            
            result = await self.detector.detect_content_type(query, response)
            
            assert result.content_type == ContentType.MOVIE
            assert result.confidence > 0.3
            assert len(result.detected_entities) > 0
            assert len(result.keywords) > 0
    
    @pytest.mark.asyncio
    async def test_detect_with_nlp_unavailable(self):
        """Test detection when NLP services are unavailable."""
        
        with patch('content_detector.nlp_service_manager', side_effect=ImportError("NLP not available")):
            query = "What's the weather?"
            response = "It's 75°F and sunny today"
            
            result = await self.detector.detect_content_type(query, response)
            
            # Should still work with pattern-based detection
            assert result.content_type == ContentType.WEATHER
            assert result.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_detect_error_handling(self):
        """Test error handling in detection."""
        
        # Mock an error in NLP analysis
        with patch.object(self.detector, '_get_nlp_analysis', side_effect=Exception("NLP error")):
            query = "test query"
            response = "test response"
            
            result = await self.detector.detect_content_type(query, response)
            
            # Should return default type on error
            assert result.content_type == ContentType.DEFAULT
            assert "Detection failed" in result.reasoning
    
    def test_calculate_content_score(self):
        """Test content score calculation."""
        text = "This is a movie about actors and directors with great ratings"
        patterns = self.detector._content_patterns[ContentType.MOVIE]
        entities = ["PERSON", "WORK_OF_ART"]
        keywords = ["movie", "film"]
        
        score = self.detector._calculate_content_score(text, patterns, entities, keywords)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some score due to keyword matches
    
    def test_generate_reasoning(self):
        """Test reasoning generation."""
        content_type = ContentType.MOVIE
        text = "movie about actors"
        entities = ["PERSON"]
        keywords = ["movie", "film"]
        
        reasoning = self.detector._generate_reasoning(content_type, text, entities, keywords)
        
        assert "movie content" in reasoning
        assert "Keywords:" in reasoning
        assert "Entities:" in reasoning
    
    def test_generate_reasoning_default(self):
        """Test reasoning for default content type."""
        reasoning = self.detector._generate_reasoning(ContentType.DEFAULT, "text", [], [])
        
        assert "No specific content type detected" in reasoning
        assert "default formatting" in reasoning
    
    def test_get_supported_content_types(self):
        """Test getting supported content types."""
        supported_types = self.detector.get_supported_content_types()
        
        assert ContentType.MOVIE in supported_types
        assert ContentType.RECIPE in supported_types
        assert ContentType.WEATHER in supported_types
        assert ContentType.NEWS in supported_types
        assert ContentType.PRODUCT in supported_types
        assert ContentType.TRAVEL in supported_types
        assert ContentType.CODE in supported_types
        assert ContentType.DEFAULT in supported_types
    
    def test_get_detection_stats(self):
        """Test getting detection statistics."""
        stats = self.detector.get_detection_stats()
        
        assert "supported_types" in stats
        assert "pattern_counts" in stats
        
        # Check that all content types are represented
        for content_type in [ContentType.MOVIE, ContentType.RECIPE, ContentType.WEATHER]:
            assert content_type.value in stats["supported_types"]
            assert content_type.value in stats["pattern_counts"]
            
            pattern_info = stats["pattern_counts"][content_type.value]
            assert "keywords" in pattern_info
            assert "patterns" in pattern_info
            assert "entities" in pattern_info
            assert pattern_info["keywords"] > 0
            assert pattern_info["patterns"] > 0


class TestContentDetectionResult:
    """Test the ContentDetectionResult data class."""
    
    def test_initialization(self):
        """Test ContentDetectionResult initialization."""
        result = ContentDetectionResult(
            content_type=ContentType.MOVIE,
            confidence=0.85,
            reasoning="Detected movie keywords",
            detected_entities=["PERSON", "WORK_OF_ART"],
            keywords=["movie", "film", "actor"]
        )
        
        assert result.content_type == ContentType.MOVIE
        assert result.confidence == 0.85
        assert result.reasoning == "Detected movie keywords"
        assert result.detected_entities == ["PERSON", "WORK_OF_ART"]
        assert result.keywords == ["movie", "film", "actor"]