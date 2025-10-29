# Extension Environment Configuration System

A comprehensive, production-ready configuration management system for extension authentication that provides environment-aware settings, secure credential storage, configuration validation, and hot-reload capabilities without service restart.

## 🎯 Requirements Addressed

This implementation addresses the following requirements from the extension runtime authentication fix specification:

- **8.1**: Environment-specific configuration (dev/staging/prod)
- **8.2**: Secure credential storage and rotation
- **8.3**: Configuration validation and health checks
- **8.4**: Configuration hot-reload without service restart
- **8.5**: Comprehensive configuration management API

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                Configuration Management Layer               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Environment     │  │    Configuration Validator         │ │
│  │ Config Manager  │  │    - Security validation           │ │
│  │ - Multi-env     │  │    - Environment consistency       │ │
│  │ - Auto-loading  │  │    - Performance checks            │ │
│  │ - File watching │  │    - Compliance validation         │ │
│  └─────────────────┘  └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Secure          │  │    Hot-Reload System                │ │
│  │ Credential      │  │    - File change detection         │ │
│  │ Manager         │  │    - Validation before apply       │ │
│  │ - Encryption    │  │    - Rollback on failure           │ │
│  │ - Auto-rotation │  │    - Debounced updates             │ │
│  └─────────────────┘  └─────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Health Monitor  │  │    Integration Layer                │ │
│  │ - System checks │  │    - FastAPI integration           │ │
│  │ - Credential    │  │    - Middleware support            │ │
│  │   monitoring    │  │    - Lifecycle management          │ │
│  │ - Auto-recovery │  │    - API endpoints                  │ │
│  └─────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
server/
├── extension_environment_config.py      # Core configuration management
├── extension_config_validator.py        # Validation and health checks
├── extension_config_hot_reload.py       # Hot-reload system
├── extension_config_api.py              # REST API endpoints
├── extension_config_integration.py      # Integration utilities
└── extension_config_example.py          # Usage examples

config/extensions/
├── development.yaml                     # Development environment config
├── staging.yaml                        # Staging environment config
├── production.yaml                     # Production environment config
├── test.yaml                           # Test environment config
└── credentials/                        # Secure credential storage
    ├── credentials.enc                 # Encrypted credentials
    └── rotation.log                    # Rotation audit log
```

## 🚀 Quick Start

### 1. Basic Setup

```python
from server.extension_config_integration import initialize_extension_config_integration
from server.extension_environment_config import get_current_extension_config

# Initialize the configuration system
await initialize_extension_config_integration()

# Get current configuration
config = get_current_extension_config()
print(f"Environment: {config.environment.value}")
print(f"Auth mode: {config.auth_mode}")
```

### 2. FastAPI Integration

```python
from fastapi import FastAPI
from server.extension_config_integration import (
    extension_config_lifespan,
    setup_extension_config_routes,
    create_extension_config_middleware
)

# Create FastAPI app with configuration lifespan
app = FastAPI(lifespan=extension_config_lifespan)

# Add configuration routes
setup_extension_config_routes(app)

# Add configuration middleware
app.add_middleware(create_extension_config_middleware())
```

### 3. Environment-Specific Configuration

```python
from server.extension_environment_config import Environment, get_config_manager

config_manager = get_config_manager()

# Get environment-specific configurations
dev_config = config_manager.get_config(Environment.DEVELOPMENT)
prod_config = config_manager.get_config(Environment.PRODUCTION)

print(f"Dev auth mode: {dev_config.auth_mode}")      # 'development'
print(f"Prod auth mode: {prod_config.auth_mode}")    # 'strict'
```

## 🔧 Core Features

### Environment-Aware Configuration

The system automatically detects the runtime environment and loads appropriate configurations:

- **Development**: Relaxed security, verbose logging, development bypasses
- **Staging**: Production-like security with debugging capabilities
- **Production**: Strict security, minimal logging, no bypasses
- **Test**: Permissive settings for automated testing

### Secure Credential Management

```python
from server.extension_environment_config import get_config_manager

config_manager = get_config_manager()
credentials_manager = config_manager.credentials_manager

# Store encrypted credential
success = credentials_manager.store_credential(
    name="api_key",
    value="secret_key_value",
    environment="production",
    rotation_interval_days=30,
    description="Production API key"
)

# Retrieve credential
api_key = credentials_manager.get_credential("api_key", "production")

# Rotate credential
credentials_manager.rotate_credential("api_key")
```

### Configuration Validation

```python
from server.extension_config_validator import validate_extension_config

# Validate current configuration
validation_result = await validate_extension_config()

if validation_result['valid']:
    print("✅ Configuration is valid")
else:
    print(f"❌ Found {validation_result['total_issues']} issues")
    for issue in validation_result['issues']:
        print(f"  - {issue['severity']}: {issue['message']}")
```

### Hot-Reload System

```python
from server.extension_config_hot_reload import reload_extension_config

# Reload configuration without restart
reload_result = await reload_extension_config(force=True)

print(f"Reload status: {reload_result['status']}")
if reload_result.get('changes'):
    print(f"Changes applied: {len(reload_result['changes'])}")
```

### Health Monitoring

```python
from server.extension_config_validator import run_extension_health_checks

# Run comprehensive health checks
health_result = await run_extension_health_checks()

print(f"Overall status: {health_result['overall_status']}")
print(f"Healthy checks: {health_result['healthy_count']}")
print(f"Failed checks: {health_result['unhealthy_count']}")
```

## 🌍 Environment Configuration

### Development Environment (`config/extensions/development.yaml`)

```yaml
# Relaxed settings for development
auth_enabled: true
auth_mode: "development"
dev_bypass_enabled: true
require_https: false
rate_limit_per_minute: 1000
max_failed_attempts: 10
lockout_duration_minutes: 1
log_level: "DEBUG"
enable_debug_logging: true
log_sensitive_data: true
```

### Production Environment (`config/extensions/production.yaml`)

```yaml
# Strict settings for production
auth_enabled: true
auth_mode: "strict"
dev_bypass_enabled: false
require_https: true
rate_limit_per_minute: 100
max_failed_attempts: 3
lockout_duration_minutes: 30
log_level: "INFO"
enable_debug_logging: false
log_sensitive_data: false
```

## 🔒 Security Features

### Credential Encryption

- **AES-256 encryption** using Fernet (cryptographically secure)
- **PBKDF2 key derivation** with 100,000 iterations
- **Automatic key rotation** with configurable intervals
- **Audit logging** for all credential operations

### Configuration Security

- **Environment-specific validation** rules
- **Production security hardening** checks
- **Sensitive data redaction** in logs and exports
- **Secure defaults** for all environments

### Access Control

- **Role-based permissions** (read, write, admin, background_tasks)
- **Environment isolation** for credentials
- **API authentication** for configuration endpoints
- **Audit trails** for all configuration changes

## 📊 Monitoring and Health Checks

### Built-in Health Checks

- **Configuration validity** - Validates current config
- **Credential health** - Checks for expired credentials
- **File permissions** - Verifies secure file access
- **Network connectivity** - Tests external dependencies
- **Database connectivity** - Validates database connections
- **System resources** - Monitors disk space and memory
- **Service dependencies** - Checks required services

### Metrics and Alerting

- **Configuration reload metrics** - Success/failure rates
- **Credential rotation tracking** - Automatic rotation status
- **Health check results** - System health trends
- **Performance monitoring** - Configuration load times

## 🔄 Hot-Reload System

### Features

- **File change detection** - Automatic configuration updates
- **Validation before apply** - Prevents invalid configurations
- **Rollback on failure** - Automatic recovery from errors
- **Debounced updates** - Prevents rapid-fire reloads
- **Configuration snapshots** - Point-in-time recovery

### Reload Triggers

- **File changes** - Automatic detection of config file modifications
- **API requests** - Manual reload via REST API
- **Scheduled reloads** - Periodic configuration refresh
- **Credential rotation** - Reload after credential updates
- **Health check failures** - Recovery-triggered reloads

## 🌐 REST API

### Configuration Management

```bash
# Get current configuration
GET /api/extension-config/

# Get environment-specific configuration
GET /api/extension-config/{environment}

# Update configuration
PUT /api/extension-config/{environment}
Content-Type: application/json
{
  "rate_limit_per_minute": 200,
  "enable_debug_logging": true
}

# Validate configuration
POST /api/extension-config/validate

# Get system health status
GET /api/extension-config/health/status
```

### Hot-Reload Management

```bash
# Reload configuration
POST /api/extension-config/reload
Content-Type: application/json
{
  "environment": "development",
  "force": true
}

# Get reload history
GET /api/extension-config/reload/history?limit=50

# Get configuration snapshots
GET /api/extension-config/snapshots/{environment}?limit=10
```

### Credential Management

```bash
# List credentials (values redacted)
GET /api/extension-config/credentials?environment=production

# Store credential
POST /api/extension-config/credentials
Content-Type: application/json
{
  "name": "api_key",
  "value": "secret_value",
  "environment": "production",
  "rotation_interval_days": 30
}

# Rotate credential
POST /api/extension-config/credentials/{name}/rotate
```

## 🧪 Testing

### Running Tests

```bash
# Run simplified tests (no external dependencies)
python3 test_extension_config_simple.py

# Run comprehensive tests (requires full environment)
python3 test_extension_environment_config.py
```

### Test Coverage

- ✅ Environment detection and configuration loading
- ✅ Configuration file creation and parsing
- ✅ Environment-specific defaults application
- ✅ Configuration validation logic
- ✅ Credential encryption/decryption
- ✅ JSON/YAML serialization
- ✅ File operations and permissions
- ✅ Configuration structure validation
- ✅ Hot-reload system functionality
- ✅ Health check system
- ✅ API endpoint functionality

## 🚀 Deployment

### Environment Variables

```bash
# Core environment detection
ENVIRONMENT=production                    # Environment name
EXTENSION_ENVIRONMENT=production         # Override environment

# Security settings
EXTENSION_SECRET_KEY=your-secret-key     # JWT secret key
EXTENSION_API_KEY=your-api-key          # API authentication key
EXTENSION_MASTER_KEY=your-master-key    # Credential encryption key

# Configuration paths
EXTENSION_CONFIG_DIR=/app/config/extensions
EXTENSION_CREDENTIALS_DIR=/app/config/extensions/credentials

# Feature flags
EXTENSION_HOT_RELOAD_ENABLED=true       # Enable hot-reload
EXTENSION_FILE_WATCHING_ENABLED=true   # Enable file watching
EXTENSION_HEALTH_CHECKS_ENABLED=true   # Enable health checks
```

### Docker Configuration

```dockerfile
# Copy configuration files
COPY config/extensions/ /app/config/extensions/

# Set environment variables
ENV ENVIRONMENT=production
ENV EXTENSION_CONFIG_DIR=/app/config/extensions
ENV EXTENSION_CREDENTIALS_DIR=/app/config/extensions/credentials

# Create secure directories
RUN mkdir -p /app/config/extensions/credentials && \
    chmod 700 /app/config/extensions/credentials
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: extension-config
data:
  production.yaml: |
    auth_enabled: true
    auth_mode: "strict"
    require_https: true
    # ... other settings

---
apiVersion: v1
kind: Secret
metadata:
  name: extension-credentials
type: Opaque
data:
  master-key: <base64-encoded-master-key>
  secret-key: <base64-encoded-secret-key>
  api-key: <base64-encoded-api-key>
```

## 🔍 Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions on config directory
   - Verify YAML syntax in configuration files
   - Check environment variable settings

2. **Credential decryption failures**
   - Verify EXTENSION_MASTER_KEY is set correctly
   - Check file permissions on credentials directory
   - Ensure credentials file is not corrupted

3. **Hot-reload not working**
   - Verify file watching is enabled
   - Check file system permissions
   - Review hot-reload logs for errors

4. **Health checks failing**
   - Check system resources (disk space, memory)
   - Verify network connectivity
   - Review individual health check results

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('server.extension_environment_config').setLevel(logging.DEBUG)
logging.getLogger('server.extension_config_hot_reload').setLevel(logging.DEBUG)

# Get detailed system status
from server.extension_environment_config import get_config_manager
config_manager = get_config_manager()
status = config_manager.get_health_status()
print(json.dumps(status, indent=2))
```

## 📈 Performance Considerations

### Optimization Features

- **Lazy loading** - Configurations loaded on-demand
- **Caching** - In-memory caching of parsed configurations
- **Debounced reloads** - Prevents excessive file system operations
- **Efficient validation** - Optimized validation rules
- **Connection pooling** - Efficient database connections

### Resource Usage

- **Memory**: ~10-50MB depending on configuration size
- **Disk**: Minimal, only for configuration and credential files
- **CPU**: Low impact, mostly during validation and reloads
- **Network**: Minimal, only for health checks and external validation

## 🤝 Contributing

### Development Setup

1. Install dependencies:
   ```bash
   pip install cryptography watchdog psutil pyyaml fastapi pydantic
   ```

2. Set up development environment:
   ```bash
   export ENVIRONMENT=development
   export EXTENSION_CONFIG_DIR=./config/extensions
   ```

3. Run tests:
   ```bash
   python3 test_extension_config_simple.py
   ```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Include comprehensive docstrings
- Add logging for important operations
- Write tests for new functionality

## 📄 License

This implementation is part of the Kari AI platform and follows the same licensing terms.

---

## 🎉 Summary

The Extension Environment Configuration System provides a complete, production-ready solution for managing extension authentication configuration across different environments. It includes:

✅ **Environment-aware configuration** with automatic detection and loading  
✅ **Secure credential storage** with encryption and automatic rotation  
✅ **Configuration validation** with comprehensive security and consistency checks  
✅ **Hot-reload capabilities** without service restart  
✅ **REST API** for configuration management  
✅ **Health monitoring** with automatic recovery  
✅ **Integration support** for FastAPI and other frameworks  
✅ **Production-ready** security and monitoring features  

The system is designed to be robust, secure, and easy to integrate with existing applications while providing the flexibility needed for different deployment environments.