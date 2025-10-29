"""
Integration tests for the Advanced Formatting Engine with the existing system.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import json

from src.ai_karen_engine.services.advanced_formatting_engine import (
    AdvancedFormattingEngine,
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
    FormatType
)


class TestAdvancedFormattingIntegration:
    """Integration tests for advanced formatting system."""
    
    @pytest.fixture
    def formatting_engine(self):
        """Create formatting engine for integration testing."""
        return AdvancedFormattingEngine()
    
    @pytest.fixture
    def complex_response_content(self):
        """Complex response content that mimics real system output."""
        return """# AI Response Analysis

## Overview
This response demonstrates the intelligent formatting system's capabilities with various content types and structures.

## Code Implementation
Here's the main implementation:

```python
class IntelligentResponseController:
    def __init__(self):
        self.formatting_engine = AdvancedFormattingEngine()
        self.cache_manager = SmartCacheManager()
    
    async def process_query(self, query: str) -> FormattedResponse:
        # Analyze query complexity
        analysis = await self.analyze_query(query)
        
        # Generate optimized response
        response = await self.generate_response(query, analysis)
        
        # Apply advanced formatting
        formatted = await self.formatting_engine.format_response(
            response.content, 
            self.create_formatting_context(analysis)
        )
        
        return formatted
```

## Configuration Options
The system supports multiple configuration options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| display_context | string | "desktop" | Target display context |
| accessibility_level | string | "basic" | Accessibility support level |
| technical_level | string | "intermediate" | User technical expertise |
| language | string | "en" | Content language |

## Features List
The advanced formatting system provides:

- **Automatic Format Selection**: Intelligently chooses optimal formatting
- **Hierarchical Organization**: Structures content logically
- **Syntax Highlighting**: Enhances code readability
- **Navigation Aids**: Provides TOC and summaries for long content
- **Accessibility Support**: Includes screen reader optimizations
- **Responsive Formatting**: Adapts to different display contexts

## JavaScript Integration
For frontend integration:

```javascript
class FormattingClient {
    constructor(apiBase) {
        this.apiBase = apiBase;
    }
    
    async formatContent(content, options = {}) {
        const response = await fetch(`${this.apiBase}/api/formatting/format`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content,
                display_context: options.displayContext || 'desktop',
                accessibility_level: options.accessibilityLevel || 'basic',
                user_preferences: options.userPreferences || {},
                technical_level: options.technicalLevel || 'intermediate',
                language: options.language || 'en'
            })
        });
        
        return await response.json();
    }
}
```

## Performance Metrics
Expected performance improvements:

1. **Response Time**: 60% reduction in formatting time
2. **CPU Usage**: Under 5% per response
3. **Memory Efficiency**: 40% reduction in memory usage
4. **Cache Hit Rate**: 85% for similar queries

## Error Handling
The system includes comprehensive error handling:

```python
try:
    formatted_response = await formatting_engine.format_response(content, context)
except FormattingError as e:
    logger.error(f"Formatting failed: {e}")
    # Fallback to basic formatting
    formatted_response = create_basic_response(content)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Return original content with minimal formatting
    formatted_response = create_minimal_response(content)
```

## Conclusion
This advanced formatting system significantly improves response quality and user experience while maintaining compatibility with existing system components.
"""
    
    @pytest.mark.asyncio
    async def test_complete_formatting_workflow(self, formatting_engine, complex_response_content):
        """Test the complete formatting workflow with complex content."""
        # Create formatting context
        context = FormattingContext(
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.ENHANCED,
            user_preferences={'prefer_tables': True, 'syntax_highlighting': True},
            content_length=len(complex_response_content),
            technical_level="advanced",
            language="en"
        )
        
        # Format the complex response
        formatted_response = await formatting_engine.format_response(
            complex_response_content, 
            context
        )
        
        # Verify response structure
        assert formatted_response is not None
        assert formatted_response.content is not None
        assert len(formatted_response.sections) > 0
        assert formatted_response.format_type is not None
        
        # Verify navigation aids were created for long content
        assert len(formatted_response.navigation_aids) > 0
        
        # Verify table of contents was created
        toc_aids = [aid for aid in formatted_response.navigation_aids if aid.type == "toc"]
        assert len(toc_aids) > 0
        
        # Verify accessibility features were added
        assert len(formatted_response.accessibility_features) > 0
        assert 'reading_level' in formatted_response.accessibility_features
        
        # Verify code sections were properly highlighted
        code_sections = [s for s in formatted_response.sections if s.section_type.value == 'code']
        assert len(code_sections) > 0
        
        # Verify estimated reading time was calculated
        assert formatted_response.estimated_reading_time is not None
        assert formatted_response.estimated_reading_time > 0
    
    @pytest.mark.asyncio
    async def test_mobile_responsive_formatting(self, formatting_engine, complex_response_content):
        """Test responsive formatting for mobile devices."""
        mobile_context = FormattingContext(
            display_context=DisplayContext.MOBILE,
            accessibility_level=AccessibilityLevel.BASIC,
            content_length=len(complex_response_content)
        )
        
        formatted_response = await formatting_engine.format_response(
            complex_response_content,
            mobile_context
        )
        
        # Verify mobile-specific formatting
        assert "📋 **Quick Navigation**" in formatted_response.content
        
        # Verify code blocks are properly formatted for mobile
        assert "```python" in formatted_response.content
        assert "```javascript" in formatted_response.content
    
    @pytest.mark.asyncio
    async def test_terminal_formatting(self, formatting_engine, complex_response_content):
        """Test formatting for terminal display."""
        terminal_context = FormattingContext(
            display_context=DisplayContext.TERMINAL,
            accessibility_level=AccessibilityLevel.BASIC
        )
        
        formatted_response = await formatting_engine.format_response(
            complex_response_content,
            terminal_context
        )
        
        # Verify terminal-specific formatting
        assert "=" * 60 in formatted_response.content
        assert "RESPONSE" in formatted_response.content
        assert "┌" in formatted_response.content  # Code block borders
        assert "│" in formatted_response.content
        assert "└" in formatted_response.content
    
    @pytest.mark.asyncio
    async def test_api_structured_output(self, formatting_engine, complex_response_content):
        """Test API structured output formatting."""
        api_context = FormattingContext(
            display_context=DisplayContext.API,
            accessibility_level=AccessibilityLevel.FULL
        )
        
        formatted_response = await formatting_engine.format_response(
            complex_response_content,
            api_context
        )
        
        # Verify JSON structure
        parsed_json = json.loads(formatted_response.content)
        
        assert 'content' in parsed_json
        assert 'format_type' in parsed_json
        assert 'sections' in parsed_json
        assert 'navigation_aids' in parsed_json
        assert 'accessibility_features' in parsed_json
        assert 'metadata' in parsed_json
        assert 'estimated_reading_time' in parsed_json
        
        # Verify sections structure
        assert len(parsed_json['sections']) > 0
        for section in parsed_json['sections']:
            assert 'content' in section
            assert 'type' in section
            assert 'priority' in section
            assert 'metadata' in section
    
    @pytest.mark.asyncio
    async def test_accessibility_features_integration(self, formatting_engine, complex_response_content):
        """Test accessibility features integration."""
        full_accessibility_context = FormattingContext(
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.FULL,
            user_preferences={'screen_reader': True, 'high_contrast': True}
        )
        
        formatted_response = await formatting_engine.format_response(
            complex_response_content,
            full_accessibility_context
        )
        
        # Verify full accessibility features
        accessibility_features = formatted_response.accessibility_features
        
        assert 'code_descriptions' in accessibility_features
        assert 'reading_level' in accessibility_features
        assert 'screen_reader_text' in accessibility_features
        assert 'keyboard_navigation' in accessibility_features
        
        # Verify code descriptions were generated
        assert len(accessibility_features['code_descriptions']) > 0
        
        # Verify keyboard navigation hints
        assert len(accessibility_features['keyboard_navigation']) > 0
    
    @pytest.mark.asyncio
    async def test_syntax_highlighting_integration(self, formatting_engine):
        """Test syntax highlighting with various programming languages."""
        multi_language_content = """
# Multi-Language Code Examples

## Python Example
```python
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
```

## JavaScript Example
```javascript
function calculateFibonacci(n) {
    if (n <= 1) return n;
    return calculateFibonacci(n-1) + calculateFibonacci(n-2);
}
```

## SQL Example
```sql
SELECT users.name, COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON users.id = orders.user_id
GROUP BY users.id
HAVING order_count > 5;
```
"""
        
        context = FormattingContext(
            display_context=DisplayContext.DESKTOP,
            user_preferences={'syntax_highlighting': True}
        )
        
        formatted_response = await formatting_engine.format_response(
            multi_language_content,
            context
        )
        
        # Verify syntax highlighting was applied
        content = formatted_response.content
        
        # Check for Python highlighting
        assert '<span class="keyword">def</span>' in content
        assert '<span class="keyword">return</span>' in content
        
        # Check for JavaScript highlighting
        assert '<span class="keyword">function</span>' in content
        
        # Verify code sections were identified
        code_sections = [s for s in formatted_response.sections if s.section_type.value == 'code']
        assert len(code_sections) >= 3  # Python, JavaScript, SQL
    
    @pytest.mark.asyncio
    async def test_performance_with_large_content(self, formatting_engine):
        """Test performance with large content blocks."""
        # Generate large content
        large_content = """# Large Document Test

## Introduction
""" + "This is a large document with extensive content. " * 100 + """

## Code Section
```python
# Large code block
""" + "\n".join([f"def function_{i}(): pass" for i in range(50)]) + """
```

## Data Section
""" + "\n".join([f"- Item {i}: Description for item {i}" for i in range(100)]) + """

## Conclusion
""" + "This concludes our large document test. " * 50
        
        context = FormattingContext(
            display_context=DisplayContext.DESKTOP,
            accessibility_level=AccessibilityLevel.ENHANCED
        )
        
        import time
        start_time = time.time()
        
        formatted_response = await formatting_engine.format_response(large_content, context)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance (should complete within reasonable time)
        assert processing_time < 5.0  # Should complete within 5 seconds
        
        # Verify response quality wasn't compromised
        assert formatted_response is not None
        assert len(formatted_response.sections) > 0
        assert len(formatted_response.navigation_aids) > 0
        assert formatted_response.estimated_reading_time is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, formatting_engine):
        """Test error recovery and graceful degradation."""
        # Test with malformed content
        malformed_content = """
# Malformed Document

```python
def broken_function(
    # Missing closing parenthesis and code block terminator

## Incomplete Section
This section has issues...

| Broken | Table |
|--------|
| Missing | Cell |
"""
        
        context = FormattingContext()
        
        # Should not raise exception, but handle gracefully
        formatted_response = await formatting_engine.format_response(malformed_content, context)
        
        assert formatted_response is not None
        assert formatted_response.content is not None
        assert len(formatted_response.sections) > 0
    
    @pytest.mark.asyncio
    async def test_caching_integration_simulation(self, formatting_engine):
        """Test integration with caching systems (simulated)."""
        content = "# Test Content\nThis is test content for caching."
        context = FormattingContext()
        
        # First formatting (cache miss simulation)
        start_time = time.time()
        response1 = await formatting_engine.format_response(content, context)
        first_time = time.time() - start_time
        
        # Second formatting (cache hit simulation)
        start_time = time.time()
        response2 = await formatting_engine.format_response(content, context)
        second_time = time.time() - start_time
        
        # Verify responses are consistent
        assert response1.format_type == response2.format_type
        assert len(response1.sections) == len(response2.sections)
        
        # Note: Actual caching would be handled by SmartCacheManager
        # This test verifies consistent output for caching integration
    
    @pytest.mark.asyncio
    async def test_multi_context_formatting(self, formatting_engine, complex_response_content):
        """Test formatting the same content for multiple contexts."""
        contexts = [
            FormattingContext(display_context=DisplayContext.DESKTOP),
            FormattingContext(display_context=DisplayContext.MOBILE),
            FormattingContext(display_context=DisplayContext.TABLET),
            FormattingContext(display_context=DisplayContext.TERMINAL),
            FormattingContext(display_context=DisplayContext.API)
        ]
        
        responses = []
        for context in contexts:
            response = await formatting_engine.format_response(complex_response_content, context)
            responses.append(response)
        
        # Verify all contexts produced valid responses
        for response in responses:
            assert response is not None
            assert response.content is not None
            assert len(response.sections) > 0
        
        # Verify context-specific differences
        desktop_response = responses[0]
        mobile_response = responses[1]
        terminal_response = responses[2]
        api_response = responses[4]
        
        # Mobile should have navigation optimizations
        assert "📋" in mobile_response.content
        
        # Terminal should have ASCII formatting
        assert "=" in terminal_response.content
        assert "┌" in terminal_response.content
        
        # API should be JSON
        try:
            json.loads(api_response.content)
            api_is_json = True
        except:
            api_is_json = False
        assert api_is_json
    
    @pytest.mark.asyncio
    async def test_content_type_detection_accuracy(self, formatting_engine):
        """Test accuracy of content type detection with various content types."""
        test_cases = [
            {
                'content': '```python\ndef test(): pass\n```\n```javascript\nfunction test() {}\n```',
                'expected_type': 'code'
            },
            {
                'content': 'This API function implements the algorithm for database optimization using advanced techniques.',
                'expected_type': 'technical'
            },
            {
                'content': 'First, open the file. Then, edit the content. Next, save the changes. Finally, close the editor.',
                'expected_type': 'instructional'
            },
            {
                'content': 'Once upon a time, there was a developer who loved clean code and elegant solutions.',
                'expected_type': 'narrative'
            },
            {
                'content': '''# Mixed Content
                This document contains code:
                ```python
                def hello(): pass
                ```
                And also has technical information about APIs and algorithms.''',
                'expected_type': 'mixed'
            }
        ]
        
        for test_case in test_cases:
            analysis = await formatting_engine.analyze_content_structure(test_case['content'])
            detected_type = analysis['content_type'].value
            
            # Allow for reasonable variations in detection
            if test_case['expected_type'] == 'mixed':
                assert detected_type in ['mixed', 'technical', 'code']
            else:
                assert detected_type == test_case['expected_type'], \
                    f"Expected {test_case['expected_type']}, got {detected_type} for content: {test_case['content'][:50]}..."


if __name__ == "__main__":
    pytest.main([__file__])