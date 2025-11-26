# Llama.cpp Server Implementation Plan

## Overview
This document outlines the implementation plan for an easy-to-setup/use/launch llama.cpp local server optimized for performance and tailored for KAREN.

## Architecture

### Two-Tier System Architecture

```
llama_CPP_Server/          ← Standalone llama.cpp server
├── runServer.py          ← Main server entry point
├── setup.py              ← Installation and setup script
├── karenOptimization.py  ← KAREN-specific optimizations
├── performanceEngine.py   ← Performance optimization engine
└── _server/              ← Server implementation directory
    ├── __init__.py
    ├── server.py          ← Core server implementation
    ├── model_manager.py   ← Dynamic model loading/management
    ├── api_endpoints.py   ← REST API endpoints
    ├── config.py          ← Configuration management
    ├── health_monitor.py  ← Health monitoring
    └── utils.py           ← Utility functions

src/extensions/           ← KAREN extension system
└── llamacpp/             ← Llama.cpp integration extension
    ├── extension_manifest.json
    ├── handler.py
    └── prompt.txt
```

## Implementation Details

### 1. Core Server (llama_CPP_Server/runServer.py)

```python
#!/usr/bin/env python3
"""
Llama.cpp Server for KAREN
A high-performance, easy-to-use local server for GGUF models with KAREN integration.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
from pathlib import Path

# Add the _server directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_server'))

from server import LlamaServer
from config import ServerConfig
from model_manager import ModelManager
from health_monitor import HealthMonitor
from performance_engine import PerformanceEngine
from karen_optimization import KarenOptimization

def main():
    """Main entry point for the llama.cpp server"""
    parser = argparse.ArgumentParser(description='Llama.cpp Server for KAREN')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to configuration file')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port to bind to')
    parser.add_argument('--models-dir', type=str, default='../models/llama-cpp',
                        help='Directory containing GGUF models')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = ServerConfig(args.config)
    
    # Initialize components
    model_manager = ModelManager(args.models_dir, config)
    health_monitor = HealthMonitor()
    performance_engine = PerformanceEngine(config)
    karen_optimization = KarenOptimization(config)
    
    # Create and start server
    server = LlamaServer(
        host=args.host,
        port=args.port,
        model_manager=model_manager,
        health_monitor=health_monitor,
        performance_engine=performance_engine,
        karen_optimization=karen_optimization,
        config=config
    )
    
    logger.info(f"Starting Llama.cpp Server on {args.host}:{args.port}")
    logger.info(f"Models directory: {args.models_dir}")
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Server Implementation (llama_CPP_Server/_server/server.py)

```python
"""
Core server implementation for llama.cpp server
"""

import asyncio
import json
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from model_manager import ModelManager
from health_monitor import HealthMonitor
from performance_engine import PerformanceEngine
from karen_optimization import KarenOptimization
from config import ServerConfig
from api_endpoints import create_api_router

logger = logging.getLogger(__name__)

class LlamaServer:
    """Main server class for llama.cpp server"""
    
    def __init__(self, host, port, model_manager, health_monitor, 
                 performance_engine, karen_optimization, config):
        self.host = host
        self.port = port
        self.model_manager = model_manager
        self.health_monitor = health_monitor
        self.performance_engine = performance_engine
        self.karen_optimization = karen_optimization
        self.config = config
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Llama.cpp Server for KAREN",
            description="High-performance local server for GGUF models",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Set up lifespan
        self.app.router.lifespan_context = self.lifespan
        
        # Include API routes
        self.app.include_router(create_api_router(self))
    
    @asynccontextmanager
    async def lifespan(self, app):
        """Manage server lifecycle"""
        # Startup
        logger.info("Starting up Llama.cpp Server...")
        
        # Initialize model manager
        await self.model_manager.initialize()
        
        # Start health monitoring
        await self.health_monitor.start()
        
        # Initialize performance engine
        await self.performance_engine.initialize()
        
        # Initialize KAREN optimizations
        await self.karen_optimization.initialize()
        
        logger.info("Llama.cpp Server started successfully")
        
        yield
        
        # Shutdown
        logger.info("Shutting down Llama.cpp Server...")
        
        # Stop health monitoring
        await self.health_monitor.stop()
        
        # Clean up model manager
        await self.model_manager.cleanup()
        
        logger.info("Llama.cpp Server shutdown complete")
    
    def run(self):
        """Run the server"""
        import uvicorn
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level=self.config.log_level.lower()
        )
```

### 3. Model Manager (llama_CPP_Server/_server/model_manager.py)

```python
"""
Dynamic model loading and management for llama.cpp server
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages loading, unloading, and switching of GGUF models"""
    
    def __init__(self, models_dir: str, config):
        self.models_dir = Path(models_dir)
        self.config = config
        self.loaded_models: Dict[str, Any] = {}
        self.available_models: List[Dict[str, Any]] = []
        self.current_model: Optional[str] = None
        
    async def initialize(self):
        """Initialize the model manager"""
        logger.info("Initializing Model Manager...")
        
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan for available models
        await self.scan_models()
        
        logger.info(f"Found {len(self.available_models)} available models")
        
    async def scan_models(self):
        """Scan models directory for GGUF files"""
        self.available_models = []
        
        async for file_path in self._scan_directory(self.models_dir):
            if file_path.suffix.lower() == '.gguf':
                model_info = {
                    "id": file_path.stem,
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                }
                self.available_models.append(model_info)
        
        logger.info(f"Scanned {len(self.available_models)} GGUF models")
        
    async def _scan_directory(self, directory: Path):
        """Recursively scan directory for files"""
        for entry in directory.iterdir():
            if entry.is_file():
                yield entry
            elif entry.is_dir():
                async for sub_entry in self._scan_directory(entry):
                    yield sub_entry
    
    async def load_model(self, model_id: str):
        """Load a model by ID"""
        if model_id in self.loaded_models:
            logger.info(f"Model {model_id} already loaded")
            return True
        
        # Find model in available models
        model_info = next((m for m in self.available_models if m["id"] == model_id), None)
        if not model_info:
            logger.error(f"Model {model_id} not found")
            return False
        
        # Load model using llama.cpp
        try:
            # This would be implemented with llama.cpp bindings
            # For now, just store the model info
            self.loaded_models[model_id] = model_info
            self.current_model = model_id
            
            logger.info(f"Successfully loaded model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def unload_model(self, model_id: str):
        """Unload a model by ID"""
        if model_id not in self.loaded_models:
            logger.warning(f"Model {model_id} not loaded")
            return True
        
        try:
            # Unload model using llama.cpp
            del self.loaded_models[model_id]
            
            if self.current_model == model_id:
                self.current_model = None
            
            logger.info(f"Successfully unloaded model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            return False
    
    async def get_loaded_models(self) -> List[Dict[str, Any]]:
        """Get list of loaded models"""
        return list(self.loaded_models.values())
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return self.available_models
    
    async def get_current_model(self) -> Optional[Dict[str, Any]]:
        """Get currently active model"""
        if not self.current_model:
            return None
        
        return self.loaded_models.get(self.current_model)
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up Model Manager...")
        
        # Unload all models
        for model_id in list(self.loaded_models.keys()):
            await self.unload_model(model_id)
        
        logger.info("Model Manager cleanup complete")
```

### 4. Performance Engine (llama_CPP_Server/_server/performance_engine.py)

```python
"""
Performance optimization engine for llama.cpp server
"""

import os
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class PerformanceEngine:
    """Manages performance optimizations for the server"""
    
    def __init__(self, config):
        self.config = config
        self.metrics = {
            "memory_usage": 0,
            "cpu_usage": 0,
            "inference_times": [],
            "model_load_times": []
        }
        
    async def initialize(self):
        """Initialize the performance engine"""
        logger.info("Initializing Performance Engine...")
        
        # Set up performance monitoring
        asyncio.create_task(self._monitor_performance())
        
        logger.info("Performance Engine initialized")
    
    async def _monitor_performance(self):
        """Monitor system performance metrics"""
        while True:
            try:
                # Get memory usage
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                self.metrics["memory_usage"] = memory_info.rss / 1024 / 1024  # MB
                
                # Get CPU usage
                self.metrics["cpu_usage"] = process.cpu_percent()
                
                # Log metrics
                logger.debug(f"Performance metrics: {self.metrics}")
                
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error monitoring performance: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def optimize_for_memory(self):
        """Apply memory optimizations"""
        logger.info("Applying memory optimizations...")
        
        # This would implement memory-specific optimizations
        # For example:
        # - Adjust context window size
        # - Enable memory mapping
        # - Optimize batch sizes
        
        logger.info("Memory optimizations applied")
    
    async def optimize_for_speed(self):
        """Apply speed optimizations"""
        logger.info("Applying speed optimizations...")
        
        # This would implement speed-specific optimizations
        # For example:
        # - Enable GPU acceleration if available
        # - Optimize thread count
        # - Enable KV caching
        
        logger.info("Speed optimizations applied")
    
    async def optimize_for_loading(self):
        """Apply model loading optimizations"""
        logger.info("Applying loading optimizations...")
        
        # This would implement loading-specific optimizations
        # For example:
        # - Enable model caching
        # - Preload commonly used models
        # - Optimize model loading parameters
        
        logger.info("Loading optimizations applied")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    async def record_inference_time(self, time_ms: float):
        """Record inference time metric"""
        self.metrics["inference_times"].append({
            "time": time.time(),
            "duration_ms": time_ms
        })
        
        # Keep only last 100 inference times
        if len(self.metrics["inference_times"]) > 100:
            self.metrics["inference_times"] = self.metrics["inference_times"][-100:]
    
    async def record_model_load_time(self, model_id: str, time_ms: float):
        """Record model loading time metric"""
        self.metrics["model_load_times"].append({
            "time": time.time(),
            "model_id": model_id,
            "duration_ms": time_ms
        })
        
        # Keep only last 20 model load times
        if len(self.metrics["model_load_times"]) > 20:
            self.metrics["model_load_times"] = self.metrics["model_load_times"][-20:]
```

### 5. KAREN Optimizations (llama_CPP_Server/_server/karen_optimization.py)

```python
"""
KAREN-specific optimizations for llama.cpp server
"""

import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class KarenOptimization:
    """Implements KAREN-specific optimizations"""
    
    def __init__(self, config):
        self.config = config
        self.karen_config = {}
        
    async def initialize(self):
        """Initialize KAREN optimizations"""
        logger.info("Initializing KAREN Optimizations...")
        
        # Load KAREN-specific configuration
        await self._load_karen_config()
        
        # Apply KAREN-specific optimizations
        await self._apply_karen_optimizations()
        
        logger.info("KAREN Optimizations initialized")
    
    async def _load_karen_config(self):
        """Load KAREN-specific configuration"""
        try:
            # This would load KAREN-specific configuration
            # For now, just use default values
            self.karen_config = {
                "context_window": 4096,
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9,
                "repetition_penalty": 1.1,
                "karen_specific_params": {
                    "enable_context_awareness": True,
                    "enable_memory_optimization": True,
                    "enable_karen_prompt_template": True
                }
            }
            
            logger.info("KAREN configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load KAREN configuration: {e}")
            self.karen_config = {}
    
    async def _apply_karen_optimizations(self):
        """Apply KAREN-specific optimizations"""
        logger.info("Applying KAREN-specific optimizations...")
        
        # Apply KAREN-specific optimizations
        # For example:
        # - Optimize for KAREN's prompt format
        # - Enable context awareness features
        # - Configure memory optimization for KAREN's use case
        
        logger.info("KAREN-specific optimizations applied")
    
    async def get_karen_config(self) -> Dict[str, Any]:
        """Get KAREN-specific configuration"""
        return self.karen_config.copy()
    
    async def optimize_prompt(self, prompt: str) -> str:
        """Optimize prompt for KAREN"""
        if not self.karen_config.get("karen_specific_params", {}).get("enable_karen_prompt_template", False):
            return prompt
        
        # Apply KAREN-specific prompt formatting
        optimized_prompt = f"""KAREN System Prompt:
You are KAREN, an advanced AI assistant with multi-modal capabilities.

User Query:
{prompt}

Please provide a helpful, accurate, and contextually appropriate response."""
        
        return optimized_prompt
    
    async def optimize_inference_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize inference parameters for KAREN"""
        # Apply KAREN-specific parameter optimizations
        optimized_params = params.copy()
        
        # Override with KAREN-specific values
        if "temperature" not in optimized_params:
            optimized_params["temperature"] = self.karen_config.get("temperature", 0.7)
        
        if "max_tokens" not in optimized_params:
            optimized_params["max_tokens"] = self.karen_config.get("max_tokens", 2048)
        
        if "top_p" not in optimized_params:
            optimized_params["top_p"] = self.karen_config.get("top_p", 0.9)
        
        return optimized_params
```

### 6. Configuration Management (llama_CPP_Server/_server/config.py)

```python
"""
Configuration management for llama.cpp server
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ServerConfig:
    """Manages server configuration"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "log_level": "INFO"
            },
            "models": {
                "directory": "../models/llama-cpp",
                "default_model": None,
                "auto_load_default": True,
                "max_loaded_models": 3
            },
            "performance": {
                "optimize_for": "balanced",  # "memory", "speed", "loading", "balanced"
                "max_memory_mb": 4096,
                "enable_gpu": True,
                "num_threads": 4
            },
            "karen": {
                "integration_enabled": True,
                "optimize_for_karen": True,
                "karen_endpoint": "http://localhost:8000",
                "auth_token": None
            },
            "api": {
                "enable_cors": True,
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 60
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge with default config
                config = self._merge_configs(default_config, user_config)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                logger.info("Using default configuration")
                return default_config
        else:
            logger.info("No configuration file found, using defaults")
            return default_config
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with default configuration"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
```

### 7. Health Monitor (llama_CPP_Server/_server/health_monitor.py)

```python
"""
Health monitoring for llama.cpp server
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitors the health of the server and its components"""
    
    def __init__(self):
        self.health_status = {
            "server": "healthy",
            "models": "healthy",
            "performance": "healthy",
            "karen_integration": "healthy"
        }
        self.health_checks = {}
        self.last_check = None
        
    async def start(self):
        """Start health monitoring"""
        logger.info("Starting Health Monitor...")
        
        # Schedule periodic health checks
        asyncio.create_task(self._periodic_health_check())
        
        logger.info("Health Monitor started")
    
    async def stop(self):
        """Stop health monitoring"""
        logger.info("Stopping Health Monitor...")
        
        # Clean up resources
        self.health_checks.clear()
        
        logger.info("Health Monitor stopped")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks"""
        while True:
            try:
                await self._check_all_components()
                self.last_check = datetime.now()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_all_components(self):
        """Check health of all components"""
        # Check server health
        self.health_status["server"] = await self._check_server_health()
        
        # Check models health
        self.health_status["models"] = await self._check_models_health()
        
        # Check performance health
        self.health_status["performance"] = await self._check_performance_health()
        
        # Check KAREN integration health
        self.health_status["karen_integration"] = await self._check_karen_health()
        
        # Determine overall health
        overall_health = "healthy"
        for component, status in self.health_status.items():
            if status == "unhealthy":
                overall_health = "unhealthy"
                break
            elif status == "degraded" and overall_health != "unhealthy":
                overall_health = "degraded"
        
        logger.debug(f"Health status: {self.health_status}, Overall: {overall_health}")
    
    async def _check_server_health(self) -> str:
        """Check server health"""
        try:
            # Check if server is responsive
            # This would implement actual server health checks
            return "healthy"
        except Exception as e:
            logger.error(f"Server health check failed: {e}")
            return "unhealthy"
    
    async def _check_models_health(self) -> str:
        """Check models health"""
        try:
            # Check if models are loaded and responsive
            # This would implement actual model health checks
            return "healthy"
        except Exception as e:
            logger.error(f"Models health check failed: {e}")
            return "unhealthy"
    
    async def _check_performance_health(self) -> str:
        """Check performance health"""
        try:
            # Check performance metrics
            # This would implement actual performance health checks
            return "healthy"
        except Exception as e:
            logger.error(f"Performance health check failed: {e}")
            return "unhealthy"
    
    async def _check_karen_health(self) -> str:
        """Check KAREN integration health"""
        try:
            # Check KAREN integration
            # This would implement actual KAREN health checks
            return "healthy"
        except Exception as e:
            logger.error(f"KAREN health check failed: {e}")
            return "unhealthy"
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        return {
            "status": self.health_status,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "checks": self.health_checks
        }
```

### 8. API Endpoints (llama_CPP_Server/_server/api_endpoints.py)

```python
"""
API endpoints for llama.cpp server
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class ModelLoadRequest(BaseModel):
    model_id: str = Field(..., description="ID of the model to load")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Model loading parameters")

class InferenceRequest(BaseModel):
    prompt: str = Field(..., description="Input prompt for inference")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Inference parameters")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")

class InferenceResponse(BaseModel):
    response: str = Field(..., description="Generated response")
    model_id: str = Field(..., description="ID of the model used")
    parameters: Dict[str, Any] = Field(..., description="Parameters used for inference")
    timing: Dict[str, float] = Field(..., description="Timing information")

def create_api_router(server):
    """Create API router for the server"""
    router = APIRouter()
    
    @router.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Llama.cpp Server for KAREN",
            "version": "1.0.0",
            "status": "running"
        }
    
    @router.get("/health")
    async def health():
        """Health check endpoint"""
        return await server.health_monitor.get_health_status()
    
    @router.get("/models")
    async def list_models():
        """List available models"""
        return {
            "available": await server.model_manager.get_available_models(),
            "loaded": await server.model_manager.get_loaded_models(),
            "current": await server.model_manager.get_current_model()
        }
    
    @router.post("/models/load")
    async def load_model(request: ModelLoadRequest, background_tasks: BackgroundTasks):
        """Load a model"""
        success = await server.model_manager.load_model(request.model_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to load model {request.model_id}")
        
        return {"status": "success", "model_id": request.model_id}
    
    @router.post("/models/unload/{model_id}")
    async def unload_model(model_id: str):
        """Unload a model"""
        success = await server.model_manager.unload_model(model_id)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to unload model {model_id}")
        
        return {"status": "success", "model_id": model_id}
    
    @router.post("/inference")
    async def inference(request: InferenceRequest):
        """Perform inference"""
        # Check if a model is loaded
        current_model = await server.model_manager.get_current_model()
        if not current_model:
            raise HTTPException(status_code=400, detail="No model loaded")
        
        # Optimize prompt for KAREN
        optimized_prompt = await server.karen_optimization.optimize_prompt(request.prompt)
        
        # Optimize inference parameters
        optimized_params = await server.karen_optimization.optimize_inference_params(request.parameters)
        
        # Record start time
        import time
        start_time = time.time()
        
        # Perform inference (this would be implemented with llama.cpp)
        try:
            # Placeholder for actual inference
            response = f"Response to: {optimized_prompt}"
            
            # Calculate timing
            end_time = time.time()
            inference_time = (end_time - start_time) * 1000  # Convert to ms
            
            # Record inference time
            await server.performance_engine.record_inference_time(inference_time)
            
            return InferenceResponse(
                response=response,
                model_id=current_model["id"],
                parameters=optimized_params,
                timing={
                    "inference_time_ms": inference_time,
                    "total_time_ms": inference_time
                }
            )
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise HTTPException(status_code=500, detail="Inference failed")
    
    @router.get("/performance")
    async def performance_metrics():
        """Get performance metrics"""
        return await server.performance_engine.get_metrics()
    
    @router.get("/karen/config")
    async def karen_config():
        """Get KAREN configuration"""
        return await server.karen_optimization.get_karen_config()
    
    return router
```

### 9. KAREN Extension (src/extensions/llamacpp/extension_manifest.json)

```json
{
  "id": "kari.llamacpp_integration",
  "name": "Llama.cpp Integration",
  "version": "1.0.0",
  "entrypoint": "handler:LlamaCppExtension",
  "description": "Integrates KAREN with the local llama.cpp server for high-performance local inference.",
  "hook_points": [
    "pre_llm_prompt",
    "post_llm_result"
  ],
  "prompt_files": {
    "system": "prompt.txt"
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "server_url": {
        "type": "string",
        "default": "http://localhost:8080",
        "description": "URL of the llama.cpp server"
      },
      "default_model": {
        "type": "string",
        "default": "Phi-3-mini-4k-instruct-q4",
        "description": "Default model to use"
      },
      "enable_local_fallback": {
        "type": "boolean",
        "default": true,
        "description": "Enable fallback to local models when remote services are unavailable"
      }
    }
  },
  "permissions": {
    "memory_read": true,
    "memory_write": false,
    "tools": ["local_llm"]
  },
  "rbac": {
    "allowed_roles": ["system", "admin", "user"],
    "default_enabled": true
  }
}
```

### 10. KAREN Extension Handler (src/extensions/llamacpp/handler.py)

```python
"""
KAREN extension handler for llama.cpp integration
"""

import logging
import aiohttp
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LlamaCppExtension:
    """KAREN extension for llama.cpp integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_url = config.get("server_url", "http://localhost:8080")
        self.default_model = config.get("default_model", "Phi-3-mini-4k-instruct-q4")
        self.enable_local_fallback = config.get("enable_local_fallback", True)
        self.session = None
        
    async def initialize(self):
        """Initialize the extension"""
        logger.info("Initializing Llama.cpp Extension...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession()
        
        # Check server health
        await self._check_server_health()
        
        logger.info("Llama.cpp Extension initialized")
    
    async def _check_server_health(self):
        """Check if the llama.cpp server is healthy"""
        try:
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"Llama.cpp server health: {health_data}")
                    return True
                else:
                    logger.warning(f"Llama.cpp server returned status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to check llama.cpp server health: {e}")
            return False
    
    async def pre_llm_prompt(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-process prompt before sending to LLM"""
        try:
            # Check if we should use local model
            if not self.enable_local_fallback:
                return context
            
            # Check if local model is available
            if not await self._check_server_health():
                logger.warning("Llama.cpp server not available, skipping local processing")
                return context
            
            # Get available models
            async with self.session.get(f"{self.server_url}/models") as response:
                if response.status == 200:
                    models_data = await response.json()
                    
                    # Check if default model is loaded
                    current_model = models_data.get("current")
                    if not current_model or current_model.get("id") != self.default_model:
                        # Load default model
                        load_data = {"model_id": self.default_model}
                        async with self.session.post(f"{self.server_url}/models/load", json=load_data) as load_response:
                            if load_response.status != 200:
                                logger.warning(f"Failed to load default model: {await load_response.text()}")
                                return context
                    
                    # Optimize prompt for local model
                    prompt = context.get("prompt", "")
                    inference_data = {
                        "prompt": prompt,
                        "parameters": {
                            "temperature": 0.7,
                            "max_tokens": 2048
                        }
                    }
                    
                    # Get inference from local model
                    async with self.session.post(f"{self.server_url}/inference", json=inference_data) as inference_response:
                        if inference_response.status == 200:
                            inference_result = await inference_response.json()
                            
                            # Add local inference result to context
                            context["local_inference"] = {
                                "response": inference_result.get("response", ""),
                                "model": inference_result.get("model_id", ""),
                                "timing": inference_result.get("timing", {})
                            }
                            
                            logger.info("Local inference completed successfully")
                        else:
                            logger.warning(f"Local inference failed: {await inference_response.text()}")
                else:
                    logger.warning(f"Failed to get models: {await response.text()}")
            
            return context
        except Exception as e:
            logger.error(f"Error in pre_llm_prompt: {e}")
            return context
    
    async def post_llm_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process LLM result"""
        try:
            # Check if we have local inference results
            local_inference = context.get("local_inference")
            if local_inference:
                # Compare local and remote results
                # This could implement various comparison and combination strategies
                
                # For now, just add metadata
                context["metadata"] = {
                    "local_inference_used": True,
                    "local_model": local_inference.get("model", ""),
                    "local_timing": local_inference.get("timing", {})
                }
            
            return context
        except Exception as e:
            logger.error(f"Error in post_llm_result: {e}")
            return context
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up Llama.cpp Extension...")
        
        if self.session:
            await self.session.close()
        
        logger.info("Llama.cpp Extension cleanup complete")
```

### 11. KAREN Extension Prompt (src/extensions/llamacpp/prompt.txt)

```
You are KAREN, an advanced AI assistant with multi-modal capabilities.

When using local models through the llama.cpp integration, please:

1. Provide accurate, helpful, and contextually appropriate responses
2. Leverage your local knowledge and capabilities
3. Be aware of your limitations as a local model
4. Maintain a helpful and professional tone
5. If you cannot answer a question, be honest about your limitations

Remember that you are running locally on the user's system, which provides:
- Faster response times
- Enhanced privacy
- Offline capability
- Integration with the user's local data and context

Please assist the user to the best of your abilities while respecting these constraints.
```

## Production-Quality Wiring Plan

1) **Core hardening**
   - Enforce input validation and schema for all endpoints (requests, configs); standardize JSON errors.
   - Add authN/authZ hooks (bearer token or mTLS) and rate limiting; document how to disable for trusted LAN.
   - Make model lifecycle idempotent (double load/unload safe) and add concurrency guards on load/swap.
   - Add process signal handling (SIGTERM/SIGINT) for graceful shutdown; drain in-flight requests.

2) **Performance and capacity**
   - Implement real llama.cpp bindings (llama-cpp-python or HTTP server) with pluggable backends (CPU, GPU, CUDA/Metal).
   - Expose tunables (threads, batch, context, rope-scaling, mmap, low-vram) via config/env; per-model overrides.
   - Add warm-start and LRU model cache with size limits; preload default model optionally.
   - Add structured perf metrics: load time, tokens/s, cache hit/miss, queue depth, memory and VRAM.
   - Provide load-shedding/backpressure when queue exceeds thresholds; return 429 with retry-after.

3) **Reliability and observability**
   - Add Prometheus/OpenTelemetry metrics + tracing spans around model load and inference.
   - Centralize logging to JSON with request ids, model ids, timings, and health states; log rotation guidance.
   - Expand health check to include downstreams (GPU availability, disk space, model presence, KAREN endpoint reachability) and readiness vs liveness.
   - Add self-test endpoint that runs a tiny inference against a fixture prompt for smoke checks.

4) **Security and compliance**
   - Support TLS termination (env-configurable cert/key paths) or document fronting with reverse proxy.
   - Secrets management: never log tokens; allow env vars for auth tokens; mask sensitive fields in logs.
   - Permission model for extensions: allowlist which hooks can call the server; enforce CORS allowlist instead of "*".

5) **Packaging and deployment**
   - Provide Dockerfile (CPU) and variant for GPU (CUDA, ROCm) with build args; multi-stage to keep images small.
   - Add start scripts for systemd/docker-compose; include healthcheck and resource limits examples.
   - Document model directory layout, volume mounts, and example .env.
   - Add versioning and changelog; embed git/semantic version into / endpoint.

6) **Testing strategy**
   - Unit tests for config merge, model manager lifecycle, performance engine metrics, health monitor states.
   - Integration tests spinning up the API with a stub llama backend; cover load/unload/inference and auth paths.
   - Contract tests for the KAREN extension (pre/post hooks) with mocked server responses.
   - Load tests for concurrency (p50/p95 latency, saturation behavior) and soak tests for leak detection.

7) **Rollout and ops**
   - CI: lint/typecheck/tests, build Docker images, publish SBOM; fail on unpinned deps drift.
   - Blue/green or canary guidance; readiness gates on health + self-test.
   - Runbook: common errors (OOM, GPU not found, model missing), remediation steps, log/metric dashboards.
   - Backup/restore guidance for configs and model cache; rotate tokens/certs playbook.

7. **Set up proper logging and error handling**
   - Add structured logging
   - Add error handling and recovery
   - Add debugging support

8. **Add documentation and setup instructions**
   - Create setup guide
   - Add API documentation
   - Add configuration examples

9. **Test the integration**
   - Test server functionality
   - Test KAREN integration
   - Test performance optimizations

## Next Steps

The next step is to begin implementing the core server functionality, starting with the basic server structure and model management.
