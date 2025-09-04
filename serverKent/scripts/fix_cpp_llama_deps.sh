#!/bin/bash
echo "[DEPRECATED] Dependency fixer is no longer needed. Use manager-based flow." >&2
exit 1
# Quick fix script for cpp-llama dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🔧 cpp-llama Dependencies Fix"
echo "============================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    print_status "Detected Linux system"
    
    # Check if we have apt (Debian/Ubuntu)
    if command -v apt >/dev/null 2>&1; then
        print_status "Installing dependencies with apt..."
        sudo apt update
        sudo apt install -y libcurl4-openssl-dev pkg-config
        print_success "Dependencies installed successfully"
        
    # Check if we have yum (CentOS/RHEL)
    elif command -v yum >/dev/null 2>&1; then
        print_status "Installing dependencies with yum..."
        sudo yum install -y libcurl-devel pkgconfig
        print_success "Dependencies installed successfully"
        
    # Check if we have dnf (Fedora)
    elif command -v dnf >/dev/null 2>&1; then
        print_status "Installing dependencies with dnf..."
        sudo dnf install -y libcurl-devel pkgconfig
        print_success "Dependencies installed successfully"
        
    else
        print_error "Could not detect package manager"
        print_status "Please install libcurl development libraries manually"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    print_status "Detected macOS system"
    
    if command -v brew >/dev/null 2>&1; then
        print_status "Installing dependencies with Homebrew..."
        brew install curl pkg-config
        print_success "Dependencies installed successfully"
    else
        print_error "Homebrew not found"
        print_status "Please install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo ""
print_status "Now rebuilding cpp-llama..."

# Clean and rebuild
INSTALL_DIR="$HOME/.kiro/cpp-llama"

if [[ -d "$INSTALL_DIR" ]]; then
    cd "$INSTALL_DIR"
    
    # Clean previous build
    rm -rf build
    mkdir -p build
    cd build
    
    # Configure with CMake
    print_status "Configuring with CMake..."
    cmake .. \
        -DLLAMA_BUILD_SERVER=ON \
        -DCMAKE_BUILD_TYPE=Release \
        -DLLAMA_CUDA=ON 2>/dev/null || \
    cmake .. \
        -DLLAMA_BUILD_SERVER=ON \
        -DCMAKE_BUILD_TYPE=Release
    
    # Build
    print_status "Building server..."
    cmake --build . --config Release --target server -j $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    
    # Copy server binary
    cp bin/server ../server 2>/dev/null || cp server ../server 2>/dev/null || true
    
    print_success "cpp-llama server built successfully!"
    print_status "Server binary: $INSTALL_DIR/server"
    
    # Test the server
    if [[ -f "$INSTALL_DIR/server" ]]; then
        print_status "Testing server binary..."
        if "$INSTALL_DIR/server" --help >/dev/null 2>&1; then
            print_success "Server binary is working correctly"
        else
            print_warning "Server binary may have issues, but build completed"
        fi
    fi
    
else
    print_error "cpp-llama directory not found at $INSTALL_DIR"
    print_status "Please run the main setup script first: ./scripts/setup_cpp_llama.sh"
    exit 1
fi

echo ""
print_success "🎉 Fix completed successfully!"
print_status "You can now:"
print_status "1. Download a model using the web interface: http://localhost:8000/static/model-manager.html"
print_status "2. Start the server: $INSTALL_DIR/start_server.sh"
print_status "3. Test the system: $INSTALL_DIR/health_check.sh"
