# AI Karen Engine - Core Infrastructure

The core infrastructure provides the foundational components for the AI Karen engine, including service architecture, error handling, logging, and the FastAPI gateway.

## Components

### Service Infrastructure (`services/`)

Provides dependency injection and service management:

- **BaseService**: Abstract base class for all services
- **ServiceContainer**: Dependency injection container
- **ServiceRegistry**: Service discovery and registration
- **ServiceConfig**: Configuration management for services

#### Usage Example
```python
from ai_karen_engine.core import BaseService, service, inject

@service
class MyService(BaseService):
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
    
    async def process(self, data: str) -> str:
        return f"Processed: {data}"

# Inject service into other components
@inject
async def my_handler(service: MyService):
    return await service.process("test data")
```

### Error Handling (`errors/`)

Comprehensive error handling system:

- **KarenError**: Base exception class
- **Specialized Exceptions**: ValidationError, AuthenticationError, etc.
- **ErrorHandler**: Centralized error processing
- **ErrorMiddleware**: FastAPI middleware for error handling

#### Error Types
- `ValidationError`: Input validation failures
- `AuthenticationError`: Authentication failures
- `AuthorizationError`: Permission denied errors
- `NotFoundError`: Resource not found
- `ServiceError`: Service-level errors
- `PluginError`: Plugin execution errors
- `MemoryError`: Memory system errors
- `AIProcessingError`: AI operation failures

### Logging (`logging/`)

Structured logging with multiple output formats:

- **KarenLogger**: Enhanced logger with context
- **StructuredFormatter**: Structured log formatting
- **JSONFormatter**: JSON log output
- **LoggingMiddleware**: Request/response logging

#### Configuration
```python
from ai_karen_engine.core import configure_logging, LogLevel

configure_logging(
    level=LogLevel.INFO,
    format=LogFormat.JSON,
    output_file="/var/log/karen/app.log"
)
```

### Gateway (`gateway/`)

FastAPI application setup and middleware:

- **KarenApp**: Enhanced FastAPI application
- **Middleware Setup**: Security, logging, error handling
- **Route Registration**: Automatic API route discovery

#### Application Setup
```python
from ai_karen_engine.core import create_app

app = create_app(
    title="AI Karen API",
    version="1.0.0",
    enable_docs=True
)
```

## Key Features

### Dependency Injection

The service container provides automatic dependency resolution:

```python
from ai_karen_engine.core import get_container

container = get_container()
service = container.get(MyService)
```

### Error Propagation

Errors are automatically caught and formatted:

```python
from ai_karen_engine.core import KarenError

class CustomError(KarenError):
    error_code = "CUSTOM_001"
    message = "Custom error occurred"

raise CustomError(details={"field": "value"})
```

### Structured Logging

All components use structured logging:

```python
from ai_karen_engine.core import get_logger

logger = get_logger(__name__)
logger.info("Operation completed", extra={
    "user_id": "123",
    "operation": "data_processing",
    "duration": 1.5
})
```

## Advanced Components

### Memory Management (`memory/`)

Core memory system components:
- Memory managers for different storage backends
- Context management and retrieval
- Multi-tenant memory isolation

### Reasoning Engine (`reasoning/`)

AI reasoning and decision-making:
- Soft reasoning engine for fuzzy logic
- Mesh planner for complex task orchestration
- Intent engine for user intent recognition

### Neuro Vault (`neuro_vault/`)

Advanced neural network storage and management:
- Model versioning and storage
- Neural network optimization
- Performance monitoring

## Configuration

Core components are configured through:

### Environment Variables
- `KAREN_LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR)
- `KAREN_LOG_FORMAT`: Log format (TEXT, JSON, STRUCTURED)
- `KAREN_SERVICE_TIMEOUT`: Service operation timeout
- `KAREN_MAX_WORKERS`: Maximum worker threads

### Service Configuration
```python
from ai_karen_engine.core import ServiceConfig

config = ServiceConfig(
    name="my-service",
    timeout=30,
    max_retries=3,
    health_check_interval=60
)
```

## Monitoring

Core infrastructure provides monitoring through:

### Health Checks
```python
from ai_karen_engine.core.health_monitor import HealthMonitor

monitor = HealthMonitor()
status = await monitor.check_all_services()
```

### Metrics Collection
- Service performance metrics
- Error rate tracking
- Resource utilization monitoring

## Extension Points

The core infrastructure provides several extension points:

### Custom Services
Implement `BaseService` to create new services that integrate with the dependency injection system.

### Custom Error Types
Extend `KarenError` to create domain-specific error types with proper error codes and handling.

### Custom Middleware
Add FastAPI middleware for cross-cutting concerns like authentication, rate limiting, etc.

### Custom Formatters
Implement custom log formatters for specialized logging requirements.

## Best Practices

1. **Service Design**: Keep services focused and follow single responsibility principle
2. **Error Handling**: Use specific error types and provide meaningful error messages
3. **Logging**: Include relevant context in log messages for debugging
4. **Configuration**: Use environment variables for runtime configuration
5. **Testing**: Write comprehensive tests for all core components

## Testing

Core infrastructure includes extensive test coverage:

```bash
# Run core infrastructure tests
pytest tests/core/

# Run specific component tests
pytest tests/core/test_services.py
pytest tests/core/test_errors.py
pytest tests/core/test_logging.py
```

## Contributing

When extending core infrastructure:

1. Follow established patterns and interfaces
2. Include comprehensive error handling
3. Add appropriate logging and monitoring
4. Write thorough tests and documentation
5. Consider backward compatibility