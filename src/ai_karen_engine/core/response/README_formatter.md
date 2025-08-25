# DRY Formatter with CopilotKit Hooks

The DRY Formatter provides consistent output structure (headings, code blocks, bullets) with optional CopilotKit enhancements as purely additive features. It ensures graceful degradation when CopilotKit is unavailable and follows DRY (Don't Repeat Yourself) principles.

## Features

### Core Formatting
- **Consistent Headings**: Normalizes heading levels to a consistent format
- **Bullet Point Standardization**: Converts various bullet styles to a unified format
- **Code Block Enhancement**: Proper syntax highlighting and truncation for long code
- **Section Extraction**: Automatically identifies and structures common sections

### CopilotKit Integration
- **Complexity Graphs**: Visual representation of code complexity
- **Inline Suggestions**: Context-aware suggestions based on intent and persona
- **UI Hints**: Recommendations for UI components and interactions
- **Performance Metrics**: Complexity estimation and optimization suggestions

### Graceful Degradation
- **CopilotKit Optional**: All core functionality works without CopilotKit
- **Error Recovery**: Falls back to raw response if formatting fails
- **Progressive Enhancement**: CopilotKit features are purely additive

## Usage

### Basic Usage

```python
from ai_karen_engine.core.response.formatter import create_formatter

# Create formatter with default configuration
formatter = create_formatter()

# Format a response
result = formatter.format_response(
    raw_response="Your raw LLM response here",
    intent="optimize_code",
    persona="ruthless_optimizer"
)

print(result["content"])  # Formatted content
print(result["sections"])  # Extracted sections
print(result["code_blocks"])  # Parsed code blocks
```

### Advanced Usage with Custom Options

```python
from ai_karen_engine.core.response.formatter import DRYFormatter
from ai_karen_engine.core.response.config import PipelineConfig

# Create custom configuration
config = PipelineConfig(enable_copilotkit=True)
formatter = DRYFormatter(config)

# Format with custom options
result = formatter.format_response(
    raw_response="Your response",
    intent="debug_error",
    persona="calm_fixit",
    bullet_style="→",
    heading_style="###",
    max_code_block_lines=10
)

# Access CopilotKit enhancements if available
if "copilotkit" in result:
    suggestions = result["copilotkit"]["inline_suggestions"]
    ui_hints = result["copilotkit"]["ui_hints"]
    complexity = result["copilotkit"]["performance_metrics"]["estimated_complexity"]
```

## Response Structure

The formatter returns a structured dictionary with the following keys:

```python
{
    "content": str,                    # Formatted response content
    "sections": Dict[str, str],        # Extracted sections (quick_plan, next_action, etc.)
    "code_blocks": List[Dict],         # Parsed code blocks with metadata
    "metadata": {
        "intent": str,                 # User intent
        "persona": str,                # Selected persona
        "formatter_version": str,      # Formatter version
        "copilotkit_enabled": bool,    # Whether CopilotKit is available
        "formatting_applied": bool,    # Whether formatting was successful
        # ... additional metadata
    },
    "copilotkit": {                    # Optional CopilotKit enhancements
        "complexity_graph": Dict,      # Complexity visualization data
        "inline_suggestions": List,    # Context-aware suggestions
        "ui_hints": Dict,             # UI component recommendations
        "performance_metrics": Dict    # Performance and complexity metrics
    }
}
```

## Section Types

The formatter automatically extracts and structures common response sections:

- **quick_plan**: High-level plan or overview
- **next_action**: Immediate next steps
- **optional_boost**: Additional enhancements or optimizations
- **summary**: Summary or overview of the response
- **details**: Detailed explanation or steps

## Code Block Handling

- **Language Detection**: Automatically detects programming language
- **Syntax Highlighting**: Preserves syntax highlighting markers
- **Truncation**: Long code blocks are truncated with line count indicators
- **Metadata**: Tracks line count, language, and other code block properties

## CopilotKit Enhancements

When CopilotKit is available and enabled, the formatter adds:

### Complexity Graphs
Visual representation of code complexity with nodes and metrics for each code block.

### Inline Suggestions
Context-aware suggestions based on:
- **Intent**: Different suggestions for debugging vs optimization
- **Persona**: Tailored to the selected persona style
- **Content**: Code-specific suggestions when code is present

### UI Hints
Recommendations for UI components and interactions:
- **Suggested Actions**: Copy to clipboard, run in sandbox, etc.
- **UI Components**: Code editor, debug console, performance dashboard
- **Interaction Hints**: Context-specific interaction recommendations

### Performance Metrics
- **Complexity Estimation**: Low, medium, or high complexity rating
- **Content Analysis**: Code block count, section count, content length
- **Next Actions**: Suggested follow-up actions based on intent and persona

## Configuration Options

### FormattingOptions

```python
@dataclass
class FormattingOptions:
    enable_copilotkit: bool = True
    enable_code_highlighting: bool = True
    enable_structured_sections: bool = True
    enable_onboarding_format: bool = True
    max_code_block_lines: int = 50
    bullet_style: str = "•"
    heading_style: str = "##"
    
    # CopilotKit specific options
    copilotkit_complexity_graphs: bool = True
    copilotkit_inline_suggestions: bool = True
    copilotkit_ui_hints: bool = True
```

### PipelineConfig Integration

The formatter integrates with the main pipeline configuration:

```python
config = PipelineConfig(
    enable_copilotkit=True,  # Enable CopilotKit features
    # ... other pipeline settings
)
```

## Error Handling and Graceful Degradation

The formatter implements multiple levels of graceful degradation:

1. **CopilotKit Unavailable**: Core formatting continues without enhancements
2. **Section Parsing Fails**: Returns content with basic formatting applied
3. **Code Block Parsing Fails**: Preserves original code blocks
4. **Complete Formatting Failure**: Returns raw response with error metadata

## Testing

Comprehensive test suite covers:

- Basic formatting functionality
- Section extraction and structuring
- Code block parsing and truncation
- CopilotKit integration and enhancements
- Graceful degradation scenarios
- Custom formatting options
- Error handling and recovery

Run tests with:
```bash
python -m pytest tests/test_dry_formatter.py -v
```

## Integration with Response Orchestrator

The formatter implements the `ResponseFormatter` protocol and integrates seamlessly with the Response Orchestrator:

```python
from ai_karen_engine.core.response import create_response_orchestrator

# The orchestrator automatically uses the DRY formatter
orchestrator = create_response_orchestrator()
response = orchestrator.respond("Optimize this code", ui_caps={})
```

## Performance Considerations

- **Lazy Loading**: CopilotKit features are only loaded when needed
- **Caching**: Template compilation and regex patterns are cached
- **Memory Efficient**: Large code blocks are truncated to prevent memory issues
- **Fast Parsing**: Efficient section extraction using line-by-line parsing

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **6.1**: Consistent output structure (headings, code blocks, bullets)
- **6.2**: CopilotKit enhancements as purely additive features
- **6.3**: Graceful degradation when CopilotKit is unavailable
- **6.4**: No errors thrown when CopilotKit is unavailable
- **8.1**: Consistent response formatting
- **8.2**: Structured onboarding sections (Quick Plan, Next Action, Optional Boost)
- **8.3**: Proper code formatting with syntax highlighting
- **8.4**: CopilotKit UI hints when enabled
- **8.5**: Raw response fallback when formatting fails

## Examples

See `examples/dry_formatter_demo.py` for comprehensive usage examples demonstrating all features.