"""
Tests for the DRY Formatter with CopilotKit hooks.

This module tests the DRYFormatter class to ensure consistent output structure,
proper CopilotKit integration, and graceful degradation when CopilotKit is
unavailable.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.ai_karen_engine.core.response.formatter import (
    DRYFormatter,
    FormattingOptions,
    FormattedResponse,
    create_formatter
)
from src.ai_karen_engine.core.response.config import PipelineConfig


class TestDRYFormatter:
    """Test cases for DRYFormatter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = PipelineConfig(enable_copilotkit=True)
        self.formatter = DRYFormatter(self.config)
    
    def test_formatter_initialization(self):
        """Test formatter initializes correctly."""
        assert self.formatter.config == self.config
        assert isinstance(self.formatter.options, FormattingOptions)
        assert self.formatter.options.enable_copilotkit == True
    
    def test_formatter_initialization_with_default_config(self):
        """Test formatter initializes with default config when none provided."""
        formatter = DRYFormatter()
        assert formatter.config is not None
        assert isinstance(formatter.options, FormattingOptions)
    
    def test_create_formatter_factory(self):
        """Test factory function creates formatter correctly."""
        formatter = create_formatter()
        assert isinstance(formatter, DRYFormatter)
        
        formatter_with_config = create_formatter(self.config)
        assert isinstance(formatter_with_config, DRYFormatter)
        assert formatter_with_config.config == self.config


class TestBasicFormatting:
    """Test basic formatting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DRYFormatter()
    
    def test_format_simple_response(self):
        """Test formatting a simple response."""
        raw_response = "This is a simple response."
        result = self.formatter.format_response(
            raw_response, 
            intent="general_assist", 
            persona="ruthless_optimizer"
        )
        
        assert result["content"] == raw_response
        assert result["metadata"]["intent"] == "general_assist"
        assert result["metadata"]["persona"] == "ruthless_optimizer"
        assert result["metadata"]["formatting_applied"] == True
    
    def test_format_response_with_code_blocks(self):
        """Test formatting response with code blocks."""
        raw_response = """Here's some code:

```python
def hello_world():
    print("Hello, World!")
    return True
```

And some more text."""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        assert len(result["code_blocks"]) == 1
        assert result["code_blocks"][0]["language"] == "python"
        assert "def hello_world():" in result["code_blocks"][0]["code"]
        assert result["code_blocks"][0]["line_count"] == 3
    
    def test_format_response_with_headings(self):
        """Test formatting response with headings."""
        raw_response = """# Main Title

## Subtitle

Some content here.

### Another Section

More content."""
        
        result = self.formatter.format_response(
            raw_response,
            intent="documentation",
            persona="technical_writer"
        )
        
        # Should normalize headings to consistent format
        assert "## Main Title" in result["content"]
        assert "## Subtitle" in result["content"]
        assert "## Another Section" in result["content"]
    
    def test_format_response_with_bullets(self):
        """Test formatting response with bullet points."""
        raw_response = """Here are some points:

- First point
* Second point
+ Third point
1. Fourth point
2. Fifth point"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="general_assist",
            persona="ruthless_optimizer"
        )
        
        # Should normalize all bullets to consistent format
        content = result["content"]
        assert "• First point" in content
        assert "• Second point" in content
        assert "• Third point" in content
        assert "• Fourth point" in content
        assert "• Fifth point" in content


class TestStructuredSections:
    """Test structured section parsing and formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DRYFormatter()
    
    def test_extract_onboarding_sections(self):
        """Test extraction of onboarding sections."""
        raw_response = """## Quick Plan
Set up the development environment and create initial project structure.

## Next Action
Install Python dependencies and configure virtual environment.

## Optional Boost
Consider using Docker for consistent development environment."""
        
        result = self.formatter.format_response(
            raw_response,
            intent="general_assist",
            persona="ruthless_optimizer"
        )
        
        assert "quick_plan" in result["sections"]
        assert "next_action" in result["sections"]
        assert "optional_boost" in result["sections"]
        
        assert "Set up the development environment" in result["sections"]["quick_plan"]
        assert "Install Python dependencies" in result["sections"]["next_action"]
        assert "Consider using Docker" in result["sections"]["optional_boost"]
    
    def test_extract_mixed_sections(self):
        """Test extraction of various section types."""
        raw_response = """## Summary
This is a summary of the solution.

## Details
Here are the detailed steps to follow.

## Quick Plan
1. First step
2. Second step"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="documentation",
            persona="technical_writer"
        )
        
        assert "summary" in result["sections"]
        assert "details" in result["sections"]
        assert "quick_plan" in result["sections"]


class TestCopilotKitIntegration:
    """Test CopilotKit integration and enhancements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        config = PipelineConfig(enable_copilotkit=True)
        self.formatter = DRYFormatter(config)
    
    def test_copilotkit_enhancements_with_code(self):
        """Test CopilotKit enhancements for code-related responses."""
        raw_response = """Here's the optimized function:

```python
def optimized_function(data):
    # Optimized implementation
    return processed_data
```

This should improve performance significantly."""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        # Should include CopilotKit enhancements when available
        if result["metadata"]["copilotkit_enabled"]:
            assert "copilotkit" in result
            assert "complexity_graph" in result["copilotkit"]
            assert "inline_suggestions" in result["copilotkit"]
            assert "ui_hints" in result["copilotkit"]
            assert "performance_metrics" in result["copilotkit"]
    
    def test_copilotkit_inline_suggestions(self):
        """Test CopilotKit inline suggestions generation."""
        raw_response = "Debug this error by checking the logs."
        
        result = self.formatter.format_response(
            raw_response,
            intent="debug_error",
            persona="calm_fixit"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            suggestions = result["copilotkit"]["inline_suggestions"]
            assert len(suggestions) > 0
            assert any(s["type"] == "debugging" for s in suggestions)
    
    def test_copilotkit_ui_hints(self):
        """Test CopilotKit UI hints generation."""
        raw_response = """```javascript
console.log('Hello World');
```"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            ui_hints = result["copilotkit"]["ui_hints"]
            assert "suggested_actions" in ui_hints
            assert "ui_components" in ui_hints
            assert len(ui_hints["suggested_actions"]) > 0


class TestGracefulDegradation:
    """Test graceful degradation when CopilotKit is unavailable."""
    
    def setup_method(self):
        """Set up test fixtures."""
        config = PipelineConfig(enable_copilotkit=False)
        self.formatter = DRYFormatter(config)
    
    def test_formatting_without_copilotkit(self):
        """Test formatting works without CopilotKit."""
        raw_response = """## Quick Plan
Set up the project.

```python
print("Hello")
```"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="general_assist",
            persona="ruthless_optimizer"
        )
        
        assert result["metadata"]["copilotkit_enabled"] == False
        assert "copilotkit" not in result
        assert result["metadata"]["formatting_applied"] == True
        assert len(result["code_blocks"]) == 1
    
    @patch('src.ai_karen_engine.core.response.formatter.DRYFormatter._check_copilotkit_availability')
    def test_copilotkit_unavailable_fallback(self, mock_check):
        """Test fallback when CopilotKit check fails."""
        mock_check.return_value = False
        
        config = PipelineConfig(enable_copilotkit=True)
        formatter = DRYFormatter(config)
        
        result = formatter.format_response(
            "Test response",
            intent="general_assist",
            persona="ruthless_optimizer"
        )
        
        assert result["metadata"]["copilotkit_enabled"] == False
        assert "copilotkit" not in result
    
    def test_formatting_error_fallback(self):
        """Test fallback to raw response when formatting fails."""
        # Mock a formatting error
        with patch.object(self.formatter, '_parse_response_structure', side_effect=Exception("Test error")):
            raw_response = "Test response"
            result = self.formatter.format_response(
                raw_response,
                intent="general_assist",
                persona="ruthless_optimizer"
            )
            
            assert result["content"] == raw_response
            assert result["metadata"]["formatting_applied"] == False
            assert "error" in result["metadata"]


class TestFormattingOptions:
    """Test formatting options and customization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DRYFormatter()
    
    def test_custom_formatting_options(self):
        """Test custom formatting options via kwargs."""
        raw_response = """- First point
- Second point"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="general_assist",
            persona="ruthless_optimizer",
            bullet_style="→",
            heading_style="###"
        )
        
        # Should use custom bullet style
        assert "→ First point" in result["content"]
        assert "→ Second point" in result["content"]
    
    def test_disable_code_highlighting(self):
        """Test disabling code highlighting."""
        raw_response = """```python
print("test")
```"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer",
            enable_code_highlighting=False
        )
        
        # Should still parse code blocks but not apply special formatting
        assert len(result["code_blocks"]) == 1
    
    def test_disable_structured_sections(self):
        """Test disabling structured sections."""
        raw_response = """# Title
Content here."""
        
        result = self.formatter.format_response(
            raw_response,
            intent="documentation",
            persona="technical_writer",
            enable_structured_sections=False
        )
        
        # Should not normalize headings
        assert result["metadata"]["headings_formatted"] == False


class TestComplexityEstimation:
    """Test complexity estimation for responses."""
    
    def setup_method(self):
        """Set up test fixtures."""
        config = PipelineConfig(enable_copilotkit=True)
        self.formatter = DRYFormatter(config)
    
    def test_low_complexity_response(self):
        """Test low complexity response estimation."""
        raw_response = "Simple response."
        
        result = self.formatter.format_response(
            raw_response,
            intent="general_assist",
            persona="ruthless_optimizer"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            complexity = result["copilotkit"]["performance_metrics"]["estimated_complexity"]
            assert complexity == "low"
    
    def test_high_complexity_response(self):
        """Test high complexity response estimation."""
        raw_response = """## Section 1
Content here.

## Section 2
More content.

```python
def complex_function():
    # Many lines of code
    pass
```

```javascript
function another_function() {
    // More code
}
```

## Section 3
Even more content with lots of text to make it longer and more complex.
This should push the complexity score higher due to multiple factors:
- Multiple code blocks
- Multiple sections
- Long content length
"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            complexity = result["copilotkit"]["performance_metrics"]["estimated_complexity"]
            assert complexity in ["medium", "high"]


class TestCodeBlockHandling:
    """Test code block parsing and formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = DRYFormatter()
    
    def test_multiple_code_blocks(self):
        """Test handling multiple code blocks."""
        raw_response = """First block:
```python
print("Python")
```

Second block:
```javascript
console.log("JavaScript");
```

Third block:
```
Plain text block
```"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        assert len(result["code_blocks"]) == 3
        assert result["code_blocks"][0]["language"] == "python"
        assert result["code_blocks"][1]["language"] == "javascript"
        assert result["code_blocks"][2]["language"] == "text"
    
    def test_long_code_block_truncation(self):
        """Test truncation of very long code blocks."""
        # Create a long code block
        long_code = "\n".join([f"line_{i} = {i}" for i in range(100)])
        raw_response = f"""```python
{long_code}
```"""
        
        result = self.formatter.format_response(
            raw_response,
            intent="optimize_code",
            persona="ruthless_optimizer",
            max_code_block_lines=10
        )
        
        assert len(result["code_blocks"]) == 1
        code_block = result["code_blocks"][0]
        assert code_block["line_count"] == 100
        
        # Should be truncated in the final content
        assert "... (90 more lines)" in result["content"]


class TestPersonaAndIntentHandling:
    """Test persona and intent-specific formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        config = PipelineConfig(enable_copilotkit=True)
        self.formatter = DRYFormatter(config)
    
    def test_debug_intent_suggestions(self):
        """Test debug intent generates appropriate suggestions."""
        result = self.formatter.format_response(
            "Check the error logs.",
            intent="debug_error",
            persona="calm_fixit"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            suggestions = result["copilotkit"]["inline_suggestions"]
            suggestion_types = [s["type"] for s in suggestions]
            assert "debugging" in suggestion_types or "testing" in suggestion_types
    
    def test_optimization_intent_suggestions(self):
        """Test optimization intent generates appropriate suggestions."""
        result = self.formatter.format_response(
            "Optimize this function.",
            intent="optimize_code",
            persona="ruthless_optimizer"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            suggestions = result["copilotkit"]["inline_suggestions"]
            suggestion_types = [s["type"] for s in suggestions]
            assert "optimization" in suggestion_types or "refactor" in suggestion_types
    
    def test_documentation_intent_suggestions(self):
        """Test documentation intent generates appropriate suggestions."""
        result = self.formatter.format_response(
            "Write documentation for this API.",
            intent="documentation",
            persona="technical_writer"
        )
        
        if result["metadata"]["copilotkit_enabled"]:
            suggestions = result["copilotkit"]["inline_suggestions"]
            suggestion_types = [s["type"] for s in suggestions]
            assert "docs" in suggestion_types


if __name__ == "__main__":
    pytest.main([__file__])