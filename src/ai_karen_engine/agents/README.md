# Agent Integration System

The Agent Integration system provides a unified interface for connecting UI components with the backend agent orchestration system, supporting multiple execution modes (Native, LangGraph, DeepAgents).

## Architecture

The Agent Integration system consists of several key components:

### Core Components

1. **Models** (`models.py`)
   - Defines data structures for requests, responses, and agent information
   - Includes type validation and serialization support
   - Key models: `AgentRequest`, `AgentResponse`, `AgentInfo`, `AgentConfig`

2. **Execution Handlers** (`execution_handlers.py`)
   - Implements handlers for different execution modes
   - `NativeExecutionHandler`: Direct LLM execution
   - `LangGraphExecutionHandler`: Graph-based orchestration
   - `DeepAgentsExecutionHandler`: Multi-agent system

3. **Lifecycle Manager** (`lifecycle_manager.py`)
   - Manages agent lifecycle (creation, status tracking, cleanup)
   - Provides metrics collection and health monitoring
   - Handles automatic cleanup of inactive agents

4. **Capability Router** (`capability_router.py`)
   - Routes requests to appropriate agents based on capabilities
   - Implements scoring algorithm for agent selection
   - Supports load balancing and health considerations

5. **Integration Service** (`integration_service.py`)
   - Main service that orchestrates all components
   - Provides unified API for agent operations
   - Handles request routing and response processing

6. **Authentication & Authorization** (`auth.py`)
   - Implements role-based access control
   - Provides permission checking decorators
   - Supports rate limiting and audit logging

7. **API Routes** (`agent_integration_routes.py`)
   - FastAPI endpoints for agent interactions
   - Supports both synchronous and streaming responses
   - Includes authentication and authorization

## Features

### Execution Modes

1. **Native Mode**
   - Direct LLM execution
   - Fastest response time
   - Basic capabilities (text generation, code generation)

2. **LangGraph Mode**
   - Graph-based orchestration
   - Advanced reasoning capabilities
   - Memory access and tool use

3. **DeepAgents Mode**
   - Multi-agent collaboration
   - Complex problem solving
   - Full capability set including multimodal

### Agent Capabilities

- **Text Generation**: Basic text generation
- **Code Generation**: Code writing and explanation
- **Analysis**: Data analysis and insights
- **Reasoning**: Logical reasoning and inference
- **Memory Access**: Access to conversation memory
- **Tool Use**: External tool integration
- **Multimodal**: Processing of multiple data types
- **Streaming**: Real-time response streaming

### Authentication & Authorization

The system implements role-based access control:

- **Viewer**: Read-only access to agents
- **User**: Execute agents and view metrics
- **Developer**: Create/modify agents, advanced access
- **Admin**: Full system access

### Performance Monitoring

- Request/response metrics
- Agent health tracking
- Resource usage monitoring
- Success/error rate tracking
- Response time analytics

## Usage

### Basic Agent Execution

```python
from ai_karen_engine.agents import get_agent_integration_service, AgentRequest, AgentExecutionMode

# Get integration service
service = get_agent_integration_service()

# Create request
request = AgentRequest(
    message="Hello, how can you help me?",
    execution_mode=AgentExecutionMode.NATIVE,
    capabilities_required=[AgentCapability.TEXT_GENERATION]
)

# Execute request
response = await service.execute_request(request)
print(response.response)
```

### Streaming Execution

```python
# Create streaming request
request = AgentRequest(
    message="Explain quantum computing",
    execution_mode=AgentExecutionMode.LANGGRAPH,
    enable_streaming=True
)

# Stream responses
async for stream_response in service.execute_request_stream(request):
    print(stream_response.chunk.content)
```

### Agent Management

```python
# Create a new agent
agent = await service.create_agent(
    agent_id="custom_agent",
    name="Custom Agent",
    description="A specialized agent for data analysis",
    execution_mode=AgentExecutionMode.DEEP_AGENTS,
    config={
        "model_name": "gpt-4",
        "temperature": 0.7,
        "capabilities": ["analysis", "reasoning"]
    }
)

# Get agent information
agent_info = await service.get_agent_info("custom_agent")
print(f"Agent status: {agent_info.status}")

# Terminate agent
await service.terminate_agent("custom_agent")
```

### API Usage

The system provides REST API endpoints:

- `POST /api/agents/execute` - Execute agent request
- `POST /api/agents/execute/stream` - Execute with streaming
- `GET /api/agents/` - List all agents
- `GET /api/agents/{agent_id}` - Get agent info
- `POST /api/agents/` - Create new agent
- `DELETE /api/agents/{agent_id}` - Delete agent
- `GET /api/agents/{agent_id}/metrics` - Get agent metrics
- `GET /api/agents/system/metrics` - Get system metrics

## Configuration

### Agent Configuration

```python
config = {
    "execution_mode": "native",
    "model_name": "gpt-3.5-turbo",
    "provider": "openai",
    "temperature": 0.7,
    "max_tokens": 2048,
    "timeout_seconds": 60,
    "enable_streaming": True,
    "capabilities": ["text_generation", "analysis"],
    "custom_config": {
        "system_prompt": "You are a helpful assistant.",
        "response_format": "json"
    }
}
```

### System Configuration

The system can be configured through environment variables or configuration files:

- `AGENT_DEFAULT_TIMEOUT`: Default request timeout (seconds)
- `AGENT_MAX_CONCURRENT_REQUESTS`: Maximum concurrent requests
- `AGENT_METRICS_RETENTION_DAYS`: Metrics retention period
- `AGENT_CLEANUP_INTERVAL`: Cleanup interval (seconds)

## Monitoring and Observability

### Metrics

The system collects comprehensive metrics:

- Request count and success rate
- Response time statistics
- Agent health and availability
- Resource usage (CPU, memory)
- Error rates and types

### Logging

Structured logging is implemented with correlation IDs:

```python
import logging
logger = logging.getLogger("ai_karen_engine.agents")

logger.info(
    "Agent request processed",
    extra={
        "request_id": request.request_id,
        "agent_id": request.agent_id,
        "execution_mode": request.execution_mode.value,
        "processing_time": response.processing_time
    }
)
```

### Health Checks

Health check endpoints provide system status:

```bash
curl http://localhost:8000/api/agents/system/health
```

Response:
```json
{
    "status": "healthy",
    "timestamp": "2023-12-20T10:30:00Z",
    "agents": {
        "total": 3,
        "healthy": 3,
        "unhealthy": 0
    },
    "metrics": {
        "total_requests": 1250,
        "success_rate": 0.98,
        "average_response_time": 1.2
    }
}
```

## Security

### Authentication

The system integrates with the existing authentication infrastructure:

- JWT token validation
- User role verification
- Permission-based access control
- Rate limiting per user/role

### Authorization

Role-based permissions control access to features:

- Agent creation/deletion requires admin role
- Streaming requires user role or higher
- DeepAgents mode requires developer role or higher
- System metrics require admin role

### Audit Logging

All access attempts are logged:

```json
{
    "timestamp": "2023-12-20T10:30:00Z",
    "user_id": "user123",
    "action": "execute_agent",
    "resource": "native_agent",
    "result": "success",
    "ip_address": "192.168.1.100"
}
```

## Integration with Existing Systems

The Agent Integration system is designed to work with existing components:

- **Memory System**: Access to conversation and episodic memory
- **Model Orchestrator**: Integration with LLM providers
- **Plugin System**: Support for custom tools and extensions
- **Monitoring System**: Metrics collection and alerting

## Best Practices

1. **Agent Selection**: Use the capability router for optimal agent selection
2. **Error Handling**: Implement proper error handling and retry logic
3. **Resource Management**: Monitor resource usage and set appropriate limits
4. **Security**: Always validate user permissions before operations
5. **Monitoring**: Track metrics and set up alerts for anomalies
6. **Lifecycle Management**: Properly initialize and cleanup agents

## Troubleshooting

### Common Issues

1. **Agent Not Available**: Check agent status and health
2. **Permission Denied**: Verify user roles and permissions
3. **Timeout Errors**: Adjust timeout settings or check agent performance
4. **Memory Issues**: Monitor memory usage and implement cleanup
5. **Rate Limiting**: Check rate limits and implement backoff

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("ai_karen_engine.agents").setLevel(logging.DEBUG)
```

### Health Diagnostics

Run health checks:

```python
service = get_agent_integration_service()
metrics = await service.get_system_metrics()
print(f"System health: {metrics}")
```

## Future Enhancements

Planned improvements include:

1. **Advanced Routing**: Machine learning-based agent selection
2. **Auto-scaling**: Dynamic agent creation based on load
3. **Federation**: Support for distributed agent systems
4. **Advanced Monitoring**: Real-time dashboards and alerts
5. **Performance Optimization**: Caching and connection pooling