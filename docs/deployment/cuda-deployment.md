# AI-Karen CUDA Deployment Guide

This guide explains how to deploy AI-Karen with CUDA-enabled llama.cpp for GPU acceleration.

## Prerequisites

### System Requirements
- NVIDIA GPU with CUDA support (RTX 2080 or better)
- CUDA 12.9 or later
- Docker and Docker Compose installed
- NVIDIA Container Toolkit
- At least 8GB GPU memory

### Software Dependencies
- Docker
- Docker Compose
- NVIDIA Container Toolkit

## Installation Steps

### 1. Verify System Requirements

```bash
# Check GPU availability
nvidia-smi

# Check Docker and NVIDIA runtime
docker info | grep -q "Runtimes:.*nvidia"

# Verify CUDA version
nvcc --version
```

### 2. Run the Deployment Script

```bash
# Make the script executable (if not already)
chmod +x deploy-cuda.sh

# Run the deployment
./deploy-cuda.sh
```

The deployment script will:
- Check system requirements
- Create necessary directories
- Update configuration files
- Pull Docker images
- Build the AI-Karen image
- Start the services

### 3. Manual Deployment (Optional)

If you prefer manual deployment:

```bash
# Set environment variables
export CUDA_VISIBLE_DEVICES=0
export KARI_LLAMACPP_HOST=llamacpp-cuda
export KARI_LLAMACPP_PORT=8080
export KARI_LLAMACPP_USE_CUDA=true

# Pull images
docker-compose -f docker-compose.cuda.yml pull llamacpp-cuda

# Build AI-Karen image
docker-compose -f docker-compose.cuda.yml build ai-karen

# Start services
docker-compose -f docker-compose.cuda.yml up -d
```

## Configuration

### Docker Compose Configuration

The `docker-compose.cuda.yml` file defines two services:

1. **llamacpp-cuda**: The CUDA-enabled llama.cpp service
2. **ai-karen**: The main AI-Karen application

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `CUDA_VISIBLE_DEVICES` | GPU device to use | `0` |
| `KARI_LLAMACPP_HOST` | llama.cpp service host | `llamacpp-cuda` |
| `KARI_LLAMACPP_PORT` | llama.cpp service port | `8080` |
| `KARI_LLAMACPP_USE_CUDA` | Enable CUDA support | `true` |

### Configuration Files

- `config/llamacpp/config.json`: llama.cpp configuration with GPU settings
- `docker-compose.cuda.yml`: Docker Compose configuration for CUDA deployment

## Service Management

### Starting Services

```bash
docker-compose -f docker-compose.cuda.yml up -d
```

### Stopping Services

```bash
docker-compose -f docker-compose.cuda.yml down
```

### Viewing Logs

```bash
# View all logs
docker-compose -f docker-compose.cuda.yml logs -f

# View specific service logs
docker-compose -f docker-compose.cuda.yml logs -f ai-karen
docker-compose -f docker-compose.cuda.yml logs -f llamacpp-cuda
```

### Health Checks

```bash
# Check service status
docker-compose -f docker-compose.cuda.yml ps

# Check individual service health
docker inspect --format='{{json .State.Health}}' ai-karen-llamacpp
docker inspect --format='{{json .State.Health}}' ai-karen-app
```

## Monitoring and Troubleshooting

### GPU Usage Monitoring

```bash
# Monitor GPU usage
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv

# Monitor Docker GPU usage
docker stats ai-karen-llamacpp
```

### Common Issues

#### 1. NVIDIA Runtime Not Available

```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list \
   && apt-get update && apt-get install -y nvidia-container-toolkit
```

#### 2. GPU Memory Issues

```bash
# Check available GPU memory
nvidia-smi --query-gpu=memory.total,memory.used --format=csv

# Adjust GPU memory usage in config/llamacpp/config.json
# Reduce n_gpu_layers or use smaller model
```

#### 3. Service Health Check Failures

```bash
# Check service logs
docker-compose -f docker-compose.cuda.yml logs llamacpp-cuda

# Restart the service
docker-compose -f docker-compose.cuda.yml restart llamacpp-cuda
```

## Performance Optimization

### GPU Layer Configuration

In `config/llamacpp/config.json`:
- `n_gpu_layers`: Number of layers to offload to GPU (-1 for all)
- `main_gpu`: Primary GPU device
- `offload_kqv`: Offload key-value cache to GPU
- `flash_attn`: Enable Flash Attention for better performance

### Memory Management

```bash
# Monitor memory usage
docker stats --no-stream

# Adjust batch size based on available GPU memory
# In config/llamacpp/config.json, adjust n_batch parameter
```

## Backup and Recovery

### Backup Configuration

```bash
# Backup configuration files
cp -r config/llamacpp/config.json config/llamacpp/config.json.backup

# Backup models (if any)
cp -r models/ models.backup
```

### Recovery

```bash
# Restore from backup
cp config/llamacpp/config.json.backup config/llamacpp/config.json

# Restart services
docker-compose -f docker-compose.cuda.yml restart
```

## Advanced Configuration

### Custom Docker Images

For custom builds:

```bash
# Build custom CUDA image
docker build \
  --build-arg PROFILE=runtime-cuda \
  -t ai-karen-custom:cuda \
  -f Dockerfile .
```

### Multi-GPU Configuration

```bash
# For multiple GPUs, update docker-compose.cuda.yml
environment:
  - CUDA_VISIBLE_DEVICES=0,1
  - NVIDIA_VISIBLE_DEVICES=all
```

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify system requirements
4. Create an issue on the GitHub repository