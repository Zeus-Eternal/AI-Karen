# Enhanced Unified LLM Client

The Enhanced Unified LLM Client provides local-first routing with intelligent model selection, warm-up mechanisms, and graceful fallback capabilities. This implementation extends the existing unified client to support the Response Core orchestrator's local-first principles.

## Features

### 🏠 Local-First Architecture
- **TinyLLaMA Support**: Direct integration with llama-cpp-python for local inference
- **Ollama Integration**: Support for Ollama server with multiple model options
- **Zero External Dependencies**: Operates fully without cloud API keys
- **Graceful Degradation**: Intelligent fallback when local models are unavailable

### 🧠 Intelligent Model Selection
- **Intent-Based Routing**: Selects models based on user intent (code_optimization, general_assist, etc.)
- **Context-Aware Decisions**: Routes to cloud for large context sizes (>4096 tokens)
- **Performance Hints**: Considers cloud routing only when explicitly beneficial
- **Local-Only Mode**: Enforces local-only operation regardless of hints

### ⚡ Performance Optimization
- **Model Warm-up**: Pre-loads and warms local models on startup
- **Performance Monitoring**: Tracks latency and routing decisions
- **Circuit Breaker Pattern**: Prevents cascading failures
- **Resource Management**: Efficient memory and CPU usage

### 🔄 Backward Compatibility
- **Legacy API Support**: Maintains compatibility with existing prompt-based API
- **Protocol Compliance**: Implements LLMClient protocol for drop-in replacement
- **Migration Path**: Easy upgrade from existing unified client

## Quick Start

### Basic Usage

```python
from core.response.unified_client import create_local_first_client

# Create local-first client
client = create_local_first_client(local_only=True)

# Generate response
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"}
]

response = client.generate(
    messages=messages,
    intent="general",
    context_size=100
)
print(response)
```

### Advanced Configuration

```python
from core.response.unified_client import UnifiedLLMClient, TinyLlamaClient, OllamaClient

# Create custom local clients
tinyllama = TinyLlamaClient(
    model_path="models/llama-cpp/custom-model.gguf",
    temperature=0.7,
    max_tokens=512
)

ollama = OllamaClient(
    model_name="llama2",
    base_url="http://localhost:11434",
    temperature=0.8
)

# Create unified client with custom configuration
client = UnifiedLLMClient(
    local_clients=[tinyllama, ollama],
    remote_client=None,  # No cloud client
    local_only=True,
    auto_warmup=True
)

# Use with intelligent routing
response = client.generate(
    messages=messages,
    intent="code_optimization",
    context_size=2000,
    cloud_hint=False  # Force local-only
)
```

### Cloud Integration (Optional)

```python
from your_cloud_client import CloudLLMClient

# Create cloud client (optional)
cloud_client = CloudLLMClient(api_key="your-key")

# Create client with cloud fallback
client = create_local_first_client(
    remote_client=cloud_client,
    local_only=False  # Allow cloud routing
)

# Cloud routing for complex tasks
response = client.generate(
    messages=complex_messages,
    intent="complex_analysis",
    context_size=8000,
    cloud_hint=True  # Suggest cloud might be beneficial
)
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedLLMClient                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  ModelSelector  │    │        Local Clients            │ │
│  │                 │    │  ┌─────────────────────────────┐ │ │
│  │ • Intent-based  │    │  │      TinyLlamaClient        │ │ │
│  │ • Context-aware │    │  │  • llama-cpp-python        │ │ │
│  │ • Performance   │    │  │  • Model warm-up           │ │ │
│  │   monitoring    │    │  │  • Chat format conversion  │ │ │
│  └─────────────────┘    │  └─────────────────────────────┘ │ │
│                         │  ┌─────────────────────────────┐ │ │
│  ┌─────────────────┐    │  │       OllamaClient          │ │ │
│  │  FallbackLLM    │    │  │  • HTTP API integration    │ │ │
│  │                 │    │  │  • Multiple model support  │ │ │
│  │ • Always works  │    │  │  • Chat/generate APIs      │ │ │
│  │ • Safe response │    │  └─────────────────────────────┘ │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Routing Logic

1. **Local-First Principle**: Always prefer local models
2. **Intent Analysis**: Route based on task complexity
3. **Context Evaluation**: Consider context size for routing
4. **Performance Hints**: Use cloud only when explicitly beneficial
5. **Graceful Fallback**: Ensure response even when all models fail

### Model Selection Criteria

| Criteria | Local Model | Cloud Model | Fallback |
|----------|-------------|-------------|----------|
| Default | ✅ Always | ❌ Never | ❌ Last resort |
| Local-only mode | ✅ Always | ❌ Never | ✅ If local fails |
| Large context (>4K tokens) | ✅ First try | ✅ If enabled | ✅ If all fail |
| Complex intent | ✅ First try | ✅ If enabled | ✅ If all fail |
| Cloud hint + enabled | ✅ First try | ✅ Second try | ✅ If all fail |

## Configuration

### Environment Variables

```bash
# TinyLLaMA Configuration
TINYLLAMA_MODEL_PATH="models/llama-cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
TINYLLAMA_CONTEXT_SIZE=2048
TINYLLAMA_THREADS=4

# Ollama Configuration
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="tinyllama"
OLLAMA_TIMEOUT=30

# Client Configuration
LOCAL_ONLY_MODE=true
AUTO_WARMUP=true
PERFORMANCE_MONITORING=true
```

### Model Setup

#### TinyLLaMA Setup

1. Download TinyLLaMA model:
```bash
mkdir -p models/llama-cpp
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  -O models/llama-cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

2. Install llama-cpp-python:
```bash
pip install llama-cpp-python
```

#### Ollama Setup

1. Install Ollama:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

2. Pull TinyLLaMA model:
```bash
ollama pull tinyllama
```

3. Start Ollama server:
```bash
ollama serve
```

## API Reference

### UnifiedLLMClient

#### Constructor

```python
UnifiedLLMClient(
    local_clients: Optional[List[LLMClient]] = None,
    remote_client: Optional[LLMClient] = None,
    local_only: bool = True,
    fallback_client: Optional[LLMClient] = None,
    auto_warmup: bool = True
)
```

#### Methods

##### generate()

```python
def generate(
    self, 
    messages: List[Dict[str, str]], 
    *,
    intent: str = "general",
    context_size: int = 0,
    cloud_hint: bool = False,
    **kwargs: Any
) -> str
```

**Parameters:**
- `messages`: List of message dictionaries with 'role' and 'content'
- `intent`: User intent for routing decisions
- `context_size`: Size of context in tokens
- `cloud_hint`: Performance hint suggesting cloud might be beneficial
- `**kwargs`: Additional generation parameters

**Returns:** Generated response text

##### get_available_models()

```python
def get_available_models(self) -> Dict[str, Any]
```

Returns information about available models including local clients, remote client, and fallback status.

### Factory Functions

#### create_local_first_client()

```python
def create_local_first_client(
    remote_client: Optional[LLMClient] = None,
    local_only: bool = True,
    tinyllama_path: Optional[str] = None,
    ollama_model: str = "tinyllama",
    ollama_url: str = "http://localhost:11434",
    **kwargs
) -> UnifiedLLMClient
```

Creates a local-first client with default TinyLLaMA and Ollama clients.

#### create_local_only_client()

```python
def create_local_only_client(**kwargs) -> UnifiedLLMClient
```

Creates a local-only client with default settings.

## Testing

### Unit Tests

```bash
python -m pytest src/core/response/tests/test_enhanced_unified_client.py -v
```

### Integration Demo

```bash
python examples/enhanced_unified_client_demo.py
```

### Manual Testing

```python
from core.response.unified_client import create_local_first_client

# Test basic functionality
client = create_local_first_client()
response = client.generate([{"role": "user", "content": "Hello"}])
print(response)

# Test model information
models = client.get_available_models()
print(models)
```

## Performance Considerations

### Memory Usage
- TinyLLaMA: ~1-2GB RAM
- Ollama: ~1-3GB RAM (depending on model)
- Client overhead: <100MB

### Latency
- Local models: 100-1000ms (depending on hardware)
- Cloud models: 500-3000ms (depending on network)
- Fallback: <1ms

### Throughput
- Single local model: 1-10 tokens/second
- Multiple local models: Parallel processing
- Cloud models: 10-50 tokens/second

## Troubleshooting

### Common Issues

#### TinyLLaMA Model Not Found
```
Error: Failed to load TinyLLaMA model: Failed to load model from file
```
**Solution:** Ensure model file exists at `models/llama-cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`

#### Ollama Connection Failed
```
Error: Failed to connect to Ollama: Connection refused
```
**Solution:** Start Ollama server with `ollama serve`

#### Model Not Found in Ollama
```
Error: model 'tinyllama' not found (status code: 404)
```
**Solution:** Pull model with `ollama pull tinyllama`

### Debug Mode

Enable debug logging to see routing decisions:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = create_local_first_client()
# Routing decisions will be logged
```

## Migration Guide

### From Original UnifiedLLMClient

```python
# Old API
client = UnifiedLLMClient(local_client, remote_client)
response = client.generate("Hello world", cloud=True)

# New API
client = create_local_first_client(remote_client=remote_client, local_only=False)
response = client.generate([{"role": "user", "content": "Hello world"}], cloud_hint=True)

# Or use legacy method for backward compatibility
response = client.generate_legacy("Hello world", cloud=True)
```

### Key Changes

1. **Messages Format**: Use list of message dictionaries instead of plain strings
2. **Intent Parameter**: Add intent for better routing decisions
3. **Cloud Hint**: Use `cloud_hint` instead of `cloud` parameter
4. **Local-First**: Default to local-only operation
5. **Multiple Local Clients**: Support for multiple local model types

## Contributing

### Adding New Local Clients

1. Implement the `LLMClient` protocol:
```python
class MyLocalClient:
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        # Implementation here
        pass
    
    def warmup(self):
        # Optional warmup implementation
        pass
```

2. Add to factory function:
```python
def create_local_first_client(...):
    local_clients = []
    # Add existing clients
    try:
        my_client = MyLocalClient()
        local_clients.append(my_client)
    except Exception as e:
        log.warning(f"MyLocalClient failed: {e}")
```

### Testing New Clients

1. Add unit tests in `test_enhanced_unified_client.py`
2. Add integration tests in demo script
3. Update documentation

## License

This implementation is part of the AI Karen project and follows the same licensing terms.