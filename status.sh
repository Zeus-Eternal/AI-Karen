#!/bin/bash

# AI-Karen Status Script
# Shows current deployment status and quick health check

echo "🤖 AI-Karen Status Check"
echo "========================"

# Check if AI-Karen is running
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ AI-Karen application: RUNNING"
else
    echo "❌ AI-Karen application: NOT RESPONDING"
fi

# Check GPU status
if nvidia-smi &> /dev/null; then
    gpu_info=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits)
    echo "🖥️  GPU Status: AVAILABLE"
    echo "   $gpu_info"
else
    echo "🖥️  GPU Status: NOT AVAILABLE"
fi

# Check deployment mode
if [ "$CUDA_VISIBLE_DEVICES" ]; then
    echo "🚀 Deployment Mode: CUDA ENABLED"
    echo "   CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
else
    echo "💻 Deployment Mode: CPU-ONLY"
fi

# Check if CUDA services are running
if docker ps | grep -q "ai-karen-llamacpp"; then
    echo "🔥 CUDA Service: RUNNING"
else
    echo "🧊 CUDA Service: NOT RUNNING (Expected in CPU mode)"
fi

echo ""
echo "📊 Quick Stats:"
echo "   Model: Phi-3-mini-4k-instruct-q4.gguf"
echo "   Config: $(jq -r '.n_gpu_layers' config/llamacpp/config.json) GPU layers"
echo "   Threads: $(jq -r '.n_threads' config/llamacpp/config.json) CPU threads"
echo "   Context: $(jq -r '.n_ctx' config/llamacpp/config.json) tokens"

echo ""
echo "🔧 Management Commands:"
echo "   Health Check: ./health-check-cuda.sh"
echo "   Performance Test: ./performance-test-cuda.sh"
if [ "$CUDA_VISIBLE_DEVICES" ]; then
    echo "   Deploy CUDA: ./deploy-cuda.sh"
else
    echo "   Enable CUDA: export CUDA_VISIBLE_DEVICES=0 && ./deploy-cuda.sh"
fi

echo ""
echo "🎯 Status check completed!"