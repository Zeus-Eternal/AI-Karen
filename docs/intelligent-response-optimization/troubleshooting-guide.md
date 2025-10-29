# Troubleshooting Guide

This guide provides comprehensive troubleshooting information for common issues with model discovery, routing, and the Intelligent Response Optimization System.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Model Discovery Issues](#model-discovery-issues)
3. [Model Routing Problems](#model-routing-problems)
4. [Performance Issues](#performance-issues)
5. [Caching Problems](#caching-problems)
6. [GPU CUDA Issues](#gpu-cuda-issues)
7. [Progressive Streaming Issues](#progressive-streaming-issues)
8. [System Integration Problems](#system-integration-problems)
9. [Diagnostic Tools](#diagnostic-tools)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostics

### System Health Check

Run these commands to quickly assess system health:

```bash
# Check system status
curl -X GET http://localhost:8000/api/system/health

# Check optimization system status
curl -X GET http://localhost:8000/api/optimization/status

# Check model discovery status
curl -X GET http://localhost:8000/api/models/discovery/status

# Check active models
curl -X GET http://localhost:8000/api/models/active

# Check resource usage
curl -X GET http://localhost:8000/api/system/resources
```

### Common Status Indicators

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `HEALTHY` | System operating normally | None |
| `DEGRADED` | Reduced performance | Check performance metrics |
| `WARNING` | Issues detected | Review warnings and logs |
| `ERROR` | System errors present | Immediate attention required |
| `OFFLINE` | Component unavailable | Restart or repair component |

## Model Discovery Issues

### Issue: Models Not Being Discovered

#### Symptoms
- Models in `models/` directory not appearing in system
- Empty model list in UI
- Discovery status shows "No models found"

#### Diagnostic Steps
```bash
# Check discovery logs
curl -X GET http://localhost:8000/api/models/discovery/logs

# Check directory permissions
ls -la models/

# Verify model files
find models/ -name "*.safetensors" -o -name "*.bin" -o -name "config.json"

# Manual discovery trigger
curl -X POST http://localhost:8000/api/models/discovery/refresh
```

#### Common Causes and Solutions

**1. Permission Issues**
```bash
# Fix permissions
chmod -R 755 models/
chown -R $(whoami):$(whoami) models/
```

**2. Incomplete Model Files**
```bash
# Check for required files in each model directory
for dir in models/*/; do
    echo "Checking $dir"
    ls "$dir" | grep -E "(config\.json|\.safetensors|\.bin)"
done
```

**3. Configuration Issues**
```json
// Check config/model_discovery.json
{
  "discovery": {
    "enabled": true,
    "scan_paths": ["models/"],
    "supported_formats": ["safetensors", "bin", "gguf"]
  }
}
```

**4. Service Not Running**
```bash
# Check if discovery service is running
curl -X GET http://localhost:8000/api/models/discovery/status

# Restart discovery service
curl -X POST http://localhost:8000/api/models/discovery/restart
```

### Issue: Incorrect Model Metadata

#### Symptoms
- Wrong model information displayed
- Missing capabilities or modalities
- Incorrect categorization

#### Diagnostic Steps
```bash
# Check specific model metadata
curl -X GET http://localhost:8000/api/models/{model_id}/metadata

# Validate model files
curl -X POST http://localhost:8000/api/models/{model_id}/validate

# Check metadata extraction logs
curl -X GET http://localhost:8000/api/models/metadata/logs
```

#### Solutions

**1. Fix Model Configuration**
```json
// Add/update config.json in model directory
{
  "model_type": "llama",
  "architectures": ["LlamaForCausalLM"],
  "max_position_embeddings": 4096,
  "vocab_size": 32000
}
```

**2. Add Custom Metadata**
```json
// Create metadata.json in model directory
{
  "display_name": "Custom Model Name",
  "modalities": ["TEXT"],
  "capabilities": ["CHAT", "CODE"],
  "use_cases": ["conversation", "programming"]
}
```

**3. Manual Metadata Update**
```bash
curl -X PUT http://localhost:8000/api/models/{model_id}/metadata \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Updated Name", "capabilities": ["CHAT"]}'
```

### Issue: Model Discovery Performance Problems

#### Symptoms
- Slow discovery process
- High CPU usage during discovery
- Discovery timeouts

#### Solutions

**1. Optimize Discovery Configuration**
```json
{
  "discovery": {
    "scan_interval_minutes": 60,
    "max_scan_depth": 3,
    "parallel_scanning": true,
    "cache_metadata": true,
    "exclude_patterns": ["*.tmp", "*.lock", ".git"]
  }
}
```

**2. Reduce Scan Scope**
```json
{
  "discovery": {
    "scan_paths": ["models/active/"],
    "skip_large_files": true,
    "file_size_limit_mb": 1000
  }
}
```

## Model Routing Problems

### Issue: Selected Model Not Being Used

#### Symptoms
- User selects specific model but responses come from different model
- Model selection UI shows one model, but logs show another
- Inconsistent model usage across requests

#### Diagnostic Steps
```bash
# Check active model routing
curl -X GET http://localhost:8000/api/models/routing/status

# Verify model selection
curl -X GET http://localhost:8000/api/models/active

# Check routing logs
curl -X GET http://localhost:8000/api/models/routing/logs

# Test specific model routing
curl -X POST http://localhost:8000/api/models/{model_id}/test-route
```

#### Common Causes and Solutions

**1. Model Not Properly Loaded**
```bash
# Check model loading status
curl -X GET http://localhost:8000/api/models/{model_id}/status

# Force model loading
curl -X POST http://localhost:8000/api/models/{model_id}/load
```

**2. Fallback Logic Activated**
```bash
# Check fallback configuration
curl -X GET http://localhost:8000/api/models/routing/fallback-config

# Disable fallback temporarily for testing
curl -X PUT http://localhost:8000/api/models/routing/fallback \
  -d '{"enabled": false}'
```

**3. Profile-Based Routing Override**
```json
// Check profile routing configuration
{
  "profile_routing": {
    "chat": "llama-2-7b-chat",
    "code": "codellama-7b",
    "reasoning": "mixtral-8x7b"
  }
}
```

### Issue: Model Connection Failures

#### Symptoms
- "Model unavailable" errors
- Connection timeouts
- Model loading failures

#### Diagnostic Steps
```bash
# Test model connectivity
curl -X POST http://localhost:8000/api/models/{model_id}/test-connection

# Check model resource requirements
curl -X GET http://localhost:8000/api/models/{model_id}/requirements

# Verify system resources
curl -X GET http://localhost:8000/api/system/resources
```

#### Solutions

**1. Resource Allocation**
```bash
# Check available resources
free -h
nvidia-smi  # For GPU models

# Increase memory limits
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

**2. Model Loading Configuration**
```json
{
  "model_loading": {
    "timeout_seconds": 300,
    "retry_attempts": 3,
    "memory_optimization": true,
    "device_map": "auto"
  }
}
```

## Performance Issues

### Issue: High Response Times

#### Symptoms
- Responses taking longer than expected
- Timeout errors
- Poor user experience

#### Diagnostic Steps
```bash
# Check response time metrics
curl -X GET http://localhost:8000/api/optimization/metrics/response-times

# Check resource usage
curl -X GET http://localhost:8000/api/system/resources/current

# Check active optimizations
curl -X GET http://localhost:8000/api/optimization/active
```

#### Solutions

**1. Enable Aggressive Optimization**
```json
{
  "optimization": {
    "mode": "performance",
    "aggressive_caching": true,
    "lightweight_processing": true,
    "gpu_acceleration": true
  }
}
```

**2. Model Selection Optimization**
```bash
# Switch to faster model
curl -X PUT http://localhost:8000/api/models/active \
  -d '{"model_id": "tinyllama-1.1b-chat"}'

# Enable model caching
curl -X PUT http://localhost:8000/api/optimization/caching \
  -d '{"enabled": true, "aggressive": true}'
```

### Issue: High CPU Usage

#### Symptoms
- CPU usage above 5% per response
- System slowdown
- Resource exhaustion warnings

#### Diagnostic Steps
```bash
# Monitor CPU usage
curl -X GET http://localhost:8000/api/system/resources/cpu

# Check optimization settings
curl -X GET http://localhost:8000/api/optimization/config

# Check concurrent requests
curl -X GET http://localhost:8000/api/system/requests/active
```

#### Solutions

**1. CPU Usage Limits**
```json
{
  "cpu_optimization": {
    "max_cpu_per_request": 3.0,
    "concurrent_request_limit": 5,
    "auto_throttling": true
  }
}
```

**2. Lightweight Processing**
```json
{
  "lightweight_processing": {
    "skip_complex_analysis": true,
    "use_cached_computations": true,
    "parallel_processing": false
  }
}
```

### Issue: Memory Exhaustion

#### Symptoms
- Out of memory errors
- System crashes
- Model loading failures

#### Solutions

**1. Memory Management**
```json
{
  "memory_management": {
    "max_memory_usage_mb": 4096,
    "aggressive_cleanup": true,
    "model_unloading": true
  }
}
```

**2. Model Optimization**
```bash
# Use quantized models
curl -X PUT http://localhost:8000/api/models/optimization \
  -d '{"quantization": "int8", "memory_efficient": true}'
```

## Caching Problems

### Issue: Low Cache Hit Rate

#### Symptoms
- Cache hit rate below 50%
- Repeated computations
- Poor performance improvement

#### Diagnostic Steps
```bash
# Check cache statistics
curl -X GET http://localhost:8000/api/optimization/cache/stats

# Check cache configuration
curl -X GET http://localhost:8000/api/optimization/cache/config

# Analyze cache patterns
curl -X GET http://localhost:8000/api/optimization/cache/analysis
```

#### Solutions

**1. Optimize Cache Settings**
```json
{
  "smart_caching": {
    "similarity_threshold": 0.7,
    "ttl_seconds": 7200,
    "cache_warming": true,
    "predictive_caching": true
  }
}
```

**2. Cache Warming**
```bash
# Warm cache with common queries
curl -X POST http://localhost:8000/api/optimization/cache/warm \
  -d '{"queries": ["common query 1", "common query 2"]}'
```

### Issue: Cache Memory Issues

#### Symptoms
- High memory usage from cache
- Cache eviction warnings
- System slowdown

#### Solutions

**1. Cache Size Management**
```json
{
  "cache_management": {
    "max_cache_size_mb": 1024,
    "eviction_policy": "lru",
    "compression": true
  }
}
```

**2. Cache Cleanup**
```bash
# Clear cache
curl -X DELETE http://localhost:8000/api/optimization/cache/clear

# Optimize cache
curl -X POST http://localhost:8000/api/optimization/cache/optimize
```

## GPU CUDA Issues

### Issue: CUDA Not Detected

#### Symptoms
- GPU acceleration disabled
- CUDA unavailable warnings
- CPU-only processing

#### Diagnostic Steps
```bash
# Check CUDA availability
nvidia-smi
nvcc --version

# Check system CUDA detection
curl -X GET http://localhost:8000/api/system/cuda/status

# Test CUDA functionality
curl -X POST http://localhost:8000/api/system/cuda/test
```

#### Solutions

**1. CUDA Installation**
```bash
# Install CUDA drivers
sudo apt update
sudo apt install nvidia-driver-470 nvidia-cuda-toolkit

# Verify installation
nvidia-smi
```

**2. PyTorch CUDA Support**
```bash
# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: GPU Memory Problems

#### Symptoms
- CUDA out of memory errors
- GPU memory exhaustion
- Model loading failures

#### Solutions

**1. GPU Memory Management**
```json
{
  "gpu_memory": {
    "allocation_strategy": "dynamic",
    "memory_fraction": 0.7,
    "garbage_collection": true
  }
}
```

**2. Model Optimization**
```bash
# Use gradient checkpointing
curl -X PUT http://localhost:8000/api/models/gpu-optimization \
  -d '{"gradient_checkpointing": true, "mixed_precision": true}'
```

## Progressive Streaming Issues

### Issue: Streaming Interruptions

#### Symptoms
- Incomplete responses
- Streaming errors
- Connection drops

#### Diagnostic Steps
```bash
# Check streaming status
curl -X GET http://localhost:8000/api/optimization/streaming/status

# Check streaming logs
curl -X GET http://localhost:8000/api/optimization/streaming/logs

# Test streaming functionality
curl -X POST http://localhost:8000/api/optimization/streaming/test
```

#### Solutions

**1. Streaming Configuration**
```json
{
  "progressive_streaming": {
    "chunk_size": 128,
    "buffer_size": 1024,
    "timeout_ms": 5000,
    "retry_attempts": 3
  }
}
```

**2. Connection Stability**
```json
{
  "streaming_stability": {
    "heartbeat_interval": 1000,
    "reconnection_attempts": 5,
    "buffer_overflow_handling": true
  }
}
```

## System Integration Problems

### Issue: Reasoning Logic Disruption

#### Symptoms
- Incorrect decision making
- Missing reasoning steps
- Logic flow errors

#### Diagnostic Steps
```bash
# Check reasoning preservation
curl -X GET http://localhost:8000/api/optimization/reasoning/status

# Verify decision engine integration
curl -X GET http://localhost:8000/api/ai/decision-engine/status

# Test reasoning flow
curl -X POST http://localhost:8000/api/ai/test-reasoning
```

#### Solutions

**1. Reasoning Preservation**
```json
{
  "reasoning_preservation": {
    "preserve_decision_engine": true,
    "maintain_flow_manager": true,
    "keep_scaffolding": true
  }
}
```

**2. Integration Validation**
```bash
# Validate integration
curl -X POST http://localhost:8000/api/optimization/validate-integration
```

## Diagnostic Tools

### System Diagnostics Script

```bash
#!/bin/bash
# comprehensive_diagnostics.sh

echo "=== System Health Check ==="
curl -s http://localhost:8000/api/system/health | jq .

echo "=== Model Discovery Status ==="
curl -s http://localhost:8000/api/models/discovery/status | jq .

echo "=== Active Models ==="
curl -s http://localhost:8000/api/models/active | jq .

echo "=== Resource Usage ==="
curl -s http://localhost:8000/api/system/resources | jq .

echo "=== Optimization Status ==="
curl -s http://localhost:8000/api/optimization/status | jq .

echo "=== Cache Statistics ==="
curl -s http://localhost:8000/api/optimization/cache/stats | jq .

echo "=== GPU Status ==="
curl -s http://localhost:8000/api/system/cuda/status | jq .
```

### Log Analysis Tools

```bash
# Check recent errors
tail -n 100 logs/error.log | grep -i "optimization\|model\|routing"

# Monitor real-time logs
tail -f logs/optimization.log

# Search for specific issues
grep -r "model not found" logs/
grep -r "routing failed" logs/
grep -r "cache miss" logs/
```

### Performance Monitoring

```bash
# Monitor response times
watch -n 5 'curl -s http://localhost:8000/api/optimization/metrics/response-times'

# Monitor resource usage
watch -n 2 'curl -s http://localhost:8000/api/system/resources/current'

# Monitor cache performance
watch -n 10 'curl -s http://localhost:8000/api/optimization/cache/stats'
```

## Emergency Procedures

### System Recovery

**1. Safe Mode Activation**
```bash
# Enable safe mode (disables optimizations)
curl -X POST http://localhost:8000/api/system/safe-mode/enable

# Restart with minimal configuration
curl -X POST http://localhost:8000/api/system/restart-minimal
```

**2. Optimization Reset**
```bash
# Reset optimization settings
curl -X POST http://localhost:8000/api/optimization/reset

# Clear all caches
curl -X DELETE http://localhost:8000/api/optimization/cache/clear-all

# Restart optimization services
curl -X POST http://localhost:8000/api/optimization/restart
```

**3. Model System Reset**
```bash
# Reset model discovery
curl -X POST http://localhost:8000/api/models/discovery/reset

# Clear model cache
curl -X DELETE http://localhost:8000/api/models/cache/clear

# Reload default models
curl -X POST http://localhost:8000/api/models/load-defaults
```

### Rollback Procedures

**1. Configuration Rollback**
```bash
# Backup current config
cp config/response_optimization.json config/response_optimization.json.backup

# Restore previous config
cp config/response_optimization.json.previous config/response_optimization.json

# Restart system
curl -X POST http://localhost:8000/api/system/restart
```

**2. Model Rollback**
```bash
# Revert to previous model selection
curl -X PUT http://localhost:8000/api/models/active \
  -d '{"model_id": "previous_stable_model"}'
```

### Contact Support

If issues persist after following this guide:

1. Collect diagnostic information using the provided scripts
2. Check system logs for detailed error messages
3. Document steps taken and results observed
4. Contact system administrator with diagnostic data

### Prevention

- Regular system health checks
- Monitor performance metrics
- Keep configurations backed up
- Test changes in staging environment
- Maintain updated documentation

This troubleshooting guide covers the most common issues with the Intelligent Response Optimization System. Regular monitoring and proactive maintenance will help prevent many of these issues from occurring.