# Config Assets System - `config_assets/`

## Overview

This directory contains the **static configuration assets** for AI-Karen. These are **data files only** - JSON, YAML, and other configuration files that are consumed by the canonical config code system in `src/ai_karen_engine/config/`.

## Architecture Principles

- **Pure Assets**: No Python code resides here - only static data files
- **Consumed by Config Code**: All access to these files goes through canonical loaders in `src/ai_karen_engine/config/`
- **Version Controlled**: Configuration data changes are tracked in git
- **Environment Specific**: Different environments can have different asset files
- **Validated on Load**: Assets are validated when loaded by the config system

## Directory Structure & File Purposes

### Core Application Configuration

#### `config.json`
**Purpose**: Main application configuration file containing all core system settings.

**Structure**:
```json
{
  "environment": "development|staging|production",
  "debug": true,
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "ai_karen",
    "username": "postgres",
    "password": "..."
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "database": 0
  },
  "llm": {
    "default_provider": "local_gguf",
    "default_model": "Phi-3-mini-4k-instruct-q4.gguf",
    "fallback_chain": ["local_gguf", "openai", "gemini"]
  },
  "security": {
    "jwt_secret": "...",
    "cors_origins": ["http://localhost:3000"]
  }
}
```

**Usage**: Loaded by `config_manager.py` as the primary application config. Provides defaults for all system components.

**Environment Overrides**: Can be overridden by environment variables (e.g., `KARI_CONFIG_FILE=path/to/custom/config.json`).

#### `optimization_config.json`
**Purpose**: Configuration for AI-Karen's optimization systems and performance tuning.

**Structure**:
```json
{
  "model_discovery": {...},
  "model_routing": {...},
  "cache": {
    "enabled": true,
    "max_size_mb": 1024,
    "ttl_seconds": 3600
  },
  "performance": {
    "max_concurrent_requests": 10,
    "timeout_seconds": 30
  },
  "cuda": {
    "enable_cuda": true,
    "preferred_device_id": 0,
    "memory_threshold": 0.8
  },
  "monitoring": {
    "enable_metrics": true,
    "metrics_interval_seconds": 60
  }
}
```

**Usage**: Loaded by `load_optimization_config()` in the config system. Controls optimization behavior across the application.

### Security & Permissions

#### `permissions.json`
**Purpose**: Role-Based Access Control (RBAC) permissions configuration.

**Structure**:
```json
{
  "role_permissions": {
    "admin": ["read", "write", "delete", "manage_users"],
    "user": ["read", "write"],
    "viewer": ["read"]
  }
}
```

**Usage**: Loaded by `load_permissions_config()` and used by the authentication middleware for permission checking.

#### `secrets/` Directory
**Purpose**: Encrypted secrets and sensitive configuration data.

**Contents**:
- `metadata.json`: Metadata about stored secrets
- `COPILOT_API_KEY.enc`: Encrypted API key for Copilot services
- `ZAI_API_KEY.enc`: Encrypted API key for ZAI services
- `.key`: Encryption key for secrets

**Usage**: Managed by the secret manager system. Secrets are encrypted at rest and decrypted only when needed by authorized components.

### Extension System

#### `extensions/` Directory
**Purpose**: Configuration files for AI-Karen extensions.

**File Format**: YAML files (one per extension environment)

**Contents**:
- `development.yaml`: Extension config for development environment
- `staging.yaml`: Extension config for staging environment
- `production.yaml`: Extension config for production environment
- `test.yaml`: Extension config for testing environment

**Example Structure** (`development.yaml`):
```yaml
id: "sample_extension"
name: "Sample Extension"
version: "1.0.0"
description: "A sample extension for AI-Karen"
enabled: true

configuration:
  api_endpoint: "http://localhost:8080"
  timeout: 30
  retry_count: 3

authentication:
  type: "bearer"
  token_env_var: "EXTENSION_TOKEN"
```

**Usage**: Loaded by `load_extension_configs()` and processed by the extension system. Each environment can have different extension configurations.

### LLM & Model Configuration

#### `llm_profiles.yml`
**Purpose**: User profile configurations for LLM provider assignments.

**Structure**:
```yaml
profiles:
  default:
    providers:
      chat: "local_gguf"
      code: "deepseek"
      reasoning: "openai"
    fallback: "openai"

  enterprise:
    providers:
      chat: "openai"
      conversation_processing: "openai"
      code: "openai"
      generic: "openai"
    fallback: "openai"
```

**Usage**: Loaded by `load_llm_profiles_config()` and used by the profile manager for user-specific provider routing.

#### `local-gguf/config.json`
**Purpose**: Configuration specific to the local GGUF model runtime.

**Structure**:
```json
{
  "model_path": "/models/local-gguf/Phi-3-mini-4k-instruct-q4.gguf",
  "download_url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf",
  "size_mb": 2300,
  "host": "localhost",
  "port": 8080,
  "n_ctx": 4096,
  "n_threads": 4,
  "n_batch": 512,
  "n_gpu_layers": 0,
  "verbose": false,
  "temperature": 0.7,
  "top_p": 0.9,
  "timeout": 30,
  "max_retries": 3,
  "auto_restart": true,
  "health_check_interval": 60
}
```

**Usage**: Loaded by `load_local_gguf_config()` and used by the local GGUF runtime manager for model execution.

### Monitoring Configuration

#### `monitoring/` Directory
**Purpose**: Static monitoring assets for Prometheus and Grafana used by Docker deployments.

**Contents**:
- `monitoring/prometheus/prometheus.yml`: Main Prometheus scrape configuration
- `monitoring/prometheus/prometheus-copilot.yml`: CoPilot-specific Prometheus configuration
- `monitoring/alerts/alert_rules.yml`: Prometheus alerting rules
- `monitoring/grafana/provisioning/grafana_provisioning.yml`: Grafana dashboard provisioning
- `monitoring/grafana/provisioning/grafana_datasources.yml`: Grafana data source provisioning
- `monitoring/grafana/dashboards/grafana_dashboard.json`: Main Grafana dashboard JSON
- `monitoring/grafana/dashboards/copilot/`: CoPilot dashboard directory

**Usage**: Mounted directly by `docker-compose.yml` and `docker-compose-copilot.yml` as static config assets.

### Memory & Performance

#### `memory.yml`
**Purpose**: Memory management policy configuration.

**Structure**:
```yaml
decay_tiers:
  short:
    max_age_hours: 24
    importance_threshold: 1
  medium:
    max_age_hours: 168
    importance_threshold: 5
  long:
    max_age_hours: 720
    importance_threshold: 8

auto_demotion_enabled: true
promotion_usage_count: 5
recency_alpha: 0.05
```

**Usage**: Loaded by `load_memory_policy_config()` and used by the memory policy system for retention and decay logic.

#### `performance.yml`
**Purpose**: Performance optimization settings.

**Structure**:
```yaml
caching:
  enabled: true
  max_cache_size_mb: 1024
  ttl_seconds: 3600

optimization:
  level: "balanced"
  experimental_features: false
  monitoring_enabled: true

resource_limits:
  max_concurrent_requests: 10
  memory_threshold_mb: 2048
  cpu_threshold_percent: 80
```

**Usage**: Loaded by `load_performance_config()` and used by the performance config manager.

### Deployment & Services

#### `services.yml`
**Purpose**: Service definitions and deployment configuration.

**Structure**:
```yaml
services:
  web_ui:
    enabled: true
    host: "0.0.0.0"
    port: 8000
    workers: 4

  api_server:
    enabled: true
    host: "0.0.0.0"
    port: 8010
    cors_origins: ["http://localhost:3000"]

  memory_service:
    enabled: true
    cache_size_mb: 512
    persistence_enabled: true

deployment:
  environment: "development"
  scaling:
    min_instances: 1
    max_instances: 5
  monitoring:
    enabled: true
    metrics_endpoint: "/metrics"
```

**Usage**: Loaded by `load_deployment_config()` and used by the deployment config manager.

## Usage Guidelines

### For Developers

1. **Never edit files directly in production**: Use deployment pipelines to manage config changes
2. **Validate changes**: Always test config changes in development environment first
3. **Use canonical loaders**: Access these files through `ai_karen_engine.config` loaders, not direct file reads
4. **Document changes**: Update this README when adding new config files
5. **Environment separation**: Use different files or environment overrides for different deployments

### For DevOps/Deployment

1. **Environment-specific configs**: Copy and modify files for different environments
2. **Secret management**: Use the `secrets/` directory for sensitive data
3. **Backup configs**: Keep backups of working configurations
4. **Version control**: All config changes should be committed to git
5. **Validation**: Run config validation before deployment

### For Configuration Management

```yaml
# Correct: Let the config system handle file access
from ai_karen_engine.config import load_extension_configs

extensions = load_extension_configs()
for ext in extensions:
    print(f"Extension: {ext['name']}")

# Incorrect: Direct file access (breaks encapsulation)
import yaml
with open('config_assets/extensions/development.yaml') as f:
    config = yaml.safe_load(f)
```

## File Naming Conventions

- **JSON files**: Use `.json` extension, snake_case naming
- **YAML files**: Use `.yml` extension, snake_case naming
- **Environment-specific**: Use environment name as suffix (e.g., `config.development.json`)
- **Backup files**: Use `.bak` extension for automatic backups

## Validation & Schema

All config files should be:
- Valid JSON/YAML syntax
- Conform to expected schemas (documented above)
- Free of sensitive data (use `secrets/` for that)
- Tested in development before production deployment

## Environment Overrides

Config files can be overridden by:
- Environment variables (e.g., `KARI_CONFIG_FILE=custom_config.json`)
- Environment-specific files (e.g., `config.production.json`)
- Runtime configuration updates (for dynamic settings)

## Security Considerations

- Never commit sensitive data to these files
- Use `secrets/` directory for encrypted sensitive configuration
- Restrict file permissions (readable by application user only)
- Audit config changes in production environments

## Troubleshooting

**File not found errors**: Check that files exist in correct location and have proper permissions
**Parsing errors**: Validate JSON/YAML syntax using online validators
**Validation errors**: Check startup logs for specific validation failure messages
**Environment issues**: Verify environment variables and file paths

## Maintenance

- **Regular review**: Audit config files for outdated settings
- **Documentation updates**: Keep this README current with new config files
- **Cleanup**: Remove unused configuration files
- **Backup**: Maintain backups of working configurations
- **Testing**: Test config changes in staging before production</content>
<parameter name="filePath">config_assets/README.md
