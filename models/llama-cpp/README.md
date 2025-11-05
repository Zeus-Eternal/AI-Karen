# Local LLM Models Directory

This directory is used by the `local-llm` service in Docker Compose to serve local language models.

## Adding Models

To use the local LLM service, you need to download a GGUF model file and place it in this directory.

### Recommended Model

The docker-compose.yml is configured to use:
- **Model**: Phi-3-mini-4k-instruct-q4.gguf
- **Location**: `models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf`

### How to Download

1. Visit HuggingFace: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
2. Download the `Phi-3-mini-4k-instruct-q4.gguf` file
3. Place it in this directory

### Alternative: Disable Local LLM Service

If you don't want to use local LLMs, you can disable the service:

```bash
# Start Docker Compose without local-llm service
docker compose up -d --scale local-llm=0
```

Or comment out the `local-llm` service in docker-compose.yml.

## Other Models

You can use any GGUF format model. To use a different model:

1. Place your model file in this directory
2. Update the `local-llm` service in docker-compose.yml:
   ```yaml
   command:
     - "-m"
     - "/models/<your-model-file>.gguf"
   ```

## Supported Formats

- GGUF (required for llama.cpp server)
- Model size should be appropriate for your system memory

## Resources

- llama.cpp: https://github.com/ggerganov/llama.cpp
- GGUF Models on HuggingFace: https://huggingface.co/models?library=gguf
