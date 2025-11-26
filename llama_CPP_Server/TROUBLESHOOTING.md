# Troubleshooting Guide

This guide provides solutions to common issues when using the Llama.cpp Server for KAREN Integration.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Runtime Issues](#runtime-issues)
4. [Model Issues](#model-issues)
5. [Performance Issues](#performance-issues)
6. [Dashboard Issues](#dashboard-issues)
7. [KAREN Integration Issues](#karen-integration-issues)
8. [Advanced Troubleshooting](#advanced-troubleshooting)

## Installation Issues

### Problem: Python version compatibility

**Error**: `SyntaxError` or `ImportError` related to Python version

**Solution**:
1. Check your Python version:
   ```bash
   python --version
   ```
2. Ensure you're using Python 3.8 or higher
3. If not, install a compatible Python version:
   ```bash
   # On Ubuntu/Debian
   sudo apt update
   sudo apt install python3.8 python3.8-venv
   
   # On CentOS/RHEL
   sudo yum install python38
   
   # On macOS (using Homebrew)
   brew install python@3.8
   ```

### Problem: Missing dependencies

**Error**: `ModuleNotFoundError: No module named 'llama_cpp'` or similar

**Solution**:
1. Use the installation wizard:
   ```bash
   python install_llamacpp.py
   ```
2. Or manually install dependencies:
   ```bash
   pip install llama-cpp-python fastapi uvicorn psutil
   ```
3. For GPU support:
   ```bash
   pip install llama-cpp-python --prefer-binary --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118
   ```

### Problem: Permission denied

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
1. Use a virtual environment:
   ```bash
   python -m venv llama_env
   source llama_env/bin/activate  # Linux/macOS
   llama_env\Scripts\activate     # Windows
   ```
2. Or install with user permissions:
   ```bash
   pip install --user llama-cpp-python
   ```

### Problem: CUDA not found

**Error**: `CUDA not found` or `GPU not detected`

**Solution**:
1. Verify CUDA installation:
   ```bash
   nvcc --version
   ```
2. If CUDA is not installed, install it:
   ```bash
   # Follow NVIDIA's official installation guide
   # https://docs.nvidia.com/cuda/cuda-installation-guide-linux/index.html
   ```
3. Reinstall llama-cpp-python with CUDA support:
   ```bash
   pip uninstall llama-cpp-python
   pip install llama-cpp-python --prefer-binary --extra-index-url=https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118
   ```

## Configuration Issues

### Problem: Configuration file not found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'config.json'`

**Solution**:
1. Run the setup wizard:
   ```bash
   python setup.py
   ```
2. Or create a default configuration file:
   ```bash
   mkdir -p config
   echo '{"server": {"host": "localhost", "port": 8080}}' > config/config.json
   ```

### Problem: Invalid configuration

**Error**: `ValidationError` or `ConfigError`

**Solution**:
1. Validate your configuration:
   ```bash
   python -c "from _server.config_manager import ConfigManager; cm = ConfigManager('config/config.json'); print(cm.config)"
   ```
2. Check the configuration schema in `config_manager.py`
3. Fix any invalid values in your configuration file

### Problem: Port already in use

**Error**: `OSError: [Errno 98] Address already in use`

**Solution**:
1. Find the process using the port:
   ```bash
   # Linux/macOS
   lsof -i :8080
   
   # Windows
   netstat -ano | findstr :8080
   ```
2. Kill the process or change the port in your configuration:
   ```json
   {
     "server": {
       "port": 8081
     }
   }
   ```

## Runtime Issues

### Problem: Server fails to start

**Error**: Various startup errors

**Solution**:
1. Check the logs:
   ```bash
   tail -f logs/server.log
   ```
2. Verify all dependencies are installed:
   ```bash
   pip list | grep -E "(llama|fastapi|uvicorn|psutil)"
   ```
3. Test with minimal configuration:
   ```bash
   python -c "from _server.backend import get_server; print('Backend import successful')"
   ```

### Problem: Server crashes or becomes unresponsive

**Error**: Server stops responding or crashes

**Solution**:
1. Check system resources:
   ```bash
   # Linux/macOS
   top
   
   # Windows
   taskmgr
   ```
2. Check logs for error messages:
   ```bash
   tail -n 100 logs/server.log
   ```
3. Reduce resource usage in configuration:
   ```json
   {
     "performance": {
       "num_threads": 4,
       "low_vram": true,
       "max_loaded_models": 1
     }
   }
   ```

### Problem: Memory issues

**Error**: `MemoryError` or `CUDA out of memory`

**Solution**:
1. Reduce context window:
   ```json
   {
     "performance": {
       "context_window": 2048
     }
   }
   ```
2. Enable low VRAM mode:
   ```json
   {
     "performance": {
       "low_vram": true
     }
   }
   ```
3. Reduce number of loaded models:
   ```json
   {
     "models": {
       "max_loaded_models": 1
     }
   }
   ```

## Model Issues

### Problem: Model not found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'model.gguf'`

**Solution**:
1. Verify model file exists:
   ```bash
   ls -la models/
   ```
2. Download the model:
   ```bash
   python model_downloader.py
   ```
3. Check model path in configuration:
   ```json
   {
     "models": {
       "directory": "models"
     }
   }
   ```

### Problem: Model format not supported

**Error**: `Invalid model format` or `Unsupported file type`

**Solution**:
1. Verify model is in GGUF format:
   ```bash
   file models/your_model.gguf
   ```
2. Convert model to GGUF format if needed:
   ```bash
   # Use llama.cpp conversion tools
   python convert.py your_model.bin --outtype f16 --outfile your_model.gguf
   ```

### Problem: Model loading fails

**Error**: Various model loading errors

**Solution**:
1. Check available memory:
   ```bash
   # Linux
   free -h
   
   # Windows
   wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list
   
   # GPU memory (if applicable)
   nvidia-smi
   ```
2. Reduce model size or use quantized version
3. Enable low VRAM mode in configuration

## Performance Issues

### Problem: Slow inference

**Symptom**: Model responses take too long

**Solution**:
1. Enable GPU acceleration if available:
   ```json
   {
     "gpu": {
       "enabled": true
     }
   }
   ```
2. Increase number of threads:
   ```json
   {
     "performance": {
       "num_threads": 8
     }
   }
   ```
3. Reduce context window:
   ```json
   {
     "performance": {
       "context_window": 2048
     }
   }
   ```
4. Use quantized models

### Problem: High memory usage

**Symptom**: System runs out of memory

**Solution**:
1. Limit cache size:
   ```json
   {
     "models": {
       "max_cache_gb": 4.0
     }
   }
   ```
2. Reduce number of loaded models:
   ```json
   {
     "models": {
       "max_loaded_models": 1
     }
   }
   ```
3. Enable low VRAM mode:
   ```json
   {
     "performance": {
       "low_vram": true
     }
   }
   ```

### Problem: High CPU usage

**Symptom**: CPU usage is consistently high

**Solution**:
1. Adjust number of threads:
   ```json
   {
     "performance": {
       "num_threads": 4
     }
   }
   ```
2. Enable GPU acceleration to offload work from CPU
3. Reduce batch size:
   ```json
   {
     "performance": {
       "batch_size": 1
     }
   }
   ```

## Dashboard Issues

### Problem: Dashboard not accessible

**Symptom**: Cannot access web dashboard at `http://localhost:8081`

**Solution**:
1. Verify server is running:
   ```bash
   ps aux | grep python
   ```
2. Check dashboard logs:
   ```bash
   tail -f logs/dashboard.log
   ```
3. Verify port is not blocked by firewall:
   ```bash
   # Linux
   sudo ufw status
   
   # Windows
   netsh advfirewall show allprofiles
   ```
4. Try accessing from different browser or in private mode

### Problem: Dashboard shows errors

**Symptom**: Dashboard displays error messages

**Solution**:
1. Check browser console for errors:
   - Chrome/Edge: F12 → Console tab
   - Firefox: F12 → Web Console
2. Clear browser cache and cookies
3. Check FastAPI installation:
   ```bash
   pip install fastapi uvicorn jinja2
   ```
4. Restart the dashboard server

### Problem: Dashboard features not working

**Symptom**: Some dashboard features don't work

**Solution**:
1. Verify JavaScript is enabled in browser
2. Check browser console for JavaScript errors
3. Refresh the page
4. Try a different browser

## KAREN Integration Issues

### Problem: KAREN cannot connect to server

**Error**: Connection refused or timeout errors

**Solution**:
1. Verify server is running:
   ```bash
   curl http://localhost:8080/health
   ```
2. Check KAREN configuration:
   ```json
   {
     "llm_server": {
       "url": "http://localhost:8080",
       "api_key": "your_api_key"
     }
   }
   ```
3. Verify network connectivity between KAREN and server
4. Check firewall settings

### Problem: Authentication issues

**Error**: `401 Unauthorized` or `403 Forbidden`

**Solution**:
1. Verify API key is correct:
   ```json
   {
     "server": {
       "api_key": "your_api_key"
     }
   }
   ```
2. Check KAREN configuration matches server API key
3. Verify authentication is enabled:
   ```json
   {
     "server": {
       "auth_enabled": true
     }
   }
   ```

### Problem: Incompatible API endpoints

**Error**: `404 Not Found` or `400 Bad Request`

**Solution**:
1. Verify API endpoints match KAREN expectations
2. Check API documentation in `README.md`
3. Update KAREN configuration to match server API

## Advanced Troubleshooting

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in configuration:
```json
{
  "server": {
    "log_level": "DEBUG"
  }
}
```

### Performance Profiling

Profile performance bottlenecks:

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Memory Debugging

Debug memory usage:

```python
import tracemalloc

tracemalloc.start()

# Your code here

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### System Information

Gather system information for debugging:

```bash
# System information
uname -a

# CPU information
lscpu

# Memory information
free -h

# Disk information
df -h

# GPU information (if applicable)
nvidia-smi

# Python information
python --version
pip list
```

### Getting Help

If you're still having issues:

1. Check the logs in the `logs/` directory
2. Review this troubleshooting guide
3. Search existing issues on the project repository
4. Create a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System information (OS, Python version, etc.)
   - Relevant log files
   - Configuration files (with sensitive information removed)

## Common Error Messages

| Error Message | Possible Cause | Solution |
|--------------|---------------|----------|
| `ImportError: No module named 'llama_cpp'` | Missing dependency | Install llama-cpp-python |
| `CUDA not found` | CUDA not installed or not in PATH | Install CUDA or update PATH |
| `Permission denied` | File permissions issue | Use virtual environment or fix permissions |
| `Address already in use` | Port already in use | Change port or kill process using the port |
| `MemoryError` | Insufficient memory | Reduce context window or enable low VRAM mode |
| `FileNotFoundError` | Model file not found | Download model or check path |
| `401 Unauthorized` | Authentication issue | Check API key or authentication settings |
| `404 Not Found` | API endpoint not found | Verify API endpoint or update KAREN configuration |