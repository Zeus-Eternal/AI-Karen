# CopilotKit Provider Documentation

## Overview

The CopilotKit Provider is a core system provider that integrates AI-powered development assistance with the unified AI-Karen platform. It provides enterprise-grade functionality including memory integration, action suggestions, and comprehensive observability through the consolidated API endpoints.

## Features

### Core Capabilities
- **Chat Assistance**: AI-powered conversational interface with context awareness
- **Memory Integration**: Unified memory search and commit operations with tenant isolation
- **Action Suggestions**: Intelligent workflow automation and task management
- **Context Awareness**: Real-time context retrieval and relevance scoring
- **Real-time Streaming**: Support for streaming responses and live updates
- **Multi-tenant Support**: Complete tenant isolation and RBAC enforcement

### Available Models

#### copilot-assist
Primary copilot assistance with memory integration and action suggestions.

**Capabilities:**
- chat_assistance
- memory_integration
- action_suggestions
- context_awareness

**Default Settings:**
```json
{
  "top_k": 6,
  "timeout": 30,
  "enable_actions": true,
  "enable_memory": true
}
```

#### copilot-memory
Memory-focused operations for search and commit functionality.

**Capabilities:**
- memory_search
- memory_commit
- tenant_isolation
- audit_logging

**Default Settings:**
```json
{
  "top_k": 12,
  "timeout": 15,
  "enable_audit": true
}
```

#### copilot-actions
Action suggestion and workflow automation.

**Capabilities:**
- action_suggestions
- workflow_automation
- task_management
- document_operations

**Default Settings:**
```json
{
  "confidence_threshold": 0.6,
  "max_actions": 5
}
```

## API Integration

The CopilotKit Provider integrates with the following unified API endpoints:

### `/copilot/assist`
Primary copilot assistance endpoint with comprehensive functionality.

**Request Schema:**
```python
{
  "user_id": "string",
  "org_id": "string (optional)",
  "message": "string (1-8000 chars)",
  "top_k": "integer (1-50, default: 6)",
  "context": "object (optional)"
}
```

**Response Schema:**
```python
{
  "answer": "string",
  "context": [ContextHit],
  "actions": [SuggestedAction],
  "timings": {
    "memory_search_ms": "float",
    "llm_generation_ms": "float", 
    "action_generation_ms": "float",
    "memory_writeback_ms": "float",
    "total_ms": "float"
  },
  "correlation_id": "string"
}
```

### `/memory/search`
Unified memory query endpoint.

**Request Schema:**
```python
{
  "user_id": "string",
  "org_id": "string (optional)",
  "query": "string (1-4096 chars)",
  "top_k": "integer (1-50, default: 12)"
}
```

### `/memory/commit`
Unified memory storage endpoint.

**Request Schema:**
```python
{
  "user_id": "string",
  "org_id": "string (optional)",
  "text": "string (1-16000 chars)",
  "tags": ["string"],
  "importance": "integer (1-10, default: 5)",
  "decay": "string (short|medium|long|pinned, default: short)"
}
```

## Usage Examples

### Basic Provider Usage

```python
from ai_karen_engine.integrations.provider_registry import get_provider_registry

# Get the provider registry
registry = get_provider_registry()

# Get CopilotKit provider instance
copilot = registry.get_provider("copilotkit")

# Initialize the provider
await copilot.initialize()

# Use assistance functionality
response = await copilot.assist(
    message="Help me understand the memory system",
    user_id="user123",
    org_id="org456",
    top_k=6
)

print(f"Answer: {response['answer']}")
print(f"Context hits: {len(response['context'])}")
print(f"Suggested actions: {len(response['actions'])}")
```

### Memory Operations

```python
# Search memory
search_results = await copilot.search_memory(
    query="memory system architecture",
    user_id="user123",
    org_id="org456",
    top_k=10
)

# Commit new memory
commit_result = await copilot.commit_memory(
    text="Important insight about memory decay policies",
    user_id="user123",
    org_id="org456",
    tags=["insight", "memory"],
    importance=8,
    decay="long"
)
```

### Provider Status and Health

```python
# Check provider status
status = copilot.get_status()
print(f"Provider health: {status['health_status']}")
print(f"Capabilities: {status['capabilities']}")

# Get available models
models = copilot.get_models()
print(f"Available models: {models}")
```

## Configuration

### Environment Variables

- `COPILOTKIT_API_BASE`: Base URL for API endpoints (default: http://localhost:8000)
- `COPILOTKIT_TIMEOUT`: Request timeout in seconds (default: 30)
- `COPILOTKIT_MODEL`: Default model to use (default: copilot-assist)

### Provider Configuration

```python
# Custom provider configuration
copilot = registry.get_provider("copilotkit", 
    model="copilot-memory",
    api_base="https://api.example.com",
    timeout=60,
    custom_setting="value"
)
```

## Integration with Extensions

The CopilotKit Provider is automatically registered in the provider registry and is available to all extensions and plugins. Extensions can access the provider through the standard registry interface:

```python
from ai_karen_engine.integrations.provider_registry import get_provider_registry

class MyExtension(BaseExtension):
    async def initialize(self):
        registry = get_provider_registry()
        self.copilot = registry.get_provider("copilotkit")
        await self.copilot.initialize()
    
    async def handle_user_query(self, message: str, user_id: str):
        response = await self.copilot.assist(
            message=message,
            user_id=user_id
        )
        return response
```

## Observability and Monitoring

The CopilotKit Provider includes comprehensive observability features:

### Metrics
- Request counts and success rates
- Latency metrics (P50, P95, P99)
- Memory quality metrics
- Action suggestion effectiveness

### Logging
- Structured JSON logging with correlation IDs
- Request/response tracing
- Error logging with context
- Performance monitoring

### Health Checks
- Provider health status
- Dependency availability
- API connectivity verification

## Security and Compliance

### RBAC Integration
- Scope-based permissions (chat:write, memory:read, memory:write)
- Tenant isolation at all layers
- Cross-tenant access prevention

### Privacy Protection
- PII protection in logs and UI
- Data export and erasure capabilities
- Audit trail maintenance

### Security Features
- HTTPS enforcement in production
- CORS allowlist configuration
- Rate limiting and abuse prevention

## Troubleshooting

### Common Issues

1. **Provider Not Available**
   - Ensure CopilotKit provider is properly installed
   - Check import paths and dependencies
   - Verify provider registration in logs

2. **API Connectivity Issues**
   - Verify API base URL configuration
   - Check network connectivity
   - Review timeout settings

3. **Authentication Failures**
   - Verify RBAC configuration
   - Check user permissions and scopes
   - Review tenant isolation settings

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger("ai_karen_engine.integrations.copilotkit_provider").setLevel(logging.DEBUG)
```

## Performance Optimization

### SLO Targets
- Vector query latency: P95 < 50ms
- First token latency: P95 < 1.2s
- End-to-end turn latency: P95 < 3s

### Optimization Strategies
- Connection pooling and keep-alive
- Response caching for hot queries
- Model preloading and warming
- Batch processing for bulk operations

## Version History

### v1.0.0
- Initial release with unified API integration
- Core assistance, memory, and action functionality
- Multi-tenant support and RBAC integration
- Comprehensive observability and monitoring

## Support and Contributing

For issues, feature requests, or contributions related to the CopilotKit Provider:

1. Check existing documentation and troubleshooting guides
2. Review provider logs and health status
3. Submit issues with detailed reproduction steps
4. Follow the standard contribution guidelines for code changes

The CopilotKit Provider is a core component of the AI-Karen platform and is actively maintained by the core development team.