"""
Unit tests for the Advanced Formatting Engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.ai_karen_engine.services.advanced_formatting_engine import (
    AdvancedFormattingEngine,
    FormattingContext,
    ContentSection,
    FormattedResponse,
    NavigationAid,
    FormatType,
    ContentType,
    AccessibilityLevel,
    DisplayContext
)


class TestAdvancedFormattingEngine:
    """Test cases for AdvancedFormattingEngine."""
    
    @pytest.fixture
    def formatting_engine(self):
        """Create a formatting engine instance for testing."""
        return AdvancedFormattingEngine()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """# Introduction
This is a sample document with various content types.

## Code Example
Here's a Python function:

```python
def hello_world():
    print("Hello, World!")
    return True
```

## Data Table
| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |

## List Items
- First item
- Second item
- Third item

This document contains mixed content types for testing.
"""
    
    @pytest.fixture
    def formatting_context(self):
        """Create a formatting context for testing."""
        return FormattingContext(
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.BASIC,
            user_preferences={},
            content_length=500,
            technical_level="intermediate",
            language="en"
        )
    
    @pytest.mark.asyncio
    async def test_analyze_content_structure(self, formatting_engine, sample_content):
        """Test content structure analysis."""
        analysis = await formatting_engine.analyze_content_structure(sample_content)
        
        assert isinstance(analysis, dict)
        assert 'content_type' in analysis
        assert 'complexity' in analysis
        assert 'sections' in analysis
        assert 'code_blocks' in analysis
        assert 'data_structures' in analysis
        assert 'length' in analysis
        assert 'reading_time' in analysis
        assert 'technical_density' in analysis
        
        # Check that code blocks were detected
        assert len(analysis['code_blocks']) > 0
        assert analysis['code_blocks'][0]['language'] == 'python'
        
        # Check that sections were identified
        assert len(analysis['sections']) > 0
        
        # Check content type detection
        assert analysis['content_type'] in [ContentType.MIXED, ContentType.TECHNICAL, ContentType.CODE]
    
    def test_detect_content_type(self, formatting_engine):
        """Test content type detection."""
        # Test code content
        code_content = "```python\ndef test(): pass\n```\n```javascript\nfunction test() {}\n```"
        content_type = formatting_engine._detect_content_type(code_content)
        assert content_type == ContentType.CODE
        
        # Test technical content
        technical_content = "This API function implements the algorithm for database optimization."
        content_type = formatting_engine._detect_content_type(technical_content)
        assert content_type == ContentType.TECHNICAL
        
        # Test instructional content
        instructional_content = "First, open the file. Then, edit the content. Finally, save the changes."
        content_type = formatting_engine._detect_content_type(instructional_content)
        assert content_type == ContentType.INSTRUCTIONAL
        
        # Test plain narrative content
        narrative_content = "This is a simple story about a person who went to the store."
        content_type = formatting_engine._detect_content_type(narrative_content)
        assert content_type == ContentType.NARRATIVE
    
    def test_assess_complexity(self, formatting_engine):
        """Test complexity assessment."""
        # Simple content
        simple_content = "Hello world. This is simple."
        complexity = formatting_engine._assess_complexity(simple_content)
        assert complexity == 'simple'
        
        # Complex content
        complex_content = """
        This is a very long and complex sentence that contains multiple clauses and technical terminology.
        It also includes several code blocks and multiple headings.
        
        # Heading 1
        ## Heading 2
        ### Heading 3
        
        ```python
        def complex_function():
            pass
        ```
        
        ```javascript
        function another_function() {}
        ```
        
        The complexity increases with more technical content and structural elements.
        """
        complexity = formatting_engine._assess_complexity(complex_content)
        assert complexity in ['moderate', 'complex']
    
    def test_extract_code_blocks(self, formatting_engine):
        """Test code block extraction."""
        content_with_code = """
        Here's some Python code:
        
        ```python
        def hello():
            print("Hello")
            return True
        ```
        
        And some JavaScript:
        
        ```javascript
        function greet() {
            console.log("Hello");
        }
        ```
        """
        
        code_blocks = formatting_engine._extract_code_blocks(content_with_code)
        
        assert len(code_blocks) == 2
        assert code_blocks[0]['language'] == 'python'
        assert code_blocks[1]['language'] == 'javascript'
        assert 'def hello' in code_blocks[0]['code']
        assert 'function greet' in code_blocks[1]['code']
    
    def test_identify_data_structures(self, formatting_engine):
        """Test data structure identification."""
        content_with_data = """
        Here's a table:
        | Name | Age |
        |------|-----|
        | John | 25  |
        | Jane | 30  |
        
        And a list:
        - Item 1
        - Item 2
        - Item 3
        - Item 4
        
        And a numbered list:
        1. First step
        2. Second step
        3. Third step
        """
        
        data_structures = formatting_engine._identify_data_structures(content_with_data)
        
        # Should find table and lists
        types_found = [ds['type'] for ds in data_structures]
        assert 'table' in types_found
        assert 'list' in types_found
    
    def test_estimate_reading_time(self, formatting_engine):
        """Test reading time estimation."""
        # Short content (should be 1 minute minimum)
        short_content = "Hello world."
        reading_time = formatting_engine._estimate_reading_time(short_content)
        assert reading_time == 1
        
        # Longer content (approximately 225 words should be 1 minute)
        long_content = " ".join(["word"] * 450)  # 450 words
        reading_time = formatting_engine._estimate_reading_time(long_content)
        assert reading_time == 2  # Should be about 2 minutes
    
    def test_calculate_technical_density(self, formatting_engine):
        """Test technical density calculation."""
        # Non-technical content
        simple_content = "This is a simple story about everyday life."
        density = formatting_engine._calculate_technical_density(simple_content)
        assert density == 0.0
        
        # Technical content
        technical_content = "This API function implements the algorithm using a class method."
        density = formatting_engine._calculate_technical_density(technical_content)
        assert density > 0.0
    
    @pytest.mark.asyncio
    async def test_select_optimal_format(self, formatting_engine, formatting_context):
        """Test optimal format selection."""
        # Code content should select CODE_BLOCK format
        code_content = "```python\ndef test(): pass\n```\n```javascript\nfunction test() {}\n```"
        format_type = await formatting_engine.select_optimal_format(code_content, formatting_context)
        assert format_type == FormatType.CODE_BLOCK
        
        # Terminal context should select PLAIN_TEXT
        terminal_context = FormattingContext(display_context=DisplayContext.TERMINAL)
        format_type = await formatting_engine.select_optimal_format("Any content", terminal_context)
        assert format_type == FormatType.PLAIN_TEXT
        
        # API context should select STRUCTURED
        api_context = FormattingContext(display_context=DisplayContext.API)
        format_type = await formatting_engine.select_optimal_format("Any content", api_context)
        assert format_type == FormatType.STRUCTURED
    
    @pytest.mark.asyncio
    async def test_organize_content_hierarchically(self, formatting_engine, sample_content):
        """Test hierarchical content organization."""
        sections = await formatting_engine.organize_content_hierarchically(sample_content)
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Check that sections are ContentSection objects
        for section in sections:
            assert isinstance(section, ContentSection)
            assert hasattr(section, 'content')
            assert hasattr(section, 'section_type')
            assert hasattr(section, 'priority')
        
        # Check that sections are sorted by priority (higher first)
        priorities = [section.priority for section in sections]
        assert priorities == sorted(priorities, reverse=True)
    
    @pytest.mark.asyncio
    async def test_apply_syntax_highlighting(self, formatting_engine):
        """Test syntax highlighting application."""
        python_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        
        highlighted = await formatting_engine.apply_syntax_highlighting(python_code, 'python')
        
        # Should contain HTML spans for highlighting
        assert '<span class="keyword">def</span>' in highlighted
        assert '<span class="builtin">print</span>' in highlighted
        assert '<span class="string">"Hello, World!"</span>' in highlighted
        
        # Test unsupported language (should return original)
        original_code = "some code"
        highlighted = await formatting_engine.apply_syntax_highlighting(original_code, 'unsupported')
        assert highlighted == original_code
    
    @pytest.mark.asyncio
    async def test_create_navigation_aids(self, formatting_engine, formatting_context):
        """Test navigation aids creation."""
        # Create sections with headings
        sections = [
            ContentSection(
                content="# Introduction",
                section_type=ContentType.TEXT,
                navigation_id="section_0"
            ),
            ContentSection(
                content="## Getting Started",
                section_type=ContentType.TEXT,
                navigation_id="section_1"
            ),
            ContentSection(
                content="### Installation",
                section_type=ContentType.TEXT,
                navigation_id="section_2"
            ),
            ContentSection(
                content="Regular content here",
                section_type=ContentType.TEXT
            )
        ]
        
        navigation_aids = await formatting_engine.create_navigation_aids(sections, formatting_context)
        
        assert isinstance(navigation_aids, list)
        
        # Should create table of contents for multiple headings
        toc_aids = [aid for aid in navigation_aids if aid.type == "toc"]
        assert len(toc_aids) > 0
        
        toc = toc_aids[0]
        assert len(toc.links) == 3  # Three headings
        assert toc.position == "top"
    
    def test_generate_table_of_contents(self, formatting_engine):
        """Test table of contents generation."""
        headings = [
            ContentSection(
                content="# Introduction",
                section_type=ContentType.TEXT,
                navigation_id="intro",
                metadata={'level': 1}
            ),
            ContentSection(
                content="## Getting Started",
                section_type=ContentType.TEXT,
                navigation_id="getting-started",
                metadata={'level': 2}
            )
        ]
        
        toc = formatting_engine._generate_table_of_contents(headings)
        
        assert "## Table of Contents" in toc
        assert "Introduction" in toc
        assert "Getting Started" in toc
        assert "#intro" in toc
        assert "#getting-started" in toc
    
    def test_generate_content_summary(self, formatting_engine):
        """Test content summary generation."""
        sections = [
            ContentSection(content="Text content", section_type=ContentType.TEXT),
            ContentSection(content="Code content", section_type=ContentType.CODE),
            ContentSection(content="Data content", section_type=ContentType.DATA),
            ContentSection(content="More text", section_type=ContentType.TEXT)
        ]
        
        summary = formatting_engine._generate_content_summary(sections)
        
        assert "## Summary" in summary
        assert "2 explanatory sections" in summary
        assert "1 code examples" in summary
        assert "1 data structures" in summary
        assert "Estimated reading time" in summary
    
    def test_generate_code_description(self, formatting_engine):
        """Test code description generation for accessibility."""
        code_with_functions = """
def hello():
    print("Hello")

class MyClass:
    def method(self):
        for i in range(10):
            if i > 5:
                break
"""
        
        description = formatting_engine._generate_code_description(code_with_functions)
        
        assert "Code block" in description
        assert "function" in description
        assert "class" in description
        assert "loop" in description
        assert "conditional" in description
    
    def test_assess_reading_level(self, formatting_engine):
        """Test reading level assessment."""
        # Basic content
        basic_content = "This is simple. Easy to read. Short sentences."
        level = formatting_engine._assess_reading_level(basic_content)
        assert level == "basic"
        
        # Advanced content
        advanced_content = """
        This is a highly complex sentence with multiple subordinate clauses and advanced technical terminology including implementation details, algorithmic optimization strategies, and architectural configuration parameters that require significant expertise to understand.
        """
        level = formatting_engine._assess_reading_level(advanced_content)
        assert level == "advanced"
    
    @pytest.mark.asyncio
    async def test_add_accessibility_features(self, formatting_engine, formatting_context):
        """Test accessibility features addition."""
        # Create a response with code sections
        response = FormattedResponse(
            content="Test content",
            format_type=FormatType.MARKDOWN,
            sections=[
                ContentSection(
                    content="def test(): pass",
                    section_type=ContentType.CODE,
                    navigation_id="code_1"
                )
            ],
            navigation_aids=[],
            accessibility_features={},
            metadata={'technical_density': 0.5}
        )
        
        # Test enhanced accessibility
        enhanced_context = FormattingContext(accessibility_level=AccessibilityLevel.ENHANCED)
        features = await formatting_engine.add_accessibility_features(response, enhanced_context)
        
        assert isinstance(features, dict)
        assert 'reading_level' in features
        assert 'content_warning' in features  # High technical density should trigger warning
        
        # Test full accessibility
        full_context = FormattingContext(accessibility_level=AccessibilityLevel.FULL)
        features = await formatting_engine.add_accessibility_features(response, full_context)
        
        assert 'screen_reader_text' in features
        assert 'keyboard_navigation' in features
    
    def test_format_for_mobile(self, formatting_engine):
        """Test mobile formatting."""
        response = FormattedResponse(
            content="Test content",
            format_type=FormatType.MARKDOWN,
            sections=[
                ContentSection(
                    content="def very_long_function_name_that_exceeds_mobile_width(): pass",
                    section_type=ContentType.CODE,
                    metadata={'language': 'python'}
                )
            ],
            navigation_aids=[
                NavigationAid(
                    type="toc",
                    content="Table of Contents",
                    links=[{"text": "Section 1", "id": "s1"}] * 10  # Many links
                )
            ],
            accessibility_features={},
            metadata={}
        )
        
        mobile_formatted = formatting_engine._format_for_mobile(response)
        
        assert "📋 **Quick Navigation**" in mobile_formatted
        assert "... and 5 more sections" in mobile_formatted  # Should truncate long TOC
        assert "```python" in mobile_formatted
    
    def test_format_for_terminal(self, formatting_engine):
        """Test terminal formatting."""
        response = FormattedResponse(
            content="Test content",
            format_type=FormatType.MARKDOWN,
            sections=[
                ContentSection(
                    content="# Header",
                    section_type=ContentType.TEXT,
                    navigation_id="header"
                ),
                ContentSection(
                    content="def test(): pass",
                    section_type=ContentType.CODE
                )
            ],
            navigation_aids=[],
            accessibility_features={},
            metadata={}
        )
        
        terminal_formatted = formatting_engine._format_for_terminal(response)
        
        assert "=" * 60 in terminal_formatted  # Header border
        assert "RESPONSE" in terminal_formatted
        assert "┌" in terminal_formatted  # Code block border
        assert "│" in terminal_formatted
        assert "└" in terminal_formatted
    
    def test_format_for_api(self, formatting_engine):
        """Test API formatting (JSON output)."""
        response = FormattedResponse(
            content="Test content",
            format_type=FormatType.MARKDOWN,
            sections=[
                ContentSection(
                    content="Test section",
                    section_type=ContentType.TEXT,
                    priority=5,
                    metadata={'test': 'value'}
                )
            ],
            navigation_aids=[
                NavigationAid(
                    type="toc",
                    content="TOC",
                    links=[{"text": "Link", "id": "link1"}]
                )
            ],
            accessibility_features={'test_feature': True},
            metadata={'test_meta': 'value'},
            estimated_reading_time=2
        )
        
        api_formatted = formatting_engine._format_for_api(response)
        
        # Should be valid JSON
        import json
        parsed = json.loads(api_formatted)
        
        assert parsed['content'] == "Test content"
        assert parsed['format_type'] == "markdown"
        assert len(parsed['sections']) == 1
        assert len(parsed['navigation_aids']) == 1
        assert parsed['accessibility_features']['test_feature'] is True
        assert parsed['estimated_reading_time'] == 2
    
    @pytest.mark.asyncio
    async def test_format_response_complete_workflow(self, formatting_engine, sample_content, formatting_context):
        """Test the complete formatting workflow."""
        formatted_response = await formatting_engine.format_response(sample_content, formatting_context)
        
        assert isinstance(formatted_response, FormattedResponse)
        assert formatted_response.content is not None
        assert formatted_response.format_type is not None
        assert isinstance(formatted_response.sections, list)
        assert isinstance(formatted_response.navigation_aids, list)
        assert isinstance(formatted_response.accessibility_features, dict)
        assert isinstance(formatted_response.metadata, dict)
        assert formatted_response.estimated_reading_time is not None
        
        # Check that sections were created
        assert len(formatted_response.sections) > 0
        
        # Check that navigation aids were created for long content
        if len(sample_content) > 1000:
            assert len(formatted_response.navigation_aids) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, formatting_engine):
        """Test error handling in various methods."""
        # Test with empty content
        empty_analysis = await formatting_engine.analyze_content_structure("")
        assert empty_analysis['content_type'] == ContentType.TEXT
        assert empty_analysis['length'] == 0
        
        # Test with malformed content
        malformed_content = "```python\nno closing backticks"
        analysis = await formatting_engine.analyze_content_structure(malformed_content)
        assert isinstance(analysis, dict)
        
        # Test format_response with error conditions
        context = FormattingContext()
        response = await formatting_engine.format_response("", context)
        assert isinstance(response, FormattedResponse)
    
    def test_initialization(self, formatting_engine):
        """Test proper initialization of the formatting engine."""
        assert isinstance(formatting_engine.code_languages, set)
        assert len(formatting_engine.code_languages) > 0
        assert 'python' in formatting_engine.code_languages
        assert 'javascript' in formatting_engine.code_languages
        
        assert isinstance(formatting_engine.format_patterns, dict)
        assert 'code_block' in formatting_engine.format_patterns
        assert 'heading' in formatting_engine.format_patterns
        
        assert isinstance(formatting_engine.syntax_highlighters, dict)
        assert 'python' in formatting_engine.syntax_highlighters
        assert 'javascript' in formatting_engine.syntax_highlighters


class TestFormattingModels:
    """Test the data models used in formatting."""
    
    def test_content_section_creation(self):
        """Test ContentSection creation and properties."""
        section = ContentSection(
            content="Test content",
            section_type=ContentType.TEXT,
            priority=5,
            format_hint=FormatType.MARKDOWN,
            metadata={'test': 'value'},
            accessibility_text="Alt text",
            navigation_id="nav_1"
        )
        
        assert section.content == "Test content"
        assert section.section_type == ContentType.TEXT
        assert section.priority == 5
        assert section.format_hint == FormatType.MARKDOWN
        assert section.metadata['test'] == 'value'
        assert section.accessibility_text == "Alt text"
        assert section.navigation_id == "nav_1"
    
    def test_formatting_context_creation(self):
        """Test FormattingContext creation and defaults."""
        context = FormattingContext()
        
        assert context.display_context == DisplayContext.DESKTOP
        assert context.accessibility_level == AccessibilityLevel.BASIC
        assert context.user_preferences == {}
        assert context.content_length == 0
        assert context.technical_level == "intermediate"
        assert context.language == "en"
    
    def test_navigation_aid_creation(self):
        """Test NavigationAid creation."""
        aid = NavigationAid(
            type="toc",
            content="Table of Contents",
            links=[{"text": "Section 1", "id": "s1"}],
            position="top"
        )
        
        assert aid.type == "toc"
        assert aid.content == "Table of Contents"
        assert len(aid.links) == 1
        assert aid.position == "top"
    
    def test_formatted_response_creation(self):
        """Test FormattedResponse creation."""
        response = FormattedResponse(
            content="Formatted content",
            format_type=FormatType.MARKDOWN,
            sections=[],
            navigation_aids=[],
            accessibility_features={},
            metadata={},
            estimated_reading_time=5
        )
        
        assert response.content == "Formatted content"
        assert response.format_type == FormatType.MARKDOWN
        assert response.estimated_reading_time == 5


if __name__ == "__main__":
    pytest.main([__file__])