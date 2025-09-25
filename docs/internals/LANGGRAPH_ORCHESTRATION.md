# LangGraph Orchestration Foundation

This document describes the LangGraph orchestration foundation implemented for the dynamic LLM provider management system.

## Overview

The LangGraph orchestration system provides a robust, extensible workflow engine for processing conversations through a series of gates and processing nodes. It supports human-in-the-loop workflows, streaming responses, and comprehensive error handling.

## Architecture

### Core Components

1. **LangGraphOrchestrator** - Main orchestration class
2. **StreamingManager** - Handles streaming integrations
3. **OrchestrationConfig** - Configuration management
4. **API Routes** - REST endpoints for orchestration

### Graph Structure

The orchestration follows this flow:

```
START → auth_gate → safety_gate → memory_fetch → intent_detect → 
planner → router_select → tool_exec → response_synth → approval_gate → 
memory_write → END
```

#### Node Descriptions

- **auth_gate**: Authentication and authorization validation
- **safety_gate**: Content safety and guardrails checking
- **memory_fetch**: Retrieval of conversation context and history
- **intent_detect**: Classification of user intent
- **planner**: Creation of execution plan based on intent
- **router_select**: Selection of appropriate LLM provider and model
- **tool_exec**: Execution of required tools
- **response_synth**: Generation of AI response
- **approval_gate**: Human-in-the-loop approval for sensitive operations
- **memory_write**: Storage of conversation and results

### State Management

The system uses typed state management with the `OrchestrationState` TypedDict:

```python
class OrchestrationState(TypedDict):
    # Input/Output
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    
    # Processing states
    auth_status: Optional[str]
    safety_status: Optional[str]
    detected_intent: Optional[str]
    selected_provider: Optional[str]
    response: Optional[str]
    
    # Error handling
    errors: List[str]
    warnings: List[str]
```

## Configuration

### OrchestrationConfig Options

```python
@dataclass
class OrchestrationConfig:
    enable_auth_gate: bool = True
    enable_safety_gate: bool = True
    enable_memory_fetch: bool = True
    enable_approval_gate: bool = False
    streaming_enabled: bool = False
    checkpoint_enabled: bool = True
    max_retries: int = 3
    timeout_seconds: int = 300
```

### Configuration Examples

**Minimal Configuration** (Auth only):
```python
config = OrchestrationConfig(
    enable_auth_gate=True,
    enable_safety_gate=False,
    enable_memory_fetch=False,
    enable_approval_gate=False
)
```

**Security-Focused Configuration**:
```python
config = OrchestrationConfig(
    enable_auth_gate=True,
    enable_safety_gate=True,
    enable_approval_gate=True,
    streaming_enabled=False
)
```

**Full-Featured Configuration**:
```python
config = OrchestrationConfig(
    enable_auth_gate=True,
    enable_safety_gate=True,
    enable_memory_fetch=True,
    enable_approval_gate=True,
    streaming_enabled=True,
    checkpoint_enabled=True
)
```

## Usage

### Basic Conversation Processing

```python
from src.ai_karen_engine.core.langgraph_orchestrator import create_orchestrator
from langchain_core.messages import HumanMessage

# Create orchestrator
orchestrator = create_orchestrator()

# Process conversation
messages = [HumanMessage(content="Hello, how can you help me?")]
result = await orchestrator.process(messages, user_id="user123")

print(f"Response: {result['response']}")
print(f"Intent: {result['detected_intent']}")
print(f"Provider: {result['selected_provider']}")
```

### Streaming Processing

```python
# Enable streaming
config = OrchestrationConfig(streaming_enabled=True)
orchestrator = create_orchestrator(config)

# Stream processing
async for chunk in orchestrator.stream_process(messages, user_id="user123"):
    for node_name, node_state in chunk.items():
        print(f"Node {node_name} completed")
        if node_state.get('response'):
            print(f"Response: {node_state['response']}")
```

### CopilotKit Integration

```python
from src.ai_karen_engine.core.streaming_integration import get_streaming_manager

streaming_manager = get_streaming_manager()

# Stream for CopilotKit
async for chunk in streaming_manager.stream_for_copilotkit(
    message="Explain quantum computing",
    user_id="user123"
):
    print(f"Chunk type: {chunk['type']}")
    if chunk['type'] == 'message':
        print(f"Content: {chunk['content']}")
```

## API Endpoints

### POST /api/orchestration/chat

Process a conversation through the orchestration graph.

**Request:**
```json
{
    "message": "Hello, how can you help me?",
    "session_id": "optional_session_id",
    "context": {},
    "streaming": false,
    "config": {}
}
```

**Response:**
```json
{
    "response": "I can help you with various tasks...",
    "session_id": "session_123",
    "metadata": {
        "model_used": "gpt-4",
        "tools_used": 0,
        "generation_time": 1.5
    },
    "processing_time": 2.3,
    "errors": [],
    "warnings": []
}
```

### POST /api/orchestration/chat/stream

Stream a conversation with real-time updates.

**Response:** Server-Sent Events stream with JSON chunks:
```
data: {"type": "node_start", "node": "auth_gate", "timestamp": "..."}
data: {"type": "node_end", "node": "auth_gate", "metadata": {...}}
data: {"type": "message", "content": "I can help you...", "timestamp": "..."}
data: [DONE]
```

### GET /api/orchestration/status

Get orchestration system status.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "active_sessions": 5,
    "total_processed": 1234,
    "uptime": 86400.0
}
```

### GET /api/orchestration/health

Simple health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "orchestrator": "available",
    "streaming": "available"
}
```

## Streaming Integration

### CopilotKit Support

The system provides native CopilotKit streaming support through the `CopilotKitStreamer` class:

```python
class StreamChunk:
    type: str  # "node_start", "node_end", "message", "error", "metadata"
    node: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
```

### Server-Sent Events (SSE)

SSE streaming is available through the `ServerSentEventStreamer`:

```python
async for sse_event in streaming_manager.stream_sse(message, user_id):
    # sse_event is formatted as "data: {...}\n\n"
    print(sse_event)
```

### WebSocket Support

WebSocket streaming is provided through the `WebSocketStreamer`:

```python
await streaming_manager.handle_websocket(websocket, user_id, session_id)
```

## Error Handling

### Graceful Degradation

The system handles errors gracefully:

1. **Node Failures**: Individual node failures don't crash the entire pipeline
2. **Missing Dependencies**: Optional dependencies are handled with fallbacks
3. **Invalid Input**: Malformed input is validated and sanitized
4. **Timeout Handling**: Long-running operations have configurable timeouts

### Error Types

- **Authentication Errors**: Invalid or missing user credentials
- **Safety Violations**: Content flagged by safety filters
- **Processing Errors**: Failures in individual nodes
- **Streaming Errors**: Network or connection issues during streaming

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python -m pytest tests/test_langgraph_orchestration.py -v
```

### Basic Functionality Test

Run the simple LangGraph foundation test:

```bash
python test_langgraph_simple.py
```

### Demo Examples

Run the orchestration demo:

```bash
python examples/langgraph_orchestration_demo.py
```

## Integration Points

### Existing System Integration

The orchestration system integrates with existing components:

1. **Authentication**: Uses existing auth system for user validation
2. **Safety**: Integrates with existing guardrails system
3. **Memory**: Connects to existing memory management
4. **LLM Router**: Uses existing provider selection logic
5. **Tools**: Integrates with existing tool execution system

### Future Enhancements

Planned integration points:

1. **Dynamic Provider Registry**: Integration with provider management
2. **Model Store**: Connection to local model management
3. **Advanced Routing**: Policy-based model selection
4. **Human-in-the-Loop**: Full approval workflow implementation
5. **Metrics Collection**: Comprehensive monitoring and analytics

## Performance Considerations

### Optimization Strategies

1. **Checkpointing**: Optional state persistence for long-running workflows
2. **Streaming**: Real-time response generation for better UX
3. **Caching**: Node-level caching for repeated operations
4. **Parallel Processing**: Concurrent execution where possible

### Resource Management

1. **Memory Usage**: Efficient state management with cleanup
2. **CPU Usage**: Optimized node execution with timeouts
3. **Network Usage**: Streaming optimization for bandwidth efficiency
4. **Storage**: Optional checkpointing with configurable retention

## Security

### Security Features

1. **Authentication Gate**: Mandatory user validation
2. **Safety Filtering**: Content safety and guardrails
3. **Approval Gates**: Human oversight for sensitive operations
4. **Input Validation**: Comprehensive input sanitization
5. **Error Sanitization**: Safe error message handling

### Best Practices

1. **Principle of Least Privilege**: Minimal required permissions
2. **Defense in Depth**: Multiple security layers
3. **Audit Logging**: Comprehensive operation logging
4. **Secure Defaults**: Safe configuration defaults
5. **Regular Updates**: Dependency and security updates

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Configuration Issues**: Verify configuration parameters
3. **Authentication Failures**: Check user credentials and permissions
4. **Streaming Issues**: Verify network connectivity and client support
5. **Performance Issues**: Check resource usage and configuration

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode in configuration
config = OrchestrationConfig(debug_mode=True)
```

### Dry-Run Analysis

Use the debug endpoint for dry-run analysis:

```bash
curl -X POST "/api/orchestration/debug/dry-run" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

## Conclusion

The LangGraph orchestration foundation provides a robust, scalable, and extensible workflow engine for the dynamic LLM provider management system. It supports streaming, human-in-the-loop workflows, comprehensive error handling, and seamless integration with existing system components.

The implementation follows best practices for security, performance, and maintainability, making it suitable for production deployment while remaining flexible for future enhancements.