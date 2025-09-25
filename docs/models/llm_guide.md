# LLM Guide

Kari supports both local and remote language models through an integrated Model Library and LLM Settings interface. The system provides comprehensive model management, provider configuration, and seamless integration between different LLM providers.

> **📖 Need Help?** Throughout the LLM Settings and Model Library interfaces, look for help icons (?) that provide contextual guidance and detailed explanations. For comprehensive help, see the [Model Library Help Guide](model_library_help_guide.md).

## Overview

The LLM system consists of several key components:

- **Model Library**: Centralized model discovery, download, and management
- **LLM Settings**: Provider configuration and integration management
- **Provider System**: Support for local and cloud-based LLM providers
- **Compatibility Service**: Automatic model-provider compatibility checking
- **Integration Testing**: Comprehensive workflow validation

## Model Library

The Model Library provides a unified interface for managing LLM models with comprehensive help and guidance:

### Features

- **Model Discovery**: Browse available models from multiple sources with contextual help
- **Download Management**: Download models with progress tracking, validation, and guided assistance
- **Local Storage**: Organize and manage downloaded models with storage optimization tips
- **Metadata Management**: Comprehensive model information with detailed explanations
- **Search and Filtering**: Find models by provider, capabilities, size, etc. with search guidance
- **Contextual Help**: Integrated help system with tooltips and detailed explanations
- **Integration Testing**: Comprehensive workflow validation with diagnostic guidance

### Supported Model Formats

- **GGUF**: For llama-cpp provider (recommended for local execution)
- **Safetensors**: For Hugging Face Transformers
- **PyTorch**: For custom model implementations
- **API Models**: Cloud-based models accessed via APIs

### Model Categories

- **Local Models**: Downloaded and ready for immediate use
- **Available Models**: Can be downloaded from remote repositories
- **Downloading Models**: Currently being downloaded with progress tracking

## LLM Settings

LLM Settings provides comprehensive provider management and configuration:

### Provider Types

#### Cloud Providers
- **OpenAI**: GPT models via API
- **Gemini**: Google's language models
- **DeepSeek**: Coding and reasoning optimized models
- **Anthropic**: Claude models (when configured)

#### Local Providers
- **llama-cpp**: GGUF model execution (replaces LNM)
- **Hugging Face**: Transformers library integration
- **Custom**: Support for custom provider implementations

#### Legacy Support
- **LNM (Local Neural Module)**: Thin orchestrator for GGUF models (deprecated, use llama-cpp)
- **OSIRIS**: In-house reasoning engine (integrated with new system)

### Provider Configuration

Each provider requires specific setup:

#### Cloud Providers
```bash
# Set API keys via environment variables
export OPENAI_API_KEY="your-api-key"
export GEMINI_API_KEY="your-api-key"
export DEEPSEEK_API_KEY="your-api-key"
```

#### Local Providers
```bash
# Configure model directories
export LLAMA_CPP_MODELS_DIR="./models/gguf"
export TRANSFORMERS_MODELS_DIR="./models/transformers"
```

### Model Integration

The system automatically integrates downloaded models with compatible providers:

1. **Download Model**: Use Model Library to download compatible models
2. **Auto-Configuration**: Providers automatically detect and configure new models
3. **Compatibility Validation**: System ensures models work with providers
4. **Health Monitoring**: Continuous monitoring of provider and model status

## Usage Examples

### Basic Setup

1. **Access LLM Settings**:
   - Open Application Settings
   - Navigate to LLM Settings
   - Use the help icon (?) for interface guidance

2. **Configure Providers**:
   - Add API keys for cloud providers (help available for each provider)
   - Set up local model directories with path guidance
   - Run health checks with diagnostic help

3. **Download Models**:
   - Switch to Model Library tab
   - Browse available models with capability explanations
   - Use search and filtering with contextual help
   - Download compatible models with progress guidance

4. **Test Integration**:
   - Run comprehensive integration tests
   - Use workflow testing with step-by-step guidance
   - Verify provider health with diagnostic information
   - Test model functionality with troubleshooting help

### Getting Help

Throughout the interface, you'll find:
- **Help Icons (?)**: Click for detailed explanations
- **Tooltips**: Hover for quick guidance
- **Contextual Help**: Relevant help for each section
- **Integration Tests**: Diagnostic tools with guided resolution

### Local Model Setup (llama-cpp)

```bash
# 1. Set model directory
export LLAMA_CPP_MODELS_DIR="./models/gguf"

# 2. Download model via Model Library UI or manually
# Models are automatically detected and configured

# 3. Verify setup
# Use integration test in LLM Settings
```

### Cloud Provider Setup (OpenAI)

```bash
# 1. Set API key
export OPENAI_API_KEY="your-api-key"

# 2. Configure in LLM Settings
# API key validation happens automatically

# 3. Test connection
# Use provider health check
```

## Model Recommendations

The system provides intelligent model recommendations based on:

### Compatibility Scoring
- **Excellent (90-100%)**: Highly optimized for the provider
- **Good (70-89%)**: Compatible with minor limitations
- **Compatible (50-69%)**: Basic functionality available
- **Incompatible (<50%)**: Not recommended

### Recommendation Factors
- Model format compatibility
- Provider capabilities
- System resource requirements
- Performance characteristics
- License compatibility

## Advanced Features

### Profile Management

Create usage profiles for different scenarios:

- **Balanced**: General-purpose configuration
- **Performance**: Optimized for speed and quality
- **Cost**: Optimized for cost efficiency
- **Privacy**: Local-only execution

### Batch Operations

- Download multiple models simultaneously
- Configure multiple providers at once
- Bulk validation and testing
- Mass cleanup operations

### Integration Testing

Comprehensive testing includes:

- API connectivity validation
- Model discovery testing
- Provider health checks
- Compatibility validation
- End-to-end workflow testing

## Migration from Legacy System

### From LNM to llama-cpp

The new system replaces LNM with llama-cpp for better performance and compatibility:

```bash
# Old LNM usage
./lnm serve --model /models/mistral.gguf

# New llama-cpp integration
# Models are automatically managed through Model Library
# No manual server startup required
```

### From Manual Model Management

The Model Library replaces manual model management:

- **Before**: Manual download and file management
- **After**: Integrated download, validation, and organization
- **Benefits**: Automatic compatibility checking, metadata management, provider integration

## Troubleshooting

### Common Issues

#### Provider Not Healthy
- Check API keys and configuration (use provider help tooltips)
- Verify network connectivity with diagnostic tools
- Review provider-specific documentation linked in help
- Use provider health checks with guided resolution

#### Model Download Failures
- Check internet connection stability (download help available)
- Verify sufficient disk space with storage guidance
- Review firewall/proxy settings with network help
- Use download manager troubleshooting tools

#### Compatibility Issues
- Use compatibility checker in Model Library with explanations
- Try alternative model variants with recommendations
- Check system resource requirements with help guidance
- Review compatibility scoring explanations

#### Integration Problems
- Run comprehensive integration test with step-by-step guidance
- Check provider health status with diagnostic information
- Validate model file integrity with validation tools
- Use workflow testing with detailed error explanations

### Getting Help

The integrated help system provides multiple levels of assistance:

#### Contextual Help
- **Help Icons (?)**: Click for detailed explanations of any feature
- **Tooltips**: Hover for quick guidance and tips
- **Section Help**: Comprehensive help for entire sections
- **Error Help**: Specific guidance for error messages

#### Diagnostic Tools
- **Integration Tests**: Comprehensive workflow validation
- **Health Checks**: Provider and system health monitoring
- **Validation Tools**: Model and configuration validation
- **Troubleshooting Guides**: Step-by-step problem resolution

#### Documentation Resources
- **Model Library Help Guide**: Comprehensive user documentation
- **Technical Guides**: Advanced configuration and development
- **Best Practices**: Optimization and security recommendations
- **API Documentation**: Programmatic access information

#### Quick Help Access
- Use the help search to find specific topics
- Access quick help panels for common tasks
- Review contextual guidance based on your current state
- Follow guided workflows for complex operations

## Best Practices

### Security
- Store API keys in environment variables
- Regular key rotation for cloud providers
- Validate downloaded models before use
- Monitor usage and costs

### Performance
- Choose appropriate model sizes for your hardware
- Use quantized models for better performance
- Monitor system resources during model usage
- Regular cleanup of unused models

### Reliability
- Configure multiple providers for redundancy
- Test integration regularly
- Monitor provider health status
- Keep models and providers updated

## API Integration

For programmatic access, the system provides REST APIs:

```bash
# Get available models
GET /api/models/library

# Download a model
POST /api/models/download
{
  "model_id": "tinyllama-1.1b-chat-q4"
}

# Check provider health
GET /api/providers/health/llama-cpp

# Get integration status
GET /api/providers/integration/status
```

## Conclusion

The integrated Model Library and LLM Settings provide a comprehensive solution for managing language models and providers. The system ensures seamless integration, automatic compatibility checking, and reliable operation across different model types and providers.

## Help System and Documentation

The LLM system includes a comprehensive help system designed to guide users through all aspects of model and provider management.

### Contextual Help Features

#### In-Interface Help
- **Help Icons (?)**: Available throughout the interface for instant guidance
- **Tooltips**: Hover over any element for quick explanations
- **Section Help**: Comprehensive help for major interface sections
- **Interactive Guidance**: Step-by-step assistance for complex workflows

#### Help Content Types
- **Quick Tips**: Brief explanations for immediate understanding
- **Detailed Guides**: Comprehensive information with examples
- **Troubleshooting**: Specific solutions for common problems
- **Best Practices**: Recommendations for optimal usage

### Documentation Resources

#### User Documentation
- **[Model Library Help Guide](model_library_help_guide.md)**: Comprehensive user guide with contextual help
- **[Model Library User Guide](model_library_user_guide.md)**: Detailed feature documentation
- **This LLM Guide**: Overview and integration information

#### Technical Documentation
- **[Model Library Technical Guide](model_library_technical_guide.md)**: Developer and advanced user information
- **API Documentation**: Programmatic access and integration
- **Configuration Guides**: Advanced setup and customization

### Using the Help System

#### Getting Started
1. Look for help icons (?) throughout the interface
2. Hover over elements for quick tooltips
3. Click help icons for detailed explanations
4. Use the help search to find specific topics

#### Finding Specific Help
- **Search Help Content**: Use keywords to find relevant help
- **Browse by Category**: Navigate help topics by feature area
- **Contextual Suggestions**: Get help relevant to your current task
- **Quick Reference**: Access frequently needed information

#### Troubleshooting Workflow
1. **Identify the Issue**: Use diagnostic tools and error messages
2. **Check Contextual Help**: Look for help icons near the problem area
3. **Use Integration Tests**: Run comprehensive validation
4. **Consult Documentation**: Review detailed guides for complex issues
5. **Follow Resolution Steps**: Use guided troubleshooting procedures

The help system is designed to provide assistance at every level, from quick tooltips for immediate questions to comprehensive guides for complex workflows. This ensures that users can effectively utilize all features of the Model Library and LLM Settings.

For detailed technical information, see the [Model Library Technical Guide](model_library_technical_guide.md) and [Model Library User Guide](model_library_user_guide.md).

## Choosing a Model

 
Use the LLM Manager page in the Control Room or call the `/models` endpoints to select a backend. The `llm_manager` plugin stores the active model in a local registry so the SelfRefactor engine and other components share the same backend. Plugins can override the global model by providing their own settings.


```bash
curl -X POST -H "Content-Type: application/json" \
    -d '{"model": "hf://mistralai/Mixtral-8x7B"}' http://localhost:8000/models/select
```

See [docs/plugin_spec.md](plugin_spec.md) for manifest details and [docs/self_refactor.md](self_refactor.md) for how the SelfRefactor engine selects models dynamically.
