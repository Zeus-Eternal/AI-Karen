"""
Main Server for Llama.cpp Server

This module provides the main FastAPI server that integrates all components:
- Model management
- Security hardening
- Performance monitoring
- Backup and recovery
- Dashboard
"""

import os
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Import our modules
from .backend import LocalLlamaBackend, BackendError
from .security_manager import SecurityManager, Permission, UserRole
from .security_routes import router as security_router
from .config import ServerConfig
from .config_manager import ConfigManager
from .system_optimizer import SystemOptimizer, get_system_optimizer
from .performance_benchmark import PerformanceBenchmark
from .backup_manager import BackupManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables
backend: Optional[LocalLlamaBackend] = None
security_manager: Optional[SecurityManager] = None
config_manager: Optional[ConfigManager] = None
system_optimizer: Optional[SystemOptimizer] = None
performance_benchmark: Optional[PerformanceBenchmark] = None
backup_manager: Optional[BackupManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Llama.cpp Server")
    
    # Initialize global variables
    global backend, security_manager, config_manager, system_optimizer, performance_benchmark, backup_manager
    
    # Initialize configuration manager
    config_path = os.environ.get("LLAMA_CPP_CONFIG_PATH", "config.json")
    config_manager = ConfigManager(config_path)
    
    # Initialize security manager
    security_manager = SecurityManager(config_path)
    
    # Initialize system optimizer
    system_optimizer = get_system_optimizer()
    
    # Initialize performance benchmark
    performance_benchmark = PerformanceBenchmark(config_path)
    
    # Initialize backup manager
    backup_manager = BackupManager(config_path)
    
    # Initialize backend
    model_path = Path(config_manager.get("model.path", "models/llama-2-7b.Q4_K_M.gguf"))
    if not model_path.exists():
        logger.warning(f"Model path {model_path} does not exist, using stub backend")
    
    threads = config_manager.get("server.threads", 4)
    low_vram = config_manager.get("server.low_vram", False)
    n_ctx = config_manager.get("server.n_ctx", 4096)
    
    backend = LocalLlamaBackend(model_path, threads, low_vram, n_ctx)
    
    # Load model
    try:
        await backend.load()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Llama.cpp Server")
    
    # Unload model
    if backend and backend.loaded:
        await backend.unload()

# Create FastAPI app
app = FastAPI(
    title="Llama.cpp Server",
    description="A premium llama.cpp server with extensive features",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly in production
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with security information"""
    start_time = time.time()
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Get user agent
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Get authentication info
    auth_header = request.headers.get("authorization")
    api_key_header = request.headers.get("x-api-key")
    
    # Process request
    response = await call_next(request)
    
    # Calculate request time
    process_time = time.time() - start_time
    
    # Log request
    logger.info(
        f"{client_ip} - \"{request.method} {request.url}\" {response.status_code} {process_time:.4f}s"
    )
    
    # Log security event if security manager is available
    if security_manager:
        security_manager.log_security_event(
            "http_request",
            {
                "method": request.method,
                "path": str(request.url.path),
                "query": str(request.url.query),
                "status_code": response.status_code,
                "process_time": process_time,
                "user_agent": user_agent,
                "has_auth_header": auth_header is not None,
                "has_api_key": api_key_header is not None
            },
            ip=client_ip
        )
    
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Log security event if security manager is available
    if security_manager:
        security_manager.log_security_event(
            "unhandled_exception",
            {
                "method": request.method,
                "path": str(request.url.path),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc)
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Backend error handler
@app.exception_handler(BackendError)
async def backend_error_handler(request: Request, exc: BackendError):
    """Handle backend errors"""
    logger.error(f"Backend error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include security routes
app.include_router(security_router)

# API routes
@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "message": "Llama.cpp Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not backend:
        return {"status": "error", "message": "Backend not initialized"}
    
    if not backend.loaded:
        return {"status": "error", "message": "Model not loaded"}
    
    return {"status": "ok", "message": "Server is healthy"}

@app.get("/api/v1/models")
async def list_models():
    """List available models"""
    models_dir = Path(config_manager.get("models.directory", "models"))
    
    if not models_dir.exists():
        return {"models": []}
    
    models = []
    for model_file in models_dir.glob("*.gguf"):
        models.append({
            "name": model_file.stem,
            "path": str(model_file),
            "size": model_file.stat().st_size
        })
    
    return {"models": models}

@app.get("/api/v1/models/current")
async def current_model():
    """Get information about the currently loaded model"""
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend not initialized"
        )
    
    if not backend.loaded:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model not loaded"
        )
    
    return {
        "path": str(backend.model_path),
        "threads": backend.threads,
        "low_vram": backend.low_vram,
        "n_ctx": backend.n_ctx,
        "loaded": backend.loaded,
        "real_backend": backend.use_real_backend
    }

@app.post("/api/v1/inference")
async def inference(
    request: Dict[str, Any],
    current_user = Depends(security_manager.get_current_user if security_manager else None)
):
    """Perform inference with the loaded model"""
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend not initialized"
        )
    
    if not backend.loaded:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model not loaded"
        )
    
    # Check permissions if security manager is available
    if security_manager and current_user:
        if not security_manager.check_permission(current_user, Permission.READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Extract prompt and parameters
    prompt = request.get("prompt", "")
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt is required"
        )
    
    # Extract inference parameters
    params = {
        "temperature": request.get("temperature", 0.7),
        "max_tokens": request.get("max_tokens", 2048),
        "top_p": request.get("top_p", 0.9)
    }
    
    # Perform inference
    try:
        response = await backend.perform_inference(prompt, params)
        return {"response": response}
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed"
        )

@app.post("/api/v1/models/load")
async def load_model(
    request: Dict[str, Any],
    current_user = Depends(security_manager.require_permission(Permission.MODEL_MANAGE) if security_manager else None)
):
    """Load a new model"""
    model_path = request.get("path")
    if not model_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model path is required"
        )
    
    model_path = Path(model_path)
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Extract parameters
    threads = request.get("threads", 4)
    low_vram = request.get("low_vram", False)
    n_ctx = request.get("n_ctx", 4096)
    
    # Unload current model if loaded
    global backend
    if backend and backend.loaded:
        await backend.unload()
    
    # Create new backend instance
    backend = LocalLlamaBackend(model_path, threads, low_vram, n_ctx)
    
    # Load model
    try:
        await backend.load()
        
        # Update configuration
        if config_manager:
            config_manager.set("model.path", str(model_path))
            config_manager.set("server.threads", threads)
            config_manager.set("server.low_vram", low_vram)
            config_manager.set("server.n_ctx", n_ctx)
            if hasattr(config_manager, 'save'):
                config_manager.save()
        
        return {"message": "Model loaded successfully"}
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )

@app.post("/api/v1/models/unload")
async def unload_model(
    current_user = Depends(security_manager.require_permission(Permission.MODEL_MANAGE) if security_manager else None)
):
    """Unload the current model"""
    if not backend:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backend not initialized"
        )
    
    if not backend.loaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model not loaded"
        )
    
    try:
        await backend.unload()
        return {"message": "Model unloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )

@app.get("/api/v1/system/status")
async def system_status(
    current_user = Depends(security_manager.get_current_user if security_manager else None)
):
    """Get system status information"""
    if not system_optimizer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System optimizer not initialized"
        )
    
    # Get system information
    system_info = system_optimizer.get_system_info() if hasattr(system_optimizer, 'get_system_info') else {}
    
    # Get performance metrics if available
    performance_metrics = None
    if performance_benchmark:
        performance_metrics = performance_benchmark.get_current_metrics() if hasattr(performance_benchmark, 'get_current_metrics') else None
    
    # Get security status if available and user has permission
    security_status = None
    if security_manager and current_user and security_manager.check_permission(current_user, Permission.ADMIN):
        security_status = security_manager.get_security_status()
    
    return {
        "system": system_info,
        "performance": performance_metrics,
        "security": security_status
    }

@app.post("/api/v1/system/optimize")
async def optimize_system(
    request: Dict[str, Any],
    current_user = Depends(security_manager.require_permission(Permission.SYSTEM_CONFIG) if security_manager else None)
):
    """Optimize system settings"""
    if not system_optimizer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System optimizer not initialized"
        )
    
    # Get optimization options
    optimize_cpu = request.get("cpu", True)
    optimize_memory = request.get("memory", True)
    optimize_disk = request.get("disk", True)
    optimize_gpu = request.get("gpu", True)
    
    try:
        # Apply optimizations
        optimizations = system_optimizer.optimize_all(
            optimize_cpu=optimize_cpu,
            optimize_memory=optimize_memory,
            optimize_disk=optimize_disk,
            optimize_gpu=optimize_gpu
        )
        
        # Log security event if security manager is available
        if security_manager and current_user:
            security_manager.log_security_event(
                "system_optimized",
                {
                    "cpu": optimize_cpu,
                    "memory": optimize_memory,
                    "disk": optimize_disk,
                    "gpu": optimize_gpu,
                    "optimizations": optimizations
                },
                user=current_user.username
            )
        
        return {"message": "System optimized successfully", "optimizations": optimizations}
    except Exception as e:
        logger.error(f"Failed to optimize system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize system: {str(e)}"
        )

@app.get("/api/v1/performance/benchmark")
async def run_benchmark(
    current_user = Depends(security_manager.require_permission(Permission.SYSTEM_CONFIG) if security_manager else None)
):
    """Run performance benchmark"""
    if not performance_benchmark:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Performance benchmark not initialized"
        )
    
    if not backend or not backend.loaded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model must be loaded to run benchmark"
        )
    
    try:
        # Run benchmark
        results = performance_benchmark.run_full_benchmark(backend) if hasattr(performance_benchmark, 'run_full_benchmark') else {}
        
        # Log security event if security manager is available
        if security_manager and current_user:
            security_manager.log_security_event(
                "performance_benchmark",
                {"results": results},
                user=current_user.username
            )
        
        return {"message": "Benchmark completed", "results": results}
    except Exception as e:
        logger.error(f"Failed to run benchmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run benchmark: {str(e)}"
        )

@app.post("/api/v1/backup/create")
async def create_backup(
    request: Dict[str, Any],
    current_user = Depends(security_manager.require_permission(Permission.SYSTEM_CONFIG) if security_manager else None)
):
    """Create a backup"""
    if not backup_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup manager not initialized"
        )
    
    # Get backup options
    backup_models = request.get("models", True)
    backup_configs = request.get("configs", True)
    backup_logs = request.get("logs", True)
    
    try:
        # Create backup
        # Check if backup_manager has the create_backup method with these parameters
        if hasattr(backup_manager, 'create_backup'):
            # Try to call with the parameters
            try:
                backup_path = backup_manager.create_backup(
                    include_models=backup_models,
                    include_config=backup_configs,
                    include_logs=backup_logs
                )
            except TypeError:
                # Fallback to create_backup without parameters
                backup_path = backup_manager.create_backup()
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup manager does not support creating backups"
            )
        
        # Log security event if security manager is available
        if security_manager and current_user:
            security_manager.log_security_event(
                "backup_created",
                {
                    "backup_path": str(backup_path),
                    "models": backup_models,
                    "configs": backup_configs,
                    "logs": backup_logs
                },
                user=current_user.username
            )
        
        return {"message": "Backup created successfully", "backup_path": str(backup_path)}
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@app.post("/api/v1/backup/restore")
async def restore_backup(
    request: Dict[str, Any],
    current_user = Depends(security_manager.require_permission(Permission.SYSTEM_CONFIG) if security_manager else None)
):
    """Restore from a backup"""
    if not backup_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup manager not initialized"
        )
    
    backup_path = request.get("backup_path")
    if not backup_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Backup path is required"
        )
    
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backup not found"
        )
    
    # Get restore options
    restore_models = request.get("models", True)
    restore_configs = request.get("configs", True)
    restore_logs = request.get("logs", True)
    
    try:
        # Restore backup
        # Check if backup_manager has the restore_backup_from_path method
        if hasattr(backup_manager, 'restore_backup_from_path'):
            # Try to call with the path-based method
            try:
                success = backup_manager.restore_backup_from_path(
                    backup_path,
                    restore_models=restore_models,
                    restore_configs=restore_configs,
                    restore_logs=restore_logs
                )
            except TypeError:
                # Fallback to restore_backup_from_path with just the path
                success = backup_manager.restore_backup_from_path(backup_path)
        elif hasattr(backup_manager, 'restore_backup'):
            # Try to call with the ID-based method
            try:
                success = backup_manager.restore_backup(
                    str(backup_path),
                    restore_models=restore_models,
                    restore_config=restore_configs,
                    restore_logs=restore_logs
                )
            except TypeError:
                # Fallback to restore_backup with just the path
                success = backup_manager.restore_backup(str(backup_path))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup manager does not support restoring backups"
            )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore backup"
            )
        
        # Log security event if security manager is available
        if security_manager and current_user:
            security_manager.log_security_event(
                "backup_restored",
                {
                    "backup_path": str(backup_path),
                    "models": restore_models,
                    "configs": restore_configs,
                    "logs": restore_logs
                },
                user=current_user.username
            )
        
        return {"message": "Backup restored successfully"}
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}"
        )

@app.get("/api/v1/backup/list")
async def list_backups(
    current_user = Depends(security_manager.get_current_user if security_manager else None)
):
    """List available backups"""
    if not backup_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup manager not initialized"
        )
    
    try:
        # List backups
        backups = backup_manager.list_backups()
        return {"backups": backups}
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )

class LlamaServer:
    """Main server class for the Llama.cpp Server"""
    
    def __init__(self, config: ServerConfig):
        """Initialize the server with configuration
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.app = app
        self.host = config.get("server.host", "0.0.0.0")
        self.port = config.get("server.port", 8000)
        # Ensure log level is valid for uvicorn
        log_level = config.get("server.log_level", "info")
        # Map to uvicorn's expected log levels
        if log_level.lower() == "debug":
            self.log_level = "debug"
        elif log_level.lower() == "info":
            self.log_level = "info"
        elif log_level.lower() in ["warning", "warn"]:
            self.log_level = "warning"
        elif log_level.lower() == "error":
            self.log_level = "error"
        elif log_level.lower() == "critical":
            self.log_level = "critical"
        else:
            self.log_level = "info"  # Default to info if invalid
        
        # Initialize global variables with config
        global config_manager
        config_manager = ConfigManager(config.config_path)
    
    def run(self):
        """Run the server"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level=self.log_level
        )

if __name__ == "__main__":
    # Load configuration
    config = ServerConfig.load()
    
    # Create and run server
    server = LlamaServer(config)
    server.run()
