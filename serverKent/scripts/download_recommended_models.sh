#!/bin/bash
echo "[DEPRECATED] Use your own GGUFs in ./models or /models. This downloader is deprecated." >&2
exit 1

# Download Recommended Models Script
# This script downloads the essential AI models for Code Kent local inference

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Code Kent server is running
check_server() {
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_error "Code Kent server is not running on localhost:8000"
        print_status "Please start the server first:"
        print_status "  uvicorn src.app.codeKent:app --host 0.0.0.0 --port 8000 --reload"
        exit 1
    fi
    print_success "Code Kent server is running"
}

# Download a model via API
download_model() {
    local model_id="$1"
    local display_name="$2"
    
    print_status "Downloading $display_name ($model_id)..."
    
    # Start download
    local response=$(curl -s -X POST http://localhost:8000/api/models/download \
        -H "Content-Type: application/json" \
        -d "{\"model_id\": \"$model_id\", \"provider\": \"CPP_LLAMA\"}" 2>/dev/null)
    
    if echo "$response" | grep -q "error"; then
        print_error "Failed to start download for $display_name"
        echo "$response"
        return 1
    fi
    
    print_success "Download started for $display_name"
    
    # Monitor progress
    local progress_url="http://localhost:8000/api/models/download/progress/CPP_LLAMA::$model_id"
    local max_attempts=300  # 5 minutes max
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local progress=$(curl -s "$progress_url" 2>/dev/null)
        
        if echo "$progress" | grep -q "completed"; then
            print_success "$display_name download completed!"
            return 0
        elif echo "$progress" | grep -q "failed"; then
            print_error "$display_name download failed!"
            echo "$progress"
            return 1
        elif echo "$progress" | grep -q "progress"; then
            local percent=$(echo "$progress" | grep -o '"progress":[0-9]*' | cut -d':' -f2)
            if [ -n "$percent" ]; then
                printf "\r${BLUE}[INFO]${NC} $display_name: ${percent}%% complete"
            fi
        fi
        
        sleep 1
        ((attempt++))
    done
    
    print_warning "$display_name download timed out"
    return 1
}

# Manual download fallback
manual_download() {
    local url="$1"
    local filename="$2"
    local display_name="$3"
    
    print_status "Manually downloading $display_name..."
    
    # Create models directory if it doesn't exist
    mkdir -p models
    cd models
    
    # Download with wget
    if command -v wget >/dev/null 2>&1; then
        wget -c "$url" -O "$filename"
    elif command -v curl >/dev/null 2>&1; then
        curl -L -C - "$url" -o "$filename"
    else
        print_error "Neither wget nor curl is available for downloading"
        return 1
    fi
    
    if [ -f "$filename" ]; then
        print_success "$display_name downloaded successfully to models/llama-cpp/$filename"
        cd ..
        return 0
    else
        print_error "Failed to download $display_name"
        cd ..
        return 1
    fi
}

# Main function
main() {
    echo "🚀 Code Kent - Recommended Models Downloader"
    echo "=============================================="
    echo ""
    
    # Check if server is running
    check_server
    
    # Define models to download
    declare -A models=(
        ["qwen2.5-coder:0.5b"]="Qwen2.5-Coder 0.5B (Fast, lightweight)"
        ["deepseek-coder:1.3b"]="DeepSeek-Coder 1.3B (Advanced coding)"
        ["phi:3.8b"]="Phi-3 Mini 3.8B (General purpose)"
    )
    
    # Manual download URLs as fallback
    declare -A manual_urls=(
        ["qwen2.5-coder:0.5b"]="https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"
        ["deepseek-coder:1.3b"]="https://huggingface.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF/resolve/main/DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf"
        ["phi:3.8b"]="https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"
    )
    
    declare -A filenames=(
        ["qwen2.5-coder:0.5b"]="qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"
        ["deepseek-coder:1.3b"]="DeepSeek-Coder-V2-Lite-Instruct-Q4_K_M.gguf"
        ["phi:3.8b"]="Phi-3-mini-4k-instruct-q4.gguf"
    )
    
    local success_count=0
    local total_count=${#models[@]}
    
    # Download each model
    for model_id in "${!models[@]}"; do
        display_name="${models[$model_id]}"
        
        echo ""
        print_status "Processing: $display_name"
        
        # Try API download first
        if download_model "$model_id" "$display_name"; then
            ((success_count++))
        else
            print_warning "API download failed, trying manual download..."
            
            # Fallback to manual download
            if manual_download "${manual_urls[$model_id]}" "${filenames[$model_id]}" "$display_name"; then
                ((success_count++))
            else
                print_error "Both API and manual download failed for $display_name"
            fi
        fi
    done
    
    echo ""
    echo "=============================================="
    print_status "Download Summary: $success_count/$total_count models downloaded successfully"
    
    if [ $success_count -eq $total_count ]; then
        print_success "All recommended models downloaded successfully!"
        echo ""
        print_status "Next steps:"
        print_status "1. Start llama.cpp server: bash scripts/setup_cpp_llama.sh"
        print_status "2. Or manually start: /home/\$USER/.codeKent/server/cpp-llama/start_server.sh"
        print_status "3. Open Code Kent UI: http://127.0.0.1:3001"
    else
        print_warning "Some downloads failed. Check the errors above and try again."
        print_status "You can also download models manually from Hugging Face."
    fi
    
    echo ""
    print_status "Model storage location: $(pwd)/models"
    print_status "Total storage used: $(du -sh models 2>/dev/null | cut -f1 || echo 'N/A')"
}

# Run main function
main "$@"
