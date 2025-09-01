# AI Karen Engine - Services Layer

The services layer provides the business logic and AI orchestration capabilities for the AI Karen platform. It includes AI orchestration, plugin management, memory services, analytics, and tool management.

## Core Services

### AI Orchestrator (`ai_orchestrator.py`)

Coordinates AI operations across multiple models and providers:

- **FlowManager**: Manages conversation flows and state transitions
- **DecisionEngine**: Routes requests to appropriate AI models
- **ContextManager**: Manages conversation context and history
- **PromptManager**: Optimizes and manages prompts for different models

#### Usage Example
```python
from ai_karen_engine.services import AIOrchestrator

orchestrator = AIOrchestrator()

# Process AI request with context
response = await orchestrator.process_request(
    prompt="Analyze this data",
    context={"user_id": "123", "session_id": "abc"},
    model_preference="gpt-4"
)
```

### Plugin Service (`plugin_service.py`)

Manages plugin discovery, execution, and lifecycle:

- **Plugin Discovery**: Automatic plugin detection and registration
- **Execution Engine**: Secure plugin execution with sandboxing
- **Marketplace Integration**: Plugin marketplace connectivity
- **Lifecycle Management**: Plugin installation, updates, and removal

#### Key Functions
```python
from ai_karen_engine.services import get_plugin_service

plugin_service = get_plugin_service()

# Discover and register all plugins
await discover_and_register_all_plugins()

# Execute plugin with parameters
result = await execute_plugin_simple(
    plugin_name="data-processor",
    params={"input": "data"},
    user_context={"user_id": "123"}
)

# Get marketplace information
marketplace_info = get_plugin_marketplace_info()
```

### Memory Service (`memory_service.py`)

Persistent memory system for conversations and context:

- **WebUIMemoryService**: Memory management for web UI interactions
- **Context Storage**: Long-term conversation memory
- **Retrieval System**: Semantic search and context retrieval
- **Multi-tenant Support**: Isolated memory per tenant

#### Usage Example
```python
from ai_karen_engine.services import WebUIMemoryService

memory_service = WebUIMemoryService()

# Store conversation context
await memory_service.store_context(
    user_id="123",
    conversation_id="conv_456",
    context={"message": "Hello", "response": "Hi there!"}
)

# Retrieve relevant context
context = await memory_service.retrieve_context(
    user_id="123",
    query="previous conversation about data"
)
```

### Tool Service (`tool_service.py`)

Manages AI tools and their execution:

- **Tool Registry**: Registration and discovery of available tools
- **Tool Execution**: Secure tool execution with validation
- **Tool Categories**: Organization of tools by functionality
- **Tool Metadata**: Rich metadata for tool discovery

#### Tool Management
```python
from ai_karen_engine.services import (
    get_tool_service, 
    register_core_tools,
    ToolCategory
)

# Initialize tool service
tool_service = get_tool_service()

# Register core tools
register_core_tools()

# Execute tool
result = await tool_service.execute_tool(
    tool_name="web-scraper",
    inputs={"url": "https://example.com"},
    user_context={"user_id": "123"}
)
```

### Analytics Service (`analytics_service.py`)

Performance monitoring and business intelligence:

- **Performance Tracking**: Real-time performance metrics
- **Usage Analytics**: User behavior and system usage patterns
- **Performance Timer**: Execution time measurement
- **Dashboard Integration**: Data for analytics dashboards

#### Analytics Usage
```python
from ai_karen_engine.services import (
    get_analytics_service,
    track_performance,
    PerformanceTimer
)

analytics = get_analytics_service()

# Track performance with decorator
@track_performance("data_processing")
async def process_data(data):
    return processed_data

# Manual performance tracking
with PerformanceTimer("custom_operation") as timer:
    result = await expensive_operation()
    timer.add_metadata({"records_processed": len(result)})
```

### Analytics Dashboard (`analytics_dashboard.py`)

Dashboard service for analytics visualization:

- **Dashboard Management**: Create and manage analytics dashboards
- **Data Aggregation**: Aggregate metrics for visualization
- **Real-time Updates**: Live dashboard updates
- **Custom Metrics**: Support for custom business metrics

## External Service Integrations

### LLM Providers

The services layer integrates with multiple LLM providers:

- **OpenAI**: GPT models and embeddings
- **Gemini**: Google's Gemini models
- **DeepSeek**: DeepSeek model integration
- **LlamaCpp**: Local GGUF model execution via llama-cpp-python

#### Provider Access
```python
from ai_karen_engine.services import (
    get_openai_service,
    get_gemini_service,
    get_deepseek_client,
    get_llamacpp_engine
)

# Use specific provider
openai_service = get_openai_service()
response = await openai_service.complete(prompt="Hello")
```

## Service Registry

The services layer uses a registry pattern for dynamic service discovery:

```python
from ai_karen_engine.services import SERVICES_REGISTRY

# Get service by name
service = SERVICES_REGISTRY["openai"]()

# Register custom service
SERVICES_REGISTRY["custom"] = get_custom_service
```

## Configuration

Services are configured through environment variables and configuration files:

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key
- `GEMINI_API_KEY`: Google Gemini API key
- `DEEPSEEK_API_KEY`: DeepSeek API key
- `PLUGIN_DISCOVERY_PATH`: Plugin discovery directories
- `MEMORY_BACKEND`: Memory storage backend
- `ANALYTICS_ENABLED`: Enable analytics collection

### Service Configuration
```python
from ai_karen_engine.services import initialize_plugin_service

# Initialize with custom configuration
await initialize_plugin_service(
    discovery_paths=["/custom/plugins"],
    sandbox_enabled=True,
    max_execution_time=30
)
```

## Error Handling

Services implement comprehensive error handling:

```python
from ai_karen_engine.core import ServiceError

try:
    result = await service.process_request(data)
except ServiceError as e:
    logger.error(f"Service error: {e.error_code} - {e.message}")
    # Handle specific error types
```

## Monitoring and Metrics

Services provide extensive monitoring capabilities:

### Performance Metrics
- Request latency and throughput
- Error rates and types
- Resource utilization
- Service health status

### Business Metrics
- User engagement and activity
- Feature usage patterns
- AI model performance
- Plugin execution statistics

## Testing

Comprehensive test coverage for all services:

```bash
# Run all service tests
pytest tests/services/

# Run specific service tests
pytest tests/services/test_ai_orchestrator.py
pytest tests/services/test_plugin_service.py
pytest tests/services/test_memory_service.py
```

## Best Practices

### Service Design
1. **Single Responsibility**: Each service has a focused purpose
2. **Dependency Injection**: Use the core DI system
3. **Error Handling**: Implement comprehensive error handling
4. **Async/Await**: Use async patterns for I/O operations
5. **Configuration**: Support flexible configuration options

### Performance
1. **Caching**: Implement appropriate caching strategies
2. **Connection Pooling**: Use connection pools for external services
3. **Rate Limiting**: Implement rate limiting for external APIs
4. **Monitoring**: Include performance monitoring

### Security
1. **Input Validation**: Validate all inputs
2. **Authentication**: Verify user authentication
3. **Authorization**: Check user permissions
4. **Audit Logging**: Log security-relevant events

## Extension Points

### Custom Services
Create custom services by following the established patterns:

```python
from ai_karen_engine.core import BaseService

class CustomService(BaseService):
    async def initialize(self):
        # Service initialization
        pass
    
    async def process(self, data):
        # Service logic
        return result
```

### Custom Tools
Register custom tools with the tool service:

```python
from ai_karen_engine.services import BaseTool, ToolMetadata

class CustomTool(BaseTool):
    metadata = ToolMetadata(
        name="custom-tool",
        description="Custom tool description",
        category=ToolCategory.UTILITY
    )
    
    async def execute(self, inputs, context):
        # Tool implementation
        return result
```

## Contributing

When contributing to the services layer:

1. Follow established service patterns
2. Include comprehensive tests
3. Add appropriate monitoring and logging
4. Update documentation
5. Consider backward compatibility
6. Follow security best practices