# Llama.cpp Server Dependencies

This document lists all the Python dependencies required for the Llama.cpp Server for KAREN.

## Core Dependencies

### Web Server and API
- **fastapi>=0.104.0**: Modern, fast web framework for building APIs with Python
- **uvicorn[standard]>=0.24.0**: ASGI server for running FastAPI applications
- **pydantic>=2.5.0**: Data validation using Python type annotations

### HTTP and Async
- **aiohttp>=3.9.0**: Async HTTP client/server library for making requests to the KAREN API

### System Monitoring
- **psutil>=5.9.0**: Cross-platform library for retrieving information on running processes and system utilization

### Llama.cpp Integration
- **llama-cpp-python**: Python bindings for llama.cpp library

#### Installation Options

**Option 1: Basic Installation (CPU-only)**
```bash
pip install llama-cpp-python
```

**Option 2: With GPU Support (CUDA)**
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**Option 3: With Metal Support (Apple Silicon)**
```bash
CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

**Option 4: With OpenCL Support**
```bash
CMAKE_ARGS="-DLLAMA_CLBLAST=on" FORCE_CMAKE=1 pip install llama-cpp-python
```

### Optional Dependencies

#### For Enhanced Performance
- **numpy>=1.24.0**: For efficient numerical operations
- **scipy>=1.10.0**: For scientific computing optimizations

#### For Monitoring and Metrics
- **prometheus-client>=0.19.0**: For exposing metrics in Prometheus format
- **structlog>=23.1.0**: For structured logging

#### For Development and Testing
- **pytest>=7.4.0**: For testing the server
- **pytest-asyncio>=0.21.0**: For testing async code
- **httpx>=0.25.0**: For making HTTP requests in tests
- **black>=23.0.0**: For code formatting
- **isort>=5.12.0**: For import sorting
- **flake8>=6.0.0**: For linting

## Complete requirements.txt

```
# Core dependencies for Llama.cpp Server
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
aiohttp>=3.9.0
psutil>=5.9.0

# Llama.cpp integration
llama-cpp-python

# Optional performance dependencies
numpy>=1.24.0
scipy>=1.10.0

# Optional monitoring dependencies
prometheus-client>=0.19.0
structlog>=23.1.0

# Development dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
```

## Installation Steps

### 1. Create Virtual Environment (Recommended)

```bash
cd llama_CPP_Server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python -c "import fastapi, uvicorn, pydantic, aiohttp, psutil, llama_cpp; print('All dependencies installed successfully')"
```

## GPU Acceleration Setup

### NVIDIA GPUs (CUDA)

1. Ensure CUDA toolkit is installed
2. Install with CUDA support:

```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

### Apple Silicon (Metal)

1. Ensure Xcode command line tools are installed
2. Install with Metal support:

```bash
CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

### AMD GPUs (OpenCL)

1. Ensure OpenCL drivers are installed
2. Install with OpenCL support:

```bash
CMAKE_ARGS="-DLLAMA_CLBLAST=on" FORCE_CMAKE=1 pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

## Troubleshooting

### Installation Issues

If you encounter issues during installation:

1. Ensure you have the latest version of pip:
   ```bash
   pip install --upgrade pip
   ```

2. For compilation errors, ensure you have build tools installed:
   - **Windows**: Visual Studio Build Tools
   - **macOS**: Xcode command line tools
   - **Linux**: build-essential package

3. For GPU-related issues, ensure you have the appropriate drivers and SDKs installed

### Runtime Issues

If you encounter issues at runtime:

1. Check that all dependencies are installed correctly:
   ```bash
   pip check
   ```

2. Verify that the llama.cpp library is working:
   ```bash
   python -c "import llama_cpp; print(llama_cpp.__version__)"
   ```

3. Check system requirements:
   - Ensure you have enough RAM for your models
   - For GPU acceleration, ensure your GPU is properly configured

## Version Compatibility

The server is designed to work with the following versions:

| Component | Minimum Version | Recommended Version |
|-----------|----------------|---------------------|
| Python    | 3.8            | 3.9+               |
| FastAPI   | 0.104.0         | 0.104.0+           |
| Pydantic  | 2.5.0           | 2.5.0+             |
| llama.cpp | Latest          | Latest              |

## Security Considerations

When installing dependencies:

1. Always use virtual environments to isolate dependencies
2. Keep dependencies updated to patch security vulnerabilities:
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```
3. Review dependencies for known vulnerabilities:
   ```bash
   pip install pip-audit
   pip-audit
   ```

## Performance Considerations

For optimal performance:

1. Use the latest versions of all dependencies
2. Enable GPU acceleration if available
3. Consider using optimized builds of llama.cpp for your specific hardware
4. Monitor memory usage and adjust configuration accordingly

## Next Steps

After installing dependencies:

1. Follow the setup guide in `SETUP_GUIDE.md`
2. Configure the server according to your needs
3. Test with your preferred models
4. Integrate with your KAREN instance