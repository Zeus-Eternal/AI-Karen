"""
Unit tests for ContentOptimizationEngine

Tests all content optimization capabilities including:
- Redundancy elimination
- Content relevance analysis
- Content depth adaptation
- Intelligent formatting
- Content synthesis
- Content prioritization
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.ai_karen_engine.services.content_optimization_engine import (
    ContentOptimizationEngine,
    ContentType,
    ExpertiseLevel,
    FormatType,
    Priority,
    ContentSection,
    RelevanceScore,
    Context,
    OptimizedContent
)


class TestContentOptimizationEngine:
    """Test suite for ContentOptimizationEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create ContentOptimizationEngine instance for testing"""
        return ContentOptimizationEngine()
    
    @pytest.fixture
    def sample_context(self):
        """Create sample context for testing"""
        return Context(
            user_id="test_user",
            expertise_level=ExpertiseLevel.INTERMEDIATE,
            query_intent="How to implement authentication",
            previous_queries=["What is JWT", "OAuth basics"],
            domain_knowledge=["web development", "security"],
            preferred_formats=[FormatType.CODE_BLOCK, FormatType.BULLET_POINTS],
            time_constraints=5.0,
            device_type="desktop"
        )
    
    @pytest.fixture
    def redundant_content(self):
        """Sample content with redundancy for testing"""
        return """
        Authentication is important for security. Security is crucial for authentication.
        JWT tokens are used for authentication. JSON Web Tokens (JWT) are authentication tokens.
        You need to implement proper authentication. Proper authentication implementation is necessary.
        """
    
    @pytest.fixture
    def mixed_content(self):
        """Sample mixed content for testing"""
        return """
        # Authentication Implementation
        
        Authentication is the process of verifying user identity.
        
        ```python
        def authenticate_user(username, password):
            # Verify credentials
            return verify_credentials(username, password)
        ```
        
        Steps to implement:
        1. Set up authentication middleware
        2. Configure JWT tokens
        3. Implement login endpoint
        
        | Component | Description |
        |-----------|-------------|
        | JWT | JSON Web Token |
        | OAuth | Open Authorization |
        """

    @pytest.mark.asyncio
    async def test_analyze_content_relevance(self, engine, sample_context):
        """Test content relevance analysis"""
        content = "JWT authentication implementation with OAuth integration"
        
        relevance_score = await engine.analyze_content_relevance(content, sample_context)
        
        assert isinstance(relevance_score, RelevanceScore)
        assert 0.0 <= relevance_score.overall_score <= 1.0
        assert 0.0 <= relevance_score.keyword_relevance <= 1.0
        assert 0.0 <= relevance_score.context_relevance <= 1.0
        assert 0.0 <= relevance_score.user_relevance <= 1.0
        assert 0.0 <= relevance_score.confidence <= 1.0
        
        # Should have high relevance due to matching keywords
        assert relevance_score.keyword_relevance > 0.3
        assert relevance_score.overall_score > 0.4

    @pytest.mark.asyncio
    async def test_eliminate_redundant_content(self, engine, redundant_content):
        """Test redundancy elimination"""
        original_length = len(redundant_content)
        
        optimized_content = await engine.eliminate_redundant_content(redundant_content)
        
        assert len(optimized_content) < original_length
        assert "Authentication is important for security" in optimized_content
        # Should not contain both similar sentences
        assert not ("Security is crucial for authentication" in optimized_content and 
                   "Authentication is important for security" in optimized_content)

    @pytest.mark.asyncio
    async def test_prioritize_content_sections(self, engine, mixed_content, sample_context):
        """Test content section prioritization"""
        sections = await engine.prioritize_content_sections(mixed_content, sample_context)
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        for section in sections:
            assert isinstance(section, ContentSection)
            assert isinstance(section.content_type, ContentType)
            assert isinstance(section.priority, Priority)
            assert 0.0 <= section.relevance_score <= 1.0
            assert isinstance(section.format_type, FormatType)
        
        # Sections should be sorted by priority
        priorities = [section.priority.value for section in sections]
        assert priorities == sorted(priorities)

    @pytest.mark.asyncio
    async def test_optimize_formatting_code_block(self, engine):
        """Test code block formatting optimization"""
        code_content = "def authenticate_user(username, password):\n    return verify_credentials(username, password)"
        
        formatted = await engine.optimize_formatting(code_content, FormatType.CODE_BLOCK)
        
        assert formatted.startswith("```")
        assert formatted.endswith("```")
        assert code_content in formatted

    @pytest.mark.asyncio
    async def test_optimize_formatting_bullet_points(self, engine):
        """Test bullet point formatting optimization"""
        list_content = "First step\nSecond step\nThird step"
        
        formatted = await engine.optimize_formatting(list_content, FormatType.BULLET_POINTS)
        
        lines = formatted.split('\n')
        for line in lines:
            if line.strip():
                assert line.strip().startswith('- ')

    @pytest.mark.asyncio
    async def test_adapt_content_depth_beginner(self, engine, sample_context):
        """Test content depth adaptation for beginners"""
        technical_content = "Implement JWT authentication with OAuth2 flow"
        beginner_context = Context(expertise_level=ExpertiseLevel.BEGINNER)
        
        adapted = await engine.adapt_content_depth(technical_content, ExpertiseLevel.BEGINNER, beginner_context)
        
        # Should contain more explanatory content for beginners
        assert len(adapted) >= len(technical_content)

    @pytest.mark.asyncio
    async def test_adapt_content_depth_expert(self, engine, sample_context):
        """Test content depth adaptation for experts"""
        detailed_content = "JWT (JSON Web Token) is a compact, URL-safe means of representing claims to be transferred between two parties"
        expert_context = Context(expertise_level=ExpertiseLevel.EXPERT)
        
        adapted = await engine.adapt_content_depth(detailed_content, ExpertiseLevel.EXPERT, expert_context)
        
        # Should be more concise for experts
        assert len(adapted) <= len(detailed_content)

    @pytest.mark.asyncio
    async def test_synthesize_content_from_sources(self, engine, sample_context):
        """Test content synthesis from multiple sources"""
        sources = [
            {
                'id': 'source1',
                'content': 'JWT authentication is secure and stateless'
            },
            {
                'id': 'source2', 
                'content': 'OAuth provides authorization framework for web applications'
            },
            {
                'id': 'source3',
                'content': 'JWT authentication is secure and stateless'  # Duplicate
            }
        ]
        
        synthesized = await engine.synthesize_content_from_sources(sources, sample_context)
        
        assert isinstance(synthesized, str)
        assert len(synthesized) > 0
        # Should contain content from multiple sources
        assert 'JWT' in synthesized or 'OAuth' in synthesized
        # Should not contain exact duplicates
        assert synthesized.count('JWT authentication is secure and stateless') <= 1

    @pytest.mark.asyncio
    async def test_optimize_content_full_pipeline(self, engine, mixed_content, sample_context):
        """Test full content optimization pipeline"""
        optimized = await engine.optimize_content(mixed_content, sample_context)
        
        assert isinstance(optimized, OptimizedContent)
        assert isinstance(optimized.sections, list)
        assert len(optimized.sections) > 0
        assert optimized.total_length > 0
        assert optimized.estimated_read_time > 0
        assert len(optimized.optimization_applied) > 0
        assert optimized.redundancy_removed >= 0
        assert optimized.relevance_improved >= 0.0
        assert isinstance(optimized.format_optimized, bool)

    def test_extract_keywords(self, engine):
        """Test keyword extraction"""
        text = "JWT authentication with OAuth2 implementation"
        keywords = engine._extract_keywords(text)
        
        assert isinstance(keywords, set)
        assert 'jwt' in keywords
        assert 'authentication' in keywords
        assert 'oauth2' in keywords
        assert 'implementation' in keywords
        # Should not contain stop words
        assert 'with' not in keywords

    def test_calculate_text_similarity(self, engine):
        """Test text similarity calculation"""
        text1 = "JWT authentication is secure"
        text2 = "JWT authentication provides security"
        text3 = "OAuth authorization framework"
        
        similarity_high = engine._calculate_text_similarity(text1, text2)
        similarity_low = engine._calculate_text_similarity(text1, text3)
        
        assert 0.0 <= similarity_high <= 1.0
        assert 0.0 <= similarity_low <= 1.0
        assert similarity_high > similarity_low

    def test_detect_content_type_code(self, engine):
        """Test code content type detection"""
        code_content = "```python\ndef authenticate_user():\n    pass\n```"
        content_type = engine._detect_content_type(code_content)
        assert content_type == ContentType.CODE

    def test_detect_content_type_list(self, engine):
        """Test list content type detection"""
        list_content = "- First item\n- Second item\n- Third item"
        content_type = engine._detect_content_type(list_content)
        assert content_type == ContentType.LIST

    def test_detect_content_type_technical(self, engine):
        """Test technical content type detection"""
        technical_content = "The API function returns a JSON response"
        content_type = engine._detect_content_type(technical_content)
        assert content_type == ContentType.TECHNICAL

    def test_determine_priority_critical(self, engine):
        """Test critical priority determination"""
        high_actionability_score = RelevanceScore(
            overall_score=0.9,
            keyword_relevance=0.8,
            context_relevance=0.9,
            user_relevance=0.8,
            freshness_score=1.0,
            actionability_score=0.8,
            confidence=0.9
        )
        
        priority = engine._determine_priority(
            high_actionability_score, 
            ContentType.CODE, 
            "Run this command to install"
        )
        
        assert priority == Priority.CRITICAL

    def test_determine_optimal_format(self, engine):
        """Test optimal format determination"""
        code_format = engine._determine_optimal_format("def func():", ContentType.CODE)
        assert code_format == FormatType.CODE_BLOCK
        
        list_format = engine._determine_optimal_format("- item 1", ContentType.LIST)
        assert list_format == FormatType.BULLET_POINTS
        
        table_format = engine._determine_optimal_format("| col1 | col2 |", ContentType.TABLE)
        assert table_format == FormatType.TABLE

    def test_is_actionable_content(self, engine):
        """Test actionable content detection"""
        actionable = "Follow these steps to install the package"
        non_actionable = "This is a general description of the concept"
        
        assert engine._is_actionable_content(actionable) == True
        assert engine._is_actionable_content(non_actionable) == False

    def test_estimate_read_time(self, engine):
        """Test reading time estimation"""
        short_text = "Short text"
        long_text = " ".join(["word"] * 200)  # 200 words
        
        short_time = engine._estimate_read_time(short_text)
        long_time = engine._estimate_read_time(long_text)
        
        assert short_time < long_time
        assert long_time == 1.0  # 200 words / 200 wpm = 1 minute

    def test_format_as_code_block(self, engine):
        """Test code block formatting"""
        code = "print('hello')"
        formatted = engine._format_as_code_block(code)
        
        assert formatted.startswith("```")
        assert formatted.endswith("```")
        assert code in formatted

    def test_format_as_bullet_points(self, engine):
        """Test bullet point formatting"""
        text = "First point\nSecond point"
        formatted = engine._format_as_bullet_points(text)
        
        lines = formatted.split('\n')
        for line in lines:
            if line.strip():
                assert line.startswith('- ')

    def test_format_as_table(self, engine):
        """Test table formatting"""
        text = "Key1: Value1\nKey2: Value2"
        formatted = engine._format_as_table(text)
        
        assert '|' in formatted
        assert 'Key' in formatted
        assert 'Value' in formatted

    @pytest.mark.asyncio
    async def test_error_handling_analyze_relevance(self, engine):
        """Test error handling in relevance analysis"""
        # Test with None context
        with patch.object(engine, '_extract_keywords', side_effect=Exception("Test error")):
            relevance = await engine.analyze_content_relevance("test content", Context())
            
            # Should return default values on error
            assert isinstance(relevance, RelevanceScore)
            assert relevance.confidence == 0.1

    @pytest.mark.asyncio
    async def test_error_handling_eliminate_redundancy(self, engine):
        """Test error handling in redundancy elimination"""
        with patch.object(engine, '_split_into_sentences', side_effect=Exception("Test error")):
            result = await engine.eliminate_redundant_content("test content")
            
            # Should return original content on error
            assert result == "test content"

    @pytest.mark.asyncio
    async def test_error_handling_optimize_content(self, engine, sample_context):
        """Test error handling in full optimization"""
        with patch.object(engine, 'eliminate_redundant_content', side_effect=Exception("Test error")):
            result = await engine.optimize_content("test content", sample_context)
            
            # Should return fallback optimization
            assert isinstance(result, OptimizedContent)
            assert "error_fallback" in result.optimization_applied

    def test_calculate_context_relevance(self, engine):
        """Test context relevance calculation"""
        content = "web development authentication security"
        context = Context(
            domain_knowledge=["web development", "security"],
            previous_queries=["authentication basics"]
        )
        
        relevance = engine._calculate_context_relevance(content, context)
        
        assert 0.0 <= relevance <= 1.0
        assert relevance > 0.5  # Should be high due to domain knowledge match

    def test_calculate_user_relevance_beginner(self, engine):
        """Test user relevance for beginner"""
        technical_content = "API SDK JSON implementation algorithm"
        relevance = engine._calculate_user_relevance(technical_content, ExpertiseLevel.BEGINNER)
        
        assert 0.0 <= relevance <= 1.0
        # Should be lower for beginners with technical content
        assert relevance < 0.8

    def test_calculate_user_relevance_expert(self, engine):
        """Test user relevance for expert"""
        technical_content = "API SDK JSON implementation algorithm"
        relevance = engine._calculate_user_relevance(technical_content, ExpertiseLevel.EXPERT)
        
        assert 0.0 <= relevance <= 1.0
        # Should be higher for experts with technical content
        assert relevance > 0.5

    def test_calculate_actionability_score(self, engine):
        """Test actionability score calculation"""
        actionable_content = "Follow these steps: 1. Install package 2. Run command ```npm install```"
        non_actionable_content = "This is a theoretical discussion about concepts"
        
        actionable_score = engine._calculate_actionability_score(actionable_content)
        non_actionable_score = engine._calculate_actionability_score(non_actionable_content)
        
        assert 0.0 <= actionable_score <= 1.0
        assert 0.0 <= non_actionable_score <= 1.0
        assert actionable_score > non_actionable_score

    def test_remove_redundant_phrases(self, engine):
        """Test redundant phrase removal"""
        redundant_text = "In other words, basically, this is important to note that we should proceed"
        cleaned = engine._remove_redundant_phrases(redundant_text)
        
        assert "in other words" not in cleaned.lower()
        assert "basically" not in cleaned.lower()
        assert "important to note" not in cleaned.lower()

    def test_split_into_sections(self, engine):
        """Test content section splitting"""
        content = "Section 1\n\nSection 2\n\n## Header\nSection 3"
        sections = engine._split_into_sections(content)
        
        assert isinstance(sections, list)
        assert len(sections) >= 2
        assert all(section.strip() for section in sections)

    def test_extract_tags(self, engine):
        """Test tag extraction"""
        technical_content = "This code function shows an API example"
        tutorial_content = "Follow this step-by-step tutorial guide"
        reference_content = "See the API documentation reference"
        
        tech_tags = engine._extract_tags(technical_content)
        tutorial_tags = engine._extract_tags(tutorial_content)
        ref_tags = engine._extract_tags(reference_content)
        
        assert 'technical' in tech_tags
        assert 'tutorial' in tutorial_tags
        assert 'reference' in ref_tags

    def test_content_adaptation_methods(self, engine):
        """Test various content adaptation methods"""
        content = "API authentication with JWT tokens"
        
        # Test detailed explanations
        detailed = engine._add_detailed_explanations(content)
        assert "Application Programming Interface" in detailed
        
        # Test excessive detail removal
        detailed_content = "API (Application Programming Interface) authentication"
        simplified = engine._remove_excessive_detail(detailed_content)
        assert len(simplified) < len(detailed_content)
        
        # Test complexity limiting
        complex_content = "This is a very complex sentence with many technical terms like API SDK JSON XML HTTP REST GraphQL OAuth JWT that exceeds the complexity threshold"
        limited = engine._limit_complexity(complex_content, 5)
        assert len(limited) <= len(complex_content)

    def test_combine_sections_coherently(self, engine):
        """Test coherent section combination"""
        sections = [
            ContentSection(
                content="This is explanatory text",
                content_type=ContentType.TEXT,
                priority=Priority.MEDIUM,
                relevance_score=0.7,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.PLAIN_TEXT
            ),
            ContentSection(
                content="def example(): pass",
                content_type=ContentType.CODE,
                priority=Priority.HIGH,
                relevance_score=0.8,
                expertise_level=ExpertiseLevel.INTERMEDIATE,
                format_type=FormatType.CODE_BLOCK
            )
        ]
        
        combined = engine._combine_sections_coherently(sections)
        
        assert isinstance(combined, str)
        assert len(combined) > 0
        assert "Code Examples" in combined  # Should add section headers
        assert sections[0].content in combined
        assert sections[1].content in combined


if __name__ == "__main__":
    pytest.main([__file__])