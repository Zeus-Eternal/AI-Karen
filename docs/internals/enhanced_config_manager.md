# Enhanced Configuration Manager

The Enhanced Configuration Manager is a comprehensive solution for managing application configuration in the AI-Karen system. It addresses requirements 9.1-9.5 from the system-warnings-errors-fix specification by providing robust configuration loading, validation, migration, and health monitoring capabilities.

## Features

### Core Capabilities

- **Configuration Loading**: Load from JSON/YAML files with fallback to defaults
- **Environment Variable Support**: Comprehensive environment variable mapping and validation
- **Pydantic V2 Migration**: Automatic migration of deprecated Pydantic V1 patterns
- **Health Monitoring**: Built-in health checks for configuration integrity
- **Validation**: Comprehensive validation with clear error messages and suggested fixes
- **Thread Safety**: Thread-safe operations for concurrent access
- **Change Notifications**: Event-driven configuration change notifications

### Key Benefits

1. **Eliminates Configuration Warnings**: Automatically handles deprecated patterns and missing configurations
2. **Clear Error Messages**: Provides actionable error messages with specific remediation steps
3. **Production Ready**: Validates production-specific requirements and security settings
4. **Developer Friendly**: Comprehensive validation and helpful defaults for development
5. **Extensible**: Easy to add custom environment mappings and validation rules

## Quick Start

### Basic Usage

```python
from ai_karen_engine.config.enhanced_config_manager import ConfigurationManager

# Initialize configuration manager
manager = ConfigurationManager(config_path="config.json")

# Load configuration
config = manager.load_config()

# Access configuration values with fallbacks
db_host = manager.get_with_fallback('database.host', 'localhost')
timeout = manager.get_with_fallback('database.timeout', 30)
```

### Environment Variable Configuration

```python
from ai_karen_engine.config.enhanced_config_manager import (
    ConfigurationManager,
    EnvironmentVariableConfig
)

# Define custom environment mappings
env_mappings = [
    EnvironmentVariableConfig(
        env_var="DB_HOST",
        config_path="database.host",
        required=True,
        description="Database host"
    ),
    EnvironmentVariableConfig(
        env_var="DEBUG_MODE",
        config_path="debug",
        value_type="bool",
        default_value=False,
        description="Enable debug mode"
    )
]

manager = ConfigurationManager(env_mappings=env_mappings)
```

### Global Configuration Manager

```python
from ai_karen_engine.config.enhanced_config_manager import (
    initialize_enhanced_config_manager,
    get_enhanced_config_manager
)

# Initialize global instance
manager = initialize_enhanced_config_manager(config_path="app_config.json")

# Access from anywhere in your application
config_manager = get_enhanced_config_manager()
config = config_manager.load_config()
```

## Configuration Structure

### Default Configuration Schema

```json
{
  "environment": "development",
  "debug": false,
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "ai_karen",
    "username": "postgres",
    "password": ""
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "password": null
  },
  "llm": {
    "provider": "local",
    "model": "llama3.2:latest",
    "openai_api_key": null
  },
  "security": {
    "jwt_secret": "change-me-in-production",
    "cors_origins": ["*"]
  },
  "memory": {
    "enabled": true,
    "provider": "local",
    "embedding_dim": 768,
    "decay_lambda": 0.1
  },
  "ui": {
    "show_debug_info": false
  }
}
```

### Environment Variable Mappings

The configuration manager supports the following environment variables by default:

| Environment Variable | Config Path | Type | Required | Description |
|---------------------|-------------|------|----------|-------------|
| `KARI_ENV` | `environment` | string | No | Application environment |
| `KARI_DEBUG` | `debug` | bool | No | Enable debug mode |
| `DB_HOST` | `database.host` | string | No | Database host |
| `DB_PORT` | `database.port` | int | No | Database port |
| `DB_NAME` | `database.name` | string | No | Database name |
| `DB_USER` | `database.username` | string | No | Database username |
| `DB_PASSWORD` | `database.password` | string | No | Database password |
| `REDIS_HOST` | `redis.host` | string | No | Redis host |
| `REDIS_PORT` | `redis.port` | int | No | Redis port |
| `REDIS_PASSWORD` | `redis.password` | string | No | Redis password |
| `OPENAI_API_KEY` | `llm.openai_api_key` | string | No | OpenAI API key |
| `LLM_PROVIDER` | `llm.provider` | string | No | LLM provider |
| `LLM_MODEL` | `llm.model` | string | No | LLM model |
| `JWT_SECRET` | `security.jwt_secret` | string | **Yes** | JWT secret key |
| `CORS_ORIGINS` | `security.cors_origins` | string | No | CORS origins (comma-separated) |

## Advanced Features

### Environment Validation

```python
# Validate environment variables
validation_result = manager.validate_environment()

if not validation_result.is_valid:
    print("Environment validation failed:")
    for issue in validation_result.issues:
        print(f"  {issue.key}: {issue.message}")
        print(f"  Fix: {issue.suggested_fix}")
```

### Pydantic V2 Migration

```python
# Migrate deprecated Pydantic V1 patterns
config_with_deprecated = {
    'model_config': {
        'schema_extra': {'example': 'value'}
    }
}

migrated_config = manager.migrate_pydantic_config(config_with_deprecated)
# Result: {'model_config': {'json_schema_extra': {'example': 'value'}}}
```

### Health Monitoring

```python
# Perform comprehensive health checks
health_result = manager.perform_health_checks()

print(f"Overall status: {health_result['overall_status']}")
for check_name, check_result in health_result['checks'].items():
    print(f"{check_name}: {check_result['status']} - {check_result['message']}")
```

### Configuration Change Notifications

```python
def on_config_change(config):
    print(f"Configuration changed: {config['environment']}")

# Register change listener
manager.add_change_listener(on_config_change)

# Load config will trigger the listener
config = manager.load_config()
```

## Validation and Error Handling

### Validation Severity Levels

- **INFO**: Informational messages
- **WARNING**: Non-critical issues that should be addressed
- **ERROR**: Critical issues that prevent proper operation
- **CRITICAL**: Security or data integrity issues

### Common Validation Issues

1. **Missing Required Environment Variables**
   ```
   Error: Required environment variable JWT_SECRET is not set
   Fix: Set JWT_SECRET=<secure-secret> in your environment
   ```

2. **Production Security Issues**
   ```
   Critical: Default JWT secret should not be used in production
   Fix: Set a secure JWT secret via JWT_SECRET environment variable
   ```

3. **Invalid Value Types**
   ```
   Error: Environment variable DB_PORT has invalid value type
   Fix: Set DB_PORT to a valid int value
   ```

4. **Deprecated Pydantic Patterns**
   ```
   Warning: Deprecated Pydantic V1 pattern 'schema_extra' found
   Fix: Use 'json_schema_extra' instead of 'schema_extra'
   ```

## Configuration Health Checks

The health monitoring system performs the following checks:

### File System Checks
- Configuration file accessibility
- File permissions and readability

### Environment Checks
- Required environment variables
- Value type validation
- Pattern matching validation

### Migration Checks
- Deprecated Pydantic patterns
- Legacy configuration formats

### Security Checks
- Production-specific validations
- Critical configuration values
- Default security settings

## Best Practices

### Development Environment

```bash
# Set basic development environment
export KARI_ENV=development
export KARI_DEBUG=true
export JWT_SECRET=dev-secret-key
export DB_HOST=localhost
```

### Production Environment

```bash
# Set secure production environment
export KARI_ENV=production
export KARI_DEBUG=false
export JWT_SECRET=your-secure-production-secret
export DB_HOST=prod-db-host
export DB_PASSWORD=secure-db-password
export REDIS_PASSWORD=secure-redis-password
```

### Configuration File Organization

```
config/
├── default.json          # Default configuration
├── development.json      # Development overrides
├── staging.json         # Staging overrides
└── production.json      # Production overrides
```

### Error Handling

```python
try:
    config = manager.load_config()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    # Handle configuration error gracefully
    sys.exit(1)
```

## Integration Examples

### Flask Application

```python
from flask import Flask
from ai_karen_engine.config.enhanced_config_manager import get_enhanced_config_manager

app = Flask(__name__)

# Initialize configuration
config_manager = get_enhanced_config_manager()
config = config_manager.load_config()

# Configure Flask from config
app.config['DEBUG'] = config['debug']
app.config['SECRET_KEY'] = config['security']['jwt_secret']
```

### FastAPI Application

```python
from fastapi import FastAPI
from ai_karen_engine.config.enhanced_config_manager import initialize_enhanced_config_manager

# Initialize configuration manager
config_manager = initialize_enhanced_config_manager("api_config.json")
config = config_manager.load_config()

app = FastAPI(
    title="AI Karen API",
    debug=config['debug']
)
```

### Database Connection

```python
import sqlalchemy
from ai_karen_engine.config.enhanced_config_manager import get_enhanced_config_manager

config_manager = get_enhanced_config_manager()
db_config = config_manager.get_with_fallback('database', {})

# Create database URL
db_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"

engine = sqlalchemy.create_engine(db_url)
```

## Troubleshooting

### Common Issues

1. **Configuration file not found**
   - Ensure the config file path is correct
   - Check file permissions
   - Verify the file exists and is readable

2. **Environment validation failures**
   - Check that required environment variables are set
   - Verify environment variable values are correct types
   - Use the validation result to identify specific issues

3. **Migration warnings**
   - Update deprecated Pydantic patterns manually
   - Enable automatic migration in the configuration manager
   - Review migration logs for specific patterns to update

4. **Health check failures**
   - Review health check results for specific issues
   - Address critical configuration problems first
   - Ensure all required services are available

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

manager = ConfigurationManager(enable_health_checks=True)
config = manager.load_config()
```

### Configuration Summary

Get a comprehensive overview of the configuration state:

```python
summary = manager.get_configuration_summary()
print(json.dumps(summary, indent=2))
```

## API Reference

### ConfigurationManager

#### Constructor
```python
ConfigurationManager(
    config_path: Optional[Union[str, Path]] = None,
    env_mappings: Optional[List[EnvironmentVariableConfig]] = None,
    enable_migration: bool = True,
    enable_health_checks: bool = True
)
```

#### Methods

- `load_config(config_path: Optional[str] = None) -> Dict[str, Any]`
- `validate_environment() -> ConfigValidationResult`
- `migrate_pydantic_config(config: Dict[str, Any]) -> Dict[str, Any]`
- `get_with_fallback(key: str, default: Any = None) -> Any`
- `report_missing_configs() -> List[ConfigIssue]`
- `perform_health_checks() -> Dict[str, Any]`
- `add_change_listener(listener: Callable[[Dict[str, Any]], None]) -> None`
- `get_configuration_summary() -> Dict[str, Any]`

### EnvironmentVariableConfig

```python
EnvironmentVariableConfig(
    env_var: str,
    config_path: str,
    required: bool = False,
    default_value: Optional[Any] = None,
    value_type: str = "str",
    description: str = "",
    validation_pattern: Optional[str] = None
)
```

### ConfigValidationResult

Properties:
- `is_valid: bool`
- `issues: List[ConfigIssue]`
- `missing_required: List[str]`
- `deprecated_configs: List[str]`
- `warnings: List[str]`
- `migration_needed: bool`
- `has_errors: bool`
- `has_warnings: bool`

## Contributing

When extending the Enhanced Configuration Manager:

1. Add new environment mappings to `DEFAULT_ENV_MAPPINGS`
2. Update validation rules in `_validate_config`
3. Add health checks in `perform_health_checks`
4. Write comprehensive tests for new features
5. Update documentation with examples

## License

This module is part of the AI-Karen project and follows the same licensing terms.