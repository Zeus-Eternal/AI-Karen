#!/bin/bash
echo "[DEPRECATED] Setup script moved to legacy. Prefer scripts/llamacpp_service.sh and docs/llamacpp_manager.md." >&2
exec "$(dirname "$0")/legacy/setup_cpp_llama.sh" "$@" 2>/dev/null || exit 1
# Automated setup script for cpp-llama server installation
# This script downloads, builds, and configures llama.cpp for use with codeKent

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LLAMA_CPP_REPO="https://github.com/ggerganov/llama.cpp.git"
INSTALL_DIR="$HOME/.codeKent/server/cpp-llama"
SERVER_PORT=8080
DEFAULT_MODEL_DIR="./models"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    local os=$(detect_os)
    print_status "Detected OS: $os"
    
    # Check for required tools
    local missing_tools=()
    
    if ! command_exists git; then
        missing_tools+=("git")
    fi
    
    if ! command_exists make; then
        missing_tools+=("make")
    fi
    
    if ! command_exists cmake; then
        missing_tools+=("cmake")
    fi
    
    if ! command_exists gcc && ! command_exists clang; then
        missing_tools+=("gcc or clang")
    fi
    
    # Check for curl development libraries
    if [[ $(detect_os) == "linux" ]]; then
        if ! pkg-config --exists libcurl 2>/dev/null && ! find /usr/include -name "curl.h" 2>/dev/null | grep -q curl; then
            missing_tools+=("libcurl-dev")
        fi
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_status "Please install the missing tools and run this script again."
        
        case $os in
            "linux")
                print_status "On Ubuntu/Debian: sudo apt update && sudo apt install git build-essential cmake libcurl4-openssl-dev"
                print_status "On CentOS/RHEL: sudo yum groupinstall 'Development Tools' && sudo yum install git cmake libcurl-devel"
                ;;
            "macos")
                print_status "Install Xcode Command Line Tools: xcode-select --install"
                print_status "Or install via Homebrew: brew install git cmake curl"
                ;;
        esac
        
        exit 1
    fi
    
    print_success "All required tools are available"
}

# Function to check for GPU support
check_gpu_support() {
    print_status "Checking for GPU support..."
    
    local gpu_support=""
    
    # Check for NVIDIA GPU
    if command_exists nvidia-smi; then
        if nvidia-smi >/dev/null 2>&1; then
            print_success "NVIDIA GPU detected"
            gpu_support="cuda"
        fi
    fi
    
    # Check for AMD GPU (ROCm)
    if command_exists rocm-smi; then
        if rocm-smi >/dev/null 2>&1; then
            print_success "AMD GPU with ROCm detected"
            gpu_support="rocm"
        fi
    fi
    
    # Check for Apple Silicon
    if [[ $(detect_os) == "macos" ]] && [[ $(uname -m) == "arm64" ]]; then
        print_success "Apple Silicon detected - Metal support available"
        gpu_support="metal"
    fi
    
    if [[ -z "$gpu_support" ]]; then
        print_warning "No GPU acceleration detected - will use CPU only"
        gpu_support="cpu"
    fi
    
    echo "$gpu_support"
}

# Function to clone or update llama.cpp repository
setup_repository() {
    print_status "Setting up llama.cpp repository..."
    
    mkdir -p "$(dirname "$INSTALL_DIR")"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        print_status "Updating existing llama.cpp repository..."
        cd "$INSTALL_DIR"
        git pull origin master
    else
        print_status "Cloning llama.cpp repository..."
        git clone "$LLAMA_CPP_REPO" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    print_success "Repository setup complete"
}

# Function to build llama.cpp with appropriate flags
build_llama_cpp() {
    local gpu_support=$1
    print_status "Building llama.cpp with $gpu_support support..."
    
    cd "$INSTALL_DIR"
    
    # Check if cmake is available
    if ! command_exists cmake; then
        print_error "CMake is required but not installed"
        print_status "Please install CMake:"
        case $(detect_os) in
            "linux")
                print_status "  Ubuntu/Debian: sudo apt install cmake"
                print_status "  CentOS/RHEL: sudo yum install cmake"
                ;;
            "macos")
                print_status "  Homebrew: brew install cmake"
                print_status "  MacPorts: sudo port install cmake"
                ;;
        esac
        exit 1
    fi
    
    # Clean previous builds
    rm -rf build 2>/dev/null || true
    mkdir -p build
    cd build
    
    # Set CMake flags based on GPU support
    local cmake_flags=()
    case $gpu_support in
        "cuda")
            cmake_flags+=("-DLLAMA_CUDA=ON")
            print_status "Building with CUDA support..."
            ;;
        "rocm")
            cmake_flags+=("-DLLAMA_HIPBLAS=ON")
            print_status "Building with ROCm support..."
            ;;
        "metal")
            cmake_flags+=("-DLLAMA_METAL=ON")
            print_status "Building with Metal support..."
            ;;
        "cpu")
            print_status "Building with CPU-only support..."
            ;;
    esac
    
    # Add common flags
    cmake_flags+=("-DLLAMA_BUILD_SERVER=ON")
    cmake_flags+=("-DCMAKE_BUILD_TYPE=Release")
    
    # Check if curl is available, disable if not
    if ! pkg-config --exists libcurl 2>/dev/null && ! find /usr/include -name "curl.h" 2>/dev/null | grep -q curl; then
        print_warning "CURL development libraries not found, disabling CURL support"
        cmake_flags+=("-DLLAMA_CURL=OFF")
    fi
    
    # Configure with CMake
    print_status "Configuring build with CMake..."
    if cmake .. "${cmake_flags[@]}"; then
        print_success "CMake configuration successful"
    else
        print_error "CMake configuration failed"
        exit 1
    fi
    
    # Build the server
    print_status "Building server (this may take several minutes)..."
    local num_cores=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    
    # Try building llama-server first (newer versions), then fallback to server
    if cmake --build . --config Release --target llama-server -j "$num_cores"; then
        print_success "llama.cpp server built successfully"
        
        # Copy server binary to main directory for easier access
        cp bin/llama-server ../server 2>/dev/null || cp llama-server ../server 2>/dev/null || true
        
    elif cmake --build . --config Release --target server -j "$num_cores"; then
        print_success "llama.cpp server built successfully"
        
        # Copy server binary to main directory for easier access
        cp bin/server ../server 2>/dev/null || cp server ../server 2>/dev/null || true
        
    else
        print_error "Failed to build llama.cpp server"
        exit 1
    fi
}

# Function to create model directory
setup_model_directory() {
    print_status "Setting up model directory..."
    
    mkdir -p "$DEFAULT_MODEL_DIR"
    
    # Create a README in the models directory
    cat > "$DEFAULT_MODEL_DIR/README.md" << EOF
# codeKent Models Directory

This directory is used to store GGUF model files for cpp-llama.

## Downloading Models

You can download models from Hugging Face Hub:

\`\`\`bash
# Example: Download a small model
wget https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/pytorch_model.bin

# Or use huggingface-hub CLI
pip install huggingface_hub
huggingface-cli download microsoft/DialoGPT-medium --local-dir ./DialoGPT-medium
\`\`\`

## Recommended Models

- **Small (< 4GB)**: TinyLlama, Phi-2
- **Medium (4-8GB)**: Llama-2-7B, CodeLlama-7B
- **Large (8GB+)**: Llama-2-13B, CodeLlama-13B

## Model Format

Make sure models are in GGUF format. You can convert models using:

\`\`\`bash
python $INSTALL_DIR/convert.py /path/to/original/model
\`\`\`
EOF
    
    print_success "Model directory created at $DEFAULT_MODEL_DIR"
}

# Function to create startup script
create_startup_script() {
    local gpu_support=$1
    print_status "Creating startup script..."
    
    local startup_script="$INSTALL_DIR/start_server.sh"
    
    cat > "$startup_script" << EOF
#!/bin/bash
# cpp-llama server startup script for codeKent
# Generated by setup_cpp_llama.sh

set -e

# Configuration
SERVER_PORT=$SERVER_PORT
MODEL_DIR="$DEFAULT_MODEL_DIR"
INSTALL_DIR="$INSTALL_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "\${GREEN}[cpp-llama]\${NC} \$1"
}

print_warning() {
    echo -e "\${YELLOW}[cpp-llama]\${NC} \$1"
}

print_error() {
    echo -e "\${RED}[cpp-llama]\${NC} \$1"
}

# Function to find a model file
find_model() {
    local model_file=""
    
    # Check if a specific model was provided
    if [[ -n "\$1" ]] && [[ -f "\$1" ]]; then
        model_file="\$1"
    elif [[ -n "\$1" ]] && [[ -f "\$MODEL_DIR/\$1" ]]; then
        model_file="\$MODEL_DIR/\$1"
    else
        # Find the first .gguf file in the model directory
        model_file=\$(find "\$MODEL_DIR" -name "*.gguf" -type f | head -n 1)
    fi
    
    echo "\$model_file"
}

# Main execution
main() {
    print_status "Starting cpp-llama server..."
    
    # Check if server binary exists
    if [[ ! -f "\$INSTALL_DIR/server" ]]; then
        print_error "Server binary not found. Please run setup script first."
        exit 1
    fi
    
    # Find model file
    local model_file=\$(find_model "\$1")
    
    if [[ -z "\$model_file" ]]; then
        print_error "No model file found."
        print_status "Please download a GGUF model to \$MODEL_DIR"
        print_status "Or specify a model file: \$0 /path/to/model.gguf"
        exit 1
    fi
    
    print_status "Using model: \$model_file"
    print_status "Server will be available at: http://127.0.0.1:\$SERVER_PORT"
    print_status "Health check: http://127.0.0.1:\$SERVER_PORT/health"
    print_status "Models endpoint: http://127.0.0.1:\$SERVER_PORT/v1/models"
    
    # Server arguments based on GPU support
    local server_args=(
        "--model" "\$model_file"
        "--port" "\$SERVER_PORT"
        "--host" "127.0.0.1"
        "--ctx-size" "4096"
        "--batch-size" "512"
        "--threads" "\$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
    )
    
EOF

    # Add GPU-specific arguments
    case $gpu_support in
        "cuda")
            cat >> "$startup_script" << 'EOF'
    # CUDA-specific arguments
    server_args+=("--n-gpu-layers" "-1")  # Use all GPU layers
EOF
            ;;
        "metal")
            cat >> "$startup_script" << 'EOF'
    # Metal-specific arguments
    server_args+=("--n-gpu-layers" "-1")  # Use all GPU layers
EOF
            ;;
    esac
    
    cat >> "$startup_script" << 'EOF'
    
    # Start the server
    print_status "Starting server with arguments: ${server_args[*]}"
    exec "$INSTALL_DIR/server" "${server_args[@]}"
}

# Handle script arguments
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [model_file]"
    echo ""
    echo "Arguments:"
    echo "  model_file    Path to GGUF model file (optional)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Use first model found in $MODEL_DIR"
    echo "  $0 llama-2-7b.gguf          # Use specific model from model directory"
    echo "  $0 /path/to/model.gguf      # Use model from absolute path"
    exit 0
fi

main "$@"
EOF
    
    chmod +x "$startup_script"
    print_success "Startup script created at $startup_script"
}

# Function to create systemd service (Linux only)
create_systemd_service() {
    if [[ $(detect_os) != "linux" ]]; then
        return 0
    fi
    
    print_status "Creating systemd service..."
    
    local service_file="/tmp/cpp-llama.service"
    
    cat > "$service_file" << EOF
[Unit]
Description=cpp-llama server for codeKent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start_server.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_status "Systemd service file created at $service_file"
    print_status "To install the service, run:"
    print_status "  sudo cp $service_file /etc/systemd/system/"
    print_status "  sudo systemctl daemon-reload"
    print_status "  sudo systemctl enable cpp-llama"
    print_status "  sudo systemctl start cpp-llama"
}

# Function to create health check script
create_health_check() {
    print_status "Creating health check script..."
    
    local health_script="$INSTALL_DIR/health_check.sh"
    
    cat > "$health_script" << EOF
#!/bin/bash
# Health check script for cpp-llama server

SERVER_URL="http://127.0.0.1:$SERVER_PORT"
TIMEOUT=10

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check_health() {
    if command -v curl >/dev/null 2>&1; then
        response=\$(curl -s -w "%{http_code}" -o /dev/null --max-time \$TIMEOUT "\$SERVER_URL/health" 2>/dev/null)
    elif command -v wget >/dev/null 2>&1; then
        response=\$(wget -q -O /dev/null -T \$TIMEOUT --server-response "\$SERVER_URL/health" 2>&1 | grep "HTTP/" | tail -1 | awk '{print \$2}')
    else
        echo -e "\${RED}Error: Neither curl nor wget is available\${NC}"
        exit 1
    fi
    
    if [[ "\$response" == "200" ]]; then
        echo -e "\${GREEN}✅ cpp-llama server is healthy\${NC}"
        echo "Server URL: \$SERVER_URL"
        
        # Try to get model info
        if command -v curl >/dev/null 2>&1; then
            models=\$(curl -s --max-time \$TIMEOUT "\$SERVER_URL/v1/models" 2>/dev/null)
            if [[ \$? -eq 0 ]] && [[ -n "\$models" ]]; then
                echo "Models endpoint: \$SERVER_URL/v1/models"
            fi
        fi
        
        exit 0
    else
        echo -e "\${RED}❌ cpp-llama server is not responding\${NC}"
        echo "Expected HTTP 200, got: \$response"
        echo "Server URL: \$SERVER_URL"
        exit 1
    fi
}

check_health
EOF
    
    chmod +x "$health_script"
    print_success "Health check script created at $health_script"
}

# Function to update codeKent configuration
update_codekent_config() {
    print_status "Updating codeKent configuration..."
    
    # Check if migration tool exists
    if [[ -f "src/llm/migrate_config.py" ]]; then
        print_status "Running configuration setup..."
        python -m src.llm.migrate_config setup cpp-llama || true
    fi
    
    # Set environment variables
    local env_file="$HOME/.kiro/cpp_llama.env"
    cat > "$env_file" << EOF
# cpp-llama environment variables for codeKent
export CPP_LLAMA_BASE="http://127.0.0.1:$SERVER_PORT"
export CPP_LLAMA_MODEL_PATH="$DEFAULT_MODEL_DIR"
export CPP_LLAMA_CONTEXT_LENGTH="4096"
export CPP_LLAMA_GPU_LAYERS="-1"
export CPP_LLAMA_BATCH_SIZE="512"
export CPP_LLAMA_SPECULATIVE_DECODING="true"
export CPP_LLAMA_PARALLEL_PROCESSING="true"
EOF
    
    print_success "Environment configuration created at $env_file"
    print_status "To use these settings, run: source $env_file"
}

# Function to print final instructions
print_final_instructions() {
    print_success "cpp-llama setup completed successfully!"
    echo ""
    print_status "📁 Installation directory: $INSTALL_DIR"
    print_status "📁 Model directory: $DEFAULT_MODEL_DIR"
    print_status "🚀 Startup script: $INSTALL_DIR/start_server.sh"
    print_status "🏥 Health check: $INSTALL_DIR/health_check.sh"
    echo ""
    print_status "Next steps:"
    echo "  1. Download a GGUF model to $DEFAULT_MODEL_DIR"
    echo "  2. Start the server: $INSTALL_DIR/start_server.sh"
    echo "  3. Check health: $INSTALL_DIR/health_check.sh"
    echo "  4. Configure codeKent to use: http://127.0.0.1:$SERVER_PORT"
    echo ""
    print_status "Example model download:"
    echo "  cd $DEFAULT_MODEL_DIR"
    echo "  wget https://huggingface.co/microsoft/DialoGPT-medium/resolve/main/model.gguf"
    echo ""
    print_warning "Remember to source the environment file:"
    echo "  source $HOME/.kiro/cpp_llama.env"
}

# Main execution
main() {
    echo "🚀 codeKent cpp-llama Setup Script"
    echo "=================================="
    echo ""
    
    check_requirements
    local gpu_support=$(check_gpu_support)
    setup_repository
    build_llama_cpp "$gpu_support"
    setup_model_directory
    create_startup_script "$gpu_support"
    create_systemd_service
    create_health_check
    update_codekent_config
    print_final_instructions
}

# Handle script arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo ""
        echo "This script will:"
        echo "  1. Check system requirements"
        echo "  2. Clone/update llama.cpp repository"
        echo "  3. Build the server with GPU support if available"
        echo "  4. Create startup and health check scripts"
        echo "  5. Configure codeKent integration"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
