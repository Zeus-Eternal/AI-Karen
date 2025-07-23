# AI Karen Engine

The AI Karen Engine is the core runtime system that powers the AI Karen platform. It provides a modular, production-ready architecture for AI-powered applications with enterprise-grade features including multi-tenancy, plugin systems, extensions, and comprehensive observability.

## Architecture Overview

The engine is organized into several key subsystems:

```
ai_karen_engine/
├── core/           # Core infrastructure and services
├── services/       # Business logic and AI orchestration
├── api_routes/     # REST API endpoints
├── database/       # Multi-tenant data layer
├── extensions/     # High-level extension system
├── plugins/        # Plugin execution and management
├── clients/        # External service integrations
├── security/       # Security and compliance
├── integrations/   # Third-party integrations
└── utils/          # Shared utilities
```

## Key Components

### LLM Orchestrator
Military-grade LLM routing engine with:
- Zero-trust model routing with cryptographic validation
- Hardware-isolated execution domains
- Adaptive load balancing with circuit breakers
- Comprehensive observability and audit trails

### Plugin System
Secure plugin execution environment featuring:
- Sandboxed plugin execution
- Role-based access control
- Metrics collection and monitoring
- Memory persistence integration

### Extension System
High-level architecture for building feature-rich modules:
- Compose multiple plugins into cohesive features
- Rich UI integration capabilities
- Independent data management
- Marketplace distribution support

### Multi-Tenant Database
Production-ready data layer with:
- PostgreSQL with vector extensions
- Redis for caching and real-time features
- DuckDB for analytics
- Milvus for vector similarity search

## Core Services

### AI Orchestrator
Coordinates AI operations across multiple models and providers:
- Flow management and decision routing
- Context management and prompt optimization
- Multi-provider model integration

### Memory Service
Persistent memory system for conversations and context:
- Long-term memory storage
- Context retrieval and similarity search
- Multi-tenant memory isolation

### Analytics Service
Performance monitoring and business intelligence:
- Real-time metrics collection
- Performance tracking and optimization
- Dashboard and reporting capabilities

## API Interface

The engine exposes REST APIs for:
- **AI Operations**: Chat, completion, and AI orchestration
- **Plugin Management**: Plugin discovery, execution, and lifecycle
- **Extension System**: Extension installation and management
- **Memory Operations**: Context storage and retrieval
- **Analytics**: Metrics and performance data
- **System Health**: Health checks and diagnostics

## Security Features

- **Zero-trust architecture** with cryptographic validation
- **Role-based access control** for all operations
- **Hardware isolation** for sensitive operations
- **Comprehensive audit logging** for compliance
- **Threat protection** and incident response

## Integration Patterns

### Plugin Development
```python
from ai_karen_engine import PluginManager

# Get plugin manager instance
plugin_manager = get_plugin_manager()

# Execute plugin with context
result = await plugin_manager.run_plugin(
    name="my-plugin",
    params={"input": "data"},
    user_ctx={"user_id": "123", "roles": ["user"]}
)
```

### Extension Development
```python
from ai_karen_engine.extensions import BaseExtension

class MyExtension(BaseExtension):
    def __init__(self):
        super().__init__(
            name="my-extension",
            version="1.0.0",
            description="Custom extension"
        )
    
    async def initialize(self):
        # Extension initialization logic
        pass
```

### LLM Integration
```python
from ai_karen_engine import LLMOrchestrator

# Get orchestrator instance
orchestrator = get_orchestrator()

# Route request to optimal model
response = orchestrator.route_request(
    prompt="Your prompt here",
    skill="text-generation",
    max_tokens=256,
    user_id="user123"
)
```

## Configuration

The engine supports configuration through:
- Environment variables for runtime settings
- JSON configuration files for complex settings
- Database-stored configuration for multi-tenant settings

Key environment variables:
- `KARI_MODEL_SIGNING_KEY`: Cryptographic key for model validation
- `KARI_MAX_LLM_CONCURRENT`: Maximum concurrent LLM requests
- `KARI_LLM_TIMEOUT`: Request timeout in seconds
- `KARI_LOG_DIR`: Custom log directory path

## Monitoring and Observability

The engine provides comprehensive monitoring through:
- **Prometheus metrics** for operational monitoring
- **Structured logging** with configurable formats
- **Health check endpoints** for service monitoring
- **Performance tracking** for optimization

## Development Guidelines

### Adding New Services
1. Extend `BaseService` for dependency injection support
2. Register service in the service container
3. Add appropriate error handling and logging
4. Include comprehensive tests

### Plugin Development
1. Follow the plugin manifest specification
2. Implement proper error handling and validation
3. Use the provided sandbox environment
4. Include security considerations

### Extension Development
1. Extend `BaseExtension` base class
2. Define clear extension manifest
3. Implement proper lifecycle management
4. Follow security best practices

## Testing

The engine includes comprehensive test coverage:
- Unit tests for individual components
- Integration tests for service interactions
- Security tests for access control
- Performance tests for optimization

Run tests with:
```bash
pytest tests/
```

## Contributing

When contributing to the AI Karen Engine:
1. Follow the established architecture patterns
2. Include comprehensive tests for new features
3. Update documentation for API changes
4. Follow security best practices
5. Ensure backward compatibility

## License

See the main project LICENSE file for licensing information.