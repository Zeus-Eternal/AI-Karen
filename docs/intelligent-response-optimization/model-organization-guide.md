# Model Organization and Metadata Management Guide

This guide provides comprehensive instructions for administrators to manage model discovery, organization, and metadata in the Intelligent Response Optimization System.

## Table of Contents

1. [Overview](#overview)
2. [Model Directory Structure](#model-directory-structure)
3. [Model Discovery Process](#model-discovery-process)
4. [Model Metadata Management](#model-metadata-management)
5. [Model Categorization](#model-categorization)
6. [Model Organization Best Practices](#model-organization-best-practices)
7. [Troubleshooting Model Discovery](#troubleshooting-model-discovery)

## Overview

The Model Discovery Engine automatically scans the `models/*` directory to find and register all available models, regardless of format or type. This system supports:

- **Multiple Model Formats**: LLAMA_CPP, HuggingFace, OpenAI, Transformers, ONNX, and more
- **Modality Detection**: Text, image, video, audio, and multimodal capabilities
- **Automatic Categorization**: Primary, secondary, and specialization classifications
- **Metadata Extraction**: Comprehensive model information from config files and model cards

## Model Directory Structure

### Recommended Directory Layout

```
models/
├── language/
│   ├── chat/
│   │   ├── llama-2-7b-chat/
│   │   ├── mistral-7b-instruct/
│   │   └── codellama-7b-instruct/
│   ├── code/
│   │   ├── codellama-13b/
│   │   ├── starcoder-15b/
│   │   └── deepseek-coder-6.7b/
│   └── reasoning/
│       ├── llama-2-70b/
│       └── mixtral-8x7b/
├── vision/
│   ├── llava-1.5-7b/
│   ├── blip2-opt-2.7b/
│   └── clip-vit-large/
├── audio/
│   ├── whisper-large-v3/
│   └── wav2vec2-base/
├── multimodal/
│   ├── gpt-4-vision/
│   └── flamingo-9b/
└── specialized/
    ├── medical/
    │   └── biogpt-large/
    ├── legal/
    │   └── legal-bert/
    └── scientific/
        └── scibert-scivocab/
```

### Model File Structure

Each model directory should contain:

```
model-name/
├── config.json              # Model configuration
├── tokenizer_config.json    # Tokenizer configuration
├── model.safetensors        # Model weights (or .bin files)
├── tokenizer.json           # Tokenizer files
├── special_tokens_map.json  # Special tokens
├── README.md               # Model card/documentation
└── metadata.json           # Custom metadata (optional)
```

## Model Discovery Process

### Automatic Discovery

The system automatically discovers models on startup and periodically refreshes the registry:

```python
# Trigger manual model discovery refresh
POST /api/models/discovery/refresh

# Check discovery status
GET /api/models/discovery/status

# View discovered models
GET /api/models/discovered
```

### Discovery Configuration

Configure discovery settings in `config/model_discovery.json`:

```json
{
  "discovery": {
    "scan_interval_minutes": 30,
    "auto_refresh_on_startup": true,
    "scan_subdirectories": true,
    "max_scan_depth": 5,
    "supported_formats": [
      "safetensors",
      "bin",
      "onnx",
      "gguf",
      "ggml"
    ],
    "exclude_patterns": [
      "*.tmp",
      "*.lock",
      ".git",
      "__pycache__"
    ]
  }
}
```

### Manual Model Registration

For models that aren't automatically discovered:

```python
# Register a model manually
POST /api/models/register
{
  "name": "custom-model",
  "path": "/path/to/model",
  "type": "HUGGINGFACE",
  "modalities": ["TEXT"],
  "capabilities": ["CHAT", "CODE"]
}
```

## Model Metadata Management

### Automatic Metadata Extraction

The system extracts metadata from various sources:

1. **config.json**: Model architecture, parameters, context length
2. **tokenizer_config.json**: Tokenizer settings, vocabulary size
3. **README.md**: Model description, use cases, performance metrics
4. **metadata.json**: Custom metadata fields

### Custom Metadata Fields

Create a `metadata.json` file in the model directory:

```json
{
  "display_name": "Llama 2 Chat 7B",
  "description": "Fine-tuned for conversational AI",
  "use_cases": ["chat", "customer_support", "creative_writing"],
  "performance_metrics": {
    "inference_speed": "fast",
    "memory_usage": "moderate",
    "accuracy_score": 0.85
  },
  "specialized_domains": ["general", "customer_service"],
  "language_support": ["en", "es", "fr", "de"],
  "license": "custom",
  "author": "Meta AI",
  "version": "2.0",
  "tags": ["conversational", "instruction-following", "safe"],
  "resource_requirements": {
    "min_ram_gb": 8,
    "recommended_ram_gb": 16,
    "gpu_memory_gb": 6,
    "cpu_cores": 4
  },
  "optimization_settings": {
    "quantization": "int8",
    "context_length": 4096,
    "batch_size": 1,
    "temperature": 0.7
  }
}
```

### Updating Model Metadata

```python
# Update model metadata
PUT /api/models/{model_id}/metadata
{
  "display_name": "Updated Model Name",
  "tags": ["new_tag", "updated"],
  "performance_metrics": {
    "accuracy_score": 0.90
  }
}

# Bulk update metadata
POST /api/models/metadata/bulk-update
{
  "updates": [
    {
      "model_id": "model1",
      "metadata": {...}
    },
    {
      "model_id": "model2", 
      "metadata": {...}
    }
  ]
}
```

## Model Categorization

### Automatic Categorization

Models are automatically categorized based on:

1. **Primary Category**: LANGUAGE, VISION, AUDIO, MULTIMODAL
2. **Secondary Category**: CHAT, CODE, REASONING, CREATIVE, ANALYSIS
3. **Specialization**: MEDICAL, LEGAL, TECHNICAL, SCIENTIFIC, GENERAL

### Category Configuration

Configure categorization rules in `config/model_categorization.json`:

```json
{
  "categorization_rules": {
    "primary_category": {
      "LANGUAGE": {
        "keywords": ["text", "language", "nlp", "gpt", "llama", "bert"],
        "file_patterns": ["*.safetensors", "tokenizer.json"]
      },
      "VISION": {
        "keywords": ["vision", "image", "visual", "clip", "vit", "resnet"],
        "modalities": ["IMAGE"]
      },
      "AUDIO": {
        "keywords": ["audio", "speech", "whisper", "wav2vec"],
        "modalities": ["AUDIO"]
      },
      "MULTIMODAL": {
        "keywords": ["multimodal", "vision-language", "flamingo"],
        "modalities": ["TEXT", "IMAGE"]
      }
    },
    "secondary_category": {
      "CHAT": {
        "keywords": ["chat", "instruct", "conversation", "assistant"]
      },
      "CODE": {
        "keywords": ["code", "programming", "codellama", "starcoder"]
      },
      "REASONING": {
        "keywords": ["reasoning", "logic", "math", "problem-solving"]
      }
    }
  }
}
```

### Manual Category Assignment

```python
# Update model category
PUT /api/models/{model_id}/category
{
  "primary": "LANGUAGE",
  "secondary": "CODE",
  "specialization": "TECHNICAL"
}
```

## Model Organization Best Practices

### 1. Consistent Naming Convention

Use descriptive, consistent names:
- `{base-model}-{size}-{variant}` (e.g., `llama-2-7b-chat`)
- Include version numbers when applicable
- Use lowercase with hyphens for directories

### 2. Proper Directory Structure

- Group models by primary function (language, vision, audio)
- Create subdirectories for specialized use cases
- Keep related models together (base model + fine-tuned variants)

### 3. Complete Metadata

Ensure each model has:
- Comprehensive description
- Accurate capability tags
- Resource requirements
- Performance characteristics
- License information

### 4. Regular Maintenance

- Remove unused or outdated models
- Update metadata when model performance changes
- Monitor disk space usage
- Validate model integrity periodically

### 5. Access Control

Configure model access permissions:

```json
{
  "access_control": {
    "public_models": ["llama-2-7b-chat", "mistral-7b"],
    "restricted_models": ["gpt-4", "claude-3"],
    "admin_only_models": ["experimental-model"],
    "user_groups": {
      "developers": ["code-models"],
      "researchers": ["research-models"],
      "production": ["stable-models"]
    }
  }
}
```

## Troubleshooting Model Discovery

### Common Issues

#### 1. Models Not Discovered

**Symptoms**: Models in `models/` directory not appearing in the system

**Solutions**:
- Check file permissions (models directory must be readable)
- Verify model files are complete (config.json, model weights)
- Check discovery logs: `GET /api/models/discovery/logs`
- Manually trigger discovery: `POST /api/models/discovery/refresh`

#### 2. Incorrect Model Metadata

**Symptoms**: Wrong model information or missing capabilities

**Solutions**:
- Verify config.json format and content
- Add custom metadata.json file
- Update metadata manually via API
- Check categorization rules configuration

#### 3. Model Loading Failures

**Symptoms**: Models discovered but fail to load

**Solutions**:
- Check model file integrity
- Verify sufficient system resources
- Review model-specific requirements
- Check compatibility with current system

#### 4. Performance Issues

**Symptoms**: Slow model discovery or high resource usage

**Solutions**:
- Reduce scan frequency in configuration
- Exclude unnecessary directories
- Limit scan depth
- Use model caching

### Diagnostic Commands

```bash
# Check model discovery status
curl -X GET http://localhost:8000/api/models/discovery/status

# View discovery logs
curl -X GET http://localhost:8000/api/models/discovery/logs

# Test model loading
curl -X POST http://localhost:8000/api/models/{model_id}/test-load

# Validate model metadata
curl -X GET http://localhost:8000/api/models/{model_id}/validate

# Check system resources
curl -X GET http://localhost:8000/api/system/resources
```

### Log Analysis

Monitor these log files for discovery issues:
- `logs/model_discovery.log`: Discovery process logs
- `logs/model_validation.log`: Model validation results
- `logs/metadata_extraction.log`: Metadata processing logs
- `logs/categorization.log`: Model categorization logs

## Advanced Configuration

### Custom Discovery Plugins

Create custom discovery plugins for specialized model formats:

```python
# plugins/custom_model_discovery.py
from ai_karen_engine.services.model_discovery_engine import ModelDiscoveryPlugin

class CustomModelDiscoveryPlugin(ModelDiscoveryPlugin):
    def can_handle(self, path: str) -> bool:
        return path.endswith('.custom')
    
    def extract_metadata(self, path: str) -> ModelMetadata:
        # Custom metadata extraction logic
        pass
    
    def detect_modalities(self, path: str) -> List[Modality]:
        # Custom modality detection
        pass
```

### Integration with External Model Registries

Configure integration with HuggingFace Hub, Model Zoo, etc.:

```json
{
  "external_registries": {
    "huggingface": {
      "enabled": true,
      "api_key": "your_api_key",
      "sync_interval_hours": 24,
      "auto_download": false
    },
    "model_zoo": {
      "enabled": false,
      "endpoint": "https://modelzoo.co/api"
    }
  }
}
```

This completes the Model Organization and Metadata Management Guide. The system provides comprehensive tools for discovering, organizing, and managing models with rich metadata support and flexible categorization options.