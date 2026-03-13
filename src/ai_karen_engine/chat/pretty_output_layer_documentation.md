# Pretty Output Layer Documentation

## Overview

The Pretty Output Layer (Global Response Formatter) is a configurable formatting system for AI responses in Karen's AI system. It provides structured, visually appealing output formatting with support for different output profiles and layout types while maintaining a headless/API-first design.

## Features

- **Configurable Output Profiles**: Choose between PLAIN, PRETTY, and DEV_DOC profiles
- **Automatic Layout Detection**: Automatically detects appropriate layouts for content
- **Interactive Elements**: Support for buttons, links, and menus
- **Error Handling**: Comprehensive error handling with fallback mechanisms
- **Performance Metrics**: Built-in performance tracking and metrics
- **Integration**: Seamless integration with existing response formatting systems

## Architecture

### Core Components

1. **PrettyOutputLayer**: Main class that orchestrates the formatting process
2. **Layout Detectors**: Analyze content to determine the best layout
3. **Layout Formatters**: Apply specific formatting based on layout type
4. **Profile Formatters**: Apply profile-specific formatting
5. **Integration Layer**: Bridges with existing response formatting systems

### Data Structures

- **OutputProfile**: Enum defining available output profiles
- **LayoutType**: Enum defining available layout types
- **LayoutHint**: Dataclass containing layout detection results
- **ResponseContext**: Dataclass containing context information
- **FormattingConfig**: Dataclass containing configuration options

## Usage

### Basic Usage

```python
from src.ai_karen_engine.chat.response_formatter import (
    PrettyOutputLayer, 
    OutputProfile, 
    LayoutType,
    ResponseContext,
    FormattingConfig
)

# Initialize with default configuration
formatter = PrettyOutputLayer()

# Create response context
context = ResponseContext(
    user_query="What movies are playing?",
    response_content="Here are the movies: **Movie 1** (2021), **Movie 2** (2022)",
    user_preferences={"theme": "dark"}
)

# Format response
result = formatter.format_response("Movie list content", context)
print(result["content"])
```

### Advanced Usage

```python
# Create custom configuration
config = FormattingConfig(
    output_profile=OutputProfile.DEV_DOC,
    default_layout=LayoutType.MOVIE_LIST,
    enable_markdown=True,
    enable_sections=True,
    enable_highlights=True,
    max_content_length=5000,
    safe_mode=True
)

# Initialize with custom configuration
formatter = PrettyOutputLayer(config)

# Force a specific layout type
formatter.force_layout_type(LayoutType.MENU)

# Enable interactive elements
formatter.enable_interactive_elements(True)

# Add interactive elements
formatted_content = formatter.add_interactive_element(
    "button", 
    "Click me", 
    action="handle_click"
)
```

### Output Profiles

#### PLAIN Profile
- Minimal formatting
- Removes markdown formatting
- Basic text output

#### PRETTY Profile
- Enhanced formatting
- Preserves markdown
- Adds visual structure
- Default profile

#### DEV_DOC Profile
- Developer-focused formatting
- Enhanced code blocks
- API references
- Annotations

### Layout Types

#### DEFAULT
- Standard paragraph formatting
- Basic markdown support
- Fallback layout

#### MENU
- Formats option lists
- Numbered and bulleted options
- Enhanced visual structure

#### MOVIE_LIST
- Specialized for movie content
- Handles titles, years, descriptions
- Structured movie cards

#### BULLET_LIST
- Formats bullet point lists
- Consistent bullet styling
- Numbered list conversion

#### SYSTEM_STATUS
- Status indicators
- Visual status cues
- Error/warning highlighting

## API Reference

### PrettyOutputLayer Class

#### Constructor
```python
PrettyOutputLayer(config: Optional[FormattingConfig] = None)
```
Initializes the Pretty Output Layer with optional configuration.

#### Methods

##### format_response
```python
format_response(response_content: str, context: ResponseContext) -> Dict[str, Any]
```
Formats a response using the configured output profile and detected layout.

**Parameters:**
- `response_content`: The raw response content to format
- `context`: Context information for formatting

**Returns:**
Dictionary containing formatted response and metadata

##### set_output_profile
```python
set_output_profile(profile: OutputProfile) -> None
```
Sets the output profile for formatting.

##### get_output_profile
```python
get_output_profile() -> OutputProfile
```
Gets the current output profile.

##### force_layout_type
```python
force_layout_type(layout_type: LayoutType) -> None
```
Forces the use of a specific layout type.

##### reset_layout_detection
```python
reset_layout_detection() -> None
```
Resets to automatic layout detection.

##### enable_interactive_elements
```python
enable_interactive_elements(enabled: bool = True) -> None
```
Enables or disables interactive elements in formatted output.

##### add_interactive_element
```python
add_interactive_element(element_type: str, content: str, **kwargs) -> str
```
Adds an interactive element to the content.

**Parameters:**
- `element_type`: Type of interactive element (button, link, menu)
- `content`: Content for the element
- `**kwargs`: Additional parameters for the element

##### get_performance_metrics
```python
get_performance_metrics() -> Dict[str, Any]
```
Gets performance metrics for the Pretty Output Layer.

##### reset_performance_metrics
```python
reset_performance_metrics() -> None
```
Resets performance metrics.

### Data Classes

#### OutputProfile Enum
- `PLAIN`: Minimal formatting
- `PRETTY`: Enhanced formatting (default)
- `DEV_DOC`: Developer documentation formatting

#### LayoutType Enum
- `DEFAULT`: Standard paragraph formatting
- `MENU`: Option list formatting
- `MOVIE_LIST`: Movie content formatting
- `BULLET_LIST`: Bullet point formatting
- `SYSTEM_STATUS`: Status information formatting

#### LayoutHint Dataclass
```python
@dataclass
class LayoutHint:
    layout_type: LayoutType
    confidence: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)
```

#### ResponseContext Dataclass
```python
@dataclass
class ResponseContext:
    user_query: str
    response_content: str
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    theme_context: Dict[str, Any] = field(default_factory=dict)
    detected_content_type: Optional[str] = None
    confidence_score: float = 0.0
```

#### FormattingConfig Dataclass
```python
@dataclass
class FormattingConfig:
    output_profile: OutputProfile = OutputProfile.PRETTY
    default_layout: LayoutType = LayoutType.DEFAULT
    enable_markdown: bool = True
    enable_sections: bool = True
    enable_highlights: bool = True
    max_content_length: int = 10000
    safe_mode: bool = True
```

## Integration

### With Existing Response Formatting

The Pretty Output Layer includes an integration layer (`ResponseFormatterAdapter`) that allows it to work with existing response formatting systems:

```python
from src.ai_karen_engine.chat.response_formatter_integration import ResponseFormatterAdapter

# Create adapter
adapter = ResponseFormatterAdapter()

# Format response with fallback
result = adapter.format_response(
    content="Response content",
    context=context,
    use_extensions=True,  # Try extensions first
    fallback_to_pretty=True  # Fall back to Pretty Output Layer
)
```

### Performance Considerations

The Pretty Output Layer includes built-in performance metrics:

```python
# Get performance metrics
metrics = formatter.get_performance_metrics()
print(f"Average layout detection time: {metrics['average_layout_detection_time']}")
print(f"Error rate: {metrics['error_rate']}")

# Reset metrics
formatter.reset_performance_metrics()
```

## Error Handling

The Pretty Output Layer includes comprehensive error handling:

- Graceful fallback to default formatting on errors
- Detailed error logging with stack traces
- Error tracking in performance metrics
- Safe mode for content sanitization

## Examples

### Menu Formatting

```python
content = """
1. Option 1
2. Option 2
3. Option 3
"""

context = ResponseContext(
    user_query="Show me options",
    response_content=content
)

result = formatter.format_response(content, context)
# Output will be formatted as a menu with bolded options
```

### Movie List Formatting

```python
content = """
**Movie 1** (2021)
Director: John Doe
Starring: Jane Smith

**Movie 2** (2022)
Director: Jane Smith
Starring: John Doe
"""

context = ResponseContext(
    user_query="What movies are playing?",
    response_content=content
)

result = formatter.format_response(content, context)
# Output will be formatted as structured movie cards
```

### System Status Formatting

```python
content = """
Service 1: Online
Service 2: Offline
Service 3: Warning
"""

context = ResponseContext(
    user_query="What is the system status?",
    response_content=content
)

result = formatter.format_response(content, context)
# Output will be formatted with status indicators
```

## Testing

The Pretty Output Layer includes comprehensive tests:

```python
# Run tests
python -m pytest tests/test_response_formatter.py

# Run specific test
python -m pytest tests/test_response_formatter.py::TestPrettyOutputLayer::test_format_response_with_menu_layout
```

## Contributing

When contributing to the Pretty Output Layer:

1. Add tests for new functionality
2. Update documentation
3. Follow existing code style
4. Ensure backward compatibility
5. Update performance metrics if needed

## License

This component is part of Karen's AI system and is subject to the project's license terms.