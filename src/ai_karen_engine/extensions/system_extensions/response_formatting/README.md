# Intelligent Response Formatting Extension

This extension provides intelligent response formatting based on content type and context detection. It integrates with the existing Kari AI extensions SDK and theme system to provide beautiful, contextual formatting for different types of AI responses.

## Features

- **Intelligent Content Detection**: Automatically detects content types (movie, recipe, weather, news, product, travel, code) using NLP analysis
- **Plugin Architecture**: Extensible formatter system that integrates with the existing extensions SDK
- **Theme Integration**: Seamless integration with the existing theme manager and design tokens
- **Fallback Handling**: Graceful degradation to default formatting when specific formatters fail
- **Performance Monitoring**: Built-in metrics and health checks for production deployment

## Supported Content Types

- **Movie**: Formats movie information with images, ratings, and reviews
- **Recipe**: Formats recipes with ingredients, steps, and cooking information
- **Weather**: Formats weather data with icons, forecasts, and conditions
- **News**: Formats news articles with headlines, sources, and publication dates
- **Product**: Formats product information with images, specs, and pricing
- **Travel**: Formats travel information with maps, itineraries, and booking links
- **Code**: Formats code with syntax highlighting and explanations
- **Default**: Basic formatting for general content

## Architecture

### Core Components

1. **ResponseFormatter (Base Class)**: Abstract base class for all formatters
2. **ResponseFormatterRegistry**: Manages formatter plugins and selection
3. **ContentTypeDetector**: Detects content types using NLP and pattern matching
4. **ResponseFormattingIntegration**: Main integration layer with existing systems

### Integration Points

- **Extensions SDK**: Integrates with the existing plugin architecture
- **Theme Manager**: Uses existing theme system and design tokens
- **NLP Services**: Leverages spaCy and DistilBERT for content analysis
- **LLM Orchestrator**: Integrates with the prompt-first framework

## Installation

The extension is automatically available as part of the Kari AI system. To use it programmatically:

```python
from extensions.response_formatting import ResponseFormattingIntegration

# Get the integration instance
integration = ResponseFormattingIntegration()

# Format a response
formatted_response = await integration.format_response(
    user_query="What's the weather like?",
    response_content="It's sunny and 75°F today",
    user_preferences={"theme": "light"},
    theme_context={"current": "light"},
    session_data={"user_id": "123"}
)
```

## Creating Custom Formatters

To create a custom formatter, extend the `ResponseFormatter` base class:

```python
from extensions.response_formatting.base import ResponseFormatter, FormattedResponse, ContentType

class CustomFormatter(ResponseFormatter):
    def __init__(self):
        super().__init__("custom-formatter", "1.0.0")
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        # Return True if this formatter can handle the content
        return "custom" in content.lower()
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        # Format the content and return FormattedResponse
        formatted_content = f"<div class='custom-format'>{content}</div>"
        
        return FormattedResponse(
            content=formatted_content,
            content_type=ContentType.DEFAULT,
            theme_requirements=["custom-theme"],
            metadata={"formatter": self.name},
            css_classes=["custom-formatted"]
        )
    
    def get_theme_requirements(self) -> List[str]:
        return ["custom-theme"]

# Register the formatter
integration.register_formatter(CustomFormatter())
```

## Configuration

The extension supports the following configuration options:

- `enable_nlp_detection`: Enable NLP-based content type detection (default: true)
- `fallback_to_default`: Fall back to default formatter on errors (default: true)
- `confidence_threshold`: Minimum confidence threshold for content type detection (default: 0.3)

## API Reference

### ResponseFormattingIntegration

Main integration class providing the following methods:

- `format_response(user_query, response_content, ...)`: Format a response
- `register_formatter(formatter)`: Register a new formatter
- `unregister_formatter(formatter_name)`: Unregister a formatter
- `detect_content_type(user_query, response_content)`: Detect content type
- `get_available_formatters()`: Get list of available formatters
- `get_integration_metrics()`: Get performance metrics

### ResponseFormatter (Base Class)

Abstract base class for formatters:

- `can_format(content, context)`: Check if formatter can handle content
- `format_response(content, context)`: Format the content
- `get_theme_requirements()`: Get required theme components
- `get_confidence_score(content, context)`: Get confidence score

## Testing

Run the test suite:

```bash
cd extensions/response-formatting
python3 run_tests.py
```

## Performance

The extension is designed for production use with:

- Efficient content type detection using pattern matching and NLP
- Caching of formatted responses
- Graceful error handling and fallback mechanisms
- Comprehensive metrics and monitoring

## Requirements

- Python 3.8+
- Existing Kari AI extensions SDK
- Access to theme manager and NLP services (optional)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Create a new formatter by extending `ResponseFormatter`
2. Add appropriate content detection patterns
3. Integrate with the existing theme system
4. Add comprehensive tests
5. Update documentation

## Changelog

### v1.0.0
- Initial release
- Support for 8 content types (movie, recipe, weather, news, product, travel, code, default)
- Integration with extensions SDK and theme system
- NLP-based content detection
- Comprehensive test suite
- Production-ready monitoring and metrics