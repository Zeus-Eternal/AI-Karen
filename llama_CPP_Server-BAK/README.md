# Llama.cpp Server for KAREN Integration

A premium, user-friendly llama.cpp server implementation designed for seamless integration with KAREN. This server provides easy installation, configuration, and management of large language models with comprehensive monitoring and optimization tools.

## Features

- **Easy Installation**: Automated installation wizard with support for virtual environments
- **User-Friendly Configuration**: Interactive setup script with comprehensive configuration options
- **Model Management**: Automatic downloader for popular GGUF models with progress tracking
- **System Optimization**: Automatic hardware detection and performance optimization
- **Web Dashboard**: Modern, responsive web interface for model management and server monitoring
- **Error Handling**: Comprehensive error handling with user guidance and troubleshooting
- **KAREN Integration**: Pre-configured for seamless integration with KAREN

## Quick Start

### Prerequisites

- Python 3.8 or higher
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space minimum (more for models)
- GPU with CUDA support recommended (not required)

### Installation

1. **One-Click Installation (Recommended)**
   ```bash
   python install_karen.py
   ```

2. **Manual Installation**
   ```bash
   # Install llama.cpp
   python install_llamacpp.py
   
   # Configure the server
   python setup.py
   
   # Start the server
   python start.py
   ```

### Usage

1. **Start the Server**
   ```bash
   python start.py
   ```

2. **Access the Dashboard**
   Open your web browser and navigate to `http://localhost:8081`

3. **Load a Model**
   - Use the dashboard to download and load models
   - Or use the command line:
     ```bash
     python model_downloader.py
     ```

## Configuration

The server can be configured through:

1. **Interactive Setup**
   ```bash
   python setup.py
   ```

2. **Configuration File**
   Edit `config/config.json`:
   ```json
   {
     "server": {
       "host": "localhost",
       "port": 8080,
       "log_level": "INFO"
     },
     "performance": {
       "num_threads": 8,
       "batch_size": 1,
       "context_window": 4096,
       "low_vram": false
     },
     "models": {
       "directory": "models",
       "max_loaded_models": 2,
       "max_cache_gb": 8.0
     }
   }
   ```

3. **Environment Variables**
   ```bash
   export LLAMA_SERVER_HOST=localhost
   export LLAMA_SERVER_PORT=8080
   export LLAMA_MODELS_DIR=models
   ```

## Model Management

### Downloading Models

1. **Using the Dashboard**
   - Navigate to the Models tab
   - Click "Add Model"
   - Select from popular models or provide a custom URL

2. **Using the Command Line**
   ```bash
   python model_downloader.py
   ```

### Supported Models

- **Llama 2**: `llama-2-7b-chat`, `llama-2-13b-chat`, `llama-2-70b-chat`
- **Mistral**: `mistral-7b-instruct`, `mixtral-8x7b-instruct`
- **Custom Models**: Any GGUF format model

### Model Optimization

The server automatically optimizes settings based on your hardware:

- **Low-End Systems** (≤8GB RAM, ≤4 CPU cores):
  - Single model loading
  - Reduced context window (2048)
  - Low VRAM mode enabled

- **Mid-Range Systems** (16GB RAM, 8 CPU cores):
  - Up to 2 models loaded
  - Standard context window (4096)
  - GPU acceleration if available

- **High-End Systems** (≥32GB RAM, ≥16 CPU cores, GPU):
  - Multiple models loaded
  - Extended context window (8192+)
  - Full GPU acceleration

## System Requirements

### Minimum Requirements

- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 10GB free space
- **OS**: Linux, macOS, or Windows
- **Python**: 3.8+

### Recommended Requirements

- **CPU**: 8+ cores
- **RAM**: 16GB+ (32GB for large models)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (CUDA 11.0+)
- **Storage**: 50GB+ SSD
- **Network**: Stable internet connection for model downloads

## Troubleshooting

### Installation Issues

**Problem**: `ImportError: No module named 'llama_cpp'`
```
Solution: Install llama.cpp
python install_llamacpp.py
```

**Problem**: `CUDA not found` or `GPU not detected`
```
Solution: 
1. Install CUDA toolkit
2. Reinstall llama.cpp with CUDA support
python install_llamacpp.py --cuda
```

**Problem**: `Permission denied` errors
```
Solution: Use virtual environment
python -m venv llama_env
source llama_env/bin/activate  # Linux/macOS
llama_env\Scripts\activate     # Windows
```

### Runtime Issues

**Problem**: Server fails to start
```
Solution:
1. Check port availability: netstat -an | grep 8080
2. Change port in config/config.json
3. Check logs in logs/server.log
```

**Problem**: Model loading fails
```
Solution:
1. Verify model file exists and is not corrupted
2. Check available RAM/VRAM
3. Reduce context window in settings
4. Enable low VRAM mode
```

**Problem**: Slow performance
```
Solution:
1. Enable GPU acceleration if available
2. Reduce context window
3. Increase number of threads
4. Use quantized models
```

### Dashboard Issues

**Problem**: Dashboard not accessible
```
Solution:
1. Verify server is running: python start.py
2. Check firewall settings
3. Try different port: config.json -> server.port
4. Check logs: logs/dashboard.log
```

**Problem**: Dashboard shows errors
```
Solution:
1. Refresh the page
2. Clear browser cache
3. Check browser console for errors
4. Verify FastAPI is installed: pip install fastapi uvicorn
```

## Advanced Configuration

### Performance Tuning

1. **Thread Optimization**
   ```json
   {
     "performance": {
       "num_threads": 8,  // Match CPU core count
       "batch_size": 2,    // Increase for better throughput
       "context_window": 4096
     }
   }
   ```

2. **Memory Management**
   ```json
   {
     "performance": {
       "low_vram": true,          // Enable for GPUs with <4GB VRAM
       "max_loaded_models": 1      // Reduce for systems with <16GB RAM
     },
     "models": {
       "max_cache_gb": 4.0        // Limit cache size
     }
   }
   ```

3. **GPU Configuration**
   ```json
   {
     "gpu": {
       "enabled": true,
       "layers": 43,             // Number of layers to offload to GPU
       "memory_split": 8.0       // GB of VRAM to use
     }
   }
   ```

### Security Configuration

1. **Basic Authentication**
   ```json
   {
     "server": {
       "auth_enabled": true,
       "auth_username": "admin",
       "auth_password": "secure_password"
     }
   }
   ```

2. **API Key Authentication**
   ```json
   {
     "server": {
       "api_key_required": true,
       "api_key": "your_secure_api_key"
     }
   }
   ```

3. **Network Configuration**
   ```json
   {
     "server": {
       "host": "0.0.0.0",        // Listen on all interfaces
       "port": 8080,
       "cors_origins": ["http://localhost:3000"]
     }
   }
   ```

## API Reference

### Server Endpoints

#### Health Check
```
GET /health
```
Returns server health status.

#### Model Loading
```
POST /api/models/load
Content-Type: application/json

{
  "name": "llama-2-7b-chat",
  "path": "/path/to/model.gguf"
}
```

#### Model Unloading
```
POST /api/models/unload
Content-Type: application/json

{
  "name": "llama-2-7b-chat"
}
```

#### Inference
```
POST /api/inference
Content-Type: application/json

{
  "model": "llama-2-7b-chat",
  "prompt": "Hello, how are you?",
  "max_tokens": 256,
  "temperature": 0.7
}
```

### Dashboard API

#### System Status
```
GET /api/system/status
```
Returns current system resource usage.

#### Model List
```
GET /api/models/list
```
Returns list of available models.

#### Settings
```
GET /api/settings/get
POST /api/settings/save
```
Get or update server settings.

## Development

### Project Structure

```
llama_CPP_Server/
├── _server/                 # Core server components
│   ├── backend.py          # Server backend
│   ├── config_manager.py    # Configuration management
│   ├── dashboard.py        # Web dashboard
│   ├── error_handler.py    # Error handling
│   ├── model_downloader.py # Model downloading
│   ├── setup.py           # Interactive setup
│   └── system_optimizer.py # System optimization
├── config/                 # Configuration files
├── logs/                  # Log files
├── models/                 # Model files
└── scripts/               # Utility scripts
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section above
2. Review the logs in the `logs/` directory
3. Open an issue on the project repository
4. Contact the development team

## Changelog

### Version 1.0.0
- Initial release
- Basic server functionality
- Web dashboard
- Model management
- System optimization
- KAREN integration