# AI-Karen CUDA Deployment Files

This directory contains files for deploying AI-Karen with CUDA-enabled llama.cpp.

## Files

- `docker-compose.cuda.yml` - Docker Compose configuration for CUDA deployment
- `deploy-cuda.sh` - Deployment script for setting up CUDA environment
- `health-check-cuda.sh` - Health monitoring script for CUDA deployment
- `stop-cuda.sh` - Script to stop the CUDA deployment
- `.env.cuda` - Environment variables for CUDA support
- `cuda-deployment.md` - Comprehensive deployment guide

## Quick Start

1. **Prerequisites**:
   - NVIDIA GPU with CUDA support
   - Docker and Docker Compose
   - NVIDIA Container Toolkit

2. **Deploy**:
   ```bash
   ./deploy-cuda.sh
   ```

3. **Monitor**:
   ```bash
   ./health-check-cuda.sh
   ```

4. **Stop**:
   ```bash
   ./stop-cuda.sh
   ```

## Configuration

The deployment uses two main services:
- `llamacpp-cuda`: CUDA-enabled llama.cpp service
- `ai-karen`: Main AI-Karen application

Environment variables in `.env.cuda` control the CUDA configuration.

## Monitoring

Use `health-check-cuda.sh` to monitor:
- Service health status
- GPU usage
- Resource consumption
- Error logs

## Documentation

See `cuda-deployment.md` for detailed deployment instructions and troubleshooting.