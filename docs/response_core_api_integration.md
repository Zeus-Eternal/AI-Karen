# Response Core API Integration

This document describes the API integration for the Response Core Orchestrator system, which provides a unified interface between the existing ChatOrchestrator and the new ResponseOrchestrator.

## Overview

The Response Core API integration provides:

1. **Backward Compatibility**: Existing chat endpoints continue to work unchanged
2. **New Response Core Endpoints**: Enhanced endpoints using the ResponseOrchestrator
3. **Compatibility Layer**: Seamless fallback between orchestrators
4. **Model Management**: APIs for managing system models and training
5. **Proper Error Handling**: Comprehensive error handling and response transformation

## API Endpoints

### Response Core Chat Endpoints

#### POST `/api/response-core/chat`
Primary endpoint for Response Core orchestrator with structured responses.

**Request:**
```json
{
  "message": "Hello, how are you?",
  "user_id": "user_123",
  "tenant_id": "tenant_456",
  "conversation_id": "conv_789",
  "session_id": "session_abc",
  "ui_caps": {
    "copilotkit": true,
    "persona_set": false,
    "project_name": "my_project"
  },
  "config_overrides": {
    "local_only": true,
    "enable_copilotkit": false
  },
  "stream": false,
  "include_context": true,
  "attachments": [],
  "metadata": {}
}
```

**Response:**
```json
{
  "intent": "general_assist",
  "persona": "assistant",
  "mood": "neutral",
  "content": "Hello! How can I help you today?",
  "metadata": {
    "model_used": "local",
    "context_tokens": 1024,
    "generation_time_ms": 150
  },
  "correlation_id": "req_123",
  "processing_time": 0.15,
  "used_fallback": false,
  "context_used": true
}
```

#### POST `/api/response-core/chat/compatible`
Compatible endpoint that can use either orchestrator with automatic fallback.

**Features:**
- Tries ResponseOrchestrator first
- Falls back to ChatOrchestrator on failure
- Returns legacy-compatible response format
- Maintains backward compatibility

#### POST `/api/response-core/chat/stream`
Streaming endpoint using Response Core orchestrator.

**Features:**
- Server-sent events (SSE) streaming
- Real-time response generation
- Fallback to existing streaming on failure
- Compatible with existing streaming clients

### Model Management Endpoints

#### POST `/api/response-core/models`
Manage system models, HuggingFace models, and custom models.

**Operations:**
- `list`: List available models
- `configure`: Update model configuration
- `download`: Download new models
- `delete`: Remove models

**Request:**
```json
{
  "operation": "list",
  "model_id": "llama-cpp",
  "config": {
    "quantization": "Q4_K_M",
    "context_length": 4096
  },
  "filters": {
    "type": "llm",
    "status": "available"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system_models": [
      {
        "id": "llama-cpp",
        "status": "available",
        "type": "llm"
      }
    ],
    "huggingface_models": [],
    "custom_models": []
  },
  "message": "Models listed successfully"
}
```

### Training Management Endpoints

#### POST `/api/response-core/training`
Manage autonomous learning and model training.

**Operations:**
- `start`: Start training job
- `stop`: Stop training job
- `status`: Get training status
- `schedule`: Schedule autonomous training

**Request:**
```json
{
  "operation": "start",
  "model_id": "spacy_model",
  "dataset_id": "training_data_v1",
  "config": {
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 10
  },
  "schedule": "0 2 * * *"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "job_123",
  "status": "started",
  "data": {
    "model_id": "spacy_model",
    "estimated_duration": "2 hours"
  },
  "message": "Training started successfully"
}
```

### Configuration Endpoints

#### GET `/api/response-core/config`
Get current Response Core configuration.

#### POST `/api/response-core/config`
Update Response Core configuration (admin only).

#### GET `/api/response-core/health`
Health check endpoint with diagnostics.

## Enhanced Existing Endpoints

### Orchestration Routes

#### POST `/api/orchestration/chat/response-core`
Alternative chat endpoint in orchestration routes using Response Core.

### Chat Runtime Routes

#### POST `/api/chat/runtime/response-core`
Response Core version of the chat runtime endpoint.

## Compatibility Layer

The `ResponseCoreCompatibilityLayer` provides seamless integration:

### Features

1. **Automatic Routing**: Intelligently routes requests to appropriate orchestrator
2. **Fallback Mechanism**: Falls back to alternative orchestrator on failure
3. **Unified Interface**: Provides consistent API regardless of underlying orchestrator
4. **Preference Logic**: Uses heuristics to determine optimal orchestrator

### Usage

```python
from ai_karen_engine.middleware.response_core_integration import get_compatibility_layer

layer = get_compatibility_layer()

result = await layer.process_chat_request(
    message="Hello",
    user_id="user_123",
    conversation_id="conv_456",
    use_response_core=True
)
```

### Preference Logic

The compatibility layer prefers Response Core for:
- Requests with `local_only=True`
- Analysis-related requests ("analyze", "explain")
- Help and guidance requests
- Persona-related requests

## Error Handling

### Response Core Errors
- Graceful degradation to error responses
- Fallback to ChatOrchestrator when enabled
- Comprehensive error logging and correlation

### Fallback Behavior
1. Try primary orchestrator
2. On failure, try fallback orchestrator (if enabled)
3. Return structured error response if both fail
4. Log all failures with correlation IDs

### Error Response Format
```json
{
  "intent": "error",
  "persona": "assistant",
  "mood": "apologetic",
  "content": "I apologize, but I encountered an error: ...",
  "metadata": {
    "error": "Error details",
    "orchestrator": "response_core",
    "used_fallback": true
  },
  "correlation_id": "req_123",
  "processing_time": 0.05,
  "used_fallback": true,
  "context_used": false
}
```

## Security and Authorization

### Admin-Only Operations
- Model management operations
- Training operations
- Configuration updates

### User-Level Operations
- Chat requests
- Configuration retrieval
- Health checks

### Authentication
- Uses existing `get_current_user` dependency
- Maintains existing RBAC patterns
- Supports tenant isolation

## Middleware Integration

### ResponseCoreIntegrationMiddleware
Optional middleware for automatic routing based on:
- Request headers (`X-Use-Response-Core: true`)
- Query parameters (`?use_response_core=true`)
- URL patterns (contains "response-core")

### Usage
```python
from ai_karen_engine.middleware.response_core_integration import ResponseCoreIntegrationMiddleware

app.add_middleware(
    ResponseCoreIntegrationMiddleware,
    enable_response_core=True,
    fallback_enabled=True
)
```

## Testing

### Test Coverage
- API endpoint functionality
- Compatibility layer behavior
- Error handling and fallback
- Model validation
- Authentication and authorization

### Running Tests
```bash
# Run all Response Core API tests
python -m pytest tests/test_response_core_api_simple.py -v

# Run specific test categories
python -m pytest tests/test_response_core_api_simple.py::TestResponseCoreCompatibilityLayer -v
```

## Migration Guide

### For Existing Applications

1. **No Changes Required**: Existing endpoints continue to work
2. **Gradual Migration**: Use compatible endpoints for testing
3. **Feature Adoption**: Gradually adopt new Response Core features
4. **Configuration**: Enable Response Core features as needed

### For New Applications

1. **Use Response Core Endpoints**: Start with `/api/response-core/chat`
2. **Enable Fallback**: Use compatible endpoints for reliability
3. **Leverage Features**: Use model management and training APIs
4. **Monitor Health**: Use health endpoints for monitoring

## Performance Considerations

### Response Core Benefits
- Local-first processing
- Structured prompt generation
- Consistent persona handling
- Optimized memory usage

### Fallback Overhead
- Minimal overhead for successful requests
- Additional latency only on failures
- Configurable fallback behavior

### Monitoring
- Prometheus metrics for both orchestrators
- Request correlation for debugging
- Performance comparison dashboards

## Future Enhancements

### Planned Features
1. **Advanced Routing**: ML-based orchestrator selection
2. **A/B Testing**: Built-in A/B testing for orchestrators
3. **Performance Optimization**: Caching and optimization
4. **Enhanced Monitoring**: Detailed performance analytics

### Migration Path
1. **Phase 1**: Compatibility layer (current)
2. **Phase 2**: Feature parity and optimization
3. **Phase 3**: Full migration to Response Core
4. **Phase 4**: Legacy orchestrator deprecation

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure proper user context
2. **Orchestrator Failures**: Check logs for specific errors
3. **Configuration Issues**: Verify config overrides
4. **Performance Issues**: Monitor processing times

### Debug Endpoints
- `/api/response-core/health`: System health
- `/api/orchestration/debug/dry-run`: Dry-run analysis
- Correlation IDs for request tracing

### Logging
- Structured logging with correlation IDs
- Error categorization and tracking
- Performance metrics and alerts