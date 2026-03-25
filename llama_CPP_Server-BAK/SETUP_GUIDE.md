# Llama.cpp Server Setup Guide

This guide will help you set up and configure the Llama.cpp Server for KAREN, an easy-to-use local server for GGUF models optimized for performance and tailored for KAREN integration.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.8 or higher
- Enough RAM to run your selected models (at least 4GB for small models, 8GB+ for larger ones)
- GGUF model files in the `models/llama-cpp/` directory

## Installation

### 1. Clone or Download the Repository

If you haven't already, ensure the `llama_CPP_Server` directory exists in your project structure.

### 2. Install Dependencies

The server requires several Python packages. Install them using pip:

```bash
cd llama_CPP_Server
pip install -r requirements.txt
```

If `requirements.txt` doesn't exist yet, you can install the dependencies manually:

```bash
pip install fastapi uvicorn aiohttp pydantic psutil
```

### 3. Install llama.cpp

The server depends on the llama.cpp library. You have two options:

#### Option A: Install from PyPI (Recommended)

```bash
pip install llama-cpp-python
```

#### Option B: Build from Source

For better performance, especially with GPU acceleration, you can build llama.cpp from source:

```bash
# Clone the llama.cpp repository
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Build the library
make

# Install the Python bindings
cd bindings/python
pip install -e .
```

### 4. Verify Installation

To verify that everything is installed correctly, run:

```bash
python -c "import llama_cpp; print('llama.cpp installed successfully')"
```

## Configuration

### 1. Create Configuration File

The server uses a JSON configuration file. Create a `config.json` file in the `llama_CPP_Server` directory:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "log_level": "INFO"
  },
  "models": {
    "directory": "../models/llama-cpp",
    "default_model": "Phi-3-mini-4k-instruct-q4",
    "auto_load_default": true,
    "max_loaded_models": 3
  },
  "performance": {
    "optimize_for": "balanced",
    "max_memory_mb": 4096,
    "enable_gpu": true,
    "num_threads": 4
  },
  "karen": {
    "integration_enabled": true,
    "optimize_for_karen": true,
    "karen_endpoint": "http://localhost:8000",
    "auth_token": null
  },
  "api": {
    "enable_cors": true,
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 60
    }
  }
}
```

### 2. Configure Models

Ensure you have GGUF model files in the `models/llama-cpp/` directory. The server will automatically scan this directory for available models.

If you don't have any models yet, you can download them from HuggingFace. For example:

```bash
# Download Phi-3-mini model
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf -O models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf
```

## Running the Server

### 1. Start the Server

You can start the server using the provided script:

```bash
python runServer.py
```

Or with custom parameters:

```bash
python runServer.py --config config.json --host 0.0.0.0 --port 8080 --models-dir ../models/llama-cpp --log-level INFO
```

### 2. Verify Server is Running

Once the server is running, you can verify it's working by accessing the health endpoint:

```bash
curl http://localhost:8080/health
```

You should see a JSON response with the server's health status.

### 3. Check Available Models

To see the list of available and loaded models:

```bash
curl http://localhost:8080/models
```

## Using the API

### 1. Load a Model

To load a specific model:

```bash
curl -X POST http://localhost:8080/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "Phi-3-mini-4k-instruct-q4"}'
```

### 2. Perform Inference

To generate text using the loaded model:

```bash
curl -X POST http://localhost:8080/inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 100
    }
  }'
```

### 3. Get Performance Metrics

To check performance metrics:

```bash
curl http://localhost:8080/performance
```

## KAREN Integration

### 1. Install the KAREN Extension

The KAREN integration is provided through a KAREN extension. Ensure the extension is properly installed in `src/extensions/llamacpp/`.

### 2. Configure the Extension

Edit the extension configuration in `src/extensions/llamacpp/extension_manifest.json` if needed:

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "server_url": {
        "type": "string",
        "default": "http://localhost:8080"
      },
      "default_model": {
        "type": "string",
        "default": "Phi-3-mini-4k-instruct-q4"
      },
      "enable_local_fallback": {
        "type": "boolean",
        "default": true
      }
    }
  }
}
```

### 3. Test the Integration

Once both the server and KAREN are running, the extension will automatically integrate local model inference into the KAREN workflow.

## Performance Optimization

The server includes several performance optimizations:

### 1. Memory Optimization

To optimize for memory usage:

```json
{
  "performance": {
    "optimize_for": "memory",
    "max_memory_mb": 2048,
    "enable_gpu": false
  }
}
```

### 2. Speed Optimization

To optimize for inference speed:

```json
{
  "performance": {
    "optimize_for": "speed",
    "enable_gpu": true,
    "num_threads": 8
  }
}
```

### 3. Loading Optimization

To optimize for model loading times:

```json
{
  "performance": {
    "optimize_for": "loading",
    "auto_load_default": true,
    "max_loaded_models": 1
  }
}
```

## Troubleshooting

### 1. Server Won't Start

If the server fails to start, check:

- Python version is 3.8 or higher
- All dependencies are installed
- The configuration file is valid JSON
- The models directory exists and is accessible

### 2. Model Loading Fails

If model loading fails, check:

- The model file exists and is a valid GGUF file
- You have enough RAM to load the model
- The model path in the configuration is correct

### 3. Inference is Slow

If inference is slow, try:

- Reducing the context window size
- Using a smaller model
- Enabling GPU acceleration if available
- Adjusting the number of threads

### 4. KAREN Integration Not Working

If the KAREN integration isn't working, check:

- The extension is properly installed
- The server URL in the extension configuration is correct
- Both the server and KAREN are running
- The server is accessible from KAREN

## Advanced Configuration

### 1. Environment Variables

You can override configuration values using environment variables:

```bash
export SERVER_HOST=0.0.0.0
export SERVER_PORT=8080
export MODELS_DIRECTORY=../models/llama-cpp
export LOG_LEVEL=INFO
```

### 2. Docker Deployment

To deploy the server using Docker:

1. Create a Dockerfile:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "runServer.py"]
```

2. Build and run:

```bash
docker build -t llama-cpp-server .
docker run -p 8080:8080 -v $(pwd)/models:/app/models llama-cpp-server
```

### 3. GPU Acceleration

To enable GPU acceleration:

1. Ensure you have a compatible GPU and drivers
2. Install the appropriate version of llama.cpp with GPU support
3. Enable GPU in the configuration:

```json
{
  "performance": {
    "enable_gpu": true,
    "gpu_layers": 35
  }
}
```

## Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the implementation plan in `IMPLEMENTATION_PLAN.md`
3. Check the logs for error messages
4. Ensure you're using the latest version of all dependencies

## Next Steps

Once the server is set up and running:

1. Test with your preferred models
2. Experiment with different performance configurations
3. Integrate with your KAREN instance
4. Monitor performance and adjust as needed