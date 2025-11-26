# Llama.cpp Server Configuration Template

This document provides a template for configuring the Llama.cpp Server for KAREN. Copy this configuration and modify it according to your needs.

## Configuration File Structure

The server uses a JSON configuration file that should be placed in the `llama_CPP_Server` directory as `config.json`.

## Complete Configuration Template

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "INFO",
    "cors_origins": ["*"],
    "api_prefix": "/api/v1"
  },
  "models": {
    "directory": "../models/llama-cpp",
    "default_model": "Phi-3-mini-4k-instruct-q4",
    "auto_load_default": true,
    "max_loaded_models": 3,
    "model_cache_size": 1,
    "scan_interval": 60,
    "supported_formats": [".gguf", ".bin"]
  },
  "performance": {
    "optimize_for": "balanced",
    "max_memory_mb": 4096,
    "enable_gpu": true,
    "gpu_layers": 35,
    "num_threads": 4,
    "batch_size": 512,
    "context_window": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "max_tokens": 2048
  },
  "inference": {
    "timeout_ms": 30000,
    "stream_responses": false,
    "cache_enabled": true,
    "cache_ttl": 3600,
    "max_concurrent_requests": 10
  },
  "karen": {
    "integration_enabled": true,
    "optimize_for_karen": true,
    "karen_endpoint": "http://localhost:8000",
    "auth_token": null,
    "enable_local_fallback": true,
    "karen_prompt_template": true,
    "context_awareness": true,
    "memory_optimization": true
  },
  "api": {
    "enable_cors": true,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 10
    },
    "authentication": {
      "enabled": false,
      "api_key_header": "X-API-Key",
      "api_keys": []
    }
  },
  "monitoring": {
    "enabled": true,
    "metrics_endpoint": "/metrics",
    "health_endpoint": "/health",
    "check_interval": 30,
    "prometheus_enabled": false,
    "log_performance": true,
    "log_requests": false
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": null,
    "max_size": "10MB",
    "backup_count": 5,
    "structured_logging": false
  }
}
```

## Configuration Options Explained

### Server Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "INFO",
    "cors_origins": ["*"],
    "api_prefix": "/api/v1"
  }
}
```

- **host**: The host address to bind to (0.0.0.0 for all interfaces)
- **port**: The port to listen on
- **log_level**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **cors_origins**: List of allowed CORS origins
- **api_prefix**: Prefix for all API endpoints

### Models Configuration

```json
{
  "models": {
    "directory": "../models/llama-cpp",
    "default_model": "Phi-3-mini-4k-instruct-q4",
    "auto_load_default": true,
    "max_loaded_models": 3,
    "model_cache_size": 1,
    "scan_interval": 60,
    "supported_formats": [".gguf", ".bin"]
  }
}
```

- **directory**: Path to the directory containing GGUF model files
- **default_model**: ID of the default model to load
- **auto_load_default**: Whether to automatically load the default model on startup
- **max_loaded_models**: Maximum number of models to keep loaded in memory
- **model_cache_size**: Number of models to keep in cache for quick loading
- **scan_interval**: Interval in seconds to scan for new models
- **supported_formats**: List of supported model file formats

### Performance Configuration

```json
{
  "performance": {
    "optimize_for": "balanced",
    "max_memory_mb": 4096,
    "enable_gpu": true,
    "gpu_layers": 35,
    "num_threads": 4,
    "batch_size": 512,
    "context_window": 4096,
    "temperature": 0.7,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
    "max_tokens": 2048
  }
}
```

- **optimize_for**: Performance optimization strategy ("memory", "speed", "loading", "balanced")
- **max_memory_mb**: Maximum memory usage in MB
- **enable_gpu**: Whether to enable GPU acceleration
- **gpu_layers**: Number of layers to offload to GPU
- **num_threads**: Number of CPU threads to use
- **batch_size**: Batch size for processing
- **context_window**: Context window size in tokens
- **temperature**: Default temperature for text generation
- **top_p**: Default top-p value for text generation
- **repetition_penalty**: Repetition penalty for text generation
- **max_tokens**: Maximum number of tokens to generate

### Inference Configuration

```json
{
  "inference": {
    "timeout_ms": 30000,
    "stream_responses": false,
    "cache_enabled": true,
    "cache_ttl": 3600,
    "max_concurrent_requests": 10
  }
}
```

- **timeout_ms**: Timeout for inference requests in milliseconds
- **stream_responses**: Whether to stream responses
- **cache_enabled**: Whether to enable response caching
- **cache_ttl**: Time-to-live for cached responses in seconds
- **max_concurrent_requests**: Maximum number of concurrent inference requests

### KAREN Integration Configuration

```json
{
  "karen": {
    "integration_enabled": true,
    "optimize_for_karen": true,
    "karen_endpoint": "http://localhost:8000",
    "auth_token": null,
    "enable_local_fallback": true,
    "karen_prompt_template": true,
    "context_awareness": true,
    "memory_optimization": true
  }
}
```

- **integration_enabled**: Whether to enable KAREN integration
- **optimize_for_karen**: Whether to apply KAREN-specific optimizations
- **karen_endpoint**: URL of the KAREN API
- **auth_token**: Authentication token for KAREN API
- **enable_local_fallback**: Whether to enable local model fallback
- **karen_prompt_template**: Whether to use KAREN-specific prompt template
- **context_awareness**: Whether to enable context awareness
- **memory_optimization**: Whether to enable memory optimization for KAREN

### API Configuration

```json
{
  "api": {
    "enable_cors": true,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 10
    },
    "authentication": {
      "enabled": false,
      "api_key_header": "X-API-Key",
      "api_keys": []
    }
  }
}
```

- **enable_cors**: Whether to enable CORS
- **rate_limit**: Rate limiting configuration
  - **enabled**: Whether to enable rate limiting
  - **requests_per_minute**: Maximum requests per minute
  - **burst_limit**: Maximum burst requests
- **authentication**: Authentication configuration
  - **enabled**: Whether to enable authentication
  - **api_key_header**: Header name for API key
  - **api_keys**: List of valid API keys

### Monitoring Configuration

```json
{
  "monitoring": {
    "enabled": true,
    "metrics_endpoint": "/metrics",
    "health_endpoint": "/health",
    "check_interval": 30,
    "prometheus_enabled": false,
    "log_performance": true,
    "log_requests": false
  }
}
```

- **enabled**: Whether to enable monitoring
- **metrics_endpoint**: Endpoint for metrics
- **health_endpoint**: Endpoint for health checks
- **check_interval**: Interval in seconds for health checks
- **prometheus_enabled**: Whether to enable Prometheus metrics
- **log_performance**: Whether to log performance metrics
- **log_requests**: Whether to log API requests

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": null,
    "max_size": "10MB",
    "backup_count": 5,
    "structured_logging": false
  }
}
```

- **level**: Logging level
- **format**: Log message format
- **file**: Path to log file (null for console logging)
- **max_size**: Maximum log file size
- **backup_count**: Number of backup log files to keep
- **structured_logging**: Whether to use structured logging

## Environment Variables

You can override configuration values using environment variables. Environment variables should be prefixed with `LLAMA_` and use uppercase letters with underscores.

For example:

```bash
export LLAMA_SERVER_HOST=0.0.0.0
export LLAMA_SERVER_PORT=8080
export LLAMA_MODELS_DIRECTORY=../models/llama-cpp
export LLAMA_PERFORMANCE_OPTIMIZE_FOR=speed
export LLAMA_PERFORMANCE_ENABLE_GPU=true
export LLAMA_KAREN_INTEGRATION_ENABLED=true
export LLAMA_KAREN_KAREN_ENDPOINT=http://localhost:8000
```

## Example Configurations

### Development Configuration

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "DEBUG"
  },
  "models": {
    "directory": "../models/llama-cpp",
    "default_model": "tinyllama-1.1b-chat-v1.0.Q4_K_M",
    "auto_load_default": true,
    "max_loaded_models": 2
  },
  "performance": {
    "optimize_for": "speed",
    "max_memory_mb": 2048,
    "enable_gpu": false,
    "num_threads": 2
  },
  "karen": {
    "integration_enabled": true,
    "optimize_for_karen": true,
    "karen_endpoint": "http://localhost:8000"
  },
  "logging": {
    "level": "DEBUG",
    "structured_logging": true
  }
}
```

### Production Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "INFO"
  },
  "models": {
    "directory": "/opt/models/llama-cpp",
    "default_model": "Phi-3-mini-4k-instruct-q4",
    "auto_load_default": true,
    "max_loaded_models": 3
  },
  "performance": {
    "optimize_for": "balanced",
    "max_memory_mb": 8192,
    "enable_gpu": true,
    "gpu_layers": 35,
    "num_threads": 8
  },
  "inference": {
    "timeout_ms": 60000,
    "max_concurrent_requests": 20
  },
  "karen": {
    "integration_enabled": true,
    "optimize_for_karen": true,
    "karen_endpoint": "https://karen.example.com",
    "auth_token": "your-secure-token"
  },
  "api": {
    "enable_cors": false,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 120
    },
    "authentication": {
      "enabled": true,
      "api_keys": ["your-api-key-1", "your-api-key-2"]
    }
  },
  "monitoring": {
    "enabled": true,
    "prometheus_enabled": true
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/llama-cpp-server.log",
    "structured_logging": true
  }
}
```

### Resource-Constrained Configuration

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8080,
    "log_level": "INFO"
  },
  "models": {
    "directory": "../models/llama-cpp",
    "default_model": "tinyllama-1.1b-chat-v1.0.Q4_K_M",
    "auto_load_default": true,
    "max_loaded_models": 1
  },
  "performance": {
    "optimize_for": "memory",
    "max_memory_mb": 1024,
    "enable_gpu": false,
    "num_threads": 1,
    "context_window": 2048,
    "max_tokens": 512
  },
  "inference": {
    "timeout_ms": 60000,
    "max_concurrent_requests": 2
  },
  "karen": {
    "integration_enabled": true,
    "enable_local_fallback": true
  }
}
```

## Next Steps

1. Copy the configuration template to `config.json`
2. Modify the configuration according to your needs
3. Start the server with `python runServer.py`
4. Test the configuration with your preferred models
5. Monitor performance and adjust as needed