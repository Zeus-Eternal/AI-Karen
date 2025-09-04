#!/bin/bash
echo "[DEPRECATED] Docker deployment script is deprecated. Prefer local manager or build your own container." >&2
exit 1
# Docker deployment script for codeKent enhanced LLM providers
# Provides easy deployment options for different configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_DIR="$(dirname "$0")/../docker"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.yml"

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

# Function to check Docker requirements
check_docker_requirements() {
    print_status "Checking Docker requirements..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        print_status "Please install Docker from https://docker.com"
        exit 1
    fi
    
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not available"
        print_status "Please install Docker Compose or use Docker with compose plugin"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_status "Please start Docker daemon"
        exit 1
    fi
    
    print_success "Docker requirements satisfied"
}

# Function to check for GPU support
check_gpu_support() {
    print_status "Checking for GPU support..."
    
    if command_exists nvidia-smi && nvidia-smi >/dev/null 2>&1; then
        if docker run --rm --gpus all nvidia/cuda:12.2-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
            print_success "NVIDIA GPU support available"
            return 0
        else
            print_warning "NVIDIA GPU detected but Docker GPU support not configured"
            print_status "Install nvidia-container-toolkit for GPU support"
        fi
    fi
    
    print_warning "No GPU support detected - will use CPU-only deployment"
    return 1
}

# Function to create environment file
create_env_file() {
    local env_file="$DOCKER_DIR/.env"
    
    if [[ -f "$env_file" ]]; then
        print_status "Environment file already exists: $env_file"
        return 0
    fi
    
    print_status "Creating environment file..."
    
    cat > "$env_file" << 'EOF'
# codeKent Docker Environment Configuration

# Model directory (mount your models here)
MODELS_DIR=./models

# API Keys (set these for cloud providers)
OPENAI_API_KEY=
CLAUDE_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
DEEPSEEK_API_KEY=
HF_TOKEN=

# Grafana admin password (for monitoring)
GRAFANA_PASSWORD=admin

# cpp-llama configuration
CPP_LLAMA_CONTEXT_LENGTH=4096
CPP_LLAMA_BATCH_SIZE=512
CPP_LLAMA_THREADS=4
EOF
    
    print_success "Environment file created: $env_file"
    print_warning "Please edit $env_file to configure your API keys"
}

# Function to create models directory
create_models_directory() {
    local models_dir="$DOCKER_DIR/models"
    
    if [[ -d "$models_dir" ]]; then
        print_status "Models directory already exists: $models_dir"
        return 0
    fi
    
    print_status "Creating models directory..."
    mkdir -p "$models_dir"
    
    # Create README
    cat > "$models_dir/README.md" << 'EOF'
# Models Directory

Place your GGUF model files in this directory for use with cpp-llama.

## Downloading Models

You can download models from Hugging Face Hub:

```bash
# Example: Download a small model
wget -O llama-2-7b-chat.gguf "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"

# Or use huggingface-hub CLI
pip install huggingface_hub
huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_K_M.gguf --local-dir .
```

## Recommended Models

- **Small (< 4GB)**: TinyLlama, Phi-2
- **Medium (4-8GB)**: Llama-2-7B, CodeLlama-7B  
- **Large (8GB+)**: Llama-2-13B, CodeLlama-13B

Make sure models are in GGUF format for compatibility with cpp-llama.
EOF
    
    print_success "Models directory created: $models_dir"
}

# Function to deploy with specific profile
deploy_profile() {
    local profile="$1"
    local gpu_support="$2"
    
    print_status "Deploying with profile: $profile"
    
    cd "$DOCKER_DIR"
    
    # Use docker compose or docker-compose
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    # Build and start services
    case "$profile" in
        "cpu")
            $compose_cmd --profile cpu up -d --build
            ;;
        "gpu")
            if [[ "$gpu_support" == "true" ]]; then
                $compose_cmd --profile gpu up -d --build
            else
                print_error "GPU support not available, cannot deploy GPU profile"
                exit 1
            fi
            ;;
        "app")
            $compose_cmd --profile app --profile cpu up -d --build
            ;;
        "full")
            if [[ "$gpu_support" == "true" ]]; then
                $compose_cmd --profile full --profile gpu up -d --build
            else
                $compose_cmd --profile full --profile cpu up -d --build
            fi
            ;;
        "monitoring")
            $compose_cmd --profile monitoring up -d --build
            ;;
        *)
            print_error "Unknown profile: $profile"
            exit 1
            ;;
    esac
    
    print_success "Deployment completed successfully!"
}

# Function to show status
show_status() {
    print_status "Checking service status..."
    
    cd "$DOCKER_DIR"
    
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    $compose_cmd ps
    
    print_status "Service endpoints:"
    echo "  cpp-llama server: http://localhost:8080"
    echo "  codeKent app: http://localhost:8000"
    echo "  Grafana (if enabled): http://localhost:3000"
    echo "  Prometheus (if enabled): http://localhost:9090"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    cd "$DOCKER_DIR"
    
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    $compose_cmd down
    
    print_success "Services stopped"
}

# Function to clean up
cleanup() {
    print_status "Cleaning up Docker resources..."
    
    cd "$DOCKER_DIR"
    
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    $compose_cmd down -v --rmi all
    docker system prune -f
    
    print_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    local service="$1"
    
    cd "$DOCKER_DIR"
    
    local compose_cmd="docker compose"
    if ! docker compose version >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    fi
    
    if [[ -n "$service" ]]; then
        $compose_cmd logs -f "$service"
    else
        $compose_cmd logs -f
    fi
}

# Function to print usage
print_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  deploy <profile>  Deploy with specific profile"
    echo "  status           Show service status"
    echo "  stop             Stop all services"
    echo "  cleanup          Stop services and clean up resources"
    echo "  logs [service]   Show logs (optionally for specific service)"
    echo ""
    echo "Profiles:"
    echo "  cpu              cpp-llama server (CPU only)"
    echo "  gpu              cpp-llama server (GPU accelerated)"
    echo "  app              Full codeKent application with cpp-llama"
    echo "  full             Complete stack with monitoring"
    echo "  monitoring       Monitoring stack only"
    echo ""
    echo "Examples:"
    echo "  $0 deploy cpu                # Deploy CPU-only cpp-llama"
    echo "  $0 deploy gpu                # Deploy GPU-accelerated cpp-llama"
    echo "  $0 deploy app                # Deploy full application"
    echo "  $0 status                    # Check service status"
    echo "  $0 logs cpp-llama           # Show cpp-llama logs"
}

# Main execution
main() {
    local command="$1"
    
    case "$command" in
        "deploy")
            local profile="$2"
            if [[ -z "$profile" ]]; then
                print_error "Profile is required for deploy command"
                print_usage
                exit 1
            fi
            
            check_docker_requirements
            create_env_file
            create_models_directory
            
            local gpu_support="false"
            if check_gpu_support; then
                gpu_support="true"
            fi
            
            deploy_profile "$profile" "$gpu_support"
            show_status
            ;;
        "status")
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup
            ;;
        "logs")
            show_logs "$2"
            ;;
        "help"|"--help"|"-h"|"")
            print_usage
            ;;
        *)
            print_error "Unknown command: $command"
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
