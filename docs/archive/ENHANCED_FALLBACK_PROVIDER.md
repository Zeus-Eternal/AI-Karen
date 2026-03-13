# Enhanced Fallback Provider - Local Model Integration

## Overview

The AI-Karen platform now includes an **Enhanced Fallback Provider** that intelligently uses local downloaded models (transformers and llama-cpp) to provide real AI responses even when cloud providers are unavailable or fail.

## Features

### 🎯 Intelligent Fallback Hierarchy

The provider implements a **4-tier fallback system**:

1. **Registered LLaMA-CPP Provider** - Uses the system's configured llama-cpp provider
2. **Local LLaMA-CPP Models** - Directly loads GGUF models from `/models/llama-cpp/`
3. **Local Transformers Models** - Loads HuggingFace models from `/models/transformers/`
4. **Intelligent Error-Based Fallback** - Provides helpful guidance based on actual errors

### 🔍 Automatic Model Discovery

The provider automatically scans local directories for available models:

**LLaMA-CPP Models (GGUF format):**
- Scans: `/mnt/development/KIRO/AI-Karen/models/llama-cpp/`
- Supported: `.gguf` files
- Examples:
  - `Phi-3-mini-4k-instruct-q4.gguf` (2.4GB)
  - `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` (668MB)

**Transformers Models:**
- Scans: `/mnt/development/KIRO/AI-Karen/models/transformers/`
- Supported: Models with `config.json`, `pytorch_model.bin`, or `model.safetensors`
- Examples:
  - `deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B`
  - `microsoft--DialoGPT-medium`
  - `gpt2`
  - `distilbert-base-uncased`
  - `sentence-transformers--all-MiniLM-L6-v2`

### 🧠 Error-Aware Responses

The provider classifies errors and provides context-aware fallback messages:

- **model_load_failed**: Suggests checking file paths, disk space, and memory
- **generation_failed**: Indicates memory/resource constraints
- **no_models**: Prompts to ensure models are downloaded and configured
- **unknown_error**: Provides generic helpful suggestions

### ⚡ Performance Optimizations

- **Model Caching**: Loaded models are reused across requests
- **Smart Selection**: Prefers smaller models for faster responses
- **Lazy Loading**: Models are loaded only when needed
- **Comprehensive Logging**: Tracks which source was used for each request

## Configuration

### Environment Variables (Optional)

```bash
# Enable model library integration
AI_KAREN_ENABLE_MODEL_LIBRARY=true

# Custom model paths (if different from default)
KAREN_MODEL_BASE_PATH=/path/to/models
KAREN_LLAMACPP_PATH=/path/to/llama-cpp/models
KAREN_TRANSFORMERS_PATH=/path/to/transformers/models
```

### Default Credentials

The system supports these default credentials for testing:

```
Username: admin
Password: admin123
```

OR

```
Email: admin@kari.ai
Password: admin123
```

## Usage

### API Integration

The enhanced fallback provider automatically works through the existing conversation API:

```bash
curl -X POST http://localhost:8000/api/ai/conversation-processing \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello! How can you help me today?",
    "conversation_history": [],
    "user_settings": {},
    "include_memories": true,
    "include_insights": true
  }'
```

### Web UI Integration

The KAREN-Theme-Default UI automatically uses the enhanced fallback when cloud providers fail. No configuration changes needed in the frontend.

## Monitoring and Debugging

### Health Check

Check the fallback provider status:

```bash
curl http://localhost:8000/api/ai/health
```

Response example:

```json
{
  "status": "healthy",
  "message": "Fallback provider operational",
  "checked_at": "2026-01-21T22:00:00.000000",
  "local_models_count": 7,
  "local_models_discovered": [
    "llamacpp_Phi-3-mini-4k-instruct-q4",
    "llamacpp_tinyllama-1.1b-chat-v1.0.Q4_K_M",
    "transformers_deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B",
    "transformers_microsoft--DialoGPT-medium",
    "transformers_gpt2",
    "transformers_distilbert-base-uncased",
    "transformers_sentence-transformers--all-MiniLM-L6-v2"
  ]
}
```

### Provider Information

Get detailed provider info:

```bash
curl http://localhost:8000/api/ai/flows
```

### Logging

The provider logs detailed information about each fallback attempt:

```
INFO:kari.fallback_provider:Attempting to use registered llamacpp provider
INFO:kari.fallback_provider:✓ Successfully used registered llamacpp provider
```

OR if fallback occurs:

```
INFO:kari.fallback_provider:Attempting to use local llama-cpp models
INFO:kari.fallback_provider:Attempting to use local model: llamacpp_tinyllama-1.1b-chat-v1.0.Q4_K_M
INFO:kari.fallback_provider:✓ Successfully used local llama-cpp model
```

## Troubleshooting

### Models Not Discovered

**Problem:** Health check shows 0 local models

**Solutions:**
1. Verify models directory exists: `ls -la /mnt/development/KIRO/AI-Karen/models/`
2. Check file permissions: Models must be readable by the application
3. Verify file formats: GGUF for llama-cpp, valid model directories for transformers
4. Check logs for specific errors during model discovery

### Model Loading Failures

**Problem:** Models are discovered but fail to load

**Solutions:**
1. Check available memory: Large models require sufficient RAM
2. Verify file integrity: Corrupted model files will fail to load
3. Check dependencies: Ensure `llama-cpp-python` and `transformers` are installed
4. Review logs: Specific error messages indicate the root cause

### Slow Responses

**Problem:** Local model responses are slow

**Solutions:**
1. Use smaller models: `tinyllama` is faster than `Phi-3`
2. Reduce `max_tokens` in generation parameters
3. Enable GPU acceleration if available
4. Use CPU optimization: Set `OMP_NUM_THREADS` environment variable

## Technical Details

### File Locations

```
/mnt/development/KIRO/AI-Karen/
├── src/ai_karen_engine/integrations/providers/
│   └── fallback_provider.py          # Enhanced fallback implementation
├── src/ai_karen_engine/inference/
│   ├── transformers_runtime.py       # Transformers engine
│   └── llamacpp_runtime.py           # LLaMA-CPP engine
└── models/
    ├── llama-cpp/                    # GGUF models
    │   ├── Phi-3-mini-4k-instruct-q4.gguf
    │   └── tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    └── transformers/                 # HuggingFace models
        ├── deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B/
        ├── microsoft--DialoGPT-medium/
        └── gpt2/
```

### Architecture

```
User Request (Chat Message)
    ↓
Frontend (KAREN-Theme-Default)
    ↓
API Proxy (/api/ai/conversation-processing)
    ↓
AI Orchestrator
    ↓
Provider Selection (with Fallback)
    ↓
┌─────────────────────────────────────┐
│ Enhanced Fallback Provider          │
│ ┌─────────────────────────────────┐ │
│ │ 1. Try registered llamacpp      │ │
│ │ 2. Try local llama-cpp models   │ │
│ │ 3. Try local transformers       │ │
│ │ 4. Intelligent fallback message │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
    ↓
Response with metadata (model used, confidence, etc.)
```

## Future Enhancements

- [ ] Add GPU acceleration support for local models
- [ ] Implement model-specific prompt templates
- [ ] Add streaming support for local models
- [ ] Create model benchmarking tools
- [ ] Add automatic model downloading from HuggingFace
- [ ] Implement model versioning and rollback

## Contributing

To add support for additional model formats:

1. Create a new runtime class in `src/ai_karen_engine/inference/`
2. Add model discovery logic in `_discover_local_models()`
3. Add generation method in `_try_local_<format>()`
4. Update the fallback hierarchy in `generate_text()`

## License

This enhancement is part of the AI-Karen enterprise platform and follows the same license terms.
